"""Wapiti adapter — signature only.

Wapiti complements Nikto with active web-app vulnerability checks.
EU-origin (French) tooling, fits the sovereignty-first bias.
"""

from __future__ import annotations


async def scan(endpoints: list[str]) -> list[str]:
    """Run Wapiti against each endpoint; return artifact paths."""
    raise NotImplementedError("wapiti adapter not yet implemented")
