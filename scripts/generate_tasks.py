"""Generate the full 130-task benchmark.

Usage: python scripts/generate_tasks.py --seed 42 --output benchmarks
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from minirepair.data.bug_catalog import get_all_variants  # noqa: E402
from minirepair.data.bug_generator import generate_task  # noqa: E402
from minirepair.data.split import assign_splits  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate full benchmark")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="benchmarks")
    parser.add_argument("--train-per-combo", type=int, default=4)
    parser.add_argument("--val-per-combo", type=int, default=1)
    parser.add_argument("--test-candidates-per-combo", type=int, default=2)
    parser.add_argument("--test-total", type=int, default=30)
    args = parser.parse_args()

    output_dir = ROOT / args.output
    variants = get_all_variants()
    print(f"Loaded {len(variants)} variants from catalog")

    # Assign splits
    splits = assign_splits(
        variants,
        train_per_combo=args.train_per_combo,
        val_per_combo=args.val_per_combo,
        test_candidates_per_combo=args.test_candidates_per_combo,
        test_total=args.test_total,
        seed=args.seed,
    )

    for name, tasks in splits.items():
        print(f"  {name}: {len(tasks)} tasks")

    total = sum(len(v) for v in splits.values())
    print(f"  total: {total} tasks")

    # Clean output directories
    for split_name in ("train", "validation", "test"):
        split_dir = output_dir / split_name
        if split_dir.exists():
            shutil.rmtree(split_dir)

    # Generate tasks
    for split_name, tasks in splits.items():
        split_dir = output_dir / split_name
        for i, variant in enumerate(tasks):
            task_id = f"task_{i + 1:04d}"
            generate_task(variant, task_id, split_name, split_dir)

        print(f"Generated {len(tasks)} tasks in {split_dir}")

    # Print distribution
    print("\nDistribution:")
    for split_name, tasks in splits.items():
        combo_counts = Counter((v.repo_type, v.bug_type) for v in tasks)
        print(f"  {split_name}:")
        for k, v in sorted(combo_counts.items()):
            print(f"    {k}: {v}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
