"""Tests for action_schema module."""

import json

from minirepair.env.action_schema import Action, ParseError, ToolArguments, ToolName, parse_action


class TestToolName:
    def test_all_values(self):
        assert ToolName.READ_FILE == "read_file"
        assert ToolName.SEARCH_CODE == "search_code"
        assert ToolName.EDIT_FILE == "edit_file"
        assert ToolName.RUN_TESTS == "run_tests"
        assert ToolName.SUBMIT == "submit"


class TestAction:
    def test_create_action(self):
        action = Action(tool=ToolName.READ_FILE, arguments=ToolArguments(path="src/foo.py"))
        assert action.tool == ToolName.READ_FILE
        assert action.arguments.path == "src/foo.py"

    def test_default_arguments(self):
        action = Action(tool=ToolName.SUBMIT)
        assert action.arguments.path is None
        assert action.arguments.max_lines == 200


class TestParseAction:
    def test_parse_valid_json(self):
        raw = json.dumps({"tool": "read_file", "arguments": {"path": "src/foo.py"}})
        result = parse_action(raw)
        assert isinstance(result, Action)
        assert result.tool == ToolName.READ_FILE
        assert result.arguments.path == "src/foo.py"

    def test_parse_valid_dict(self):
        raw = {"tool": "submit"}
        result = parse_action(raw)
        assert isinstance(result, Action)
        assert result.tool == ToolName.SUBMIT

    def test_parse_invalid_json(self):
        result = parse_action("not json {{{")
        assert isinstance(result, ParseError)
        assert "Invalid JSON" in result.error

    def test_parse_missing_tool(self):
        result = parse_action({"arguments": {"path": "x"}})
        assert isinstance(result, ParseError)
        assert "Missing 'tool'" in result.error

    def test_parse_invalid_tool(self):
        result = parse_action({"tool": "nonexistent"})
        assert isinstance(result, ParseError)

    def test_parse_non_dict(self):
        result = parse_action([1, 2, 3])
        assert isinstance(result, ParseError)
        assert "Expected dict" in result.error
