"""Generate task directories from BugVariant definitions."""

from __future__ import annotations

import json
from pathlib import Path

from minirepair.data.bug_catalog import BugVariant

# Clean source code templates (only the functions that are NOT being mutated)
STRING_UTILS_CLEAN = '''\
"""String utility functions."""


def truncate_string(s: str, max_len: int) -> str:
    """Truncate string to max_len characters. Add '...' if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def count_substring(s: str, sub: str) -> int:
    """Count non-overlapping occurrences of sub in s (case-sensitive)."""
    if not sub:
        return 0
    count = 0
    start = 0
    while True:
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count


def reverse_words(s: str) -> str:
    """Reverse the order of words in a string. Preserve internal spacing style by returning single spaces."""
    return " ".join(s.split()[::-1])


def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string to at least min_width characters using fill_char."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding


def capitalize_words(s: str) -> str:
    """Capitalize the first letter of each word, lowercase the rest."""
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))
'''

VALIDATORS_CLEAN = '''\
"""Validation utility functions."""

import re


def validate_email(email: str) -> bool:
    """Validate email: must have exactly one @, non-empty local/domain, domain has dot."""
    if not email or ".." in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True


def validate_phone(phone: str) -> bool:
    """Validate phone: 10-15 digits, optional leading +, optional dashes/spaces between groups."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_password_strength(password: str) -> bool:
    """Validate password: >=8 chars, has upper, lower, digit, special char."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special


def validate_url(url: str) -> bool:
    """Validate URL: must start with http:// or https://, then non-empty host."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest


def validate_date_format(date_str: str) -> bool:
    """Validate date string is YYYY-MM-DD and represents a real date."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
'''

# Clean test templates (base tests that don't catch specific bugs)
STRING_UTILS_TESTS = '''\
"""Public tests for string_utils."""

from src.string_utils import (
    capitalize_words,
    count_substring,
    pad_string,
    reverse_words,
    truncate_string,
)


class TestTruncateString:
    def test_no_truncation_needed(self):
        assert truncate_string("hello", 10) == "hello"

    def test_exact_length(self):
        assert truncate_string("hello", 5) == "hello"


class TestCountSubstring:
    def test_basic_count(self):
        assert count_substring("hello world", "o") == 2

    def test_no_match(self):
        assert count_substring("hello", "xyz") == 0

    def test_empty_substring(self):
        assert count_substring("hello", "") == 0


class TestReverseWords:
    def test_basic_reverse(self):
        assert reverse_words("hello world") == "world hello"

    def test_single_word(self):
        assert reverse_words("hello") == "hello"


class TestPadString:
    def test_no_padding_needed(self):
        assert pad_string("hello", 5) == "hello"

    def test_padding_with_default_space(self):
        assert pad_string("hi", 5) == "hi   "

    def test_longer_than_min_width(self):
        assert pad_string("hello world", 5) == "hello world"


class TestCapitalizeWords:
    def test_basic_capitalize(self):
        assert capitalize_words("hello world") == "Hello World"

    def test_empty_string(self):
        assert capitalize_words("") == ""
'''

VALIDATORS_TESTS = '''\
"""Public tests for validators."""

from src.validators import (
    validate_date_format,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_url,
)


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_missing_at(self):
        assert validate_email("userexample.com") is False


class TestValidatePhone:
    def test_valid_10_digits(self):
        assert validate_phone("1234567890") is True

    def test_too_short(self):
        assert validate_phone("12345") is False


class TestValidatePasswordStrength:
    def test_strong_password(self):
        assert validate_password_strength("Abc12345!") is True

    def test_too_short(self):
        assert validate_password_strength("Ab1!") is False


class TestValidateUrl:
    def test_valid_https(self):
        assert validate_url("https://example.com/path") is True

    def test_no_protocol(self):
        assert validate_url("example.com/path") is False


class TestValidateDateFormat:
    def test_valid_date(self):
        assert validate_date_format("2024-01-15") is True

    def test_invalid_format(self):
        assert validate_date_format("01/15/2024") is False
'''

# Private tests (shared across all tasks)
STRING_UTILS_PRIVATE = '''\
"""Private tests for string_utils."""

from src.string_utils import (
    capitalize_words,
    count_substring,
    pad_string,
    reverse_words,
    truncate_string,
)


class TestTruncatePrivate:
    def test_unicode(self):
        result = truncate_string("caf\\u00e9", 4)
        assert result == "caf\\u00e9"


class TestCountPrivate:
    def test_repeated(self):
        assert count_substring("aaaa", "aa") == 2


class TestReversePrivate:
    def test_multi_space(self):
        assert reverse_words("a  b  c") == "c b a"


class TestPadPrivate:
    def test_zero_width(self):
        assert pad_string("hello", 0) == "hello"

    def test_empty_string(self):
        assert pad_string("", 3) == "   "


class TestCapitalizePrivate:
    def test_mixed_case(self):
        assert capitalize_words("hELLo WoRLD") == "Hello World"

    def test_all_upper(self):
        assert capitalize_words("HELLO") == "Hello"
'''

