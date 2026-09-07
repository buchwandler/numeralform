"""Oracle protocol and metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OracleInfo:
    implementation: str
    implementation_version: str
    cldr_version: str | None
    unicode_version: str | None


class NumberOracle(Protocol):
    def info(self) -> OracleInfo: ...
    def list_rule_sets(self, locale: str) -> tuple[str, ...]: ...
    def format(self, value: int, *, locale: str, rule_set: str) -> str: ...
