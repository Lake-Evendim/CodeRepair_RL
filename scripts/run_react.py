"""CLI entry point for running ReAct baseline evaluation."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from minirepair.agents.react_agent import LLMPolicy, MockPolicy  # noqa: E402
from minirepair.evaluation.evaluator import Evaluator  # noqa: E402
from minirepair.evaluation.metrics import EvalMode  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ReAct baseline evaluation")
    parser.add_argument(
        "--split", required=True, choices=["train", "validation", "test"],
        help="Which split to evaluate",
    )
    parser.add_argument(
        "--policy", default="mock", choices=["mock", "qwen_base"],
        help="Policy type to use",
    )
    parser.add_argument(
        "--model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        help="HuggingFace model ID (for qwen_base policy)",
    )
    parser.add_argument(
        "--eval-mode", default=None,
        choices=["train_reward", "validation_selection", "final_test"],
        help="Eval mode. Auto-inferred from split if not provided.",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output directory for trajectories and metrics",
    )
    parser.add_argument(
        "--max-tasks", type=int, default=None,
        help="Maximum number of tasks to evaluate",
    )
    parser.add_argument(
        "--benchmarks-dir", default="benchmarks",
        help="Root benchmarks directory",
    )
    return parser.parse_args()


def infer_eval_mode(split: str, eval_mode: str | None) -> EvalMode:
    """Infer eval_mode from split if not explicitly provided."""
    if eval_mode is not None:
        return EvalMode(eval_mode)

    mapping = {
        "train": EvalMode.TRAIN_REWARD,
        "validation": EvalMode.VALIDATION_SELECTION,
        "test": EvalMode.FINAL_TEST,
    }
    return mapping[split]


def build_policy(args: argparse.Namespace):
    """Build the policy from CLI args."""
    if args.policy == "mock":
        # For mock, we need metadata from the first task to construct gold actions
        # The evaluator will create a fresh MockPolicy per task if needed
        # Here we create a placeholder that the evaluator can override
        benchmarks_dir = Path(args.benchmarks_dir)
        split_dir = benchmarks_dir / args.split
        task_dirs = sorted(
            d for d in split_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        )
        if not task_dirs:
            logger.error("No tasks found in %s", split_dir)
            sys.exit(1)
        metadata = json.loads((task_dirs[0] / "metadata.json").read_text())
        return MockPolicy(metadata)
    elif args.policy == "qwen_base":
        return LLMPolicy(model_name=args.model)
    else:
        raise ValueError(f"Unknown policy: {args.policy}")


def main() -> None:
    args = parse_args()
    eval_mode = infer_eval_mode(args.split, args.eval_mode)
    benchmarks_dir = Path(args.benchmarks_dir)
    split_dir = benchmarks_dir / args.split

    if not split_dir.exists():
        logger.error("Split directory not found: %s", split_dir)
        sys.exit(1)

    output_dir = Path(args.output) if args.output else Path("logs") / f"react_{args.split}"
    output_dir.mkdir(parents=True, exist_ok=True)

    policy = build_policy(args)

    logger.info("Running ReAct evaluation: split=%s, policy=%s, eval_mode=%s", args.split, args.policy, eval_mode.value)

    evaluator = Evaluator(
        policy=policy,
        eval_mode=eval_mode,
        method_name="react",
        trajectory_dir=output_dir,
    )

    result = evaluator.evaluate_split(
        split_path=split_dir,
        max_tasks=args.max_tasks,
    )

    # Print summary
    agg = result["aggregate"]
    logger.info("=== Evaluation Summary ===")
    logger.info("Tasks evaluated: %d", result["num_tasks"])
    logger.info("Public pass rate: %.2f%%", agg.get("public_pass_rate", 0) * 100)
    if agg.get("private_pass_rate") is not None:
        logger.info("Private pass rate: %.2f%%", agg.get("private_pass_rate", 0) * 100)
    if agg.get("hidden_pass_rate") is not None:
        logger.info("Hidden pass rate: %.2f%%", agg.get("hidden_pass_rate", 0) * 100)
    logger.info("Avg steps: %.1f", agg.get("avg_steps", 0))
    logger.info("Avg invalid actions: %.1f", agg.get("avg_invalid_actions", 0))
    logger.info("Output saved to: %s", output_dir)

    # Save full result as JSON
    result_path = output_dir / "result.json"
    # Convert non-serializable types
    serializable_result = {
        "num_tasks": result["num_tasks"],
        "eval_mode": result["eval_mode"],
        "method_name": result["method_name"],
        "policy_type": result["policy_type"],
        "aggregate": result["aggregate"],
    }
    result_path.write_text(json.dumps(serializable_result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
