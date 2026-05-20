"""Nikto adapter — signature only.

Nikto is the lightweight HTTP fingerprinting scanner. It runs only
when http-discovery finds web endpoints.
"""

from __future__ import annotations


async def scan(endpoints: list[str]) -> list[str]:
    """Run Nikto against each endpoint; return artifact paths."""
    raise NotImplementedError("nikto adapter not yet implemented")
