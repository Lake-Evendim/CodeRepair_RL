"""Tests for CodeRepairEnv."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from minirepair.env.code_repair_env import MAX_CONSECUTIVE_INVALID, MAX_EDITS, MAX_STEPS, MAX_TESTS, CodeRepairEnv

SEED_DIR = Path(__file__).resolve().parent.parent / "benchmarks" / "tasks" / "seed"


def _gold_action_sequence(task_path: Path) -> list[dict]:
    """Build a gold action sequence from a task's metadata."""
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


class TestReset:
    def test_reset_loads_metadata(self):
        env = CodeRepairEnv()
        task_path = SEED_DIR / "task_0001"
        state = env.reset(task_path)
        assert state["task_id"] == "task_0001"
        assert state["repo_type"] == "string_utils"
        assert state["step_count"] == 0
        assert state["done"] is False
        env.close()

    def test_reset_nonexistent_task(self):
        env = CodeRepairEnv()
        with pytest.raises(FileNotFoundError):
            env.reset(Path("/nonexistent/task"))
        env.close()

    def test_reset_creates_sandbox(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        assert env.sandbox is not None
        assert env.sandbox.working_path is not None
        env.close()


class TestStep:
    def test_step_read_file(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        obs, done, info = env.step({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
        assert obs["status"] == "success"
        assert "def truncate_string" in obs["content"]
        assert done is False
        env.close()

    def test_step_submit(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        obs, done, info = env.step({"tool": "submit", "arguments": {}})
        assert obs["status"] == "submitted"
        assert done is True
        assert info["termination_reason"] == "submitted"
        env.close()

    def test_step_after_done(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        env.step({"tool": "submit", "arguments": {}})
        obs, done, info = env.step({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
        assert obs["status"] == "error"
        assert "already done" in obs["error"]
        env.close()

    def test_step_invalid_json(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        obs, done, info = env.step("not valid json")
        assert obs["status"] == "error"
        assert done is False
        assert env.invalid_count == 1
        env.close()

    def test_step_edit_file_budget(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0002")
        # Do max edits (use two non-conflicting edits on the same file)
        edits = [
            ("    return s[: max_len - 3] + \"...\"", "    return s[: max_len - 4] + \"...\""),
            ("        start = idx + 1", "        start = idx + len(sub)"),
        ]
        for old, new in edits:
            env.step({
                "tool": "edit_file",
                "arguments": {"path": "src/string_utils.py", "old_text": old, "new_text": new},
            })
        assert env.tool_state.edit_count == MAX_EDITS
        # One more should fail due to budget
        obs, _, _ = env.step({
            "tool": "edit_file",
            "arguments": {"path": "src/string_utils.py", "old_text": "x", "new_text": "y"},
        })
        assert obs["status"] == "error"
        assert "budget" in obs["error"].lower()
        env.close()

    def test_step_run_tests_budget(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        for _ in range(MAX_TESTS):
            env.step({"tool": "run_tests", "arguments": {}})
        obs, _, _ = env.step({"tool": "run_tests", "arguments": {}})
        assert obs["status"] == "error"
        assert "budget" in obs["error"].lower()
        env.close()


class TestTermination:
    def test_max_steps_termination(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        for i in range(MAX_STEPS):
            obs, done, info = env.step({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
        assert done is True
        assert env.termination_reason == "max_steps"
        env.close()

    def test_consecutive_invalid_termination(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        for i in range(MAX_CONSECUTIVE_INVALID - 1):
            env.step("invalid json")
            assert env.done is False
        obs, done, info = env.step("invalid json")
        assert done is True
        assert env.termination_reason == "consecutive_invalid"
        env.close()

    def test_valid_action_resets_invalid_count(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        env.step("invalid json")
        assert env.invalid_count == 1
        env.step({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
        assert env.invalid_count == 0
        env.close()


class TestRenderState:
    def test_no_private_leakage(self):
        """render_state must not contain private/hidden test info."""
        env = CodeRepairEnv()
        state = env.reset(SEED_DIR / "task_0001")
        state_str = json.dumps(state)
        assert "tests_private" not in state_str
        assert "tests_hidden" not in state_str
        assert "gold_patch" not in state_str
        assert "old_text" not in state_str
        assert "new_text" not in state_str
        env.close()

    def test_render_after_steps(self):
        env = CodeRepairEnv()
        env.reset(SEED_DIR / "task_0001")
        env.step({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
        state = env.render_state()
        assert state["step_count"] == 1
        assert len(state["tool_history"]) == 1
        assert state["tool_history"][0]["tool"] == "read_file"
        env.close()


class TestGoldSequence:
    @pytest.mark.parametrize("task_id", [
        "task_0001", "task_0002", "task_0003", "task_0004", "task_0005",
    ])
    def test_gold_fixes_string_utils_tasks(self, task_id: str):
        """Gold action sequence should fix string_utils tasks."""
        task_path = SEED_DIR / task_id
        env = CodeRepairEnv()
        env.reset(task_path)

        actions = _gold_action_sequence(task_path)
        for action in actions:
            obs, done, info = env.step(action)
            if done:
                break

        assert env.termination_reason == "submitted"
        # The last run_tests before submit should show success
        # Find the run_tests observation
        test_obs = None
        for entry in env.trajectory:
            if isinstance(entry.get("action"), dict) and entry["action"].get("tool") == "run_tests":
                test_obs = entry["observation"]
        assert test_obs is not None
        assert test_obs["status"] == "success"
        env.close()

    @pytest.mark.parametrize("task_id", [
        "task_0011", "task_0012", "task_0014", "task_0019", "task_0017",
    ])
    def test_gold_fixes_validator_tasks(self, task_id: str):
        """Gold action sequence should fix validator tasks."""
        task_path = SEED_DIR / task_id
        env = CodeRepairEnv()
        env.reset(task_path)

        actions = _gold_action_sequence(task_path)
        for action in actions:
            obs, done, info = env.step(action)
            if done:
                break

        assert env.termination_reason == "submitted"
        test_obs = None
        for entry in env.trajectory:
            if isinstance(entry.get("action"), dict) and entry["action"].get("tool") == "run_tests":
                test_obs = entry["observation"]
        assert test_obs is not None
        assert test_obs["status"] == "success"
        env.close()


class TestTrajectory:
    def test_trajectory_logging(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = CodeRepairEnv(trajectory_dir=Path(tmp))
            env.reset(SEED_DIR / "task_0001")
            env.step({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
            env.step({"tool": "submit", "arguments": {}})
            env.close()

            traj_path = Path(tmp) / "task_0001.jsonl"
            assert traj_path.exists()
            lines = traj_path.read_text().strip().split("\n")
            assert len(lines) == 2
            entry = json.loads(lines[0])
            assert entry["task_id"] == "task_0001"
            assert entry["step"] == 1  # step_count incremented after execution
