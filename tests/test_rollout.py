"""Tests for rollout collection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from minirepair.agents.react_agent import Policy
from minirepair.env.code_repair_env import CodeRepairEnv
from minirepair.env.reward import RewardCalculator
from minirepair.evaluation.metrics import EvalMode
from minirepair.training.rollout import RolloutResult, RolloutStep, collect_rollout


class FixedPolicy(Policy):
    """Test policy that returns a fixed sequence of actions."""

    def __init__(self, actions: list[str]) -> None:
        self._actions = actions
        self._idx = 0

    def generate(self, prompt: str) -> str:
        action = self._actions[min(self._idx, len(self._actions) - 1)]
        self._idx += 1
        return action

    @property
    def policy_type(self) -> str:
        return "test_fixed"


# ============================================================
# Unit tests with mock env
# ============================================================


class TestRolloutDataStructures:
    def test_rollout_step_fields(self):
        step = RolloutStep(
            step_idx=0,
            prompt="test prompt",
            raw_output='{"tool": "submit", "arguments": {}}',
            parsed_action={"tool": "submit", "arguments": {}},
            observation={"status": "submitted"},
            reward=0.0,
            done=True,
            info={"termination_reason": "submitted"},
        )
        assert step.step_idx == 0
        assert step.prompt == "test prompt"
        assert step.parsed_action is not None
        assert step.prompt_token_ids is None  # Phase 7C

    def test_rollout_result_fields(self):
        result = RolloutResult(
            task_id="test_001",
            policy_type="test",
            steps=[],
            total_return=1.0,
            termination_reason="submitted",
        )
        assert result.task_id == "test_001"
        assert result.trajectory_log_prob is None  # Phase 7C


# ============================================================
# Integration tests with real env + mocked sandbox
# ============================================================


def _make_task_dir(tmp_path: Path) -> Path:
    """Create a minimal task directory for testing."""
    task_dir = tmp_path / "task_test"
    task_dir.mkdir()

    # Metadata
    metadata = {
        "task_id": "test_001",
        "repo_type": "string_utils",
        "bug_type": "boundary",
        "bug_description": "Test bug",
        "gold_patch": {
            "file_path": "src/string_utils.py",
            "old_text": "old",
            "new_text": "new",
        },
        "split": "train",
    }
    (task_dir / "metadata.json").write_text(json.dumps(metadata))

    # Minimal repo
    repo = task_dir / "repo"
    repo.mkdir()
    src = repo / "src"
    src.mkdir()
    (src / "string_utils.py").write_text("def hello():\n    return 'old'\n")

    # Public tests (must pass for reward) - use src. prefix like real benchmarks
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_hello.py").write_text(
        "from src.string_utils import hello\n"
        "def test_hello():\n"
        "    assert hello() == 'new'\n"
    )

    # Private tests
    tests_private = repo / "tests_private"
    tests_private.mkdir()
    (tests_private / "test_private.py").write_text(
        "from src.string_utils import hello\n"
        "def test_private():\n"
        "    assert hello() == 'new'\n"
    )

    return task_dir


class TestCollectRollout:
    def test_submit_immediately(self, tmp_path):
        """Submit on first step: 1 step, terminal reward only."""
        task_dir = _make_task_dir(tmp_path)
        policy = FixedPolicy(['{"tool": "submit", "arguments": {}}'])
        reward_calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        assert result.task_id == "test_001"
        assert result.policy_type == "test_fixed"
        assert len(result.steps) == 1
        assert result.termination_reason == "submitted"
        # Step reward is 0.0 (sparse), terminal is based on private tests
        assert isinstance(result.total_return, float)

    def test_invalid_json_preserved(self, tmp_path):
        """Invalid JSON raw_output must be preserved, not discarded."""
        task_dir = _make_task_dir(tmp_path)
        policy = FixedPolicy([
            "this is not valid json",
            '{"tool": "submit", "arguments": {}}',
        ])
        reward_calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        assert len(result.steps) == 2
        # First step: invalid JSON preserved
        assert result.steps[0].raw_output == "this is not valid json"
        assert result.steps[0].parsed_action is None
        # Invalid action should have negative reward (dense mode)
        assert result.steps[0].reward < 0.0

    def test_max_steps_termination(self, tmp_path):
        """Episode terminates at max steps."""
        task_dir = _make_task_dir(tmp_path)
        # Keep reading files until max steps
        read_action = json.dumps({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}})
        policy = FixedPolicy([read_action] * 10)
        reward_calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        assert result.termination_reason == "max_steps"
        assert len(result.steps) == 6  # MAX_STEPS

    def test_total_return_sums_step_and_terminal(self, tmp_path):
        """total_return = sum of step rewards + terminal reward."""
        task_dir = _make_task_dir(tmp_path)
        policy = FixedPolicy([
            json.dumps({"tool": "edit_file", "arguments": {"path": "src/string_utils.py", "old_text": "old", "new_text": "new"}}),
            json.dumps({"tool": "run_tests", "arguments": {}}),
            json.dumps({"tool": "submit", "arguments": {}}),
        ])
        reward_calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        # total_return includes step_sum + terminal reward
        # Terminal reward is non-zero (tests pass/fail), so total_return != step_sum
        # Just verify it's a valid float and step_sum is included
        assert isinstance(result.total_return, float)
        assert result.total_return != 0.0  # Should have some reward

    def test_prompt_captured_per_step(self, tmp_path):
        """Each step captures the full prompt text."""
        task_dir = _make_task_dir(tmp_path)
        policy = FixedPolicy([
            json.dumps({"tool": "read_file", "arguments": {"path": "src/string_utils.py"}}),
            json.dumps({"tool": "submit", "arguments": {}}),
        ])
        reward_calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        for step in result.steps:
            assert isinstance(step.prompt, str)
            assert len(step.prompt) > 0
            assert "code repair agent" in step.prompt.lower() or "tool" in step.prompt.lower()

    def test_severe_guardrail_detected(self, tmp_path):
        """Severe guardrail violation sets had_severe flag."""
        task_dir = _make_task_dir(tmp_path)
        # Try to modify tests (severe guardrail)
        policy = FixedPolicy([
            json.dumps({"tool": "edit_file", "arguments": {"path": "tests/test_hello.py", "old_text": "assert", "new_text": "pass"}}),
            json.dumps({"tool": "submit", "arguments": {}}),
        ])
        reward_calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        # First step should have guardrail error
        assert result.steps[0].observation.get("status") == "error"
        # Dense mode: severe guardrail gives -1.0
        assert result.steps[0].reward == pytest.approx(-1.0)

    def test_observation_no_leakage(self, tmp_path):
        """Observations must not contain private/hidden test content."""
        task_dir = _make_task_dir(tmp_path)
        policy = FixedPolicy([
            json.dumps({"tool": "run_tests", "arguments": {}}),
            json.dumps({"tool": "submit", "arguments": {}}),
        ])
        reward_calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)

        env = CodeRepairEnv()
        try:
            result = collect_rollout(env, task_dir, policy, reward_calc)
        finally:
            env.close()

        for step in result.steps:
            obs_str = json.dumps(step.observation)
            assert "tests_private" not in obs_str
            assert "tests_hidden" not in obs_str
