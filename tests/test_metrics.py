"""Tests for metrics computation."""

import csv
from pathlib import Path

import pytest

from minirepair.evaluation.metrics import (
    EvalMode,
    aggregate_metrics,
    compute_episode_metrics,
    write_metrics_csv,
)


def _make_trajectory(steps: list[dict] | None = None, termination: str = "submitted") -> list[dict]:
    """Helper to build a minimal trajectory."""
    if steps is None:
        steps = [
            {
                "action": {"tool": "read_file", "arguments": {"path": "src/a.py"}},
                "observation": {"status": "success", "content": "...", "error": "", "tool_name": "read_file", "info": {}},
            },
            {
                "action": {"tool": "submit", "arguments": {}},
                "observation": {"status": "submitted", "content": "Episode submitted", "error": "", "tool_name": "submit", "info": {"termination_reason": termination}},
                "info": {"termination_reason": termination},
            },
        ]
    return steps


class TestComputeEpisodeMetrics:
    def test_basic_metrics(self):
        traj = _make_trajectory()
        metrics = compute_episode_metrics(traj, {"task_id": "task_0001"}, "mock", "react")
        assert metrics["task_id"] == "task_0001"
        assert metrics["total_steps"] == 2
        assert metrics["read_count"] == 1
        assert metrics["submit_count"] == 1
        assert metrics["termination_reason"] == "submitted"

    def test_invalid_action_counted(self):
        traj = [
            {
                "action": "not valid json",
                "observation": {"status": "error", "error": "Invalid JSON", "tool_name": "parse", "info": {}},
            },
            {
                "action": {"tool": "submit", "arguments": {}},
                "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
                "info": {"termination_reason": "submitted"},
            },
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["invalid_action_count"] == 1

    def test_excluded_from_main_results_mock(self):
        traj = _make_trajectory()
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "mock", "react")
        assert metrics["excluded_from_main_results"] is True

    def test_not_excluded_qwen_base(self):
        traj = _make_trajectory()
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["excluded_from_main_results"] is False

    def test_submit_before_test(self):
        traj = [
            {
                "action": {"tool": "submit", "arguments": {}},
                "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
                "info": {"termination_reason": "submitted"},
            },
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["submit_before_test"] is True

    def test_guardrail_violations_counted(self):
        traj = [
            {
                "action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}},
                "observation": {
                    "status": "success",
                    "content": "Edited",
                    "error": "",
                    "tool_name": "edit_file",
                    "info": {"warnings": [{"rule": "potential_reward_hacking", "message": "suspicious"}]},
                },
            },
            {
                "action": {"tool": "submit", "arguments": {}},
                "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
                "info": {"termination_reason": "submitted"},
            },
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["guardrail_violation_count"] == 1

    def test_tool_counts(self):
        traj = _make_trajectory([
            {
                "action": {"tool": "read_file", "arguments": {"path": "src/a.py"}},
                "observation": {"status": "success", "content": "", "error": "", "tool_name": "read_file", "info": {}},
            },
            {
                "action": {"tool": "search_code", "arguments": {"query": "def"}},
                "observation": {"status": "success", "content": "", "error": "", "tool_name": "search_code", "info": {}},
            },
            {
                "action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}},
                "observation": {"status": "success", "content": "", "error": "", "tool_name": "edit_file", "info": {}},
            },
            {
                "action": {"tool": "run_tests", "arguments": {}},
                "observation": {"status": "success", "content": "", "error": "", "tool_name": "run_tests", "info": {"passed": 3, "failed": 0}},
            },
            {
                "action": {"tool": "submit", "arguments": {}},
                "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
                "info": {"termination_reason": "submitted"},
            },
        ])
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["read_count"] == 1
        assert metrics["search_count"] == 1
        assert metrics["edit_count"] == 1
        assert metrics["test_count"] == 1
        assert metrics["submit_count"] == 1

    def test_empty_trajectory(self):
        metrics = compute_episode_metrics([], {"task_id": "t1"}, "mock", "react")
        assert metrics["total_steps"] == 0
        assert metrics["termination_reason"] == ""

    def test_repeated_test_call_rate_no_repeats(self):
        """Test calls separated by edits should have zero repeated rate."""
        traj = [
            {"action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "edit_file", "info": {}}},
            {"action": {"tool": "run_tests", "arguments": {}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "run_tests", "info": {"passed": 1}}},
            {"action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "a", "new_text": "b"}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "edit_file", "info": {}}},
            {"action": {"tool": "run_tests", "arguments": {}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "run_tests", "info": {"passed": 1}}},
            {"action": {"tool": "submit", "arguments": {}},
             "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
             "info": {"termination_reason": "submitted"}},
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["repeated_test_call_rate"] == 0.0

    def test_repeated_test_call_rate_with_repeat(self):
        """Test calls without intervening edits should count as repeated."""
        traj = [
            {"action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "edit_file", "info": {}}},
            {"action": {"tool": "run_tests", "arguments": {}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "run_tests", "info": {"passed": 1}}},
            {"action": {"tool": "run_tests", "arguments": {}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "run_tests", "info": {"passed": 1}}},
            {"action": {"tool": "submit", "arguments": {}},
             "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
             "info": {"termination_reason": "submitted"}},
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        # 2 test calls, 1 repeated (second has no edit between it and first)
        assert metrics["repeated_test_call_rate"] == 0.5

    def test_repeated_test_call_rate_single_test(self):
        """Single test call should have zero repeated rate."""
        traj = [
            {"action": {"tool": "run_tests", "arguments": {}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "run_tests", "info": {"passed": 1}}},
            {"action": {"tool": "submit", "arguments": {}},
             "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
             "info": {"termination_reason": "submitted"}},
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["repeated_test_call_rate"] == 0.0

    def test_patch_minimality(self):
        """Patch minimality should track modified files and lines."""
        traj = [
            {"action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "line1\nline2\n"}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "edit_file", "info": {}}},
            {"action": {"tool": "edit_file", "arguments": {"path": "src/b.py", "old_text": "y", "new_text": "line3"}},
             "observation": {"status": "success", "content": "", "error": "", "tool_name": "edit_file", "info": {}}},
            {"action": {"tool": "submit", "arguments": {}},
             "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
             "info": {"termination_reason": "submitted"}},
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["patch_modified_files"] == 2
        assert metrics["patch_modified_lines"] == 3  # "line1\nline2\n" has 3 lines + "line3" has 1 line
        assert metrics["edit_count"] == 2

    def test_patch_minimality_failed_edit(self):
        """Failed edits should not count toward patch minimality."""
        traj = [
            {"action": {"tool": "edit_file", "arguments": {"path": "src/a.py", "old_text": "x", "new_text": "y"}},
             "observation": {"status": "error", "content": "", "error": "Guardrail violation", "tool_name": "edit_file", "info": {}}},
            {"action": {"tool": "submit", "arguments": {}},
             "observation": {"status": "submitted", "content": "", "error": "", "tool_name": "submit", "info": {"termination_reason": "submitted"}},
             "info": {"termination_reason": "submitted"}},
        ]
        metrics = compute_episode_metrics(traj, {"task_id": "t1"}, "qwen_base", "react")
        assert metrics["patch_modified_files"] == 0
        assert metrics["patch_modified_lines"] == 0


class TestEvalMode:
    def test_eval_mode_values(self):
        assert EvalMode.TRAIN_REWARD == "train_reward"
        assert EvalMode.VALIDATION_SELECTION == "validation_selection"
        assert EvalMode.FINAL_TEST == "final_test"
        assert EvalMode.DATASET_VALIDATION == "dataset_validation"


class TestWriteMetricsCsv:
    def test_write_and_read(self, tmp_path: Path):
        metrics_list = [
            compute_episode_metrics(
                _make_trajectory(), {"task_id": "task_0001"}, "mock", "react"
            ),
            compute_episode_metrics(
                _make_trajectory(), {"task_id": "task_0002"}, "qwen_base", "react"
            ),
        ]
        csv_path = tmp_path / "metrics.csv"
        write_metrics_csv(metrics_list, csv_path)
        assert csv_path.exists()

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["task_id"] == "task_0001"
        assert rows[1]["task_id"] == "task_0002"

    def test_empty_list(self, tmp_path: Path):
        csv_path = tmp_path / "empty.csv"
        write_metrics_csv([], csv_path)
        assert not csv_path.exists()


class TestAggregateMetrics:
    def test_basic_aggregation(self):
        metrics_list = [
            {"public_pass": True, "private_pass": True, "hidden_pass": None, "total_steps": 3, "invalid_action_count": 0, "invalid_edit_count": 0, "regression_count": 0, "submit_before_test": False, "guardrail_violation_count": 0, "read_count": 1, "search_count": 0, "edit_count": 1, "test_count": 1, "submit_count": 1, "repeated_test_call_rate": 0.0, "patch_modified_lines": 2, "patch_modified_files": 1},
            {"public_pass": False, "private_pass": False, "hidden_pass": None, "total_steps": 6, "invalid_action_count": 2, "invalid_edit_count": 1, "regression_count": 1, "submit_before_test": True, "guardrail_violation_count": 1, "read_count": 0, "search_count": 0, "edit_count": 0, "test_count": 0, "submit_count": 1, "repeated_test_call_rate": 0.0, "patch_modified_lines": 0, "patch_modified_files": 0},
        ]
        agg = aggregate_metrics(metrics_list)
        assert agg["num_episodes"] == 2
        assert agg["public_pass_rate"] == 0.5
        assert agg["avg_steps"] == 4.5
        assert agg["avg_invalid_actions"] == 1.0
        assert agg["submit_before_test_rate"] == 0.5
        assert agg["avg_repeated_test_call_rate"] == 0.0
        assert agg["avg_patch_modified_lines"] == 1.0
        assert agg["avg_patch_modified_files"] == 0.5

    def test_gap_metrics_with_private(self):
        """Public-private gap should be computed when private_pass is present."""
        metrics_list = [
            {"public_pass": True, "private_pass": True, "hidden_pass": None, "total_steps": 1, "invalid_action_count": 0, "invalid_edit_count": 0, "regression_count": 0, "submit_before_test": False, "guardrail_violation_count": 0, "read_count": 0, "search_count": 0, "edit_count": 0, "test_count": 0, "submit_count": 0, "repeated_test_call_rate": 0.0, "patch_modified_lines": 0, "patch_modified_files": 0},
            {"public_pass": False, "private_pass": True, "hidden_pass": None, "total_steps": 1, "invalid_action_count": 0, "invalid_edit_count": 0, "regression_count": 0, "submit_before_test": False, "guardrail_violation_count": 0, "read_count": 0, "search_count": 0, "edit_count": 0, "test_count": 0, "submit_count": 0, "repeated_test_call_rate": 0.0, "patch_modified_lines": 0, "patch_modified_files": 0},
        ]
        agg = aggregate_metrics(metrics_list)
        assert agg["public_pass_rate"] == 0.5
        assert agg["private_pass_rate"] == 1.0
        assert agg["public_private_gap"] == pytest.approx(0.5)

    def test_gap_metrics_with_hidden(self):
        """Public-hidden gap should be computed when hidden_pass is present."""
        metrics_list = [
            {"public_pass": True, "private_pass": None, "hidden_pass": True, "total_steps": 1, "invalid_action_count": 0, "invalid_edit_count": 0, "regression_count": 0, "submit_before_test": False, "guardrail_violation_count": 0, "read_count": 0, "search_count": 0, "edit_count": 0, "test_count": 0, "submit_count": 0, "repeated_test_call_rate": 0.0, "patch_modified_lines": 0, "patch_modified_files": 0},
            {"public_pass": False, "private_pass": None, "hidden_pass": False, "total_steps": 1, "invalid_action_count": 0, "invalid_edit_count": 0, "regression_count": 0, "submit_before_test": False, "guardrail_violation_count": 0, "read_count": 0, "search_count": 0, "edit_count": 0, "test_count": 0, "submit_count": 0, "repeated_test_call_rate": 0.0, "patch_modified_lines": 0, "patch_modified_files": 0},
        ]
        agg = aggregate_metrics(metrics_list)
        assert "public_hidden_gap" in agg
        assert agg["public_hidden_gap"] == pytest.approx(0.0)
        assert "public_private_gap" not in agg

    def test_empty_list(self):
        assert aggregate_metrics([]) == {}
