"""Generate 20 seed benchmark tasks for MiniRepair-RL.

Creates benchmarks/tasks/seed/task_0001 through task_0020.
Each task has: metadata.json, repo/src/, repo/tests/, repo/tests_private/, repo/tests_quality_holdout/.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "benchmarks" / "tasks" / "seed"

# ---------------------------------------------------------------------------
# Clean source code (shared by all tasks of the same repo type)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Buggy function variants (only the function that differs from clean)
# ---------------------------------------------------------------------------

BUGGY_TRUNCATE_OFF_BY_ONE = '''\
def truncate_string(s: str, max_len: int) -> str:
    """Truncate string to max_len characters. Add '...' if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len] + "..."
'''

BUGGY_COUNT_OVERLAPPING = '''\
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
        start = idx + 1
    return count
'''

BUGGY_REVERSE_SPLIT_ONLY_SPACE = '''\
def reverse_words(s: str) -> str:
    """Reverse the order of words in a string."""
    return " ".join(s.split(" ")[::-1])
'''

BUGGY_PAD_WRONG_MATH = '''\
def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string to at least min_width characters using fill_char."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (len(s) - min_width)
    return s + padding
'''

BUGGY_CAPITALIZE_NO_LOWER = '''\
def capitalize_words(s: str) -> str:
    """Capitalize the first letter of each word, uppercase the rest."""
    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))
