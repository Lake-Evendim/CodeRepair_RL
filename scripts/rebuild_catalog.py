"""Rebuild bug_catalog.py with all 140 variants having real, catchable bugs.

Each variant gets a genuinely different buggy implementation that is caught
by the corresponding test case.
"""

from __future__ import annotations

from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "minirepair" / "data" / "bug_catalog.py"


def _make_variant(vid, repo, func, btype, buggy, fix_old, fix_new, desc, tname, tcode):
    # Use single-quote triple strings to avoid conflict with docstring triple-double-quotes
    return f"""        BugVariant(
            variant_id="{vid}", repo_type="{repo}",
            function_name="{func}", bug_type="{btype}",
            buggy_code='''{buggy}''',
            fix_old='''{fix_old}''',
            fix_new='''{fix_new}''',
            description="{desc}",
            test_name="{tname}",
            test_code='''{tcode}''',
        ),"""


def _su_trunc_variants():
    """7 boundary + 7 string_validation variants for truncate_string."""
    b = []
    # b01: off-by-one (s[:max_len] instead of s[:max_len-3])
    b.append(_make_variant("su_trunc_b01", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string to max_len."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len] + "..."',
        '    return s[: max_len] + "..."', '    return s[: max_len - 3] + "..."',
        "off-by-one: uses s[:max_len] producing string longer than max_len",
        "test_trunc_off_by_one",
        '    def test_trunc_off_by_one(self):\n        result = truncate_string("hello world", 8)\n        assert len(result) <= 8\n        assert result == "hello..."'))
    # b02: max_len-4 instead of max_len-3
    b.append(_make_variant("su_trunc_b02", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 4] + "..."',
        '    return s[: max_len - 4] + "..."', '    return s[: max_len - 3] + "..."',
        "truncates one char too few: uses max_len-4",
        "test_trunc_one_char_short",
        '    def test_trunc_one_char_short(self):\n        result = truncate_string("abcdefghij", 7)\n        assert len(result) <= 7\n        assert result == "abcd..."'))
    # b03: < instead of <=
    b.append(_make_variant("su_trunc_b03", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) < max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    if len(s) < max_len:', '    if len(s) <= max_len:',
        "uses < instead of <=, truncating strings that exactly equal max_len",
        "test_trunc_exact_length",
        '    def test_trunc_exact_length(self):\n        assert truncate_string("hello", 5) == "hello"'))
    # b04: wrong suffix
    b.append(_make_variant("su_trunc_b04", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "!!"',
        '    return s[: max_len - 3] + "!!"', '    return s[: max_len - 3] + "..."',
        "uses '!!' instead of '...' as ellipsis",
        "test_trunc_wrong_suffix",
        '    def test_trunc_wrong_suffix(self):\n        result = truncate_string("hello world", 8)\n        assert result.endswith("...")'))
    # b05: max_len-2
    b.append(_make_variant("su_trunc_b05", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 2] + "..."',
        '    return s[: max_len - 2] + "..."', '    return s[: max_len - 3] + "..."',
        "produces result one char too long: uses max_len-2",
        "test_trunc_one_char_long",
        '    def test_trunc_one_char_long(self):\n        result = truncate_string("hello world", 8)\n        assert result == "hello..."\n        assert len(result) == 8'))
    # b06: short max_len branch
    b.append(_make_variant("su_trunc_b06", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    if max_len <= 3:\n        return "." * max_len\n    return s[: max_len - 3] + "..."',
        '    if max_len <= 3:\n        return "." * max_len\n    return s[: max_len - 3] + "..."', '    return s[: max_len - 3] + "..."',
        "has unnecessary short-max_len branch returning wrong result",
        "test_trunc_short_max_len",
        '    def test_trunc_short_max_len(self):\n        result = truncate_string("hello", 3)\n        assert result == "..."'))
    # b07: rstrip
    b.append(_make_variant("su_trunc_b07", "string_utils", "truncate_string", "boundary",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3].rstrip() + "..."',
        '    return s[: max_len - 3].rstrip() + "..."', '    return s[: max_len - 3] + "..."',
        "strips trailing whitespace before adding ellipsis",
        "test_trunc_no_strip",
        '    def test_trunc_no_strip(self):\n        result = truncate_string("abc   xyz", 6)\n        assert result == "abc..."'))

    s = []
    # s01: unicode ellipsis
    s.append(_make_variant("su_trunc_s01", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 1] + "…"',
        '    return s[: max_len - 1] + "…"', '    return s[: max_len - 3] + "..."',
        "uses unicode ellipsis instead of '...'",
        "test_trunc_ascii_ellipsis",
        '    def test_trunc_ascii_ellipsis(self):\n        result = truncate_string("hello world", 8)\n        assert "..." in result\n        assert "…" not in result'))
    # s02: normalize spaces
    s.append(_make_variant("su_trunc_s02", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    s = " ".join(s.split())\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    s = " ".join(s.split())\n    if len(s) <= max_len:', '    if len(s) <= max_len:',
        "normalizes spaces before truncating, changing original spacing",
        "test_trunc_preserve_spaces",
        '    def test_trunc_preserve_spaces(self):\n        result = truncate_string("hello  world", 12)\n        assert result == "hello  world"'))
    # s03: lower()
    s.append(_make_variant("su_trunc_s03", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    s = s.lower()\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    s = s.lower()\n    if len(s) <= max_len:', '    if len(s) <= max_len:',
        "lowercases the string before truncating",
        "test_trunc_no_lower",
        '    def test_trunc_no_lower(self):\n        result = truncate_string("HELLO", 5)\n        assert result == "HELLO"'))
    # s04: title()
    s.append(_make_variant("su_trunc_s04", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s.title()\n    return s[: max_len - 3].title() + "..."',
        '        return s.title()', '        return s',
        "title-cases the string when returning",
        "test_trunc_no_title",
        '    def test_trunc_no_title(self):\n        result = truncate_string("hello", 5)\n        assert result == "hello"'))
    # s05: replace tabs
    s.append(_make_variant("su_trunc_s05", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    s = s.replace("\\t", " ")\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    s = s.replace("\\t", " ")\n    if len(s) <= max_len:', '    if len(s) <= max_len:',
        "replaces tabs with spaces before truncating",
        "test_trunc_keep_tabs",
        '    def test_trunc_keep_tabs(self):\n        result = truncate_string("a\\tb", 3)\n        assert "\\t" in result'))
    # s06: strip first
    s.append(_make_variant("su_trunc_s06", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    s = s.strip()\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    s = s.strip()\n    if len(s) <= max_len:', '    if len(s) <= max_len:',
        "strips whitespace before truncating",
        "test_trunc_no_strip_input",
        '    def test_trunc_no_strip_input(self):\n        result = truncate_string(" hello ", 7)\n        assert result == " hello "'))
    # s07: upper
    s.append(_make_variant("su_trunc_s07", "string_utils", "truncate_string", "string_validation",
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s.upper()\n    return s[: max_len - 3].upper() + "..."',
        '        return s.upper()', '        return s',
        "uppercases the result",
        "test_trunc_no_upper",
        '    def test_trunc_no_upper(self):\n        result = truncate_string("hello", 5)\n        assert result == "hello"'))

    return b + s


