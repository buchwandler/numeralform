"""Strict Unicode comparison helpers."""

from __future__ import annotations

import unicodedata


def normalize_nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def is_nfc(value: str) -> bool:
    return value == normalize_nfc(value)


def codepoint_repr(value: str) -> str:
    return " ".join(f"U+{ord(char):04X}" for char in value)


def escaped(value: str) -> str:
    return value.encode("unicode_escape").decode("ascii")
