"""Validate seed benchmark tasks.

Checks:
1. metadata.json is valid against TaskMetadata schema
2. No tests_hidden/ directory in seed tasks
3. Buggy version: public tests have at least 1 failure
4. After applying gold patch: all public + private tests pass
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from minirepair.data.task_schema import TaskMetadata  # noqa: E402


def run_pytest(repo_dir: Path, test_dirs: list[str]) -> tuple[int, int]:
    """Run pytest in repo_dir on the given test directories. Returns (passed, failed)."""
    cmd = [
        sys.executable, "-m", "pytest",
        *[str(repo_dir / d) for d in test_dirs],
        "-v", "--tb=line", "-q",
        "--rootdir", str(repo_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo_dir))
    output = result.stdout + result.stderr

    passed = 0
    failed = 0
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("FAILED"):
            failed += 1
        elif " passed" in line and "failed" in line:
            # Summary line like "2 failed, 3 passed"
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if "failed" in part:
                    try:
                        failed = int(part.split()[0])
                    except ValueError:
                        pass
                elif "passed" in part:
                    try:
                        passed = int(part.split()[0])
                    except ValueError:
                        pass
        elif "passed" in line and "=" in line:
            # Summary line like "====== 5 passed ======="
            for word in line.split():
                if word.isdigit():
                    passed = int(word)

    return passed, failed


def apply_gold_patch(repo_dir: Path, patch: dict) -> None:
    """Apply a gold patch (file_path, old_text, new_text) to the repo."""
    file_path = repo_dir / patch["file_path"]
    content = file_path.read_text(encoding="utf-8")
    if patch["old_text"] not in content:
        raise ValueError(f"old_text not found in {file_path}")
    new_content = content.replace(patch["old_text"], patch["new_text"], 1)
    file_path.write_text(new_content, encoding="utf-8")


def validate_task(task_dir: Path) -> tuple[bool, str]:
    """Validate a single task. Returns (success, message)."""
    task_id = task_dir.name

    # 1. Check metadata.json exists and is valid
    metadata_path = task_dir / "metadata.json"
    if not metadata_path.exists():
        return False, f"{task_id}: metadata.json not found"

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        TaskMetadata(**metadata)
    except Exception as e:
        return False, f"{task_id}: invalid metadata: {e}"

    # 2. Check no tests_hidden/ in seed tasks
    repo_dir = task_dir / "repo"
    if (repo_dir / "tests_hidden").exists():
        return False, f"{task_id}: tests_hidden/ must not exist in seed tasks"

    # 3. Check repo structure
    if not (repo_dir / "src").exists():
        return False, f"{task_id}: repo/src/ not found"
    if not (repo_dir / "tests").exists():
        return False, f"{task_id}: repo/tests/ not found"
    if not (repo_dir / "tests_private").exists():
        return False, f"{task_id}: repo/tests_private/ not found"

    # 4. Copy to temp dir and test buggy version
    with tempfile.TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp) / "repo"
        shutil.copytree(repo_dir, tmp_repo)

        # Run public tests on buggy version - should have failures
        _, failed_buggy = run_pytest(tmp_repo, ["tests"])
        if failed_buggy == 0:
            return False, f"{task_id}: buggy version has no public test failures"

        # 5. Apply gold patch
        try:
            apply_gold_patch(tmp_repo, metadata["gold_patch"])
        except Exception as e:
            return False, f"{task_id}: failed to apply gold patch: {e}"

        # 6. Run public + private tests on patched version - should all pass
        _, failed_patched = run_pytest(tmp_repo, ["tests", "tests_private"])
        if failed_patched > 0:
            # Re-run to get more detail
            passed_p, failed_p = run_pytest(tmp_repo, ["tests", "tests_private"])
            return False, f"{task_id}: patched version has {failed_p} failures (passed: {passed_p})"

    return True, f"{task_id}: OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate benchmark tasks")
    parser.add_argument(
        "--tasks", nargs="+", required=True,
        help="Directories containing tasks to validate",
    )
    args = parser.parse_args()

    task_dirs: list[Path] = []
    for tasks_path in args.tasks:
        p = Path(tasks_path)
        if not p.exists():
            print(f"ERROR: {p} does not exist")
            return 1
        # If it's a task directory (has metadata.json), add it directly
        if (p / "metadata.json").exists():
            task_dirs.append(p)
        else:
            # It's a parent directory containing task subdirectories
            for child in sorted(p.iterdir()):
                if child.is_dir() and (child / "metadata.json").exists():
                    task_dirs.append(child)

    if not task_dirs:
        print("ERROR: No tasks found")
        return 1

    print(f"Validating {len(task_dirs)} tasks...\n")

    passed = 0
    failed = 0
    errors: list[str] = []

    for task_dir in task_dirs:
        ok, msg = validate_task(task_dir)
        if ok:
            passed += 1
            print(f"  PASS  {msg}")
        else:
            failed += 1
            errors.append(msg)
            print(f"  FAIL  {msg}")

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {len(task_dirs)} total")

    if errors:
        print("\nFailed tasks:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\nAll tasks passed validation!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
