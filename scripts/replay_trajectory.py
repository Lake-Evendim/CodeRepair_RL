"""Replay a trajectory JSONL file through CodeRepairEnv."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from minirepair.env.code_repair_env import CodeRepairEnv  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a trajectory")
    parser.add_argument("--trajectory", required=True, help="Path to trajectory JSONL file")
    parser.add_argument("--task", required=True, help="Path to the original task directory")
    args = parser.parse_args()

    traj_path = Path(args.trajectory)
    task_path = Path(args.task)

    if not traj_path.exists():
        print(f"ERROR: trajectory file not found: {traj_path}")
        return 1
    if not task_path.exists():
        print(f"ERROR: task directory not found: {task_path}")
        return 1

    # Load trajectory
    entries = []
    for line in traj_path.read_text().strip().split("\n"):
        if line.strip():
            entries.append(json.loads(line))

    if not entries:
        print("ERROR: trajectory is empty")
        return 1

    print(f"Replaying {len(entries)} steps from {traj_path}")
    print(f"Task: {task_path}")
    print("=" * 60)

    # Replay
    env = CodeRepairEnv()
    env.reset(task_path)

    for i, entry in enumerate(entries):
        action = entry["action"]
        print(f"\n--- Step {i} ---")
        print(f"Action: {json.dumps(action, ensure_ascii=False)}")

        obs, done, info = env.step(action)
        print(f"Status: {obs['status']}")
        if obs.get("content"):
            content_preview = obs["content"][:200]
            print(f"Content: {content_preview}...")
        if obs.get("error"):
            print(f"Error: {obs['error']}")

        # Compare with original observation
        orig_obs = entry.get("observation", {})
        if orig_obs.get("status") != obs.get("status"):
            print(f"WARNING: status mismatch! original={orig_obs.get('status')}, replay={obs.get('status')}")

        if done:
            print(f"\nDone! Reason: {info.get('termination_reason', 'unknown')}")
            break

    env.close()
    print("\n" + "=" * 60)
    print("Replay complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
