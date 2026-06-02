#!/usr/bin/env python3
"""CLI entry point for SFT training."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="SFT training for MiniRepair-RL")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/sft.yaml"),
        help="Path to SFT config YAML (default: configs/sft.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load only a few samples and run 1-2 steps for validation",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory from config",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if args.output_dir:
        config["output_dir"] = args.output_dir

    logger = logging.getLogger(__name__)
    logger.info("Config: %s", config)

    # Import and run training
    from minirepair.training.train_sft import train_sft

    output_path = train_sft(config, dry_run=args.dry_run)
    print(f"SFT training complete. Adapter saved to: {output_path}")


if __name__ == "__main__":
    main()
