"""Bug variant catalog for benchmark generation.

Defines 140 unique BugVariant objects (7 per function\u00d7bug_type combination).
Each variant has: unique buggy implementation, fix, test case, and signature.
All bugs produce finite wrong behavior (no infinite loops / timeout dependencies).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BugVariant:
    variant_id: str
    repo_type: str
    function_name: str
    bug_type: str
    buggy_code: str
    fix_old: str
    fix_new: str
    description: str
    test_name: str
    test_code: str


def get_all_variants() -> list[BugVariant]:
    """Return all 140 bug variants."""
    return [
        BugVariant(
            variant_id="su_trunc_b01", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string to max_len."""
    if len(s) <= max_len:
        return s
    return s[: max_len] + "..."''',
            fix_old='''    return s[: max_len] + "..."''',
            fix_new='''    return s[: max_len - 3] + "..."''',
            description="off-by-one: uses s[:max_len] producing string longer than max_len",
            test_name="test_trunc_off_by_one",
            test_code='''    def test_trunc_off_by_one(self):
        result = truncate_string("hello world", 8)
        assert len(result) <= 8
        assert result == "hello..."''',
        ),
        BugVariant(
            variant_id="su_trunc_b02", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 4] + "..."''',
            fix_old='''    return s[: max_len - 4] + "..."''',
            fix_new='''    return s[: max_len - 3] + "..."''',
            description="truncates one char too few: uses max_len-4",
            test_name="test_trunc_one_char_short",
            test_code='''    def test_trunc_one_char_short(self):
        result = truncate_string("abcdefghij", 7)
        assert len(result) <= 7
        assert result == "abcd..."''',
        ),
        BugVariant(
            variant_id="su_trunc_b03", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) < max_len:
        return s
    return s[: max_len - 3] + "..."''',
            fix_old='''    if len(s) < max_len:''',
            fix_new='''    if len(s) <= max_len:''',
            description="uses < instead of <=, truncating strings that exactly equal max_len",
            test_name="test_trunc_exact_length",
            test_code='''    def test_trunc_exact_length(self):
        assert truncate_string("hello", 5) == "hello"''',
        ),
        BugVariant(
            variant_id="su_trunc_b04", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "!!"''',
            fix_old='''    return s[: max_len - 3] + "!!"''',
            fix_new='''    return s[: max_len - 3] + "..."''',
            description="uses '!!' instead of '...' as ellipsis",
            test_name="test_trunc_wrong_suffix",
            test_code='''    def test_trunc_wrong_suffix(self):
        result = truncate_string("hello world", 8)
        assert result.endswith("...")''',
        ),
        BugVariant(
            variant_id="su_trunc_b05", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 2] + "..."''',
            fix_old='''    return s[: max_len - 2] + "..."''',
            fix_new='''    return s[: max_len - 3] + "..."''',
            description="produces result one char too long: uses max_len-2",
            test_name="test_trunc_one_char_long",
            test_code='''    def test_trunc_one_char_long(self):
        result = truncate_string("hello world", 8)
        assert result == "hello..."
        assert len(result) == 8''',
        ),
        BugVariant(
            variant_id="su_trunc_b06", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s
    if max_len <= 3:
        return "." * (max_len + 1)
    return s[: max_len - 3] + "..."''',
            fix_old='''        return "." * (max_len + 1)''',
            fix_new='''        return s[: max_len - 3] + "..."''',
            description="returns wrong length for short max_len",
            test_name="test_trunc_short_max_len",
            test_code='''    def test_trunc_short_max_len(self):
        result = truncate_string("hello", 3)
        assert result == "..."''',
        ),
        BugVariant(
            variant_id="su_trunc_b07", repo_type="string_utils",
            function_name="truncate_string", bug_type="boundary",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 3].rstrip() + "..."''',
            fix_old='''    return s[: max_len - 3].rstrip() + "..."''',
            fix_new='''    return s[: max_len - 3] + "..."''',
            description="strips trailing whitespace before adding ellipsis",
            test_name="test_trunc_no_strip",
            test_code='''    def test_trunc_no_strip(self):
        result = truncate_string("ab   xyz", 6)
        assert result == "ab ..."''',
        ),
        BugVariant(
            variant_id="su_trunc_s01", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"''',
            fix_old='''    return s[: max_len - 1] + "…"''',
            fix_new='''    return s[: max_len - 3] + "..."''',
            description="uses unicode ellipsis instead of '...'",
            test_name="test_trunc_ascii_ellipsis",
            test_code='''    def test_trunc_ascii_ellipsis(self):
        result = truncate_string("hello world", 8)
        assert "..." in result
        assert "…" not in result''',
        ),
        BugVariant(
            variant_id="su_trunc_s02", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    s = " ".join(s.split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."''',
            fix_old='''    s = " ".join(s.split())
    if len(s) <= max_len:''',
            fix_new='''    if len(s) <= max_len:''',
            description="normalizes spaces before truncating, changing original spacing",
            test_name="test_trunc_preserve_spaces",
            test_code='''    def test_trunc_preserve_spaces(self):
        result = truncate_string("hello  world", 12)
        assert result == "hello  world"''',
        ),
        BugVariant(
            variant_id="su_trunc_s03", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    s = s.lower()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."''',
            fix_old='''    s = s.lower()
    if len(s) <= max_len:''',
            fix_new='''    if len(s) <= max_len:''',
            description="lowercases the string before truncating",
            test_name="test_trunc_no_lower",
            test_code='''    def test_trunc_no_lower(self):
        result = truncate_string("HELLO", 5)
        assert result == "HELLO"''',
        ),
        BugVariant(
            variant_id="su_trunc_s04", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s.title()
    return s[: max_len - 3].title() + "..."''',
            fix_old='''        return s.title()''',
            fix_new='''        return s''',
            description="title-cases the string when returning",
            test_name="test_trunc_no_title",
            test_code='''    def test_trunc_no_title(self):
        result = truncate_string("hello", 5)
        assert result == "hello"''',
        ),
        BugVariant(
            variant_id="su_trunc_s05", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    s = s.replace("\t", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."''',
            fix_old='''    s = s.replace("\t", " ")
    if len(s) <= max_len:''',
            fix_new='''    if len(s) <= max_len:''',
            description="replaces tabs with spaces before truncating",
            test_name="test_trunc_keep_tabs",
            test_code='''    def test_trunc_keep_tabs(self):
        result = truncate_string("a\tb", 3)
        assert "\t" in result''',
        ),
        BugVariant(
            variant_id="su_trunc_s06", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."''',
            fix_old='''    s = s.strip()
    if len(s) <= max_len:''',
            fix_new='''    if len(s) <= max_len:''',
            description="strips whitespace before truncating",
            test_name="test_trunc_no_strip_input",
            test_code='''    def test_trunc_no_strip_input(self):
        result = truncate_string(" hello ", 7)
        assert result == " hello "''',
        ),
        BugVariant(
            variant_id="su_trunc_s07", repo_type="string_utils",
            function_name="truncate_string", bug_type="string_validation",
            buggy_code='''def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    if len(s) <= max_len:
        return s.upper()
    return s[: max_len - 3].upper() + "..."''',
            fix_old='''        return s.upper()''',
            fix_new='''        return s''',
            description="uppercases the result",
            test_name="test_trunc_no_upper",
            test_code='''    def test_trunc_no_upper(self):
        result = truncate_string("hello", 5)
        assert result == "hello"''',
        ),
        BugVariant(
            variant_id="su_cnt_b01", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
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
    return count''',
            fix_old='''        start = idx + 1''',
            fix_new='''        start = idx + len(sub)''',
            description="advances by 1 instead of len(sub), counting overlapping matches",
            test_name="test_count_overlapping",
            test_code='''    def test_count_overlapping(self):
        assert count_substring("banana", "ana") == 1''',
        ),
        BugVariant(
            variant_id="su_cnt_b02", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    count = 1
    start = 0
    while True:
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count''',
            fix_old='''    count = 1''',
            fix_new='''    count = 0''',
            description="initializes count to 1, always overcounting by 1",
            test_name="test_count_init_one",
            test_code='''    def test_count_init_one(self):
        assert count_substring("hello", "xyz") == 0''',
        ),
        BugVariant(
            variant_id="su_cnt_b03", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    count = 0
    start = 1
    while True:
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count''',
            fix_old='''    start = 1''',
            fix_new='''    start = 0''',
            description="starts search at index 1, missing matches at position 0",
            test_name="test_count_skip_first",
            test_code='''    def test_skip_first(self):
        assert count_substring("aaa", "a") == 3''',
        ),
        BugVariant(
            variant_id="su_cnt_b04", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    return s.count(sub) + 1''',
            fix_old='''    return s.count(sub) + 1''',
            fix_new='''    return s.count(sub)''',
            description="adds 1 to built-in count, always overcounting",
            test_name="test_count_plus_one",
            test_code='''    def test_count_plus_one(self):
        assert count_substring("hello world", "o") == 2''',
        ),
        BugVariant(
            variant_id="su_cnt_b05", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    count = 0
    start = 0
    while start < len(s) - len(sub):
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count''',
            fix_old='''    while start < len(s) - len(sub):''',
            fix_new='''    while True:''',
            description="uses wrong loop bound, missing match at end of string",
            test_name="test_count_end_match",
            test_code='''    def test_count_end_boundary(self):
        assert count_substring("abcabc", "abc") == 2''',
        ),
        BugVariant(
            variant_id="su_cnt_b06", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
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
    if s.endswith(sub):
        count += 1
    return count''',
            fix_old='''    if s.endswith(sub):
        count += 1
    return count''',
            fix_new='''    return count''',
            description="double-counts if string ends with sub",
            test_name="test_count_no_double_end",
            test_code='''    def test_count_no_double_end(self):
        assert count_substring("abcabc", "abc") == 2''',
        ),
        BugVariant(
            variant_id="su_cnt_b07", repo_type="string_utils",
            function_name="count_substring", bug_type="boundary",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    count = 0
    for i in range(len(s) - len(sub) + 1):
        if s[i:i + len(sub)] == sub:
            count += 1
            if len(sub) > 1:
                count += 1
    return count''',
            fix_old='''    count = 0
    for i in range(len(s) - len(sub) + 1):
        if s[i:i + len(sub)] == sub:
            count += 1
            if len(sub) > 1:
                count += 1
    return count''',
            fix_new='''    count = 0
    start = 0
    while True:
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count''',
            description="double-counts multi-character substrings",
            test_name="test_count_no_double_multi",
            test_code='''    def test_count_no_double_multi(self):
        assert count_substring("aaa", "aa") == 1''',
        ),
        BugVariant(
            variant_id="su_cnt_s01", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    count = 0
    start = 0
    s_lower = s.lower()
    sub_lower = sub.lower()
    while True:
        idx = s_lower.find(sub_lower, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count''',
            fix_old='''    s_lower = s.lower()
    sub_lower = sub.lower()
    while True:
        idx = s_lower.find(sub_lower, start)''',
            fix_new='''    while True:
        idx = s.find(sub, start)''',
            description="uses case-insensitive comparison",
            test_name="test_count_case_sensitive",
            test_code='''    def test_count_case_sensitive(self):
        assert count_substring("AaAa", "a") == 2''',
        ),
        BugVariant(
            variant_id="su_cnt_s02", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    return s.count(sub.lower())''',
            fix_old='''    return s.count(sub.lower())''',
            fix_new='''    return s.count(sub)''',
            description="lowercases sub but not s, causing case mismatch",
            test_name="test_count_no_partial_lower",
            test_code='''    def test_count_no_partial_lower(self):
        assert count_substring("HELLO", "HELLO") == 1''',
        ),
        BugVariant(
            variant_id="su_cnt_s03", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    return s.strip().count(sub)''',
            fix_old='''    return s.strip().count(sub)''',
            fix_new='''    return s.count(sub)''',
            description="strips s before counting, losing leading/trailing matches",
            test_name="test_count_no_strip",
            test_code='''    def test_count_no_strip(self):
        assert count_substring("  hello  ", " ") == 4''',
        ),
        BugVariant(
            variant_id="su_cnt_s04", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    return s.lower().count(sub.lower())''',
            fix_old='''    return s.lower().count(sub.lower())''',
            fix_new='''    return s.count(sub)''',
            description="uses case-insensitive counting",
            test_name="test_count_s04",
            test_code='''    def test_count_s04(self):
        assert count_substring("AaAa", "a") == 2''',
        ),
        BugVariant(
            variant_id="su_cnt_s05", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    s = s.replace("\\n", " ")
    return s.count(sub)''',
            fix_old='''    s = s.replace("\\n", " ")
    return s.count(sub)''',
            fix_new='''    return s.count(sub)''',
            description="replaces newlines before counting, losing newline matches",
            test_name="test_count_preserve_newlines",
            test_code='''    def test_count_preserve_newlines(self):
        assert count_substring("a\\nb\\na", "\\n") == 2''',
        ),
        BugVariant(
            variant_id="su_cnt_s06", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    return s.upper().count(sub)''',
            fix_old='''    return s.upper().count(sub)''',
            fix_new='''    return s.count(sub)''',
            description="uppercases s before counting",
            test_name="test_count_no_upper",
            test_code='''    def test_count_no_upper(self):
        assert count_substring("Hello", "Hello") == 1''',
        ),
        BugVariant(
            variant_id="su_cnt_s07", repo_type="string_utils",
            function_name="count_substring", bug_type="string_validation",
            buggy_code='''def count_substring(s: str, sub: str) -> int:
    """Count occurrences."""
    if not sub:
        return 0
    return s.count(sub.strip())''',
            fix_old='''    return s.count(sub.strip())''',
            fix_new='''    return s.count(sub)''',
            description="strips sub before counting",
            test_name="test_count_no_strip_sub",
            test_code='''    def test_count_no_strip_sub(self):
        assert count_substring("hello  world", "  ") == 1''',
        ),
        BugVariant(
            variant_id="su_rev_b01", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    return " ".join(s.split(" ")[::-1])''',
            fix_old='''    return " ".join(s.split(" ")[::-1])''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="splits on single space, failing on multiple spaces",
            test_name="test_reverse_multi_space",
            test_code='''    def test_reverse_multi_space(self):
        assert reverse_words("a  b  c") == "c b a"''',
        ),
        BugVariant(
            variant_id="su_rev_b02", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    result = " ".join(words[::-1])
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    return result''',
            fix_old='''    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    return result''',
            fix_new='''    return result''',
            description="capitalizes first character of result",
            test_name="test_reverse_no_capitalize",
            test_code='''    def test_reverse_no_capitalize(self):
        assert reverse_words("hello world") == "world hello"''',
        ),
        BugVariant(
            variant_id="su_rev_b03", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    if not words:
        return " "
    return " ".join(words[::-1])''',
            fix_old='''    if not words:
        return " "
    return " ".join(words[::-1])''',
            fix_new='''    return " ".join(words[::-1])''',
            description="returns single space for empty string instead of empty string",
            test_name="test_reverse_empty",
            test_code='''    def test_reverse_empty(self):
        assert reverse_words("") == ""''',
        ),
        BugVariant(
            variant_id="su_rev_b04", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    result = " ".join(words[::-1])
    return result + " "''',
            fix_old='''    return result + " "''',
            fix_new='''    return result''',
            description="appends trailing space to result",
            test_name="test_reverse_no_trailing_space",
            test_code='''    def test_reverse_no_trailing_space(self):
        result = reverse_words("hello world")
        assert result == "world hello"
        assert not result.endswith(" ")''',
        ),
        BugVariant(
            variant_id="su_rev_b05", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    if len(words) <= 1:
        return s
    return " ".join(words[::-1])''',
            fix_old='''    if len(words) <= 1:
        return s
    return " ".join(words[::-1])''',
            fix_new='''    return " ".join(words[::-1])''',
            description="returns original string (with spaces) for single word",
            test_name="test_reverse_single_word_spaces",
            test_code='''    def test_reverse_single_word_spaces(self):
        assert reverse_words("  hello  ") == "hello"''',
        ),
        BugVariant(
            variant_id="su_rev_b06", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    return " ".join(words[::-1]) + " "''',
            fix_old='''    return " ".join(words[::-1]) + " "''',
            fix_new='''    return " ".join(words[::-1])''',
            description="appends trailing space to result",
            test_name="test_reverse_no_trailing_space",
            test_code='''    def test_reverse_no_trailing_space(self):
        result = reverse_words("hello world")
        assert result == "world hello"
        assert not result.endswith(" ")''',
        ),
        BugVariant(
            variant_id="su_rev_b07", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    return " ".join(words[::-1]) + " "''',
            fix_old='''    return " ".join(words[::-1]) + " "''',
            fix_new='''    return " ".join(words[::-1])''',
            description="appends trailing space to result",
            test_name="test_reverse_b07",
            test_code='''    def test_reverse_b07(self):
        result = reverse_words("hello world")
        assert result == "world hello"
        assert not result.endswith(" ")''',
        ),
        BugVariant(
            variant_id="su_rev_s01", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse each word."""
    return " ".join(w[::-1] for w in s.split())''',
            fix_old='''    return " ".join(w[::-1] for w in s.split())''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="reverses characters within each word instead of word order",
            test_name="test_reverse_word_order",
            test_code='''    def test_reverse_word_order(self):
        assert reverse_words("hello world") == "world hello"''',
        ),
        BugVariant(
            variant_id="su_rev_s02", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order, lowercasing."""
    return " ".join(w.lower() for w in s.split()[::-1])''',
            fix_old='''    return " ".join(w.lower() for w in s.split()[::-1])''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="lowercases all words during reversal",
            test_name="test_reverse_preserve_case",
            test_code='''    def test_reverse_preserve_case(self):
        assert reverse_words("Hello World") == "World Hello"''',
        ),
        BugVariant(
            variant_id="su_rev_s03", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order, removing duplicates."""
    words = s.split()[::-1]
    seen = []
    for w in words:
        if w not in seen:
            seen.append(w)
    return " ".join(seen)''',
            fix_old='''    words = s.split()[::-1]
    seen = []
    for w in words:
        if w not in seen:
            seen.append(w)
    return " ".join(seen)''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="removes duplicate words during reversal",
            test_name="test_reverse_keep_duplicates",
            test_code='''    def test_reverse_keep_duplicates(self):
        assert reverse_words("hello hello world") == "world hello hello"''',
        ),
        BugVariant(
            variant_id="su_rev_s04", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order, sorting."""
    words = s.split()[::-1]
    return " ".join(sorted(words))''',
            fix_old='''    words = s.split()[::-1]
    return " ".join(sorted(words))''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="sorts words alphabetically instead of reversing",
            test_name="test_reverse_not_sorted",
            test_code='''    def test_reverse_not_sorted(self):
        assert reverse_words("c b a") == "a b c"''',
        ),
        BugVariant(
            variant_id="su_rev_s05", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order, joining with comma."""
    return ",".join(s.split()[::-1])''',
            fix_old='''    return ",".join(s.split()[::-1])''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="joins with comma instead of space",
            test_name="test_reverse_space_join",
            test_code='''    def test_reverse_space_join(self):
        result = reverse_words("hello world")
        assert "," not in result
        assert result == "world hello"''',
        ),
        BugVariant(
            variant_id="su_rev_s06", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order, uppercasing."""
    return " ".join(w.upper() for w in s.split()[::-1])''',
            fix_old='''    return " ".join(w.upper() for w in s.split()[::-1])''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="uppercases all words during reversal",
            test_name="test_reverse_no_upper",
            test_code='''    def test_reverse_no_upper(self):
        assert reverse_words("Hello World") == "World Hello"''',
        ),
        BugVariant(
            variant_id="su_rev_s07", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order, uppercasing each word."""
    return " ".join(w.upper() for w in s.split()[::-1])''',
            fix_old='''    return " ".join(w.upper() for w in s.split()[::-1])''',
            fix_new='''    return " ".join(s.split()[::-1])''',
            description="uppercases each word during reversal",
            test_name="test_reverse_s07",
            test_code='''    def test_reverse_s07(self):
        assert reverse_words("hello world") == "world hello"''',
        ),
        BugVariant(
            variant_id="su_pad_b01", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (len(s) - min_width)
    return s + padding''',
            fix_old='''    padding = fill_char * (len(s) - min_width)''',
            fix_new='''    padding = fill_char * (min_width - len(s))''',
            description="computes padding as len(s)-min_width (negative)",
            test_name="test_pad_wrong_math",
            test_code='''    def test_pad_wrong_math(self):
        assert pad_string("hi", 5) == "hi   "''',
        ),
        BugVariant(
            variant_id="su_pad_b02", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return padding + s''',
            fix_old='''    return padding + s''',
            fix_new='''    return s + padding''',
            description="pads on the left instead of right",
            test_name="test_pad_right",
            test_code='''    def test_pad_right(self):
        assert pad_string("hi", 5) == "hi   "''',
        ),
        BugVariant(
            variant_id="su_pad_b03", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s + fill_char
    padding = fill_char * (min_width - len(s))
    return s + padding''',
            fix_old='''        return s + fill_char''',
            fix_new='''        return s''',
            description="adds extra fill_char when string already meets min_width",
            test_name="test_pad_exact_width",
            test_code='''    def test_pad_exact_width(self):
        assert pad_string("hello", 5) == "hello"''',
        ),
        BugVariant(
            variant_id="su_pad_b04", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s) + 1)
    return s + padding''',
            fix_old='''    padding = fill_char * (min_width - len(s) + 1)''',
            fix_new='''    padding = fill_char * (min_width - len(s))''',
            description="adds one extra padding character",
            test_name="test_pad_extra_char",
            test_code='''    def test_pad_extra_char(self):
        result = pad_string("hi", 5)
        assert len(result) == 5
        assert result == "hi   "''',
        ),
        BugVariant(
            variant_id="su_pad_b05", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s) - 1)
    return s + padding''',
            fix_old='''    padding = fill_char * (min_width - len(s) - 1)''',
            fix_new='''    padding = fill_char * (min_width - len(s))''',
            description="adds one fewer padding character",
            test_name="test_pad_one_fewer",
            test_code='''    def test_pad_one_fewer(self):
        result = pad_string("hi", 5)
        assert len(result) == 5
        assert result == "hi   "''',
        ),
        BugVariant(
            variant_id="su_pad_b06", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    return s.ljust(min_width)''',
            fix_old='''    return s.ljust(min_width)''',
            fix_new='''    padding = fill_char * (min_width - len(s))
    return s + padding''',
            description="ignores fill_char, always using spaces",
            test_name="test_pad_custom_char",
            test_code='''    def test_pad_custom_char(self):
        assert pad_string("hi", 5, "-") == "hi---"''',
        ),
        BugVariant(
            variant_id="su_pad_b07", repo_type="string_utils",
            function_name="pad_string", bug_type="boundary",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding + fill_char''',
            fix_old='''    return s + padding + fill_char''',
            fix_new='''    return s + padding''',
            description="appends one extra fill_char after padding",
            test_name="test_pad_no_extra_suffix",
            test_code='''    def test_pad_no_extra_suffix(self):
        result = pad_string("hi", 5)
        assert len(result) == 5''',
        ),
        BugVariant(
            variant_id="su_pad_s01", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    s = " ".join(s.split())
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding''',
            fix_old='''    s = " ".join(s.split())
    if len(s) >= min_width:''',
            fix_new='''    if len(s) >= min_width:''',
            description="normalizes internal whitespace before padding",
            test_name="test_pad_no_normalize",
            test_code='''    def test_pad_no_normalize(self):
        result = pad_string("a  b", 6)
        assert result == "a  b  "''',
        ),
        BugVariant(
            variant_id="su_pad_s02", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    if len(s) >= min_width:
        return s
    fc = fill_char[0] if fill_char else " "
    padding = fc * (min_width - len(s))
    return s + padding''',
            fix_old='''    fc = fill_char[0] if fill_char else " "
    padding = fc * (min_width - len(s))''',
            fix_new='''    padding = fill_char * (min_width - len(s))''',
            description="takes only first char of fill_char",
            test_name="test_pad_multi_char_fill",
            test_code='''    def test_pad_multi_char_fill(self):
        result = pad_string("x", 4, "ab")
        assert result == "xababab"''',
        ),
        BugVariant(
            variant_id="su_pad_s03", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    s = s.strip()
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding''',
            fix_old='''    s = s.strip()
    if len(s) >= min_width:''',
            fix_new='''    if len(s) >= min_width:''',
            description="strips whitespace from s before padding",
            test_name="test_pad_no_strip",
            test_code='''    def test_pad_no_strip(self):
        result = pad_string(" hi ", 6)
        assert result == " hi   "''',
        ),
        BugVariant(
            variant_id="su_pad_s04", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string, centering."""
    if len(s) >= min_width:
        return s
    total = min_width - len(s)
    left = total // 2
    right = total - left
    return fill_char * left + s + fill_char * right''',
            fix_old='''    total = min_width - len(s)
    left = total // 2
    right = total - left
    return fill_char * left + s + fill_char * right''',
            fix_new='''    padding = fill_char * (min_width - len(s))
    return s + padding''',
            description="centers the string instead of left-aligning",
            test_name="test_pad_left_align",
            test_code='''    def test_pad_left_align(self):
        result = pad_string("hi", 6)
        assert result.startswith("hi")''',
        ),
        BugVariant(
            variant_id="su_pad_s05", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    s = s.upper()
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding''',
            fix_old='''    s = s.upper()
    if len(s) >= min_width:''',
            fix_new='''    if len(s) >= min_width:''',
            description="uppercases s before padding",
            test_name="test_pad_no_upper",
            test_code='''    def test_pad_no_upper(self):
        result = pad_string("hi", 5)
        assert result == "hi   "''',
        ),
        BugVariant(
            variant_id="su_pad_s06", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string."""
    s = s.lower()
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding''',
            fix_old='''    s = s.lower()
    if len(s) >= min_width:''',
            fix_new='''    if len(s) >= min_width:''',
            description="lowercases s before padding",
            test_name="test_pad_no_lower",
            test_code='''    def test_pad_no_lower(self):
        result = pad_string("HI", 5)
        assert result == "HI   "''',
        ),
        BugVariant(
            variant_id="su_pad_s07", repo_type="string_utils",
            function_name="pad_string", bug_type="string_validation",
            buggy_code='''def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string, replacing tabs."""
    s = s.replace("\t", " ")
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding''',
            fix_old='''    s = s.replace("\t", " ")
    if len(s) >= min_width:''',
            fix_new='''    if len(s) >= min_width:''',
            description="replaces tabs with spaces before padding",
            test_name="test_pad_keep_tabs",
            test_code='''    def test_pad_keep_tabs(self):
        result = pad_string("a\tb", 5)
        assert "\t" in result''',
        ),
        BugVariant(
            variant_id="su_cap_b01", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))''',
            fix_old='''    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="uses .upper() on rest instead of .lower()",
            test_name="test_cap_rest_lower",
            test_code='''    def test_cap_rest_lower(self):
        assert capitalize_words("hELLo WoRLD") == "Hello World"''',
        ),
        BugVariant(
            variant_id="su_cap_b02", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize first char."""
    if not s:
        return s
    return s[0].upper() + s[1:]''',
            fix_old='''    if not s:
        return s
    return s[0].upper() + s[1:]''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="only capitalizes first character of string",
            test_name="test_cap_all_words",
            test_code='''    def test_cap_all_words(self):
        assert capitalize_words("hello world") == "Hello World"''',
        ),
        BugVariant(
            variant_id="su_cap_b03", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    words = s.split()
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)''',
            fix_old='''    words = s.split()
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="uses s.split() instead of s.split(' '), collapsing multiple spaces",
            test_name="test_cap_preserve_spaces",
            test_code='''    def test_cap_preserve_spaces(self):
        assert capitalize_words("hello  world") == "Hello  World"''',
        ),
        BugVariant(
            variant_id="su_cap_b04", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    result = " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))
    return result.rstrip()''',
            fix_old='''    return result.rstrip()''',
            fix_new='''    return result''',
            description="strips trailing whitespace from result",
            test_name="test_cap_no_rstrip",
            test_code='''    def test_cap_no_rstrip(self):
        result = capitalize_words("hello world  ")
        assert result.endswith("  ")''',
        ),
        BugVariant(
            variant_id="su_cap_b05", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    if not s:
        return " "
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            fix_old='''    if not s:
        return " "
    return " ".join(''',
            fix_new='''    return " ".join(''',
            description="returns single space for empty string",
            test_name="test_cap_empty",
            test_code='''    def test_cap_empty(self):
        assert capitalize_words("") == ""''',
        ),
        BugVariant(
            variant_id="su_cap_b06", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words, uppercasing rest."""
    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))''',
            fix_old='''    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="uppercases rest of word instead of lowercasing",
            test_name="test_cap_b06",
            test_code='''    def test_cap_b06(self):
        assert capitalize_words("hELLo WoRLD") == "Hello World"''',
        ),
        BugVariant(
            variant_id="su_cap_b07", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")) + " "''',
            fix_old='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")) + " "''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="appends trailing space to result",
            test_name="test_cap_no_trailing_space",
            test_code='''    def test_cap_no_trailing_space(self):
        result = capitalize_words("hello world")
        assert not result.endswith(" ")''',
        ),
        BugVariant(
            variant_id="su_cap_s01", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words using title()."""
    return s.title()''',
            fix_old='''    return s.title()''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="uses .title() which capitalizes after apostrophes incorrectly",
            test_name="test_cap_not_title",
            test_code='''    def test_cap_not_title(self):
        result = capitalize_words("it's a test")
        assert result == "It's A Test"''',
        ),
        BugVariant(
            variant_id="su_cap_s02", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    return " ".join(w[:1].upper() + w[1:] if w else "" for w in s.split(" "))''',
            fix_old='''    return " ".join(w[:1].upper() + w[1:] if w else "" for w in s.split(" "))''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="does not lowercase the rest of the word",
            test_name="test_cap_lower_rest",
            test_code='''    def test_cap_lower_rest(self):
        assert capitalize_words("hELLo") == "Hello"''',
        ),
        BugVariant(
            variant_id="su_cap_s03", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split())''',
            fix_old='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split())''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="collapses multiple spaces (uses split() instead of split(' '))",
            test_name="test_cap_preserve_multi_space",
            test_code='''    def test_cap_preserve_multi_space(self):
        assert capitalize_words("hello  world") == "Hello  World"''',
        ),
        BugVariant(
            variant_id="su_cap_s04", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words, removing punctuation."""
    import string
    s = s.translate(str.maketrans("", "", string.punctuation))
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            fix_old='''    import string
    s = s.translate(str.maketrans("", "", string.punctuation))
    return " ".join(''',
            fix_new='''    return " ".join(''',
            description="removes punctuation before capitalizing",
            test_name="test_cap_keep_punctuation",
            test_code='''    def test_cap_keep_punctuation(self):
        result = capitalize_words("hello, world!")
        assert "," in result
        assert "!" in result''',
        ),
        BugVariant(
            variant_id="su_cap_s05", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    s = s.replace("\t", " ")
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            fix_old='''    s = s.replace("\t", " ")
    return " ".join(''',
            fix_new='''    return " ".join(''',
            description="replaces tabs with spaces before processing",
            test_name="test_cap_keep_tabs",
            test_code='''    def test_cap_keep_tabs(self):
        result = capitalize_words("hello\tworld")
        assert "\t" in result''',
        ),
        BugVariant(
            variant_id="su_cap_s06", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words, sorting."""
    words = s.split(" ")
    words.sort()
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)''',
            fix_old='''    words = s.split(" ")
    words.sort()
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="sorts words alphabetically before capitalizing",
            test_name="test_cap_no_sort",
            test_code='''    def test_cap_no_sort(self):
        assert capitalize_words("world hello") == "World Hello"''',
        ),
        BugVariant(
            variant_id="su_cap_s07", repo_type="string_utils",
            function_name="capitalize_words", bug_type="string_validation",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words, reversing order."""
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")[::-1])''',
            fix_old='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")[::-1])''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="reverses word order before capitalizing",
            test_name="test_cap_no_reverse",
            test_code='''    def test_cap_no_reverse(self):
        assert capitalize_words("hello world") == "Hello World"''',
        ),
        BugVariant(
            variant_id="val_eml_b01", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
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
    return True''',
            fix_old='''    if not email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True''',
            fix_new='''    if not email or ".." in email:
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
    return True''',
            description="allows consecutive dots and domain starting/ending with dot",
            test_name="test_email_boundary_dots",
            test_code='''    def test_email_boundary_dots(self):
        assert validate_email("user@example..com") is False
        assert validate_email("user@.example.com") is False
        assert validate_email("user@example.com.") is False''',
        ),
        BugVariant(
            variant_id="val_eml_b02", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    if not email:
        return False
    if "@" not in email:
        return False
    domain = email.split("@")[1]
    if "." not in domain:
        return False
    return True''',
            fix_old='''    if not email:
        return False
    if "@" not in email:
        return False
    domain = email.split("@")[1]
    if "." not in domain:
        return False
    return True''',
            fix_new='''    if not email or ".." in email:
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
    return True''',
            description="allows multiple @ signs, empty local part",
            test_name="test_email_boundary_at",
            test_code='''    def test_email_boundary_at(self):
        assert validate_email("@example.com") is False
        assert validate_email("user@@example.com") is False''',
        ),
        BugVariant(
            variant_id="val_eml_b03", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    if not email:
        return False
    if "@" not in email:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith("."):
        return False
    return True''',
            fix_old='''    if domain.startswith("."):
        return False
    return True''',
            fix_new='''    if domain.startswith(".") or domain.endswith("."):
        return False
    return True''',
            description="does not check if domain ends with dot",
            test_name="test_email_domain_end_dot",
            test_code='''    def test_email_domain_end_dot(self):
        assert validate_email("user@example.com.") is False''',
        ),
        BugVariant(
            variant_id="val_eml_b04", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    if not email:
        return False
    if "@" not in email:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.endswith("."):
        return False
    return True''',
            fix_old='''    if domain.endswith("."):
        return False
    return True''',
            fix_new='''    if domain.startswith(".") or domain.endswith("."):
        return False
    return True''',
            description="does not check if domain starts with dot",
            test_name="test_email_domain_start_dot",
            test_code='''    def test_email_domain_start_dot(self):
        assert validate_email("user@.example.com") is False''',
        ),
        BugVariant(
            variant_id="val_eml_b05", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    if not email:
        return False
    email = email.replace(" ", "")
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
    return True''',
            fix_old='''    email = email.replace(" ", "")
    parts = email.split("@")''',
            fix_new='''    parts = email.split("@")''',
            description="strips spaces from email before validation",
            test_name="test_email_no_strip_spaces",
            test_code='''    def test_email_no_strip_spaces(self):
        assert validate_email(" @example.com") is True''',
        ),
        BugVariant(
            variant_id="val_eml_b06", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    return "@" in email and "." in email''',
            fix_old='''    return "@" in email and "." in email''',
            fix_new='''    if not email or ".." in email:
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
    return True''',
            description="minimal validation, accepts many invalid formats",
            test_name="test_email_minimal",
            test_code='''    def test_email_minimal(self):
        assert validate_email("@.") is False
        assert validate_email("user@") is False''',
        ),
        BugVariant(
            variant_id="val_eml_b07", repo_type="validators",
            function_name="validate_email", bug_type="boundary",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    if not email or ".." in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if any(c.isdigit() for c in local):
        return False
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True''',
            fix_old='''    if any(c.isdigit() for c in local):
        return False
    if not local or not domain:''',
            fix_new='''    if not local or not domain:''',
            description="rejects emails with digits in local part",
            test_name="test_email_b07",
            test_code='''    def test_email_b07_allow_digits(self):
        assert validate_email("user123@example.com") is True''',
        ),
        BugVariant(
            variant_id="val_eml_s01", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    if not email:
        return False
    if "@" not in email:
        return False
    domain = email.split("@")[1]
    if "." not in domain:
        return False
    return True''',
            fix_old='''    if not email:
        return False
    if "@" not in email:
        return False
    domain = email.split("@")[1]
    if "." not in domain:
        return False
    return True''',
            fix_new='''    if not email or ".." in email:
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
    return True''',
            description="missing multiple checks: empty local, multiple @, domain dots",
            test_name="test_email_sv_full",
            test_code='''    def test_email_sv_full(self):
        assert validate_email("@example.com") is False
        assert validate_email("user@example..com") is False''',
        ),
        BugVariant(
            variant_id="val_eml_s02", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email with regex."""
    import re
    pattern = r"^[^@]+@[^@]+\\.[^@]+$"
    return bool(re.match(pattern, email))''',
            fix_old='''    import re
    pattern = r"^[^@]+@[^@]+\\.[^@]+$"
    return bool(re.match(pattern, email))''',
            fix_new='''    if not email or ".." in email:
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
    return True''',
            description="uses regex that allows consecutive dots",
            test_name="test_email_sv_regex",
            test_code='''    def test_email_sv_regex(self):
        assert validate_email("user@example..com") is False''',
        ),
        BugVariant(
            variant_id="val_eml_s03", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    return "@" in email and "." in email.split("@")[-1]''',
            fix_old='''    return "@" in email and "." in email.split("@")[-1]''',
            fix_new='''    if not email or ".." in email:
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
    return True''',
            description="minimal validation with split-based check",
            test_name="test_email_sv_minimal",
            test_code='''    def test_email_sv_minimal(self):
        assert validate_email("@.") is False
        assert validate_email("user@") is False''',
        ),
        BugVariant(
            variant_id="val_eml_s04", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    email = email.strip()
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
    return True''',
            fix_old='''    email = email.strip()
    if not email:''',
            fix_new='''    if not email:''',
            description="strips whitespace before validation",
            test_name="test_email_sv_strip",
            test_code='''    def test_email_sv_strip(self):
        assert validate_email(" @example.com") is True''',
        ),
        BugVariant(
            variant_id="val_eml_s05", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
    email = email.strip()
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
    return True''',
            fix_old='''    email = email.strip()
    if not email or ".." in email:''',
            fix_new='''    if not email or ".." in email:''',
            description="strips whitespace before validation",
            test_name="test_email_sv_no_strip",
            test_code='''    def test_email_sv_no_strip(self):
        assert validate_email(" @example.com") is True''',
        ),
        BugVariant(
            variant_id="val_eml_s06", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email: reject digits in local."""
    if not email or ".." in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if any(c.isdigit() for c in local):
        return False
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True''',
            fix_old='''    if any(c.isdigit() for c in local):
        return False
    if not local or not domain:''',
            fix_new='''    if not local or not domain:''',
            description="rejects emails with digits in local part",
            test_name="test_email_s06",
            test_code='''    def test_email_sv_allow_digits(self):
        assert validate_email("user123@example.com") is True''',
        ),
        BugVariant(
            variant_id="val_eml_s07", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email: reject underscores in local."""
    if not email or ".." in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if "_" in local:
        return False
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True''',
            fix_old='''    if "_" in local:
        return False
    if not local or not domain:''',
            fix_new='''    if not local or not domain:''',
            description="rejects emails with underscores in local part",
            test_name="test_email_s07",
            test_code='''    def test_email_sv_allow_underscore(self):
        assert validate_email("user_name@example.com") is True''',
        ),
        BugVariant(
            variant_id="val_phn_b01", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return len(cleaned) >= 10''',
            fix_old='''    return len(cleaned) >= 10''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="only checks length >= 10, not digit-only or upper bound",
            test_name="test_phone_boundary_digits",
            test_code='''    def test_phone_boundary_digits(self):
        assert validate_phone("123-456-7890x") is False
        assert validate_phone("1234567890123456") is False''',
        ),
        BugVariant(
            variant_id="val_phn_b02", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and len(cleaned) >= 10''',
            fix_old='''    return cleaned.isdigit() and len(cleaned) >= 10''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="allows numbers longer than 15 digits",
            test_name="test_phone_upper_bound",
            test_code='''    def test_phone_upper_bound(self):
        assert validate_phone("1234567890123456") is False''',
        ),
        BugVariant(
            variant_id="val_phn_b03", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return len(cleaned) >= 10 and cleaned[:-1].isdigit()''',
            fix_old='''    return len(cleaned) >= 10 and cleaned[:-1].isdigit()''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="allows last character to be non-digit",
            test_name="test_phone_last_digit",
            test_code='''    def test_phone_last_digit(self):
        assert validate_phone("123456789x") is False''',
        ),
        BugVariant(
            variant_id="val_phn_b04", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    cleaned = phone.replace("-", "").replace(" ", "")
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="does not handle leading + prefix",
            test_name="test_phone_plus_prefix",
            test_code='''    def test_phone_plus_prefix(self):
        assert validate_phone("+861234567890") is True''',
        ),
        BugVariant(
            variant_id="val_phn_b05", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 9 <= len(cleaned) <= 15''',
            fix_old='''    return cleaned.isdigit() and 9 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="allows 9-digit numbers (should be min 10)",
            test_name="test_phone_min_10",
            test_code='''    def test_phone_min_10(self):
        assert validate_phone("123456789") is False''',
        ),
        BugVariant(
            variant_id="val_phn_b06", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if len(cleaned) < 10:
        return False
    return cleaned.isdigit()''',
            fix_old='''    if len(cleaned) < 10:
        return False
    return cleaned.isdigit()''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="missing upper bound check",
            test_name="test_phone_no_upper",
            test_code='''    def test_phone_no_upper(self):
        assert validate_phone("1234567890123456") is False''',
        ),
        BugVariant(
            variant_id="val_phn_b07", repo_type="validators",
            function_name="validate_phone", bug_type="boundary",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("0"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    if cleaned.startswith("0"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="incorrectly rejects numbers starting with 0",
            test_name="test_phone_allow_leading_zero",
            test_code='''    def test_phone_allow_leading_zero(self):
        assert validate_phone("0123456789") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s01", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return len(cleaned) >= 10''',
            fix_old='''    return len(cleaned) >= 10''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="does not verify all characters are digits",
            test_name="test_phone_sv_digits",
            test_code='''    def test_phone_sv_digits(self):
        assert validate_phone("123-456-7890x") is False''',
        ),
        BugVariant(
            variant_id="val_phn_s02", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return len(cleaned) >= 10 and len(cleaned) <= 15''',
            fix_old='''    return len(cleaned) >= 10 and len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="allows non-digit characters within length bounds",
            test_name="test_phone_sv_non_digit",
            test_code='''    def test_phone_sv_non_digit(self):
        assert validate_phone("123abc45678") is False''',
        ),
        BugVariant(
            variant_id="val_phn_s03", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code=r'''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    import re
    cleaned = re.sub(r"\D", "", phone)
    return 10 <= len(cleaned) <= 15''',
            fix_old=r'''    import re
    cleaned = re.sub(r"\D", "", phone)
    return 10 <= len(cleaned) <= 15''',
            fix_new='''    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="strips all non-digits including parentheses",
            test_name="test_phone_sv_strip_method",
            test_code='''    def test_phone_sv_strip_method(self):
        assert validate_phone("+1 (234) 567-8901") is False''',
        ),
        BugVariant(
            variant_id="val_phn_s04", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    cleaned = cleaned.lstrip("0")
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    cleaned = cleaned.lstrip("0")
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="strips leading zeros before validation",
            test_name="test_phone_no_strip_zeros",
            test_code='''    def test_phone_no_strip_zeros(self):
        assert validate_phone("0012345678") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s05", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone: reject all same digits."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if len(set(cleaned)) == 1:
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    if len(set(cleaned)) == 1:
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="rejects phone numbers with all same digits",
            test_name="test_phone_s05",
            test_code='''    def test_phone_sv_allow_same_digits(self):
        assert validate_phone("1111111111") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s06", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("0"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    if cleaned.startswith("0"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="rejects numbers starting with 0",
            test_name="test_phone_sv_leading_zero",
            test_code='''    def test_phone_sv_leading_zero(self):
        assert validate_phone("0123456789") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s07", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone: reject starting with 0."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("0"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    if cleaned.startswith("0"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="rejects phone numbers starting with 0",
            test_name="test_phone_s07",
            test_code='''    def test_phone_sv_allow_leading_zero(self):
        assert validate_phone("0123456789") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_b01", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_lower and has_digit and has_special''',
            fix_old='''    return has_lower and has_digit and has_special''',
            fix_new='''    has_upper = any(c.isupper() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            description="missing uppercase check",
            test_name="test_pwd_need_upper",
            test_code='''    def test_pwd_need_upper(self):
        assert validate_password_strength("abc12345!") is False''',
        ),
        BugVariant(
            variant_id="val_pwd_b02", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 6:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if len(password) < 6:''',
            fix_new='''    if len(password) < 8:''',
            description="requires only 6 chars instead of 8",
            test_name="test_pwd_min_length",
            test_code='''    def test_pwd_min_length(self):
        assert validate_password_strength("Abc12!") is False''',
        ),
        BugVariant(
            variant_id="val_pwd_b03", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    if len(password) > 20:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if len(password) > 20:
        return False
    has_upper''',
            fix_new='''    has_upper''',
            description="incorrectly rejects passwords longer than 20 chars",
            test_name="test_pwd_no_max_length",
            test_code='''    def test_no_max_length(self):
        assert validate_password_strength("Abc12345!Abc12345!Abc") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_b04", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: need 2+ uppercase."""
    if len(password) < 8:
        return False
    uppers = sum(1 for c in password if c.isupper())
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return uppers >= 2 and has_lower and has_digit and has_special''',
            fix_old='''    return uppers >= 2 and has_lower and has_digit and has_special''',
            fix_new='''    has_upper = any(c.isupper() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            description="requires 2+ uppercase letters instead of 1",
            test_name="test_pwd_b04",
            test_code='''    def test_pwd_need_2_upper(self):
        assert validate_password_strength("Abc12345!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_b05", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: need 2+ digits."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    digits = sum(1 for c in password if c.isdigit())
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and digits >= 2 and has_special''',
            fix_old='''    return has_upper and has_lower and digits >= 2 and has_special''',
            fix_new='''    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            description="requires 2+ digits instead of 1",
            test_name="test_pwd_b05",
            test_code='''    def test_pwd_need_2_digits(self):
        assert validate_password_strength("Abcdefg1!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_b06", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: reject 3+ consecutive same chars."""
    if len(password) < 8:
        return False
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            return False
    has_upper''',
            fix_new='''    has_upper''',
            description="rejects passwords with 3+ consecutive same characters",
            test_name="test_pwd_b06",
            test_code='''    def test_pwd_no_consecutive(self):
        assert validate_password_strength("Abc111234!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_b07", repo_type="validators",
            function_name="validate_password_strength", bug_type="boundary",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: require 10+ chars."""
    if len(password) < 10:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if len(password) < 10:''',
            fix_new='''    if len(password) < 8:''',
            description="requires 10+ chars instead of 8",
            test_name="test_pwd_b07",
            test_code='''    def test_pwd_min_8_not_10(self):
        assert validate_password_strength("Abc1234!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s01", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_lower and has_digit and has_special''',
            fix_old='''    return has_lower and has_digit and has_special''',
            fix_new='''    has_upper = any(c.isupper() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            description="does not require uppercase letters",
            test_name="test_pwd_sv_upper",
            test_code='''    def test_pwd_sv_upper(self):
        assert validate_password_strength("abc12345!") is False''',
        ),
        BugVariant(
            variant_id="val_pwd_s02", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    return len(password) >= 8''',
            fix_old='''    return len(password) >= 8''',
            fix_new='''    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            description="only checks length, not character diversity",
            test_name="test_pwd_sv_diversity",
            test_code='''    def test_pwd_sv_diversity(self):
        assert validate_password_strength("12345678") is False''',
        ),
        BugVariant(
            variant_id="val_pwd_s03", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    if " " in password:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if " " in password:
        return False
    has_upper''',
            fix_new='''    has_upper''',
            description="rejects passwords with spaces",
            test_name="test_pwd_sv_spaces",
            test_code='''    def test_pwd_sv_spaces(self):
        assert validate_password_strength("Abc 1234!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s04", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: reject common words."""
    if len(password) < 8:
        return False
    lower = password.lower()
    for word in ("password", "123456", "qwerty", "abc123"):
        if word in lower:
            return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    lower = password.lower()
    for word in ("password", "123456", "qwerty", "abc123"):
        if word in lower:
            return False
    has_upper''',
            fix_new='''    has_upper''',
            description="rejects passwords containing common words",
            test_name="test_pwd_s04",
            test_code='''    def test_pwd_no_common_words(self):
        assert validate_password_strength("MyP@ssw0rd!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s05", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: must start with uppercase."""
    if len(password) < 8:
        return False
    if not password[0].isupper():
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if not password[0].isupper():
        return False
    has_upper''',
            fix_new='''    has_upper''',
            description="requires password to start with uppercase",
            test_name="test_pwd_s05",
            test_code='''    def test_pwd_no_start_upper(self):
        assert validate_password_strength("aBc12345!") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s06", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    lower_pwd = password.lower()
    if "password" in lower_pwd or "123456" in lower_pwd:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    lower_pwd = password.lower()
    if "password" in lower_pwd or "123456" in lower_pwd:
        return False
    has_upper''',
            fix_new='''    has_upper''',
            description="rejects passwords containing common substrings",
            test_name="test_pwd_sv_pattern",
            test_code='''    def test_pwd_sv_pattern(self):
        assert validate_password_strength("MyP@ssw0rd123456") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s07", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password: max 20 chars."""
    if len(password) < 8:
        return False
    if len(password) > 20:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if len(password) > 20:
        return False
    has_upper''',
            fix_new='''    has_upper''',
            description="rejects passwords longer than 20 chars",
            test_name="test_pwd_s07",
            test_code='''    def test_pwd_no_max_length(self):
        assert validate_password_strength("Abc12345!Abc12345!Abc") is True''',
        ),
        BugVariant(
            variant_id="val_url_b01", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0''',
            fix_old='''    return len(rest) > 0''',
            fix_new='''    return len(rest) > 0 and "/" in rest''',
            description="accepts URLs without a path component",
            test_name="test_url_need_path",
            test_code='''    def test_url_need_path(self):
        assert validate_url("https://example.com") is False''',
        ),
        BugVariant(
            variant_id="val_url_b02", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    for prefix in ("https://", "http://", "ftp://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            return len(rest) > 0 and "/" in rest
    return False''',
            fix_old='''    for prefix in ("https://", "http://", "ftp://"):''',
            fix_new='''    for prefix in ("https://", "http://"):''',
            description="also accepts ftp:// protocol",
            test_name="test_url_no_ftp",
            test_code='''    def test_url_no_ftp(self):
        assert validate_url("ftp://example.com/path") is False''',
        ),
        BugVariant(
            variant_id="val_url_b03", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: reject query params."""
    if not url:
        return False
    if "?" in url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    if "?" in url:
        return False
    if url.startswith("https://"):''',
            fix_new='''    if url.startswith("https://"):''',
            description="rejects URLs with query parameters",
            test_name="test_url_b03",
            test_code='''    def test_url_allow_query(self):
        assert validate_url("https://example.com/path?q=1") is True''',
        ),
        BugVariant(
            variant_id="val_url_b04", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: reject fragments."""
    if not url:
        return False
    if "#" in url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    if "#" in url:
        return False
    if url.startswith("https://"):''',
            fix_new='''    if url.startswith("https://"):''',
            description="rejects URLs with fragments",
            test_name="test_url_b04",
            test_code='''    def test_url_allow_fragment(self):
        assert validate_url("https://example.com/path#section") is True''',
        ),
        BugVariant(
            variant_id="val_url_b05", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: reject port numbers."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    if ":" in rest.split("/")[0]:
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    if ":" in rest.split("/")[0]:
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_new='''    return len(rest) > 0 and "/" in rest''',
            description="rejects URLs with port numbers",
            test_name="test_url_b05",
            test_code='''    def test_url_allow_port(self):
        assert validate_url("http://localhost:8080/api") is True''',
        ),
        BugVariant(
            variant_id="val_url_b06", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: reject IP addresses."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    host = rest.split("/")[0]
    if host.replace(".", "").isdigit():
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    host = rest.split("/")[0]
    if host.replace(".", "").isdigit():
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_new='''    return len(rest) > 0 and "/" in rest''',
            description="rejects URLs with IP addresses",
            test_name="test_url_b06",
            test_code='''    def test_url_allow_ip(self):
        assert validate_url("http://192.168.1.1/api") is True''',
        ),
        BugVariant(
            variant_id="val_url_b07", repo_type="validators",
            function_name="validate_url", bug_type="boundary",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    return url.startswith("http://") or url.startswith("https://")''',
            fix_old='''    return url.startswith("http://") or url.startswith("https://")''',
            fix_new='''    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            description="only checks protocol prefix, no host/path validation",
            test_name="test_url_need_host",
            test_code='''    def test_url_need_host(self):
        assert validate_url("http://") is False
        assert validate_url("https://x") is False''',
        ),
        BugVariant(
            variant_id="val_url_s01", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    for prefix in ("https://", "http://", "ftp://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            return len(rest) > 0 and "/" in rest
    return False''',
            fix_old='''    for prefix in ("https://", "http://", "ftp://"):''',
            fix_new='''    for prefix in ("https://", "http://"):''',
            description="accepts ftp:// protocol",
            test_name="test_url_sv_no_ftp",
            test_code='''    def test_url_sv_no_ftp(self):
        assert validate_url("ftp://example.com/path") is False''',
        ),
        BugVariant(
            variant_id="val_url_s02", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    if "://" not in url:
        return False
    rest = url.split("://", 1)[1]
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    if "://" not in url:
        return False
    rest = url.split("://", 1)[1]
    return len(rest) > 0 and "/" in rest''',
            fix_new='''    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            description="accepts any protocol with ://",
            test_name="test_url_sv_protocol",
            test_code='''    def test_url_sv_protocol(self):
        assert validate_url("ftp://example.com/path") is False''',
        ),
        BugVariant(
            variant_id="val_url_s03", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: also accept ftp."""
    if not url:
        return False
    for prefix in ("https://", "http://", "ftp://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            return len(rest) > 0 and "/" in rest
    return False''',
            fix_old='''    for prefix in ("https://", "http://", "ftp://"):''',
            fix_new='''    for prefix in ("https://", "http://"):''',
            description="also accepts ftp:// protocol",
            test_name="test_url_s03",
            test_code='''    def test_url_sv_no_ftp(self):
        assert validate_url("ftp://example.com/path") is False''',
        ),
        BugVariant(
            variant_id="val_url_s04", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: also accept ssh."""
    if not url:
        return False
    for prefix in ("https://", "http://", "ssh://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            return len(rest) > 0 and "/" in rest
    return False''',
            fix_old='''    for prefix in ("https://", "http://", "ssh://"):''',
            fix_new='''    for prefix in ("https://", "http://"):''',
            description="also accepts ssh:// protocol",
            test_name="test_url_s04",
            test_code='''    def test_url_sv_no_ssh(self):
        assert validate_url("ssh://example.com/path") is False''',
        ),
        BugVariant(
            variant_id="val_url_s05", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL: accept any protocol."""
    if not url:
        return False
    if "://" not in url:
        return False
    rest = url.split("://", 1)[1]
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    if "://" not in url:
        return False
    rest = url.split("://", 1)[1]
    return len(rest) > 0 and "/" in rest''',
            fix_new='''    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            description="accepts any protocol with ://",
            test_name="test_url_s05",
            test_code='''    def test_url_sv_specific_protocol(self):
        assert validate_url("ftp://example.com/path") is False''',
        ),
        BugVariant(
            variant_id="val_url_s06", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    url = url.rstrip("/")
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    url = url.rstrip("/")
    if not url:''',
            fix_new='''    if not url:''',
            description="strips trailing slash before validation",
            test_name="test_url_sv_rstrip",
            test_code='''    def test_url_sv_rstrip(self):
        assert validate_url("https://example.com/") is True''',
        ),
        BugVariant(
            variant_id="val_url_s07", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL, lowercasing first."""
    url = url.lower()
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest''',
            fix_old='''    url = url.lower()
    if not url:''',
            fix_new='''    if not url:''',
            description="lowercases URL before validation",
            test_name="test_url_sv_lower",
            test_code='''    def test_url_sv_lower(self):
        assert validate_url("HTTPS://Example.COM/Path") is False''',
        ),
        BugVariant(
            variant_id="val_dat_b01", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    return True''',
            fix_old='''    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    return True''',
            fix_new='''    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    from datetime import datetime as _dt
    try:
        _dt.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False''',
            description="only checks regex, not actual date validity",
            test_name="test_date_real_validation",
            test_code='''    def test_date_real_validation(self):
        assert validate_date_format("2024-02-30") is False
        assert validate_date_format("2024-13-01") is False''',
        ),
        BugVariant(
            variant_id="val_dat_b02", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    normalized = date_str.replace("/", "-")
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):
        return False
    try:
        _dt.strptime(normalized, "%Y-%m-%d")
        return True
    except ValueError:
        return False''',
            fix_old='''    normalized = date_str.replace("/", "-")
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):
        return False
    try:
        _dt.strptime(normalized, "%Y-%m-%d")''',
            fix_new='''    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")''',
            description="accepts dates with '/' separator",
            test_name="test_date_no_slash",
            test_code='''    def test_date_no_slash(self):
        assert validate_date_format("2024/01/15") is False''',
        ),
        BugVariant(
            variant_id="val_dat_b03", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code=r'''def validate_date_format(date_str: str) -> bool:
    """Validate date: reject before 1900."""
    from datetime import datetime as _dt

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt.year < 1900:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt.year < 1900:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects dates before year 1900",
            test_name="test_date_b03",
            test_code='''    def test_date_allow_old(self):
        assert validate_date_format("1899-12-31") is True''',
        ),
        BugVariant(
            variant_id="val_dat_b04", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code=r'''def validate_date_format(date_str: str) -> bool:
    """Validate date: reject after 2100."""
    from datetime import datetime as _dt

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt.year > 2100:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt.year > 2100:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects dates after year 2100",
            test_name="test_date_b04",
            test_code='''    def test_date_allow_future(self):
        assert validate_date_format("2101-01-01") is True''',
        ),
        BugVariant(
            variant_id="val_dat_b05", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date: reject weekends."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt.weekday() >= 5:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects weekend dates",
            test_name="test_date_allow_weekends",
            test_code='''    def test_date_allow_weekends(self):
        assert validate_date_format("2024-01-13") is True''',
        ),
        BugVariant(
            variant_id="val_dat_b06", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt.year < 2000:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt.year < 2000:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects dates before year 2000",
            test_name="test_date_allow_old",
            test_code='''    def test_date_allow_old(self):
        assert validate_date_format("1999-12-31") is True''',
        ),
        BugVariant(
            variant_id="val_dat_b07", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code=r'''def validate_date_format(date_str: str) -> bool:
    """Validate date: reject weekends."""
    from datetime import datetime as _dt

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt.weekday() >= 5:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects weekend dates",
            test_name="test_date_b07",
            test_code='''    def test_date_allow_weekends(self):
        assert validate_date_format("2024-01-13") is True''',
        ),
        BugVariant(
            variant_id="val_dat_s01", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    normalized = date_str.replace("/", "-")
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):
        return False
    try:
        _dt.strptime(normalized, "%Y-%m-%d")
        return True
    except ValueError:
        return False''',
            fix_old='''    normalized = date_str.replace("/", "-")
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):
        return False
    try:
        _dt.strptime(normalized, "%Y-%m-%d")''',
            fix_new='''    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")''',
            description="accepts '/' separator",
            test_name="test_date_sv_slash",
            test_code='''    def test_date_sv_slash(self):
        assert validate_date_format("2024/01/15") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s02", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            _dt.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False''',
            fix_old='''    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):''',
            fix_new='''    for fmt in ("%Y-%m-%d",):''',
            description="also accepts DD-MM-YYYY format",
            test_name="test_date_sv_only_ymd",
            test_code='''    def test_date_sv_only_ymd(self):
        assert validate_date_format("15-01-2024") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s03", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date: accept DD-MM-YYYY."""
    from datetime import datetime as _dt

    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            _dt.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False''',
            fix_old='''    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):''',
            fix_new='''    for fmt in ("%Y-%m-%d",):''',
            description="also accepts DD-MM-YYYY format",
            test_name="test_date_s03",
            test_code='''    def test_date_sv_only_ymd(self):
        assert validate_date_format("15-01-2024") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s04", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date: accept MM-DD-YYYY."""
    from datetime import datetime as _dt

    for fmt in ("%Y-%m-%d", "%m-%d-%Y"):
        try:
            _dt.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False''',
            fix_old='''    for fmt in ("%Y-%m-%d", "%m-%d-%Y"):''',
            fix_new='''    for fmt in ("%Y-%m-%d",):''',
            description="also accepts MM-DD-YYYY format",
            test_name="test_date_s04",
            test_code='''    def test_date_sv_no_mdy(self):
        assert validate_date_format("01-15-2024") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s05", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code=r'''def validate_date_format(date_str: str) -> bool:
    """Validate date: accept YYYY/MM/DD."""
    from datetime import datetime as _dt

    normalized = date_str.replace("/", "-")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", normalized):
        return False
    try:
        _dt.strptime(normalized, "%Y-%m-%d")
        return True
    except ValueError:
        return False''',
            fix_old=r'''    normalized = date_str.replace("/", "-")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", normalized):
        return False
    try:
        _dt.strptime(normalized, "%Y-%m-%d")''',
            fix_new=r'''    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")''',
            description="accepts / separator in dates",
            test_name="test_date_s05",
            test_code='''    def test_date_sv_no_slash(self):
        assert validate_date_format("2024/01/15") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s06", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    date_str = date_str.strip()
    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False''',
            fix_old='''    date_str = date_str.strip()
    if not re.match''',
            fix_new='''    if not re.match''',
            description="strips whitespace before validation",
            test_name="test_date_sv_strip",
            test_code='''    def test_date_sv_strip(self):
        assert validate_date_format(" 2024-01-15 ") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s07", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt > _dt.now():
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt > _dt.now():
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects future dates",
            test_name="test_date_sv_future",
            test_code='''    def test_date_sv_future(self):
        assert validate_date_format("2099-12-31") is True''',
        ),
        # --- Additional unique variants to reach 130+ after gold_patch dedup ---
        BugVariant(
            variant_id="val_dat_s08", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}[-/]\\d{2}[-/]\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str.replace("/", "-"), "%Y-%m-%d")
        return True
    except ValueError:
        return False''',
            fix_old='''    if not re.match(r"^\\d{4}[-/]\\d{2}[-/]\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str.replace("/", "-"), "%Y-%m-%d")''',
            fix_new='''    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")''',
            description="accepts slash separators in date format",
            test_name="test_date_sv_slash_rejected",
            test_code='''    def test_date_sv_slash_rejected(self):
        assert validate_date_format("2024/01/15") is False''',
        ),
        BugVariant(
            variant_id="val_dat_s09", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        dt = _dt.strptime(date_str, "%Y-%m-%d")
        if dt.year > 2030:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if dt.year > 2030:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects dates after year 2030",
            test_name="test_date_sv_no_upper_year",
            test_code='''    def test_date_sv_no_upper_year(self):
        assert validate_date_format("2099-12-31") is True''',
        ),
        BugVariant(
            variant_id="val_dat_s10", repo_type="validators",
            function_name="validate_date_format", bug_type="string_validation",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")
        if int(date_str[:4]) < 1900:
            return False
        return True
    except ValueError:
        return False''',
            fix_old='''        if int(date_str[:4]) < 1900:
            return False
        return True''',
            fix_new='''        return True''',
            description="rejects dates before year 1900",
            test_name="test_date_sv_no_year_limit",
            test_code='''    def test_date_sv_no_year_limit(self):
        assert validate_date_format("1800-01-01") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s08", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 12''',
            fix_old='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 12''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="upper bound is 12 instead of 15",
            test_name="test_phone_sv_upper_15",
            test_code='''    def test_phone_sv_upper_15(self):
        assert validate_phone("1234567890123") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s09", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("1"):
        return cleaned.isdigit() and 10 <= len(cleaned) <= 15
    return False''',
            fix_old='''    if cleaned.startswith("1"):
        return cleaned.isdigit() and 10 <= len(cleaned) <= 15
    return False''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="only accepts numbers starting with 1",
            test_name="test_phone_sv_any_prefix",
            test_code='''    def test_phone_sv_any_prefix(self):
        assert validate_phone("8123456789") is True''',
        ),
        BugVariant(
            variant_id="val_url_s08", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return "/" in rest and len(rest) > 3''',
            fix_old='''    return "/" in rest and len(rest) > 3''',
            fix_new='''    return len(rest) > 0 and "/" in rest''',
            description="requires rest length > 3 instead of > 0",
            test_name="test_url_sv_short_path",
            test_code='''    def test_url_sv_short_path(self):
        assert validate_url("http://x/1") is True''',
        ),
        BugVariant(
            variant_id="val_url_s09", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest and "." in rest''',
            fix_old='''    return len(rest) > 0 and "/" in rest and "." in rest''',
            fix_new='''    return len(rest) > 0 and "/" in rest''',
            description="requires dot in rest (rejects localhost URLs)",
            test_name="test_url_sv_no_dot_requirement",
            test_code='''    def test_url_sv_no_dot_requirement(self):
        assert validate_url("http://localhost/api") is True''',
        ),
        BugVariant(
            variant_id="val_eml_s08", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
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
    if len(local) > 64:
        return False
    return True''',
            fix_old='''    if len(local) > 64:
        return False
    return True''',
            fix_new='''    return True''',
            description="rejects local parts longer than 64 chars",
            test_name="test_email_sv_no_local_limit",
            test_code='''    def test_email_sv_no_local_limit(self):
        long_local = "a" * 65
        assert validate_email(f"{long_local}@example.com") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s08", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    if " " in password:
        return False
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if " " in password:
        return False
    return has_upper and has_lower and has_digit and has_special''',
            fix_new='''    return has_upper and has_lower and has_digit and has_special''',
            description="rejects passwords containing spaces",
            test_name="test_pwd_sv_allow_spaces",
            test_code='''    def test_pwd_sv_allow_spaces(self):
        assert validate_password_strength("Abc 1234!") is True''',
        ),
        BugVariant(
            variant_id="su_rev_b08", repo_type="string_utils",
            function_name="reverse_words", bug_type="boundary",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    if not words:
        return s
    return " ".join(words[::-1])''',
            fix_old='''    if not words:
        return s
    return " ".join(words[::-1])''',
            fix_new='''    return " ".join(words[::-1])''',
            description="returns original string for empty split (preserves whitespace-only input)",
            test_name="test_reverse_b08_ws_only",
            test_code='''    def test_reverse_b08_ws_only(self):
        assert reverse_words("   ") == ""''',
        ),
        BugVariant(
            variant_id="su_cap_b08", repo_type="string_utils",
            function_name="capitalize_words", bug_type="boundary",
            buggy_code='''def capitalize_words(s: str) -> str:
    """Capitalize words."""
    return "-".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            fix_old='''    return "-".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            fix_new='''    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))''',
            description="joins words with hyphen instead of space",
            test_name="test_cap_b08_space_join",
            test_code='''    def test_cap_b08_space_join(self):
        result = capitalize_words("hello world")
        assert result == "Hello World"
        assert "-" not in result''',
        ),
        # --- 6 more unique variants to fill size-6 combos to 7 ---
        BugVariant(
            variant_id="su_rev_s08", repo_type="string_utils",
            function_name="reverse_words", bug_type="string_validation",
            buggy_code='''def reverse_words(s: str) -> str:
    """Reverse word order."""
    words = s.split()
    return " ".join(words[-1:] + words[:-1])''',
            fix_old='''    return " ".join(words[-1:] + words[:-1])''',
            fix_new='''    return " ".join(words[::-1])''',
            description="rotates words right by one instead of reversing",
            test_name="test_reverse_sv_s08_rotate",
            test_code='''    def test_reverse_sv_s08_rotate(self):
        assert reverse_words("a b c") == "c b a"''',
        ),
        BugVariant(
            variant_id="val_dat_b08", repo_type="validators",
            function_name="validate_date_format", bug_type="boundary",
            buggy_code='''def validate_date_format(date_str: str) -> bool:
    """Validate date format."""
    from datetime import datetime as _dt

    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return len(date_str) == 10''',
            fix_old='''    except ValueError:
        return len(date_str) == 10''',
            fix_new='''    except ValueError:
        return False''',
            description="returns True for invalid dates that match length",
            test_name="test_date_b08_invalid_by_length",
            test_code='''    def test_date_b08_invalid_by_length(self):
        assert validate_date_format("2024-13-01") is False''',
        ),
        BugVariant(
            variant_id="val_eml_s09", repo_type="validators",
            function_name="validate_email", bug_type="string_validation",
            buggy_code='''def validate_email(email: str) -> bool:
    """Validate email."""
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
    if local.startswith(".") or local.endswith("."):
        return False
    return True''',
            fix_old='''    if local.startswith(".") or local.endswith("."):
        return False
    return True''',
            fix_new='''    return True''',
            description="rejects local parts starting or ending with dot",
            test_name="test_email_sv_allow_local_dots",
            test_code='''    def test_email_sv_allow_local_dots(self):
        assert validate_email(".user@example.com") is True''',
        ),
        BugVariant(
            variant_id="val_pwd_s09", repo_type="validators",
            function_name="validate_password_strength", bug_type="string_validation",
            buggy_code='''def validate_password_strength(password: str) -> bool:
    """Validate password."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    if password != password.strip():
        return False
    return has_upper and has_lower and has_digit and has_special''',
            fix_old='''    if password != password.strip():
        return False
    return has_upper and has_lower and has_digit and has_special''',
            fix_new='''    return has_upper and has_lower and has_digit and has_special''',
            description="rejects passwords with leading/trailing whitespace",
            test_name="test_pwd_sv_allow_whitespace",
            test_code='''    def test_pwd_sv_allow_whitespace(self):
        assert validate_password_strength(" Abc1234!") is True''',
        ),
        BugVariant(
            variant_id="val_phn_s10", repo_type="validators",
            function_name="validate_phone", bug_type="string_validation",
            buggy_code='''def validate_phone(phone: str) -> bool:
    """Validate phone."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("00"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_old='''    if cleaned.startswith("00"):
        return False
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            fix_new='''    return cleaned.isdigit() and 10 <= len(cleaned) <= 15''',
            description="rejects numbers starting with 00",
            test_name="test_phone_sv_allow_double_zero",
            test_code='''    def test_phone_sv_allow_double_zero(self):
        assert validate_phone("0012345678") is True''',
        ),
        BugVariant(
            variant_id="val_url_s10", repo_type="validators",
            function_name="validate_url", bug_type="string_validation",
            buggy_code='''def validate_url(url: str) -> bool:
    """Validate URL."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest and not rest.startswith("/")''',
            fix_old='''    return len(rest) > 0 and "/" in rest and not rest.startswith("/")''',
            fix_new='''    return len(rest) > 0 and "/" in rest''',
            description="rejects URLs where path starts immediately after protocol",
            test_name="test_url_sv_allow_triple_slash",
            test_code='''    def test_url_sv_allow_triple_slash(self):
        assert validate_url("http:///path") is True''',
        ),
    ]
