"""Rollout collection for RL training: run episodes and collect trajectories."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from minirepair.agents.action_parser import extract_action_from_llm_output
from minirepair.agents.react_agent import Policy, build_react_prompt
from minirepair.env.action_schema import Action
from minirepair.env.code_repair_env import CodeRepairEnv
from minirepair.env.reward import RewardCalculator


@dataclass
class RolloutStep:
    """One step of a rollout, capturing everything needed for REINFORCE."""

    step_idx: int
    prompt: str
    raw_output: str
    parsed_action: dict | None
    observation: dict
    reward: float
    done: bool
    info: dict
    # Token-level info (populated in Phase 7C)
    prompt_token_ids: list[int] | None = None
    action_token_ids: list[int] | None = None
    attention_mask: list[int] | None = None
    action_token_log_prob: float | None = None  # detached, for audit only


@dataclass
class RolloutResult:
    """Complete rollout for one episode."""

    task_id: str
    policy_type: str
    steps: list[RolloutStep]
    total_return: float
    termination_reason: str
    # Trajectory-level log-prob (audit only, populated in Phase 7C)
    trajectory_log_prob: float | None = None


def collect_rollout(
    env: CodeRepairEnv,
    task_path: Path,
    policy: Policy,
    reward_calculator: RewardCalculator,
) -> RolloutResult:
    """Run one episode, collecting prompt/action/reward at each step.

    Unlike run_episode(), this preserves the full prompt text and computes
    step/terminal rewards via RewardCalculator.

    Invalid JSON/actions are preserved (not discarded).
    """
    state = env.reset(task_path)
    reward_calculator.reset()

    history: list[dict] = []
    steps: list[RolloutStep] = []
    total_return = 0.0
    done = False

    while not done:
        step_idx = env.step_count
        prompt = build_react_prompt(state, history)
        raw_output = policy.generate(prompt)

        # Parse action
        action_result = extract_action_from_llm_output(raw_output)
        if isinstance(action_result, Action):
            action_dict = action_result.model_dump()
            obs_dict, done, info = env.step(action_dict)
        else:
            # Invalid action: pass raw string to env
            action_dict = None
            obs_dict, done, info = env.step(raw_output)

        # Compute step reward
        step_reward = reward_calculator.compute_step_reward(
            step_obs=obs_dict,
            tool_history=env.tool_history,
            step_info=info,
        )
        total_return += step_reward

        # Record step
        rollout_step = RolloutStep(
            step_idx=step_idx,
            prompt=prompt,
            raw_output=raw_output,
            parsed_action=action_dict,
            observation=obs_dict,
            reward=step_reward,
            done=done,
            info=info,
        )
        steps.append(rollout_step)

        # Update history for next prompt
        history.append({
            "action": action_dict if action_dict else raw_output,
            "observation": obs_dict,
        })

        state = env.render_state()

    # Compute terminal reward
    had_severe = any(
        step.reward <= -1.0 and step.info.get("termination_reason") == "guardrail"
        for step in steps
    )
    # Also check if severe guardrail occurred at any step (dense mode)
    if not had_severe:
        from minirepair.env.reward import is_severe_violation
        for step in steps:
            if is_severe_violation(step.observation.get("info", {})):
                had_severe = True
                break

    if env.sandbox and env.metadata:
        split = env.metadata.split
        terminal_reward = reward_calculator.compute_terminal_reward(
            sandbox=env.sandbox,
            metadata=env.metadata.model_dump(),
            split=split,
            had_severe_guardrail=had_severe,
        )
    else:
        terminal_reward = 0.0

    total_return += terminal_reward

    return RolloutResult(
        task_id=env.metadata.task_id if env.metadata else "unknown",
        policy_type=policy.policy_type,
        steps=steps,
        total_return=total_return,
        termination_reason=env.termination_reason or "unknown",
    )
