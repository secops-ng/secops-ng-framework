"""Evidence-bundle sealing primitive (preserve step).

Seals the NIS2 Article 23 evidence bundle: a closed manifest over the
four artifact kinds the step description enumerates (LLM API call
logs, credential-enumeration timeline, lateral-movement graph,
containment-action ledger), each an opaque store reference plus the
operator-computed SHA-256 of the stored artifact. The bundle id is
content-derived, so re-sealing the same evidence resolves to the same
``__evidence_bundle__`` — the downstream incident-management engine
can consume the id idempotently.

Design constraints
------------------

* **Pure / replayable.** The primitive never reads the artifacts; the
  evidence store adapter computes and supplies the digests. What is
  deterministic here is the manifest shape and the bundle identity.
* **Closed, complete artifact set.** All four kinds are required and
  no other kind is accepted — a bundle missing its lateral-movement
  graph would silently under-serve the notification chain, and an
  unknown kind is the caller mislabelling evidence.
* **Digest-conflict asymmetry (pinned by tests).** The same kind
  presented twice with an identical reference and digest collapses to
  one entry (idempotent re-presentation); the same kind with a
  *different* digest fails loud — conflicting evidence must never be
  silently resolved.
* **Joined by signal.** The manifest carries the escalation envelope's
  ``signal_id`` as the join key: the workflow escalates before it
  seals, so the bundle points at the case rather than the envelope
  pointing at the bundle.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "ConflictingEvidenceError",
    "IncompleteEvidenceError",
    "InvalidEvidenceInputError",
    "seal_evidence_bundle",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

_REQUIRED_KINDS = frozenset(
    {
        "llm_api_call_logs",
        "credential_enumeration_timeline",
        "lateral_movement_graph",
        "containment_action_ledger",
    }
)


class InvalidEvidenceInputError(ValueError):
    """Raised when an artifact entry cannot join a valid manifest."""


class IncompleteEvidenceError(ValueError):
    """Raised when a required artifact kind is missing."""


class ConflictingEvidenceError(ValueError):
    """Raised when one kind is presented with two different digests."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidEvidenceInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidEvidenceInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidEvidenceInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def seal_evidence_bundle(signal_id: str, artifacts: list) -> dict:
    """Seal the notification-chain evidence bundle for one case.

    Inputs
    ------
    signal_id
        The escalation envelope's ``signal_id`` — the join key the
        downstream incident-management engine correlates on.
    artifacts
        List of artifact entries, each an object with ``kind`` (one of
        ``llm_api_call_logs``, ``credential_enumeration_timeline``,
        ``lateral_movement_graph``, ``containment_action_ledger``),
        ``ref`` (role-shaped evidence-store pointer) and ``sha256``
        (64-hex digest of the stored artifact, any case — canonical
        form is lowercase). All four kinds must be present; identical
        re-presentations of a kind collapse.

    Returns
    -------
    JSON-native bundle manifest::

        {
            "bundle_id": "atr-evb-<24 hex>",
            "signal_id": "...",
            "artifacts": [
                {"kind": "...", "ref": "...", "sha256": "<64 hex>"},
                ...  # sorted by kind
            ]
        }
    """
    signal = _canonical_pointer(signal_id, "signal_id")

    if not isinstance(artifacts, list) or not artifacts:
        raise InvalidEvidenceInputError(
            "artifacts must be a non-empty list"
        )

    by_kind: dict[str, dict] = {}
    for index, artifact in enumerate(artifacts):
        field = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            raise InvalidEvidenceInputError(
                f"{field} must be an object, got {type(artifact).__name__}"
            )
        kind = artifact.get("kind")
        if not isinstance(kind, str) or kind not in _REQUIRED_KINDS:
            raise InvalidEvidenceInputError(
                f"{field}.kind {kind!r} is not one of "
                f"{sorted(_REQUIRED_KINDS)}"
            )
        ref = _canonical_pointer(artifact.get("ref"), f"{field}.ref")
        digest_raw = artifact.get("sha256")
        if not isinstance(digest_raw, str) or not _SHA256_RE.match(
            digest_raw.strip()
        ):
            raise InvalidEvidenceInputError(
                f"{field}.sha256 must be a 64-hex SHA-256 digest"
            )
        # Hex case is presentation, not identity: canonicalise to
        # lowercase before any comparison so AB.. and ab.. collapse.
        digest = digest_raw.strip().lower()

        entry = {"kind": kind, "ref": ref, "sha256": digest}
        if kind in by_kind:
            if by_kind[kind]["sha256"] != digest:
                raise ConflictingEvidenceError(
                    f"{field} presents kind {kind!r} with digest "
                    f"{digest!r} after {by_kind[kind]['sha256']!r}; "
                    "conflicting evidence must not be silently resolved"
                )
            if by_kind[kind]["ref"] != ref:
                raise ConflictingEvidenceError(
                    f"{field} presents kind {kind!r} at ref {ref!r} after "
                    f"{by_kind[kind]['ref']!r}; conflicting evidence must "
                    "not be silently resolved"
                )
            continue
        by_kind[kind] = entry

    missing = _REQUIRED_KINDS - by_kind.keys()
    if missing:
        raise IncompleteEvidenceError(
            "evidence bundle is missing required artifact kinds: "
            + ", ".join(sorted(missing))
        )

    manifest = [by_kind[k] for k in sorted(by_kind)]
    digest = hashlib.sha256(
        (signal + "|" + json.dumps(manifest, sort_keys=True)).encode("utf-8")
    ).hexdigest()

    return {
        "bundle_id": "atr-evb-" + digest[:24],
        "signal_id": signal,
        "artifacts": manifest,
    }
