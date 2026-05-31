"""Quality holdout tests for validators."""

from src.validators import (
    validate_email,
    validate_password_strength,
    validate_phone,
)


class TestValidateEmailQuality:
    def test_numeric_local_part(self):
        assert validate_email("123@example.com") is True

    def test_dot_in_local_part(self):
        assert validate_email("first.last@example.com") is True


class TestValidatePhoneQuality:
    def test_leading_zeros(self):
        assert validate_phone("0012345678") is True

    def test_all_same_digit(self):
        assert validate_phone("1111111111") is True


class TestValidatePasswordStrengthQuality:
    def test_long_all_special(self):
        assert validate_password_strength("!!!!!!!!") is False

    def test_mixed_with_spaces(self):
        assert validate_password_strength("Abc 1234!") is True
