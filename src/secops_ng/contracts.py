"""Typed I/O contracts for SecOps-NG tools, activities, and workflows.

Every value that crosses a workflow / activity / agent / tool boundary should
be a subclass of :class:`ToolIO`. Strict mode is enabled so that loose data
from external systems fails fast at the boundary rather than corrupting
durable workflow state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["low", "medium", "high", "critical"]


class ToolIO(BaseModel):
    """Base class for all typed I/O contracts in SecOps-NG.

    Subclass this for every tool input, tool output, activity argument, and
    activity return value. Strict mode means string coercion is off — callers
    must hand in the right types.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        validate_assignment=True,
    )


class VulnerabilityFinding(ToolIO):
    """A single vulnerability finding observed on an asset.

    This is the canonical example of the I/O-contract pattern: a Pydantic
    model that flows through workflows and activities as immutable, typed
    state.
    """

    id: str
    severity: Severity
    cve: str | None
    asset: str
    discovered_at: datetime
