"""Technical-documentation primitive (assemble technical documentation).

Assembles the Article 11 technical documentation bundle, read with Annex IV,
and pins the two commit anchors the freshness indicator reads.

Two bundles, not one. Art. 11 read with Annex IV governs the technical
documentation; Art. 13(2)-(3) governs the instructions for use handed to the
deployer. They are maintained on different cadences by different owners, and
``kri.transparency_doc_freshness_age@v1`` takes the **maximum** of the two
ages precisely so a current technical file cannot mask stale instructions. So
this primitive carries both anchors and refuses to infer one from the other.

**Commit dates are supplied, never read from a clock.** The age itself is
computed by the indicator at evaluation time against its own window; what
this step records is when each bundle was committed. A primitive that called
``date.today()`` would emit a different envelope on every run and make the
whole lifecycle unreplayable.

**Annex IV(5) must name the register.** Annex IV point 5 is the description
of the risk-management system "according to Article 9" — so the bundle is
required to reference the register the assessment step produced, and a
mismatch is a hard error rather than a warning. This is the one cross-step
invariant in the playbook: it is what makes the documentation demonstrably
about *this* iteration rather than about the system in general.

**Incompleteness is represented, not refused.** A provider assembling the
bundle over several weeks legitimately holds an incomplete Annex IV set, and
Art. 11 requires the documentation to be kept up to date rather than to
spring into existence complete. So a missing section yields
``complete: false`` with the gaps named, and only Annex IV(5) hard-fails —
because that one is not a gap in the bundle, it is a broken link to the
register.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output; ``missing_sections``
  is emitted in Annex IV order rather than set order.
* **Public-bar safe.** Section values are references into the provider's own
  documentation store, matched against a closed regex — never document
  bodies, which is where a public-bar artifact would leak the contents of a
  technical file.
* **Read-only-by-contract.** No document is written or published; the
  envelope records what the operator's own store holds.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "ANNEX_IV_SECTIONS",
    "InvalidTechnicalDocumentationError",
    "assemble_technical_documentation",
]


_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Annex IV points 1-9, in Annex order. The tuple is ordered rather than a
# frozenset so `missing_sections` reports in the order the Annex lists them,
# which is the order a reviewer reads the file in.
ANNEX_IV_SECTIONS: tuple[str, ...] = (
    "1-general-description",
    "2-elements-and-development-process",
    "3-monitoring-functioning-control",
    "4-performance-metrics-appropriateness",
    "5-risk-management-system",
    "6-lifecycle-changes",
    "7-harmonised-standards-applied",
    "8-eu-declaration-of-conformity",
    "9-post-market-monitoring-plan",
)

_RISK_MANAGEMENT_SECTION = "5-risk-management-system"

_SCHEMA_VERSION = "1.0.0"
_STREAM = "eu_ai_act_risk_management_documentation"


class InvalidTechnicalDocumentationError(ValueError):
    """Raised when a documentation input or Annex IV invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidTechnicalDocumentationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidTechnicalDocumentationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidTechnicalDocumentationError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _require_iso_date(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_DATE_RE.match(text):
        raise InvalidTechnicalDocumentationError(
            f"{field} {text!r} is not an ISO-8601 date (YYYY-MM-DD)"
        )
    return text


def assemble_technical_documentation(
    risk_register: dict,
    annex_iv_sections: dict,
    technical_doc_committed_at: str,
    instructions_committed_at: str,
) -> dict:
    """Assemble the Art. 11 / Annex IV bundle and pin its freshness anchors.

    Args:
        risk_register: The register envelope from the assessment step
            (``__risk_register_id__``).
        annex_iv_sections: Annex IV section key to a reference into the
            provider's documentation store. Keys must come from
            :data:`ANNEX_IV_SECTIONS`; unknown keys are rejected rather than
            ignored, since a typo would otherwise read as a missing section.
        technical_doc_committed_at: ISO-8601 date the Art. 11 / Annex IV
            bundle was last committed (``__technical_doc_committed_at__``).
        instructions_committed_at: ISO-8601 date the Art. 13 instructions for
            use were last committed (``__instructions_committed_at__``).

    Returns:
        JSON-native envelope with ``schema_version``, ``stream``,
        ``technical_documentation_id``, ``ai_system_id``,
        ``risk_register_id``, ``iteration_id``, ``sections`` (the validated
        mapping), ``missing_sections`` in Annex IV order, ``complete``, and
        the two commit anchors ``technical_doc_committed_at`` and
        ``instructions_committed_at``.

    Raises:
        InvalidTechnicalDocumentationError: any input fails validation, a
            section key is unknown, or Annex IV(5) is absent or does not
            reference the supplied register.
    """
    if not isinstance(risk_register, dict):
        raise InvalidTechnicalDocumentationError(
            f"risk_register must be a mapping, got {type(risk_register).__name__}"
        )
    register_id = _require_pattern(
        risk_register.get("risk_register_id"),
        "risk_register.risk_register_id",
        _REF_RE,
    )
    system = _require_pattern(
        risk_register.get("ai_system_id"), "risk_register.ai_system_id", _REF_RE
    )
    iteration = _require_pattern(
        risk_register.get("iteration_id"), "risk_register.iteration_id", _REF_RE
    )

    if not isinstance(annex_iv_sections, dict):
        raise InvalidTechnicalDocumentationError(
            "annex_iv_sections must be a mapping of Annex IV section key to "
            "reference"
        )
    unknown = sorted(set(annex_iv_sections) - set(ANNEX_IV_SECTIONS))
    if unknown:
        raise InvalidTechnicalDocumentationError(
            f"annex_iv_sections carries unknown section key(s) {unknown}; "
            f"expected keys from {list(ANNEX_IV_SECTIONS)} — an unrecognised "
            f"key would otherwise read as a missing section"
        )
    sections = {
        key: _require_pattern(
            annex_iv_sections[key], f"annex_iv_sections[{key!r}]", _REF_RE
        )
        for key in ANNEX_IV_SECTIONS
        if key in annex_iv_sections
    }

    if _RISK_MANAGEMENT_SECTION not in sections:
        raise InvalidTechnicalDocumentationError(
            f"annex_iv_sections is missing {_RISK_MANAGEMENT_SECTION!r}; "
            f"Annex IV point 5 is the description of the Art. 9 "
            f"risk-management system, so a bundle assembled against a register "
            f"must reference it"
        )
    if sections[_RISK_MANAGEMENT_SECTION] != register_id:
        raise InvalidTechnicalDocumentationError(
            f"annex_iv_sections[{_RISK_MANAGEMENT_SECTION!r}] references "
            f"{sections[_RISK_MANAGEMENT_SECTION]!r} but the supplied register "
            f"is {register_id!r}; the Annex IV point 5 description must be of "
            f"this iteration's register"
        )

    missing = [k for k in ANNEX_IV_SECTIONS if k not in sections]
    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "technical_documentation_id": f"{system}:annex-iv:{iteration}",
        "ai_system_id": system,
        "risk_register_id": register_id,
        "iteration_id": iteration,
        "sections": sections,
        "missing_sections": missing,
        "complete": not missing,
        "technical_doc_committed_at": _require_iso_date(
            technical_doc_committed_at, "technical_doc_committed_at"
        ),
        "instructions_committed_at": _require_iso_date(
            instructions_committed_at, "instructions_committed_at"
        ),
    }
