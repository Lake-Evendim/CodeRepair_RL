"""String utility functions."""


def truncate_string(s: str, max_len: int) -> str:
    """Truncate string."""
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."
def count_substring(s: str, sub: str) -> int:
    """Count non-overlapping occurrences of sub in s (case-sensitive)."""
    if not sub:
        return 0
    count = 0
    start = 0
    while True:
        idx = s.find(sub, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(sub)
    return count


def reverse_words(s: str) -> str:
    """Reverse the order of words in a string. Preserve internal spacing style by returning single spaces."""
    return " ".join(s.split()[::-1])


def pad_string(s: str, min_width: int, fill_char: str = " ") -> str:
    """Pad string to at least min_width characters using fill_char."""
    if len(s) >= min_width:
        return s
    padding = fill_char * (min_width - len(s))
    return s + padding


def capitalize_words(s: str) -> str:
    """Capitalize the first letter of each word, lowercase the rest."""
    return " ".join(w[:1].upper() + w[1:].lower() if w else "" for w in s.split(" "))
