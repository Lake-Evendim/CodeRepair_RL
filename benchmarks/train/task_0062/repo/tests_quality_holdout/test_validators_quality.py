"""Quality holdout tests for validators."""

from src.validators import validate_email, validate_phone


class TestEmailQuality:
    def test_numeric_local(self):
        assert validate_email("123@example.com") is True


class TestPhoneQuality:
    def test_leading_zeros(self):
        assert validate_phone("0012345678") is True
