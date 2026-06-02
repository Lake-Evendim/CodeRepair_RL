"""Tests for report formatting helpers."""

from minirepair.evaluation.reports import (
    format_case_study,
    format_failure_analysis,
    format_main_results_table,
    format_reward_ablation_table,
)


class TestFormatMainResultsTable:
    def test_basic_table(self):
        results = [
            {
                "method_name": "react",
                "policy_type": "qwen_base",
                "eval_mode": "validation_selection",
                "split": "validation",
                "num_tasks": 20,
                "aggregate": {
                    "public_pass_rate": 0.1,
                    "private_pass_rate": 0.4,
                    "public_private_gap": 0.3,
                    "avg_invalid_actions": 2.5,
                    "avg_invalid_edits": 1.0,
                    "avg_steps": 4.0,
                    "avg_repeated_test_call_rate": 0.2,
                    "avg_patch_modified_lines": 3.0,
                },
            },
            {
                "method_name": "sft",
                "policy_type": "sft_qwen_lora",
                "eval_mode": "final_test",
                "split": "test",
                "num_tasks": 30,
                "aggregate": {
                    "public_pass_rate": 0.5,
                    "hidden_pass_rate": 0.3,
                    "public_hidden_gap": -0.2,
                    "avg_invalid_actions": 0.5,
                    "avg_invalid_edits": 0.1,
                    "avg_steps": 3.0,
                    "avg_repeated_test_call_rate": 0.1,
                    "avg_patch_modified_lines": 2.0,
                },
            },
        ]
        table = format_main_results_table(results)
        assert "# Main Results" in table
        assert "react" in table
        assert "sft" in table
        assert "private" in table
        assert "hidden" in table

    def test_empty_results(self):
        table = format_main_results_table([])
        assert "# Main Results" in table


class TestFormatRewardAblationTable:
    def test_basic_table(self):
        results = [
            {
                "method_name": "rl_sparse",
                "aggregate": {
                    "private_pass_rate": 0.55,
                    "hidden_pass_rate": 0.3,
                    "avg_invalid_actions": 1.0,
                    "avg_invalid_edits": 0.5,
                    "avg_steps": 3.5,
                },
            },
            {
                "method_name": "rl_dense",
                "aggregate": {
                    "private_pass_rate": 0.6,
                    "hidden_pass_rate": 0.35,
                    "avg_invalid_actions": 0.8,
                    "avg_invalid_edits": 0.3,
                    "avg_steps": 3.2,
                },
            },
        ]
        table = format_reward_ablation_table(results)
        assert "# Reward Ablation" in table
        assert "Sparse" in table
        assert "Dense" in table


class TestFormatCaseStudy:
    def test_basic_case_study(self):
        cs = format_case_study(
            task_id="task_0001",
            method="react",
            metrics={
                "total_steps": 4,
                "edit_count": 1,
                "test_count": 1,
                "invalid_action_count": 0,
                "invalid_edit_count": 0,
                "termination_reason": "max_steps",
            },
            failure_types=["localization_error", "semantic_patch_error"],
        )
        assert "task_0001" in cs
        assert "react" in cs
        assert "localization_error" in cs
        assert "semantic_patch_error" in cs

    def test_with_trajectory(self):
        traj = [
            {"action": {"tool": "read_file", "arguments": {"path": "src/a.py"}},
             "observation": {"status": "success"}},
            {"action": {"tool": "edit_file", "arguments": {"path": "src/a.py"}},
             "observation": {"status": "success"}},
        ]
        cs = format_case_study(
            task_id="t1", method="sft",
            metrics={"total_steps": 2, "edit_count": 1, "test_count": 0,
                     "invalid_action_count": 0, "invalid_edit_count": 0,
                     "termination_reason": "submitted"},
            failure_types=["premature_submit"],
            trajectory=traj,
        )
        assert "read_file" in cs
        assert "edit_file" in cs


class TestFormatFailureAnalysis:
    def test_basic_report(self):
        summary = {
            "total_failed": 5,
            "failure_counts": {
                "invalid_action": 2,
                "localization_error": 3,
                "semantic_patch_error": 3,
                "invalid_edit": 0,
                "reward_hacking_attempt": 0,
                "premature_submit": 0,
                "regression_error": 0,
                "tool_misuse": 0,
                "context_misunderstanding": 0,
            },
            "primary_distribution": {
                "invalid_action": 2,
                "localization_error": 3,
                "semantic_patch_error": 0,
                "invalid_edit": 0,
                "reward_hacking_attempt": 0,
                "premature_submit": 0,
                "regression_error": 0,
                "tool_misuse": 0,
                "context_misunderstanding": 0,
            },
            "category_task_ids": {
                "invalid_action": ["t1", "t2"],
                "localization_error": ["t3", "t4", "t5"],
            },
        }
        report = format_failure_analysis(summary, case_studies=[])
        assert "# Failure Analysis" in report
        assert "5" in report
        assert "localization_error" in report

    def test_with_case_studies(self):
        summary = {
            "total_failed": 1,
            "failure_counts": {"invalid_action": 1, "localization_error": 0, "semantic_patch_error": 0, "invalid_edit": 0, "reward_hacking_attempt": 0, "premature_submit": 0, "regression_error": 0, "tool_misuse": 0, "context_misunderstanding": 0},
            "primary_distribution": {"invalid_action": 1, "localization_error": 0, "semantic_patch_error": 0, "invalid_edit": 0, "reward_hacking_attempt": 0, "premature_submit": 0, "regression_error": 0, "tool_misuse": 0, "context_misunderstanding": 0},
            "category_task_ids": {"invalid_action": ["t1"]},
        }
        cs = format_case_study("t1", "react", {"total_steps": 1, "edit_count": 0, "test_count": 0, "invalid_action_count": 1, "invalid_edit_count": 0, "termination_reason": "error"}, ["invalid_action"])
        report = format_failure_analysis(summary, case_studies=[cs])
        assert "Case Studies" in report
        assert "t1" in report
