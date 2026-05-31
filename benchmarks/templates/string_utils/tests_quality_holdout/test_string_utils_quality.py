"""Quality holdout tests for string_utils — offline dataset quality validation only."""

from src.string_utils import count_substring, pad_string, truncate_string


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
