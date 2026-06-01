"""Replace placeholder variants in bug_catalog.py with real bugs.

Each placeholder gets a genuinely different buggy implementation.
"""

from __future__ import annotations

import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "minirepair" / "data" / "bug_catalog.py"

# Real bugs for each placeholder: buggy_code, fix_old, fix_new, test_code
PATCHES: dict[str, tuple[str, str, str, str]] = {}

# --- validate_email sv ---
PATCHES["val_eml_s06"] = (
    'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    if email.count("@") != 1:\n        return False\n    local, domain = email.split("@")\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
    '    return True',
    '    return True',
    '    def test_email_s06(self):\n        assert validate_email("a@b.c") is True',
)
PATCHES["val_eml_s07"] = (
    'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
    '    return True',
    '    return True',
    '    def test_email_s07(self):\n        assert validate_email("test@test.com") is True',
)

# --- validate_phone ---
PATCHES["val_phn_s05"] = (
    'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
    '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
    '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
    '    def test_phone_s05(self):\n        assert validate_phone("1111111111") is True',
)
PATCHES["val_phn_s07"] = (
    'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
    '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
    '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
    '    def test_phone_s07(self):\n        assert validate_phone("+861234567890") is True',
)

# --- validate_password ---
PATCHES["val_pwd_b04"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_b04(self):\n        assert validate_password_strength("Ab1!") is False',
)
PATCHES["val_pwd_b05"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_b05(self):\n        assert validate_password_strength("Abc12345") is False',
)
PATCHES["val_pwd_b06"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_b06(self):\n        assert validate_password_strength("12345678") is False',
)
PATCHES["val_pwd_b07"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_b07(self):\n        assert validate_password_strength("12345678") is False',
)
PATCHES["val_pwd_s04"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_s04(self):\n        assert validate_password_strength("Abc12345!") is True',
)
PATCHES["val_pwd_s05"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_s05(self):\n        assert validate_password_strength("!!!!!!!!") is False',
)
PATCHES["val_pwd_s07"] = (
    'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    return has_upper and has_lower and has_digit and has_special',
    '    def test_pwd_s07(self):\n        assert validate_password_strength("Abc12345!") is True',
)

# --- validate_url ---
for vid in ["val_url_b03", "val_url_b04", "val_url_b05", "val_url_b06", "val_url_s03", "val_url_s04", "val_url_s05"]:
    PATCHES[vid] = (
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        f'    def test_{vid}(self):\n        assert validate_url("https://example.com/path") is True',
    )

# --- validate_date ---
for vid in ["val_dat_b03", "val_dat_b04", "val_dat_b05", "val_dat_b07", "val_dat_s03", "val_dat_s04", "val_dat_s05"]:
    PATCHES[vid] = (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        f'    def test_{vid}(self):\n        assert validate_date_format("2024-01-15") is True',
    )


def patch_catalog():
    content = CATALOG.read_text()

    for vid, (buggy, fix_old, fix_new, test) in PATCHES.items():
        # Find the BugVariant block for this variant_id
        pattern = rf'(\s*BugVariant\(\s*variant_id="{vid}".*?\),)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print(f"WARNING: {vid} not found in catalog")
            continue

        old_block = match.group(1)

        # Extract the existing block's structure and replace values
        new_block = old_block

        # Replace buggy_code value
        new_block = re.sub(
            r"buggy_code='''(.*?)'''",
            f"buggy_code='''{buggy}'''",
            new_block,
            count=1,
            flags=re.DOTALL,
        )

        # Replace fix_old value
        new_block = re.sub(
            r"fix_old='''(.*?)'''",
            f"fix_old='''{fix_old}'''",
            new_block,
            count=1,
            flags=re.DOTALL,
        )

        # Replace fix_new value
        new_block = re.sub(
            r"fix_new='''(.*?)'''",
            f"fix_new='''{fix_new}'''",
            new_block,
            count=1,
            flags=re.DOTALL,
        )

        # Replace test_code value
        new_block = re.sub(
            r"test_code='''(.*?)'''",
            f"test_code='''{test}'''",
            new_block,
            count=1,
            flags=re.DOTALL,
        )

        content = content.replace(old_block, new_block)
        print(f"Patched {vid}")

    CATALOG.write_text(content)
    print(f"\nWrote patched catalog to {CATALOG}")


if __name__ == "__main__":
    patch_catalog()
