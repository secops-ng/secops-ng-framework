"""Disclosure-timeline record stub builder (track-timeline).

Builds the public-bar-safe per-finding disclosure-timeline record stub
shaped against
``content/evidence/codebase-vuln-management/disclosure-timeline-record.schema.json``.
The full durable emitter wiring (artifact-path, content-addressed
filename, JSON-canonical write) is owned by the F-CP-05-equivalent
evidence-emitter slice; this primitive only produces the JSON-native
payload the per-target adapter consumes — exactly the input shape that
``compilers._shared.evidence.disclosure_timeline`` already accepts.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. Inputs
  are JSON-native; output is JSON-native; same inputs ⇒ byte-identical
  output.
* **Public-bar safe.** Source-data payload is not embedded — only the
  shape pointer (``kind`` + optional ``ocsf_class_uid`` / ``telemetry_ref``)
  travels through, per AGENTS.md §3 and the schema's
  ``source_data`` contract.
* **Determinism.** The record ``id`` is a SHA-256 hex digest of
  ``<workflow_id>|<sbom_content_hash>|<purl>|<advisory_id>`` (UTF-8,
  exact bytes, no separators around the pipes). Same finding ⇒ same id.
"""

from __future__ import annotations

import hashlib
import re

__all__ = [
    "InvalidDisclosureRecordError",
    "build_disclosure_timeline_stub",
]