'''

BUGGY_EMAIL_NO_DOUBLE_DOT = '''\
def validate_email(email: str) -> bool:
    """Validate email: must have exactly one @, non-empty local/domain, domain has dot."""
    if not email:
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
'''

BUGGY_PHONE_NOT_ALL_DIGIT = '''\
def validate_phone(phone: str) -> bool:
    """Validate phone: 10-15 digits, optional leading +, optional dashes/spaces between groups."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return len(cleaned) >= 10
'''

BUGGY_PASSWORD_NO_UPPER = '''\
def validate_password_strength(password: str) -> bool:
    """Validate password: >=8 chars, has lower, digit, special char."""
    if len(password) < 8:
        return False
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_lower and has_digit and has_special
'''

BUGGY_URL_NO_PATH = '''\
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
    return len(rest) > 0
'''

BUGGY_DATE_INVALID_ACCEPT = '''\
def validate_date_format(date_str: str) -> bool:
    """Validate date string is YYYY-MM-DD format."""
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    return True
'''

# ---------------------------------------------------------------------------
# Test files (templates)
# ---------------------------------------------------------------------------

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

    def test_truncation_with_ellipsis(self):
        assert truncate_string("hello world", 8) == "hello..."

    def test_very_short_max_len(self):
        result = truncate_string("hello", 4)
        assert len(result) <= 4 or result.endswith("...")


class TestCountSubstring:
    def test_basic_count(self):
        assert count_substring("hello world", "o") == 2

    def test_no_match(self):
        assert count_substring("hello", "xyz") == 0

    def test_empty_substring(self):
        assert count_substring("hello", "") == 0

    def test_count_with_context(self):
        assert count_substring("banana", "ana") == 1

    def test_case_sensitive(self):
        assert count_substring("AaAa", "a") == 2


class TestReverseWords:
    def test_basic_reverse(self):
        assert reverse_words("hello world") == "world hello"

    def test_single_word(self):
        assert reverse_words("hello") == "hello"

    def test_leading_trailing_spaces(self):
        assert reverse_words("  hello  world  ") == "world hello"


class TestPadString:
    def test_no_padding_needed(self):
        assert pad_string("hello", 5) == "hello"

    def test_padding_with_default_space(self):
        assert pad_string("hi", 5) == "hi   "

    def test_padding_with_custom_char(self):
        assert pad_string("hi", 5, "-") == "hi---"

    def test_longer_than_min_width(self):
        assert pad_string("hello world", 5) == "hello world"


class TestCapitalizeWords:
    def test_basic_capitalize(self):
        assert capitalize_words("hello world") == "Hello World"

    def test_empty_string(self):
        assert capitalize_words("") == ""

    def test_single_char_words(self):
        assert capitalize_words("a b c") == "A B C"

    def test_preserves_spaces(self):
        assert capitalize_words("hello  world") == "Hello  World"
'''

STRING_UTILS_TESTS_PRIVATE = '''\
"""Private tests for string_utils."""

from src.string_utils import (
    capitalize_words,
    count_substring,
    pad_string,
    reverse_words,
    truncate_string,
)


class TestTruncateStringPrivate:
    def test_unicode_truncation(self):
        result = truncate_string("caf\\u00e9", 4)
        assert result == "caf\\u00e9"

    def test_truncate_at_boundary(self):
        assert truncate_string("abcdefghij", 7) == "abcd..."


class TestCountSubstringPrivate:
    def test_repeated_pattern(self):
        assert count_substring("aaaa", "aa") == 2

    def test_substring_at_start_and_end(self):
        assert count_substring("ababab", "ab") == 3


class TestReverseWordsPrivate:
    def test_multiple_spaces(self):
        assert reverse_words("a  b  c") == "c b a"

    def test_tabs_and_newlines(self):
        assert reverse_words("hello\\tworld") == "world hello"


class TestPadStringPrivate:
    def test_zero_min_width(self):
        assert pad_string("hello", 0) == "hello"

    def test_empty_string_padding(self):
        assert pad_string("", 3) == "   "


class TestCapitalizeWordsPrivate:
    def test_mixed_case(self):
        assert capitalize_words("hELLo WoRLD") == "Hello World"

    def test_all_uppercase(self):
        assert capitalize_words("HELLO") == "Hello"
'''

STRING_UTILS_TESTS_QUALITY = '''\
"""Quality holdout tests for string_utils."""

from src.string_utils import (
    count_substring,
    pad_string,
    truncate_string,
)


class TestTruncateStringQuality:
    def test_short_string_unchanged(self):
        assert truncate_string("hi", 10) == "hi"

    def test_truncate_preserves_prefix(self):
        result = truncate_string("abcdefgh", 5)
        assert result.startswith("ab")


class TestCountSubstringQuality:
    def test_case_sensitive(self):
        assert count_substring("AaAa", "a") == 2

    def test_long_substring_no_match(self):
        assert count_substring("short", "longer_than_input") == 0


class TestPadStringQuality:
    def test_single_char_fill(self):
        assert pad_string("x", 1, "0") == "x"

    def test_large_padding(self):
        result = pad_string("a", 10, ".")
        assert len(result) == 10
        assert result == "a........."
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

    def test_double_at(self):
        assert validate_email("user@@example.com") is False

    def test_consecutive_dots_in_domain(self):
        assert validate_email("user@example..com") is False


class TestValidatePhone:
    def test_valid_10_digits(self):
        assert validate_phone("1234567890") is True

    def test_valid_with_plus(self):
        assert validate_phone("+861234567890") is True

    def test_too_short(self):
        assert validate_phone("12345") is False

    def test_non_digit_chars(self):
        assert validate_phone("123-456-7890x") is False

    def test_too_long(self):
        assert validate_phone("1234567890123456") is False


class TestValidatePasswordStrength:
    def test_strong_password(self):
        assert validate_password_strength("Abc12345!") is True

    def test_too_short(self):
        assert validate_password_strength("Ab1!") is False

    def test_no_uppercase(self):
        assert validate_password_strength("abc12345!") is False

    def test_no_special_char(self):
        assert validate_password_strength("Abc12345") is False

    def test_six_chars_too_short(self):
        assert validate_password_strength("Abc12!") is False


class TestValidateUrl:
    def test_valid_https(self):
        assert validate_url("https://example.com/path") is True

    def test_valid_http(self):
        assert validate_url("http://example.com/path") is True

    def test_no_protocol(self):
        assert validate_url("example.com/path") is False

    def test_ftp_protocol(self):
        assert validate_url("ftp://example.com/path") is False

    def test_no_path(self):
        assert validate_url("https://example.com") is False


class TestValidateDateFormat:
    def test_valid_date(self):
        assert validate_date_format("2024-01-15") is True

    def test_invalid_format(self):
        assert validate_date_format("01/15/2024") is False

    def test_invalid_month(self):
        assert validate_date_format("2024-13-01") is False

    def test_invalid_day(self):
        assert validate_date_format("2024-02-30") is False

    def test_slash_separator(self):
        assert validate_date_format("2024/01/15") is False
'''

VALIDATORS_TESTS_PRIVATE = '''\
"""Private tests for validators."""

from src.validators import (
    validate_date_format,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_url,
)


class TestValidateEmailPrivate:
    def test_empty_string(self):
        assert validate_email("") is False

    def test_no_domain(self):
        assert validate_email("user@") is False

    def test_subdomain(self):
        assert validate_email("user@sub.example.com") is True


class TestValidatePhonePrivate:
    def test_15_digits_max(self):
        assert validate_phone("123456789012345") is True

    def test_16_digits_too_long(self):
        assert validate_phone("1234567890123456") is False

    def test_spaces_format(self):
        assert validate_phone("123 456 7890") is True


class TestValidatePasswordStrengthPrivate:
    def test_exactly_8_chars(self):
        assert validate_password_strength("Abc1234!") is True

    def test_7_chars_fails(self):
        assert validate_password_strength("Abc123!") is False

    def test_all_digits(self):
        assert validate_password_strength("12345678") is False


class TestValidateUrlPrivate:
    def test_just_host(self):
        assert validate_url("https://example.com") is False

    def test_empty_string(self):
        assert validate_url("") is False

    def test_path_with_port(self):
        assert validate_url("http://localhost:8080/api") is True


class TestValidateDateFormatPrivate:
    def test_leap_year(self):
        assert validate_date_format("2024-02-29") is True

    def test_non_leap_year_feb29(self):
        assert validate_date_format("2023-02-29") is False

    def test_leap_year_century(self):
        assert validate_date_format("1900-02-29") is False

    def test_leap_year_400(self):
        assert validate_date_format("2000-02-29") is True
'''

VALIDATORS_TESTS_QUALITY = '''\
"""Quality holdout tests for validators."""

from src.validators import (
    validate_email,
    validate_password_strength,
    validate_phone,
)


class TestValidateEmailQuality:
    def test_numeric_local_part(self):
        assert validate_email("123@example.com") is True

    def test_dot_in_local_part(self):
        assert validate_email("first.last@example.com") is True


class TestValidatePhoneQuality:
    def test_leading_zeros(self):
        assert validate_phone("0012345678") is True

    def test_all_same_digit(self):
        assert validate_phone("1111111111") is True


class TestValidatePasswordStrengthQuality:
    def test_long_all_special(self):
        assert validate_password_strength("!!!!!!!!") is False

    def test_mixed_with_spaces(self):
        assert validate_password_strength("Abc 1234!") is True
'''

# ---------------------------------------------------------------------------
# Helper to assemble full buggy source from clean source + buggy function
# ---------------------------------------------------------------------------


def make_buggy_source(clean: str, clean_func_sig: str, buggy_func: str) -> str:
    """Replace one function in clean source with its buggy version."""
    # Find the function in clean source and replace it
    lines = clean.split("\n")
    result = []
    skip = False
    func_inserted = False
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect start of target function
        if not func_inserted and line.startswith(clean_func_sig):
            # Skip until next top-level def or end of indented block
            skip = True
            # Insert buggy version
            result.append(buggy_func.rstrip())
            func_inserted = True
            i += 1
            continue
        if skip:
            # Skip lines that are part of the old function (indented or blank after def)
            if line == "" or line[0] == " " or line[0] == "\t":
                i += 1
                continue
            else:
                skip = False
        result.append(line)
        i += 1
    return "\n".join(result)


# Actually, the above approach is fragile. Let me use a simpler approach:
# just define the full buggy source for each task variant directly.


def _make_string_utils_buggy(buggy_function_name: str, buggy_function_code: str) -> str:
    """Build a full string_utils.py with one buggy function replaced."""
    clean = STRING_UTILS_CLEAN
    lines = clean.split("\n")
    result = []
    in_target = False
    func_def_pattern = f"def {buggy_function_name}("

    for line in lines:
        if func_def_pattern in line and not in_target:
            in_target = True
            result.append(buggy_function_code.rstrip())
            continue
        if in_target:
            if line == "" or (len(line) > 0 and (line[0] == " " or line[0] == "\t")):
                continue
            else:
                in_target = False
        result.append(line)

    source = "\n".join(result)
    if not source.endswith("\n"):
        source += "\n"
    return source


def _make_validators_buggy(buggy_function_name: str, buggy_function_code: str) -> str:
    """Build a full validators.py with one buggy function replaced."""
    clean = VALIDATORS_CLEAN
    lines = clean.split("\n")
    result = []
    in_target = False
    func_def_pattern = f"def {buggy_function_name}("

    for line in lines:
        if func_def_pattern in line and not in_target:
            in_target = True
            result.append(buggy_function_code.rstrip())
            continue
        if in_target:
            if line == "" or (len(line) > 0 and (line[0] == " " or line[0] == "\t")):
                continue
            else:
                in_target = False
        result.append(line)

    source = "\n".join(result)
    if not source.endswith("\n"):
        source += "\n"
    return source


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

TASK_DEFS: list[dict] = []

# --- string_utils / boundary (task 0001-0005) ---

TASK_DEFS.append(
    {
        "task_id": "task_0001",
        "repo_type": "string_utils",
        "bug_type": "boundary",
        "bug_description": "truncate_string has off-by-one: uses s[:max_len] instead of s[:max_len-3], producing string that is too long.",
        "buggy_func_name": "truncate_string",
        "buggy_func_code": BUGGY_TRUNCATE_OFF_BY_ONE,
        "gold_old": "    return s[: max_len] + \"...\"",
        "gold_new": "    return s[: max_len - 3] + \"...\"",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0002",
        "repo_type": "string_utils",
        "bug_type": "boundary",
        "bug_description": "count_substring advances by 1 instead of len(sub), counting overlapping matches.",
        "buggy_func_name": "count_substring",
        "buggy_func_code": BUGGY_COUNT_OVERLAPPING,
        "gold_old": "        start = idx + 1",
        "gold_new": "        start = idx + len(sub)",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0003",
        "repo_type": "string_utils",
        "bug_type": "boundary",
        "bug_description": "reverse_words splits on single space only, failing to handle multiple consecutive spaces.",
        "buggy_func_name": "reverse_words",
        "buggy_func_code": BUGGY_REVERSE_SPLIT_ONLY_SPACE,
        "gold_old": '    return " ".join(s.split(" ")[::-1])',
        "gold_new": "    return \" \".join(s.split()[::-1])",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0004",
        "repo_type": "string_utils",
        "bug_type": "boundary",
        "bug_description": "pad_string computes padding as len(s)-min_width instead of min_width-len(s), producing wrong padding amount.",
        "buggy_func_name": "pad_string",
        "buggy_func_code": BUGGY_PAD_WRONG_MATH,
        "gold_old": "    padding = fill_char * (len(s) - min_width)",
        "gold_new": "    padding = fill_char * (min_width - len(s))",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0005",
        "repo_type": "string_utils",
        "bug_type": "boundary",
        "bug_description": "capitalize_words uses .upper() on the rest of the word instead of .lower().",
        "buggy_func_name": "capitalize_words",
        "buggy_func_code": BUGGY_CAPITALIZE_NO_LOWER,
        "gold_old": '    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))',
        "gold_new": '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
    }
)

# --- string_utils / string_validation (task 0006-0010) ---

TASK_DEFS.append(
    {
        "task_id": "task_0006",
        "repo_type": "string_utils",
        "bug_type": "string_validation",
        "bug_description": "truncate_string truncates at max_len-2 instead of max_len-3, producing one extra character.",
        "buggy_func_name": "truncate_string",
        "buggy_func_code": 'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string to max_len characters. Add \'...\' if truncated."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 2] + "..."\n',
        "gold_old": "    return s[: max_len - 2] + \"...\"",
        "gold_new": "    return s[: max_len - 3] + \"...\"",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0007",
        "repo_type": "string_utils",
        "bug_type": "string_validation",
        "bug_description": "count_substring uses case-insensitive comparison instead of case-sensitive.",
        "buggy_func_name": "count_substring",
        "buggy_func_code": 'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences of sub in s (case-insensitive)."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    s_lower = s.lower()\n    sub_lower = sub.lower()\n    while True:\n        idx = s_lower.find(sub_lower, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count\n',
        "gold_old": '    s_lower = s.lower()\n    sub_lower = sub.lower()\n    while True:\n        idx = s_lower.find(sub_lower, start)',
        "gold_new": '    while True:\n        idx = s.find(sub, start)',
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0008",
        "repo_type": "string_utils",
        "bug_type": "string_validation",
        "bug_description": "reverse_words reverses characters within each word instead of reversing word order.",
        "buggy_func_name": "reverse_words",
        "buggy_func_code": 'def reverse_words(s: str) -> str:\n    """Reverse each word in a string."""\n    return " ".join(w[::-1] for w in s.split())\n',
        "gold_old": '    return " ".join(w[::-1] for w in s.split())',
        "gold_new": "    return \" \".join(s.split()[::-1])",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0009",
        "repo_type": "string_utils",
        "bug_type": "string_validation",
        "bug_description": "pad_string pads on the left instead of the right.",
        "buggy_func_name": "pad_string",
        "buggy_func_code": 'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string to at least min_width characters using fill_char (left-padded)."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return padding + s\n',
        "gold_old": "    return padding + s",
        "gold_new": "    return s + padding",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0010",
        "repo_type": "string_utils",
        "bug_type": "string_validation",
        "bug_description": "capitalize_words only capitalizes the first word instead of all words.",
        "buggy_func_name": "capitalize_words",
        "buggy_func_code": 'def capitalize_words(s: str) -> str:\n    """Capitalize the first letter of the string."""\n    if not s:\n        return s\n    return s[0].upper() + s[1:]\n',
        "gold_old": "    if not s:\n        return s\n    return s[0].upper() + s[1:]",
        "gold_new": '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
    }
)

# --- validators / boundary (task 0011-0015) ---

TASK_DEFS.append(
    {
        "task_id": "task_0011",
        "repo_type": "validators",
        "bug_type": "boundary",
        "bug_description": "validate_email allows consecutive dots in domain (missing '..' check).",
        "buggy_func_name": "validate_email",
        "buggy_func_code": BUGGY_EMAIL_NO_DOUBLE_DOT,
        "gold_old": '    if not email:',
        "gold_new": '    if not email or ".." in email:',
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0012",
        "repo_type": "validators",
        "bug_type": "boundary",
        "bug_description": "validate_phone only checks length >= 10, does not verify all characters are digits.",
        "buggy_func_name": "validate_phone",
        "buggy_func_code": BUGGY_PHONE_NOT_ALL_DIGIT,
        "gold_old": "    return len(cleaned) >= 10",
        "gold_new": "    return cleaned.isdigit() and 10 <= len(cleaned) <= 15",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0013",
        "repo_type": "validators",
        "bug_type": "boundary",
        "bug_description": "validate_password_strength does not check for uppercase letters.",
        "buggy_func_name": "validate_password_strength",
        "buggy_func_code": BUGGY_PASSWORD_NO_UPPER,
        "gold_old": "    return has_lower and has_digit and has_special",
        "gold_new": "    has_upper = any(c.isupper() for c in password)\n    return has_upper and has_lower and has_digit and has_special",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0014",
        "repo_type": "validators",
        "bug_type": "boundary",
        "bug_description": "validate_url accepts URLs without a path component (e.g. 'https://example.com').",
        "buggy_func_name": "validate_url",
        "buggy_func_code": BUGGY_URL_NO_PATH,
        "gold_old": "    return len(rest) > 0",
        "gold_new": '    return len(rest) > 0 and "/" in rest',
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0015",
        "repo_type": "validators",
        "bug_type": "boundary",
        "bug_description": "validate_date_format only checks regex pattern, does not verify the date is real (accepts 2024-02-30).",
        "buggy_func_name": "validate_date_format",
        "buggy_func_code": BUGGY_DATE_INVALID_ACCEPT,
        "gold_old": '    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    return True',
        "gold_new": '    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
    }
)

# --- validators / string_validation (task 0016-0020) ---

TASK_DEFS.append(
    {
        "task_id": "task_0016",
        "repo_type": "validators",
        "bug_type": "string_validation",
        "bug_description": "validate_email does not check for empty local part, allows multiple @, and does not check domain start/end dots.",
        "buggy_func_name": "validate_email",
        "buggy_func_code": 'def validate_email(email: str) -> bool:\n    """Validate email format."""\n    if not email:\n        return False\n    if "@" not in email:\n        return False\n    domain = email.split("@")[1]\n    if "." not in domain:\n        return False\n    return True\n',
        "gold_old": '    if not email:\n        return False\n    if "@" not in email:\n        return False\n    domain = email.split("@")[1]\n    if "." not in domain:\n        return False\n    return True',
        "gold_new": '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0017",
        "repo_type": "validators",
        "bug_type": "string_validation",
        "bug_description": "validate_phone allows phone numbers longer than 15 digits.",
        "buggy_func_name": "validate_phone",
        "buggy_func_code": 'def validate_phone(phone: str) -> bool:\n    """Validate phone: digits with optional + prefix."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and len(cleaned) >= 10\n',
        "gold_old": "    return cleaned.isdigit() and len(cleaned) >= 10",
        "gold_new": "    return cleaned.isdigit() and 10 <= len(cleaned) <= 15",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0018",
        "repo_type": "validators",
        "bug_type": "string_validation",
        "bug_description": "validate_password_strength requires only 6 characters instead of 8.",
        "buggy_func_name": "validate_password_strength",
        "buggy_func_code": 'def validate_password_strength(password: str) -> bool:\n    """Validate password: >=6 chars, has upper, lower, digit, special char."""\n    if len(password) < 6:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special\n',
        "gold_old": "    if len(password) < 6:",
        "gold_new": "    if len(password) < 8:",
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0019",
        "repo_type": "validators",
        "bug_type": "string_validation",
        "bug_description": "validate_url also accepts ftp:// protocol.",
        "buggy_func_name": "validate_url",
        "buggy_func_code": 'def validate_url(url: str) -> bool:\n    """Validate URL: must start with http://, https://, or ftp://."""\n    if not url:\n        return False\n    for prefix in ("https://", "http://", "ftp://"):\n        if url.startswith(prefix):\n            rest = url[len(prefix):]\n            return len(rest) > 0 and "/" in rest\n    return False\n',
        "gold_old": '    for prefix in ("https://", "http://", "ftp://"):',
        "gold_new": '    for prefix in ("https://", "http://"):',
    }
)

