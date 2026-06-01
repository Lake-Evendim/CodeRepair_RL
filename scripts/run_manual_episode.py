"""Run a manual episode using gold action sequence from task metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from minirepair.env.code_repair_env import CodeRepairEnv  # noqa: E402


def build_gold_actions(task_path: Path) -> list[dict]:
    """Build gold action sequence from task metadata."""
    meta = json.loads((task_path / "metadata.json").read_text())
    patch = meta["gold_patch"]
    return [
        {"tool": "read_file", "arguments": {"path": patch["file_path"]}},
        {
            "tool": "edit_file",
            "arguments": {
                "path": patch["file_path"],
                "old_text": patch["old_text"],
                "new_text": patch["new_text"],
            },
        },
        {"tool": "run_tests", "arguments": {}},
        {"tool": "submit", "arguments": {}},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a manual episode with gold actions")
    parser.add_argument("--task", required=True, help="Path to task directory")
    parser.add_argument("--output", help="Path to save trajectory JSONL")
    args = parser.parse_args()

    task_path = Path(args.task)
    if not task_path.exists():
        print(f"ERROR: task not found: {task_path}")
        return 1

    meta = json.loads((task_path / "metadata.json").read_text())
    print(f"Task: {meta['task_id']}")
    print(f"Repo: {meta['repo_type']}")
    print(f"Bug: {meta['bug_description']}")
    print("=" * 60)

    actions = build_gold_actions(task_path)

    trajectory_dir = Path(args.output) if args.output else None
    env = CodeRepairEnv(trajectory_dir=trajectory_dir)
    env.reset(task_path)

    for i, action in enumerate(actions):
        print(f"\n--- Step {i}: {action['tool']} ---")
        if action.get("arguments", {}).get("path"):
            print(f"  path: {action['arguments']['path']}")

        obs, done, info = env.step(action)

        print(f"  status: {obs['status']}")
        if obs.get("content"):
            # Show first few lines
            lines = obs["content"].split("\n")[:10]
            for line in lines:
                print(f"  | {line}")
            if len(obs["content"].split("\n")) > 10:
                print(f"  | ... ({len(obs['content'].split(chr(10)))} lines total)")
        if obs.get("error"):
            print(f"  error: {obs['error']}")

        if done:
            print(f"\nDone! Reason: {info.get('termination_reason', 'unknown')}")
            break

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Steps: {env.step_count}")
    print(f"  Edits: {env.tool_state.edit_count if env.tool_state else 0}")
    print(f"  Tests: {env.tool_state.test_count if env.tool_state else 0}")
    print(f"  Modified files: {sorted(env.modified_files)}")
    print(f"  Termination: {env.termination_reason}")

    # Verify no leakage in render_state
    state = env.render_state()
    state_str = json.dumps(state)
    if "tests_private" in state_str or "gold_patch" in state_str:
        print("\nWARNING: render_state may leak private info!")
    else:
        print("  No private info leakage detected.")

    if trajectory_dir:
        traj_file = trajectory_dir / f"{meta['task_id']}.jsonl"
        print(f"  Trajectory saved to: {traj_file}")

    env.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
