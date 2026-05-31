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
