"""Structured action schema for CodeRepairEnv tools."""

from __future__ import annotations

from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, Field


class ToolName(str, Enum):
    READ_FILE = "read_file"
    SEARCH_CODE = "search_code"
    EDIT_FILE = "edit_file"
    RUN_TESTS = "run_tests"
    SUBMIT = "submit"


class ToolArguments(BaseModel):
    path: str | None = None
    old_text: str | None = None
    new_text: str | None = None
    query: str | None = None
    max_lines: int = 200
    test_dir: str = "tests"


class Action(BaseModel):
    tool: ToolName
    arguments: ToolArguments = Field(default_factory=ToolArguments)


class ParseError(BaseModel):
    error: str
    raw_input: str


def parse_action(raw: Union[str, dict[str, Any]]) -> Action | ParseError:
    """Parse a JSON string or dict into an Action. Returns ParseError on failure."""
    if isinstance(raw, str):
        try:
            import json

            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            return ParseError(error=f"Invalid JSON: {e}", raw_input=raw)

    if not isinstance(raw, dict):
        return ParseError(error=f"Expected dict, got {type(raw).__name__}", raw_input=str(raw))

    if "tool" not in raw:
        return ParseError(error="Missing 'tool' field", raw_input=str(raw))

    try:
        return Action(**raw)
    except Exception as e:
        return ParseError(error=str(e), raw_input=str(raw))
