"""Tests for failure taxonomy classification."""

from minirepair.evaluation.failure_taxonomy import (
    FAILURE_CATEGORIES,
    classify_failure,
    get_failure_summary,
)


def _base_metrics(**overrides) -> dict:
    """Build a minimal metrics dict with sensible defaults."""
    m = {
        "task_id": "task_0001",
        "public_pass": False,
        "private_pass": False,
        "hidden_pass": None,
        "total_steps": 4,
        "invalid_action_count": 0,
        "invalid_edit_count": 0,
        "regression_count": 0,
        "submit_before_test": False,
        "guardrail_violation_count": 0,
        "termination_reason": "max_steps",
        "read_count": 1,
        "search_count": 0,
        "edit_count": 1,
        "test_count": 1,
        "submit_count": 0,
        "repeated_test_call_rate": 0.0,
        "patch_modified_lines": 3,
        "patch_modified_files": 1,
    }
    m.update(overrides)
    return m


class TestClassifyFailure:
    def test_passed_episode(self):
        """A passing episode should not be classified as a failure."""
        m = _base_metrics(public_pass=True)
        result = classify_failure([], m)
        assert result["passed"] is True
        assert result["primary"] is None
        assert result["all_categories"] == []

    def test_invalid_action(self):
        """Episodes with invalid actions should be flagged."""
        m = _base_metrics(invalid_action_count=2)
        result = classify_failure([], m)
        assert "invalid_action" in result["all_categories"]
        assert result["passed"] is False

    def test_invalid_edit(self):
        """Episodes with invalid edits should be flagged."""
        m = _base_metrics(invalid_edit_count=1)
        result = classify_failure([], m)
        assert "invalid_edit" in result["all_categories"]

    def test_premature_submit(self):
        """Submitting without running tests should be flagged."""
        m = _base_metrics(submit_before_test=True, test_count=0)
        result = classify_failure([], m)
        assert "premature_submit" in result["all_categories"]

    def test_regression_error(self):
        """Episodes with regressions should be flagged."""
        m = _base_metrics(regression_count=1)
        result = classify_failure([], m)
        assert "regression_error" in result["all_categories"]

    def test_tool_misuse(self):
        """Heavy reading/searching without edits should be flagged."""
        m = _base_metrics(edit_count=0, read_count=3, search_count=2, total_steps=5)
        result = classify_failure([], m)
        assert "tool_misuse" in result["all_categories"]

    def test_context_misunderstanding(self):
        """Reading/searching without edits (but below tool_misuse threshold)."""
        m = _base_metrics(edit_count=0, read_count=1, search_count=1, total_steps=2)
        result = classify_failure([], m)
        assert "context_misunderstanding" in result["all_categories"]
        assert "tool_misuse" not in result["all_categories"]

    def test_localization_error(self):
        """Editing but failing public tests should be flagged."""
        m = _base_metrics(edit_count=1, public_pass=False)
        result = classify_failure([], m)
        assert "localization_error" in result["all_categories"]

    def test_semantic_patch_error(self):
        """Editing + testing but still failing should be flagged."""
        m = _base_metrics(edit_count=1, test_count=1, public_pass=False)
        result = classify_failure([], m)
        assert "semantic_patch_error" in result["all_categories"]

    def test_reward_hacking_attempt(self):
        """Trajectory with reward hacking warnings should be flagged."""
        traj = [
            {
                "action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}},
                "observation": {
                    "status": "success",
                    "content": "",
                    "error": "",
                    "tool_name": "edit_file",
                    "info": {"warnings": [{"rule": "potential_reward_hacking", "message": "suspicious"}]},
                },
            },
        ]
        m = _base_metrics(guardrail_violation_count=1)
        result = classify_failure(traj, m)
        assert "reward_hacking_attempt" in result["all_categories"]

    def test_primary_is_first_in_priority(self):
        """Primary failure should be the highest-priority matching category."""
        m = _base_metrics(
            invalid_action_count=1,
            edit_count=1,
            test_count=1,
            public_pass=False,
        )
        result = classify_failure([], m)
        # invalid_action has higher priority than semantic_patch_error
        assert result["primary"] == "invalid_action"

    def test_multiple_categories(self):
        """An episode can match multiple failure categories."""
        m = _base_metrics(
            invalid_action_count=1,
            invalid_edit_count=1,
            regression_count=1,
            edit_count=1,
            test_count=1,
            public_pass=False,
        )
        result = classify_failure([], m)
        assert len(result["all_categories"]) >= 4
        assert "invalid_action" in result["all_categories"]
        assert "invalid_edit" in result["all_categories"]
        assert "regression_error" in result["all_categories"]
        assert "semantic_patch_error" in result["all_categories"]

    def test_all_categories_covered(self):
        """Each failure category should be triggerable."""
        # This test ensures FAILURE_CATEGORIES is consistent
        assert len(FAILURE_CATEGORIES) == 9
        assert set(FAILURE_CATEGORIES) == {
            "invalid_action", "invalid_edit", "reward_hacking_attempt",
            "premature_submit", "regression_error", "tool_misuse",
            "context_misunderstanding", "localization_error", "semantic_patch_error",
        }


class TestGetFailureSummary:
    def test_empty_metrics(self):
        summary = get_failure_summary([])
        assert summary["total_failed"] == 0

    def test_mixed_pass_fail(self):
        metrics = [
            _base_metrics(task_id="t1", public_pass=True),
            _base_metrics(task_id="t2", public_pass=False, invalid_action_count=1, edit_count=0, test_count=0),
            _base_metrics(task_id="t3", public_pass=False, edit_count=1, test_count=1, invalid_action_count=0),
        ]
        summary = get_failure_summary(metrics)
        assert summary["total_failed"] == 2
        assert summary["failure_counts"]["invalid_action"] == 1
        assert summary["failure_counts"]["localization_error"] == 1
        assert summary["failure_counts"]["semantic_patch_error"] == 1

    def test_category_task_ids(self):
        metrics = [
            _base_metrics(task_id="t1", public_pass=False, invalid_action_count=1),
            _base_metrics(task_id="t2", public_pass=False, invalid_action_count=1),
        ]
        summary = get_failure_summary(metrics)
        assert "t1" in summary["category_task_ids"]["invalid_action"]
        assert "t2" in summary["category_task_ids"]["invalid_action"]
