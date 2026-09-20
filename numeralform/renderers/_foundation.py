"""Shared base for small, reviewed foundation locale renderers."""

from typing import ClassVar

from ._shared import LexicalRenderer


class FoundationRenderer(LexicalRenderer):
    """Standalone cardinal renderer with an intentionally bounded domain."""

    max_cardinal = 9_999
    ordinals: ClassVar[dict[int, str]] = {}
