"""Action token log-prob computation for REINFORCE training."""

from __future__ import annotations

import torch


def compute_action_log_probs(
    logits: torch.Tensor,
    action_token_ids: torch.Tensor,
    prompt_len: int,
) -> torch.Tensor:
    """Extract per-token log-probs for action tokens from model logits.

    Given model output logits for the full sequence (prompt + action),
    compute log P(action_token_i | prompt, action_token_<i).

    Args:
        logits: Model output logits, shape (batch=1, seq_len, vocab_size).
        action_token_ids: Action token IDs, shape (1, action_len).
        prompt_len: Length of the prompt portion of the input.

    Returns:
        Per-token log-probs, shape (action_len,). Requires grad if logits require grad.
    """
    # Shift logits: position i predicts token i+1
    shifted_logits = logits[:, :-1, :]  # (1, seq_len-1, vocab_size)

    # Select logits corresponding to action tokens
    # shifted_logits[prompt_len-1] predicts action_token_ids[0]
    # shifted_logits[prompt_len-1 + k] predicts action_token_ids[k]
    action_logits = shifted_logits[:, prompt_len - 1 : prompt_len - 1 + action_token_ids.shape[1], :]

    # Compute log-softmax and gather
    log_probs = torch.log_softmax(action_logits, dim=-1)
    token_log_probs = log_probs.gather(2, action_token_ids.unsqueeze(-1)).squeeze(-1).squeeze(0)

    return token_log_probs


def compute_trajectory_log_prob(token_log_probs: torch.Tensor) -> torch.Tensor:
    """Sum per-token log-probs to get trajectory-level log-prob.

    Args:
        token_log_probs: Per-token log-probs, shape (action_len,).

    Returns:
        Scalar tensor: sum of log-probs.
    """
    return token_log_probs.sum()
