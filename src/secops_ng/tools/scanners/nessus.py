"""Nessus adapter — signature only.

Nessus is supported as an optional commercial scanner for environments
that already have a licence; OpenVAS remains the sovereignty-first
default.
"""

from __future__ import annotations


async def scan(target: str) -> list[str]:
    """Run a Nessus scan against ``target``; return artifact paths."""
    raise NotImplementedError("nessus adapter not yet implemented")
