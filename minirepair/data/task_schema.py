"""Task metadata and gold patch schema for MiniRepair-RL benchmark."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GoldPatch(BaseModel):
    """A single-file code patch: exact string replacement."""

    file_path: str = Field(description="Relative path to the file to patch, e.g. 'src/string_utils.py'")
    old_text: str = Field(description="Exact text to find in the file (must appear exactly once)")
    new_text: str = Field(description="Replacement text")


class TaskMetadata(BaseModel):
    """Metadata for a single benchmark task."""

    task_id: str = Field(description="Unique task identifier, e.g. 'task_0001'")
    repo_type: Literal["string_utils", "validators"] = Field(description="Which repo template this task uses")
    bug_type: Literal["boundary", "string_validation"] = Field(description="Category of the injected bug")
    bug_description: str = Field(description="Human-readable description of the bug")
    gold_patch: GoldPatch = Field(description="The patch that fixes the bug")
    split: Literal["seed", "train", "validation", "test"] = Field(
        default="seed", description="Which dataset split this task belongs to"
    )
