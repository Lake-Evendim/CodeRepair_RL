"""Tests for SFTPolicy (mock-based, no real model download)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from minirepair.agents.react_agent import Policy


class TestSFTPolicyInterface:
    """Test SFTPolicy without loading real models."""

    def test_sft_policy_is_policy_subclass(self):
        from minirepair.agents.sft_policy import SFTPolicy

        assert issubclass(SFTPolicy, Policy)

    def test_sft_policy_type(self, tmp_path: Path):
        from minirepair.agents.sft_policy import SFTPolicy

        policy = SFTPolicy(
            base_model_name="mock-model",
            adapter_path=str(tmp_path / "fake_adapter"),
        )
        assert policy.policy_type == "sft_qwen_lora"

    @patch("minirepair.agents.sft_policy.SFTPolicy._load_model")
    def test_sft_policy_generate_returns_string(self, mock_load: MagicMock, tmp_path: Path):
        from minirepair.agents.sft_policy import SFTPolicy

        policy = SFTPolicy(
            base_model_name="mock-model",
            adapter_path=str(tmp_path / "fake_adapter"),
        )

        # Mock the model and tokenizer
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "test prompt"

        mock_input_ids = MagicMock()
        mock_input_ids.shape = (1, 10)
        mock_attention_mask = MagicMock()

        mock_tokenizer.return_value = {
            "input_ids": mock_input_ids,
            "attention_mask": mock_attention_mask,
        }
        mock_tokenizer.decode.return_value = '{"tool": "read_file", "arguments": {"path": "src/test.py"}}'
        mock_model.device = "cpu"
        mock_model.generate.return_value = MagicMock()

        policy._model = mock_model
        policy._tokenizer = mock_tokenizer

        result = policy.generate("test prompt")
        assert isinstance(result, str)
        assert "read_file" in result

    def test_sft_policy_lazy_load(self, tmp_path: Path):
        """Model should not be loaded until generate() is called."""
        from minirepair.agents.sft_policy import SFTPolicy

        policy = SFTPolicy(
            base_model_name="mock-model",
            adapter_path=str(tmp_path / "fake_adapter"),
        )
        assert policy._model is None
        assert policy._tokenizer is None
