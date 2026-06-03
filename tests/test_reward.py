"""Tests for the reward system (sparse and dense modes)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from minirepair.env.reward import (
    REWARD_EXTRA_TOOL_CALL,
    REWARD_INVALID_ACTION,
    REWARD_INVALID_EDIT,
    REWARD_RECOVERED_PUBLIC_TEST,
    REWARD_REGRESSION,
    REWARD_SEVERE_GUARDRAIL,
    REWARD_TERMINAL_PUBLIC_PASS,
    REWARD_VALID_EDIT,
    RewardCalculator,
)
from minirepair.evaluation.metrics import EvalMode


@pytest.fixture
def mock_sandbox():
    sandbox = MagicMock()
    sandbox.working_path = Path("/tmp/fake")
    return sandbox


# ============================================================
# Sparse reward tests
# ============================================================


class TestSparseReward:
    def test_step_reward_always_zero(self, mock_sandbox):
        """Sparse reward has no step-level feedback."""
        calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)

        obs = {"status": "success", "tool_name": "edit_file", "info": {}}
        assert calc.compute_step_reward(obs, [{"tool": "edit_file"}]) == 0.0

        obs_err = {"status": "error", "tool_name": "parse", "info": {}}
        assert calc.compute_step_reward(obs_err, []) == 0.0

    @patch("minirepair.env.reward.evaluate_final_state")
    def test_terminal_private_pass_plus_one(self, mock_eval, mock_sandbox):
        mock_eval.return_value = {"private_pass": True, "hidden_pass": None}
        calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", False) == 1.0

    @patch("minirepair.env.reward.evaluate_final_state")
    def test_terminal_private_fail_zero(self, mock_eval, mock_sandbox):
        mock_eval.return_value = {"private_pass": False, "hidden_pass": None}
        calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", False) == 0.0

    def test_terminal_severe_guardrail_minus_one(self, mock_sandbox):
        calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", True) == -1.0

    def test_sparse_does_not_access_hidden_tests(self, mock_sandbox):
        """Sparse TRAIN_REWARD must not access hidden tests."""
        with patch("minirepair.env.reward.evaluate_final_state") as mock_eval:
            mock_eval.return_value = {"private_pass": True, "hidden_pass": None}
            calc = RewardCalculator("sparse", EvalMode.TRAIN_REWARD)
            calc.compute_terminal_reward(mock_sandbox, {}, "train", False)
            mock_eval.assert_called_once()
            _, kwargs = mock_eval.call_args
            # EvaluateMode should be TRAIN_REWARD, not FINAL_TEST
            assert mock_eval.call_args[0][2] == EvalMode.TRAIN_REWARD


# ============================================================
# Dense reward step-level tests
# ============================================================


class TestDenseStepReward:
    def test_valid_edit_plus_0_1(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "success", "tool_name": "edit_file", "info": {}}
        assert calc.compute_step_reward(obs, [{"tool": "edit_file"}]) == pytest.approx(REWARD_VALID_EDIT)

    def test_invalid_action_minus_0_3(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "error", "tool_name": "parse", "info": {}}
        assert calc.compute_step_reward(obs, []) == pytest.approx(REWARD_INVALID_ACTION)

    def test_invalid_edit_minus_0_5(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "error", "tool_name": "edit_file", "info": {}}
        assert calc.compute_step_reward(obs, [{"tool": "edit_file"}]) == pytest.approx(REWARD_INVALID_EDIT)

    def test_regression_minus_0_2(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {
            "status": "error",
            "tool_name": "run_tests",
            "info": {"failed": 1, "passed": 2},
        }
        # History must contain a prior edit_file AND a prior run_tests
        # so len > 1 is True (extra tool call) but we only check the regression part
        history = [{"tool": "edit_file"}, {"tool": "run_tests"}]
        result = calc.compute_step_reward(obs, history)
        # -0.2 (regression) + -0.05 (extra tool call, len=2 > 1)
        assert result == pytest.approx(REWARD_REGRESSION + REWARD_EXTRA_TOOL_CALL)

    def test_public_recovery_plus_0_2(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "success", "tool_name": "run_tests", "info": {"failed": 0}}
        assert calc.compute_step_reward(obs, [{"tool": "run_tests"}]) == pytest.approx(REWARD_RECOVERED_PUBLIC_TEST)

    def test_public_pass_second_time_no_recovery_bonus(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "success", "tool_name": "run_tests", "info": {"failed": 0}}
        calc.compute_step_reward(obs, [{"tool": "run_tests"}])
        # Second call: no recovery bonus
        result = calc.compute_step_reward(obs, [{"tool": "run_tests"}, {"tool": "run_tests"}])
        assert result == pytest.approx(REWARD_EXTRA_TOOL_CALL)

    def test_extra_tool_call_minus_0_05(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "success", "tool_name": "read_file", "info": {}}
        history = [{"tool": "read_file"}, {"tool": "read_file"}]
        assert calc.compute_step_reward(obs, history) == pytest.approx(REWARD_EXTRA_TOOL_CALL)

    def test_first_tool_call_no_penalty(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "success", "tool_name": "read_file", "info": {}}
        assert calc.compute_step_reward(obs, [{"tool": "read_file"}]) == 0.0

    def test_severe_guardrail_violation_minus_1(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {
            "status": "error",
            "tool_name": "edit_file",
            "info": {"violations": [{"rule": "forbidden_path", "severity": "block"}]},
        }
        assert calc.compute_step_reward(obs, []) == pytest.approx(REWARD_SEVERE_GUARDRAIL)

    def test_no_regression_without_prior_edit(self, mock_sandbox):
        """Failing tests before any edit is not a regression."""
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "error", "tool_name": "run_tests", "info": {"failed": 1}}
        assert calc.compute_step_reward(obs, [{"tool": "run_tests"}]) == 0.0


# ============================================================
# Dense reward terminal tests
# ============================================================


class TestDenseTerminalReward:
    @patch("minirepair.env.reward.run_public_tests_for_pass")
    @patch("minirepair.env.reward.evaluate_final_state")
    def test_both_pass_plus_1_5(self, mock_eval, mock_pub, mock_sandbox):
        mock_pub.return_value = True
        mock_eval.return_value = {"private_pass": True, "hidden_pass": None}
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", False) == pytest.approx(1.5)

    @patch("minirepair.env.reward.run_public_tests_for_pass")
    @patch("minirepair.env.reward.evaluate_final_state")
    def test_public_pass_private_fail_plus_0_5(self, mock_eval, mock_pub, mock_sandbox):
        mock_pub.return_value = True
        mock_eval.return_value = {"private_pass": False, "hidden_pass": None}
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", False) == pytest.approx(REWARD_TERMINAL_PUBLIC_PASS)

    @patch("minirepair.env.reward.run_public_tests_for_pass")
    @patch("minirepair.env.reward.evaluate_final_state")
    def test_neither_pass_zero(self, mock_eval, mock_pub, mock_sandbox):
        mock_pub.return_value = False
        mock_eval.return_value = {"private_pass": False, "hidden_pass": None}
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", False) == 0.0

    def test_severe_guardrail_terminal_minus_1(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        assert calc.compute_terminal_reward(mock_sandbox, {}, "train", True) == -1.0


# ============================================================
# Edge cases and constraints
# ============================================================


class TestRewardConstraints:
    def test_invalid_reward_mode_raises(self):
        with pytest.raises(ValueError, match="reward_mode"):
            RewardCalculator("invalid", EvalMode.TRAIN_REWARD)

    def test_reset_clears_public_tracking(self, mock_sandbox):
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
        obs = {"status": "success", "tool_name": "run_tests", "info": {"failed": 0}}
        calc.compute_step_reward(obs, [{"tool": "run_tests"}])
        assert calc._public_passed_at_least_once is True
        calc.reset()
        assert calc._public_passed_at_least_once is False

    def test_eval_mode_propagates_to_evaluator(self, mock_sandbox):
        """Verify the correct EvalMode is passed to evaluate_final_state."""
        with patch("minirepair.env.reward.evaluate_final_state") as mock_eval:
            mock_eval.return_value = {"private_pass": False, "hidden_pass": None}
            calc = RewardCalculator("sparse", EvalMode.VALIDATION_SELECTION)
            calc.compute_terminal_reward(mock_sandbox, {}, "validation", False)
            assert mock_eval.call_args[0][2] == EvalMode.VALIDATION_SELECTION

    def test_hidden_tests_never_accessed_in_train_reward(self, mock_sandbox):
        """TRAIN_REWARD eval mode must not access hidden tests."""
        with patch("minirepair.env.reward.evaluate_final_state") as mock_eval:
            mock_eval.return_value = {"private_pass": True, "hidden_pass": None}
            calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)
            calc.compute_terminal_reward(mock_sandbox, {}, "train", False)
            # hidden_pass should never be set by TRAIN_REWARD
            result = mock_eval.return_value
            assert result["hidden_pass"] is None

    def test_combined_step_and_terminal_dense(self, mock_sandbox):
        """Full episode: step rewards + terminal reward."""
        calc = RewardCalculator("dense", EvalMode.TRAIN_REWARD)

        # Step 1: valid edit
        obs1 = {"status": "success", "tool_name": "edit_file", "info": {}}
        r1 = calc.compute_step_reward(obs1, [{"tool": "edit_file"}])
        assert r1 == pytest.approx(REWARD_VALID_EDIT)

        # Step 2: run tests - recovery
        obs2 = {"status": "success", "tool_name": "run_tests", "info": {"failed": 0}}
        r2 = calc.compute_step_reward(obs2, [{"tool": "edit_file"}, {"tool": "run_tests"}])
        assert r2 == pytest.approx(REWARD_RECOVERED_PUBLIC_TEST + REWARD_EXTRA_TOOL_CALL)

        # Terminal
        with patch("minirepair.env.reward.run_public_tests_for_pass") as mock_pub, \
             patch("minirepair.env.reward.evaluate_final_state") as mock_eval:
            mock_pub.return_value = True
            mock_eval.return_value = {"private_pass": True, "hidden_pass": None}
            r_term = calc.compute_terminal_reward(mock_sandbox, {}, "train", False)

        total = r1 + r2 + r_term
        assert total == pytest.approx(REWARD_VALID_EDIT + REWARD_RECOVERED_PUBLIC_TEST + REWARD_EXTRA_TOOL_CALL + 1.5)
