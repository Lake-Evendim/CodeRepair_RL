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
        result = truncate_string("caf\u00e9", 4)
        assert result == "caf\u00e9"


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
