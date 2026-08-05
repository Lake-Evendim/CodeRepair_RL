"""Shared RL training loop for sparse and dense REINFORCE."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

import torch

from minirepair.agents.react_agent import Policy
from minirepair.env.code_repair_env import CodeRepairEnv
from minirepair.env.reward import RewardCalculator
from minirepair.evaluation.evaluator import Evaluator
from minirepair.evaluation.metrics import EvalMode
from minirepair.training.rollout import collect_rollout
from minirepair.training.train_reinforce import MovingAverageBaseline, reinforce_update

logger = logging.getLogger(__name__)


class _RolloutPolicy(Policy):
    """Policy wrapper for rollout collection during RL training."""

    def __init__(self, model: Any, tokenizer: Any, config: dict[str, Any]) -> None:
        self._model = model
        self._tokenizer = tokenizer
        self._config = config

    def generate(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt")
        device = next(self._model.parameters()).device
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        with torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=self._config.get("max_new_tokens", 512),
                do_sample=self._config.get("do_sample", True),
                temperature=self._config.get("temperature", 0.7),
                top_p=0.95,
            )
        new_tokens = output_ids[0, input_ids.shape[1]:]
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)

    @property
    def policy_type(self) -> str:
        return "rl_training"


def _load_policy(config: dict[str, Any], reward_mode: str) -> tuple[Any, Any]:
    """Load model + tokenizer from SFT adapter for RL training."""
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from minirepair.training.train_sft import resolve_model_path

    model_name = config["model_name"]
    sft_adapter = config["sft_adapter_path"]

    model_path = resolve_model_path(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map={"": 0} if device == "cuda" else None,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(model, sft_adapter)
    model.enable_adapter_layers()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()

    logger.info("Loaded model with SFT adapter from %s", sft_adapter)
    trainable = sum(1 for _, p in model.named_parameters() if p.requires_grad)
    logger.info("Trainable parameters: %d", trainable)

    return model, tokenizer


def _get_task_dirs(benchmark_root: Path, split: str = "train") -> list[Path]:
    """Get sorted list of task directories."""
    split_path = benchmark_root / split
    return sorted(
        d for d in split_path.iterdir()
        if d.is_dir() and (d / "metadata.json").exists()
    )


def _evaluate_validation(policy: Policy, benchmark_root: Path, max_tasks: int | None = None) -> dict:
    """Run validation evaluation and return metrics."""
    evaluator = Evaluator(
        policy=policy,
        eval_mode=EvalMode.VALIDATION_SELECTION,
        method_name=policy.policy_type,
    )
    result = evaluator.evaluate_split(
        benchmark_root / "validation",
        max_tasks=max_tasks,
    )
    return result["aggregate"]


def run_rl_training(
    config: dict[str, Any],
    reward_mode: str,
    dry_run: bool = False,
) -> Path:
    """Run REINFORCE RL training loop.

    Args:
        config: Training configuration dict.
        reward_mode: "sparse" or "dense".
        dry_run: If True, run minimal training for validation.

    Returns:
        Path to saved adapter directory.
    """
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_root = Path(config.get("benchmark_root", "benchmarks"))
    num_epochs = config.get("num_epochs", 3)
    num_rollouts = config.get("num_rollouts_per_task", 2)
    lr = config.get("learning_rate", 1e-5)
    baseline_momentum = config.get("baseline_momentum", 0.9)
    eval_interval = config.get("eval_interval", 1)
    max_tasks_per_epoch = config.get("max_tasks_per_epoch", None)

    dry_cfg = config.get("dry_run", {})
    max_updates = None
    if dry_run:
        max_tasks_per_epoch = dry_cfg.get("max_tasks", 2)
        max_updates = dry_cfg.get("max_updates", None)
        num_epochs = 1

    # Load model and tokenizer
    model, tokenizer = _load_policy(config, reward_mode)

    # Setup optimizer (LoRA params only)
    for name, param in model.named_parameters():
        if "lora" not in name.lower():
            param.requires_grad = False
    optimizer = torch.optim.Adam(
        [p for p in model.parameters() if p.requires_grad], lr=lr
    )
    baseline = MovingAverageBaseline(momentum=baseline_momentum)

    # Get training tasks
    task_dirs = _get_task_dirs(benchmark_root, "train")
    logger.info("Found %d training tasks", len(task_dirs))

    rollout_policy = _RolloutPolicy(model, tokenizer, config)

    # Training logs
    training_log: list[dict] = []
    curves: dict[str, list] = {
        "epoch": [], "loss": [], "avg_return": [],
        "baseline": [], "val_private_pass": [],
    }

    for epoch in range(num_epochs):
        random.shuffle(task_dirs)
        epoch_tasks = task_dirs[:max_tasks_per_epoch] if max_tasks_per_epoch else task_dirs

        epoch_returns = []
        epoch_losses = []

        for task_idx, task_path in enumerate(epoch_tasks):
            reward_calc = RewardCalculator(reward_mode, EvalMode.TRAIN_REWARD)

            # Collect rollouts for this task
            task_rollouts = []
            for _ in range(num_rollouts):
                env = CodeRepairEnv()
                try:
                    result = collect_rollout(env, task_path, rollout_policy, reward_calc)
                    task_rollouts.append(result)
                    epoch_returns.append(result.total_return)
                finally:
                    env.close()

            # REINFORCE update using collected rollouts
            update_result = reinforce_update(
                model, tokenizer, task_rollouts, baseline, optimizer
            )
            epoch_losses.append(update_result.loss)

            task_returns = [r.total_return for r in task_rollouts]
            logger.info(
                "  [%d/%d] %s: returns=%s, loss=%.4f, advantage=%.4f",
                task_idx + 1, len(epoch_tasks), task_path.name,
                [f"{r:.2f}" for r in task_returns],
                update_result.loss, update_result.avg_advantage,
            )

            # Free GPU memory from computation graph
            torch.cuda.empty_cache()

            if max_updates and task_idx + 1 >= max_updates:
                logger.info("Dry-run: stopping after %d update(s)", task_idx + 1)
                break

        # Update baseline once per epoch with mean return
        if epoch_returns:
            epoch_mean_return = sum(epoch_returns) / len(epoch_returns)
            baseline.update(epoch_mean_return)

        # Log epoch stats
        avg_loss = sum(epoch_losses) / len(epoch_losses) if epoch_losses else 0.0
        avg_return = sum(epoch_returns) / len(epoch_returns) if epoch_returns else 0.0

        curves["epoch"].append(epoch)
        curves["loss"].append(avg_loss)
        curves["avg_return"].append(avg_return)
        curves["baseline"].append(baseline.value)

        logger.info(
            "Epoch %d/%d: loss=%.4f, avg_return=%.4f, baseline=%.4f",
            epoch + 1, num_epochs, avg_loss, avg_return, baseline.value,
        )

        # Validation
        if (epoch + 1) % eval_interval == 0:
            from minirepair.agents.rl_policy import RLPolicy

            # Save current adapter for eval
            model.save_pretrained(str(output_dir))
            tokenizer.save_pretrained(str(output_dir))

            eval_policy = RLPolicy(
                base_model_name=config["model_name"],
                adapter_path=str(output_dir),
                policy_type=f"rl_{reward_mode}_qwen_lora",
            )

            val_metrics = _evaluate_validation(eval_policy, benchmark_root)
            val_private = val_metrics.get("private_pass_rate", 0.0)
            curves["val_private_pass"].append(val_private)
            logger.info("Validation private pass rate: %.3f", val_private)

            training_log.append({
                "epoch": epoch + 1,
                "loss": avg_loss,
                "avg_return": avg_return,
                "baseline": baseline.value,
                "val_private_pass_rate": val_private,
            })

    # Save final adapter
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    logger.info("Adapter saved to %s", output_dir)

    # Save training log
    log_path = output_dir / "training_log.json"
    log_path.write_text(json.dumps(training_log, indent=2))

    # Save curves
    curves_path = output_dir / "curves.json"
    curves_path.write_text(json.dumps(curves, indent=2))

    return output_dir
