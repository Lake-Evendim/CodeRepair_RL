"""Tests for SFT training module (mock-based, no real GPU/model required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_module(name: str, **attrs: object) -> ModuleType:
    """Create a mock module with given attributes."""
    mod = ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


class TestTrainSft:
    """Test train_sft without requiring GPU or model download."""

    def test_train_sft_dry_run_with_mocks(self, tmp_path: Path):
        """Dry-run should work with mocked transformers/trl/peft."""
        # Create a minimal SFT JSONL
        sample = {
            "messages": [
                {"role": "system", "content": "You are a code repair agent."},
                {"role": "user", "content": "Fix the bug."},
                {"role": "assistant", "content": '{"tool": "read_file", "arguments": {"path": "src/test.py"}}'},
            ],
        }
        data_path = tmp_path / "sft_train.jsonl"
        data_path.write_text(json.dumps(sample) + "\n")

        config = {
            "model_name": "mock-model",
            "dataset_path": str(data_path),
            "output_dir": str(tmp_path / "adapter"),
            "lora_r": 4,
            "lora_alpha": 8,
            "batch_size": 1,
            "epochs": 1,
            "learning_rate": 1e-4,
            "dry_run": {"max_samples": 2, "max_steps": 1},
        }

        # Build mock modules
        mock_tokenizer = MagicMock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = "eos"
        mock_tokenizer.apply_chat_template.return_value = "formatted"

        mock_model = MagicMock()

        mock_transformers = MagicMock()
        mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
        mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model

        mock_peft = MagicMock()
        mock_peft.get_peft_model.return_value = mock_model

        mock_trl = MagicMock()
        mock_trainer = MagicMock()
        mock_trl.SFTTrainer.return_value = mock_trainer

        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=1)
        mock_dataset.column_names = ["messages"]
        mock_dataset.select.return_value = mock_dataset
        mock_dataset.map.return_value = mock_dataset

        mock_datasets = MagicMock()
        mock_datasets.load_dataset.return_value = mock_dataset

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        # Inject mock modules into sys.modules so lazy imports find them
        mock_modules = {
            "transformers": mock_transformers,
            "peft": mock_peft,
            "trl": mock_trl,
            "datasets": mock_datasets,
            "torch": mock_torch,
        }

        with patch.dict(sys.modules, mock_modules):
            # Force reimport so lazy imports pick up mocked modules
            if "minirepair.training.train_sft" in sys.modules:
                del sys.modules["minirepair.training.train_sft"]

            from minirepair.training.train_sft import train_sft

            output = train_sft(config, dry_run=True)

            assert output == tmp_path / "adapter"
            mock_trainer.train.assert_called_once()
            mock_model.save_pretrained.assert_called_once()

    def test_train_sft_requires_train_split(self):
        """The build_sft_dataset function rejects non-train splits."""
        from scripts.build_sft_dataset import build_sft_dataset

        with pytest.raises(ValueError, match="source_split must be one of"):
            build_sft_dataset(
                benchmark_root=Path("benchmarks"),
                source_split="validation",
                output_train=Path("/tmp/train.jsonl"),
                output_dev=Path("/tmp/dev.jsonl"),
            )


class TestEvaluateCli:
    """Test evaluate.py CLI without real models."""

    def test_evaluate_requires_adapter_for_rl_methods(self):
        """rl_sparse and rl_dense should require --adapter."""
        from scripts.evaluate import build_policy

        with pytest.raises(ValueError, match="--adapter"):
            build_policy(method="rl_sparse")

        with pytest.raises(ValueError, match="--adapter"):
            build_policy(method="rl_dense")

    def test_evaluate_rejects_unknown_method(self):
        """Unknown methods should raise ValueError."""
        from scripts.evaluate import build_policy

        with pytest.raises(ValueError, match="Unknown method"):
            build_policy(method="nonexistent")

    def test_evaluate_sft_requires_adapter(self):
        """SFT method requires --adapter."""
        from scripts.evaluate import build_policy

        with pytest.raises(ValueError, match="--adapter is required"):
            build_policy(method="sft")
