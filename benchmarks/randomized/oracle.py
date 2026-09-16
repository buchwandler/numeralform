"""Oracle invocation keys, result caches, and runtime statistics."""

from __future__ import annotations

import heapq
import json
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter

from .adapters import run_num2words
from .model import ExecutionResult, RandomCase

REJECTED_CACHE_MAX = 4096
SLOWEST_CALLS_KEPT = 10


@dataclass(frozen=True, slots=True)
class OracleInvocationKey:
    """Identity of one upstream oracle invocation.

    Describes what the oracle is asked to convert, not replay metadata such as
    case IDs, indices, surfaces, tags, the seed, or the canonical locale.
    """

    oracle_locale: str
    kind: str
    value_kind: str
    value: str
    currency: str | None
    options_json: str
    call_variant: str | None
    transport: str


def oracle_invocation_key(case: RandomCase) -> OracleInvocationKey:
    return OracleInvocationKey(
        oracle_locale=case.oracle_locale,
        kind=case.kind,
        value_kind=case.value.kind,
        value=case.value.value,
        currency=case.currency,
        options_json=json.dumps(case.options, sort_keys=True),
        call_variant=case.call_variant,
        transport=case.transport,
    )


@dataclass
class OracleRuntimeStats:
    keep_slowest: int = SLOWEST_CALLS_KEPT
    executions: int = 0
    accepted_cache_hits: int = 0
    rejected_cache_hits: int = 0
    total_time: float = 0.0
    max_time: float = 0.0
    _slowest: list[tuple[float, int, OracleInvocationKey]] = field(
        default_factory=list, repr=False
    )
    _sequence: int = field(default=0, repr=False)

    def record(self, key: OracleInvocationKey, elapsed: float) -> None:
        self.executions += 1
        self.total_time += elapsed
        self.max_time = max(self.max_time, elapsed)
        entry = (elapsed, self._sequence, key)
        self._sequence += 1
        if len(self._slowest) < self.keep_slowest:
            heapq.heappush(self._slowest, entry)
        elif elapsed > self._slowest[0][0]:
            heapq.heapreplace(self._slowest, entry)

    def slowest(self) -> tuple[tuple[float, OracleInvocationKey], ...]:
        return tuple(
            (elapsed, key)
            for elapsed, _sequence, key in sorted(self._slowest, reverse=True)
        )


@dataclass
class OracleRunner:
    """Executes oracle invocations once and retains the results.

    Text outcomes are cached indefinitely because accepted generated cases
    need the exact same ``ExecutionResult`` during the comparison pass.
    Rejected outcomes use a bounded LRU so repeated unsupported edge probes
    cannot grow without limit.
    """

    function: Callable[..., object]
    rejected_cache_max: int = REJECTED_CACHE_MAX
    stats: OracleRuntimeStats = field(default_factory=OracleRuntimeStats)
    accepted: dict[OracleInvocationKey, ExecutionResult] = field(default_factory=dict)
    rejected: OrderedDict[OracleInvocationKey, ExecutionResult] = field(
        default_factory=OrderedDict
    )

    def key(self, case: RandomCase) -> OracleInvocationKey:
        return oracle_invocation_key(case)

    def execute(self, case: RandomCase) -> ExecutionResult:
        key = self.key(case)
        cached = self.accepted.get(key)
        if cached is not None:
            self.stats.accepted_cache_hits += 1
            return cached
        rejected = self.rejected.get(key)
        if rejected is not None:
            self.stats.rejected_cache_hits += 1
            self.rejected.move_to_end(key)
            return rejected
        start = perf_counter()
        result = run_num2words(case, self.function)
        self.stats.record(key, perf_counter() - start)
        if result.outcome == "text":
            self.accepted[key] = result
        else:
            self.rejected[key] = result
            while len(self.rejected) > self.rejected_cache_max:
                self.rejected.popitem(last=False)
        return result

    def supports(self, case: RandomCase) -> bool:
        return self.execute(case).outcome == "text"


__all__ = [
    "REJECTED_CACHE_MAX",
    "SLOWEST_CALLS_KEPT",
    "OracleInvocationKey",
    "OracleRunner",
    "OracleRuntimeStats",
    "oracle_invocation_key",
]