VALIDATORS_PRIVATE = '''\
"""Private tests for validators."""

from src.validators import (
    validate_date_format,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_url,
)


class TestEmailPrivate:
    def test_empty(self):
        assert validate_email("") is False

    def test_no_domain(self):
        assert validate_email("user@") is False

    def test_subdomain(self):
        assert validate_email("user@sub.example.com") is True


class TestPhonePrivate:
    def test_15_digits(self):
        assert validate_phone("123456789012345") is True

    def test_16_digits(self):
        assert validate_phone("1234567890123456") is False

    def test_spaces(self):
        assert validate_phone("123 456 7890") is True


class TestPasswordPrivate:
    def test_exactly_8(self):
        assert validate_password_strength("Abc1234!") is True

    def test_7_chars(self):
        assert validate_password_strength("Abc123!") is False

    def test_all_digits(self):
        assert validate_password_strength("12345678") is False


class TestUrlPrivate:
    def test_just_host(self):
        assert validate_url("https://example.com") is False

    def test_empty(self):
        assert validate_url("") is False

    def test_port(self):
        assert validate_url("http://localhost:8080/api") is True


class TestDatePrivate:
    def test_leap_year(self):
        assert validate_date_format("2024-02-29") is True

    def test_non_leap(self):
        assert validate_date_format("2023-02-29") is False

    def test_century(self):
        assert validate_date_format("1900-02-29") is False

    def test_400_year(self):
        assert validate_date_format("2000-02-29") is True
'''

# Quality holdout tests (for train/validation)
STRING_UTILS_QUALITY = '''\
"""Quality holdout tests for string_utils."""

from src.string_utils import count_substring, pad_string, truncate_string


class TestTruncateQuality:
    def test_short_unchanged(self):
        assert truncate_string("hi", 10) == "hi"


class TestCountQuality:
    def test_case_sensitive(self):
        assert count_substring("AaAa", "a") == 2


class TestPadQuality:
    def test_large_padding(self):
        result = pad_string("a", 10, ".")
        assert len(result) == 10
'''

VALIDATORS_QUALITY = '''\
"""Quality holdout tests for validators."""

from src.validators import validate_email, validate_phone


class TestEmailQuality:
    def test_numeric_local(self):
        assert validate_email("123@example.com") is True


class TestPhoneQuality:
    def test_leading_zeros(self):
        assert validate_phone("0012345678") is True
'''

# Hidden tests (for test split only)
STRING_UTILS_HIDDEN = '''\
"""Hidden tests for string_utils — test split only."""

from src.string_utils import (
    capitalize_words,
    count_substring,
    pad_string,
    reverse_words,
    truncate_string,
)


class TestTruncateHidden:
    def test_trunc_preserves_prefix(self):
        result = truncate_string("abcdefgh", 5)
        assert result.startswith("ab")


class TestCountHidden:
    def test_long_sub_no_match(self):
        assert count_substring("short", "longer_than_input") == 0


class TestReverseHidden:
    def test_tabs(self):
        assert reverse_words("hello\\tworld") == "world hello"


class TestPadHidden:
    def test_single_char_fill(self):
        assert pad_string("x", 1, "0") == "x"


class TestCapitalizeHidden:
    def test_single_char_words(self):
        assert capitalize_words("a b c") == "A B C"
'''

VALIDATORS_HIDDEN = '''\
"""Hidden tests for validators — test split only."""

from src.validators import (
    validate_date_format,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_url,
)


class TestEmailHidden:
    def test_dot_in_local(self):
        assert validate_email("first.last@example.com") is True


class TestPhoneHidden:
    def test_all_same(self):
        assert validate_phone("1111111111") is True


class TestPasswordHidden:
    def test_mixed_with_spaces(self):
        assert validate_password_strength("Abc 1234!") is True


class TestUrlHidden:
    def test_path_with_port(self):
        assert validate_url("http://localhost:8080/api") is True


class TestDateHidden:
    def test_leap_400(self):
        assert validate_date_format("2000-02-29") is True
'''


def _replace_function(source: str, function_name: str, buggy_code: str) -> str:
    """Replace a single function in source with buggy_code."""
    lines = source.split("\n")
    result = []
    in_target = False
    pattern = f"def {function_name}("

    for line in lines:
        if pattern in line and not in_target:
            in_target = True
            result.append(buggy_code.rstrip())
            continue
        if in_target:
            if line == "" or (len(line) > 0 and (line[0] == " " or line[0] == "\t")):
                continue
            else:
                in_target = False
        result.append(line)

    out = "\n".join(result)
    if not out.endswith("\n"):
        out += "\n"
    return out