_SCHEMA_VERSION = "0.1.0"
_STREAM = "codebase_vuln_management"
_WORKFLOW_ID = "codebase_vuln_management"
_WINDOWED_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
_ALLOWED_SOURCE_KINDS = frozenset({"ocsf", "telemetry", "none"})
_ISO_Z_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_POLICY_REF_PATTERN = re.compile(
    r"^policy\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_REF_VIZ_PATTERN = re.compile(
    r"^viz\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_PURL_PATTERN = re.compile(r"^pkg:[a-z][a-z0-9+.\-]*/")
_SBOM_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class InvalidDisclosureRecordError(ValueError):
    """Raised when the inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidDisclosureRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    if not value.strip():
        raise InvalidDisclosureRecordError(f"{field} is empty")
    return value


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_PATTERN.match(text):
        raise InvalidDisclosureRecordError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _validate_component(component: object) -> dict:
    if not isinstance(component, dict):
        raise InvalidDisclosureRecordError(
            f"component must be an object, got {type(component).__name__}"
        )
    purl = _require_str(component.get("purl"), "component.purl")
    if not _PURL_PATTERN.match(purl):
        raise InvalidDisclosureRecordError(
            f"component.purl {purl!r} is not a valid PURL"
        )
    version = _require_str(component.get("version"), "component.version")
    return {"purl": purl, "version": version}


def _validate_disclosure_window(window: object) -> dict:
    if not isinstance(window, dict):
        raise InvalidDisclosureRecordError(
            f"disclosure_window must be an object, got {type(window).__name__}"
        )
    policy_ref = _require_str(window.get("policy_ref"), "disclosure_window.policy_ref")
    if not _POLICY_REF_PATTERN.match(policy_ref):
        raise InvalidDisclosureRecordError(
            f"disclosure_window.policy_ref {policy_ref!r} does not match "
            "the policy stable-id pattern"
        )
    return {
        "policy_ref": policy_ref,
        "acknowledge_by": _require_iso_z(
            window.get("acknowledge_by"), "disclosure_window.acknowledge_by"
        ),
        "fix_by": _require_iso_z(
            window.get("fix_by"), "disclosure_window.fix_by"
        ),
        "disclose_by": _require_iso_z(
            window.get("disclose_by"), "disclosure_window.disclose_by"
        ),
    }


def _validate_source_data(source_data: object) -> dict:
    if not isinstance(source_data, dict):
        raise InvalidDisclosureRecordError(
            f"source_data must be an object, got {type(source_data).__name__}"
        )
    kind = source_data.get("kind")
    if kind not in _ALLOWED_SOURCE_KINDS:
        raise InvalidDisclosureRecordError(
            f"source_data.kind {kind!r} must be one of "
            f"{sorted(_ALLOWED_SOURCE_KINDS)!r}"
        )
    out: dict = {"kind": kind}
    if kind == "ocsf":
        ocsf_class_uid = source_data.get("ocsf_class_uid")
        if not isinstance(ocsf_class_uid, int) or isinstance(ocsf_class_uid, bool):
            raise InvalidDisclosureRecordError(
                "source_data.ocsf_class_uid must be an integer when kind == 'ocsf'"
            )
        if ocsf_class_uid < 0:
            raise InvalidDisclosureRecordError(
                "source_data.ocsf_class_uid must be non-negative"
            )
        out["ocsf_class_uid"] = ocsf_class_uid
    elif kind == "telemetry":
        out["telemetry_ref"] = _require_str(
            source_data.get("telemetry_ref"), "source_data.telemetry_ref"
        )
    return out


def build_disclosure_timeline_stub(
    finding: dict,
    disclosure_window: dict,
    captured_at: str,
    ref_viz: str,
    source_data: dict,
) -> dict:
    """Build one disclosure-timeline record stub from one normalised finding.

    Inputs
    ------
    finding
        One entry from :func:`...primitives.sbom.normalise_findings`,
        carrying ``advisory_id``, ``purl``, ``version``, ``severity``,
        and ``sbom_content_hash``.
    disclosure_window
        Output of :func:`...primitives.disclosure_window.resolve_disclosure_window`
        — ``policy_ref`` + the three ISO-Z deadline strings. Empty
        windows (``info`` / ``unknown`` severities) are rejected here
        because the schema enum only carries the four real bands.
    captured_at
        ISO-8601 UTC second-precision timestamp pinned by the assess-
        disclosure step at emission time.
    ref_viz
        Stable visualisation pointer, ``viz.<slug>@v<semver>``.
    source_data
        Public-bar-safe shape pointer for the underlying advisory
        payload. ``{"kind": "ocsf", "ocsf_class_uid": 2002}`` for the
        codebase-finding reference class; ``{"kind": "none"}`` is
        acceptable when no telemetry channel is wired.

    Returns
    -------
    JSON-native dict matching
    ``content/evidence/codebase-vuln-management/disclosure-timeline-record.schema.json``.
    """
    if not isinstance(finding, dict):
        raise InvalidDisclosureRecordError(
            f"finding must be an object, got {type(finding).__name__}"
        )

    advisory_id = _require_str(finding.get("advisory_id"), "finding.advisory_id")
    purl = _require_str(finding.get("purl"), "finding.purl")
    version = _require_str(finding.get("version"), "finding.version")
    severity = _require_str(finding.get("severity"), "finding.severity")
    if severity not in _WINDOWED_SEVERITIES:
        raise InvalidDisclosureRecordError(
            f"finding.severity {severity!r} is not one of "
            f"{sorted(_WINDOWED_SEVERITIES)!r}; info/unknown findings do "
            "not produce disclosure-timeline records"
        )
    sbom_content_hash = _require_str(
        finding.get("sbom_content_hash"), "finding.sbom_content_hash"
    )
    if not _SBOM_HASH_PATTERN.match(sbom_content_hash):
        raise InvalidDisclosureRecordError(
            "finding.sbom_content_hash must be a 64-char SHA-256 lower-hex string"
        )

    component = _validate_component({"purl": purl, "version": version})
    window = _validate_disclosure_window(disclosure_window)
    if any(window[key] == "" for key in ("acknowledge_by", "fix_by", "disclose_by")):
        raise InvalidDisclosureRecordError(
            "disclosure_window is empty — only severities critical/high/"
            "medium/low produce disclosure-timeline records"
        )

    captured_at_value = _require_iso_z(captured_at, "captured_at")
    ref_viz_value = _require_str(ref_viz, "ref_viz")
    if not _REF_VIZ_PATTERN.match(ref_viz_value):
        raise InvalidDisclosureRecordError(
            f"ref_viz {ref_viz_value!r} must match viz.<slug>@v<semver>"
        )
    source_data_value = _validate_source_data(source_data)

    identity_input = (
        f"{_WORKFLOW_ID}|{sbom_content_hash}|"
        f"{component['purl']}|{advisory_id}"
    ).encode("utf-8")
    record_id = hashlib.sha256(identity_input).hexdigest()

    return {
        "schema_version": _SCHEMA_VERSION,
        "id": record_id,
        "stream": _STREAM,
        "workflow_id": _WORKFLOW_ID,
        "sbom_content_hash": sbom_content_hash,
        "advisory_id": advisory_id,
        "component": component,
        "severity": severity,
        "disclosure_window": window,
        "source_data": source_data_value,
        "ref_viz": ref_viz_value,
        "captured_at": captured_at_value,
    }
