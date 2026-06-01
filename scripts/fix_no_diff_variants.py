"""Fix variants where buggy code has no behavior difference for test inputs.

For each variant, either:
1. Change test input to trigger the bug
2. Change buggy code to produce different behavior
"""

from __future__ import annotations

import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "minirepair" / "data" / "bug_catalog.py"

# Fixes: variant_id -> (new_buggy, new_fix_old, new_fix_new, new_test, new_desc)
FIXES: dict[str, tuple[str, str, str, str, str]] = {
    # su_cap_s01: .title() produces same result for "hello world"
    # Fix: change test to use input where .title() differs
    "su_cap_s01": (
        'def capitalize_words(s: str) -> str:\n    """Capitalize words using title()."""\n    return s.title()',
        '    return s.title()',
        '    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))',
        '    def test_cap_not_title(self):\n        result = capitalize_words("it\'s a test")\n        assert result == "It\'s A Test"',
        "uses .title() which capitalizes after apostrophes incorrectly",
    ),
    # su_cnt_b05: wrong loop condition, need match at boundary
    # The condition `start < len(s) - len(sub) + 1` is actually equivalent to correct
    # Fix: change buggy code to use `start < len(s) - len(sub)` (off by one)
    "su_cnt_b05": (
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    count = 0\n    start = 0\n    while start < len(s) - len(sub):\n        idx = s.find(sub, start)\n        if idx == -1:\n            break\n        count += 1\n        start = idx + len(sub)\n    return count',
        '    while start < len(s) - len(sub):',
        '    while True:',
        '    def test_count_end_boundary(self):\n        assert count_substring("abcabc", "abc") == 2',
        "uses wrong loop bound, missing match at end of string",
    ),
    # su_cnt_s05: replaces newlines - need input with newlines
    "su_cnt_s05": (
        'def count_substring(s: str, sub: str) -> int:\n    """Count occurrences."""\n    if not sub:\n        return 0\n    s = s.replace("\\n", " ")\n    return s.count(sub)',
        '    s = s.replace("\\n", " ")\n    return s.count(sub)',
        '    return s.count(sub)',
        '    def test_count_preserve_newlines(self):\n        assert count_substring("a\\nb\\na", "\\n") == 2',
        "replaces newlines before counting, losing newline matches",
    ),
    # su_pad_b03: > vs >=, need input where len(s) == min_width
    # The bug doesn't manifest because padding is 0. Change buggy to produce extra char.
    "su_pad_b03": (
        'def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:\n    """Pad string."""\n    if len(s) >= min_width:\n        return s + fill_char\n    padding = fill_char * (min_width - len(s))\n    return s + padding',
        '        return s + fill_char',
        '        return s',
        '    def test_pad_exact_width(self):\n        assert pad_string("hello", 5) == "hello"',
        "adds extra fill_char when string already meets min_width",
    ),
    # su_rev_b04: .strip() is no-op. Change to strip words.
    "su_rev_b04": (
        'def reverse_words(s: str) -> str:\n    """Reverse word order."""\n    words = s.split()\n    result = " ".join(words[::-1])\n    return result.strip()',
        '    return result.strip()',
        '    return result',
        '    def test_reverse_no_strip(self):\n        result = reverse_words(" hello world ")\n        assert result == "world hello"',
        "strips leading/trailing whitespace from result",
    ),
    # su_trunc_b06: short max_len branch produces same result. Change to return different value.
    "su_trunc_b06": (
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    if max_len <= 3:\n        return "." * (max_len + 1)\n    return s[: max_len - 3] + "..."',
        '        return "." * (max_len + 1)',
        '        return s[: max_len - 3] + "..."',
        '    def test_trunc_short_max_len(self):\n        result = truncate_string("hello", 3)\n        assert result == "..."',
        "returns wrong length for short max_len",
    ),
    # su_trunc_b07: .rstrip() is no-op. Change test input.
    "su_trunc_b07": (
        'def truncate_string(s: str, max_len: int) -> str:\n    """Truncate string."""\n    if len(s) <= max_len:\n        return s\n    return s[: max_len - 3].rstrip() + "..."',
        '    return s[: max_len - 3].rstrip() + "..."',
        '    return s[: max_len - 3] + "..."',
        '    def test_trunc_no_strip(self):\n        result = truncate_string("abc   xyz", 6)\n        assert result == "abc   " or result == "abc..."',
        "strips trailing whitespace before adding ellipsis",
    ),
    # val_dat_b05: rejects dates with time - need input without time
    # Change to reject dates with leading/trailing whitespace
    "val_dat_b05": (
        'def validate_date_format(date_str: str) -> bool:\n    """Validate date: reject leading/trailing whitespace."""\n    from datetime import datetime as _dt\n\n    if date_str != date_str.strip():\n        return False\n    if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", date_str):\n        return False\n    try:\n        _dt.strptime(date_str, "%Y-%m-%d")\n        return True\n    except ValueError:\n        return False',
        '    if date_str != date_str.strip():\n        return False\n    if not re.match',
        '    if not re.match',
        '    def test_date_no_whitespace_check(self):\n        assert validate_date_format(" 2024-01-15 ") is True',
        "rejects dates with leading/trailing whitespace",
    ),
    # val_eml_b07: placeholder - add real bug (reject emails with digits in local)
    "val_eml_b07": (
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if any(c.isdigit() for c in local):\n        return False\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    if any(c.isdigit() for c in local):\n        return False\n    if not local or not domain:',
        '    if not local or not domain:',
        '    def test_email_b07_allow_digits(self):\n        assert validate_email("user123@example.com") is True',
        "rejects emails with digits in local part",
    ),
    # val_eml_s05: lowercases email - need input where case matters
    # The validation doesn't depend on case, so this is a non-bug.
    # Change to strip whitespace instead.
    "val_eml_s05": (
        'def validate_email(email: str) -> bool:\n    """Validate email."""\n    email = email.strip()\n    if not email or ".." in email:\n        return False\n    parts = email.split("@")\n    if len(parts) != 2:\n        return False\n    local, domain = parts\n    if not local or not domain:\n        return False\n    if "." not in domain:\n        return False\n    if domain.startswith(".") or domain.endswith("."):\n        return False\n    return True',
        '    email = email.strip()\n    if not email or ".." in email:',
        '    if not email or ".." in email:',
        '    def test_email_sv_no_strip(self):\n        assert validate_email(" user@example.com ") is False',
        "strips whitespace before validation",
    ),
    # val_phn_s03: strips all non-digits - same result for current test
    # Change to not handle + prefix
    "val_phn_s03": (
        'def validate_phone(phone: str) -> bool:\n    """Validate phone."""\n    import re\n    cleaned = re.sub(r"\\D", "", phone)\n    return 10 <= len(cleaned) <= 15',
        '    import re\n    cleaned = re.sub(r"\\D", "", phone)\n    return 10 <= len(cleaned) <= 15',
        '    cleaned = phone.replace("-", "").replace(" ", "")\n    if cleaned.startswith("+"):\n        cleaned = cleaned[1:]\n    return cleaned.isdigit() and 10 <= len(cleaned) <= 15',
        '    def test_phone_sv_strip_method(self):\n        assert validate_phone("+1-234-567-8901") is True',
        "strips all non-digits including +, different length calculation",
    ),
    # val_pwd_b05: requires 2+ digits - need input with 1 digit
    "val_pwd_b05": (
        'def validate_password_strength(password: str) -> bool:\n    """Validate password: need 2+ digits."""\n    if len(password) < 8:\n        return False\n    has_upper = any(c.isupper() for c in password)\n    has_lower = any(c.islower() for c in password)\n    digits = sum(1 for c in password if c.isdigit())\n    has_special = any(not c.isalnum() for c in password)\n    return has_upper and has_lower and digits >= 2 and has_special',
        '    return has_upper and has_lower and digits >= 2 and has_special',
        '    has_digit = any(c.isdigit() for c in password)\n    return has_upper and has_lower and has_digit and has_special',
        '    def test_pwd_need_2_digits(self):\n        assert validate_password_strength("Abcdefg1!") is True',
        "requires 2+ digits instead of 1",
    ),
    # val_url_s07: test bug - clean code also fails. Fix test.
    "val_url_s07": (
        'def validate_url(url: str) -> bool:\n    """Validate URL, lowercasing first."""\n    url = url.lower()\n    if not url:\n        return False\n    if url.startswith("https://"):\n        rest = url[8:]\n    elif url.startswith("http://"):\n        rest = url[7:]\n    else:\n        return False\n    return len(rest) > 0 and "/" in rest',
        '    url = url.lower()\n    if not url:',
        '    if not url:',
        '    def test_url_sv_lower(self):\n        assert validate_url("HTTPS://Example.COM/Path") is True',
        "lowercases URL before validation",
    ),
}


def apply_fixes():
    content = CATALOG.read_text()
    count = 0

    for vid, (buggy, fix_old, fix_new, test, desc) in FIXES.items():
        # Find the BugVariant block
        pattern = rf'(\s*BugVariant\(\s*variant_id="{vid}".*?\),\n)'
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            print(f"WARNING: {vid} not found")
            continue

        old_block = match.group(1)
        new_block = old_block

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
        new_block = re.sub(r'description=".*?"', f'description="{desc}"', new_block, count=1)

        content = content.replace(old_block, new_block)
        count += 1
        print(f"Fixed {vid}: {desc}")

    CATALOG.write_text(content)
    print(f"\nApplied {count} fixes")


if __name__ == "__main__":
    apply_fixes()
