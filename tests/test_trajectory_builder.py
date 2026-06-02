"""Tests for trajectory_builder: SFT sample construction."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from minirepair.data.task_schema import GoldPatch, TaskMetadata
from minirepair.data.trajectory_builder import (
    build_gold_action_sequence,
    build_search_first_sequence,
    build_sft_samples_from_task,
)


@pytest.fixture
def sample_task(tmp_path: Path) -> Path:
    """Create a minimal task directory for testing."""
    task_dir = tmp_path / "task_test"
    task_dir.mkdir()

    # Create metadata
    metadata = TaskMetadata(
        task_id="task_test",
        repo_type="string_utils",
        bug_type="boundary",
        bug_description="Test bug",
        gold_patch=GoldPatch(
            file_path="src/string_utils.py",
            old_text='def is_empty(s):\n    return s == ""',
            new_text="def is_empty(s):\n    return len(s) == 0",
        ),
        split="train",
    )
    (task_dir / "metadata.json").write_text(metadata.model_dump_json(indent=2))

    # Create repo structure
    repo = task_dir / "repo"
    src = repo / "src"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "string_utils.py").write_text(
        'def is_empty(s):\n    return s == ""\n\ndef hello():\n    return "hello"\n'
    )

    tests = repo / "tests"
    tests.mkdir()
    (tests / "__init__.py").write_text("")
    (tests / "test_string_utils.py").write_text(
        "from src.string_utils import is_empty\n\ndef test_empty():\n    assert is_empty('') == True\n"
    )

    return task_dir


class TestBuildGoldActionSequence:
    def test_basic_sequence(self, sample_task: Path):
        metadata = TaskMetadata(**json.loads((sample_task / "metadata.json").read_text()))
        seq = build_gold_action_sequence(metadata)

        assert len(seq) == 4
        assert seq[0]["tool"] == "read_file"
        assert seq[1]["tool"] == "edit_file"
        assert seq[2]["tool"] == "run_tests"
        assert seq[3]["tool"] == "submit"
        assert seq[1]["arguments"]["old_text"] == metadata.gold_patch.old_text
        assert seq[1]["arguments"]["new_text"] == metadata.gold_patch.new_text


class TestBuildSearchFirstSequence:
    def test_search_first_sequence(self, sample_task: Path):
        metadata = TaskMetadata(**json.loads((sample_task / "metadata.json").read_text()))
        seq = build_search_first_sequence(metadata)

        assert len(seq) == 5
        assert seq[0]["tool"] == "search_code"
        assert seq[1]["tool"] == "read_file"
        assert seq[2]["tool"] == "edit_file"
        assert seq[3]["tool"] == "run_tests"
        assert seq[4]["tool"] == "submit"


class TestBuildSftSamplesFromTask:
    def test_samples_structure(self, sample_task: Path):
        rng = random.Random(42)
        samples = build_sft_samples_from_task(sample_task, rng=rng, include_search_first=False)

        assert len(samples) == 4  # 4 steps in standard sequence

        for sample in samples:
            assert "messages" in sample
            messages = sample["messages"]
            assert len(messages) == 3
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[2]["role"] == "assistant"

            # Assistant content must be valid JSON
            action = json.loads(messages[2]["content"])
            assert "tool" in action
            assert action["tool"] in ("read_file", "edit_file", "run_tests", "submit")

    def test_gold_patch_metadata_not_in_prompts(self, sample_task: Path):
        """Gold patch metadata must not be explicitly included in prompts.

        Note: When replaying gold actions through the env, the agent's own
        recorded actions (e.g. edit_file with old_text/new_text) may appear
        in history-based prompts. This is acceptable because it reflects what
        the agent actually did. The constraint is that gold_patch metadata
        itself is not injected into prompts.
        """
        rng = random.Random(42)
        samples = build_sft_samples_from_task(sample_task, rng=rng, include_search_first=False)

        for sample in samples:
            system = sample["messages"][0]["content"]

            # Gold patch metadata should not be explicitly included in system prompt
            assert "gold_patch" not in system.lower()

            # The assistant target must be valid JSON with tool field
            target = json.loads(sample["messages"][2]["content"])
            assert "tool" in target

    def test_new_text_only_in_edit_action_target(self, sample_task: Path):
        """The fix (new_text) should only appear as the assistant target for edit_file steps,
        not injected into system prompts or other assistant targets."""
        rng = random.Random(42)
        samples = build_sft_samples_from_task(sample_task, rng=rng, include_search_first=False)

        for sample in samples:
            system = sample["messages"][0]["content"]
            target = json.loads(sample["messages"][2]["content"])

            if target["tool"] != "edit_file":
                # Non-edit steps should not contain the fix in their target
                target_str = json.dumps(target)
                assert "len(s) == 0" not in target_str

            # System prompt should never contain the fix
            assert "len(s) == 0" not in system

    def test_search_first_variant(self, sample_task: Path):
        rng = random.Random(42)
        samples = build_sft_samples_from_task(sample_task, rng=rng, include_search_first=True)

        # Should have 4 (standard) + 5 (search_first) = 9 samples
        assert len(samples) == 9

        # Check that one of the first samples is search_code
        tools = [json.loads(s["messages"][2]["content"])["tool"] for s in samples[:5]]
        assert "search_code" in tools

    def test_no_private_hidden_leakage(self, sample_task: Path):
        """Ensure no private/hidden test content in prompts."""
        rng = random.Random(42)
        samples = build_sft_samples_from_task(sample_task, rng=rng)

        for sample in samples:
            for msg in sample["messages"]:
                content = msg["content"].lower()
                assert "tests_private" not in content
                assert "tests_hidden" not in content

    def test_metadata_fields(self, sample_task: Path):
        rng = random.Random(42)
        samples = build_sft_samples_from_task(sample_task, rng=rng, include_search_first=False)

        for sample in samples:
            meta = sample["metadata"]
            assert meta["task_id"] == "task_test"
            assert meta["split"] == "train"
            assert meta["tool"] in ("read_file", "edit_file", "run_tests", "submit")
            assert meta["variant"] == "standard"


class TestBuildSftDatasetRejection:
    def test_rejects_validation_split(self, tmp_path: Path):
        """build_sft_dataset must reject source_split=validation."""
        from scripts.build_sft_dataset import build_sft_dataset

        with pytest.raises(ValueError, match="source_split must be one of"):
            build_sft_dataset(
                benchmark_root=tmp_path,
                source_split="validation",
                output_train=tmp_path / "train.jsonl",
                output_dev=tmp_path / "dev.jsonl",
            )

    def test_rejects_test_split(self, tmp_path: Path):
        """build_sft_dataset must reject source_split=test."""
        from scripts.build_sft_dataset import build_sft_dataset

        with pytest.raises(ValueError, match="source_split must be one of"):
            build_sft_dataset(
                benchmark_root=tmp_path,
                source_split="test",
                output_train=tmp_path / "train.jsonl",
                output_dev=tmp_path / "dev.jsonl",
            )
