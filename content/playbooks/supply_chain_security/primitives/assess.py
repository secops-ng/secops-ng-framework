"""Supplier-signal assessment primitive (assess-supplier-signal).

Canonicalises the operator-supplied raw supply-chain signal envelope
into the closed ``assessment`` block the F-WF-SCS workflow consumes
downstream:

* ``verdict`` — one of ``no_impact``, ``watch``,
  ``confirmed_compromise``. Pinned vocabulary; ``unknown`` is not a
  valid sink because the assessment is meant to be acted on (the
  upstream feed-tier may carry an ``unknown`` signal, but the verdict
  this primitive emits is the operator-side disposition).
* ``affected_supplier_handle`` — ``provider.<id>@v<n>`` shape, mirrors
  the ``schemas/evidence/supply-chain.schema.json`` provider-id
  vocabulary so the artifact-emit downstream can carry the same
  handle without re-canonicalisation.
* ``affected_component_set`` — sorted, deduplicated list of PURL
  pointers (``pkg:<type>/<namespace>/<name>@<version>``-shape) for
  the components implicated on this execution. Empty list is valid
  and means "the verdict is ``no_impact`` or the signal is purely
  supplier-level (not component-level)".
* ``received_at`` — ISO-8601 UTC second-precision timestamp pinned by
  the upstream signal source (not derived here; no clock reads).
* ``signal_class`` — short operator-defined token classifying the
  signal source (``sbom_diff``, ``supplier_attestation``,
  ``upstream_advisory``, ``threat_intel``, ``operator_report``).
  Validated against the closed vocabulary so a free-text signal
  class fails loud here rather than at the artifact-emit boundary.

The operator's compile target performs the upstream I/O — signal-feed
ingestion, SBOM correlation against the operator's component
inventory, supplier-attestation lookup, verdict scoring. This
primitive is the shape-and-discipline gate at the step boundary; the
real policy lives in operator-side configuration, not in the
framework.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  Inputs are JSON-native; output is a JSON-native dict ready for the
  ``build_supply_chain_evidence_artifact`` primitive call downstream.
* **Sovereign-stack neutral.** No vendor signal-feed SDK is imported;
  the signal envelope is opaque operator-side JSON.
* **Public-bar safe.** ``affected_supplier_handle`` is matched
  against the same ``provider.<id>@v<n>`` regex the F-CP-03 schema
  pins, so a personal-name or contact-shaped supplier reference
  fails loud here.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidSupplierSignalError",
    "assess_supplier_signal",
]


_ALLOWED_VERDICTS = frozenset({"no_impact", "watch", "confirmed_compromise"})
_ALLOWED_SIGNAL_CLASSES = frozenset(
    {
        "sbom_diff",
        "supplier_attestation",
        "upstream_advisory",
        "threat_intel",
        "operator_report",
    }
)

# Mirrors compilers/_shared/evidence/supply_chain.py::_PROVIDER_ID_RE so
# the same handle round-trips into the F-CP-03 artifact-emit downstream
# without re-canonicalisation.
_PROVIDER_ID_RE = re.compile(
    r"^provider\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)

# Conservative PURL regex per https://github.com/package-url/purl-spec.
# Matches scheme + type + (optional namespace) + name + (optional
# version / qualifiers / subpath). The schema does not yet pin a
# component-set vocabulary; this primitive is the canonical gate.
_PURL_RE = re.compile(
    r"^pkg:[A-Za-z][A-Za-z0-9.+-]*"
    r"(/[A-Za-z0-9._~%-]+)*"
    r"/[A-Za-z0-9._~%-]+"
    r"(@[A-Za-z0-9._~%:+-]+)?"
    r"(\?[A-Za-z0-9._~%=&-]+)?"
    r"(#[A-Za-z0-9._~%/-]+)?$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class InvalidSupplierSignalError(ValueError):
    """Raised when the raw signal cannot produce a valid assessment block."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidSupplierSignalError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidSupplierSignalError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidSupplierSignalError(
            f"{field} {text!r} is not ISO-8601 UTC "
            "'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _validate_component_set(components: object) -> list[str]:
    if components is None:
        return []
    if not isinstance(components, list):
        raise InvalidSupplierSignalError(
            f"affected_component_set must be a list, got "
            f"{type(components).__name__}"
        )
    seen: set[str] = set()
    out: list[str] = []
    for index, value in enumerate(components):
        if not isinstance(value, str):
            raise InvalidSupplierSignalError(
                f"affected_component_set[{index}] must be a string, got "
                f"{type(value).__name__}"
            )
        normalised = unicodedata.normalize("NFKC", value).strip()
        if not normalised:
            raise InvalidSupplierSignalError(
                f"affected_component_set[{index}] is empty after "
                "canonicalisation"
            )
        if len(normalised) > 500 or not _PURL_RE.match(normalised):
            raise InvalidSupplierSignalError(
                f"affected_component_set[{index}] {value!r} is not a "
                "valid PURL (pkg:<type>/<namespace?>/<name>@<version?>)"
            )
        if normalised in seen:
            continue
        seen.add(normalised)
        out.append(normalised)
    out.sort()
    return out


