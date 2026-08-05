#!/usr/bin/env python3
"""Export RL training curves as PNG images."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def plot_curves(curves_path: Path, output_dir: Path, label: str) -> None:
    """Plot training curves from a curves.json file."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = json.loads(curves_path.read_text())
    epochs = data["epoch"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(f"RL {label} Training Curves", fontsize=14)

    # Loss
    ax = axes[0, 0]
    ax.plot(epochs, data["loss"], "b-o", linewidth=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Policy Gradient Loss")
    ax.grid(True, alpha=0.3)

    # Average Return
    ax = axes[0, 1]
    ax.plot(epochs, data["avg_return"], "g-o", linewidth=2, label="Avg Return")
    ax.plot(epochs, data["baseline"], "r--s", linewidth=1.5, label="Baseline")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Return")
    ax.set_title("Average Return vs Baseline")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Validation Private Pass Rate
    ax = axes[1, 0]
    ax.plot(epochs, data["val_private_pass"], "m-D", linewidth=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Pass Rate")
    ax.set_title("Validation Private Pass Rate")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)

    # Advantage (return - baseline)
    ax = axes[1, 1]
    advantage = [r - b for r, b in zip(data["avg_return"], data["baseline"])]
    ax.bar(epochs, advantage, color=["green" if a >= 0 else "red" for a in advantage], alpha=0.7)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Advantage")
    ax.set_title("Advantage (Return - Baseline)")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"rl_{label.lower().replace(' ', '_')}_curves.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main() -> None:
    output_dir = Path("reports")

    adapters = [
        ("outputs/rl_sparse_adapter_trained/curves.json", "Sparse"),
        ("outputs/rl_dense_adapter_trained/curves.json", "Dense"),
    ]

    for curves_file, label in adapters:
        path = Path(curves_file)
        if path.exists():
            plot_curves(path, output_dir, label)
        else:
            print(f"Warning: {curves_file} not found, skipping")


if __name__ == "__main__":
    main()
