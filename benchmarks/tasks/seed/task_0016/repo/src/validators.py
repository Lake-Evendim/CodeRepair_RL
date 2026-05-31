"""Validation utility functions."""

import re


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    if "@" not in email:
        return False
    domain = email.split("@")[1]
    if "." not in domain:
        return False
    return True
def validate_phone(phone: str) -> bool:
    """Validate phone: 10-15 digits, optional leading +, optional dashes/spaces between groups."""
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_password_strength(password: str) -> bool:
    """Validate password: >=8 chars, has upper, lower, digit, special char."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special


def validate_url(url: str) -> bool:
    """Validate URL: must start with http:// or https://, then non-empty host."""
    if not url:
        return False
    if url.startswith("https://"):
        rest = url[8:]
    elif url.startswith("http://"):
        rest = url[7:]
    else:
        return False
    return len(rest) > 0 and "/" in rest


def validate_date_format(date_str: str) -> bool:
    """Validate date string is YYYY-MM-DD and represents a real date."""
    from datetime import datetime as _dt

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        _dt.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
