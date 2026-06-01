"""CodeRepairEnv: MDP environment wrapping the tool layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minirepair.data.task_schema import TaskMetadata
from minirepair.env.action_schema import ParseError, ToolName, parse_action
from minirepair.env.sandbox import Sandbox
from minirepair.env.tools import Observation, ToolState, execute_tool

MAX_STEPS = 6
MAX_EDITS = 2
MAX_TESTS = 2
MAX_CONSECUTIVE_INVALID = 3


class CodeRepairEnv:
    """MDP environment for code repair tasks."""

    def __init__(self, trajectory_dir: Path | None = None) -> None:
        self.trajectory_dir = trajectory_dir
        # State (reset by reset())
        self.task_path: Path | None = None
        self.metadata: TaskMetadata | None = None
        self.sandbox: Sandbox | None = None
        self.tool_state: ToolState | None = None
        self.step_count: int = 0
        self.invalid_count: int = 0
        self.done: bool = False
        self.termination_reason: str | None = None
        self.tool_history: list[dict] = []
        self.modified_files: set[str] = set()
        self.last_observation: dict | None = None
        self.trajectory: list[dict] = []
        self._trajectory_file = None

    def reset(self, task_path: str | Path) -> dict:
        """Reset environment with a new task. Returns initial render_state."""
        task_path = Path(task_path)

        # Load metadata
        metadata_path = task_path / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.json not found in {task_path}")
        self.metadata = TaskMetadata(**json.loads(metadata_path.read_text()))

        # Setup sandbox
        repo_path = task_path / "repo"
        if not repo_path.exists():
            raise FileNotFoundError(f"repo/ not found in {task_path}")

        self.task_path = task_path
        self.sandbox = Sandbox(repo_path)
        self.sandbox.__enter__()

        self.tool_state = ToolState(
            episode_edit_limit=MAX_EDITS,
            episode_test_limit=MAX_TESTS,
        )
        self.step_count = 0
        self.invalid_count = 0
        self.done = False
        self.termination_reason = None
        self.tool_history = []
        self.modified_files = set()
        self.last_observation = None
        self.trajectory = []

        # Setup trajectory logging
        if self.trajectory_dir:
            self.trajectory_dir.mkdir(parents=True, exist_ok=True)
            task_id = self.metadata.task_id
            traj_path = self.trajectory_dir / f"{task_id}.jsonl"
            self._trajectory_file = open(traj_path, "w", encoding="utf-8")
        else:
            self._trajectory_file = None

        return self.render_state()

    def step(self, action_raw: str | dict[str, Any]) -> tuple[dict, bool, dict]:
        """Execute one step. Returns (observation_dict, done, info)."""
        if self.done:
            return {"status": "error", "error": "Episode already done"}, True, {"termination_reason": self.termination_reason}

        if self.sandbox is None or self.tool_state is None:
            return {"status": "error", "error": "Environment not reset"}, True, {}

        # Parse action
        action_or_error = parse_action(action_raw)
        if isinstance(action_or_error, ParseError):
            self.invalid_count += 1
            obs_dict = {"status": "error", "error": action_or_error.error, "tool_name": "parse"}
            self._record_step(action_raw, obs_dict, False, {})
            if self.invalid_count >= MAX_CONSECUTIVE_INVALID:
                self.done = True
                self.termination_reason = "consecutive_invalid"
                return obs_dict, True, {"termination_reason": self.termination_reason}
            return obs_dict, False, {}

        action = action_or_error

        # Reset invalid count on valid action
        self.invalid_count = 0

        # Execute tool
        obs: Observation = execute_tool(self.sandbox, action, self.tool_state)
        obs_dict = {"status": obs.status, "content": obs.content, "error": obs.error, "tool_name": obs.tool_name, "info": obs.info}

        # Track modified files
        if action.tool == ToolName.EDIT_FILE and obs.status == "success" and action.arguments.path:
            self.modified_files.add(action.arguments.path)

        # Update history
        self.tool_history.append({
            "step": self.step_count,
            "tool": action.tool.value,
            "status": obs.status,
        })
        self.last_observation = obs_dict
        self.step_count += 1

        # Check submit
        if action.tool == ToolName.SUBMIT and obs.status == "submitted":
            self.done = True
            self.termination_reason = "submitted"
            self._record_step(action_raw, obs_dict, True, {"termination_reason": self.termination_reason})
            return obs_dict, True, {"termination_reason": self.termination_reason}

        # Check max steps
        if self.step_count >= MAX_STEPS:
            self.done = True
            self.termination_reason = "max_steps"
            self._record_step(action_raw, obs_dict, True, {"termination_reason": self.termination_reason})
            return obs_dict, True, {"termination_reason": self.termination_reason}

        self._record_step(action_raw, obs_dict, False, {})
        return obs_dict, False, {}

    def render_state(self) -> dict:
        """Return Agent-visible state. Must NOT leak private/hidden info."""
        state: dict[str, Any] = {
            "step_count": self.step_count,
            "max_steps": MAX_STEPS,
            "edit_count": self.tool_state.edit_count if self.tool_state else 0,
            "max_edits": MAX_EDITS,
            "test_count": self.tool_state.test_count if self.tool_state else 0,
            "max_tests": MAX_TESTS,
            "invalid_count": self.invalid_count,
            "done": self.done,
            "termination_reason": self.termination_reason,
            "modified_files": sorted(self.modified_files),
            "tool_history": list(self.tool_history),
            "last_observation": self.last_observation,
        }
        if self.metadata:
            state["task_id"] = self.metadata.task_id
            state["repo_type"] = self.metadata.repo_type
            state["bug_type"] = self.metadata.bug_type
            state["bug_description"] = self.metadata.bug_description
        return state

    def _record_step(self, action: Any, observation: dict, done: bool, info: dict) -> None:
        """Record one step to trajectory."""
        entry = {
            "task_id": self.metadata.task_id if self.metadata else None,
            "step": self.step_count,
            "action": action if isinstance(action, dict) else str(action),
            "observation": observation,
            "done": done,
            "info": info,
        }
        self.trajectory.append(entry)
        if self._trajectory_file:
            self._trajectory_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._trajectory_file.flush()

    def close(self) -> None:
        """Clean up resources."""
        if self._trajectory_file:
            self._trajectory_file.close()
            self._trajectory_file = None
        if self.sandbox:
            self.sandbox.__exit__(None, None, None)
            self.sandbox = None