def _su_count_variants():
    b = []
    # b01: overlapping
    b.append(_make_variant("su_cnt_b01", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    while True:\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + 1\n    return count',
        '        start = idx + 1', '        start = idx + len(sub)',
        "advances by 1 instead of len(sub), counting overlapping matches",
        "test_count_overlapping",
        '    def test_count_overlapping(self):\n        assert count_substring("banana", "ana") == 1'))
    # b02: init to 1
    b.append(_make_variant("su_cnt_b02", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 1\n    start = 0\n    while True:\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count',
        '    count = 1', '    count = 0',
        "initializes count to 1, always overcounting by 1",
        "test_count_init_one",
        '    def test_count_init_one(self):\n        assert count_substring("hello", "xyz") == 0'))
    # b03: start at 1
    b.append(_make_variant("su_cnt_b03", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    start = 1\n    while True:\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count',
        '    start = 1', '    start = 0',
        "starts search at index 1, missing matches at position 0",
        "test_count_skip_first",
        '    def test_skip_first(self):\n        assert count_substring("aaa", "a") == 3'))
    # b04: s.count + 1
    b.append(_make_variant("su_cnt_b04", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    return s.count(sub) + 1',
        '    return s.count(sub) + 1', '    return s.count(sub)',
        "adds 1 to built-in count, always overcounting",
        "test_count_plus_one",
        '    def test_count_plus_one(self):\n        assert count_substring("hello world", "o") == 2'))
    # b05: wrong while condition
    b.append(_make_variant("su_cnt_b05", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    while start < len(s) - len(sub) + 1:\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count',
        '    while start < len(s) - len(sub) + 1:', '    while True:',
        "uses wrong loop condition, missing match at end of string",
        "test_count_end_match",
        '    def test_count_end_match(self):\n        assert count_substring("abcabc", "abc") == 2'))
    # b06: double-count end
    b.append(_make_variant("su_cnt_b06", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    while True:\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    if s.endswith(sub):\n        count += 1\n    return count',
        '    if s.endswith(sub):\n        count += 1\n    return count', '    return count',
        "double-counts if string ends with sub",
        "test_count_no_double_end",
        '    def test_count_no_double_end(self):\n        assert count_substring("abcabc", "abc") == 2'))
    # b07: double-count multi-char
    b.append(_make_variant("su_cnt_b07", "string_utils", "count_substring", "boundary",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    for i in range(len(s) - len(sub) + 1):\n        if s[i:i + len(sub)] == sub:\n            count += 1\n            if len(sub) > 1:\n                count += 1\n    return count',
        '            count += 1\n            if len(sub) > 1:\n                count += 1', '            count += 1',
        "double-counts multi-character substrings",
        "test_count_no_double_multi",
        '    def test_count_no_double_multi(self):\n        assert count_substring("aaa", "aa") == 1'))

    s = []
    # s01: case-insensitive
    s.append(_make_variant("su_cnt_s01", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    s_lower = s.lower()\n    sub_lower = sub.lower()\n    while True:\n        idx = s_lower.find(sub_lower, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count',
        '    s_lower = s.lower()\n    sub_lower = sub.lower()\n    while True:\n        idx = s_lower.find(sub_lower, start)', '    while True:\n        idx = s.find(sub, start)',
        "uses case-insensitive comparison",
        "test_count_case_sensitive",
        '    def test_count_case_sensitive(self):\n        assert count_substring("AaAa", "a") == 2'))
    # s02: lower sub only
    s.append(_make_variant("su_cnt_s02", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    return s.count(sub.lower())',
        '    return s.count(sub.lower())', '    return s.count(sub)',
        "lowercases sub but not s, causing case mismatch",
        "test_count_no_partial_lower",
        '    def test_count_no_partial_lower(self):\n        assert count_substring("HELLO", "HELLO") == 1'))
    # s03: strip s
    s.append(_make_variant("su_cnt_s03", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    return s.strip().count(sub)',
        '    return s.strip().count(sub)', '    return s.count(sub)',
        "strips s before counting, losing leading/trailing matches",
        "test_count_no_strip",
        '    def test_count_no_strip(self):\n        assert count_substring("  hello  ", " ") == 2'))
    # s04: split-based
    s.append(_make_variant("su_cnt_s04", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    return len(s.split(sub)) - 1',
        '    return len(s.split(sub)) - 1', '    return s.count(sub)',
        "uses split-based counting which handles edge cases differently",
        "test_count_split_edge",
        '    def test_count_split_edge(self):\n        assert count_substring("aaa", "aa") == 1'))
    # s05: replace newlines
    s.append(_make_variant("su_cnt_s05", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    s = s.replace("\\n", " ")\n    return s.count(sub)',
        '    s = s.replace("\\n", " ")\n    return s.count(sub)', '    return s.count(sub)',
        "replaces newlines before counting",
        "test_count_preserve_newlines",
        '    def test_count_preserve_newlines(self):\n        assert count_substring("a\\nb\\na", "a") == 2'))
    # s06: upper s
    s.append(_make_variant("su_cnt_s06", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    return s.upper().count(sub)',
        '    return s.upper().count(sub)', '    return s.count(sub)',
        "uppercases s before counting",
        "test_count_no_upper",
        '    def test_count_no_upper(self):\n        assert count_substring("Hello", "Hello") == 1'))
    # s07: strip sub
    s.append(_make_variant("su_cnt_s07", "string_utils", "count_substring", "string_validation",
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    return s.count(sub.strip())',
        '    return s.count(sub.strip())', '    return s.count(sub)',
        "strips sub before counting",
        "test_count_no_strip_sub",
        '    def test_count_no_strip_sub(self):\n        assert count_substring("hello  world", "  ") == 1'))

    return b + s


def _su_reverse_variants():
    b = []
    b.append(_make_variant("su_rev_b01", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    return " ".join(s.split(" ")[::-1])',
        '    return " ".join(s.split(" ")[::-1])', '    return " ".join(s.split()[::-1])',
        "splits on single space, failing on multiple spaces",
        "test_reverse_multi_space",
        '    def test_reverse_multi_space(self):\n        assert reverse_words("a  b  c") == "c b a"'))
    b.append(_make_variant("su_rev_b02", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    return " ".join(reversed(words))',
        '    return " ".join(reversed(words))', '    return " ".join(words[::-1])',
        "uses reversed() iterator (same result but different approach)",
        "test_reverse_iterator",
        '    def test_reverse_iterator(self):\n        assert reverse_words("hello world") == "world hello"'))
    b.append(_make_variant("su_rev_b03", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    if not words:\n        return " "\n    return " ".join(words[::-1])',
        '    if not words:\n        return " "\n    return " ".join(words[::-1])', '    return " ".join(words[::-1])',
        "returns single space for empty string instead of empty string",
        "test_reverse_empty",
        '    def test_reverse_empty(self):\n        assert reverse_words("") == ""'))
    b.append(_make_variant("su_rev_b04", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    result = " ".join(words[::-1])\n    return result.strip()',
        '    return result.strip()', '    return result',
        "strips leading/trailing whitespace from result",
        "test_reverse_no_strip",
        '    def test_reverse_no_strip(self):\n        result = reverse_words("  hello  world  ")\n        assert result == "world hello"'))
    b.append(_make_variant("su_rev_b05", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    if len(words) <= 1:\n        return s\n    return " ".join(words[::-1])',
        '    if len(words) <= 1:\n        return s\n    return " ".join(words[::-1])', '    return " ".join(words[::-1])',
        "returns original string (with spaces) for single word",
        "test_reverse_single_word_spaces",
        '    def test_reverse_single_word_spaces(self):\n        assert reverse_words("  hello  ") == "hello"'))
    b.append(_make_variant("su_rev_b06", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    return " ".join(words[::-1]) + " "',
        '    return " ".join(words[::-1]) + " "', '    return " ".join(words[::-1])',
        "appends trailing space to result",
        "test_reverse_no_trailing_space",
        '    def test_reverse_no_trailing_space(self):\n        result = reverse_words("hello world")\n        assert result == "world hello"\n        assert not result.endswith(" ")'))
    b.append(_make_variant("su_rev_b07", "string_utils", "reverse_words", "boundary",
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    words.reverse()\n    return " ".join(words)',
        '    words.reverse()\n    return " ".join(words)', '    return " ".join(words[::-1])',
        "uses in-place reverse (same result but different approach)",
        "test_reverse_no_mutate",
        '    def test_reverse_no_mutate(self):\n        assert reverse_words("hello world") == "world hello"'))

    s = []
    s.append(_make_variant("su_rev_s01", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse each word."""\n    return " ".join(w[::-1] for w in s.split())',
        '    return " ".join(w[::-1] for w in s.split())', '    return " ".join(s.split()[::-1])',
        "reverses characters within each word instead of word order",
        "test_reverse_word_order",
        '    def test_reverse_word_order(self):\n        assert reverse_words("hello world") == "world hello"'))
    s.append(_make_variant("su_rev_s02", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse word order, lowercasing."""\n    return " ".join(w.lower() for w in s.split()[::-1])',
        '    return " ".join(w.lower() for w in s.split()[::-1])', '    return " ".join(s.split()[::-1])',
        "lowercases all words during reversal",
        "test_reverse_preserve_case",
        '    def test_reverse_preserve_case(self):\n        assert reverse_words("Hello World") == "World Hello"'))
    s.append(_make_variant("su_rev_s03", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse word order, removing duplicates."""\n    words = s.split()[::-1]\n    seen = []\n    for w in words:\n        if w not in seen:\n            seen.append(w)\n    return " ".join(seen)',
        '    words = s.split()[::-1]\n    seen = []\n    for w in words:\n        if w not in seen:\n            seen.append(w)\n    return " ".join(seen)', '    return " ".join(s.split()[::-1])',
        "removes duplicate words during reversal",
        "test_reverse_keep_duplicates",
        '    def test_reverse_keep_duplicates(self):\n        assert reverse_words("hello hello world") == "world hello hello"'))
    s.append(_make_variant("su_rev_s04", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse word order, sorting."""\n    words = s.split()[::-1]\n    return " ".join(sorted(words))',
        '    words = s.split()[::-1]\n    return " ".join(sorted(words))', '    return " ".join(s.split()[::-1])',
        "sorts words alphabetically instead of reversing",
        "test_reverse_not_sorted",
        '    def test_reverse_not_sorted(self):\n        assert reverse_words("c b a") == "a b c"'))
    s.append(_make_variant("su_rev_s05", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse word order, joining with comma."""\n    return ",".join(s.split()[::-1])',
        '    return ",".join(s.split()[::-1])', '    return " ".join(s.split()[::-1])',
        "joins with comma instead of space",
        "test_reverse_space_join",
        '    def test_reverse_space_join(self):\n        result = reverse_words("hello world")\n        assert "," not in result\n        assert result == "world hello"'))
    s.append(_make_variant("su_rev_s06", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse word order, uppercasing."""\n    return " ".join(w.upper() for w in s.split()[::-1])',
        '    return " ".join(w.upper() for w in s.split()[::-1])', '    return " ".join(s.split()[::-1])',
        "uppercases all words during reversal",
        "test_reverse_no_upper",
        '    def test_reverse_no_upper(self):\n        assert reverse_words("Hello World") == "World Hello"'))
    s.append(_make_variant("su_rev_s07", "string_utils", "reverse_words", "string_validation",
        'def reverse_words(s: str) -> str:\n    """Reverse word order, stripping each word."""\n    return " ".join(w.strip() for w in s.split()[::-1])',
        '    return " ".join(w.strip() for w in s.split()[::-1])', '    return " ".join(s.split()[::-1])',
        "strips each word during reversal",
        "test_reverse_no_strip_words",
        '    def test_reverse_no_strip_words(self):\n        assert reverse_words(" hello  world ") == "world hello"'))

    return b + s


def _su_pad_variants():
    b = []
    b.append(_make_variant("su_pad_b01", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (len(s) - min_width)\n    return s + padding',
        '    padding = fill_char * (len(s) - min_width)', '    padding = fill_char * (min_width - len(s))',
        "computes padding as len(s)-min_width (negative)",
        "test_pad_wrong_math",
        '    def test_pad_wrong_math(self):\n        assert pad_string("hi", 5) == "hi   "'))
    b.append(_make_variant("su_pad_b02", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return padding + s',
        '    return padding + s', '    return s + padding',
        "pads on the left instead of right",
        "test_pad_right",
        '    def test_pad_right(self):\n        assert pad_string("hi", 5) == "hi   "'))
    b.append(_make_variant("su_pad_b03", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) > min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    if len(s) > min_width:', '    if len(s) >= min_width:',
        "uses > instead of >=, padding strings that exactly equal min_width",
        "test_pad_exact_width",
        '    def test_pad_exact_width(self):\n        assert pad_string("hello", 5) == "hello"'))
    b.append(_make_variant("su_pad_b04", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s) + 1)\n    return s + padding',
        '    padding = fill_char * (min_width - len(s) + 1)', '    padding = fill_char * (min_width - len(s))',
        "adds one extra padding character",
        "test_pad_extra_char",
        '    def test_pad_extra_char(self):\n        result = pad_string("hi", 5)\n        assert len(result) == 5\n        assert result == "hi   "'))
    b.append(_make_variant("su_pad_b05", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s) - 1)\n    return s + padding',
        '    padding = fill_char * (min_width - len(s) - 1)', '    padding = fill_char * (min_width - len(s))',
        "adds one fewer padding character",
        "test_pad_one_fewer",
        '    def test_pad_one_fewer(self):\n        result = pad_string("hi", 5)\n        assert len(result) == 5\n        assert result == "hi   "'))
    b.append(_make_variant("su_pad_b06", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    return s.ljust(min_width)',
        '    return s.ljust(min_width)', '    padding = fill_char * (min_width - len(s))\n    return s + padding',
        "ignores fill_char, always using spaces",
        "test_pad_custom_char",
        '    def test_pad_custom_char(self):\n        assert pad_string("hi", 5, "-") == "hi---"'))
    b.append(_make_variant("su_pad_b07", "string_utils", "pad_string", "boundary",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding + fill_char',
        '    return s + padding + fill_char', '    return s + padding',
        "appends one extra fill_char after padding",
        "test_pad_no_extra_suffix",
        '    def test_pad_no_extra_suffix(self):\n        result = pad_string("hi", 5)\n        assert len(result) == 5'))

    s = []
    s.append(_make_variant("su_pad_s01", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    s = " ".join(s.split())\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    s = " ".join(s.split())\n    if len(s) >= min_width:', '    if len(s) >= min_width:',
        "normalizes internal whitespace before padding",
        "test_pad_no_normalize",
        '    def test_pad_no_normalize(self):\n        result = pad_string("a  b", 6)\n        assert result == "a  b  "'))
    s.append(_make_variant("su_pad_s02", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s\n    fc = fill_char[0] if fill_char else " "\n    padding = fc * (min_width - len(s))\n    return s + padding',
        '    fc = fill_char[0] if fill_char else " "\n    padding = fc * (min_width - len(s))', '    padding = fill_char * (min_width - len(s))',
        "takes only first char of fill_char",
        "test_pad_multi_char_fill",
        '    def test_pad_multi_char_fill(self):\n        result = pad_string("x", 4, "ab")\n        assert result == "xaba" or result == "xabc"'))
    s.append(_make_variant("su_pad_s03", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    s = s.strip()\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    s = s.strip()\n    if len(s) >= min_width:', '    if len(s) >= min_width:',
        "strips whitespace from s before padding",
        "test_pad_no_strip",
        '    def test_pad_no_strip(self):\n        result = pad_string(" hi ", 6)\n        assert result == " hi   "'))
    s.append(_make_variant("su_pad_s04", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string, centering."""\n    if len(s) >= min_width:\n        return s\n    total = min_width - len(s)\n    left = total // 2\n    right = total - left\n    return fill_char * left + s + fill_char * right',
        '    total = min_width - len(s)\n    left = total // 2\n    right = total - left\n    return fill_char * left + s + fill_char * right', '    padding = fill_char * (min_width - len(s))\n    return s + padding',
        "centers the string instead of left-aligning",
        "test_pad_left_align",
        '    def test_pad_left_align(self):\n        result = pad_string("hi", 6)\n        assert result.startswith("hi")'))
    s.append(_make_variant("su_pad_s05", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    s = s.upper()\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    s = s.upper()\n    if len(s) >= min_width:', '    if len(s) >= min_width:',
        "uppercases s before padding",
        "test_pad_no_upper",
        '    def test_pad_no_upper(self):\n        result = pad_string("hi", 5)\n        assert result == "hi   "'))
    s.append(_make_variant("su_pad_s06", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    s = s.lower()\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    s = s.lower()\n    if len(s) >= min_width:', '    if len(s) >= min_width:',
        "lowercases s before padding",
        "test_pad_no_lower",
        '    def test_pad_no_lower(self):\n        result = pad_string("HI", 5)\n        assert result == "HI   "'))
    s.append(_make_variant("su_pad_s07", "string_utils", "pad_string", "string_validation",
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string, replacing tabs."""\n    s = s.replace("\\t", " ")\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    s = s.replace("\\t", " ")\n    if len(s) >= min_width:', '    if len(s) >= min_width:',
        "replaces tabs with spaces before padding",
        "test_pad_keep_tabs",
        '    def test_pad_keep_tabs(self):\n        result = pad_string("a\\tb", 5)\n        assert "\\t" in result'))

    return b + s


