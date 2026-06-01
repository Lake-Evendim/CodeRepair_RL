"""Tests for sandbox module."""

from pathlib import Path

from minirepair.env.sandbox import Sandbox

SEED_TASK = Path(__file__).resolve().parent.parent / "benchmarks" / "tasks" / "seed" / "task_0001" / "repo"


class TestSandbox:
    def test_copy_and_isolation(self):
        """Sandbox copies repo and does not modify original."""
        original_src = SEED_TASK / "src" / "string_utils.py"
        original_content = original_src.read_text()

        with Sandbox(SEED_TASK) as sandbox:
            assert sandbox.working_path is not None
            assert sandbox.working_path.exists()
            assert (sandbox.working_path / "src" / "string_utils.py").exists()

            # Modify sandbox copy
            sandbox_file = sandbox.working_path / "src" / "string_utils.py"
            sandbox_file.write_text("# modified\n")

        # Original must be unchanged
        assert original_src.read_text() == original_content

    def test_cleanup(self):
        """Sandbox cleans up temp directory on exit."""
        sandbox = Sandbox(SEED_TASK)
        sandbox.__enter__()
        working_path = sandbox.working_path
        assert working_path is not None
        assert working_path.exists()
        sandbox.__exit__()
        assert not working_path.exists()

    def test_run_pytest_on_buggy_task(self):
        """Pytest on buggy task_0001 should have failures."""
        with Sandbox(SEED_TASK) as sandbox:
            result = sandbox.run_pytest(test_dirs=["tests"])
            assert result.returncode != 0
            assert result.failed > 0

    def test_run_pytest_nonexistent_dir(self):
        """Pytest on nonexistent test dir should fail gracefully."""
        with Sandbox(SEED_TASK) as sandbox:
            result = sandbox.run_pytest(test_dirs=["nonexistent"])
            assert result.returncode != 0

    def test_run_pytest_result_parsing(self):
        """Pytest result parses passed/failed counts."""
        with Sandbox(SEED_TASK) as sandbox:
            result = sandbox.run_pytest(test_dirs=["tests"])
            # buggy task_0001 should have some passed and some failed
            assert result.passed + result.failed > 0
