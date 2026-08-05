"""High-risk classification primitive (identify high-risk AI system).

Resolves whether the AI system under ``__ai_system_id__`` is a high-risk AI
system, and on which of Article 6's three paths, pinning the Annex III
use-case category the rest of the lifecycle is scoped to.

The three paths are kept distinct because they carry different obligations
and different evidence:

* ``annex_i_product_safety`` — Art. 6(1). The system is a safety component
  of, or itself, a product covered by the Union harmonisation legislation in
  Annex I, and that legislation requires a third-party conformity
  assessment. High-risk. Pins the harmonisation reference rather than an
  Annex III area, because Art. 6(1) does not route through Annex III.
* ``annex_iii_standalone`` — Art. 6(2). The system falls in one of the eight
  Annex III areas. High-risk. Pins the area.
* ``annex_iii_derogated`` — Art. 6(3). The system falls in an Annex III area
  but does **not** pose a significant risk of harm to health, safety or
  fundamental rights, on one of the four grounds Art. 6(3) enumerates. **Not
  high-risk**, and therefore outside Art. 9 — but only against a documented
  assessment, which Art. 6(4) requires the provider to hold before placing
  the system on the market.

The derogation is the reason this primitive returns a verdict rather than a
boolean. A provider claiming Art. 6(3) must name the ground *and* the
assessment that supports it; a derogation with no assessment reference is
not representable here, because the readable form of that state on an
operator's dashboard would be "not high-risk" with nothing behind it.

Art. 6(3) is also deliberately not inferable: the primitive never derives
the derogation from the area or the intended purpose. The provider asserts
it and supplies its evidence, and this step records the assertion.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output.
* **Public-bar safe.** System-id, area, harmonisation reference and
  assessment reference are matched against closed regexes, so
  personal-name / credential-shaped strings fail loud at this boundary.
* **Read-only-by-contract.** No registration or market action is
  represented; Art. 49(2) registration of a derogated system is the
  operator's own surface.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "ANNEX_III_AREAS",
    "InvalidHighRiskClassificationError",
    "classify_high_risk_system",
]


_SYSTEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")

# The eight Annex III areas, as pinned in this playbook's mappings.yaml. The
# suffixes match the `eu_ai_act:annex-iii-N-<area>` mapping ids one-for-one,
# so a value here is resolvable to a shipped mapping entry rather than being
# free text.
ANNEX_III_AREAS: frozenset[str] = frozenset({
    "biometrics",
    "critical-infrastructure",
    "education-vocational-training",
    "employment-workers-management",
    "essential-services",
    "law-enforcement",
    "migration-asylum-border",
    "justice-democratic-processes",
})

_BASES = frozenset({
    "annex_i_product_safety",
    "annex_iii_standalone",
    "annex_iii_derogated",
})

# The four grounds Art. 6(3) allows a provider to rely on.
_DEROGATION_GROUNDS = frozenset({
    "narrow_procedural_task",
    "improves_prior_human_activity",
    "detects_decision_patterns_without_replacing_human_assessment",
    "preparatory_task",
})

_SCHEMA_VERSION = "1.0.0"
_STREAM = "eu_ai_act_risk_management_classification"


class InvalidHighRiskClassificationError(ValueError):
    """Raised when a classification input or per-path invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidHighRiskClassificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidHighRiskClassificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidHighRiskClassificationError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _require_absent(value: object, field: str, basis: str) -> None:
    if value is not None:
        raise InvalidHighRiskClassificationError(
            f"{field} must be absent for classification_basis {basis!r}"
        )


