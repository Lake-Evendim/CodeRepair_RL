"""Metrics computation for episode trajectories."""

from __future__ import annotations

import csv
from enum import Enum
from pathlib import Path
from typing import Any


class EvalMode(str, Enum):
    TRAIN_REWARD = "train_reward"
    VALIDATION_SELECTION = "validation_selection"
    FINAL_TEST = "final_test"
    DATASET_VALIDATION = "dataset_validation"


def compute_episode_metrics(
    trajectory: list[dict[str, Any]],
    metadata: dict[str, Any],
    policy_type: str = "unknown",
    method_name: str = "unknown",
) -> dict[str, Any]:
    """Compute metrics from a completed episode trajectory.

    Args:
        trajectory: List of step dicts from CodeRepairEnv.trajectory.
        metadata: Task metadata dict (from TaskMetadata).
        policy_type: e.g. "mock", "qwen_base".
        method_name: e.g. "react", "sft", "rl_sparse".

    Returns:
        Dict of metric name -> value.
    """
    tool_counts: dict[str, int] = {}
    invalid_action_count = 0
    invalid_edit_count = 0
    guardrail_violations: list[dict] = []
    regression_count = 0
    saw_test = False
    submitted = False
    termination_reason = ""

    # For repeated_test_call_rate: track test calls and whether a new edit happened before each
    test_call_indices: list[int] = []
    edit_call_indices: list[int] = []

    # For patch_minimality: track unique modified files and total changed lines
    modified_files: set[str] = set()
    total_modified_lines = 0

    for step_idx, step in enumerate(trajectory):
        obs = step.get("observation", {})
        action = step.get("action", {})

        if isinstance(action, str):
            # invalid JSON action stored as string
            if obs.get("status") == "error" and obs.get("tool_name") == "parse":
                invalid_action_count += 1
            continue

        if not isinstance(action, dict):
            continue

        tool = action.get("tool", "")
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

        # Track test calls
        if tool == "run_tests":
            saw_test = True
            test_call_indices.append(step_idx)

        # Track submit
        if tool == "submit" and obs.get("status") == "submitted":
            submitted = True

        # Track invalid edits
        if tool == "edit_file" and obs.get("status") == "error":
            err = obs.get("error", "")
            if "Guardrail violation" in err or "Edit budget" in err:
                invalid_edit_count += 1

        # Track edit calls for repeated_test_call_rate and patch_minimality
        if tool == "edit_file":
            edit_call_indices.append(step_idx)
            if obs.get("status") == "success":
                args = action.get("arguments", {})
                path = args.get("path", "")
                if path:
                    modified_files.add(path)
                new_text = args.get("new_text", "")
                total_modified_lines += len(new_text.splitlines()) if new_text else 0

        # Track guardrail violations from info
        info = obs.get("info", {})
        if "violations" in info:
            for v in info["violations"]:
                guardrail_violations.append(v)
        if "warnings" in info:
            for w in info["warnings"]:
                guardrail_violations.append(w)

        # Track public test results for regression detection
        if tool == "run_tests" and obs.get("status") in ("success", "error"):
            test_info = obs.get("info", {})
            failed = test_info.get("failed", 0)
            # Simple regression: test call after edit with failures
            if tool_counts.get("edit_file", 0) > 0 and failed > 0:
                regression_count += 1

    # Extract termination reason from last step info
    if trajectory:
        last_info = trajectory[-1].get("info", {})
        termination_reason = last_info.get("termination_reason", "")

    submit_before_test = submitted and not saw_test

    # Compute repeated_test_call_rate:
    # A test call is "repeated" if there is no new valid edit between it and the previous test call.
    repeated_test_calls = 0
    if len(test_call_indices) > 1:
        for i in range(1, len(test_call_indices)):
            prev_test_idx = test_call_indices[i - 1]
            curr_test_idx = test_call_indices[i]
            # Check if any edit happened between the two test calls
            edits_between = [
                idx for idx in edit_call_indices
                if prev_test_idx < idx < curr_test_idx
            ]
            if not edits_between:
                repeated_test_calls += 1
    total_test_calls = len(test_call_indices)
    repeated_test_call_rate = repeated_test_calls / total_test_calls if total_test_calls > 0 else 0.0

    task_id = metadata.get("task_id", "unknown")
    excluded = policy_type in ("mock", "gold", "oracle")

    metrics: dict[str, Any] = {
        "task_id": task_id,
        "policy_type": policy_type,
        "method_name": method_name,
        "excluded_from_main_results": excluded,
        "total_steps": len(trajectory),
        "invalid_action_count": invalid_action_count,
        "invalid_edit_count": invalid_edit_count,
        "regression_count": regression_count,
        "submit_before_test": submit_before_test,
        "guardrail_violation_count": len(guardrail_violations),
        "termination_reason": termination_reason,
        "tool_call_counts": tool_counts,
        "read_count": tool_counts.get("read_file", 0),
        "search_count": tool_counts.get("search_code", 0),
        "edit_count": tool_counts.get("edit_file", 0),
        "test_count": tool_counts.get("run_tests", 0),
        "submit_count": tool_counts.get("submit", 0),
        "repeated_test_call_rate": repeated_test_call_rate,
        "patch_modified_lines": total_modified_lines,
        "patch_modified_files": len(modified_files),
        # These are filled by the evaluator after running private/hidden tests
        "public_pass": False,
        "private_pass": None,
        "hidden_pass": None,
    }
    return metrics


