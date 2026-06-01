"""Sandbox: isolated execution environment for task repos."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PytestResult:
    stdout: str
    stderr: str
    returncode: int
    passed: int = 0
    failed: int = 0

    def __post_init__(self) -> None:
        if not self.passed and not self.failed:
            self._parse_counts()

    def _parse_counts(self) -> None:
        for line in (self.stdout + self.stderr).split("\n"):
            line = line.strip()
            if " passed" in line and "=" in line:
                for word in line.split():
                    if word.isdigit():
                        self.passed = int(word)
            if " failed" in line and "=" in line:
                for word in line.split():
                    if word.isdigit():
                        self.failed = int(word)


class Sandbox:
    """Manages an isolated copy of a task repo for safe execution."""

    def __init__(self, task_repo_path: Path) -> None:
        self.original_path = task_repo_path.resolve()
        self._tmp_dir: tempfile.TemporaryDirectory | None = None
        self.working_path: Path | None = None

    def __enter__(self) -> Sandbox:
        self._tmp_dir = tempfile.TemporaryDirectory(prefix="minirepair_")
        self.working_path = Path(self._tmp_dir.name) / "repo"
        shutil.copytree(self.original_path, self.working_path)
        return self

    def __exit__(self, *args: object) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        if self._tmp_dir is not None:
            self._tmp_dir.cleanup()
            self._tmp_dir = None
            self.working_path = None

    def run_pytest(
        self,
        test_dirs: list[str] | None = None,
        timeout: float = 30.0,
    ) -> PytestResult:
        """Run pytest in the sandbox. Returns structured result."""
        if self.working_path is None:
            return PytestResult(stdout="", stderr="Sandbox not initialized", returncode=1)

        if test_dirs is None:
            test_dirs = ["tests"]

        abs_test_dirs = [str(self.working_path / d) for d in test_dirs]
        cmd = [
            sys.executable, "-m", "pytest",
            *abs_test_dirs,
            "-v", "--tb=short", "-q",
            "--rootdir", str(self.working_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.working_path),
            )
            return PytestResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return PytestResult(
                stdout="",
                stderr=f"pytest timed out after {timeout}s",
                returncode=-1,
            )
