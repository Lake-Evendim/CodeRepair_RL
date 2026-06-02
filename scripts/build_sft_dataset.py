#!/usr/bin/env python3
"""Build SFT dataset from train split gold patches.

SFT supervised targets can ONLY come from benchmarks/train metadata.gold_patch.
This script rejects --source-split validation and --source-split test at both
function and CLI level.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from pathlib import Path

from minirepair.data.trajectory_builder import build_sft_samples_from_task

logger = logging.getLogger(__name__)

ALLOWED_SPLITS = {"train"}


def build_sft_dataset(
    benchmark_root: Path,
    source_split: str,
    output_train: Path,
    output_dev: Path,
    dev_fraction: float = 0.1,
    seed: int = 42,
) -> dict[str, int]:
    """Build SFT dataset from the specified split.

    Args:
        benchmark_root: Root benchmarks/ directory.
        source_split: Which split to use. Only "train" is allowed.
        output_train: Output path for training JSONL.
        output_dev: Output path for dev JSONL.
        dev_fraction: Fraction of data to use for dev set.
        seed: Random seed.

    Returns:
        Dict with counts: {"train": N, "dev": M, "total": N+M}.

    Raises:
        ValueError: If source_split is not "train".
    """
    # Hard reject validation/test at function level
    if source_split not in ALLOWED_SPLITS:
        raise ValueError(
            f"source_split must be one of {ALLOWED_SPLITS}, got '{source_split}'. "
            "SFT supervised targets can only come from train split gold_patch."
        )

    split_path = benchmark_root / source_split
    if not split_path.exists():
        raise FileNotFoundError(f"Split directory not found: {split_path}")

    task_dirs = sorted(
        d for d in split_path.iterdir()
        if d.is_dir() and (d / "metadata.json").exists()
    )
    logger.info("Found %d tasks in %s", len(task_dirs), split_path)

    rng = random.Random(seed)
    all_samples: list[dict] = []

    for i, task_path in enumerate(task_dirs):
        logger.info("[%d/%d] Building SFT samples for %s", i + 1, len(task_dirs), task_path.name)
        try:
            samples = build_sft_samples_from_task(task_path, rng=rng)
            all_samples.extend(samples)
        except Exception:
            logger.exception("Failed to build samples for %s", task_path.name)

    # Shuffle and split
    rng.shuffle(all_samples)
    dev_count = max(1, int(len(all_samples) * dev_fraction))
    dev_samples = all_samples[:dev_count]
    train_samples = all_samples[dev_count:]

    # Write outputs
    output_train.parent.mkdir(parents=True, exist_ok=True)
    output_dev.parent.mkdir(parents=True, exist_ok=True)

    with open(output_train, "w", encoding="utf-8") as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    with open(output_dev, "w", encoding="utf-8") as f:
        for sample in dev_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    logger.info("Wrote %d train samples to %s", len(train_samples), output_train)
    logger.info("Wrote %d dev samples to %s", len(dev_samples), output_dev)

    return {"train": len(train_samples), "dev": len(dev_samples), "total": len(all_samples)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build SFT dataset from train split gold patches")
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        required=True,
        help="Root benchmarks/ directory",
    )
    parser.add_argument(
        "--source-split",
        type=str,
        required=True,
        choices=["train"],
        help="Source split (only 'train' is allowed)",
    )
    parser.add_argument(
        "--dev-fraction",
        type=float,
        default=0.1,
        help="Fraction of data for dev set (default: 0.1)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument(
        "--output-train",
        type=Path,
        required=True,
        help="Output path for training JSONL",
    )
    parser.add_argument(
        "--output-dev",
        type=Path,
        required=True,
        help="Output path for dev JSONL",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # CLI-level rejection (argparse choices already enforces this, but be explicit)
    if args.source_split not in ALLOWED_SPLITS:
        print(f"ERROR: --source-split must be 'train', got '{args.source_split}'", file=sys.stderr)
        sys.exit(1)

    counts = build_sft_dataset(
        benchmark_root=args.benchmark_root,
        source_split=args.source_split,
        output_train=args.output_train,
        output_dev=args.output_dev,
        dev_fraction=args.dev_fraction,
        seed=args.seed,
    )
    print(f"Dataset built: {counts}")


if __name__ == "__main__":
    main()
