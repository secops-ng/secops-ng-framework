"""Advisory-artifact primitive (publish_advisory).

Emits the pure JSON-native envelope the human-readable Markdown
advisory template and the CSAF 2.0 machine-readable advisory
template both render from. Template rendering (Jinja2) is owned by
the per-target compiler adapters (see
``compilers/{n8n,temporal,langgraph}``); this primitive only builds
the deterministic envelope dict.

The envelope is a CSAF 2.0 shape stub: the fields align with the
``advisory.csaf2.json.j2`` template so a single primitive call
produces the joint input for both the Markdown and CSAF 2.0
renderers without a second per-target reshape.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  ``disclosure_date_iso`` is supplied by the caller (typically from
  ``__disclosure_target_date__`` recorded at
  ``coordinate_disclosure``).
* **Determinism.** Same inputs => byte-identical output dict.
  ``affected_products`` and ``mitigations`` are normalised so any
  incoming ordering yields the same canonical output.
* **Public-bar safe.** All strings are canonicalised (NFKC + strip)
  and length-bounded; ``credit_display`` is carried verbatim (it
  either matches the reporter's opt-in attribution string or the
  literal anonymous marker per the coordinate_disclosure step's
  contract).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidAdvisoryArtifactError",
    "build_advisory_artifact",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "cra_cvd_advisory"

_ADVISORY_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:-]{0,63}$")
_CVE_ID_RE = re.compile(r"^CVE-[0-9]{4}-[0-9]{4,}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SEVERITY_LABELS = frozenset({"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"})
_TRACKING_STATUSES = frozenset({"final", "interim"})
_PRODUCT_ID_RE = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")
_BRANCH_STATUSES = frozenset({"affected", "fixed", "under_investigation"})
# CVSS v4.0 vector shape: starts with CVSS:4.0/AV:.../AC:.../... . Full
# grammar validation is out of scope; this is a schema-floor sanity
# check so an obvious free-text drift fails loud at this boundary.
_CVSS_V4_RE = re.compile(r"^CVSS:4\.0/[A-Z]+:[A-Z0-9]+(/[A-Z]+:[A-Z0-9]+)+$")


class InvalidAdvisoryArtifactError(ValueError):
    """Raised when the advisory inputs cannot produce a deterministic envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAdvisoryArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAdvisoryArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _canonical_optional_text(value: object, field: str) -> str:
    """Canonicalise a free-text string (may become empty after strip)."""
    if not isinstance(value, str):
        raise InvalidAdvisoryArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    return unicodedata.normalize("NFKC", value).strip()


