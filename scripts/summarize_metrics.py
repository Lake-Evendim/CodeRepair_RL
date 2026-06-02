"""Aggregate evaluation logs into summary reports."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize evaluation metrics into reports")
    parser.add_argument(
        "--inputs", nargs="+", required=True,
        help="Input directories containing metrics.csv",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output markdown file path",
    )
    parser.add_argument(
        "--include-smoke-tests", action="store_true",
        help="Include mock/gold/oracle policy results (excluded by default)",
    )
    parser.add_argument(
        "--require-main-comparable", action="store_true",
        help="Only include results from the main comparable model family",
    )
    parser.add_argument(
        "--title", default=None,
        help="Report title (default: auto-detect from inputs)",
    )
    return parser.parse_args()


def load_metrics_from_dir(input_dir: Path) -> list[dict]:
    """Load metrics from a directory's metrics.csv."""
    csv_path = input_dir / "metrics.csv"
    if not csv_path.exists():
        logger.warning("No metrics.csv found in %s", input_dir)
        return []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_summary_from_dir(input_dir: Path) -> dict | None:
    """Load summary.json if available."""
    summary_path = input_dir / "summary.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text())
    return None


def filter_metrics(metrics_list: list[dict], include_smoke: bool) -> list[dict]:
    """Filter out excluded results unless --include-smoke-tests."""
    if include_smoke:
        return metrics_list

    filtered = []
    for m in metrics_list:
        excluded = m.get("excluded_from_main_results", "False")
        if isinstance(excluded, str):
            excluded = excluded.lower() in ("true", "1", "yes")
        if excluded:
            continue
        policy_type = m.get("policy_type", "")
        if policy_type in ("mock", "gold", "oracle"):
            continue
        filtered.append(m)
    return filtered


def compute_aggregate(metrics_list: list[dict]) -> dict:
    """Compute summary statistics from filtered metrics."""
    if not metrics_list:
        return {"num_episodes": 0}

    n = len(metrics_list)

    def safe_float(val: str | float | None, default: float = 0.0) -> float:
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def safe_bool(val: str | bool | None) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return False

    def mean(key: str) -> float:
        vals = [safe_float(m.get(key)) for m in metrics_list if m.get(key) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    def rate(key: str) -> float:
        return sum(1 for m in metrics_list if safe_bool(m.get(key))) / n

    pub = rate("public_pass")
    priv = rate("private_pass")
    hid = rate("hidden_pass")

    result = {
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

    # Gap metrics
    has_private = any(m.get("private_pass") not in (None, "", "None") for m in metrics_list)
    has_hidden = any(m.get("hidden_pass") not in (None, "", "None") for m in metrics_list)
    if has_private:
        result["public_private_gap"] = priv - pub
    if has_hidden:
        result["public_hidden_gap"] = hid - pub

    return result


def format_markdown_report(input_results: list[dict], output_path: Path, title: str | None = None) -> str:
    """Format a markdown report from multiple input summaries."""
    if title is None:
        # Auto-detect title from method names
        methods = set()
        for entry in input_results:
            mn = entry.get("method_name", "react")
            methods.add(mn)
        if methods == {"react"}:
            title = "ReAct Baseline Report"
        elif len(methods) > 1:
            title = "Main Results"
        else:
            title = f"{methods.pop().replace('_', ' ').title()} Report"

    lines = [f"# {title}", ""]

    for entry in input_results:
        input_dir = entry["input_dir"]
        total = entry["total_metrics"]
        filtered = entry["filtered_metrics"]
        agg = entry["aggregate"]
        policy_type = entry.get("policy_type", "unknown")
        method_name = entry.get("method_name", "react")
        eval_mode = entry.get("eval_mode", "unknown")

        lines.append(f"## {input_dir}")
        lines.append("")
        lines.append(f"- Policy: `{policy_type}`")
        lines.append(f"- Method: `{method_name}`")
        lines.append(f"- Eval mode: `{eval_mode}`")
        lines.append(f"- Total episodes: {total}")
        lines.append(f"- Included episodes: {filtered}")
        lines.append("")

        if agg.get("num_episodes", 0) > 0:
            lines.append("### Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Public pass rate | {agg.get('public_pass_rate', 0):.2%} |")
            if agg.get("private_pass_rate") is not None:
                lines.append(f"| Private pass rate | {agg.get('private_pass_rate', 0):.2%} |")
            if agg.get("hidden_pass_rate") is not None:
                lines.append(f"| Hidden pass rate | {agg.get('hidden_pass_rate', 0):.2%} |")
            lines.append(f"| Avg invalid actions | {agg.get('avg_invalid_actions', 0):.2f} |")
            lines.append(f"| Avg invalid edits | {agg.get('avg_invalid_edits', 0):.2f} |")
            lines.append(f"| Avg regressions | {agg.get('avg_regressions', 0):.2f} |")
            lines.append(f"| Avg steps | {agg.get('avg_steps', 0):.2f} |")
            lines.append(f"| Avg read calls | {agg.get('avg_read_calls', 0):.2f} |")
            lines.append(f"| Avg search calls | {agg.get('avg_search_calls', 0):.2f} |")
            lines.append(f"| Avg edit calls | {agg.get('avg_edit_calls', 0):.2f} |")
            lines.append(f"| Avg test calls | {agg.get('avg_test_calls', 0):.2f} |")
            lines.append(f"| Submit-before-test rate | {agg.get('submit_before_test_rate', 0):.2%} |")
            lines.append(f"| Avg guardrail violations | {agg.get('avg_guardrail_violations', 0):.2f} |")
            lines.append(f"| Avg repeated test call rate | {agg.get('avg_repeated_test_call_rate', 0):.2%} |")
            lines.append(f"| Avg patch modified lines | {agg.get('avg_patch_modified_lines', 0):.1f} |")
            lines.append(f"| Avg patch modified files | {agg.get('avg_patch_modified_files', 0):.1f} |")
            if "public_private_gap" in agg:
                lines.append(f"| Public-private gap | {agg['public_private_gap']:+.2%} |")
            if "public_hidden_gap" in agg:
                lines.append(f"| Public-hidden gap | {agg['public_hidden_gap']:+.2%} |")
            lines.append("")
        else:
            lines.append("No episodes to summarize (all filtered out).")
            lines.append("")

    report = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        logger.info("Report written to %s", output_path)

    return report


def main() -> None:
    args = parse_args()

    input_results: list[dict] = []
    for input_str in args.inputs:
        input_dir = Path(input_str)
        if not input_dir.exists():
            logger.warning("Input directory not found: %s", input_dir)
            continue

        all_metrics = load_metrics_from_dir(input_dir)
        filtered = filter_metrics(all_metrics, args.include_smoke_tests)
        agg = compute_aggregate(filtered)

        # Try to load additional info from summary.json
        summary = load_summary_from_dir(input_dir)

        input_results.append({
            "input_dir": str(input_dir),
            "total_metrics": len(all_metrics),
            "filtered_metrics": len(filtered),
            "aggregate": agg,
            "policy_type": summary.get("policy_type", "unknown") if summary else (filtered[0].get("policy_type", "unknown") if filtered else "unknown"),
            "method_name": summary.get("method_name", "react") if summary else (filtered[0].get("method_name", "react") if filtered else "react"),
            "eval_mode": summary.get("eval_mode", "unknown") if summary else "unknown",
        })

    output_path = Path(args.output) if args.output else Path("reports/react_baseline.md")
    report = format_markdown_report(input_results, output_path, title=args.title)
    print(report)


if __name__ == "__main__":
    main()
