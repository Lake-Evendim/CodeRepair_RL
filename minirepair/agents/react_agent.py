"""ReAct agent: prompt construction, policy interface, and episode loop."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from minirepair.agents.action_parser import extract_action_from_llm_output
from minirepair.env.action_schema import Action
from minirepair.env.code_repair_env import CodeRepairEnv

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a code repair agent. You are given a Python repository with a bug. Your goal is to fix the bug by using the available tools.

## Available Tools

You must respond with a single JSON object specifying a tool call:

1. read_file: Read a file from the repository.
   {"tool": "read_file", "arguments": {"path": "src/filename.py"}}

2. search_code: Search for a pattern in src/ directory.
   {"tool": "search_code", "arguments": {"query": "function_name"}}

3. edit_file: Apply a search-replace edit to a single file. old_text must appear exactly once in the file, and the edit must modify at most 5 lines.
   {"tool": "edit_file", "arguments": {"path": "src/filename.py", "old_text": "exact old code", "new_text": "replacement code"}}

4. run_tests: Run the public tests.
   {"tool": "run_tests", "arguments": {}}

5. submit: Submit your fix when you believe the bug is fixed.
   {"tool": "submit", "arguments": {}}

## Rules
- Respond with ONLY a single JSON tool call, nothing else.
- You can read files and search code to understand the bug before editing.
- You can run tests to verify your fix.
- You have a limited number of steps, edits, and test runs.
- Do NOT modify test files or configuration files.
"""


def build_react_prompt(state: dict, history: list[dict]) -> str:
    """Build the full ReAct prompt for the current step.

    Args:
        state: Current env state from render_state().
        history: List of previous step dicts (action, observation).

    Returns:
        Full prompt string to send to the policy.
    """
    parts = [SYSTEM_PROMPT, ""]

    # Task context (no leakage of private/hidden info)
    parts.append("## Task Information")
    parts.append(f"- Task ID: {state.get('task_id', 'unknown')}")
    parts.append(f"- Repository type: {state.get('repo_type', 'unknown')}")
    parts.append(f"- Bug type: {state.get('bug_type', 'unknown')}")
    parts.append(f"- Bug description: {state.get('bug_description', 'unknown')}")
    parts.append(f"- Step: {state.get('step_count', 0)} / {state.get('max_steps', 6)}")
    parts.append(f"- Edits used: {state.get('edit_count', 0)} / {state.get('max_edits', 2)}")
    parts.append(f"- Tests used: {state.get('test_count', 0)} / {state.get('max_tests', 2)}")
    parts.append("")

    # History
    if history:
        parts.append("## Previous Actions")
        for entry in history:
            action = entry.get("action", {})
            obs = entry.get("observation", {})
            if isinstance(action, dict):
                parts.append(f"Action: {json.dumps(action, ensure_ascii=False)}")
            else:
                parts.append(f"Action (invalid): {action}")
            # Only include safe observation fields
            parts.append(f"Status: {obs.get('status', 'unknown')}")
            if obs.get("content"):
                # Truncate long outputs
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

    parts.append("## Your Action (respond with a single JSON tool call):")
    return "\n".join(parts)


class Policy(ABC):
    """Abstract base class for agent policies."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a raw response string given a prompt.

        The response should contain a JSON tool call.
        """

    @property
    @abstractmethod
    def policy_type(self) -> str:
        """Return the policy type identifier (e.g. 'mock', 'qwen_base')."""

    @property
    def uses_gold_patch(self) -> bool:
        """Whether this policy uses gold patch information."""
        return False