def _build_public_test(repo_type: str, variant: BugVariant) -> str:
    """Build public test file: base tests + variant-specific test."""
    if repo_type == "string_utils":
        base = STRING_UTILS_TESTS
    else:
        base = VALIDATORS_TESTS

    # Find the right test class to add the variant test to
    test_func = variant.test_code
    func_name = variant.function_name

    # Map function name to test class
    class_map = {
        "truncate_string": "TestTruncateString",
        "count_substring": "TestCountSubstring",
        "reverse_words": "TestReverseWords",
        "pad_string": "TestPadString",
        "capitalize_words": "TestCapitalizeWords",
        "validate_email": "TestValidateEmail",
        "validate_phone": "TestValidatePhone",
        "validate_password_strength": "TestValidatePasswordStrength",
        "validate_url": "TestValidateUrl",
        "validate_date_format": "TestValidateDateFormat",
    }

    target_class = class_map.get(func_name)
    if target_class and f"class {target_class}:" in base:
        # Insert the test method after the last method in the target class
        lines = base.split("\n")
        result = []
        in_class = False
        last_class_line = 0
        for i, line in enumerate(lines):
            if line.startswith(f"class {target_class}:"):
                in_class = True
            elif in_class and line.startswith("class "):
                # We've left the target class
                in_class = False
                # Insert before this line
                break
            if in_class and line.strip().startswith("def "):
                last_class_line = i
        # Find the end of the last method in the target class
        insert_at = last_class_line + 1
        while insert_at < len(lines) and (lines[insert_at].startswith("        ") or lines[insert_at].strip() == ""):
            insert_at += 1
        # Insert the variant test
        result = lines[:insert_at]
        result.append("")
        result.append(test_func)
        result.extend(lines[insert_at:])
        return "\n".join(result)

    # Fallback: append to end
    return base + "\n\n" + test_func


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _strip_unused_re_import(source: str) -> str:
    """Remove 'import re' if 're' is not used elsewhere in the file."""
    if "import re" not in source:
        return source
    # Check if 're.' or 're(' or 're,' or 're\n' appears outside the import line
    lines = source.split("\n")
    import_line_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "import re":
            import_line_idx = i
            break
    if import_line_idx is None:
        return source
    # Check if re is used anywhere else
    other_lines = lines[:import_line_idx] + lines[import_line_idx + 1:]
    other_text = "\n".join(other_lines)
    if "re." in other_text or "re(" in other_text or "re," in other_text:
        return source
    # Remove the import line
    lines.pop(import_line_idx)
    return "\n".join(lines)


def generate_task(
    variant: BugVariant,
    task_id: str,
    split: str,
    output_dir: Path,
) -> None:
    """Generate a complete task directory from a BugVariant."""
    task_dir = output_dir / task_id
    repo_dir = task_dir / "repo"

    # Select clean source and test templates
    if variant.repo_type == "string_utils":
        clean_source = STRING_UTILS_CLEAN
        src_name = "string_utils.py"
        private_tests = STRING_UTILS_PRIVATE
        quality_tests = STRING_UTILS_QUALITY
        hidden_tests = STRING_UTILS_HIDDEN
    else:
        clean_source = VALIDATORS_CLEAN
        src_name = "validators.py"
        private_tests = VALIDATORS_PRIVATE
        quality_tests = VALIDATORS_QUALITY
        hidden_tests = VALIDATORS_HIDDEN

    # Build buggy source
    buggy_source = _replace_function(clean_source, variant.function_name, variant.buggy_code)
    buggy_source = _strip_unused_re_import(buggy_source)

    # Build public tests with variant-specific test
    public_tests = _build_public_test(variant.repo_type, variant)

    # Write metadata
    metadata = {
        "task_id": task_id,
        "repo_type": variant.repo_type,
        "bug_type": variant.bug_type,
        "bug_description": variant.description,
        "gold_patch": {
            "file_path": f"src/{src_name}",
            "old_text": variant.fix_old,
            "new_text": variant.fix_new,
        },
        "split": split,
        "variant_id": variant.variant_id,
    }
    _write_file(task_dir / "metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))

    # Write source
    _write_file(repo_dir / "src" / "__init__.py", "")
    _write_file(repo_dir / "src" / src_name, buggy_source)

    # Write public tests
    _write_file(repo_dir / "tests" / "__init__.py", "")
    test_name = f"test_{src_name}"
    _write_file(repo_dir / "tests" / test_name, public_tests)

    # Write private tests
    _write_file(repo_dir / "tests_private" / "__init__.py", "")
    private_name = f"test_{src_name.replace('.py', '')}_private.py"
    _write_file(repo_dir / "tests_private" / private_name, private_tests)

    # Write split-specific tests
    if split in ("train", "validation"):
        _write_file(repo_dir / "tests_quality_holdout" / "__init__.py", "")
        quality_name = f"test_{src_name.replace('.py', '')}_quality.py"
        _write_file(repo_dir / "tests_quality_holdout" / quality_name, quality_tests)
    elif split == "test":
        _write_file(repo_dir / "tests_hidden" / "__init__.py", "")
        hidden_name = f"test_{src_name.replace('.py', '')}_hidden.py"
        _write_file(repo_dir / "tests_hidden" / hidden_name, hidden_tests)
