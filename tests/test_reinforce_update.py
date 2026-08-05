"""Tests for single-batch REINFORCE update."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from minirepair.training.rollout import RolloutResult, RolloutStep
from minirepair.training.train_reinforce import MovingAverageBaseline, reinforce_update

pytest.importorskip("peft")

CACHED_MODEL_PATH = "/home/amlab/.cache/modelscope/hub/models/Qwen/Qwen2___5-Coder-1___5B-Instruct"
SFT_ADAPTER_PATH = Path("outputs/sft_adapter")


@pytest.fixture(scope="module")
def model_and_tokenizer():
    """Load base model with SFT LoRA adapter for testing."""
    import os

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not os.path.exists(CACHED_MODEL_PATH):
        pytest.skip("Qwen model not cached locally")
    if not SFT_ADAPTER_PATH.exists():
        pytest.skip("SFT adapter not found")

    from minirepair.training.train_sft import resolve_model_path

    model_path = resolve_model_path("Qwen/Qwen2.5-Coder-1.5B-Instruct")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(model, str(SFT_ADAPTER_PATH))
    model.enable_adapter_layers()
    model.train()
    return model, tokenizer


def _make_rollout(prompt: str, raw_output: str, total_return: float) -> RolloutResult:
    """Create a simple single-step RolloutResult for testing."""
    return RolloutResult(
        task_id="test_task",
        policy_type="test",
        steps=[
            RolloutStep(
                step_idx=0,
                prompt=prompt,
                raw_output=raw_output,
                parsed_action={"tool": "submit", "arguments": {}},
                observation={"status": "submitted"},
                reward=total_return,
                done=True,
                info={},
            )
        ],
        total_return=total_return,
        termination_reason="submitted",
    )


class TestMovingAverageBaseline:
    def test_initial_update(self):
        bl = MovingAverageBaseline(momentum=0.9)
        assert bl.update(1.0) == 1.0
        assert bl.value == 1.0
        assert bl.initialized is True

    def test_subsequent_updates(self):
        bl = MovingAverageBaseline(momentum=0.9)
        bl.update(1.0)
        bl.update(0.0)
        # 0.9 * 1.0 + 0.1 * 0.0 = 0.9
        assert bl.value == pytest.approx(0.9)

    def test_momentum_effect(self):
        bl = MovingAverageBaseline(momentum=0.5)
        bl.update(2.0)
        bl.update(0.0)
        # 0.5 * 2.0 + 0.5 * 0.0 = 1.0
        assert bl.value == pytest.approx(1.0)


class TestReinforceUpdate:
    def test_single_batch_loss_finite(self, model_and_tokenizer):
        """Single update produces a finite loss."""
        model, tokenizer = model_and_tokenizer
        model.train()

        # Freeze base model, only train LoRA
        for name, param in model.named_parameters():
            if "lora" not in name.lower():
                param.requires_grad = False

        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=1e-5
        )
        baseline = MovingAverageBaseline(momentum=0.9)

        rollout = _make_rollout(
            prompt="Fix the bug in this code: def add(a, b): return a - b",
            raw_output='{"tool": "submit", "arguments": {}}',
            total_return=1.0,
        )

        result = reinforce_update(model, tokenizer, [rollout], baseline, optimizer)

        assert isinstance(result.loss, float)
        assert result.loss != float("inf")
        assert result.loss != float("nan")
        assert result.num_trajectories == 1
        assert result.avg_return == pytest.approx(1.0)

    def test_adapter_params_change(self, model_and_tokenizer):
        """At least one LoRA adapter parameter must change after update."""
        model, tokenizer = model_and_tokenizer
        model.train()

        # Freeze base model
        for name, param in model.named_parameters():
            if "lora" not in name.lower():
                param.requires_grad = False

        # Save adapter params before
        params_before = {
            name: param.data.clone()
            for name, param in model.named_parameters()
            if param.requires_grad
        }

        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=1e-3
        )
        baseline = MovingAverageBaseline(momentum=0.9)
        # Pre-initialize baseline so advantage is non-zero
        baseline.value = 0.0
        baseline.initialized = True

        rollout = _make_rollout(
            prompt="Fix: def add(a, b): return a - b",
            raw_output='{"tool": "edit_file", "arguments": {"path": "src/math.py", "old_text": "a - b", "new_text": "a + b"}}',
            total_return=1.0,
        )

        reinforce_update(model, tokenizer, [rollout], baseline, optimizer)

        # Check at least one param changed
        changed = False
        for name, param in model.named_parameters():
            if param.requires_grad:
                if not torch.allclose(params_before[name], param.data):
                    changed = True
                    break
        assert changed, "No LoRA adapter parameter changed after update"

    def test_base_model_params_frozen(self, model_and_tokenizer):
        """Base model parameters must not change."""
        model, tokenizer = model_and_tokenizer
        model.train()

        for name, param in model.named_parameters():
            if "lora" not in name.lower():
                param.requires_grad = False

        # Save base params
        base_params_before = {
            name: param.data.clone()
            for name, param in model.named_parameters()
            if not param.requires_grad
        }

        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=1e-4
        )
        baseline = MovingAverageBaseline(momentum=0.9)

        rollout = _make_rollout(
            prompt="Fix this code",
            raw_output='{"tool": "submit", "arguments": {}}',
            total_return=1.0,
        )

        reinforce_update(model, tokenizer, [rollout], baseline, optimizer)

        # Verify base params unchanged
        for name, param in model.named_parameters():
            if not param.requires_grad:
                assert torch.allclose(base_params_before[name], param.data), \
                    f"Base model param {name} changed!"

    def test_multiple_rollouts(self, model_and_tokenizer):
        """Multiple rollouts in a batch."""
        model, tokenizer = model_and_tokenizer
        model.train()

        for name, param in model.named_parameters():
            if "lora" not in name.lower():
                param.requires_grad = False

        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=1e-5
        )
        baseline = MovingAverageBaseline(momentum=0.9)

        rollouts = [
            _make_rollout("Fix code A", '{"tool": "submit", "arguments": {}}', 1.0),
            _make_rollout("Fix code B", '{"tool": "submit", "arguments": {}}', 0.0),
        ]

        result = reinforce_update(model, tokenizer, rollouts, baseline, optimizer)
        assert result.num_trajectories == 2
        assert isinstance(result.loss, float)

    def test_invalid_trajectory_not_discarded(self, model_and_tokenizer):
        """Invalid JSON action trajectories must be included (not discarded)."""
        model, tokenizer = model_and_tokenizer
        model.train()

        for name, param in model.named_parameters():
            if "lora" not in name.lower():
                param.requires_grad = False

        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=1e-5
        )
        baseline = MovingAverageBaseline(momentum=0.9)

        # One valid, one invalid
        rollouts = [
            _make_rollout("Fix code", '{"tool": "submit", "arguments": {}}', 1.0),
            _make_rollout("Fix code", "this is not valid json", -0.3),
        ]

        result = reinforce_update(model, tokenizer, rollouts, baseline, optimizer)
        assert result.num_trajectories == 2  # Both included

    def test_baseline_is_not_updated_within_batch(self, model_and_tokenizer):
        """The caller, not a trajectory batch, should update the baseline."""
        model, tokenizer = model_and_tokenizer
        model.train()

        for name, param in model.named_parameters():
            if "lora" not in name.lower():
                param.requires_grad = False

        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=1e-5
        )
        baseline = MovingAverageBaseline(momentum=0.9)

        rollouts = [
            _make_rollout("Fix A", '{"tool": "submit", "arguments": {}}', 1.0),
            _make_rollout("Fix B", '{"tool": "submit", "arguments": {}}', 0.5),
        ]

        result = reinforce_update(model, tokenizer, rollouts, baseline, optimizer)

        assert baseline.initialized is False
        assert baseline.value == pytest.approx(0.0)
        assert result.baseline == pytest.approx(0.0)
