#!/usr/bin/env python3
"""Unified evaluation CLI for MiniRepair-RL.

Supports methods: react, sft (Phase 6). rl_sparse/rl_dense are reserved for Phase 7/8.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from minirepair.agents.react_agent import LLMPolicy, Policy
from minirepair.evaluation.evaluator import Evaluator
from minirepair.evaluation.metrics import EvalMode

logger = logging.getLogger(__name__)

SUPPORTED_METHODS = {"react", "sft", "rl_sparse", "rl_dense"}


def build_policy(
    method: str,
    model_name: str | None = None,
    adapter_path: str | None = None,
    device: str | None = None,
) -> Policy:
    """Construct the appropriate Policy for the given method."""
    if method == "react":
        return LLMPolicy(
            model_name=model_name or "Qwen/Qwen2.5-Coder-1.5B-Instruct",
            device=device,
        )
    elif method == "sft":
        if not adapter_path:
            raise ValueError("--adapter is required for method 'sft'")
        from minirepair.agents.sft_policy import SFTPolicy

        return SFTPolicy(
            base_model_name=model_name or "Qwen/Qwen2.5-Coder-1.5B-Instruct",
            adapter_path=adapter_path,
            device=device,
        )
    elif method in ("rl_sparse", "rl_dense"):
        if not adapter_path:
            raise ValueError(f"--adapter is required for method '{method}'")
        from minirepair.agents.rl_policy import RLPolicy

        return RLPolicy(
            base_model_name=model_name or "Qwen/Qwen2.5-Coder-1.5B-Instruct",
            adapter_path=adapter_path,
            device=device,
            policy_type=f"{method}_qwen_lora",
        )
    else:
        raise ValueError(f"Unknown method: {method}. Supported: {SUPPORTED_METHODS}")


def resolve_split_path(benchmark_root: Path, split: str) -> Path:
    """Get the path to a split directory."""
    split_path = benchmark_root / split
    if not split_path.exists():
        raise FileNotFoundError(f"Split directory not found: {split_path}")
    return split_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified evaluation CLI for MiniRepair-RL")
    parser.add_argument(
        "--method",
        type=str,
        required=True,
        choices=sorted(SUPPORTED_METHODS),
        help="Evaluation method",
    )
    parser.add_argument(
        "--split",
        type=str,
        required=True,
        choices=["train", "validation", "test"],
        help="Dataset split to evaluate",
    )
    parser.add_argument(
        "--eval-mode",
        type=str,
        required=True,
        choices=["train_reward", "validation_selection", "final_test"],
        help="Evaluation mode controlling test access",
    )
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("benchmarks"),
        help="Root benchmarks directory (default: benchmarks)",
    )
    parser.add_argument("--policy", type=str, default=None, help="Policy type (for react)")
    parser.add_argument("--model", type=str, default=None, help="Model name or path")
    parser.add_argument("--adapter", type=str, default=None, help="LoRA adapter path")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda/cpu)")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for trajectories and metrics",
    )
    parser.add_argument("--max-tasks", type=int, default=None, help="Max tasks to evaluate")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Validate eval mode / split combinations
    eval_mode = EvalMode(args.eval_mode)
    if eval_mode == EvalMode.FINAL_TEST and args.split != "test":
        print(f"ERROR: final_test eval mode requires --split test, got {args.split}", file=sys.stderr)
        sys.exit(1)
    if eval_mode == EvalMode.VALIDATION_SELECTION and args.split not in ("train", "validation"):
        print("ERROR: validation_selection requires --split train or validation", file=sys.stderr)
        sys.exit(1)

    # Build policy
    try:
        policy = build_policy(
            method=args.method,
            model_name=args.model,
            adapter_path=args.adapter,
            device=args.device,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Resolve split path
    split_path = resolve_split_path(args.benchmark_root, args.split)

    # Build evaluator
    evaluator = Evaluator(
        policy=policy,
        eval_mode=eval_mode,
        method_name=args.method,
        trajectory_dir=args.output,
    )

    # Run evaluation
    logger.info("Evaluating %s on %s split (mode=%s)", args.method, args.split, args.eval_mode)
    result = evaluator.evaluate_split(split_path, max_tasks=args.max_tasks)

    # Print summary
    agg = result["aggregate"]
    print(f"\n=== {args.method} on {args.split} ({args.eval_mode}) ===")
    print(f"Tasks evaluated: {result['num_tasks']}")
    print(f"Public pass rate: {agg.get('public_pass_rate', 0):.3f}")
    if agg.get("private_pass_rate") is not None:
        print(f"Private pass rate: {agg.get('private_pass_rate', 0):.3f}")
    if agg.get("hidden_pass_rate") is not None:
        print(f"Hidden pass rate: {agg.get('hidden_pass_rate', 0):.3f}")
    print(f"Avg invalid actions: {agg.get('avg_invalid_actions', 0):.3f}")
    print(f"Avg invalid edits: {agg.get('avg_invalid_edits', 0):.3f}")
    print(f"Avg steps: {agg.get('avg_steps', 0):.3f}")
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
