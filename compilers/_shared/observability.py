"""Shared OpenTelemetry / audit-mirror source-emit helpers for the reference compilers.

Both the LangGraph and Temporal emitters wrap their generated nodes and tool
calls with OpenTelemetry spans and a parallel audit-trail mirror. To keep span
naming, attribute keys, and the audit collector identical across compile
targets — so a playbook that runs against either target produces structurally
compatible telemetry — those bits live here as **pure string-emit helpers**.

Design notes
------------
* This module is runtime-free. It never imports ``opentelemetry`` at module
  top level; the ``opentelemetry`` import only appears in the **emitted**
  source returned by :func:`render_otel_imports`. The framework therefore
  builds and tests without an OTel SDK installed.
* Output is deterministic — every helper that consumes a mapping iterates
  keys in sorted order so the same spec yields byte-identical source.
* The helpers produce *fragments* (already-indented blocks) intended to be
  inserted into a larger generated module by the compiler. They never wrap a
  whole file on their own.
* Vendor neutrality: no commercial APM SDK is emitted or referenced.
  Operators wire their own OTLP exporter at runtime; the emitted code only
  talks to the OTel API surface.

Public API:
    - Attribute-key constants (``SPAN_ATTR_*``)
    - :class:`SpanSpec`
    - :func:`render_otel_imports`
    - :func:`render_audit_mirror_imports`
    - :func:`emit_node_span_block`
    - :func:`emit_tool_span_block`
    - :func:`render_audit_mirror_module`
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Span attribute keys
#
# Stable string constants shared by every compile target. Both the LangGraph
# and Temporal emitters MUST attach attributes under these keys so a downstream
# OTel consumer can correlate spans regardless of which compiler produced
# them. Add new keys at the bottom — do not reorder, the test pins the tuple.
# ---------------------------------------------------------------------------

SPAN_ATTR_PLAYBOOK_ID = "secops_ng.playbook.id"
SPAN_ATTR_PLAYBOOK_VERSION = "secops_ng.playbook.version"
SPAN_ATTR_STEP_ID = "secops_ng.step.id"
SPAN_ATTR_STEP_NAME = "secops_ng.step.name"
SPAN_ATTR_STEP_TYPE = "secops_ng.step.type"
SPAN_ATTR_WORKFLOW_RUN_ID = "secops_ng.workflow.run_id"
SPAN_ATTR_COMPILE_TARGET = "secops_ng.compile.target"
SPAN_ATTR_TOOL_NAME = "secops_ng.tool.name"
SPAN_ATTR_TOOL_KIND = "secops_ng.tool.kind"
SPAN_ATTR_INPUT_SCHEMA = "secops_ng.io.input_schema"
SPAN_ATTR_OUTPUT_SCHEMA = "secops_ng.io.output_schema"

#: Canonical, ordered list of attribute keys this module exports. The unit
#: tests snapshot this tuple — adding a key is fine, reordering or renaming
#: is a breaking change for downstream span consumers and will fail CI.
SPAN_ATTR_KEYS: tuple[str, ...] = (
    SPAN_ATTR_PLAYBOOK_ID,
    SPAN_ATTR_PLAYBOOK_VERSION,
    SPAN_ATTR_STEP_ID,
    SPAN_ATTR_STEP_NAME,
    SPAN_ATTR_STEP_TYPE,
    SPAN_ATTR_WORKFLOW_RUN_ID,
    SPAN_ATTR_COMPILE_TARGET,
    SPAN_ATTR_TOOL_NAME,
    SPAN_ATTR_TOOL_KIND,
    SPAN_ATTR_INPUT_SCHEMA,
    SPAN_ATTR_OUTPUT_SCHEMA,
)


# ---------------------------------------------------------------------------
# Span spec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpanSpec:
    """Description of a single span the emitter wants to wrap a body in.

    Attributes are str→(str|int|float|bool) — the subset of attribute value
    types the OTel spec recommends for cross-vendor portability. ``None``
    values are dropped at emit time rather than serialised as the literal
    string "None".
    """

    span_name: str
    attributes: Mapping[str, str | int | float | bool | None] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------


def _py_repr(value: str | int | float | bool | None) -> str:
    """Return a deterministic Python literal for an attribute value."""
    # ``repr`` is deterministic for these primitive types across CPython
    # versions we support (3.11+); booleans render as True/False, strings get
    # quoted with escapes, ints/floats round-trip.
    return repr(value)


def _format_attributes_literal(attributes: Mapping[str, str | int | float | bool | None]) -> str:
    """Render an attributes mapping as a dict literal, keys sorted, Nones dropped.

    Empty mapping renders as ``{}`` (not omitted) so callers can rely on the
    keyword being present in the emitted ``start_as_current_span(...)`` call.
    """
    items = sorted((k, v) for k, v in attributes.items() if v is not None)
    if not items:
        return "{}"
    inner = ", ".join(f"{_py_repr(k)}: {_py_repr(v)}" for k, v in items)
    return "{" + inner + "}"


def render_otel_imports() -> str:
    """Return the canonical OpenTelemetry import block emitted code should use.

    Only the OTel **API** is imported — never a vendor SDK. The emitted module
    obtains a tracer via ``trace.get_tracer(__name__)`` so the operator picks
    the exporter (OTLP, console, none) at runtime by configuring the global
    TracerProvider out-of-band. Trailing newline so callers can splice into
    a header block without worrying about delimiters.
    """
    return "from opentelemetry import trace\n\n_TRACER = trace.get_tracer(__name__)\n"


def render_audit_mirror_imports() -> str:
    """Return the import line emitted code uses to reach the audit collector.

    The audit-mirror module is generated alongside the compiled artifact (see
    :func:`render_audit_mirror_module`) and is imported by sibling modules
    under the package-relative name ``_audit_mirror``.
    """
    return "from ._audit_mirror import AuditRecord, AuditTrail\n"


def emit_node_span_block(
    spec: SpanSpec,
    body_source: str,
    *,
    indent: str = "    ",
) -> str:
    """Wrap a node body in a ``with _TRACER.start_as_current_span(...)`` block.

    Parameters
    ----------
    spec:
        Span name + attributes. Attributes are emitted in sorted-key order.
    body_source:
        Source text for the body. May be multi-line; each non-empty line is
        re-indented one level deeper than ``indent``. Empty lines are
        preserved (no trailing whitespace).
    indent:
        The indentation of the *with* statement itself. The body is indented
        one further level (four extra spaces) inside it.

    The returned block also appends an :class:`AuditRecord` to the surrounding
    audit trail so audit holds even when no OTel exporter is configured.
    """
    attrs_literal = _format_attributes_literal(spec.attributes)
    name_lit = _py_repr(spec.span_name)
    inner_indent = indent + "    "
    body = _reindent(body_source, inner_indent)
    lines = [
        f"{indent}with _TRACER.start_as_current_span(",
        f"{indent}    name={name_lit},",
        f"{indent}    attributes={attrs_literal},",
        f"{indent}):",
        f"{inner_indent}AuditTrail.current().append(",
        f"{inner_indent}    AuditRecord(span_name={name_lit}, attributes={attrs_literal})",
        f"{inner_indent})",
        body,
    ]
    return "\n".join(lines) + "\n"


def emit_tool_span_block(
    spec: SpanSpec,
    body_source: str,
    *,
    indent: str = "    ",
) -> str:
    """Wrap a tool/child-call body in a child span.

    Structurally identical to :func:`emit_node_span_block` today, but kept
    separate so the two surfaces can diverge (tool spans may grow input/output
    payload-size attributes, etc.) without touching node-span emit sites.
    """
    return emit_node_span_block(spec, body_source, indent=indent)


def _reindent(source: str, indent: str) -> str:
    """Indent every non-empty line of ``source`` by ``indent``.

    Empty lines stay empty (no trailing whitespace) so the result still
    round-trips cleanly through ast.parse / unparse.
    """
    out_lines = []
    for line in source.splitlines():
        if line.strip():
            out_lines.append(indent + line)
        else:
            out_lines.append("")
    return "\n".join(out_lines)


# ---------------------------------------------------------------------------
# Audit-mirror runtime module
# ---------------------------------------------------------------------------

_AUDIT_MIRROR_SOURCE = '''\
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
'''


def render_audit_mirror_module() -> str:
    """Return the source of the audit-mirror module the compiler writes alongside its output.

    The module is dependency-free (stdlib only) so it can sit next to
    generated code in any deployment target. Same input → byte-identical
    output.
    """
    return _AUDIT_MIRROR_SOURCE


__all__ = [
    "SPAN_ATTR_PLAYBOOK_ID",
    "SPAN_ATTR_PLAYBOOK_VERSION",
    "SPAN_ATTR_STEP_ID",
    "SPAN_ATTR_STEP_NAME",
    "SPAN_ATTR_STEP_TYPE",
    "SPAN_ATTR_WORKFLOW_RUN_ID",
    "SPAN_ATTR_COMPILE_TARGET",
    "SPAN_ATTR_TOOL_NAME",
    "SPAN_ATTR_TOOL_KIND",
    "SPAN_ATTR_INPUT_SCHEMA",
    "SPAN_ATTR_OUTPUT_SCHEMA",
    "SPAN_ATTR_KEYS",
    "SpanSpec",
    "render_otel_imports",
    "render_audit_mirror_imports",
    "render_audit_mirror_module",
    "emit_node_span_block",
    "emit_tool_span_block",
]
