"""Tests for action_parser: extracting JSON actions from LLM output."""

from minirepair.agents.action_parser import extract_action_from_llm_output, extract_json_candidates
from minirepair.env.action_schema import Action, ParseError, ToolName


class TestExtractJsonCandidates:
    def test_raw_json(self):
        text = '{"tool": "read_file", "arguments": {"path": "src/main.py"}}'
        candidates = extract_json_candidates(text)
        assert len(candidates) >= 1
        assert candidates[0] == text

    def test_markdown_code_block(self):
        text = 'Here is my action:\n```json\n{"tool": "submit", "arguments": {}}\n```'
        candidates = extract_json_candidates(text)
        assert any(c.strip() == '{"tool": "submit", "arguments": {}}' for c in candidates)

    def test_code_block_without_json_tag(self):
        text = '```\n{"tool": "run_tests", "arguments": {"test_dir": "tests"}}\n```'
        candidates = extract_json_candidates(text)
        assert len(candidates) >= 1

    def test_json_embedded_in_thought(self):
        text = 'I think I should read the file first. {"tool": "read_file", "arguments": {"path": "src/a.py"}} Let me do that.'
        candidates = extract_json_candidates(text)
        assert len(candidates) >= 1

    def test_no_json(self):
        candidates = extract_json_candidates("I don't know what to do.")
        assert candidates == []

    def test_nested_braces(self):
        text = 'Thought: I need to edit. {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "def f():\\n    pass", "new_text": "def f():\\n    return 1"}}'
        candidates = extract_json_candidates(text)
        assert len(candidates) >= 1


class TestExtractActionFromLlmOutput:
    def test_raw_json(self):
        text = '{"tool": "read_file", "arguments": {"path": "src/main.py"}}'
        result = extract_action_from_llm_output(text)
        assert isinstance(result, Action)
        assert result.tool == ToolName.READ_FILE
        assert result.arguments.path == "src/main.py"

    def test_markdown_block(self):
        text = 'Let me read the buggy file.\n```json\n{"tool": "read_file", "arguments": {"path": "src/string_utils.py"}}\n```'
        result = extract_action_from_llm_output(text)
        assert isinstance(result, Action)
        assert result.tool == ToolName.READ_FILE

    def test_edit_action(self):
        text = '{"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}}'
        result = extract_action_from_llm_output(text)
        assert isinstance(result, Action)
        assert result.tool == ToolName.EDIT_FILE
        assert result.arguments.old_text == "x"

    def test_submit_action(self):
        text = '{"tool": "submit", "arguments": {}}'
        result = extract_action_from_llm_output(text)
        assert isinstance(result, Action)
        assert result.tool == ToolName.SUBMIT

    def test_no_json_returns_parse_error(self):
        result = extract_action_from_llm_output("I don't know what to do.")
        assert isinstance(result, ParseError)
        assert "No JSON object found" in result.error

    def test_invalid_json_returns_parse_error(self):
        result = extract_action_from_llm_output("{broken json")
        assert isinstance(result, ParseError)

    def test_missing_tool_returns_parse_error(self):
        result = extract_action_from_llm_output('{"arguments": {"path": "x.py"}}')
        assert isinstance(result, ParseError)

    def test_invalid_tool_name_returns_parse_error(self):
        result = extract_action_from_llm_output('{"tool": "invalid_tool"}')
        assert isinstance(result, ParseError)
