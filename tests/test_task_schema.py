"""Unit tests for task schema."""

import pytest

from minirepair.data.task_schema import GoldPatch, TaskMetadata


class TestGoldPatch:
    def test_valid_creation(self):
        patch = GoldPatch(file_path="src/foo.py", old_text="old", new_text="new")
        assert patch.file_path == "src/foo.py"
        assert patch.old_text == "old"
        assert patch.new_text == "new"

    def test_missing_field(self):
        with pytest.raises(Exception):
            GoldPatch(file_path="src/foo.py")  # missing old_text and new_text


class TestTaskMetadata:
    def test_valid_string_utils_task(self):
        meta = TaskMetadata(
            task_id="task_0001",
            repo_type="string_utils",
            bug_type="boundary",
            bug_description="off-by-one error",
            gold_patch=GoldPatch(file_path="src/string_utils.py", old_text="old", new_text="new"),
        )
        assert meta.task_id == "task_0001"
        assert meta.split == "seed"  # default

    def test_valid_validators_task(self):
        meta = TaskMetadata(
            task_id="task_0011",
            repo_type="validators",
            bug_type="string_validation",
            bug_description="missing check",
            gold_patch=GoldPatch(file_path="src/validators.py", old_text="a", new_text="b"),
            split="train",
        )
        assert meta.repo_type == "validators"
        assert meta.split == "train"

    def test_invalid_repo_type(self):
        with pytest.raises(Exception):
            TaskMetadata(
                task_id="task_9999",
                repo_type="invalid_repo",  # type: ignore
                bug_type="boundary",
                bug_description="test",
                gold_patch=GoldPatch(file_path="src/foo.py", old_text="a", new_text="b"),
            )

    def test_invalid_bug_type(self):
        with pytest.raises(Exception):
            TaskMetadata(
                task_id="task_9999",
                repo_type="string_utils",
                bug_type="invalid_bug",  # type: ignore
                bug_description="test",
                gold_patch=GoldPatch(file_path="src/foo.py", old_text="a", new_text="b"),
            )

    def test_invalid_split(self):
        with pytest.raises(Exception):
            TaskMetadata(
                task_id="task_9999",
                repo_type="string_utils",
                bug_type="boundary",
                bug_description="test",
                gold_patch=GoldPatch(file_path="src/foo.py", old_text="a", new_text="b"),
                split="invalid_split",  # type: ignore
            )

    def test_task_id_required(self):
        with pytest.raises(Exception):
            TaskMetadata(
                repo_type="string_utils",
                bug_type="boundary",
                bug_description="test",
                gold_patch=GoldPatch(file_path="src/foo.py", old_text="a", new_text="b"),
            )
