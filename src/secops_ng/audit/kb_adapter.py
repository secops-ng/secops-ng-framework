"""Sovereign-provider knowledge base lookup adapter.

The posture audit pipeline needs to translate a ``(declared_provider,
region)`` pair from a :class:`~secops_ng.audit.manifest.CloudFootprintManifest`
into a sovereignty verdict (sovereign, non-sovereign, partial, or
unknown). The translation is data-driven: the canonical KB lives in a
private sibling repository and may eventually be served from a sovereign
API. To keep the audit code testable and storage-agnostic, all KB access
goes through a thin :class:`KBAdapter` Protocol.

This module defines:

* :class:`SovereigntyVerdict` — closed enum of verdict states the audit
  layer can pattern-match against.
* :class:`KBLookupResult` — immutable value object pairing a verdict
  with an explanatory reason code.
* :class:`KBAdapter` — Protocol describing the lookup contract.
* :class:`FileBackedKBAdapter` — reference implementation that loads a
  JSON fixture at construction time and serves lookups from an
  in-memory index.

The file-backed adapter is intended for tests and small offline
demonstrations. Production deployments will provide their own adapter
implementations (HTTP, database) without touching downstream audit
code.

JSON fixture schema (version 1)::

    {
      "version": 1,
      "providers": [
        {
          "slug": "eu-provider-alpha",
          "label": "EU Provider Alpha",
          "regions": [
            {"id": "eu-west-1", "verdict": "sovereign",
             "reason": "eu-hosted-eu-owned"},
            {"id": "*",         "verdict": "sovereign",
             "reason": "eu-hosted-eu-owned"}
          ]
        }
      ]
    }

Region matching is exact-first, then falls back to a literal ``"*"``
wildcard entry if the provider declares one. If a provider declares
multiple non-wildcard entries for the same region id, the lookup
returns an ``AMBIGUOUS`` verdict rather than guessing — the KB curator
is expected to resolve the conflict.

Misses are returned as distinct verdict states (``UNKNOWN_PROVIDER``,
``UNKNOWN_REGION``) rather than raised as exceptions: a miss is a
normal audit signal, not an error.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable


class SovereigntyVerdict(StrEnum):
    """Closed set of sovereignty verdicts the audit layer understands.

    The string values are stable and may be serialised into reports.
    """

    SOVEREIGN = "sovereign"
    """EU-hosted and EU-owned/operated under EU law."""

    PARTIAL = "partial"
    """EU-hosted but non-EU control plane, or similar mixed posture."""

    NON_SOVEREIGN = "non_sovereign"
    """Hosted or operated outside EU sovereignty guarantees."""

    UNKNOWN_PROVIDER = "unknown_provider"
    """Provider slug is not present in the KB."""

    UNKNOWN_REGION = "unknown_region"
    """Provider is known, but the region is not catalogued and no
    wildcard fallback is declared."""

    AMBIGUOUS = "ambiguous"
    """The KB declares multiple conflicting entries for the same
    ``(provider, region)`` pair. Curator intervention required."""


@dataclass(frozen=True)
class KBLookupResult:
    """Immutable result of a KB lookup.

    ``reason`` is a short machine-readable code (e.g.
    ``"eu-hosted-eu-owned"``, ``"provider-not-in-kb"``) that downstream
    reports can map to human-readable explanations. It is always set
    so consumers never have to special-case ``None``.
    """

    verdict: SovereigntyVerdict
    reason: str


_REASON_UNKNOWN_PROVIDER = "provider-not-in-kb"
_REASON_UNKNOWN_REGION = "region-not-in-kb"
_REASON_AMBIGUOUS = "ambiguous-region-entries"
_REASON_DEFAULT_HIT = "kb-entry"


@runtime_checkable
class KBAdapter(Protocol):
    """Lookup contract for sovereign-provider knowledge bases.

    Implementations must be safe to call concurrently from multiple
    Temporal activities. They must never raise on a miss — misses are
    represented as :class:`SovereigntyVerdict` states on the returned
    :class:`KBLookupResult`.
    """

    def lookup(self, declared_provider: str, region: str) -> KBLookupResult:
        """Return a verdict for ``(declared_provider, region)``.

        Provider slugs and region identifiers are compared
        case-insensitively after stripping surrounding whitespace.
        """
        ...


class KBLoadError(ValueError):
    """Raised when a KB fixture cannot be read or its shape is invalid.

    This is distinct from a lookup miss: load errors indicate the
    adapter cannot be constructed, while misses are a normal lookup
    outcome.
    """


class FileBackedKBAdapter:
    """KB adapter backed by a JSON fixture loaded at construction time.

    The fixture is read once and indexed in memory; subsequent lookups
    do no I/O. Intended for tests, local development, and small offline
    demonstrations — production deployments will substitute a remote
    adapter that implements the same :class:`KBAdapter` Protocol.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._index: dict[str, dict[str, list[KBLookupResult]]] = {}
        self._load()

    @property
    def path(self) -> Path:
        """Path the adapter was constructed from."""
        return self._path

    def _load(self) -> None:
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise KBLoadError(f"could not read KB fixture {self._path}: {exc}") from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise KBLoadError(f"invalid JSON in {self._path}: {exc}") from exc

        if not isinstance(data, dict):
            raise KBLoadError(
                f"KB root must be a mapping, got {type(data).__name__}"
            )
        version = data.get("version")
        if version != 1:
            raise KBLoadError(f"unsupported KB version: {version!r} (expected 1)")
        providers = data.get("providers")
        if not isinstance(providers, list):
            raise KBLoadError("KB 'providers' must be a list")

        for entry in providers:
            if not isinstance(entry, dict):
                raise KBLoadError("each provider entry must be a mapping")
            slug = entry.get("slug")
            if not isinstance(slug, str) or not slug.strip():
                raise KBLoadError(f"provider entry missing 'slug': {entry!r}")
            regions = entry.get("regions")
            if not isinstance(regions, list):
                raise KBLoadError(
                    f"provider {slug!r}: 'regions' must be a list"
                )

            provider_key = slug.strip().lower()
            region_index: dict[str, list[KBLookupResult]] = {}
            for region_entry in regions:
                if not isinstance(region_entry, dict):
                    raise KBLoadError(
                        f"provider {slug!r}: each region entry must be a mapping"
                    )
                region_id = region_entry.get("id")
                verdict_raw = region_entry.get("verdict")
                reason = region_entry.get("reason", _REASON_DEFAULT_HIT)
                if not isinstance(region_id, str) or not region_id.strip():
                    raise KBLoadError(
                        f"provider {slug!r}: region entry missing 'id'"
                    )
                if not isinstance(verdict_raw, str):
                    raise KBLoadError(
                        f"provider {slug!r}: region {region_id!r} missing 'verdict'"
                    )
                try:
                    verdict = SovereigntyVerdict(verdict_raw)
                except ValueError as exc:
                    raise KBLoadError(
                        f"provider {slug!r}: region {region_id!r} has "
                        f"unknown verdict {verdict_raw!r}"
                    ) from exc
                # The "miss" verdicts are not legitimate KB content —
                # they are reserved for lookup-time states.
                if verdict in (
                    SovereigntyVerdict.UNKNOWN_PROVIDER,
                    SovereigntyVerdict.UNKNOWN_REGION,
                    SovereigntyVerdict.AMBIGUOUS,
                ):
                    raise KBLoadError(
                        f"provider {slug!r}: region {region_id!r} uses "
                        f"reserved verdict {verdict_raw!r}"
                    )
                if not isinstance(reason, str) or not reason.strip():
                    raise KBLoadError(
                        f"provider {slug!r}: region {region_id!r} has "
                        f"empty 'reason'"
                    )

                region_key = region_id.strip().lower()
                region_index.setdefault(region_key, []).append(
                    KBLookupResult(verdict=verdict, reason=reason)
                )
            self._index[provider_key] = region_index

    def lookup(self, declared_provider: str, region: str) -> KBLookupResult:
        provider_key = declared_provider.strip().lower()
        region_key = region.strip().lower()

        provider = self._index.get(provider_key)
        if provider is None:
            return KBLookupResult(
                verdict=SovereigntyVerdict.UNKNOWN_PROVIDER,
                reason=_REASON_UNKNOWN_PROVIDER,
            )

        # Exact-region match wins over wildcard.
        entries = provider.get(region_key)
        if entries is None:
            wildcard = provider.get("*")
            if wildcard is None:
                return KBLookupResult(
                    verdict=SovereigntyVerdict.UNKNOWN_REGION,
                    reason=_REASON_UNKNOWN_REGION,
                )
            entries = wildcard

        if len(entries) > 1:
            return KBLookupResult(
                verdict=SovereigntyVerdict.AMBIGUOUS,
                reason=_REASON_AMBIGUOUS,
            )
        return entries[0]


__all__ = [
    "FileBackedKBAdapter",
    "KBAdapter",
    "KBLoadError",
    "KBLookupResult",
    "SovereigntyVerdict",
]
