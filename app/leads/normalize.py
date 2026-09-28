"""Data normalization functions for incoming lead records.

Cleans phone numbers, emails, names, priorities, and demographics into
standardized forms.
"""

from __future__ import annotations

import re

RE_NOT_AVAILABLE = re.compile(r"^(not available|na|n/a|none|nil|-)$", re.IGNORECASE)
RE_DIGITS = re.compile(r"\D")
RE_SPACES = re.compile(r"\s+")


def clean_str(val: object | None) -> str:
    """Trim and collapse internal whitespace."""
    if val is None:
        return ""
    text = str(val).strip()
    return RE_SPACES.sub(" ", text)


def normalize_name(raw: object | None) -> str:
    """Clean and title-case lead names."""
    cleaned = clean_str(raw)
    if not cleaned or RE_NOT_AVAILABLE.match(cleaned):
        return "Unknown"
    # Title-case gracefully while preserving initials like 'N.'
    parts = cleaned.split()
    return " ".join(p.capitalize() if len(p) > 1 else p.upper() for p in parts)


def normalize_email(raw: object | None) -> tuple[str | None, str]:
    """Return (normalized_email, raw_email).

    If email is empty, invalid, or literally 'Not Available', returns (None, raw).
    """
    cleaned = clean_str(raw)
    if not cleaned or RE_NOT_AVAILABLE.match(cleaned):
        return None, cleaned

    lower = cleaned.lower()
    if "@" in lower and "." in lower.split("@")[-1]:
        return lower, cleaned
    return None, cleaned


def normalize_phone(raw: object | None) -> tuple[str | None, str]:
    """Return (normalized_10_digit_phone, raw_phone).

    Extracts rightmost 10 digits for Indian standard numbers (+91-XXXXX-XXXXX).
    If fewer than 10 digits, returns (None, raw).
    """
    cleaned = clean_str(raw)
    if not cleaned or RE_NOT_AVAILABLE.match(cleaned):
        return None, cleaned

    digits = RE_DIGITS.sub("", cleaned)
    if len(digits) >= 10:
        return digits[-10:], cleaned
    return None, cleaned


def normalize_priority(raw: object | None) -> bool:
    """Determine whether the lead has Priority designation."""
    cleaned = clean_str(raw).lower()
    return cleaned == "priority" or cleaned in {"yes", "true", "1", "high"}


def normalize_gender(raw: object | None) -> str | None:
    cleaned = clean_str(raw).lower()
    if cleaned in {"m", "male"}:
        return "m"
    if cleaned in {"f", "female"}:
        return "f"
    return None


def normalize_age(raw: object | None) -> int | None:
    cleaned = clean_str(raw)
    try:
        val = int(cleaned)
        return val if 10 <= val <= 110 else None
    except ValueError:
        return None


def normalize_text_field(raw: object | None) -> str | None:
    cleaned = clean_str(raw)
    if not cleaned or RE_NOT_AVAILABLE.match(cleaned):
        return None
    return cleaned