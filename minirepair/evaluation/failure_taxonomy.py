"""Failure taxonomy for classifying agent episode failures."""

from __future__ import annotations

from typing import Any

# Ordered by priority — first match is primary failure type.
FAILURE_CATEGORIES = [
    "invalid_action",
    "invalid_edit",
    "reward_hacking_attempt",
    "premature_submit",
    "regression_error",
    "tool_misuse",
    "context_misunderstanding",
    "localization_error",
    "semantic_patch_error",
]

FAILURE_DESCRIPTIONS = {
    "invalid_action": "Agent produced invalid JSON or unparseable action output",
    "invalid_edit": "Edit was blocked by guardrails or exceeded edit budget",
    "reward_hacking_attempt": "Guardrail detected potential reward hacking (skip, hardcoded returns, etc.)",
    "premature_submit": "Agent submitted without running any tests",
    "regression_error": "Agent's edit introduced new test failures",
    "tool_misuse": "Agent spent budget on reads/searches without attempting any edit",
    "context_misunderstanding": "Agent read/searched extensively but produced no effective edit",
    "localization_error": "Agent edited code but failed to fix the bug (public tests still fail)",
    "semantic_patch_error": "Agent edited and tested, but tests still fail after edit",
}


def _safe_bool(val: Any) -> bool:
    """Convert a value to bool, handling CSV string representations."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return bool(val)


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert a value to float, handling CSV string representations."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def classify_failure(
    trajectory: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """Classify a failed episode into failure categories.

    Args:
        trajectory: Full trajectory from the episode.
        metrics: Per-episode metrics dict from compute_episode_metrics().

    Returns:
        Dict with:
        - "primary": first matching failure category (str)
        - "all_categories": list of all matching categories
        - "passed": True if the episode succeeded (no failure classification needed)
    """
    public_pass = _safe_bool(metrics.get("public_pass", False))
    if public_pass:
        return {"primary": None, "all_categories": [], "passed": True}

    matched: list[str] = []

    invalid_actions = _safe_float(metrics.get("invalid_action_count", 0))
    invalid_edits = _safe_float(metrics.get("invalid_edit_count", 0))
    guardrail_violations = _safe_float(metrics.get("guardrail_violation_count", 0))
    regression_count = _safe_float(metrics.get("regression_count", 0))
    submit_before_test = _safe_bool(metrics.get("submit_before_test", False))
    edit_count = _safe_float(metrics.get("edit_count", 0))
    read_count = _safe_float(metrics.get("read_count", 0))
    search_count = _safe_float(metrics.get("search_code", 0) or metrics.get("search_count", 0))
    test_count = _safe_float(metrics.get("test_count", 0))
    total_steps = _safe_float(metrics.get("total_steps", 0))

    # Check for reward hacking warnings in trajectory
    has_reward_hacking = False
    if guardrail_violations > 0:
        for step in trajectory:
            obs = step.get("observation", {})
            info = obs.get("info", {})
            for w in info.get("warnings", []):
                if isinstance(w, dict) and "reward_hacking" in w.get("rule", ""):
                    has_reward_hacking = True
                    break
            if has_reward_hacking:
                break

    # 1. invalid_action
    if invalid_actions > 0:
        matched.append("invalid_action")

    # 2. invalid_edit
    if invalid_edits > 0:
        matched.append("invalid_edit")

    # 3. reward_hacking_attempt
    if has_reward_hacking:
        matched.append("reward_hacking_attempt")

    # 4. premature_submit
    if submit_before_test:
        matched.append("premature_submit")

    # 5. regression_error
    if regression_count > 0:
        matched.append("regression_error")

    # 6. tool_misuse: heavy read/search, zero edits
    if edit_count == 0 and (read_count + search_count) >= 4 and total_steps >= 3:
        matched.append("tool_misuse")

    # 7. context_misunderstanding: read/search but no edit (broader than tool_misuse)
    if edit_count == 0 and (read_count + search_count) >= 2 and "tool_misuse" not in matched:
        matched.append("context_misunderstanding")

    # 8. localization_error: edited but public tests still fail
    if edit_count > 0 and not public_pass:
        matched.append("localization_error")

    # 9. semantic_patch_error: edited + tested but tests still fail
    if edit_count > 0 and test_count > 0 and not public_pass:
        matched.append("semantic_patch_error")

    # Determine primary: first match in priority order
    primary = None
    for cat in FAILURE_CATEGORIES:
        if cat in matched:
            primary = cat
            break

    return {"primary": primary, "all_categories": matched, "passed": False}


def get_failure_summary(
    metrics_list: list[dict[str, Any]],
    trajectories: list[list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Summarize failure distribution across a set of episodes.

    Args:
        metrics_list: List of per-episode metrics dicts.
        trajectories: Optional list of trajectories (same length as metrics_list).
            If provided, used for reward_hacking detection.

    Returns:
        Dict with failure_counts, primary_distribution, and per-category task_ids.
    """
    failure_counts: dict[str, int] = {cat: 0 for cat in FAILURE_CATEGORIES}
    primary_distribution: dict[str, int] = {cat: 0 for cat in FAILURE_CATEGORIES}
    category_task_ids: dict[str, list[str]] = {cat: [] for cat in FAILURE_CATEGORIES}
    total_failed = 0

    for i, m in enumerate(metrics_list):
        traj = trajectories[i] if trajectories and i < len(trajectories) else []
        result = classify_failure(traj, m)
        if result["passed"]:
            continue
        total_failed += 1
        for cat in result["all_categories"]:
            failure_counts[cat] += 1
        primary = result["primary"]
        if primary:
            primary_distribution[primary] += 1
            category_task_ids[primary].append(m.get("task_id", "unknown"))

    return {
        "total_failed": total_failed,
        "failure_counts": failure_counts,
        "primary_distribution": primary_distribution,
        "category_task_ids": category_task_ids,
    }
