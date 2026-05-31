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
        result = truncate_string("caf\u00e9", 4)
        assert result == "caf\u00e9"

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
        assert reverse_words("hello\tworld") == "world hello"


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