def _require_iso_date(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_DATE_RE.match(text):
        raise InvalidAdvisoryArtifactError(
            f"{field} {text!r} is not ISO-8601 date 'YYYY-MM-DD'"
        )
    return text


def _validate_score(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidAdvisoryArtifactError(
            f"severity_score must be a number, got {type(value).__name__}"
        )
    score = float(value)
    if not (0.0 <= score <= 10.0):
        raise InvalidAdvisoryArtifactError(
            f"severity_score {score} must be within [0.0, 10.0]"
        )
    return score


def _validate_affected_products(value: object) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise InvalidAdvisoryArtifactError(
            "affected_products must be a non-empty list"
        )
    seen_product_ids: set[str] = set()
    out: list[dict] = []
    for i, row in enumerate(value):
        if not isinstance(row, dict):
            raise InvalidAdvisoryArtifactError(
                f"affected_products[{i}] must be an object"
            )
        pid = _canonical_text(row.get("product_id"), f"affected_products[{i}].product_id")
        if not _PRODUCT_ID_RE.match(pid):
            raise InvalidAdvisoryArtifactError(
                f"affected_products[{i}].product_id {pid!r} does not "
                "match the schema pattern"
            )
        if pid in seen_product_ids:
            raise InvalidAdvisoryArtifactError(
                f"affected_products has duplicate product_id {pid!r}"
            )
        seen_product_ids.add(pid)
        pname = _canonical_text(
            row.get("product_name"), f"affected_products[{i}].product_name"
        )
        raw_branches = row.get("branches")
        if not isinstance(raw_branches, list) or not raw_branches:
            raise InvalidAdvisoryArtifactError(
                f"affected_products[{i}].branches must be a non-empty list"
            )
        seen_versions: set[str] = set()
        norm_branches: list[dict] = []
        for j, br in enumerate(raw_branches):
            if not isinstance(br, dict):
                raise InvalidAdvisoryArtifactError(
                    f"affected_products[{i}].branches[{j}] must be an object"
                )
            version = _canonical_text(
                br.get("version"),
                f"affected_products[{i}].branches[{j}].version",
            )
            status = _canonical_text(
                br.get("status"),
                f"affected_products[{i}].branches[{j}].status",
            )
            if status not in _BRANCH_STATUSES:
                raise InvalidAdvisoryArtifactError(
                    f"affected_products[{i}].branches[{j}].status "
                    f"{status!r} is not in the closed alphabet "
                    f"{sorted(_BRANCH_STATUSES)!r}"
                )
            if version in seen_versions:
                raise InvalidAdvisoryArtifactError(
                    f"affected_products[{i}].branches has duplicate "
                    f"version {version!r}"
                )
            seen_versions.add(version)
            norm_branches.append({"version": version, "status": status})
        # Sort branches by version so upstream ordering does not leak
        # into the emitted advisory.
        norm_branches.sort(key=lambda b: b["version"])
        out.append(
            {
                "product_id": pid,
                "product_name": pname,
                "branches": norm_branches,
            }
        )
    # Sort products by product_id for determinism.
    out.sort(key=lambda r: r["product_id"])
    return out


def _validate_mitigations(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise InvalidAdvisoryArtifactError(
            f"mitigations must be a list, got {type(value).__name__}"
        )
    seen: set[str] = set()
    out: list[str] = []
    for i, item in enumerate(value):
        text = _canonical_text(item, f"mitigations[{i}]")
        if len(text) > 2000:
            raise InvalidAdvisoryArtifactError(
                f"mitigations[{i}] must be <= 2000 chars"
            )
        if text in seen:
            # Deduplicate silently -- the input contract is a set of
            # mitigations, not an ordered list.
            continue
        seen.add(text)
        out.append(text)
    # Deterministic order.
    out.sort()
    return out


def build_advisory_artifact(
    case_id: str,
    advisory_id: str,
    title: str,
    summary: str,
    impact: str,
    affected_products: list,
    severity_cvss_v4: str,
    severity_score: float,
    severity_label: str,
    fix_reference: str,
    credit_display: str,
    disclosure_date_iso: str,
    operator_display: str,
    operator_namespace: str,
    tracking_status: str = "final",
    cve_id: str | None = None,
    advisory_url: str | None = None,
    mitigations: list | None = None,
) -> dict:
    """Build the public-advisory envelope (CSAF 2.0 shape stub).

    Parameters mirror the F-WF-CRA-CVD ``publish_advisory`` core_body
    in-args (``case_id``, ``fix_reference``, ``disclosure_target_date``,
    ``reporter_credit_display``) plus the operator-side advisory
    content the template renders against.

    Args:
        case_id: Operator-assigned CVD case identifier (join key
            across the disclosure lifecycle).
        advisory_id: Operator-issued advisory identifier
            (``__advisory_id__``). Uppercase / digit shape.
        title: One-line vulnerability summary.
        summary: 1-3 sentence executive summary.
        impact: Plain-English impact statement.
        affected_products: Non-empty list of
            ``{product_id, product_name, branches:[{version, status}]}``
            rows. Sorted deterministically on output.
        severity_cvss_v4: Full CVSS v4.0 vector string.
        severity_score: Numeric base score in [0.0, 10.0].
        severity_label: One of ``NONE / LOW / MEDIUM / HIGH / CRITICAL``.
        fix_reference: Release / build id the fix ships in.
        credit_display: Reporter credit line, or the literal
            anonymous marker (``reporter chose to remain anonymous``)
            when the reporter has not opted in via the
            coordinate_disclosure consent capture. Carried verbatim.
        disclosure_date_iso: ISO-8601 date (``YYYY-MM-DD``) the
            advisory becomes public.
        operator_display: Publisher display name.
        operator_namespace: Publisher namespace (RFC 3986 URI).
        tracking_status: ``final`` (coordinated release) or
            ``interim`` (partial disclosure held on operator
            discretion).
        cve_id: Optional CVE identifier when a CNA has assigned one.
        advisory_url: Optional canonical URL of the operator's
            advisory listing.
        mitigations: Optional list of mitigation strings; deduplicated
            and sorted on output.

    Returns:
        JSON-native dict carrying ``schema_version``, ``stream``,
        ``case_id``, ``advisory_id``, ``tracking_status``, ``title``,
        ``summary``, ``impact``, ``affected_products``, ``severity``
        (``cvss_v4`` + ``score`` + ``label``), ``fix_reference``,
        ``credit_display``, ``disclosure_date``, ``publisher``
        (``display`` + ``namespace``), ``mitigations``, and the
        optional ``cve_id`` / ``advisory_url``.

    Raises:
        InvalidAdvisoryArtifactError: any input fails validation.
    """
    cid = _canonical_text(case_id, "case_id")

    aid = _canonical_text(advisory_id, "advisory_id")
    if not _ADVISORY_ID_RE.match(aid):
        raise InvalidAdvisoryArtifactError(
            f"advisory_id {advisory_id!r} does not match the schema pattern"
        )

    status = _canonical_text(tracking_status, "tracking_status")
    if status not in _TRACKING_STATUSES:
        raise InvalidAdvisoryArtifactError(
            f"tracking_status {status!r} is not in the closed alphabet "
            f"{sorted(_TRACKING_STATUSES)!r}"
        )

    title_text = _canonical_text(title, "title")
    if len(title_text) > 300:
        raise InvalidAdvisoryArtifactError("title must be <= 300 chars")
    summary_text = _canonical_text(summary, "summary")
    if len(summary_text) > 2000:
        raise InvalidAdvisoryArtifactError("summary must be <= 2000 chars")
    impact_text = _canonical_text(impact, "impact")
    if len(impact_text) > 2000:
        raise InvalidAdvisoryArtifactError("impact must be <= 2000 chars")

    products = _validate_affected_products(affected_products)

    vector = _canonical_text(severity_cvss_v4, "severity_cvss_v4")
    if not _CVSS_V4_RE.match(vector):
        raise InvalidAdvisoryArtifactError(
            f"severity_cvss_v4 {severity_cvss_v4!r} does not look like a "
            "CVSS v4.0 vector"
        )
    score = _validate_score(severity_score)
    label = _canonical_text(severity_label, "severity_label").upper()
    if label not in _SEVERITY_LABELS:
        raise InvalidAdvisoryArtifactError(
            f"severity_label {label!r} is not in the closed alphabet "
            f"{sorted(_SEVERITY_LABELS)!r}"
        )

    fix_ref = _canonical_text(fix_reference, "fix_reference")
    if len(fix_ref) > 300:
        raise InvalidAdvisoryArtifactError("fix_reference must be <= 300 chars")

    credit = _canonical_optional_text(credit_display, "credit_display")
    if not credit:
        raise InvalidAdvisoryArtifactError(
            "credit_display is empty; the coordinate_disclosure step "
            "must populate either the opted-in attribution string or "
            "the literal anonymous marker."
        )
    if len(credit) > 400:
        raise InvalidAdvisoryArtifactError("credit_display must be <= 400 chars")

    disclosure_date = _require_iso_date(disclosure_date_iso, "disclosure_date_iso")

    op_display = _canonical_text(operator_display, "operator_display")
    op_ns = _canonical_text(operator_namespace, "operator_namespace")

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "case_id": cid,
        "advisory_id": aid,
        "tracking_status": status,
        "title": title_text,
        "summary": summary_text,
        "impact": impact_text,
        "affected_products": products,
        "severity": {
            "cvss_v4": vector,
            "score": score,
            "label": label,
        },
        "fix_reference": fix_ref,
        "credit_display": credit,
        "disclosure_date": disclosure_date,
        "publisher": {
            "display": op_display,
            "namespace": op_ns,
        },
        "mitigations": _validate_mitigations(mitigations),
    }

    if cve_id is not None:
        cve_text = _canonical_text(cve_id, "cve_id").upper()
        if not _CVE_ID_RE.match(cve_text):
            raise InvalidAdvisoryArtifactError(
                f"cve_id {cve_id!r} does not match 'CVE-YYYY-NNNN[N...]'"
            )
        envelope["cve_id"] = cve_text

    if advisory_url is not None:
        envelope["advisory_url"] = _canonical_text(advisory_url, "advisory_url")

    return envelope
