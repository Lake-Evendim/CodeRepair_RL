"""Private tests for validators."""

from src.validators import (
    validate_date_format,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_url,
)


class TestValidateEmailPrivate:
    def test_empty_string(self):
        assert validate_email("") is False

    def test_no_domain(self):
        assert validate_email("user@") is False

    def test_subdomain(self):
        assert validate_email("user@sub.example.com") is True


class TestValidatePhonePrivate:
    def test_15_digits_max(self):
        assert validate_phone("123456789012345") is True

    def test_16_digits_too_long(self):
        assert validate_phone("1234567890123456") is False

    def test_spaces_format(self):
        assert validate_phone("123 456 7890") is True


class TestValidatePasswordStrengthPrivate:
    def test_exactly_8_chars(self):
        assert validate_password_strength("Abc1234!") is True

    def test_7_chars_fails(self):
        assert validate_password_strength("Abc123!") is False

    def test_all_digits(self):
        assert validate_password_strength("12345678") is False


class TestValidateUrlPrivate:
    def test_just_host(self):
        assert validate_url("https://example.com") is False

    def test_empty_string(self):
        assert validate_url("") is False

    def test_path_with_port(self):
        assert validate_url("http://localhost:8080/api") is True


class TestValidateDateFormatPrivate:
    def test_leap_year(self):
        assert validate_date_format("2024-02-29") is True

    def test_non_leap_year_feb29(self):
        assert validate_date_format("2023-02-29") is False

    def test_leap_year_century(self):
        assert validate_date_format("1900-02-29") is False

    def test_leap_year_400(self):
        assert validate_date_format("2000-02-29") is True
