"""Process-local audit-trail mirror emitted alongside the compiled artifact.

Every span the compiled module opens also appends an :class:`AuditRecord`
to a contextvar-scoped :class:`AuditTrail`. This guarantees audit data
holds even when no OpenTelemetry exporter is configured — useful for
operators running disconnected, sovereign, or air-gapped deployments
where OTLP egress is not available.

The trail is per-context, not per-process: each new asyncio task or
thread that does not explicitly bind the contextvar starts with its own
empty list, so concurrent workflow runs do not bleed into each other.

The trail also knows how to render itself as a JSONL **envelope** (one
header line + one body line per record, in append order). The envelope
is the offline / air-gapped replay shape — see
``docs/observability/audit-mirror.md`` for the binding spec. Envelope
rendering is stdlib-only and deterministic: same input → byte-identical
bytes.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

#: Envelope schema version. Bump when the body-line shape changes
#: incompatibly. Header always carries this value verbatim.
ENVELOPE_SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class AuditRecord:
    """One audit row: the span name and its attributes at open time.

    ``attributes`` carries the deterministic attribute set the wrapping
    span recorded — workflow id, step id, run id, attempt, status, plus
    target-specific keys. Keys come straight from the
    ``SPAN_ATTR_*`` constants exported by the framework helper layer,
    so a record built from a langgraph-emitted span and a record built
    from a temporal-emitted span with the same logical data are equal.
    """

    span_name: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvelopeHeader:
    """Header line of a rendered audit envelope.

    Fields:
        workflow_id: stable identifier of the playbook / graph definition.
        run_id: identifier of this specific run.
        compile_target: ``"langgraph"`` or ``"temporal"`` (other targets
            may extend this in future). Stored verbatim; the helper does
            not validate the value.
        schema_version: defaults to :data:`ENVELOPE_SCHEMA_VERSION`.
    """

    workflow_id: str
    run_id: str
    compile_target: str
    schema_version: str = ENVELOPE_SCHEMA_VERSION


_TRAIL: ContextVar[list[AuditRecord]] = ContextVar("secops_ng_audit_trail")


def _record_key(record: AuditRecord) -> str:
    """Stable identity used for idempotent append dedup.

    Two records with the same span name and identical attribute set are
    considered the same logical event — replaying the same input yields
    the same key, so the second append is a no-op.
    """
    return json.dumps(
        {"span_name": record.span_name, "attributes": record.attributes},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _record_body_line(record: AuditRecord) -> str:
    """Render one body line of the envelope as deterministic JSON."""
    return json.dumps(
        {"span_name": record.span_name, "attributes": record.attributes},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _header_line(header: EnvelopeHeader) -> str:
    """Render the envelope header line as deterministic JSON."""
    return json.dumps(
        {
            "kind": "header",
            "schema_version": header.schema_version,
            "compile_target": header.compile_target,
            "workflow_id": header.workflow_id,
            "run_id": header.run_id,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


class AuditTrail:
    """Context-local collector of :class:`AuditRecord` rows.

    Construct via :meth:`current`. Records are kept in append order;
    :meth:`snapshot` returns a defensive copy so consumers cannot mutate
    the underlying list out from under in-flight emitters.

    :meth:`append` is **idempotent**: re-appending a record with the
    same identity (span name + attributes) is a no-op. This makes
    workflow replays — Temporal in particular — safe against double
    counting when the same activity is re-driven from history.
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
        key = _record_key(record)
        for existing in self._records:
            if _record_key(existing) == key:
                return
        self._records.append(record)

    def snapshot(self) -> list[AuditRecord]:
        return list(self._records)

    def render_envelope(self, header: EnvelopeHeader) -> bytes:
        """Render the trail as a JSONL envelope.

        One header line, one body line per record, in append order.
        Trailing newline on every line. Output is deterministic — same
        records + same header always produce byte-identical bytes — and
        contains nothing besides what the spec in
        ``docs/observability/audit-mirror.md`` binds.
        """
        lines = [_header_line(header)]
        for record in self._records:
            lines.append(_record_body_line(record))
        return ("\n".join(lines) + "\n").encode("utf-8")
