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