def assess_supplier_signal(
    signal_class: str,
    verdict: str,
    affected_supplier_handle: str,
    received_at: str,
    affected_component_set: list | None = None,
    signal_id: str | None = None,
    scoring_notes: str | None = None,
) -> dict:
    """Canonicalise a raw supply-chain signal into the assessment block.

    Inputs
    ------
    signal_class
        One of ``sbom_diff``, ``supplier_attestation``,
        ``upstream_advisory``, ``threat_intel``, ``operator_report``.
        Classifies the source feed the upstream runtime read on this
        execution. Free text is rejected.
    verdict
        One of ``no_impact``, ``watch``, ``confirmed_compromise`` —
        the operator-side disposition emitted by the scoring policy.
        ``unknown`` is intentionally not a valid sink at this layer.
    affected_supplier_handle
        Stable operator-side supplier id in ``provider.<id>@v<n>``
        shape. Mirrors the F-CP-03 ``dependencies[].provider_id``
        vocabulary so the assessment round-trips into the
        supply-chain-evidence artifact without re-canonicalisation.
        Personal names and contact-shaped strings fail at the regex
        boundary per the public-bar discipline.
    received_at
        ISO-8601 UTC second-precision timestamp (``...Z``) pinned by
        the upstream signal source. No clock reads here.
    affected_component_set
        Optional JSON-native list of PURL pointers
        (``pkg:<type>/<namespace?>/<name>@<version?>``). Dedups
        exact-match repeats and sorts so two replays of the same
        signal collapse to byte-identical bytes. Defaults to ``[]``
        which is valid for supplier-level signals.
    signal_id
        Optional opaque operator-side signal identifier (free string,
        ``<= 200`` chars) for cross-referencing back to the source
        feed entry.
    scoring_notes
        Optional short operator-side rationale (``<= 400`` chars) for
        the scoring decision. Free text is allowed but bounded.

    Returns
    -------
    JSON-native dict with the closed assessment shape:
    ``{verdict, affected_supplier_handle, affected_component_set,
    received_at, signal_class, signal_id?, scoring_notes?}``. Sorted
    keys are not enforced here; the artifact-emit primitive
    downstream canonicalises the serialisation.
    """
    klass = _canonical_text(signal_class, "signal_class")
    if klass not in _ALLOWED_SIGNAL_CLASSES:
        raise InvalidSupplierSignalError(
            f"signal_class {signal_class!r} is not one of "
            f"{sorted(_ALLOWED_SIGNAL_CLASSES)!r}"
        )

    vtext = _canonical_text(verdict, "verdict")
    if vtext not in _ALLOWED_VERDICTS:
        raise InvalidSupplierSignalError(
            f"verdict {verdict!r} is not one of "
            f"{sorted(_ALLOWED_VERDICTS)!r}; the assessment block does "
            "not carry an 'unknown' sink at this layer"
        )

    handle = _canonical_text(
        affected_supplier_handle, "affected_supplier_handle"
    )
    if len(handle) > 200 or not _PROVIDER_ID_RE.match(handle):
        raise InvalidSupplierSignalError(
            f"affected_supplier_handle {affected_supplier_handle!r} "
            "does not match the provider.<id>@v<n> shape pinned by the "
            "F-CP-03 schema"
        )

    received_text = _require_iso_z(received_at, "received_at")
    components = _validate_component_set(affected_component_set)

    out: dict = {
        "verdict": vtext,
        "affected_supplier_handle": handle,
        "affected_component_set": components,
        "received_at": received_text,
        "signal_class": klass,
    }

    if signal_id is not None:
        sid = _canonical_text(signal_id, "signal_id")
        if len(sid) > 200:
            raise InvalidSupplierSignalError(
                "signal_id must be <= 200 chars when present"
            )
        out["signal_id"] = sid

    if scoring_notes is not None:
        notes = _canonical_text(scoring_notes, "scoring_notes")
        if len(notes) > 400:
            raise InvalidSupplierSignalError(
                "scoring_notes must be <= 400 chars when present"
            )
        out["scoring_notes"] = notes

    return out
