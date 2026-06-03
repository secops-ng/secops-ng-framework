"""Process-local audit-trail mirror emitted alongside the compiled artifact.

Every span the compiled module opens also appends an :class:`AuditRecord`
to a contextvar-scoped :class:`AuditTrail`. This guarantees audit data
holds even when no OpenTelemetry exporter is configured — useful for
operators running disconnected, sovereign, or air-gapped deployments
where OTLP egress is not available.

The trail is per-context, not per-process: each new asyncio task or
thread that does not explicitly bind the contextvar starts with its own
empty list, so concurrent workflow runs do not bleed into each other.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    """One audit row: the span name and its attributes at open time."""

    span_name: str
    attributes: dict[str, Any] = field(default_factory=dict)


_TRAIL: ContextVar[list[AuditRecord]] = ContextVar("secops_ng_audit_trail")


class AuditTrail:
    """Context-local collector of :class:`AuditRecord` rows.

    Construct via :meth:`current`. Records are kept in append order;
    :meth:`snapshot` returns a defensive copy so consumers cannot mutate
    the underlying list out from under in-flight emitters.
    """

    def __init__(self, records: list[AuditRecord]) -> None:
        self._records = records

    @classmethod
    def current(cls) -> "AuditTrail":
        try:
            records = _TRAIL.get()
        except LookupError:
            records = []
            _TRAIL.set(records)
        return cls(records)

    def append(self, record: AuditRecord) -> None:
        self._records.append(record)

    def snapshot(self) -> list[AuditRecord]:
        return list(self._records)
