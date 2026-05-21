"""Minimal DefectDojo API client.

Conventions:

* one Product per target (created on first run)
* one Engagement per scan run (created each time)
* artifacts are reimported (not imported) so findings dedupe across runs

All configuration is sourced from the environment — never hardcoded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class DefectDojoClient:
    """Client for the DefectDojo REST API.

    Implementation is intentionally minimal at this stage; the public
    surface (`from_env`, `reimport`) is what the workflow depends on.
    Full wire-up is follow-on work tracked separately.
    """

    base_url: str
    api_token: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> DefectDojoClient:
        url = os.environ.get("DEFECTDOJO_URL", "").rstrip("/")
        token = os.environ.get("DEFECTDOJO_API_TOKEN", "")
        if not url or not token:
            raise RuntimeError(
                "DEFECTDOJO_URL and DEFECTDOJO_API_TOKEN must be set in the environment"
            )
        return cls(base_url=url, api_token=token)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self.api_token}"}

    async def reimport(
        self,
        target: str,
        artifacts: list[str],
        engagement_name: str | None,
    ) -> int | None:
        """Upload ``artifacts`` to the engagement for ``target``.

        Signature only — full implementation is follow-on work. Returns
        the engagement id when wired up.
        """
        _ = (target, artifacts, engagement_name, httpx)  # keep imports honest
        raise NotImplementedError("defectdojo reimport not yet implemented")
