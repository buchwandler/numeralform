"""Thin optional PyICU RuleBasedNumberFormat adapter.

This module is imported only by maintainer-time generator commands.
"""

from __future__ import annotations

from .base import OracleInfo


class OracleUnavailable(RuntimeError):
    pass


class ICUOracle:
    def __init__(self) -> None:
        try:
            import icu  # type: ignore
        except ImportError as exc:
            raise OracleUnavailable(
                "PyICU is required for CLDR corpus generation; install the pinned validation extra"
            ) from exc
        self._icu = icu

    def info(self) -> OracleInfo:
        icu_version = str(getattr(self._icu, "ICU_VERSION", "unknown"))
        unicode_version = getattr(self._icu, "UNICODE_VERSION", None)
        if unicode_version is not None:
            unicode_version = str(unicode_version)
        cldr_version = None
        getter = getattr(self._icu, "getCLDRVersion", None)
        if callable(getter):
            try:
                cldr_version = str(getter())
            except Exception:  # noqa: BLE001
                cldr_version = None
        return OracleInfo("PyICU", icu_version, cldr_version, unicode_version)

    def _formatter(self, locale: str):
        cls = getattr(self._icu, "RuleBasedNumberFormat", None)
        if cls is None:
            raise OracleUnavailable("PyICU does not expose RuleBasedNumberFormat")
        kind = getattr(cls, "SPELLOUT", 0)
        formatter = cls(self._icu.Locale(locale), kind)
        return formatter

    def list_rule_sets(self, locale: str) -> tuple[str, ...]:
        formatter = self._formatter(locale)
        names = formatter.getRuleSetNames()
        return tuple(sorted(str(name) for name in names))

    def format(self, value: int, *, locale: str, rule_set: str) -> str:
        formatter = self._formatter(locale)
        names = self.list_rule_sets(locale)
        if rule_set not in names:
            raise LookupError(
                f"ICU rule set {rule_set!r} is unavailable for locale {locale!r}; available: {', '.join(names)}"
            )
        formatter.setDefaultRuleSet(rule_set)
        result = str(formatter.format(value))
        if not result:
            raise RuntimeError("ICU returned empty output")
        return result
