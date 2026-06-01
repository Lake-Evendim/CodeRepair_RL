"""Diagnostic helper: compare buggy vs clean behavior for failing variants.

Run: python scripts/diagnose_variants.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from minirepair.data.bug_catalog import BugVariant, get_all_variants  # noqa: E402
from minirepair.data.bug_generator import _replace_function  # noqa: E402


def _run_tests_in_source(source: str, src_name: str, test_code: str, test_dir_name: str = "tests") -> tuple[int, int, str]:
    """Run tests against a source implementation. Returns (passed, failed, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Write source
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")
        (src_dir / src_name).write_text(source)

        # Write test
        test_dir = tmp_path / test_dir_name
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("")
        test_file = test_dir / f"test_{src_name}"

        # Build test content with import
        if src_name == "string_utils.py":
            imports = "from src.string_utils import (\n    capitalize_words,\n    count_substring,\n    pad_string,\n    reverse_words,\n    truncate_string,\n)\n"
        else:
            imports = "from src.validators import (\n    validate_date_format,\n    validate_email,\n    validate_password_strength,\n    validate_phone,\n    validate_url,\n)\n"

        test_content = f'"""Test."""\n\n{imports}\n\nclass TestVariant:\n{test_code}\n'
        test_file.write_text(test_content)

        # Run pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=line", "-q", "--rootdir", str(tmp_path)],
            capture_output=True, text=True, timeout=10, cwd=str(tmp_path),
        )
        output = result.stdout + result.stderr

        passed = failed = 0
        for line in output.split("\n"):
            if " passed" in line and "=" in line:
                for w in line.split():
                    if w.isdigit():
                        passed = int(w)
            if " failed" in line and "=" in line:
                for w in line.split():
                    if w.isdigit():
                        failed = int(w)

        return passed, failed, output


def diagnose_variant(variant: BugVariant) -> str:
    """Diagnose why a variant's buggy code doesn't fail tests."""
    # Get clean source
    if variant.repo_type == "string_utils":
        from minirepair.data.bug_generator import STRING_UTILS_CLEAN as clean_source
        src_name = "string_utils.py"
    else:
        from minirepair.data.bug_generator import VALIDATORS_CLEAN as clean_source
        src_name = "validators.py"

    # Build buggy source
    buggy_source = _replace_function(clean_source, variant.function_name, variant.buggy_code)

    # Run variant test against buggy code
    p_buggy, f_buggy, out_buggy = _run_tests_in_source(buggy_source, src_name, variant.test_code)

    # Run variant test against clean code
    p_clean, f_clean, out_clean = _run_tests_in_source(clean_source, src_name, variant.test_code)

    if f_buggy > 0:
        return f"OK (buggy fails: {f_buggy})"
    elif f_clean > 0:
        return f"TEST BUG (clean also fails: {f_clean})"
    else:
        return f"NO BEHAVIOR DIFF (buggy passes {p_buggy}, clean passes {p_clean})"


def main() -> int:
    # Find failing variant IDs from validation output
    result = subprocess.run(
        [sys.executable, "scripts/validate_tasks.py", "--tasks", "benchmarks/train"],
        capture_output=True, text=True, timeout=300, cwd=str(ROOT),
    )

    failing_vids: set[str] = set()
    for line in (result.stdout + result.stderr).split("\n"):
        if "FAIL" in line and "task_" in line:
            # Extract task_id
            import re
            m = re.search(r"task_(\d+)", line)
            if m:
                task_id = f"task_{m.group(1)}"
                meta_path = ROOT / "benchmarks" / "train" / task_id / "metadata.json"
                if meta_path.exists():
                    import json
                    meta = json.loads(meta_path.read_text())
                    failing_vids.add(meta.get("variant_id", ""))

    variants = {v.variant_id: v for v in get_all_variants()}

    print(f"Found {len(failing_vids)} failing variant IDs\n")
    print(f"{'variant_id':<20} {'function':<30} {'bug_type':<20} {'diagnosis'}")
    print("-" * 100)

    for vid in sorted(failing_vids):
        v = variants.get(vid)
        if v:
            diag = diagnose_variant(v)
            print(f"{vid:<20} {v.function_name:<30} {v.bug_type:<20} {diag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
