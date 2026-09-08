"""Explicit placeholders for upstream locales not yet independently implemented."""

from __future__ import annotations

from ..errors import UnsupportedFormError
from ..locale import LocaleCapabilities
from ..model import NumeralRequest


class UnsupportedLocaleRenderer:
    """A truthful registry entry with no advertised rendering surface."""

    def __init__(self, locale: str):
        self.locale = locale

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        return LocaleCapabilities(
            notes=(
                "Upstream locale is registered but its successful surfaces remain incomplete.",
            )
        )

    def render(self, request: NumeralRequest):
        raise UnsupportedFormError(
            f"locale {self.locale!r} is registered for discovery but has no implemented compatibility surface"
        )