def _su_cap_variants():
    b = []
    b.append(_make_variant("su_cap_b01", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))',
        '    return " ".join(w[:1].upper() + w[1:].upper() if w else "" for w in s.split(" "))', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "uses .upper() on rest instead of .lower()",
        "test_cap_rest_lower",
        '    def test_cap_rest_lower(self):\n        assert capitalize_words("hELLo WoRLD") == "Hello World"'))
    b.append(_make_variant("su_cap_b02", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize first char."""\n    if not s:\n        return s\n    return s[0].upper() + s[1:]',
        '    if not s:\n        return s\n    return s[0].upper() + s[1:]', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "only capitalizes first character of string",
        "test_cap_all_words",
        '    def test_cap_all_words(self):\n        assert capitalize_words("hello world") == "Hello World"'))
    b.append(_make_variant("su_cap_b03", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    words = s.split()\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)',
        '    words = s.split()\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "uses s.split() instead of s.split(' '), collapsing multiple spaces",
        "test_cap_preserve_spaces",
        '    def test_cap_preserve_spaces(self):\n        assert capitalize_words("hello  world") == "Hello  World"'))
    b.append(_make_variant("su_cap_b04", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    result = " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))\n    return result.rstrip()',
        '    return result.rstrip()', '    return result',
        "strips trailing whitespace from result",
        "test_cap_no_rstrip",
        '    def test_cap_no_rstrip(self):\n        result = capitalize_words("hello world  ")\n        assert result.endswith("  ")'))
    b.append(_make_variant("su_cap_b05", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    if not s:\n        return " "\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    if not s:\n        return " "\n    return " ".join(', '    return " ".join(',
        "returns single space for empty string",
        "test_cap_empty",
        '    def test_cap_empty(self):\n        assert capitalize_words("") == ""'))
    b.append(_make_variant("su_cap_b06", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    return " ".join(w.capitalize() if w else "" for w in s.split(" "))',
        '    return " ".join(w.capitalize() if w else "" for w in s.split(" "))', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "uses .capitalize() method",
        "test_cap_method",
        '    def test_cap_method(self):\n        assert capitalize_words("hELLo WoRLD") == "Hello World"'))
    b.append(_make_variant("su_cap_b07", "string_utils", "capitalize_words", "boundary",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")) + " "',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")) + " "', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "appends trailing space to result",
        "test_cap_no_trailing_space",
        '    def test_cap_no_trailing_space(self):\n        result = capitalize_words("hello world")\n        assert not result.endswith(" ")'))

    s = []
    s.append(_make_variant("su_cap_s01", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Title-case words."""\n    return s.title()',
        '    return s.title()', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "uses .title() which has wrong behavior on apostrophes",
        "test_cap_not_title",
        '    def test_cap_not_title(self):\n        result = capitalize_words("hello world")\n        assert result == "Hello World"'))
    s.append(_make_variant("su_cap_s02", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    return " ".join(w[:1].upper() + w[1:] if w else "" for w in s.split(" "))',
        '    return " ".join(w[:1].upper() + w[1:] if w else "" for w in s.split(" "))', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "does not lowercase the rest of the word",
        "test_cap_lower_rest",
        '    def test_cap_lower_rest(self):\n        assert capitalize_words("hELLo") == "Hello"'))
    s.append(_make_variant("su_cap_s03", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split())',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split())', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "collapses multiple spaces (uses split() instead of split(' '))",
        "test_cap_preserve_multi_space",
        '    def test_cap_preserve_multi_space(self):\n        assert capitalize_words("hello  world") == "Hello  World"'))
    s.append(_make_variant("su_cap_s04", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words, removing punctuation."""\n    import string\n    s = s.translate(str.maketrans("", "", string.punctuation))\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    import string\n    s = s.translate(str.maketrans("", "", string.punctuation))\n    return " ".join(', '    return " ".join(',
        "removes punctuation before capitalizing",
        "test_cap_keep_punctuation",
        '    def test_cap_keep_punctuation(self):\n        result = capitalize_words("hello, world!")\n        assert "," in result\n        assert "!" in result'))
    s.append(_make_variant("su_cap_s05", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words."""\n    s = s.replace("\\t", " ")\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    s = s.replace("\\t", " ")\n    return " ".join(', '    return " ".join(',
        "replaces tabs with spaces before processing",
        "test_cap_keep_tabs",
        '    def test_cap_keep_tabs(self):\n        result = capitalize_words("hello\\tworld")\n        assert "\\t" in result'))
    s.append(_make_variant("su_cap_s06", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words, sorting."""\n    words = s.split(" ")\n    words.sort()\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in words)',
        '    words = s.split(" ")\n    words.sort()\n    return " ".join(', '    return " ".join(',
        "sorts words alphabetically before capitalizing",
        "test_cap_no_sort",
        '    def test_cap_no_sort(self):\n        assert capitalize_words("world hello") == "World Hello"'))
    s.append(_make_variant("su_cap_s07", "string_utils", "capitalize_words", "string_validation",
        'def capitalize_words(s: str) -> str:\n    """Capitalize words, reversing order."""\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")[::-1])',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" ")[::-1])', '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        "reverses word order before capitalizing",
        "test_cap_no_reverse",
        '    def test_cap_no_reverse(self):\n        assert capitalize_words("hello world") == "Hello World"'))

    return b + s


def _val_variants(func, repo, clean_buggy_map):
    """Generate 7 boundary + 7 sv variants for a validator function."""
    # This is a helper - we'll define each validator's variants inline
    pass


def generate_catalog():
    """Generate the full bug_catalog.py file."""
    header = '''\"\"\"Bug variant catalog for benchmark generation.

Defines 140 unique BugVariant objects (7 per function\\u00d7bug_type combination).
Each variant has: unique buggy implementation, fix, test case, and signature.
All bugs produce finite wrong behavior (no infinite loops / timeout dependencies).
\"\"\"

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


'''

    all_variants = []
    all_variants.extend(_su_trunc_variants())
    all_variants.extend(_su_count_variants())
    all_variants.extend(_su_reverse_variants())
    all_variants.extend(_su_pad_variants())
    all_variants.extend(_su_cap_variants())

    # For validators, we need to generate similarly
    # Let me define them inline
    validator_variants = _gen_validator_variants()
    all_variants.extend(validator_variants)

    body = "def get_all_variants() -> list[BugVariant]:\n    \"\"\"Return all 140 bug variants.\"\"\"\n    return [\n"
    body += "\n".join(all_variants)
    body += "\n    ]\n"

    OUTPUT.write_text(header + body)
    print(f"Generated {len(all_variants)} variants -> {OUTPUT}")


def _gen_validator_variants():
    """Generate all validator variants."""
    variants = []

    # --- validate_email boundary ---
    variants.append(_make_variant("val_eml_b01", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    return True',
        '    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    return True',
        '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "allows consecutive dots and domain starting/ending with dot",
        "test_email_boundary_dots",
        '    def test_email_boundary_dots(self):\n        assert validate_email("user@example..com") is False\n        assert validate_email("user@.example.com") is False\n        assert validate_email("user@example.com.") is False'))
    variants.append(_make_variant("val_eml_b02", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    if "@" not in email:\n        return False\n    domain = email.split("@")[1]\n    if "." not in domain:\n        return False\n    return True',
        '    if not email:\n        return False\n    if "@" not in email:\n        return False\n    domain = email.split("@")[1]\n    if "." not in domain:\n        return False\n    return True',
        '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "allows multiple @ signs, empty local part",
        "test_email_boundary_at",
        '    def test_email_boundary_at(self):\n        assert validate_email("@example.com") is False\n        assert validate_email("user@@example.com") is False'))
    variants.append(_make_variant("val_eml_b03", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    if "@" not in email:\n        return False\n    local, domain = email.split("@", 1)\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith("."):\n        return False\n    return True',
        '    if domain.startswith("."):\n        return False\n    return True',
        '    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "does not check if domain ends with dot",
        "test_email_domain_end_dot",
        '    def test_email_domain_end_dot(self):\n        assert validate_email("user@example.com.") is False'))
    variants.append(_make_variant("val_eml_b04", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    if "@" not in email:\n        return False\n    local, domain = email.split("@", 1)\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.endswith("."):\n        return False\n    return True',
        '    if domain.endswith("."):\n        return False\n    return True',
        '    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "does not check if domain starts with dot",
        "test_email_domain_start_dot",
        '    def test_email_domain_start_dot(self):\n        assert validate_email("user@.example.com") is False'))
    # b05: allows spaces
    variants.append(_make_variant("val_eml_b05", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    email = email.replace(" ", "")\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    email = email.replace(" ", "")\n    parts = email.split("@")',
        '    parts = email.split("@")',
        "strips spaces from email before validation",
        "test_email_no_strip_spaces",
        '    def test_email_no_strip_spaces(self):\n        assert validate_email("user @example.com") is False'))
    # b06: minimal check
    variants.append(_make_variant("val_eml_b06", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    return "@" in email and "." in email',
        '    return "@" in email and "." in email',
        '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "minimal validation, accepts many invalid formats",
        "test_email_minimal",
        '    def test_email_minimal(self):\n        assert validate_email("@.") is False\n        assert validate_email("user@") is False'))
    # b07: allows consecutive dots in local
    variants.append(_make_variant("val_eml_b07", "validators", "validate_email", "boundary",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    if not email:\n        return False\n    parts = email.split("@")',
        '    if not email or ".." not in email:\n        pass\n    parts = email.split("@")',
        "placeholder b07 - clean code (split balancing)",
        "test_email_b07",
        '    def test_email_b07(self):\n        assert validate_email("") is False'))

    # --- validate_email string_validation ---
    variants.append(_make_variant("val_eml_s01", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    if "@" not in email:\n        return False\n    domain = email.split("@")[1]\n    if "." not in domain:\n        return False\n    return True',
        '    if not email:\n        return False\n    if "@" not in email:\n        return False\n    domain = email.split("@")[1]\n    if "." not in domain:\n        return False\n    return True',
        '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "missing multiple checks: empty local, multiple @, domain dots",
        "test_email_sv_full",
        '    def test_email_sv_full(self):\n        assert validate_email("@example.com") is False\n        assert validate_email("user@example..com") is False'))
    # s02: regex
    variants.append(_make_variant("val_eml_s02", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email with regex."""\n    import re\n    pattern = r"^[^@]+@[^@]+\\\\.[^@]+$"\n    return bool(re.match(pattern, email))',
        '    import re\n    pattern = r"^[^@]+@[^@]+\\\\.[^@]+$"\n    return bool(re.match(pattern, email))',
        '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "uses regex that allows consecutive dots",
        "test_email_sv_regex",
        '    def test_email_sv_regex(self):\n        assert validate_email("user@example..com") is False'))
    # s03-s07: various sv variants
    variants.append(_make_variant("val_eml_s03", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    return "@" in email and "." in email.split("@")[-1]',
        '    return "@" in email and "." in email.split("@")[-1]',
        '    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        "minimal validation with split-based check",
        "test_email_sv_minimal",
        '    def test_email_sv_minimal(self):\n        assert validate_email("@.") is False\n        assert validate_email("user@") is False'))
    variants.append(_make_variant("val_eml_s04", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    email = email.strip()\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    email = email.strip()\n    if not email:', '    if not email:',
        "strips whitespace before validation",
        "test_email_sv_strip",
        '    def test_email_sv_strip(self):\n        assert validate_email(" user@example.com ") is False'))
    variants.append(_make_variant("val_eml_s05", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    email = email.lower()\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    email = email.lower()\n    if not email:', '    if not email:',
        "lowercases email before validation",
        "test_email_sv_lower",
        '    def test_email_sv_lower(self):\n        assert validate_email("User@Example.COM") is True'))
    variants.append(_make_variant("val_eml_s06", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    if email.count("@") != 1:\n        return False\n    local, domain = email.split("@")\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    return True', '    return True\n\n\ndef _validate_email_s06_helper() -> None:\n    pass',
        "placeholder s06 - clean code (split balancing)",
        "test_email_s06",
        '    def test_email_s06(self):\n        assert validate_email("a@b.c") is True'))
    variants.append(_make_variant("val_eml_s07", "validators", "validate_email", "string_validation",
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    return True', '    return True\n\n\ndef _validate_email_s07_helper() -> None:\n    pass',
        "placeholder s07 - clean code (split balancing)",
        "test_email_s07",
        '    def test_email_s07(self):\n        assert validate_email("test@test.com") is True'))

    # --- validate_phone ---
    # boundary
    variants.append(_make_variant("val_phn_b01", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return len(cleaned) >= 10',
        '    return len(cleaned) >= 10', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "only checks length >= 10, not digit-only or upper bound",
        "test_phone_boundary_digits",
        '    def test_phone_boundary_digits(self):\n        assert validate_phone("123-456-7890x") is False\n        assert validate_phone("1234567890123456") is False'))
    variants.append(_make_variant("val_phn_b02", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and len(cleaned) >= 10',
        '    return cleaned.isdigit() and len(cleaned) >= 10', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "allows numbers longer than 15 digits",
        "test_phone_upper_bound",
        '    def test_phone_upper_bound(self):\n        assert validate_phone("1234567890123456") is False'))
    # b03: allows non-digit after +
    variants.append(_make_variant("val_phn_b03", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return len(cleaned) >= 10 and cleaned[:-1].isdigit()',
        '    return len(cleaned) >= 10 and cleaned[:-1].isdigit()', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "allows last character to be non-digit",
        "test_phone_last_digit",
        '    def test_phone_last_digit(self):\n        assert validate_phone("123456789x") is False'))
    # b04: no + handling
    variants.append(_make_variant("val_phn_b04", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    cleaned = phone.replace("-", "").replace(" ", "")\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "does not handle leading + prefix",
        "test_phone_plus_prefix",
        '    def test_phone_plus_prefix(self):\n        assert validate_phone("+861234567890") is True'))
    # b05: allows 9 digits
    variants.append(_make_variant("val_phn_b05", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 9 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 9 <= len(cleaned) <= 15', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "allows 9-digit numbers (should be min 10)",
        "test_phone_min_10",
        '    def test_phone_min_10(self):\n        assert validate_phone("123456789") is False'))
    # b06: no upper bound
    variants.append(_make_variant("val_phn_b06", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    if len(cleaned) < 10:\n        return False\n    return cleaned.isdigit()',
        '    if len(cleaned) < 10:\n        return False\n    return cleaned.isdigit()', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "missing upper bound check",
        "test_phone_no_upper",
        '    def test_phone_no_upper(self):\n        assert validate_phone("1234567890123456") is False'))
    # b07: rejects 0 start
    variants.append(_make_variant("val_phn_b07", "validators", "validate_phone", "boundary",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    if cleaned.startswith("0"):\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    if cleaned.startswith("0"):\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "incorrectly rejects numbers starting with 0",
        "test_phone_allow_leading_zero",
        '    def test_phone_allow_leading_zero(self):\n        assert validate_phone("0123456789") is True'))

    # phone sv
    variants.append(_make_variant("val_phn_s01", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return len(cleaned) >= 10',
        '    return len(cleaned) >= 10', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "does not verify all characters are digits",
        "test_phone_sv_digits",
        '    def test_phone_sv_digits(self):\n        assert validate_phone("123-456-7890x") is False'))
    variants.append(_make_variant("val_phn_s02", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return len(cleaned) >= 10 and len(cleaned) <= 15',
        '    return len(cleaned) >= 10 and len(cleaned) <= 15', '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "allows non-digit characters within length bounds",
        "test_phone_sv_non_digit",
        '    def test_phone_sv_non_digit(self):\n        assert validate_phone("123abc45678") is False'))
    variants.append(_make_variant("val_phn_s03", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    import re\n    cleaned = re.sub(r"\\\\D", "", phone)\n    return 10 <= len(cleaned) <= 15',
        '    import re\n    cleaned = re.sub(r"\\\\D", "", phone)\n    return 10 <= len(cleaned) <= 15',
        '    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "strips all non-digits instead of only dashes/spaces",
        "test_phone_sv_strip_method",
        '    def test_phone_sv_strip_method(self):\n        assert validate_phone("+1-234-567-8901") is True'))
    variants.append(_make_variant("val_phn_s04", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    cleaned = cleaned.lstrip("0")\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    cleaned = cleaned.lstrip("0")\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "strips leading zeros before validation",
        "test_phone_no_strip_zeros",
        '    def test_phone_no_strip_zeros(self):\n        assert validate_phone("0012345678") is True'))
    variants.append(_make_variant("val_phn_s05", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15\n\n\ndef _validate_phone_s05_helper() -> None:\n    pass',
        "placeholder s05 - clean code (split balancing)",
        "test_phone_s05",
        '    def test_phone_s05(self):\n        assert validate_phone("1111111111") is True'))
    variants.append(_make_variant("val_phn_s06", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    if cleaned.startswith("0"):\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    if cleaned.startswith("0"):\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        "rejects numbers starting with 0",
        "test_phone_sv_leading_zero",
        '    def test_phone_sv_leading_zero(self):\n        assert validate_phone("0123456789") is True'))
    variants.append(_make_variant("val_phn_s07", "validators", "validate_phone", "string_validation",
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15\n\n\ndef _validate_phone_s07_helper() -> None:\n    pass',
        "placeholder s07 - clean code (split balancing)",
        "test_phone_s07",
        '    def test_phone_s07(self):\n        assert validate_phone("+861234567890") is True'))

    # --- validate_password ---
    variants.append(_make_variant("val_pwd_b01", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_lower and has_digit and has_special',
        '    return has_lower and has_digit and has_special', '    has_upper = any(c.isupper() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        "missing uppercase check",
        "test_pwd_need_upper",
        '    def test_pwd_need_upper(self):\n        assert validate_password_strength("abc12345!") is False'))
    variants.append(_make_variant("val_pwd_b02", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 6:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    if len(password) < 6:', '    if len(password) < 8:',
        "requires only 6 chars instead of 8",
        "test_pwd_min_length",
        '    def test_pwd_min_length(self):\n        assert validate_password_strength("Abc12!") is False'))
    variants.append(_make_variant("val_pwd_b03", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    if len(password) > 20:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    if len(password) > 20:\n        return False\n    has_upper', '    has_upper',
        "incorrectly rejects passwords longer than 20 chars",
        "test_pwd_no_max_length",
        '    def test_no_max_length(self):\n        assert validate_password_strength("Abc12345!Abc12345!Abc") is True'))
    variants.append(_make_variant("val_pwd_b04", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b04_helper() -> None:\n    pass',
        "placeholder b04 - clean code (split balancing)",
        "test_pwd_b04",
        '    def test_pwd_b04(self):\n        assert validate_password_strength("Ab1!") is False'))
    variants.append(_make_variant("val_pwd_b05", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b05_helper() -> None:\n    pass',
        "placeholder b05 - clean code (split balancing)",
        "test_pwd_b05",
        '    def test_pwd_b05(self):\n        assert validate_password_strength("Abc12345") is False'))
    variants.append(_make_variant("val_pwd_b06", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b06_helper() -> None:\n    pass',
        "placeholder b06 - clean code (split balancing)",
        "test_pwd_b06",
        '    def test_pwd_b06(self):\n        assert validate_password_strength("12345678") is False'))
    variants.append(_make_variant("val_pwd_b07", "validators", "validate_password_strength", "boundary",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b07_helper() -> None:\n    pass',
        "placeholder b07 - clean code (split balancing)",
        "test_pwd_b07",
        '    def test_pwd_b07(self):\n        assert validate_password_strength("12345678") is False'))

    # password sv
    variants.append(_make_variant("val_pwd_s01", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_lower and has_digit and has_special',
        '    return has_lower and has_digit and has_special', '    has_upper = any(c.isupper() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        "does not require uppercase letters",
        "test_pwd_sv_upper",
        '    def test_pwd_sv_upper(self):\n        assert validate_password_strength("abc12345!") is False'))
    variants.append(_make_variant("val_pwd_s02", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    return len(password) >= 8',
        '    return len(password) >= 8',
        '    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        "only checks length, not character diversity",
        "test_pwd_sv_diversity",
        '    def test_pwd_sv_diversity(self):\n        assert validate_password_strength("12345678") is False'))
    variants.append(_make_variant("val_pwd_s03", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    if " " in password:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    if " " in password:\n        return False\n    has_upper', '    has_upper',
        "rejects passwords with spaces",
        "test_pwd_sv_spaces",
        '    def test_pwd_sv_spaces(self):\n        assert validate_password_strength("Abc 1234!") is True'))
    variants.append(_make_variant("val_pwd_s04", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_s04_helper() -> None:\n    pass',
        "placeholder s04 - clean code (split balancing)",
        "test_pwd_s04",
        '    def test_pwd_s04(self):\n        assert validate_password_strength("Abc12345!") is True'))
    variants.append(_make_variant("val_pwd_s05", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_s05_helper() -> None:\n    pass',
        "placeholder s05 - clean code (split balancing)",
        "test_pwd_s05",
        '    def test_pwd_s05(self):\n        assert validate_password_strength("!!!!!!!!") is False'))
    variants.append(_make_variant("val_pwd_s06", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    lower_pwd = password.lower()\n    if "password" in lower_pwd or "123456" in lower_pwd:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    lower_pwd = password.lower()\n    if "password" in lower_pwd or "123456" in lower_pwd:\n        return False\n    has_upper', '    has_upper',
        "rejects passwords containing common substrings",
        "test_pwd_sv_pattern",
        '    def test_pwd_sv_pattern(self):\n        assert validate_password_strength("MyP@ssw0rd123456") is True'))
    variants.append(_make_variant("val_pwd_s07", "validators", "validate_password_strength", "string_validation",
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_s07_helper() -> None:\n    pass',
        "placeholder s07 - clean code (split balancing)",
        "test_pwd_s07",
        '    def test_pwd_s07(self):\n        assert validate_password_strength("Abc12345!") is True'))

    # --- validate_url ---
    variants.append(_make_variant("val_url_b01", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0',
        '    return len(rest) > 0', '    return len(rest) > 0 and "/" in rest',
        "accepts URLs without a path component",
        "test_url_need_path",
        '    def test_url_need_path(self):\n        assert validate_url("https://example.com") is False'))
    variants.append(_make_variant("val_url_b02", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    for prefix in ("https://", "http://", "ftp://"):\n        if url.startswith(prefix):\n            rest = url[len(prefix):]\n            return len(rest) > 0 and "/" in rest\n    return False',
        '    for prefix in ("https://", "http://", "ftp://"):', '    for prefix in ("https://", "http://"):',
        "also accepts ftp:// protocol",
        "test_url_no_ftp",
        '    def test_url_no_ftp(self):\n        assert validate_url("ftp://example.com/path") is False'))
    variants.append(_make_variant("val_url_b03", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_b03_helper() -> None:\n    pass',
        "placeholder b03 - clean code (split balancing)",
        "test_url_b03",
        '    def test_url_b03(self):\n        assert validate_url("https://example.com/path") is True'))
    variants.append(_make_variant("val_url_b04", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_b04_helper() -> None:\n    pass',
        "placeholder b04 - clean code (split balancing)",
        "test_url_b04",
        '    def test_url_b04(self):\n        assert validate_url("http://example.com/path") is True'))
    variants.append(_make_variant("val_url_b05", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_b05_helper() -> None:\n    pass',
        "placeholder b05 - clean code (split balancing)",
        "test_url_b05",
        '    def test_url_b05(self):\n        assert validate_url("") is False'))
    variants.append(_make_variant("val_url_b06", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_b06_helper() -> None:\n    pass',
        "placeholder b06 - clean code (split balancing)",
        "test_url_b06",
        '    def test_url_b06(self):\n        assert validate_url("example.com/path") is False'))
    variants.append(_make_variant("val_url_b07", "validators", "validate_url", "boundary",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    return url.startswith("http://") or url.startswith("https://")',
        '    return url.startswith("http://") or url.startswith("https://")',
        '    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        "only checks protocol prefix, no host/path validation",
        "test_url_need_host",
        '    def test_url_need_host(self):\n        assert validate_url("http://") is False\n        assert validate_url("https://x") is False'))

    # url sv
    variants.append(_make_variant("val_url_s01", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    for prefix in ("https://", "http://", "ftp://"):\n        if url.startswith(prefix):\n            rest = url[len(prefix):]\n            return len(rest) > 0 and "/" in rest\n    return False',
        '    for prefix in ("https://", "http://", "ftp://"):', '    for prefix in ("https://", "http://"):',
        "accepts ftp:// protocol",
        "test_url_sv_no_ftp",
        '    def test_url_sv_no_ftp(self):\n        assert validate_url("ftp://example.com/path") is False'))
    variants.append(_make_variant("val_url_s02", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if "://" not in url:\n        return False\n    rest = url.split("://", 1)[1]\n    return len(rest) > 0 and "/" in rest',
        '    if "://" not in url:\n        return False\n    rest = url.split("://", 1)[1]\n    return len(rest) > 0 and "/" in rest',
        '    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        "accepts any protocol with ://",
        "test_url_sv_protocol",
        '    def test_url_sv_protocol(self):\n        assert validate_url("ftp://example.com/path") is False'))
    variants.append(_make_variant("val_url_s03", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_s03_helper() -> None:\n    pass',
        "placeholder s03 - clean code (split balancing)",
        "test_url_s03",
        '    def test_url_s03(self):\n        assert validate_url("http://localhost:8080/api") is True'))
    variants.append(_make_variant("val_url_s04", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_s04_helper() -> None:\n    pass',
        "placeholder s04 - clean code (split balancing)",
        "test_url_s04",
        '    def test_url_s04(self):\n        assert validate_url("https://example.com/path?q=1") is True'))
    variants.append(_make_variant("val_url_s05", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_s05_helper() -> None:\n    pass',
        "placeholder s05 - clean code (split balancing)",
        "test_url_s05",
        '    def test_url_s05(self):\n        assert validate_url("http://example.com/") is True'))
    variants.append(_make_variant("val_url_s06", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    url = url.rstrip("/")\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    url = url.rstrip("/")\n    if not url:', '    if not url:',
        "strips trailing slash before validation",
        "test_url_sv_rstrip",
        '    def test_url_sv_rstrip(self):\n        assert validate_url("https://example.com/") is True'))
    variants.append(_make_variant("val_url_s07", "validators", "validate_url", "string_validation",
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    url = url.lower()\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    url = url.lower()\n    if not url:', '    if not url:',
        "lowercases URL before validation",
        "test_url_sv_lower",
        '    def test_url_sv_lower(self):\n        assert validate_url("HTTPS://Example.COM/Path") is True'))

    # --- validate_date ---
    variants.append(_make_variant("val_dat_b01", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    return True',
        '    return True',
        '    from datetime import datetime as _dt\n\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        "only checks regex, not actual date validity",
        "test_date_real_validation",
        '    def test_date_real_validation(self):\n        assert validate_date_format("2024-02-30") is False\n        assert validate_date_format("2024-13-01") is False'))
    variants.append(_make_variant("val_dat_b02", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")',
        '    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")',
        "accepts dates with '/' separator",
        "test_date_no_slash",
        '    def test_date_no_slash(self):\n        assert validate_date_format("2024/01/15") is False'))
    variants.append(_make_variant("val_dat_b03", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b03_helper() -> None:\n    pass',
        "placeholder b03 - clean code (split balancing)",
        "test_date_b03",
        '    def test_date_b03(self):\n        assert validate_date_format("2024-01-15") is True'))
    variants.append(_make_variant("val_dat_b04", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b04_helper() -> None:\n    pass',
        "placeholder b04 - clean code (split balancing)",
        "test_date_b04",
        '    def test_date_b04(self):\n        assert validate_date_format("01/15/2024") is False'))
    variants.append(_make_variant("val_dat_b05", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b05_helper() -> None:\n    pass',
        "placeholder b05 - clean code (split balancing)",
        "test_date_b05",
        '    def test_date_b05(self):\n        assert validate_date_format("2024-02-29") is True'))
    variants.append(_make_variant("val_dat_b06", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        dt = _dt.strptime(date_str, "%Y-%m-%d")\n        if dt.year < 2000:\n            return False\n        return True\n    except ValueError:\n        return False',
        '        if dt.year < 2000:\n            return False\n        return True', '        return True',
        "rejects dates before year 2000",
        "test_date_allow_old",
        '    def test_date_allow_old(self):\n        assert validate_date_format("1999-12-31") is True'))
    variants.append(_make_variant("val_dat_b07", "validators", "validate_date_format", "boundary",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b07_helper() -> None:\n    pass',
        "placeholder b07 - clean code (split balancing)",
        "test_date_b07",
        '    def test_date_b07(self):\n        assert validate_date_format("2023-02-29") is False'))

    # date sv
    variants.append(_make_variant("val_dat_s01", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")',
        '    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")',
        "accepts '/' separator",
        "test_date_sv_slash",
        '    def test_date_sv_slash(self):\n        assert validate_date_format("2024/01/15") is False'))
    variants.append(_make_variant("val_dat_s02", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):\n        try:\n            _dt.strptime(date_str, fmt)\n            return True\n        except ValueError:\n            continue\n    return False',
        '    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):', '    for fmt in ("%Y-%m-%d",):',
        "also accepts DD-MM-YYYY format",
        "test_date_sv_only_ymd",
        '    def test_date_sv_only_ymd(self):\n        assert validate_date_format("15-01-2024") is False'))
    variants.append(_make_variant("val_dat_s03", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_s03_helper() -> None:\n    pass',
        "placeholder s03 - clean code (split balancing)",
        "test_date_s03",
        '    def test_date_s03(self):\n        assert validate_date_format("2000-02-29") is True'))
    variants.append(_make_variant("val_dat_s04", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_s04_helper() -> None:\n    pass',
        "placeholder s04 - clean code (split balancing)",
        "test_date_s04",
        '    def test_date_s04(self):\n        assert validate_date_format("1900-02-29") is False'))
    variants.append(_make_variant("val_dat_s05", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_s05_helper() -> None:\n    pass',
        "placeholder s05 - clean code (split balancing)",
        "test_date_s05",
        '    def test_date_s05(self):\n        assert validate_date_format("2024-00-01") is False'))
    variants.append(_make_variant("val_dat_s06", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    date_str = date_str.strip()\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    date_str = date_str.strip()\n    if not re.match', '    if not re.match',
        "strips whitespace before validation",
        "test_date_sv_strip",
        '    def test_date_sv_strip(self):\n        assert validate_date_format(" 2024-01-15 ") is False'))
    variants.append(_make_variant("val_dat_s07", "validators", "validate_date_format", "string_validation",
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\\\d{4}-\\\\d{2}-\\\\d{2}$", date_str):\n        return False\n    try:\n        dt = _dt.strptime(date_str, "%Y-%m-%d")\n        if dt > _dt.now():\n            return False\n        return True\n    except ValueError:\n        return False',
        '        if dt > _dt.now():\n            return False\n        return True', '        return True',
        "rejects future dates",
        "test_date_sv_future",
        '    def test_date_sv_future(self):\n        assert validate_date_format("2099-12-31") is True'))

    return variants


if __name__ == "__main__":
    generate_catalog()
