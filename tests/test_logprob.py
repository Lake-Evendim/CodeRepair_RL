"""Tests for action token log-prob computation."""

from __future__ import annotations

import pytest
import torch

from minirepair.training.logprob import (
    compute_action_log_probs,
    compute_trajectory_log_prob,
)

# Skip if transformers not installed (training dependency)
pytest.importorskip("transformers")


CACHED_MODEL_PATH = "/home/amlab/.cache/modelscope/hub/models/Qwen/Qwen2___5-Coder-1___5B-Instruct"


@pytest.fixture(scope="module")
def model_and_tokenizer():
    """Load a locally cached model for testing."""
    import os

    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_path = CACHED_MODEL_PATH
    if not os.path.exists(model_path):
        pytest.skip("Qwen model not cached locally")

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    model.eval()
    return model, tokenizer


def _get_logits_and_ids(model, tokenizer, prompt_text, action_text):
    """Run forward pass and return logits, prompt_ids, action_ids."""
    device = next(model.parameters()).device
    prompt_ids = tokenizer.encode(prompt_text, return_tensors="pt").to(device)
    action_ids = tokenizer.encode(action_text, return_tensors="pt").to(device)
    full_ids = torch.cat([prompt_ids, action_ids], dim=1)
    attention_mask = torch.ones_like(full_ids)

    with torch.no_grad():
        outputs = model(full_ids, attention_mask=attention_mask)
    return outputs.logits, prompt_ids, action_ids, full_ids


class TestComputeActionLogProbs:
    def test_output_shape(self, model_and_tokenizer):
        """Output shape should be (action_len,)."""
        model, tokenizer = model_and_tokenizer
        logits, prompt_ids, action_ids, _ = _get_logits_and_ids(
            model, tokenizer, "Hello world", "test action"
        )
        log_probs = compute_action_log_probs(logits, action_ids, prompt_ids.shape[1])
        assert log_probs.shape == (action_ids.shape[1],)

    def test_values_are_negative(self, model_and_tokenizer):
        """Log-probs should be negative (log of probability in [0,1])."""
        model, tokenizer = model_and_tokenizer
        logits, prompt_ids, action_ids, _ = _get_logits_and_ids(
            model, tokenizer, "The answer is", " 42"
        )
        log_probs = compute_action_log_probs(logits, action_ids, prompt_ids.shape[1])
        assert torch.all(log_probs <= 0.0)

    def test_requires_grad_with_grad_enabled(self, model_and_tokenizer):
        """When logits require grad, output should also require grad."""
        model, tokenizer = model_and_tokenizer
        device = next(model.parameters()).device
        prompt_ids = tokenizer.encode("Hello", return_tensors="pt").to(device)
        action_ids = tokenizer.encode(" world", return_tensors="pt").to(device)
        full_ids = torch.cat([prompt_ids, action_ids], dim=1)
        attention_mask = torch.ones_like(full_ids)

        # Forward with grad
        model.train()
        outputs = model(full_ids, attention_mask=attention_mask)
        log_probs = compute_action_log_probs(outputs.logits, action_ids, prompt_ids.shape[1])
        assert log_probs.requires_grad is True
        model.eval()

    def test_no_grad_when_detached(self, model_and_tokenizer):
        """When logits don't require grad, output shouldn't either."""
        model, tokenizer = model_and_tokenizer
        logits, prompt_ids, action_ids, _ = _get_logits_and_ids(
            model, tokenizer, "Hello", " world"
        )
        log_probs = compute_action_log_probs(logits, action_ids, prompt_ids.shape[1])
        assert log_probs.requires_grad is False

    def test_single_token_action(self, model_and_tokenizer):
        """Single action token produces shape (1,)."""
        model, tokenizer = model_and_tokenizer
        logits, prompt_ids, action_ids, _ = _get_logits_and_ids(
            model, tokenizer, "The capital of France is", " Paris"
        )
        if action_ids.shape[1] == 1:
            log_probs = compute_action_log_probs(logits, action_ids, prompt_ids.shape[1])
            assert log_probs.shape == (1,)
        else:
            pytest.skip("Tokenizer produced multiple tokens for 'Paris'")

    def test_multi_token_action(self, model_and_tokenizer):
        """Multi-token action produces correct shape."""
        model, tokenizer = model_and_tokenizer
        logits, prompt_ids, action_ids, _ = _get_logits_and_ids(
            model, tokenizer, "Write a greeting:", " Hello, how are you?"
        )
        log_probs = compute_action_log_probs(logits, action_ids, prompt_ids.shape[1])
        assert log_probs.shape == (action_ids.shape[1],)
        assert action_ids.shape[1] > 1  # Ensure we actually have multiple tokens

    def test_different_prompts_different_logprobs(self, model_and_tokenizer):
        """Same action with different prompts should give different log-probs."""
        model, tokenizer = model_and_tokenizer
        action_text = " test"

        logits1, prompt1, action1, _ = _get_logits_and_ids(
            model, tokenizer, "Hello", action_text
        )
        logits2, prompt2, action2, _ = _get_logits_and_ids(
            model, tokenizer, "Goodbye", action_text
        )

        lp1 = compute_action_log_probs(logits1, action1, prompt1.shape[1])
        lp2 = compute_action_log_probs(logits2, action2, prompt2.shape[1])

        # They should be different (different contexts)
        assert not torch.allclose(lp1, lp2, atol=1e-4)


class TestComputeTrajectoryLogProb:
    def test_sum_of_log_probs(self):
        token_log_probs = torch.tensor([-1.0, -2.0, -0.5])
        result = compute_trajectory_log_prob(token_log_probs)
        assert result == pytest.approx(-3.5)

    def test_single_token(self):
        token_log_probs = torch.tensor([-1.5])
        result = compute_trajectory_log_prob(token_log_probs)
        assert result == pytest.approx(-1.5)

    def test_preserves_grad(self):
        """Sum should preserve gradient connection."""
        token_log_probs = torch.tensor([-1.0, -2.0], requires_grad=True)
        result = compute_trajectory_log_prob(token_log_probs)
        assert result.requires_grad is True
        result.backward()
        assert token_log_probs.grad is not None


class TestGradientFlow:
    """Test that gradients flow correctly through the log-prob computation."""

    def test_gradient_flows_to_model_params(self, model_and_tokenizer):
        """A loss computed from log-probs should produce gradients for model params."""
        model, tokenizer = model_and_tokenizer
        device = next(model.parameters()).device
        model.train()

        prompt_ids = tokenizer.encode("Hello", return_tensors="pt").to(device)
        action_ids = tokenizer.encode(" world", return_tensors="pt").to(device)
        full_ids = torch.cat([prompt_ids, action_ids], dim=1)
        attention_mask = torch.ones_like(full_ids)

        outputs = model(full_ids, attention_mask=attention_mask)
        log_probs = compute_action_log_probs(outputs.logits, action_ids, prompt_ids.shape[1])
        loss = -log_probs.sum()
        loss.backward()

        # At least one parameter should have a gradient
        has_grad = any(
            p.grad is not None and p.grad.abs().sum() > 0
            for p in model.parameters()
        )
        assert has_grad, "No gradient flowed to model parameters"

        model.zero_grad()
        model.eval()
