"""Article 9(2) risk-assessment primitive (assess risk under Art. 9(2)).

Runs one iteration of the Art. 9(2) cycle over the risks the provider has
identified, scores each against the operator's acceptability threshold for
the pinned Annex III area, and returns the risk-register envelope the rest of
the lifecycle reads.

Art. 9(2) names four stages, and each identified risk carries the paragraph
it originates from so the register is auditable against the article rather
than being one undifferentiated list:

* ``9(2)(a)`` — known and reasonably foreseeable risks of the system used in
  accordance with its intended purpose.
* ``9(2)(b)`` — risks that may emerge under the intended purpose *and* under
  conditions of reasonably foreseeable misuse.
* ``9(2)(c)`` — risks identified from post-market monitoring data under
  Art. 72. These enter through :mod:`.post_market`, which is why a risk may
  legitimately appear in a later iteration that was absent from the first.

``9(2)(d)`` — the adoption of targeted risk-management measures — is carried
per risk as ``measure_refs`` rather than as a fourth origin, because a
measure is a response to a risk rather than a source of one.

**Acceptability is per risk, never aggregated.** Art. 9(5) requires the
residual risk of each individual hazard to be judged acceptable; an average
across a register hides exactly the one hazard that is not. So the envelope
reports a per-risk verdict and derives ``art9_5_acceptable`` as "every risk
is within threshold", not as a score.

**Re-scoring within an iteration collapses.** A provider re-scoring the same
register entry after applying a measure produces two observations for one
hazard, and counting both would double-report the breach. Within an
iteration the last observation for a given ``risk_id`` wins, earlier ones are
marked ``superseded``, and ``breach_count`` counts distinct breaching entries
— which is the population ``kri.residual_risk_threshold_breach_count@v1``
reads.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output. Scores are
  normalised through :class:`~decimal.Decimal` and emitted as canonical
  strings, so no float repr reaches the envelope.
* **Public-bar safe.** Ids and references are matched against closed
  regexes; risk *descriptions* are deliberately not accepted at this
  boundary, because a free-text hazard description is where personal data
  and internal detail would leak into a public-bar artifact. The register
  carries references to the provider's own risk documentation instead.
* **Read-only-by-contract.** No risk-register write is represented; the
  envelope is the record the operator's own store persists.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from content.playbooks.eu_ai_act_risk_management.primitives.classification import (
    ANNEX_III_AREAS,
)

__all__ = [
    "InvalidArt9AssessmentError",
    "assess_art9_risks",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")

_ORIGINS = frozenset({"9(2)(a)", "9(2)(b)", "9(2)(c)"})

_SCHEMA_VERSION = "1.0.0"
_STREAM = "eu_ai_act_risk_management_assessment"


class InvalidArt9AssessmentError(ValueError):
    """Raised when an assessment input or Art. 9 invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidArt9AssessmentError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidArt9AssessmentError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidArt9AssessmentError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _decimal(value: object, field: str) -> Decimal:
    """Accept int / str decimal, reject float and non-finite.

    A float is rejected rather than coerced: ``0.1`` has no exact binary
    representation, so accepting one would make the emitted canonical string
    depend on the caller's literal rather than on the value.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidArt9AssessmentError(
            f"{field} must be an int or a decimal string, not "
            f"{type(value).__name__} — a float cannot round-trip exactly"
        )
    if isinstance(value, int):
        return Decimal(value)
    text = _canonical_text(value, field)
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise InvalidArt9AssessmentError(
            f"{field} {text!r} is not a decimal"
        ) from exc
    if not parsed.is_finite():
        raise InvalidArt9AssessmentError(f"{field} must be finite")
    return parsed


def _validate_risk(record: object, index: int) -> tuple[str, str, Decimal, tuple[str, ...]]:
    if not isinstance(record, dict):
        raise InvalidArt9AssessmentError(
            f"identified_risks[{index}] must be a mapping, got "
            f"{type(record).__name__}"
        )
    risk_id = _require_pattern(
        record.get("risk_id"), f"identified_risks[{index}].risk_id", _ID_RE
    )
    origin = _canonical_text(
        record.get("origin_paragraph"),
        f"identified_risks[{index}].origin_paragraph",
    )
    if origin not in _ORIGINS:
        raise InvalidArt9AssessmentError(
            f"identified_risks[{index}].origin_paragraph {origin!r} not in "
            f"{sorted(_ORIGINS)}"
        )
    score = _decimal(
        record.get("residual_score"), f"identified_risks[{index}].residual_score"
    )
    raw_measures = record.get("measure_refs") or []
    if isinstance(raw_measures, str) or not isinstance(raw_measures, (list, tuple)):
        raise InvalidArt9AssessmentError(
            f"identified_risks[{index}].measure_refs must be a list of "
            f"references"
        )
    measures = tuple(
        _require_pattern(m, f"identified_risks[{index}].measure_refs[{j}]", _REF_RE)
        for j, m in enumerate(raw_measures)
    )
    return risk_id, origin, score, measures


def assess_art9_risks(
    classification: dict,
    iteration_id: str,
    identified_risks: list,
    acceptability_thresholds: dict,
) -> dict:
    """Score one Art. 9(2) iteration against the operator's thresholds.

    Args:
        classification: The verdict envelope from the classification step
            (``__annex_iii_use_case__``). Must be high-risk: an Art. 6(3)
            derogated system is outside Art. 9 entirely, and scoring one
            would produce a register the article does not ask for.
        iteration_id: Identifier of this Art. 9(2) iteration
            (``__iteration_id__``). Art. 9(2) is a continuous iterative
            process, so the register is always scoped to an iteration.
        identified_risks: Risk records, each a mapping with ``risk_id``,
            ``origin_paragraph`` (one of ``9(2)(a)``, ``9(2)(b)``,
            ``9(2)(c)``), ``residual_score`` (int or decimal string) and
            optional ``measure_refs``.
        acceptability_thresholds: Annex III area to threshold, as int or
            decimal string. Only the pinned area is read; the rest are
            ignored so an operator can pass one policy object for an estate.

    Returns:
        JSON-native risk-register envelope with ``schema_version``,
        ``stream``, ``risk_register_id`` (the supplied ``iteration_id``
        scoped to the system), ``ai_system_id``, ``annex_iii_area``,
        ``iteration_id``, ``threshold``, ``entries`` (per-risk verdicts, each
        with ``risk_id``, ``origin_paragraph``, ``residual_score``,
        ``within_threshold``, ``superseded`` and ``measure_refs``),
        ``breach_count`` over distinct non-superseded breaching entries, and
        ``art9_5_acceptable``.

    Raises:
        InvalidArt9AssessmentError: any input fails validation, the
            classification is not high-risk, the pinned area has no
            threshold, or ``identified_risks`` is empty.
    """
    if not isinstance(classification, dict):
        raise InvalidArt9AssessmentError(
            f"classification must be a mapping, got {type(classification).__name__}"
        )
    if classification.get("high_risk") is not True:
        raise InvalidArt9AssessmentError(
            "classification is not high-risk; Art. 9 applies to high-risk AI "
            "systems, and an Art. 6(3) derogated system has no Art. 9(2) "
            "register to score"
        )
    system = _require_pattern(
        classification.get("ai_system_id"), "classification.ai_system_id", _ID_RE
    )
    area = _canonical_text(
        classification.get("annex_iii_area"), "classification.annex_iii_area"
    )
    if area not in ANNEX_III_AREAS:
        raise InvalidArt9AssessmentError(
            f"classification.annex_iii_area {area!r} not in "
            f"{sorted(ANNEX_III_AREAS)} — the Art. 6(1) product-safety path "
            f"pins no Annex III area, so its threshold must be supplied under "
            f"an explicit area"
        )
    iteration = _require_pattern(iteration_id, "iteration_id", _ID_RE)

    if not isinstance(acceptability_thresholds, dict):
        raise InvalidArt9AssessmentError(
            "acceptability_thresholds must be a mapping of Annex III area to "
            "threshold"
        )
    if area not in acceptability_thresholds:
        raise InvalidArt9AssessmentError(
            f"acceptability_thresholds carries no entry for the pinned area "
            f"{area!r}; Art. 9(5) acceptability is judged against the "
            f"operator's own policy and this primitive ships no default"
        )
    threshold = _decimal(
        acceptability_thresholds[area], f"acceptability_thresholds[{area!r}]"
    )

    if isinstance(identified_risks, str) or not isinstance(
        identified_risks, (list, tuple)
    ):
        raise InvalidArt9AssessmentError(
            "identified_risks must be a list of risk records"
        )
    if not identified_risks:
        raise InvalidArt9AssessmentError(
            "identified_risks is empty; an Art. 9(2) iteration that identified "
            "no risk is a finding about the assessment, not an empty register, "
            "so it is not representable here"
        )

    validated = [_validate_risk(r, i) for i, r in enumerate(identified_risks)]

    # Within an iteration the last observation for a risk_id wins; earlier
    # ones are kept but marked superseded so the audit trail of re-scoring
    # survives while the breach count does not double-report.
    last_index: dict[str, int] = {}
    for i, (risk_id, _, _, _) in enumerate(validated):
        last_index[risk_id] = i

    entries = []
    for i, (risk_id, origin, score, measures) in enumerate(validated):
        superseded = last_index[risk_id] != i
        entries.append({
            "risk_id": risk_id,
            "origin_paragraph": origin,
            "residual_score": str(score),
            "within_threshold": score <= threshold,
            "superseded": superseded,
            "measure_refs": list(measures),
        })

    breaching = {
        e["risk_id"] for e in entries
        if not e["superseded"] and not e["within_threshold"]
    }
    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "risk_register_id": f"{system}:{iteration}",
        "ai_system_id": system,
        "annex_iii_area": area,
        "iteration_id": iteration,
        "threshold": str(threshold),
        "entries": entries,
        "breach_count": len(breaching),
        "art9_5_acceptable": not breaching,
    }
