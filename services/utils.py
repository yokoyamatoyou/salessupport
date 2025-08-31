from __future__ import annotations

import re


def sanitize_for_prompt(text: str) -> str:
    """Remove potentially dangerous prompt directives and HTML tags.

    This helper strips role markers like ``system:``, ``assistant:``,
    ``user:``, or ``developer:``, removes HTML tags, and eliminates
    backticks or zero-width characters while preserving other text such as
    braces or non-ASCII characters.
    """
    if not isinstance(text, str):
        return text

    sanitized = re.sub(r"(?i)\b(?:system|assistant|user|developer)\s*:", "", text)
    sanitized = re.sub(r"<[^>]*>", "", sanitized)
    sanitized = sanitized.replace("`", "")
    sanitized = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]", "", sanitized)
    sanitized = re.sub(r"[\u2600-\u27BF]", "", sanitized)
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized.strip()


def escape_braces(text: str) -> str:
    """Escape curly braces in the given text for safe formatting.

    This replaces ``{"`` with ``"{{"`` and ``"}"`` with ``"}}"`` so that
    user provided values containing braces do not interfere with string
    formatting templates.
    """
    if not isinstance(text, str):
        return text
    return text.replace("{", "{{").replace("}", "}}")


EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = re.compile(r"\+?\d[\d\-\s]{9,}\d")
NAME_REGEX = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b|[\u4e00-\u9fff]{3,}")


def mask_pii(text: str) -> str:
    """Mask common personally identifiable information in the given text.

    This function replaces email addresses, phone numbers, and personal names
    with asterisks (``***``) to prevent accidental logging of sensitive data.
    """

    if not isinstance(text, str):
        text = str(text)

    text = EMAIL_REGEX.sub("***", text)
    text = PHONE_REGEX.sub("***", text)
    text = NAME_REGEX.sub("***", text)
    return text
