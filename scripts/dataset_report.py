"""Generate dataset quality report for the benchmark.

Usage: python scripts/dataset_report.py --input benchmarks --output reports/dataset_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _count_tests(task_dir: Path, test_dir: str) -> int:
    """Count test functions in a test directory."""
    d = task_dir / "repo" / test_dir
    if not d.exists():
        return 0
    count = 0
    for f in d.rglob("*.py"):
        if f.name.startswith("test_"):
            content = f.read_text()
            count += content.count("def test_")
    return count


def _load_tasks(split_dir: Path) -> list[dict]:
    """Load all task metadata from a split directory."""
    tasks = []
    if not split_dir.exists():
        return tasks
    for task_dir in sorted(split_dir.iterdir()):
        meta_path = task_dir / "metadata.json"
        if meta_path.exists():
            tasks.append(json.loads(meta_path.read_text()))
    return tasks


def generate_report(benchmarks_dir: Path, output_path: Path) -> None:
    """Generate the dataset quality report."""
    lines: list[str] = []
    lines.append("# Dataset Quality Report\n")

    all_tasks: dict[str, list[dict]] = {}
    all_signatures: dict[str, list[str]] = {}
    all_patches: dict[str, list[tuple[str, str]]] = {}
    all_descriptions: dict[str, list[str]] = {}

    for split_name in ("train", "validation", "test"):
        split_dir = benchmarks_dir / split_name
        tasks = _load_tasks(split_dir)
        all_tasks[split_name] = tasks

        if not tasks:
            continue

        lines.append(f"## {split_name.capitalize()} Split\n")
        lines.append(f"**Tasks:** {len(tasks)}\n")

        # Repo distribution
        repo_counts = Counter(t["repo_type"] for t in tasks)
        lines.append("### Repo Distribution\n")
        lines.append("| Repo | Count |")
        lines.append("|------|-------|")
        for repo, count in sorted(repo_counts.items()):
            lines.append(f"| {repo} | {count} |")
        lines.append("")

        # Bug type distribution
        bug_counts = Counter(t["bug_type"] for t in tasks)
        lines.append("### Bug Type Distribution\n")
        lines.append("| Bug Type | Count |")
        lines.append("|----------|-------|")
        for bt, count in sorted(bug_counts.items()):
            lines.append(f"| {bt} | {count} |")
        lines.append("")

        # Function distribution
        func_map: Counter[str] = Counter()
        for t in tasks:
            desc = t.get("bug_description", "")
            func_map[desc.split(" ")[0] if desc else "unknown"] += 1

        # Test counts
        lines.append("### Test Counts\n")
        lines.append("| Task | Public | Private | Quality/Hidden |")
        lines.append("|------|--------|---------|----------------|")
        for t in tasks[:5]:  # Show first 5
            task_dir = split_dir / t["task_id"]
            pub = _count_tests(task_dir, "tests")
            priv = _count_tests(task_dir, "tests_private")
            if split_name in ("train", "validation"):
                extra = _count_tests(task_dir, "tests_quality_holdout")
                extra_label = "quality"
            else:
                extra = _count_tests(task_dir, "tests_hidden")
                extra_label = "hidden"
            lines.append(f"| {t['task_id']} | {pub} | {priv} | {extra} ({extra_label}) |")
        if len(tasks) > 5:
            lines.append("| ... | ... | ... | ... |")
        lines.append("")

        # Collect for cross-split analysis
        signatures = []
        patches = []
        descriptions = []
        for t in tasks:
            patch = t.get("gold_patch", {})
            sig = f"{t['repo_type']}_{t['function_name'] if 'function_name' in t else ''}_{t['bug_type']}"
            signatures.append(sig)
            patches.append((patch.get("old_text", ""), patch.get("new_text", "")))
            descriptions.append(t.get("bug_description", ""))

        all_signatures[split_name] = signatures
        all_patches[split_name] = patches
        all_descriptions[split_name] = descriptions

    # Cross-split dedup analysis
    lines.append("## Cross-Split Deduplication Analysis\n")

    # Check gold_patch pair overlap
    train_patches = set(all_patches.get("train", []))
    val_patches = set(all_patches.get("validation", []))
    test_patches = set(all_patches.get("test", []))

    train_val_overlap = train_patches & val_patches
    train_test_overlap = train_patches & test_patches
    val_test_overlap = val_patches & test_patches

    lines.append("### Gold Patch Pair Overlap\n")
    lines.append("| Comparison | Overlap |")
    lines.append("|------------|---------|")
    lines.append(f"| train ∩ validation | {len(train_val_overlap)} |")
    lines.append(f"| train ∩ test | {len(train_test_overlap)} |")
    lines.append(f"| validation ∩ test | {len(val_test_overlap)} |")
    lines.append("")

    # Check description overlap
    train_desc = set(all_descriptions.get("train", []))
    val_desc = set(all_descriptions.get("validation", []))
    test_desc = set(all_descriptions.get("test", []))

    lines.append("### Bug Description Overlap\n")
    lines.append("| Comparison | Overlap |")
    lines.append("|------------|---------|")
    lines.append(f"| train ∩ validation | {len(train_desc & val_desc)} |")
    lines.append(f"| train ∩ test | {len(train_desc & test_desc)} |")
    lines.append(f"| validation ∩ test | {len(val_desc & test_desc)} |")
    lines.append("")

    # Summary
    lines.append("## Summary\n")
    total_tasks = sum(len(v) for v in all_tasks.values())
    lines.append(f"- **Total tasks:** {total_tasks}")
    lines.append(f"- **Train:** {len(all_tasks.get('train', []))}")
    lines.append(f"- **Validation:** {len(all_tasks.get('validation', []))}")
    lines.append(f"- **Test:** {len(all_tasks.get('test', []))}")
    lines.append(f"- **Gold patch pair duplicates across splits:** {len(train_val_overlap) + len(train_test_overlap) + len(val_test_overlap)}")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dataset quality report")
    parser.add_argument("--input", type=str, default="benchmarks")
    parser.add_argument("--output", type=str, default="reports/dataset_report.md")
    args = parser.parse_args()

    input_dir = ROOT / args.input
    output_path = ROOT / args.output

    if not input_dir.exists():
        print(f"ERROR: {input_dir} does not exist")
        return 1

    generate_report(input_dir, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
