"""Regional renderers whose number systems differ from their base locale."""

from __future__ import annotations

from .en import EnglishRenderer
from .fr import _UNDER_20, FrenchRenderer


class EnglishIndiaRenderer(EnglishRenderer):
    locale = "en-IN"

    def _render_cardinal(self, value: int, style: str | None = None) -> str:
        if value < 0:
            return "minus " + self._render_cardinal(-value, style)
        if value < 1_000:
            return super()._render_cardinal(value, style)
        for scale, name in (
            (10_000_000, "crore"),
            (100_000, "lakh"),
            (1_000, "thousand"),
        ):
            if value >= scale:
                quotient, remainder = divmod(value, scale)
                suffix = self._render_cardinal(remainder, style) if remainder else ""
                if suffix and style == "british-and" and remainder < 100:
                    suffix = "and " + suffix
                return f"{self._render_cardinal(quotient, style)} {name}" + (
                    f" {suffix}" if suffix else ""
                )
        raise ValueError("Indian English cardinal value is outside the supported range")


class FrenchBelgiumRenderer(FrenchRenderer):
    locale = "fr-BE"

    def _cardinal(self, value: int) -> str:
        if 70 <= value < 80:
            units = value - 70
            return (
                "septante"
                if not units
                else "septante et un"
                if units == 1
                else f"septante-{_UNDER_20[units]}"
            )
        if 90 <= value < 100:
            units = value - 90
            return (
                "nonante"
                if not units
                else "nonante et un"
                if units == 1
                else f"nonante-{_UNDER_20[units]}"
            )
        return super()._cardinal(value)


class FrenchSwissRenderer(FrenchRenderer):
    locale = "fr-CH"

    def _cardinal(self, value: int) -> str:
        if 70 <= value < 80:
            units = value - 70
            return (
                "septante"
                if not units
                else "septante et un"
                if units == 1
                else f"septante-{_UNDER_20[units]}"
            )
        if 80 <= value < 90:
            units = value - 80
            return (
                "huitante"
                if not units
                else "huitante et un"
                if units == 1
                else f"huitante-{_UNDER_20[units]}"
            )
        if 90 <= value < 100:
            units = value - 90
            return (
                "nonante"
                if not units
                else "nonante et un"
                if units == 1
                else f"nonante-{_UNDER_20[units]}"
            )
        return super()._cardinal(value)


__all__ = ["EnglishIndiaRenderer", "FrenchBelgiumRenderer", "FrenchSwissRenderer"]
