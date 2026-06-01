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


    def test_cap_keep_tabs(self):
        result = capitalize_words("hello	world")
        assert "	" in result
