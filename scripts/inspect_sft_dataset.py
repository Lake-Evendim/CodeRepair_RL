#!/usr/bin/env python3
"""Inspect SFT dataset samples for quality checking."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect_dataset(input_path: Path, num_samples: int = 5) -> None:
    """Print the first N samples from an SFT JSONL file."""
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            sample = json.loads(line)
            print(f"=== Sample {i + 1} ===")
            messages = sample.get("messages", [])
            for msg in messages:
                role = msg.get("role", "?")
                content = msg.get("content", "")
                print(f"[{role}] {content[:300]}{'...' if len(content) > 300 else ''}")
            meta = sample.get("metadata", {})
            print(f"metadata: {json.dumps(meta, ensure_ascii=False)}")
            print()

    # Count total
    with open(input_path, "r", encoding="utf-8") as f:
        total = sum(1 for _ in f)
    print(f"Total samples in file: {total}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect SFT dataset samples")
    parser.add_argument("--input", type=Path, required=True, help="Input JSONL file")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to show")
    args = parser.parse_args()

    inspect_dataset(args.input, args.num_samples)


if __name__ == "__main__":
    main()
