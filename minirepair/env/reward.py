"""Reward system for RL training: sparse and dense reward modes."""

from __future__ import annotations

import logging
from typing import Any

from minirepair.env.sandbox import Sandbox
from minirepair.evaluation.evaluator import evaluate_final_state, run_public_tests_for_pass
from minirepair.evaluation.metrics import EvalMode

logger = logging.getLogger(__name__)

# Dense reward constants
REWARD_TERMINAL_PRIVATE_PASS = 1.0
REWARD_TERMINAL_PUBLIC_PASS = 0.5
REWARD_RECOVERED_PUBLIC_TEST = 0.2
REWARD_VALID_EDIT = 0.1
REWARD_REGRESSION = -0.2
REWARD_EXTRA_TOOL_CALL = -0.05
REWARD_INVALID_ACTION = -0.3
REWARD_INVALID_EDIT = -0.5
REWARD_SEVERE_GUARDRAIL = -1.0

SEVERE_GUARDRAIL_RULES = frozenset({
    "forbidden_path",
    "forbidden_file",
    "skip_pattern",
    "assert_deletion",
})


def is_severe_violation(info: dict) -> bool:
    """Check if step info contains a severe guardrail violation."""
    for violation in info.get("violations", []):
        if violation.get("rule") in SEVERE_GUARDRAIL_RULES:
            return True
    return False


class RewardCalculator:
    """Compute sparse or dense rewards for RL training.

    Sparse: +1.0 terminal private pass, 0.0 otherwise, -1.0 severe guardrail.
    Dense: step-level feedback + terminal bonuses.
    """

    def __init__(self, reward_mode: str, eval_mode: EvalMode) -> None:
        if reward_mode not in ("sparse", "dense"):
            raise ValueError(f"reward_mode must be 'sparse' or 'dense', got {reward_mode!r}")
        self.reward_mode = reward_mode
        self.eval_mode = eval_mode
        self._public_passed_at_least_once = False

    def compute_step_reward(
        self,
        step_obs: dict[str, Any],
        tool_history: list[dict],
        step_info: dict[str, Any] | None = None,
    ) -> float:
        """Compute incremental reward for one step.

        Args:
            step_obs: Observation dict from env.step().
            tool_history: Full tool history from the environment.
            step_info: Info dict from env.step().

        Returns:
            Step reward (float).
        """
        if self.reward_mode == "sparse":
            return 0.0

        obs_info = step_obs.get("info", {})
        tool = step_obs.get("tool_name", "")
        status = step_obs.get("status", "")
        reward = 0.0

        # Severe guardrail violation: immediate -1.0
        if is_severe_violation(obs_info):
            return REWARD_SEVERE_GUARDRAIL

        # Valid edit: +0.1
        if tool == "edit_file" and status == "success":
            reward += REWARD_VALID_EDIT

        # Invalid action (parse error): -0.3
        if tool == "parse" and status == "error":
            reward += REWARD_INVALID_ACTION

        # Invalid edit (guardrail block or budget exceeded): -0.5
        if tool == "edit_file" and status == "error":
            reward += REWARD_INVALID_EDIT

        # Public test regression: -0.2
        if tool == "run_tests" and status in ("success", "error"):
            failed = obs_info.get("failed", 0)
            edit_count = sum(1 for h in tool_history if h.get("tool") == "edit_file")
            if edit_count > 0 and failed > 0:
                reward += REWARD_REGRESSION

        # Public test pass: +0.2 for first recovery, track for terminal bonus
        if tool == "run_tests" and status == "success":
            if not self._public_passed_at_least_once:
                reward += REWARD_RECOVERED_PUBLIC_TEST
            self._public_passed_at_least_once = True

        # Extra tool call penalty: -0.05 per non-first tool call
        if len(tool_history) > 1:
            reward += REWARD_EXTRA_TOOL_CALL

        return reward

    def compute_terminal_reward(
        self,
        sandbox: Sandbox,
        metadata: dict[str, Any],
        split: str,
        had_severe_guardrail: bool,
    ) -> float:
        """Compute terminal reward at episode end.

        Args:
            sandbox: Active sandbox with working_path available.
            metadata: Task metadata dict.
            split: Dataset split name.
            had_severe_guardrail: Whether a severe guardrail violation occurred.

        Returns:
            Terminal reward (float).
        """
        if self.reward_mode == "sparse":
            return self._sparse_terminal(sandbox, split, had_severe_guardrail)
        return self._dense_terminal(sandbox, split, had_severe_guardrail)

    def _sparse_terminal(
        self,
        sandbox: Sandbox,
        split: str,
        had_severe_guardrail: bool,
    ) -> float:
        if had_severe_guardrail:
            return REWARD_SEVERE_GUARDRAIL

        result = evaluate_final_state(sandbox, split, self.eval_mode)
        private_pass = result.get("private_pass")
        if private_pass:
            return REWARD_TERMINAL_PRIVATE_PASS
        return 0.0

    def _dense_terminal(
        self,
        sandbox: Sandbox,
        split: str,
        had_severe_guardrail: bool,
    ) -> float:
        if had_severe_guardrail:
            return REWARD_SEVERE_GUARDRAIL

        reward = 0.0

        # Public pass bonus
        public_pass = run_public_tests_for_pass(sandbox)
        if public_pass:
            reward += REWARD_TERMINAL_PUBLIC_PASS

        # Private pass bonus
        result = evaluate_final_state(sandbox, split, self.eval_mode)
        private_pass = result.get("private_pass")
        if private_pass:
            reward += REWARD_TERMINAL_PRIVATE_PASS

        return reward

    def reset(self) -> None:
        """Reset episode-level tracking state."""
        self._public_passed_at_least_once = False
