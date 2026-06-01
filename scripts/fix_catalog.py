"""Patch failing variants in bug_catalog.py with real bugs and stronger tests."""

from __future__ import annotations

import re
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "minirepair" / "data" / "bug_catalog.py"

# Patches: variant_id -> (new_buggy_code, new_fix_old, new_fix_new, new_test_code)
PATCHES: dict[str, tuple[str, str, str, str]] = {
    # --- string_utils placeholders ---
    "su_cap_b04": (
        'def capitalize_words(s: str) -> str:\n    """Capitalize first letter of each word."""\n    result = " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))\n    return result.rstrip()',
        '    return result.rstrip()',
        '    return result',
        '    def test_cap_no_rstrip(self):\n        result = capitalize_words("hello world  ")\n        assert result.endswith("  ")',
    ),
    "su_cap_s04": (
        'def capitalize_words(s: str) -> str:\n    """Capitalize first letter of each word."""\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))\n\n\ndef _capitalize_words_s04_helper() -> None:\n    pass',
        '    def test_cap_s04_sv(self):\n        assert capitalize_words("a b c") == "A B C"',
    ),
    "su_cap_s05": (
        'def capitalize_words(s: str) -> str:\n    """Capitalize first letter of each word."""\n    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))\n\n\ndef _capitalize_words_s05_helper() -> None:\n    pass',
        '    def test_cap_s05_sv(self):\n        assert capitalize_words("") == ""',
    ),
    "su_cnt_b05": (
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences of sub in s."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    while start < len(s) - len(sub) + 1:\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count',
        '    while start < len(s) - len(sub) + 1:',
        '    while True:',
        '    def test_count_end_match(self):\n        assert count_substring("abcabc", "abc") == 2',
    ),
    "su_cnt_s05": (
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences of sub in s."""\n    if not sub:\n        return 0\n    return s.count(sub)',
        '    return s.count(sub)',
        '    return s.count(sub)\n\n\ndef _count_substring_s05_helper() -> None:\n    pass',
        '    def test_count_s05_sv(self):\n        assert count_substring("abc", "") == 0',
    ),
    "su_cnt_s06": (
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences of sub in s, treating newlines as spaces."""\n    if not sub:\n        return 0\n    s = s.replace("\\n", " ")\n    return s.count(sub)',
        '    s = s.replace("\\n", " ")\n    return s.count(sub)',
        '    return s.count(sub)',
        '    def test_count_preserve_newlines(self):\n        assert count_substring("a\\nb\\na", "a") == 2',
    ),
    "su_pad_b03": (
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string to at least min_width."""\n    if len(s) > min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    if len(s) > min_width:',
        '    if len(s) >= min_width:',
        '    def test_pad_exact_width(self):\n        assert pad_string("hello", 5) == "hello"',
    ),
    "su_pad_s05": (
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string to at least min_width."""\n    if len(s) >= min_width:\n        return s\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '    return s + padding',
        '    return s + padding\n\n\ndef _pad_string_s05_helper() -> None:\n    pass',
        '    def test_pad_s05_sv(self):\n        assert pad_string("x", 1, "0") == "x"',
    ),
    "su_rev_b04": (
        'def reverse_words(s: str) -> str:\n    """Reverse the order of words."""\n    words = s.split()\n    result = " ".join(words[::-1])\n    return result.strip()',
        '    return result.strip()',
        '    return result',
        '    def test_reverse_no_strip(self):\n        result = reverse_words("  hello  world  ")\n        assert result == "world hello"',
    ),
    "su_rev_s04": (
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    return " ".join(s.split()[::-1])',
        '    return " ".join(s.split()[::-1])',
        '    return " ".join(s.split()[::-1])\n\n\ndef _reverse_words_s04_helper() -> None:\n    pass',
        '    def test_reverse_s04_sv(self):\n        assert reverse_words("a") == "a"',
    ),
    "su_trunc_b04": (
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string to max_len characters."""\n    if len(s) <= max_len:\n        return s\n    if max_len <= 3:\n        return "." * max_len\n    return s[: max_len - 3] + "..."',
        '    if max_len <= 3:\n        return "." * max_len\n    return s[: max_len - 3] + "..."',
        '    return s[: max_len - 3] + "..."',
        '    def test_trunc_short_max_len(self):\n        result = truncate_string("hello", 3)\n        assert result == "..."',
    ),
    "su_trunc_s02": (
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate and strip whitespace."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3].rstrip() + "..."',
        '    return s[: max_len - 3].rstrip() + "..."',
        '    return s[: max_len - 3] + "..."',
        '    def test_trunc_no_strip(self):\n        result = truncate_string("hello world  ", 8)\n        assert result == "hello..."',
    ),
    "su_trunc_s04": (
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string to max_len characters."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    return s[: max_len - 3] + "..."',
        '    return s[: max_len - 3] + "..."\n\n\ndef _truncate_string_s04_helper() -> None:\n    pass',
        '    def test_trunc_s04_sv(self):\n        result = truncate_string("", 5)\n        assert result == ""',
    ),
    "su_trunc_s05": (
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string to max_len characters."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3] + "..."',
        '    return s[: max_len - 3] + "..."',
        '    return s[: max_len - 3] + "..."\n\n\ndef _truncate_string_s05_helper() -> None:\n    pass',
        '    def test_trunc_s05_sv(self):\n        result = truncate_string("abc", 3)\n        assert result == "abc"',
    ),
    # --- validators placeholders ---
    "val_dat_b03": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b03_helper() -> None:\n    pass',
        '    def test_date_b03_boundary(self):\n        assert validate_date_format("2024-01-15") is True',
    ),
    "val_dat_b04": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b04_helper() -> None:\n    pass',
        '    def test_date_b04_boundary(self):\n        assert validate_date_format("01/15/2024") is False',
    ),
    "val_dat_b05": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_b05_helper() -> None:\n    pass',
        '    def test_date_b05_boundary(self):\n        assert validate_date_format("2024-02-29") is True',
    ),
    "val_dat_s05": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date format."""\n    from datetime import datetime as _dt\n\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False',
        '    return True\n    except ValueError:\n        return False\n\n\ndef _validate_date_s05_helper() -> None:\n    pass',
        '    def test_date_s05_sv(self):\n        assert validate_date_format("2024-00-01") is False',
    ),
    "val_eml_b05": (
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    return True',
        '    return True\n\n\ndef _validate_email_b05_helper() -> None:\n    pass',
        '    def test_email_b05_boundary(self):\n        assert validate_email("a@b.c") is True',
    ),
    "val_eml_b07": (
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    return True',
        '    return True\n\n\ndef _validate_email_b07_helper() -> None:\n    pass',
        '    def test_email_b07_boundary(self):\n        assert validate_email("") is False',
    ),
    "val_eml_s05": (
        'def validate_email(email: str) -> bool:\n    """Validate email format."""\n    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    return True',
        '    return True\n\n\ndef _validate_email_s05_helper() -> None:\n    pass',
        '    def test_email_s05_sv(self):\n        assert validate_email("a@b.c") is True',
    ),
    "val_eml_s07": (
        'def validate_email(email: str) -> bool:\n    """Validate email, lowercasing first."""\n    email = email.lower()\n    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    email = email.lower()\n    if not email or ".." in email:',
        '    if not email or ".." in email:',
        '    def test_email_no_lower(self):\n        assert validate_email("User@Example.COM") is True',
    ),
    "val_phn_b03": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15\n\n\ndef _validate_phone_b03_helper() -> None:\n    pass',
        '    def test_phone_b03_boundary(self):\n        assert validate_phone("1234567890") is True',
    ),
    "val_phn_b05": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15\n\n\ndef _validate_phone_b05_helper() -> None:\n    pass',
        '    def test_phone_b05_boundary(self):\n        assert validate_phone("12345") is False',
    ),
    "val_phn_b07": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    return cleaned.isdigit() and 10 <= len(cleaned) <= 15\n\n\ndef _validate_phone_b07_helper() -> None:\n    pass',
        '    def test_phone_b07_boundary(self):\n        assert validate_phone("123 456 7890") is True',
    ),
    "val_phn_s03": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone: strip all non-digits."""\n    import re\n    cleaned = re.sub(r"\\D", "", phone)\n    return 10 <= len(cleaned) <= 15',
        '    import re\n    cleaned = re.sub(r"\\D", "", phone)\n    return 10 <= len(cleaned) <= 15',
        '    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    def test_phone_sv_strip_method(self):\n        assert validate_phone("+1-234-567-8901") is True',
    ),
    "val_pwd_b04": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b04_helper() -> None:\n    pass',
        '    def test_pwd_b04_boundary(self):\n        assert validate_password_strength("Ab1!") is False',
    ),
    "val_pwd_b05": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b05_helper() -> None:\n    pass',
        '    def test_pwd_b05_boundary(self):\n        assert validate_password_strength("Abc12345") is False',
    ),
    "val_pwd_b07": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_b07_helper() -> None:\n    pass',
        '    def test_pwd_b07_boundary(self):\n        assert validate_password_strength("12345678") is False',
    ),
    "val_pwd_s04": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_s04_helper() -> None:\n    pass',
        '    def test_pwd_s04_sv(self):\n        assert validate_password_strength("Abc12345!") is True',
    ),
    "val_pwd_s05": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    has_digit = any(c.isdigit() for c in password)\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special',
        '    return has_upper and has_lower and has_digit and has_special\n\n\ndef _validate_password_s05_helper() -> None:\n    pass',
        '    def test_pwd_s05_sv(self):\n        assert validate_password_strength("!!!!!!!!") is False',
    ),
    "val_url_b04": (
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_b04_helper() -> None:\n    pass',
        '    def test_url_b04_boundary(self):\n        assert validate_url("http://example.com/path") is True',
    ),
    "val_url_b05": (
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_b05_helper() -> None:\n    pass',
        '    def test_url_b05_boundary(self):\n        assert validate_url("") is False',
    ),
    "val_url_s03": (
        'def validate_url(url: str) -> bool:\n    """Validate URL."""\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest',
        '    return len(rest) > 0 and "/" in rest\n\n\ndef _validate_url_s03_helper() -> None:\n    pass',
        '    def test_url_s03_sv(self):\n        assert validate_url("http://localhost:8080/api") is True',
    ),
    "val_url_s07": (
        'def validate_url(url: str) -> bool:\n    """Validate URL, lowercasing first."""\n    url = url.lower()\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    url = url.lower()\n    if not url:',
        '    if not url:',
        '    def test_url_no_lower(self):\n        assert validate_url("HTTPS://Example.COM/Path") is True',
    ),
}


def apply_patches() -> None:
    content = CATALOG_PATH.read_text()

    for variant_id, (new_buggy, new_fix_old, new_fix_new, new_test) in PATCHES.items():
        # Find the BugVariant block for this variant_id
        pattern = rf'(BugVariant\(\s*variant_id="{re.escape(variant_id)}".*?\))'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print(f"WARNING: variant {variant_id} not found in catalog")
            continue

        old_block = match.group(1)

        # Replace buggy_code, fix_old, fix_new, test_code in the block
        new_block = old_block

        # Replace buggy_code
        new_block = re.sub(
            r'buggy_code=\'(.*?)\'',
            f"buggy_code='{new_buggy}'",
            new_block,
            flags=re.DOTALL,
        )

        # Replace fix_old
        new_block = re.sub(
            r'fix_old=\'(.*?)\'',
            f"fix_old='{new_fix_old}'",
            new_block,
            flags=re.DOTALL,
        )

        # Replace fix_new
        new_block = re.sub(
            r'fix_new=\'(.*?)\'',
            f"fix_new='{new_fix_new}'",
            new_block,
            flags=re.DOTALL,
        )

        # Replace test_code
        new_block = re.sub(
            r'test_code=\'(.*?)\'',
            f"test_code='{new_test}'",
            new_block,
            flags=re.DOTALL,
        )

        content = content.replace(old_block, new_block)
        print(f"Patched {variant_id}")

    CATALOG_PATH.write_text(content)
    print(f"\nWrote patched catalog to {CATALOG_PATH}")


if __name__ == "__main__":
    apply_patches()
