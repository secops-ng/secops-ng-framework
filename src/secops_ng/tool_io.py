"""Typed I/O contracts for SecOps-NG tools, activities, and graph nodes.

Every value that crosses a workflow node / tool / agent boundary should be a
subclass of :class:`ToolIO`. ``ToolIO`` is a Pydantic v2 ``BaseModel`` with
strict, immutable semantics:

* ``extra="forbid"`` — unknown fields fail loudly at the boundary instead of
  silently corrupting downstream state. This is non-negotiable for the
  NIS2-aligned audit trail: every field that flows through a workflow must be
  declared.
* ``frozen=True`` — models are hashable and cannot be mutated after
  construction. Graph nodes therefore return *new* state objects rather than
  mutating shared ones, which keeps LangGraph state transitions deterministic
  and replayable.

This module replaces the dataclass-based ``ToolIO`` from the pre-LangGraph
prototype. It is the canonical home for typed I/O contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["info", "low", "medium", "high", "critical"]
"""Canonical severity ladder used across the framework.

Note ``info`` is included here (it was absent from the pre-pivot enum) because
the DSPy severity-classification signature in
:mod:`secops_ng.workflows.vulnerability_triage` may emit ``info`` for findings
that turn out to be false positives or purely informational.
"""


class ToolIO(BaseModel):
    """Base class for all typed I/O contracts in SecOps-NG.

    Subclass this for every tool input, tool output, activity argument, and
    graph-node payload. The strict, frozen config means the boundary fails
    fast on unknown / malformed data and state objects stay immutable.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
    )


class VulnerabilityFinding(ToolIO):
    """A single vulnerability finding observed on an asset.

    Canonical example of the I/O-contract pattern: a Pydantic model that flows
    through workflows and tools as immutable, typed state.
    """

    id: str
    severity: Severity
    cve: str | None
    asset: str
    discovered_at: datetime
