"""Fix all placeholder variants in bug_catalog.py with real, testable bugs."""

from __future__ import annotations

import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "minirepair" / "data" / "bug_catalog.py"

# Each entry: variant_id -> (new_buggy_code, new_fix_old, new_fix_new, new_test_code)
FIXES: dict[str, tuple[str, str, str, str]] = {
    # --- validate_password_strength boundary ---
    "val_pwd_b04": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: need 2+ uppercase."""\n    if len(password) < 8:\n        return False\n    uppers = sum(1 for c in password if c.isupper())\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return uppers >= 2 and has_lower and has_digit and has_special',
        '    return uppers >= 2 and has_lower and has_digit and has_special',
        '    has_upper = any(c.isupper() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    def test_pwd_need_2_upper(self):\n        assert validate_password_strength("Abc12345!") is True',
    ),
    "val_pwd_b05": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: need 2+ digits."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    digits = sum(1 for c in password if c.isdigit())\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and digits >= 2 and has_special',
        '    return has_upper and has_lower and digits >= 2 and has_special',
        '    has_digit = any(c.isdigit() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    def test_pwd_need_2_digits(self):\n        assert validate_password_strength("Abc12345!") is True',
    ),
    "val_pwd_b06": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: reject 3+ consecutive same chars."""\n    if len(password) < 8:\n        return False\n    for i in range(len(password) - 2):\n        if password[i] == password[i+1] == password[i+2]:\n            return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    for i in range(len(password) - 2):\n        if password[i] == password[i+1] == password[i+2]:\n            return False\n    has_upper',
        '    has_upper',
        '    def test_pwd_no_consecutive(self):\n        assert validate_password_strength("Abc111234!") is True',
    ),
    "val_pwd_b07": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: require 10+ chars."""\n    if len(password) < 10:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    if len(password) < 10:', '    if len(password) < 8:',
        '    def test_pwd_min_8_not_10(self):\n        assert validate_password_strength("Abc1234!") is True',
    ),
    # --- validate_password_strength string_validation ---
    "val_pwd_s04": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: reject common words."""\n    if len(password) < 8:\n        return False\n    lower = password.lower()\n    for word in ("password", "123456", "qwerty", "abc123"):\n        if word in lower:\n            return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    lower = password.lower()\n    for word in ("password", "123456", "qwerty", "abc123"):\n        if word in lower:\n            return False\n    has_upper',
        '    has_upper',
        '    def test_pwd_no_common_words(self):\n        assert validate_password_strength("MyP@ssw0rd!") is True',
    ),
    "val_pwd_s05": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: must start with uppercase."""\n    if len(password) < 8:\n        return False\n    if not password[0].isupper():\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    if not password[0].isupper():\n        return False\n    has_upper',
        '    has_upper',
        '    def test_pwd_no_start_upper(self):\n        assert validate_password_strength("aBc12345!") is True',
    ),
    "val_pwd_s07": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: max 20 chars."""\n    if len(password) < 8:\n        return False\n    if len(password) > 20:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    if len(password) > 20:\n        return False\n    has_upper', '    has_upper',
        '    def test_pwd_no_max_length(self):\n        assert validate_password_strength("Abc12345!Abc12345!Abc") is True',
    ),
    # --- validate_url boundary ---
    "val_url_b03": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: reject query params."""\n    if not url:\n        return False\n    if "?" in url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    if "?" in url:\n        return False\n    if url.startswith("https://"):',
        '    if url.startswith("https://"):',
        '    def test_url_allow_query(self):\n        assert validate_url("https://example.com/path?q=1") is True',
    ),
    "val_url_b04": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: reject fragments."""\n    if not url:\n        return False\n    if "#" in url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    if "#" in url:\n        return False\n    if url.startswith("https://"):',
        '    if url.startswith("https://"):',
        '    def test_url_allow_fragment(self):\n        assert validate_url("https://example.com/path#section") is True',
    ),
    "val_url_b05": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: reject port numbers."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    if ":" in rest.split("/")[0]:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    if ":" in rest.split("/")[0]:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    def test_url_allow_port(self):\n        assert validate_url("http://localhost:8080/api") is True',
    ),
    "val_url_b06": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: reject IP addresses."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    host = rest.split("/")[0]\n    if host.replace(".", "").isdigit():\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    host = rest.split("/")[0]\n    if host.replace(".", "").isdigit():\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    def test_url_allow_ip(self):\n        assert validate_url("http://192.168.1.1/api") is True',
    ),
    # --- validate_url string_validation ---
    "val_url_s03": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: also accept ftp."""\n    if not url:\n        return False\n    for prefix in ("https://", "http://", "ftp://"):\n        if url.startswith(prefix):\n            rest = url[len(prefix):]\n            return len(rest) > 0 and "/" in rest\n    return False',
        '    for prefix in ("https://", "http://", "ftp://"):', '    for prefix in ("https://", "http://"):',
        '    def test_url_sv_no_ftp(self):\n        assert validate_url("ftp://example.com/path") is False',
    ),
    "val_url_s04": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: also accept ssh."""\n    if not url:\n        return False\n    for prefix in ("https://", "http://", "ssh://"):\n        if url.startswith(prefix):\n            rest = url[len(prefix):]\n            return len(rest) > 0 and "/" in rest\n    return False',
        '    for prefix in ("https://", "http://", "ssh://"):', '    for prefix in ("https://", "http://"):',
        '    def test_url_sv_no_ssh(self):\n        assert validate_url("ssh://example.com") is False',
    ),
    "val_url_s05": (
        'def validate_url(url: str) -> bool:\n    """Validate URL: accept any protocol."""\n    if not url:\n        return False\n    if "://" not in url:\n        return False\n    rest = url.split("://", 1)[1]\n    return len(rest) > 0 and "/" in rest',
        '    if "://" not in url:\n        return False\n    rest = url.split("://", 1)[1]\n    return len(rest) > 0 and "/" in rest',
        '    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    def test_url_sv_specific_protocol(self):\n        assert validate_url("ftp://example.com/path") is False',
    ),
    # --- validate_date boundary ---
    "val_dat_b03": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: reject before 1900."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        dt = _dt.strptime(date_str, "%Y-%m-%d")\n        if dt.year < 1900:\n            return False\n        return True\n    except ValueError:\n        return False',
        '        if dt.year < 1900:\n            return False\n        return True', '        return True',
        '    def test_date_allow_old(self):\n        assert validate_date_format("1899-12-31") is True',
    ),
    "val_dat_b04": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: reject after 2100."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        dt = _dt.strptime(date_str, "%Y-%m-%d")\n        if dt.year > 2100:\n            return False\n        return True\n    except ValueError:\n        return False',
        '        if dt.year > 2100:\n            return False\n        return True', '        return True',
        '    def test_date_allow_future(self):\n        assert validate_date_format("2101-01-01") is True',
    ),
    "val_dat_b05": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: reject dates with time."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    if "T" in date_str or " " in date_str:\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    if "T" in date_str or " " in date_str:\n        return False\n    try:', '    try:',
        '    def test_date_no_time_check(self):\n        assert validate_date_format("2024-01-15") is True',
    ),
    "val_dat_b07": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: reject weekends."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        dt = _dt.strptime(date_str, "%Y-%m-%d")\n        if dt.weekday() >= 5:\n            return False\n        return True\n    except ValueError:\n        return False',
        '        if dt.weekday() >= 5:\n            return False\n        return True', '        return True',
        '    def test_date_allow_weekends(self):\n        assert validate_date_format("2024-01-13") is True',  # Saturday
    ),
    # --- validate_date string_validation ---
    "val_dat_s03": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: accept DD-MM-YYYY."""\n    from datetime import datetime as _dt\n\n    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):\n        try:\n            _dt.strptime(date_str, fmt)\n            return True\n        except ValueError:\n            continue\n    return False',
        '    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):', '    for fmt in ("%Y-%m-%d",):',
        '    def test_date_sv_only_ymd(self):\n        assert validate_date_format("15-01-2024") is False',
    ),
    "val_dat_s04": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: accept MM-DD-YYYY."""\n    from datetime import datetime as _dt\n\n    for fmt in ("%Y-%m-%d", "%m-%d-%Y"):\n        try:\n            _dt.strptime(date_str, fmt)\n            return True\n        except ValueError:\n            continue\n    return False',
        '    for fmt in ("%Y-%m-%d", "%m-%d-%Y"):', '    for fmt in ("%Y-%m-%d",):',
        '    def test_date_sv_no_mdy(self):\n        assert validate_date_format("01-15-2024") is False',
    ),
    "val_dat_s05": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: accept YYYY/MM/DD."""\n    from datetime import datetime as _dt\n\n    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    normalized = date_str.replace("/", "-")\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", normalized):\n        return False\n    try:\n        _dt.strptime(normalized, "%Y-%m-%d")',
        '    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")',
        '    def test_date_sv_no_slash(self):\n        assert validate_date_format("2024/01/15") is False',
    ),
    # --- validate_email sv ---
    "val_eml_s06": (
        'def validate_email(email: str) -> bool:\n    """Validate email: reject digits in local."""\n    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if any(c.isdigit() for c in local):\n        return False\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    if any(c.isdigit() for c in local):\n        return False\n    if not local or not domain:',
        '    if not local or not domain:',
        '    def test_email_sv_allow_digits(self):\n        assert validate_email("user123@example.com") is True',
    ),
    "val_eml_s07": (
        'def validate_email(email: str) -> bool:\n    """Validate email: reject underscores in local."""\n    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if "_" in local:\n        return False\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    if "_" in local:\n        return False\n    if not local or not domain:',
        '    if not local or not domain:',
        '    def test_email_sv_allow_underscore(self):\n        assert validate_email("user_name@example.com") is True',
    ),
    # --- validate_phone sv ---
    "val_phn_s05": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone: reject all same digits."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    if len(set(cleaned)) == 1:\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    if len(set(cleaned)) == 1:\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    def test_phone_sv_allow_same_digits(self):\n        assert validate_phone("1111111111") is True',
    ),
    "val_phn_s07": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone: reject starting with 0."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    if cleaned.startswith("0"):\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    if cleaned.startswith("0"):\n        return False\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    def test_phone_sv_allow_leading_zero(self):\n        assert validate_phone("0123456789") is True',
    ),
}


def apply_fixes():
    content = CATALOG.read_text()
    count = 0

    for vid, (buggy, fix_old, fix_new, test) in FIXES.items():
        # Find the BugVariant block
        pattern = rf'(\s*BugVariant\(\s*variant_id="{vid}".*?\),\n)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print(f"WARNING: {vid} not found")
            continue

        old_block = match.group(1)

        # Build replacement block by updating fields
        # Use string replacement instead of regex to avoid escape issues
        new_block = old_block

        # Helper to replace a triple-quoted field
        def _replace_field(text, field_name, new_value):
            pattern_start = f"{field_name}='''"
            idx = text.find(pattern_start)
            if idx == -1:
                return text
            start = idx + len(pattern_start)
            end = text.find("'''", start)
            if end == -1:
                return text
            return text[:start] + new_value + text[end:]

        new_block = _replace_field(new_block, "buggy_code", buggy)
        new_block = _replace_field(new_block, "fix_old", fix_old)
        new_block = _replace_field(new_block, "fix_new", fix_new)
        new_block = _replace_field(new_block, "test_code", test)

        # Update description
        desc_map = {
            "val_pwd_b04": "requires 2+ uppercase letters instead of 1",
            "val_pwd_b05": "requires 2+ digits instead of 1",
            "val_pwd_b06": "rejects passwords with 3+ consecutive same characters",
            "val_pwd_b07": "requires 10+ chars instead of 8",
            "val_pwd_s04": "rejects passwords containing common words",
            "val_pwd_s05": "requires password to start with uppercase",
            "val_pwd_s07": "rejects passwords longer than 20 chars",
            "val_url_b03": "rejects URLs with query parameters",
            "val_url_b04": "rejects URLs with fragments",
            "val_url_b05": "rejects URLs with port numbers",
            "val_url_b06": "rejects URLs with IP addresses",
            "val_url_s03": "also accepts ftp:// protocol",
            "val_url_s04": "also accepts ssh:// protocol",
            "val_url_s05": "accepts any protocol with ://",
            "val_dat_b03": "rejects dates before year 1900",
            "val_dat_b04": "rejects dates after year 2100",
            "val_dat_b05": "rejects dates with time component",
            "val_dat_b07": "rejects weekend dates",
            "val_dat_s03": "also accepts DD-MM-YYYY format",
            "val_dat_s04": "also accepts MM-DD-YYYY format",
            "val_dat_s05": "accepts / separator in dates",
            "val_eml_s06": "rejects emails with digits in local part",
            "val_eml_s07": "rejects emails with underscores in local part",
            "val_phn_s05": "rejects phone numbers with all same digits",
            "val_phn_s07": "rejects phone numbers starting with 0",
        }
        if vid in desc_map:
            new_block = re.sub(
                r'description=".*?"',
                f'description="{desc_map[vid]}"',
                new_block, count=1,
            )

        content = content.replace(old_block, new_block)
        count += 1
        print(f"Fixed {vid}")

    CATALOG.write_text(content)
    print(f"\nApplied {count} fixes to {CATALOG}")


if __name__ == "__main__":
    apply_fixes()
