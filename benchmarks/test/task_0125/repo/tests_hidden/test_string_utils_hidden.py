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
        assert reverse_words("hello\tworld") == "world hello"


class TestPadHidden:
    def test_single_char_fill(self):
        assert pad_string("x", 1, "0") == "x"


class TestCapitalizeHidden:
    def test_single_char_words(self):
        assert capitalize_words("a b c") == "A B C"