def write_metrics_csv(metrics_list: list[dict[str, Any]], output_path: Path) -> None:
    """Write metrics list to CSV file."""
    if not metrics_list:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten tool_call_counts into separate columns
    fieldnames = [k for k in metrics_list[0] if k != "tool_call_counts"]
    fieldnames.extend([
        "tool_read_count", "tool_search_count", "tool_edit_count",
        "tool_test_count", "tool_submit_count",
    ])

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics_list:
            row = {k: v for k, v in m.items() if k != "tool_call_counts"}
            counts = m.get("tool_call_counts", {})
            row["tool_read_count"] = counts.get("read_file", 0)
            row["tool_search_count"] = counts.get("search_code", 0)
            row["tool_edit_count"] = counts.get("edit_file", 0)
            row["tool_test_count"] = counts.get("run_tests", 0)
            row["tool_submit_count"] = counts.get("submit", 0)
            writer.writerow(row)


def aggregate_metrics(metrics_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate a list of per-episode metrics into summary statistics."""
    if not metrics_list:
        return {}

    n = len(metrics_list)

    def mean(key: str) -> float:
        vals = [m[key] for m in metrics_list if m.get(key) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    def rate(key: str) -> float:
        return sum(1 for m in metrics_list if m.get(key)) / n if n else 0.0

    pub = rate("public_pass")
    priv = rate("private_pass")
    hid = rate("hidden_pass")

    result: dict[str, Any] = {
        "num_episodes": n,
        "public_pass_rate": pub,
        "private_pass_rate": priv,
        "hidden_pass_rate": hid,
        "avg_invalid_actions": mean("invalid_action_count"),
        "avg_invalid_edits": mean("invalid_edit_count"),
        "avg_regressions": mean("regression_count"),
        "avg_steps": mean("total_steps"),
        "avg_read_calls": mean("read_count"),
        "avg_search_calls": mean("search_count"),
        "avg_edit_calls": mean("edit_count"),
        "avg_test_calls": mean("test_count"),
        "submit_before_test_rate": rate("submit_before_test"),
        "avg_guardrail_violations": mean("guardrail_violation_count"),
        "avg_repeated_test_call_rate": mean("repeated_test_call_rate"),
        "avg_patch_modified_lines": mean("patch_modified_lines"),
        "avg_patch_modified_files": mean("patch_modified_files"),
    }

    # Compute gap metrics only when the corresponding pass rates are meaningful
    has_private = any(m.get("private_pass") is not None for m in metrics_list)
    has_hidden = any(m.get("hidden_pass") is not None for m in metrics_list)
    if has_private:
        result["public_private_gap"] = priv - pub
    if has_hidden:
        result["public_hidden_gap"] = hid - pub

    return result
