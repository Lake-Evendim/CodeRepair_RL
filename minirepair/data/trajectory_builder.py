"""Build SFT training samples by replaying gold action sequences through CodeRepairEnv.

Each SFT sample is one step: system + user (safe state) + assistant (target action).
Gold patch old_text/new_text appears ONLY in the assistant target, never in prompts.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

from minirepair.data.task_schema import TaskMetadata
from minirepair.env.code_repair_env import CodeRepairEnv

logger = logging.getLogger(__name__)

SYSTEM_PROMPTS = [
    "You are a code repair agent. Given a Python repository with a bug, fix it using the available tools. Respond with ONLY a single JSON tool call.",
    "You are a debugging assistant. A Python codebase has a bug. Use the tools to find and fix it. Your response must be exactly one JSON tool call.",
    "You are a code repair agent. Your task is to locate and fix a bug in a Python repository. Always respond with a single JSON object for a tool call.",
]

READ_THOUGHTS = [
    "Let me read the buggy file to understand the issue.",
    "I'll start by reading the source file to see what's wrong.",
    "First, let me look at the file that contains the bug.",
]

SEARCH_THOUGHTS = [
    "Let me search for the relevant function first.",
    "I'll search the codebase to locate the buggy code.",
]

EDIT_THOUGHTS = [
    "Now I'll apply the fix.",
    "I can see the bug. Let me edit the file to fix it.",
    "I'll make the necessary code change.",
]

TEST_THOUGHTS = [
    "Let me run the tests to verify the fix.",
    "I'll run the public tests to check if my fix works.",
]

SUBMIT_THOUGHTS = [
    "The tests pass. I'll submit my fix.",
    "All tests are green. Submitting the solution.",
]


def _pick(items: list[str], rng: random.Random) -> str:
    return rng.choice(items)


def build_gold_action_sequence(metadata: TaskMetadata) -> list[dict[str, Any]]:
    """Build the gold action sequence for a task.

    Returns a list of action dicts that can be passed to env.step().
    The sequence is: read_file -> edit_file -> run_tests -> submit.
    """
    gp = metadata.gold_patch
    return [
        {"tool": "read_file", "arguments": {"path": gp.file_path}},
        {"tool": "edit_file", "arguments": {"path": gp.file_path, "old_text": gp.old_text, "new_text": gp.new_text}},
        {"tool": "run_tests", "arguments": {}},
        {"tool": "submit", "arguments": {}},
    ]


def build_search_first_sequence(metadata: TaskMetadata) -> list[dict[str, Any]]:
    """Alternative sequence: search_code -> read_file -> edit_file -> run_tests -> submit."""
    gp = metadata.gold_patch
    # Extract function name or first word from old_text for search
    query = gp.old_text.strip().split("\n")[0].strip()
    # Use first meaningful token
    tokens = query.split()
    query = tokens[0] if tokens else "def"
    return [
        {"tool": "search_code", "arguments": {"query": query}},
        {"tool": "read_file", "arguments": {"path": gp.file_path}},
        {"tool": "edit_file", "arguments": {"path": gp.file_path, "old_text": gp.old_text, "new_text": gp.new_text}},
        {"tool": "run_tests", "arguments": {}},
        {"tool": "submit", "arguments": {}},
    ]


def _thought_for_action(action_dict: dict[str, Any], rng: random.Random) -> str:
    """Pick a thought string for the given action (used in user prompt metadata)."""
    tool = action_dict.get("tool", "")
    if tool == "read_file":
        return _pick(READ_THOUGHTS, rng)
    if tool == "search_code":
        return _pick(SEARCH_THOUGHTS, rng)
    if tool == "edit_file":
        return _pick(EDIT_THOUGHTS, rng)
    if tool == "run_tests":
        return _pick(TEST_THOUGHTS, rng)
    if tool == "submit":
        return _pick(SUBMIT_THOUGHTS, rng)
    return ""


def _build_user_prompt(state: dict, history: list[dict], thought: str) -> str:
    """Build the user prompt for one SFT step.

    Contains safe state info and action history. No private/hidden leakage.
    """
    parts = []
    parts.append("## Task Information")
    parts.append(f"- Task ID: {state.get('task_id', 'unknown')}")
    parts.append(f"- Repository type: {state.get('repo_type', 'unknown')}")
    parts.append(f"- Bug type: {state.get('bug_type', 'unknown')}")
    parts.append(f"- Bug description: {state.get('bug_description', 'unknown')}")
    parts.append(f"- Step: {state.get('step_count', 0)} / {state.get('max_steps', 6)}")
    parts.append(f"- Edits used: {state.get('edit_count', 0)} / {state.get('max_edits', 2)}")
    parts.append(f"- Tests used: {state.get('test_count', 0)} / {state.get('max_tests', 2)}")
    parts.append("")

    if history:
        parts.append("## Previous Actions")
        for entry in history:
            act = entry.get("action", {})
            obs = entry.get("observation", {})
            if isinstance(act, dict):
                parts.append(f"Action: {json.dumps(act, ensure_ascii=False)}")
            else:
                parts.append(f"Action (invalid): {act}")
            parts.append(f"Status: {obs.get('status', 'unknown')}")
            if obs.get("content"):
                content = obs["content"]
                if len(content) > 500:
                    content = content[:500] + "\n... (truncated)"
                parts.append(f"Output:\n{content}")
            if obs.get("error"):
                parts.append(f"Error: {obs['error']}")
            parts.append("")
    else:
        parts.append("## No previous actions yet. Start by reading the buggy file.")
        parts.append("")

    if thought:
        parts.append(f"## Thought\n{thought}")
        parts.append("")

    parts.append("## Your Action (respond with a single JSON tool call):")
    return "\n".join(parts)


def build_sft_samples_from_task(
    task_path: Path,
    rng: random.Random | None = None,
    include_search_first: bool = True,
) -> list[dict[str, Any]]:
    """Build SFT samples for a single task by replaying gold actions through the env.

    Each step produces one sample:
    {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}

    Gold patch old_text/new_text only appears in the assistant target action.

    Args:
        task_path: Path to the task directory (must contain metadata.json and repo/).
        rng: Random generator for template selection.
        include_search_first: Whether to also generate a search-first variant.

    Returns:
        List of SFT sample dicts.
    """
    if rng is None:
        rng = random.Random(42)

    # Load metadata
    metadata_path = task_path / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found in {task_path}")
    metadata = TaskMetadata(**json.loads(metadata_path.read_text()))

    samples: list[dict[str, Any]] = []

    # Build action sequences
    sequences = [build_gold_action_sequence(metadata)]
    if include_search_first:
        sequences.append(build_search_first_sequence(metadata))

    for action_sequence in sequences:
        env = CodeRepairEnv()
        try:
            state = env.reset(task_path)
            history: list[dict] = []

            for action_dict in action_sequence:
                # Build user prompt from safe state
                thought = _thought_for_action(action_dict, rng)
                user_prompt = _build_user_prompt(state, history, thought)
                system_prompt = _pick(SYSTEM_PROMPTS, rng)

                # Target action is pure JSON
                target_action = json.dumps(action_dict, ensure_ascii=False)

                # Build SFT sample
                sample = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": target_action},
                    ],
                    "metadata": {
                        "task_id": metadata.task_id,
                        "split": metadata.split,
                        "tool": action_dict["tool"],
                        "variant": "search_first" if action_dict["tool"] == "search_code" else "standard",
                    },
                }
                samples.append(sample)

                # Execute the action in the env to get real observation
                obs_dict, done, info = env.step(action_dict)

                # Update history with real observation
                history.append({
                    "action": action_dict,
                    "observation": obs_dict,
                })

                if done:
                    break

        finally:
            env.close()

    return samples
