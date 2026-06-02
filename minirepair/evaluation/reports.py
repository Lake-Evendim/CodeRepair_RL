"""Report formatting helpers for evaluation results."""

from __future__ import annotations

from typing import Any


def format_main_results_table(results: list[dict[str, Any]]) -> str:
    """Format main results comparison table for all methods.

    Args:
        results: List of dicts, each with keys:
            - method_name, policy_type, eval_mode, split
            - aggregate: dict from aggregate_metrics()
            - num_tasks: int

    Returns:
        Markdown string for the main results table.
    """
    headers = [
        "Method", "Public Pass", "Private/Hidden Pass",
        "Gap", "Invalid Action", "Invalid Edit",
        "Avg Steps", "Repeated Test", "Patch Lines",
    ]
    lines = ["# Main Results", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for r in results:
        agg = r.get("aggregate", {})
        method = r.get("method_name", "unknown")
        split = r.get("split", "unknown")
        eval_mode = r.get("eval_mode", "unknown")

        pub = agg.get("public_pass_rate", 0)

        # Pick the right pass rate and gap depending on eval mode
        if eval_mode == "final_test" or split == "test":
            pass_label = "hidden"
            pass_rate = agg.get("hidden_pass_rate", 0)
            gap = agg.get("public_hidden_gap", 0)
        else:
            pass_label = "private"
            pass_rate = agg.get("private_pass_rate", 0)
            gap = agg.get("public_private_gap", 0)

        pass_str = f"{pass_rate:.1%} ({pass_label})"
        gap_str = f"{gap:+.1%}" if gap else "N/A"

        vals = [
            method,
            f"{pub:.1%}",
            pass_str,
            gap_str,
            f"{agg.get('avg_invalid_actions', 0):.2f}",
            f"{agg.get('avg_invalid_edits', 0):.2f}",
            f"{agg.get('avg_steps', 0):.1f}",
            f"{agg.get('avg_repeated_test_call_rate', 0):.1%}",
            f"{agg.get('avg_patch_modified_lines', 0):.1f}",
        ]
        lines.append("| " + " | ".join(vals) + " |")

    lines.append("")
    lines.append(f"Total methods compared: {len(results)}")
    return "\n".join(lines)


def format_reward_ablation_table(results: list[dict[str, Any]]) -> str:
    """Format reward ablation comparison table.

    Args:
        results: List of dicts with method_name, aggregate, split, eval_mode.

    Returns:
        Markdown string for the reward ablation table.
    """
    headers = [
        "Reward", "Val Private Pass", "Test Hidden Pass",
        "Invalid Action", "Invalid Edit", "Avg Steps",
    ]
    lines = ["# Reward Ablation", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for r in results:
        agg = r.get("aggregate", {})
        method = r.get("method_name", "unknown")

        # Extract reward mode from method name
        if "sparse" in method:
            reward = "Sparse"
        elif "dense" in method:
            reward = "Dense"
        else:
            reward = method

        vals = [
            reward,
            f"{agg.get('private_pass_rate', 0):.1%}",
            f"{agg.get('hidden_pass_rate', 'N/A')}" if isinstance(agg.get("hidden_pass_rate"), str) else f"{agg.get('hidden_pass_rate', 0):.1%}",
            f"{agg.get('avg_invalid_actions', 0):.2f}",
            f"{agg.get('avg_invalid_edits', 0):.2f}",
            f"{agg.get('avg_steps', 0):.1f}",
        ]
        lines.append("| " + " | ".join(vals) + " |")

    lines.append("")
    return "\n".join(lines)


def format_case_study(
    task_id: str,
    method: str,
    metrics: dict[str, Any],
    failure_types: list[str],
    trajectory: list[dict[str, Any]] | None = None,
    max_trajectory_steps: int = 3,
) -> str:
    """Format a single failure case study.

    Args:
        task_id: Task identifier.
        method: Method name (react, sft, etc.).
        metrics: Per-episode metrics dict.
        failure_types: List of failure categories for this episode.
        trajectory: Optional trajectory for summarizing key steps.
        max_trajectory_steps: Max trajectory steps to include in summary.

    Returns:
        Markdown string for the case study.
    """
    lines = [
        f"### Case: {task_id} ({method})",
        "",
        f"- **Primary failure**: {failure_types[0] if failure_types else 'unknown'}",
        f"- **All categories**: {', '.join(failure_types) if failure_types else 'none'}",
        f"- **Steps**: {metrics.get('total_steps', 0)}",
        f"- **Edits**: {metrics.get('edit_count', 0)}",
        f"- **Tests**: {metrics.get('test_count', 0)}",
        f"- **Invalid actions**: {metrics.get('invalid_action_count', 0)}",
        f"- **Invalid edits**: {metrics.get('invalid_edit_count', 0)}",
        f"- **Termination**: {metrics.get('termination_reason', 'unknown')}",
    ]

    if trajectory:
        lines.append("")
        lines.append("**Trajectory summary:**")
        lines.append("```")
        for i, step in enumerate(trajectory[:max_trajectory_steps]):
            action = step.get("action", {})
            obs = step.get("observation", {})
            if isinstance(action, dict):
                tool = action.get("tool", "?")
                args = action.get("arguments", {})
                status = obs.get("status", "?")
                lines.append(f"  Step {i+1}: {tool}({args}) -> {status}")
            else:
                lines.append(f"  Step {i+1}: invalid_action -> {obs.get('status', 'error')}")
        if len(trajectory) > max_trajectory_steps:
            lines.append(f"  ... ({len(trajectory) - max_trajectory_steps} more steps)")
        lines.append("```")

    lines.append("")
    return "\n".join(lines)


def format_failure_analysis(
    failure_summary: dict[str, Any],
    case_studies: list[str],
    title: str = "Failure Analysis",
) -> str:
    """Format the complete failure analysis report.

    Args:
        failure_summary: Output from get_failure_summary().
        case_studies: List of formatted case study strings.
        title: Report title.

    Returns:
        Complete markdown report string.
    """
    from minirepair.evaluation.failure_taxonomy import FAILURE_DESCRIPTIONS

    total_failed = failure_summary.get("total_failed", 0)
    primary_dist = failure_summary.get("primary_distribution", {})
    failure_counts = failure_summary.get("failure_counts", {})

    lines = [f"# {title}", ""]

    # Overview
    lines.append(f"Total failed episodes: {total_failed}")
    lines.append("")

    # Primary failure distribution table
    lines.append("## Primary Failure Distribution")
    lines.append("")
    lines.append("| Category | Count | % of Failures | Description |")
    lines.append("|----------|-------|---------------|-------------|")

    for cat, count in sorted(primary_dist.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        pct = count / total_failed * 100 if total_failed > 0 else 0
        desc = FAILURE_DESCRIPTIONS.get(cat, "")
        lines.append(f"| {cat} | {count} | {pct:.1f}% | {desc} |")

    lines.append("")

    # Multi-label failure counts
    lines.append("## All Failure Categories (multi-label)")
    lines.append("")
    lines.append("| Category | Occurrences |")
    lines.append("|----------|-------------|")
    for cat, count in sorted(failure_counts.items(), key=lambda x: -x[1]):
        if count == 0:
            continue
        lines.append(f"| {cat} | {count} |")

    lines.append("")

    # Case studies
    if case_studies:
        lines.append("## Case Studies")
        lines.append("")
        for cs in case_studies:
            lines.append(cs)

    return "\n".join(lines)
