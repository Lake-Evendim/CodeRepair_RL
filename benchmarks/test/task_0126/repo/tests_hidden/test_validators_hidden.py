"""Hidden tests for validators — test split only."""

from src.validators import (
    validate_date_format,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_url,
)


class TestEmailHidden:
    def test_dot_in_local(self):
        assert validate_email("first.last@example.com") is True


class TestPhoneHidden:
    def test_all_same(self):
        assert validate_phone("1111111111") is True


class TestPasswordHidden:
    def test_mixed_with_spaces(self):
        assert validate_password_strength("Abc 1234!") is True


class TestUrlHidden:
    def test_path_with_port(self):
        assert validate_url("http://localhost:8080/api") is True


class TestDateHidden:
    def test_leap_400(self):
        assert validate_date_format("2000-02-29") is True