class MockPolicy(Policy):
    """Smoke-test policy that replays the gold action sequence.

    Excluded from main results. Only for pipeline validation.
    """

    def __init__(self, metadata: dict[str, Any]) -> None:
        self._metadata = metadata
        self._step_index = 0

    def generate(self, prompt: str) -> str:
        gold = self._metadata.get("gold_patch", {})
        file_path = gold.get("path", gold.get("file_path", "src/unknown.py"))
        old_text = gold.get("old_text", "")
        new_text = gold.get("new_text", "")

        sequence = [
            {"tool": "read_file", "arguments": {"path": file_path}},
            {"tool": "edit_file", "arguments": {"path": file_path, "old_text": old_text, "new_text": new_text}},
            {"tool": "run_tests", "arguments": {}},
            {"tool": "submit", "arguments": {}},
        ]

        idx = min(self._step_index, len(sequence) - 1)
        self._step_index += 1
        return json.dumps(sequence[idx])

    @property
    def policy_type(self) -> str:
        return "mock"

    @property
    def uses_gold_patch(self) -> bool:
        return True


class LLMPolicy(Policy):
    """Policy that calls a HuggingFace causal LM."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        do_sample: bool = False,
        device: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature
        self._do_sample = do_sample
        self._device = device
        self._model = None
        self._tokenizer = None

    def _load_model(self) -> None:
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        from minirepair.training.train_sft import resolve_model_path

        model_path = resolve_model_path(self._model_name)
        logger.info("Loading model from: %s", model_path)
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True
        )
        device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
        )
        if device == "cpu":
            self._model = self._model.to(device)
        self._model.eval()
        logger.info("Model loaded on %s", device)

    def generate(self, prompt: str) -> str:
        self._load_model()
        assert self._model is not None and self._tokenizer is not None

        import torch

        # Build chat messages for Qwen
        messages = [{"role": "user", "content": prompt}]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self._model.device)
        attention_mask = inputs["attention_mask"].to(self._model.device)

        with torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=self._max_new_tokens,
                do_sample=self._do_sample,
                temperature=self._temperature if self._do_sample else None,
                top_p=0.95 if self._do_sample else None,
            )

        # Decode only the generated tokens
        new_tokens = output_ids[0, input_ids.shape[1] :]
        raw_output = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        return raw_output

    @property
    def policy_type(self) -> str:
        return "qwen_base"


def run_episode(
    env: CodeRepairEnv,
    task_path: Path,
    policy: Policy,
) -> dict[str, Any]:
    """Run a single episode with the given policy.

    Returns:
        Dict with keys: task_id, policy_type, trajectory, raw_outputs,
        parsed_actions, final_state.
    """
    state = env.reset(task_path)
    history: list[dict] = []
    raw_outputs: list[str] = []
    parsed_actions: list[dict | None] = []
    done = False

    while not done:
        prompt = build_react_prompt(state, history)
        raw_output = policy.generate(prompt)
        raw_outputs.append(raw_output)

        # Parse the action (returns Action or ParseError)
        action_result = extract_action_from_llm_output(raw_output)
        if isinstance(action_result, Action):
            action_dict = action_result.model_dump()
            parsed_actions.append(action_dict)
            step_result = env.step(action_dict)
        else:
            # Invalid action - pass raw string to env, it will count as invalid
            parsed_actions.append(None)
            step_result = env.step(raw_output)

        obs_dict, done, info = step_result

        # Record in history
        history.append({
            "action": action_dict if isinstance(action_result, Action) else raw_output,
            "observation": obs_dict,
        })

        state = env.render_state()

    # Enrich trajectory entries with raw_output and parsed_action
    enriched_trajectory = []
    for i, step in enumerate(env.trajectory):
        entry = dict(step)
        entry["raw_output"] = raw_outputs[i] if i < len(raw_outputs) else None
        entry["parsed_action"] = parsed_actions[i] if i < len(parsed_actions) else None
        enriched_trajectory.append(entry)

    return {
        "task_id": env.metadata.task_id if env.metadata else "unknown",
        "policy_type": policy.policy_type,
        "uses_gold_patch": policy.uses_gold_patch,
        "trajectory": enriched_trajectory,
        "raw_outputs": raw_outputs,
        "parsed_actions": parsed_actions,
        "final_state": state,
    }
