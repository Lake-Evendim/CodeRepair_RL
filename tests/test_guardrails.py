"""Tests for guardrails module."""

from pathlib import Path

from minirepair.env.action_schema import Action, ToolArguments, ToolName
from minirepair.env.guardrails import check_edit

# Use a real task repo for testing
SEED_TASK = Path(__file__).resolve().parent.parent / "benchmarks" / "tasks" / "seed" / "task_0001" / "repo"


def _make_edit_action(path: str, old_text: str, new_text: str) -> Action:
    return Action(
        tool=ToolName.EDIT_FILE,
        arguments=ToolArguments(path=path, old_text=old_text, new_text=new_text),
    )


class TestForbiddenPaths:
    def test_forbid_tests_dir(self):
        action = _make_edit_action("tests/test_foo.py", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_path" in rules

    def test_forbid_tests_private_dir(self):
        action = _make_edit_action("tests_private/test_foo.py", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_path" in rules

    def test_forbid_tests_hidden_dir(self):
        action = _make_edit_action("tests_hidden/test_foo.py", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_path" in rules

    def test_forbid_tests_quality_holdout_dir(self):
        action = _make_edit_action("tests_quality_holdout/test_foo.py", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_path" in rules

    def test_forbid_pyproject_toml(self):
        action = _make_edit_action("pyproject.toml", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_file" in rules

    def test_forbid_conftest_py(self):
        action = _make_edit_action("conftest.py", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_file" in rules

    def test_forbid_requirements_txt(self):
        action = _make_edit_action("requirements.txt", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_file" in rules

    def test_allow_src_file(self):
        action = _make_edit_action("src/string_utils.py", "old", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "forbidden_path" not in rules
        assert "forbidden_file" not in rules


class TestOldTextUniqueness:
    def test_old_text_not_found(self):
        action = _make_edit_action("src/string_utils.py", "nonexistent_text", "new")
        violations = check_edit(SEED_TASK, action, 0)
        rules = [v.rule for v in violations]
        assert "old_text_not_found" in rules

    def test_old_text_multiple_matches(self):
        action = _make_edit_action("src/string_utils.py", "return", "new")
        violations = check_edit(SEED_TASK, action, 5)
        rules = [v.rule for v in violations]
        assert "old_text_not_unique" in rules

    def test_old_text_unique(self):
        action = _make_edit_action("src/string_utils.py", "unique_text", "new")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "old_text_not_found" not in rules
        assert "old_text_not_unique" not in rules


class TestSkipPatterns:
    def test_pytest_skip_in_new_text(self):
        action = _make_edit_action("src/foo.py", "old", "pytest.skip('reason')")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "skip_pattern" in rules

    def test_pytest_xfail_in_new_text(self):
        action = _make_edit_action("src/foo.py", "old", "pytest.xfail('reason')")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "skip_pattern" in rules

    def test_no_skip_pattern(self):
        action = _make_edit_action("src/foo.py", "old", "return result")
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "skip_pattern" not in rules


class TestAssertDeletion:
    def test_delete_assert(self):
        old = "    assert x == 1\n    return x"
        new = "    return x"
        action = _make_edit_action("src/foo.py", old, new)
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "assert_deletion" in rules

    def test_keep_assert(self):
        old = "    x = 1"
        new = "    assert x == 1\n    x = 1"
        action = _make_edit_action("src/foo.py", old, new)
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "assert_deletion" not in rules


class TestLineLimit:
    def test_within_limit(self):
        new_text = "line1\nline2\nline3"
        action = _make_edit_action("src/foo.py", "old", new_text)
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "line_limit" not in rules

    def test_exceeds_limit(self):
        new_text = "\n".join([f"line{i}" for i in range(10)])
        action = _make_edit_action("src/foo.py", "old", new_text)
        violations = check_edit(SEED_TASK, action, 1)
        rules = [v.rule for v in violations]
        assert "line_limit" in rules


class TestRewardHackingHeuristic:
    def test_single_return_fixed_value(self):
        action = _make_edit_action("src/foo.py", "old", "    return [1, 2, 3]")
        violations = check_edit(SEED_TASK, action, 1)
        warnings = [v for v in violations if v.severity == "warn"]
        assert any(v.rule == "potential_reward_hacking" for v in warnings)

    def test_normal_edit_no_warning(self):
        action = _make_edit_action("src/foo.py", "old", "    x = x + 1\n    return x")
        violations = check_edit(SEED_TASK, action, 1)
        warnings = [v for v in violations if v.severity == "warn"]
        assert not any(v.rule == "potential_reward_hacking" for v in warnings)


class TestNonEditTool:
    def test_non_edit_action_no_violations(self):
        action = Action(tool=ToolName.READ_FILE, arguments=ToolArguments(path="src/foo.py"))
        violations = check_edit(SEED_TASK, action, 0)
        assert violations == []
