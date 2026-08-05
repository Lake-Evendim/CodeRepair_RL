"""REINFORCE with moving-average baseline for RL fine-tuning."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import torch

from minirepair.training.logprob import compute_action_log_probs, compute_trajectory_log_prob
from minirepair.training.rollout import RolloutResult

logger = logging.getLogger(__name__)


class MovingAverageBaseline:
    """Exponential moving-average baseline for advantage estimation."""

    def __init__(self, momentum: float = 0.9) -> None:
        self.momentum = momentum
        self.value: float = 0.0
        self.initialized: bool = False

    def update(self, return_value: float) -> float:
        """Update baseline with new return value. Returns current baseline."""
        if not self.initialized:
            self.value = return_value
            self.initialized = True
        else:
            self.value = self.momentum * self.value + (1 - self.momentum) * return_value
        return self.value


@dataclass
class ReinforceUpdateResult:
    """Result of one REINFORCE update step."""

    loss: float
    avg_return: float
    baseline: float
    avg_advantage: float
    num_trajectories: int


def reinforce_update(
    model: torch.nn.Module,
    tokenizer: Any,
    rollout_results: list[RolloutResult],
    baseline: MovingAverageBaseline,
    optimizer: torch.optim.Optimizer,
) -> ReinforceUpdateResult:
    """Perform one REINFORCE update step.

    For each rollout trajectory:
    1. Re-forward current policy to get fresh action-token log-probs (with grad)
    2. Compute trajectory_log_prob = sum(step_log_probs)
    3. Compute advantage = total_return - baseline
    4. Accumulate loss = -advantage.detach() * trajectory_log_prob

    All trajectories use the same baseline snapshot. The caller owns baseline
    updates so a batch is not biased by trajectory ordering.

    Invalid JSON/action trajectories are NOT discarded.

    Args:
        model: PeftModel with LoRA adapter.
        tokenizer: Tokenizer for the model.
        rollout_results: List of RolloutResult from rollout collection.
        baseline: MovingAverageBaseline for advantage estimation.
        optimizer: Optimizer for the LoRA adapter parameters.

    Returns:
        ReinforceUpdateResult with loss, return, baseline, advantage stats.
    """
    device = next(model.parameters()).device
    model.train()

    total_loss = torch.tensor(0.0, device=device, requires_grad=True)
    returns = []
    advantages = []
    num_valid = 0

    # Use current baseline (not updated within this call)
    current_baseline = baseline.value if baseline.initialized else 0.0

    for rollout in rollout_results:
        advantage = rollout.total_return - current_baseline
        returns.append(rollout.total_return)
        advantages.append(advantage)

        # Re-forward all steps to get fresh log-probs with grad
        # Accumulate log-prob scalar directly to avoid storing intermediate graphs
        trajectory_log_prob = torch.tensor(0.0, device=device, requires_grad=True)
        for step in rollout.steps:
            prompt_text = step.prompt
            action_text = step.raw_output

            # Tokenize
            prompt_ids = tokenizer.encode(prompt_text, return_tensors="pt").to(device)
            action_ids = tokenizer.encode(action_text, return_tensors="pt").to(device)
            full_ids = torch.cat([prompt_ids, action_ids], dim=1)
            attention_mask = torch.ones_like(full_ids)

            # Forward with grad
            outputs = model(full_ids, attention_mask=attention_mask)

            # Compute action log-probs (with grad) and accumulate immediately
            token_log_probs = compute_action_log_probs(
                outputs.logits, action_ids, prompt_ids.shape[1]
            )
            step_lp = compute_trajectory_log_prob(token_log_probs)
            trajectory_log_prob = trajectory_log_prob + step_lp

            # Free intermediate tensors
            del outputs, full_ids, attention_mask, prompt_ids, action_ids
            del token_log_probs, step_lp
            torch.cuda.empty_cache()

        # REINFORCE loss: -advantage * trajectory_log_prob
        loss_term = -advantage * trajectory_log_prob
        total_loss = total_loss + loss_term
        num_valid += 1

    if num_valid == 0:
        return ReinforceUpdateResult(
            loss=0.0,
            avg_return=0.0,
            baseline=baseline.value,
            avg_advantage=0.0,
            num_trajectories=0,
        )

    # Average loss over trajectories
    avg_loss = total_loss / num_valid

    # Backward and update
    optimizer.zero_grad()
    avg_loss.backward()
    optimizer.step()

    return ReinforceUpdateResult(
        loss=avg_loss.item(),
        avg_return=sum(returns) / len(returns),
        baseline=baseline.value,
        avg_advantage=sum(advantages) / len(advantages),
        num_trajectories=num_valid,
    )
