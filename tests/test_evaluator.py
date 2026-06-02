"""Tests for evaluator: evaluate_final_state and Evaluator."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from minirepair.agents.react_agent import MockPolicy
from minirepair.evaluation.evaluator import Evaluator, evaluate_final_state
from minirepair.evaluation.metrics import EvalMode


@pytest.fixture
def seed_task_path():
    """Return path to first seed task."""
    path = Path("benchmarks/tasks/seed/task_0001")
    if not path.exists():
        pytest.skip("Seed tasks not generated")
    return path


@pytest.fixture
def validation_task_path():
    """Return path to first validation task."""
    path = Path("benchmarks/validation/task_0081")
    if not path.exists():
        # Try to find any validation task
        val_dir = Path("benchmarks/validation")
        if val_dir.exists():
            tasks = sorted(d for d in val_dir.iterdir() if d.is_dir() and (d / "metadata.json").exists())
            if tasks:
                return tasks[0]
        pytest.skip("Validation tasks not generated")
    return path


class TestEvaluateFinalState:
    def test_validation_selection_with_validation_split(self, validation_task_path):
        """VALIDATION_SELECTION on validation split should run tests_private/."""
        metadata_path = validation_task_path / "metadata.json"
        if not metadata_path.exists():
            pytest.skip("No metadata")

        from minirepair.env.sandbox import Sandbox

        repo_path = validation_task_path / "repo"
        if not repo_path.exists():
            pytest.skip("No repo dir")

        sandbox = Sandbox(repo_path)
        sandbox.__enter__()
        try:
            result = evaluate_final_state(sandbox, "validation", EvalMode.VALIDATION_SELECTION)
            assert "private_pass" in result
            assert result["hidden_pass"] is None
        finally:
            sandbox.__exit__(None, None, None)

    def test_final_test_with_test_split(self):
        """FINAL_TEST on test split should run tests_hidden/."""
        test_dir = Path("benchmarks/test")
        if not test_dir.exists():
            pytest.skip("Test tasks not generated")
        tasks = sorted(d for d in test_dir.iterdir() if d.is_dir() and (d / "metadata.json").exists())
        if not tasks:
            pytest.skip("No test tasks")

        from minirepair.env.sandbox import Sandbox

        task_path = tasks[0]
        repo_path = task_path / "repo"
        sandbox = Sandbox(repo_path)
        sandbox.__enter__()
        try:
            result = evaluate_final_state(sandbox, "test", EvalMode.FINAL_TEST)
            assert "hidden_pass" in result
            assert result["private_pass"] is None
        finally:
            sandbox.__exit__(None, None, None)

    def test_validation_selection_rejects_test_split(self):
        """VALIDATION_SELECTION must not be used with test split."""
        from minirepair.env.sandbox import Sandbox

        sandbox = MagicMock(spec=Sandbox)
        sandbox.working_path = Path("/fake")
        with pytest.raises(ValueError, match="VALIDATION_SELECTION"):
            evaluate_final_state(sandbox, "test", EvalMode.VALIDATION_SELECTION)

    def test_final_test_rejects_validation_split(self):
        """FINAL_TEST must not be used with validation split."""
        from minirepair.env.sandbox import Sandbox

        sandbox = MagicMock(spec=Sandbox)
        sandbox.working_path = Path("/fake")
        with pytest.raises(ValueError, match="FINAL_TEST"):
            evaluate_final_state(sandbox, "validation", EvalMode.FINAL_TEST)

    def test_dataset_validation_rejected(self):
        """DATASET_VALIDATION should not be used in evaluator."""
        from minirepair.env.sandbox import Sandbox

        sandbox = MagicMock(spec=Sandbox)
        sandbox.working_path = Path("/fake")
        with pytest.raises(ValueError, match="DATASET_VALIDATION"):
            evaluate_final_state(sandbox, "test", EvalMode.DATASET_VALIDATION)

    def test_train_reward_with_train_split(self, seed_task_path):
        """TRAIN_REWARD on train-like split should run tests_private/."""
        from minirepair.env.sandbox import Sandbox

        repo_path = seed_task_path / "repo"
        if not repo_path.exists():
            pytest.skip("No repo dir")

        sandbox = Sandbox(repo_path)
        sandbox.__enter__()
        try:
            result = evaluate_final_state(sandbox, "train", EvalMode.TRAIN_REWARD)
            assert "private_pass" in result
            assert result["hidden_pass"] is None
        finally:
            sandbox.__exit__(None, None, None)


class TestEvaluator:
    def test_evaluate_single_task_with_mock(self, seed_task_path):
        """MockPolicy should complete a single task evaluation."""
        metadata_path = seed_task_path / "metadata.json"
        if not metadata_path.exists():
            pytest.skip("No metadata")

        metadata = json.loads(metadata_path.read_text())
        policy = MockPolicy(metadata)
        evaluator = Evaluator(
            policy=policy,
            eval_mode=EvalMode.TRAIN_REWARD,
            method_name="react",
            trajectory_dir=None,
        )
        metrics = evaluator.evaluate_task(seed_task_path)
        assert "task_id" in metrics
        assert "public_pass" in metrics
        assert metrics["policy_type"] == "mock"
        assert metrics["excluded_from_main_results"] is True

    def test_evaluate_split_mock(self, tmp_path):
        """MockPolicy should evaluate a small split."""
        seed_dir = Path("benchmarks/tasks/seed")
        if not seed_dir.exists():
            pytest.skip("Seed tasks not generated")
        tasks = sorted(d for d in seed_dir.iterdir() if d.is_dir() and (d / "metadata.json").exists())
        if len(tasks) < 2:
            pytest.skip("Not enough seed tasks")

        # Use metadata from first task for MockPolicy
        metadata = json.loads((tasks[0] / "metadata.json").read_text())
        policy = MockPolicy(metadata)
        evaluator = Evaluator(
            policy=policy,
            eval_mode=EvalMode.TRAIN_REWARD,
            method_name="react",
            trajectory_dir=tmp_path / "output",
        )
        result = evaluator.evaluate_split(seed_dir, max_tasks=2)
        assert result["num_tasks"] == 2
        assert len(result["metrics_list"]) == 2
        assert "aggregate" in result
        assert (tmp_path / "output" / "metrics.csv").exists()
        assert (tmp_path / "output" / "summary.json").exists()