def classify_high_risk_system(
    ai_system_id: str,
    classification_basis: str,
    annex_iii_area: str | None = None,
    union_harmonisation_ref: str | None = None,
    derogation_ground: str | None = None,
    derogation_assessment_ref: str | None = None,
) -> dict:
    """Resolve the Article 6 high-risk classification for one AI system.

    Args:
        ai_system_id: Identifier of the AI system under assessment
            (``__ai_system_id__``).
        classification_basis: Which Article 6 path applies. One of
            ``annex_i_product_safety`` (Art. 6(1)),
            ``annex_iii_standalone`` (Art. 6(2)), or
            ``annex_iii_derogated`` (Art. 6(3)).
        annex_iii_area: One of :data:`ANNEX_III_AREAS`. Required for the two
            Annex III paths, forbidden for the Annex I path.
        union_harmonisation_ref: Reference to the Annex I Union
            harmonisation legislation entry. Required for the Annex I path,
            forbidden for the Annex III paths.
        derogation_ground: One of the four Art. 6(3) grounds. Required for
            the derogated path, forbidden otherwise.
        derogation_assessment_ref: Reference to the Art. 6(4) documented
            assessment supporting the derogation. Required for the derogated
            path, forbidden otherwise.

    Returns:
        JSON-native verdict envelope with ``schema_version``, ``stream``,
        ``ai_system_id``, ``classification_basis``, ``high_risk`` (False only
        on the Art. 6(3) path), ``art6_paragraph``, the pinned
        ``annex_iii_area`` or ``union_harmonisation_ref``, and — on the
        derogated path — ``derogation_ground`` and
        ``derogation_assessment_ref``. Absent fields are present as empty
        strings rather than omitted, so the envelope shape is stable across
        paths and a downstream consumer needs no per-path branching to read
        it.

    Raises:
        InvalidHighRiskClassificationError: any input fails validation, or a
            per-path invariant is violated — including a derogation claimed
            without both a ground and an assessment reference.
    """
    system = _require_pattern(ai_system_id, "ai_system_id", _SYSTEM_ID_RE)
    basis = _canonical_text(classification_basis, "classification_basis")
    if basis not in _BASES:
        raise InvalidHighRiskClassificationError(
            f"classification_basis {basis!r} not in {sorted(_BASES)}"
        )

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "ai_system_id": system,
        "classification_basis": basis,
        "high_risk": basis != "annex_iii_derogated",
        "art6_paragraph": {
            "annex_i_product_safety": "6(1)",
            "annex_iii_standalone": "6(2)",
            "annex_iii_derogated": "6(3)",
        }[basis],
        "annex_iii_area": "",
        "union_harmonisation_ref": "",
        "derogation_ground": "",
        "derogation_assessment_ref": "",
    }

    if basis == "annex_i_product_safety":
        _require_absent(annex_iii_area, "annex_iii_area", basis)
        _require_absent(derogation_ground, "derogation_ground", basis)
        _require_absent(
            derogation_assessment_ref, "derogation_assessment_ref", basis
        )
        if union_harmonisation_ref is None:
            raise InvalidHighRiskClassificationError(
                "annex_i_product_safety requires union_harmonisation_ref"
            )
        envelope["union_harmonisation_ref"] = _require_pattern(
            union_harmonisation_ref, "union_harmonisation_ref", _REF_RE
        )
        return envelope

    _require_absent(
        union_harmonisation_ref, "union_harmonisation_ref", basis
    )
    if annex_iii_area is None:
        raise InvalidHighRiskClassificationError(
            f"{basis} requires annex_iii_area"
        )
    area = _canonical_text(annex_iii_area, "annex_iii_area")
    if area not in ANNEX_III_AREAS:
        raise InvalidHighRiskClassificationError(
            f"annex_iii_area {area!r} not in {sorted(ANNEX_III_AREAS)}"
        )
    envelope["annex_iii_area"] = area

    if basis == "annex_iii_standalone":
        _require_absent(derogation_ground, "derogation_ground", basis)
        _require_absent(
            derogation_assessment_ref, "derogation_assessment_ref", basis
        )
        return envelope

    # Art. 6(3): both the ground and its documented assessment, or nothing.
    if derogation_ground is None or derogation_assessment_ref is None:
        raise InvalidHighRiskClassificationError(
            "annex_iii_derogated requires both derogation_ground and "
            "derogation_assessment_ref — Art. 6(4) requires the provider to "
            "document the assessment before placing the system on the market, "
            "so a derogation with no assessment reference is not a state this "
            "primitive will emit"
        )
    ground = _canonical_text(derogation_ground, "derogation_ground")
    if ground not in _DEROGATION_GROUNDS:
        raise InvalidHighRiskClassificationError(
            f"derogation_ground {ground!r} not in {sorted(_DEROGATION_GROUNDS)}"
        )
    envelope["derogation_ground"] = ground
    envelope["derogation_assessment_ref"] = _require_pattern(
        derogation_assessment_ref, "derogation_assessment_ref", _REF_RE
    )
    return envelope
