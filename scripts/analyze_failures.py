#!/usr/bin/env python3
"""Failure analysis CLI: classify failures and generate case studies."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from minirepair.evaluation.failure_taxonomy import (
    FAILURE_CATEGORIES,
    classify_failure,
    get_failure_summary,
)
from minirepair.evaluation.reports import (
    format_case_study,
    format_failure_analysis,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def load_metrics(input_dir: Path) -> list[dict]:
    """Load metrics.csv from an eval log directory."""
    csv_path = input_dir / "metrics.csv"
    if not csv_path.exists():
        logger.warning("No metrics.csv found in %s", input_dir)
        return []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_trajectory(input_dir: Path, task_id: str) -> list[dict]:
    """Load trajectory JSONL for a given task."""
    traj_path = input_dir / f"{task_id}.jsonl"
    if not traj_path.exists():
        return []
    steps = []
    with open(traj_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                steps.append(json.loads(line))
    return steps


def safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    return False


def select_case_studies(
    metrics_list: list[dict],
    input_dirs: list[Path],
    max_per_category: int = 2,
) -> list[str]:
    """Select and format representative case studies per failure category.

    Ensures every category in FAILURE_CATEGORIES gets case studies by iterating
    per-category and picking episodes that contain that category, rather than
    assigning episodes to a single "primary" category.
    """
    # Build a mapping from task_id -> (metrics, input_dir) for failed episodes
    failed_tasks: list[tuple[dict, Path]] = []
    for m in metrics_list:
        if safe_bool(m.get("public_pass")):
            continue
        task_id = m.get("task_id", "unknown")
        for input_dir in input_dirs:
            if (input_dir / f"{task_id}.jsonl").exists():
                failed_tasks.append((m, input_dir))
                break
        else:
            failed_tasks.append((m, input_dirs[0] if input_dirs else Path(".")))

    # Classify each failure
    classified: list[tuple[dict, list[str], Path]] = []
    for m, input_dir in failed_tasks:
        task_id = m.get("task_id", "unknown")
        trajectory = load_trajectory(input_dir, task_id)
        result = classify_failure(trajectory, m)
        if not result["passed"] and result["all_categories"]:
            classified.append((m, result["all_categories"], input_dir))

    # Select case studies per category, ensuring every category is covered.
    # Track which (task_id, method) pairs have already been selected to avoid
    # duplicates across categories.
    selected_keys: set[tuple[str, str]] = set()
    category_case_studies: dict[str, list[str]] = {cat: [] for cat in FAILURE_CATEGORIES}

    # Build index: category -> list of (metrics, cats, input_dir) episodes
    category_episodes: dict[str, list[tuple[dict, list[str], Path]]] = {cat: [] for cat in FAILURE_CATEGORIES}
    for m, cats, input_dir in classified:
        for cat in cats:
            if cat in category_episodes:
                category_episodes[cat].append((m, cats, input_dir))

    # First pass: ensure each category gets at least 1 case study
    for cat in FAILURE_CATEGORIES:
        episodes = category_episodes[cat]
        count = 0
        for m, cats, input_dir in episodes:
            if count >= max_per_category:
                break
            task_id = m.get("task_id", "unknown")
            method = m.get("method_name", "unknown")
            key = (task_id, method)
            if key in selected_keys:
                continue
            trajectory = load_trajectory(input_dir, task_id)
            cs = format_case_study(
                task_id=task_id,
                method=method,
                metrics=m,
                failure_types=cats,
                trajectory=trajectory,
            )
            category_case_studies[cat].append(cs)
            selected_keys.add(key)
            count += 1

    # Flatten, preserving category order from FAILURE_CATEGORIES
    case_studies: list[str] = []
    for cat in FAILURE_CATEGORIES:
        case_studies.extend(category_case_studies[cat])

    return case_studies


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze evaluation failures")
    parser.add_argument(
        "--inputs", nargs="+", required=True,
        help="Eval log directories containing metrics.csv and trajectory JSONLs",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/failure_analysis.md"),
        help="Output report path (default: reports/failure_analysis.md)",
    )
    parser.add_argument(
        "--max-case-studies", type=int, default=2,
        help="Max case studies per failure category (default: 2)",
    )
    parser.add_argument(
        "--include-smoke-tests", action="store_true",
        help="Include mock/gold/oracle policy results",
    )

    args = parser.parse_args()

    # Load all metrics
    all_metrics: list[dict] = []
    input_dirs: list[Path] = []
    for input_str in args.inputs:
        input_dir = Path(input_str)
        if not input_dir.exists():
            logger.warning("Input directory not found: %s", input_dir)
            continue
        metrics = load_metrics(input_dir)
        if not args.include_smoke_tests:
            metrics = [
                m for m in metrics
                if m.get("policy_type", "") not in ("mock", "gold", "oracle")
                and not safe_bool(m.get("excluded_from_main_results"))
            ]
        all_metrics.extend(metrics)
        input_dirs.append(input_dir)

    if not all_metrics:
        logger.error("No metrics found in any input directory")
        sys.exit(1)

    logger.info("Loaded %d episodes from %d directories", len(all_metrics), len(input_dirs))

    # Build trajectories list for classification
    trajectories: list[list[dict]] = []
    for m in all_metrics:
        task_id = m.get("task_id", "unknown")
        traj = None
        for input_dir in input_dirs:
            t = load_trajectory(input_dir, task_id)
            if t:
                traj = t
                break
        trajectories.append(traj or [])

    # Compute failure summary
    failure_summary = get_failure_summary(all_metrics, trajectories)
    logger.info(
        "Failure summary: %d failed out of %d total",
        failure_summary["total_failed"], len(all_metrics),
    )

    # Select case studies
    case_studies = select_case_studies(
        all_metrics, input_dirs, args.max_case_studies,
    )
    logger.info("Generated %d case studies", len(case_studies))

    # Generate report
    report = format_failure_analysis(
        failure_summary=failure_summary,
        case_studies=case_studies,
    )

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    logger.info("Failure analysis written to %s", args.output)
    print(report)


if __name__ == "__main__":
    main()
