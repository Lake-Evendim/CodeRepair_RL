#!/usr/bin/env python3
"""Train RL agent with sparse reward (REINFORCE + moving-average baseline)."""

from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def _import_common():
    common_path = Path(__file__).resolve().parent / "_train_rl_common.py"
    spec = importlib.util.spec_from_file_location("_train_rl_common", common_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    parser = argparse.ArgumentParser(description="RL training with sparse reward")
    parser.add_argument("--config", type=Path, default=Path("configs/rl_sparse.yaml"))
    parser.add_argument("--dry-run", action="store_true", help="Quick test run")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = yaml.safe_load(args.config.read_text())

    common = _import_common()
    common.run_rl_training(config, reward_mode="sparse", dry_run=args.dry_run)


if __name__ == "__main__":
    main()
