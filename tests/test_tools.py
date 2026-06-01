"""Tests for tools module."""

from pathlib import Path

from minirepair.env.action_schema import Action, ToolArguments, ToolName
from minirepair.env.sandbox import Sandbox
from minirepair.env.tools import ToolState, execute_tool, read_file, search_code, submit

SEED_TASK = Path(__file__).resolve().parent.parent / "benchmarks" / "tasks" / "seed" / "task_0001" / "repo"


class TestReadFile:
    def test_read_existing_file(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.READ_FILE, arguments=ToolArguments(path="src/string_utils.py"))
            obs = read_file(sandbox, action)
            assert obs.status == "success"
            assert "def truncate_string" in obs.content

    def test_read_nonexistent_file(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.READ_FILE, arguments=ToolArguments(path="src/nonexistent.py"))
            obs = read_file(sandbox, action)
            assert obs.status == "error"
            assert "not found" in obs.error

    def test_read_missing_path(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.READ_FILE)
            obs = read_file(sandbox, action)
            assert obs.status == "error"
            assert "Missing" in obs.error

    def test_read_path_escape(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.READ_FILE, arguments=ToolArguments(path="../secret.py"))
            obs = read_file(sandbox, action)
            assert obs.status == "error"

    def test_read_truncation(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(
                tool=ToolName.READ_FILE,
                arguments=ToolArguments(path="tests/test_string_utils.py", max_lines=5),
            )
            obs = read_file(sandbox, action)
            assert obs.status == "success"
            assert obs.info.get("truncated") is True
            assert obs.info["returned_lines"] == 5


class TestSearchCode:
    def test_search_match(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.SEARCH_CODE, arguments=ToolArguments(query="truncate"))
            obs = search_code(sandbox, action)
            assert obs.status == "success"
            assert "truncate" in obs.content.lower()

    def test_search_no_match(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.SEARCH_CODE, arguments=ToolArguments(query="xyznonexistent"))
            obs = search_code(sandbox, action)
            assert obs.status == "success"
            assert "No matches" in obs.content

    def test_search_missing_query(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.SEARCH_CODE)
            obs = search_code(sandbox, action)
            assert obs.status == "error"
            assert "Missing" in obs.error


class TestEditFile:
    def test_edit_success(self):
        with Sandbox(SEED_TASK) as sandbox:
            state = ToolState()
            action = Action(
                tool=ToolName.EDIT_FILE,
                arguments=ToolArguments(
                    path="src/string_utils.py",
                    old_text="    return s[: max_len] + \"...\"",
                    new_text="    return s[: max_len - 3] + \"...\"",
                ),
            )
            result = execute_tool(sandbox, action, state)
            assert result.status == "success"
            assert state.edit_count == 1

    def test_edit_budget_exceeded(self):
        with Sandbox(SEED_TASK) as sandbox:
            state = ToolState(edit_count=2, episode_edit_limit=2)
            action = Action(
                tool=ToolName.EDIT_FILE,
                arguments=ToolArguments(
                    path="src/string_utils.py",
                    old_text="old",
                    new_text="new",
                ),
            )
            result = execute_tool(sandbox, action, state)
            assert result.status == "error"
            assert "budget" in result.error.lower()

    def test_edit_forbidden_path(self):
        with Sandbox(SEED_TASK) as sandbox:
            state = ToolState()
            action = Action(
                tool=ToolName.EDIT_FILE,
                arguments=ToolArguments(
                    path="tests/test_string_utils.py",
                    old_text="old",
                    new_text="new",
                ),
            )
            result = execute_tool(sandbox, action, state)
            assert result.status == "error"
            assert "Guardrail" in result.error or "forbidden" in result.error.lower()

    def test_edit_old_text_not_unique(self):
        with Sandbox(SEED_TASK) as sandbox:
            state = ToolState()
            action = Action(
                tool=ToolName.EDIT_FILE,
                arguments=ToolArguments(
                    path="src/string_utils.py",
                    old_text="return",
                    new_text="xxx",
                ),
            )
            result = execute_tool(sandbox, action, state)
            assert result.status == "error"


class TestRunTests:
    def test_run_tests_on_buggy(self):
        with Sandbox(SEED_TASK) as sandbox:
            state = ToolState()
            action = Action(tool=ToolName.RUN_TESTS)
            result = execute_tool(sandbox, action, state)
            assert result.tool_name == "run_tests"
            assert state.test_count == 1

    def test_run_tests_budget_exceeded(self):
        with Sandbox(SEED_TASK) as sandbox:
            state = ToolState(test_count=2, episode_test_limit=2)
            action = Action(tool=ToolName.RUN_TESTS)
            result = execute_tool(sandbox, action, state)
            assert result.status == "error"
            assert "budget" in result.error.lower()


class TestSubmit:
    def test_submit(self):
        with Sandbox(SEED_TASK) as sandbox:
            action = Action(tool=ToolName.SUBMIT)
            obs = submit(sandbox, action)
            assert obs.status == "submitted"