TASK_DEFS.append(
    {
        "task_id": "task_0020",
        "repo_type": "validators",
        "bug_type": "string_validation",
        "bug_description": "validate_date_format accepts dates with '/' separator instead of '-' only.",
        "buggy_func_name": "validate_date_format",
        "buggy_func_code": 'def validate_date_format(date_str: str) -> bool:\n    """Validate date string is YYYY-MM-DD or YYYY/MM/DD and represents a real date."""\n    from datetime import datetime as _dt\n\n    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False\n',
        "gold_old": '    from datetime import datetime as _dt\n\n    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")',
        "gold_new": '    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")',
    }
)


# ---------------------------------------------------------------------------
# Generation logic
# ---------------------------------------------------------------------------


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_task(task_def: dict) -> None:
    task_id = task_def["task_id"]
    repo_type = task_def["repo_type"]
    task_dir = SEED_DIR / task_id
    repo_dir = task_dir / "repo"

    # Build buggy source
    if repo_type == "string_utils":
        buggy_source = _make_string_utils_buggy(task_def["buggy_func_name"], task_def["buggy_func_code"])
        src_name = "string_utils.py"
        test_name = "test_string_utils.py"
        private_test_name = "test_string_utils_private.py"
        quality_test_name = "test_string_utils_quality.py"
        test_content = STRING_UTILS_TESTS
        private_test_content = STRING_UTILS_TESTS_PRIVATE
        quality_test_content = STRING_UTILS_TESTS_QUALITY
    else:
        buggy_source = _make_validators_buggy(task_def["buggy_func_name"], task_def["buggy_func_code"])
        src_name = "validators.py"
        test_name = "test_validators.py"
        private_test_name = "test_validators_private.py"
        quality_test_name = "test_validators_quality.py"
        test_content = VALIDATORS_TESTS
        private_test_content = VALIDATORS_TESTS_PRIVATE
        quality_test_content = VALIDATORS_TESTS_QUALITY

    # metadata.json
    metadata = {
        "task_id": task_id,
        "repo_type": repo_type,
        "bug_type": task_def["bug_type"],
        "bug_description": task_def["bug_description"],
        "gold_patch": {
            "file_path": f"src/{src_name}",
            "old_text": task_def["gold_old"],
            "new_text": task_def["gold_new"],
        },
        "split": "seed",
    }
    write_file(task_dir / "metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))

    # Buggy source
    write_file(repo_dir / "src" / "__init__.py", "")
    write_file(repo_dir / "src" / src_name, buggy_source)

    # Tests (same for all tasks of same repo type)
    write_file(repo_dir / "tests" / "__init__.py", "")
    write_file(repo_dir / "tests" / test_name, test_content)

    write_file(repo_dir / "tests_private" / "__init__.py", "")
    write_file(repo_dir / "tests_private" / private_test_name, private_test_content)

    write_file(repo_dir / "tests_quality_holdout" / "__init__.py", "")
    write_file(repo_dir / "tests_quality_holdout" / quality_test_name, quality_test_content)


def main() -> None:
    # Clean existing seed directory
    if SEED_DIR.exists():
        shutil.rmtree(SEED_DIR)

    for task_def in TASK_DEFS:
        generate_task(task_def)
        print(f"  Generated {task_def['task_id']} ({task_def['repo_type']}/{task_def['bug_type']})")

    print(f"\nGenerated {len(TASK_DEFS)} seed tasks in {SEED_DIR}")


if __name__ == "__main__":
    main()
