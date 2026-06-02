"""Evaluator: batch-run splits and collect metrics with eval-mode-aware test access."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from minirepair.agents.react_agent import Policy, run_episode
from minirepair.env.code_repair_env import CodeRepairEnv
from minirepair.env.sandbox import Sandbox
from minirepair.evaluation.metrics import (
    EvalMode,
    aggregate_metrics,
    compute_episode_metrics,
    write_metrics_csv,
)

logger = logging.getLogger(__name__)


def evaluate_final_state(
    sandbox: Sandbox,
    split: str,
    eval_mode: EvalMode,
) -> dict[str, bool | None]:
    """Run private/hidden tests on the sandbox after an episode.

    Access is strictly controlled by eval_mode:
    - VALIDATION_SELECTION: only tests_private/ (for validation split)
    - FINAL_TEST: only tests_hidden/ (for test split)
    - TRAIN_REWARD: only tests_private/ (for train split)
    - DATASET_VALIDATION: not used here (offline validation only)

    Args:
        sandbox: Active sandbox with working_path still available.
        split: "train", "validation", or "test".
        eval_mode: Controls which test dirs are accessible.

    Returns:
        Dict with "private_pass" and/or "hidden_pass" booleans.
    """
    result: dict[str, bool | None] = {"private_pass": None, "hidden_pass": None}

    if sandbox.working_path is None:
        return result

    # Validate eval_mode / split combinations
    if eval_mode == EvalMode.DATASET_VALIDATION:
        raise ValueError("DATASET_VALIDATION is for offline use only, not for evaluator runs")

    if eval_mode == EvalMode.VALIDATION_SELECTION:
        if split not in ("train", "validation"):
            raise ValueError(f"VALIDATION_SELECTION requires train or validation split, got {split}")
        # Run private tests only
        private_dir = sandbox.working_path / "tests_private"
        if private_dir.exists():
            pytest_result = sandbox.run_pytest(test_dirs=["tests_private"])
            result["private_pass"] = pytest_result.returncode == 0

    elif eval_mode == EvalMode.FINAL_TEST:
        if split != "test":
            raise ValueError(f"FINAL_TEST requires test split, got {split}")
        # Run hidden tests only
        hidden_dir = sandbox.working_path / "tests_hidden"
        if hidden_dir.exists():
            pytest_result = sandbox.run_pytest(test_dirs=["tests_hidden"])
            result["hidden_pass"] = pytest_result.returncode == 0

    elif eval_mode == EvalMode.TRAIN_REWARD:
        if split not in ("train", "seed"):
            raise ValueError(f"TRAIN_REWARD requires train or seed split, got {split}")
        # Run private tests only
        private_dir = sandbox.working_path / "tests_private"
        if private_dir.exists():
            pytest_result = sandbox.run_pytest(test_dirs=["tests_private"])
            result["private_pass"] = pytest_result.returncode == 0

    return result


def run_public_tests_for_pass(sandbox: Sandbox) -> bool:
    """Run public tests on the sandbox to check if they pass."""
    if sandbox.working_path is None:
        return False
    result = sandbox.run_pytest(test_dirs=["tests"])
    return result.returncode == 0


class Evaluator:
    """Batch-evaluate a split with a given policy."""

    def __init__(
        self,
        policy: Policy,
        eval_mode: EvalMode,
        method_name: str = "react",
        trajectory_dir: Path | None = None,
    ) -> None:
        self.policy = policy
        self.eval_mode = eval_mode
        self.method_name = method_name
        self.trajectory_dir = trajectory_dir

    def evaluate_task(self, task_path: Path) -> dict[str, Any]:
        """Evaluate a single task.

        Returns metrics dict for this episode.
        """
        env = CodeRepairEnv(trajectory_dir=self.trajectory_dir)
        try:
            episode_result = run_episode(env, task_path, self.policy)
            trajectory = episode_result["trajectory"]
            metadata = env.metadata
            metadata_dict = metadata.model_dump() if metadata else {}

            # Overwrite trajectory JSONL with enriched version (includes raw_output, parsed_action)
            if self.trajectory_dir and metadata:
                import json as _json
                traj_path = self.trajectory_dir / f"{metadata.task_id}.jsonl"
                traj_path.parent.mkdir(parents=True, exist_ok=True)
                with open(traj_path, "w", encoding="utf-8") as f:
                    for entry in trajectory:
                        f.write(_json.dumps(entry, ensure_ascii=False, default=str) + "\n")

            # Compute episode-level metrics from trajectory
            metrics = compute_episode_metrics(
                trajectory=trajectory,
                metadata=metadata_dict,
                policy_type=self.policy.policy_type,
                method_name=self.method_name,
            )

            # Check public pass from final state
            metrics["public_pass"] = run_public_tests_for_pass(env.sandbox) if env.sandbox else False

            # Run private/hidden tests via evaluate_final_state
            if env.sandbox and env.sandbox.working_path:
                split = metadata_dict.get("split", "unknown")
                final_metrics = evaluate_final_state(
                    sandbox=env.sandbox,
                    split=split,
                    eval_mode=self.eval_mode,
                )
                metrics["private_pass"] = final_metrics.get("private_pass")
                metrics["hidden_pass"] = final_metrics.get("hidden_pass")

            return metrics
        finally:
            env.close()

    def evaluate_split(
        self,
        split_path: Path,
        max_tasks: int | None = None,
    ) -> dict[str, Any]:
        """Evaluate all tasks in a split directory.

        Args:
            split_path: Path to the split directory (e.g. benchmarks/validation/).
            max_tasks: Maximum number of tasks to evaluate (None = all).

        Returns:
            Dict with "metrics_list", "aggregate", "output_dir" keys.
        """
        task_dirs = sorted(
            d for d in split_path.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        )
        if max_tasks is not None:
            task_dirs = task_dirs[:max_tasks]

        logger.info("Evaluating %d tasks from %s", len(task_dirs), split_path)

        metrics_list: list[dict[str, Any]] = []
        for i, task_path in enumerate(task_dirs):
            logger.info("[%d/%d] Evaluating %s", i + 1, len(task_dirs), task_path.name)
            try:
                task_metrics = self.evaluate_task(task_path)
                metrics_list.append(task_metrics)
            except Exception:
                logger.exception("Failed to evaluate %s", task_path.name)
                metrics_list.append({
                    "task_id": task_path.name,
                    "policy_type": self.policy.policy_type,
                    "method_name": self.method_name,
                    "excluded_from_main_results": self.policy.uses_gold_patch,
                    "total_steps": 0,
                    "invalid_action_count": 0,
                    "invalid_edit_count": 0,
                    "regression_count": 0,
                    "submit_before_test": False,
                    "guardrail_violation_count": 0,
                    "termination_reason": "error",
                    "tool_call_counts": {},
                    "read_count": 0,
                    "search_count": 0,
                    "edit_count": 0,
                    "test_count": 0,
                    "submit_count": 0,
                    "public_pass": False,
                    "private_pass": None,
                    "hidden_pass": None,
                })

        agg = aggregate_metrics(metrics_list)

        # Write outputs
        if self.trajectory_dir:
            self.trajectory_dir.mkdir(parents=True, exist_ok=True)
            metrics_csv_path = self.trajectory_dir / "metrics.csv"
            write_metrics_csv(metrics_list, metrics_csv_path)

            # Write summary JSON
            summary_path = self.trajectory_dir / "summary.json"
            summary_path.write_text(json.dumps(agg, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "metrics_list": metrics_list,
            "aggregate": agg,
            "num_tasks": len(task_dirs),
            "eval_mode": self.eval_mode.value,
            "method_name": self.method_name,
            "policy_type": self.policy.policy_type,
        }
