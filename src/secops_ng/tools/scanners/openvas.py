"""OpenVAS / Greenbone adapter — signature only.

OpenVAS is the EU-origin baseline scanner for network-level vulnerability
discovery. Integration is tracked as follow-on work.
"""

from __future__ import annotations


async def scan(target: str) -> list[str]:
    """Run an OpenVAS scan against ``target``; return artifact paths."""
    raise NotImplementedError("openvas adapter not yet implemented")
