"""Deterministic significance + cross-border classification policy.

The classify-significance action in the incident_management source
playbook (F-WF-05) produces two booleans the regulator-submission
stages consume:

* ``__significant__`` — NIS2 Article 23(3) significance flag.
* ``__cross_border__`` — NIS2 Article 23(6) cross-border-scope flag.

Per ``docs/FOUNDATION.md`` §LLM determinism the classification itself
is **code, not LM** — DSPy is reserved for the free-text fields on the
final-report submission (see :mod:`.signatures`). The policy is
table-driven so a contributor change is a diff against the YAML at
``classification_policy.yaml`` rather than a code change, and so the
unit tests pin the table by id rather than by literal verdict.

The verdict is a frozen :class:`ClassificationVerdict` carrying both
flags, the rule ids that fired, every reason that fired (ordered),
and a short hex digest over the canonical inputs so a
replay-vs-original comparison is a single string-equal check.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Tuple

import yaml
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

__all__ = [
    "ClassificationVerdict",
    "DataClassification",
    "DisruptionSeverity",
    "IntakeSignals",
    "classify_significance",
    "load_policy",
    "policy_path",
]


# Closed alphabets used by the intake-signals input + the policy
# table. These are pinned here (not in the YAML) so a typo in the
# YAML is caught at load time, not silently treated as a new value.
DisruptionSeverity = Literal["none", "minor", "major", "severe"]
DataClassification = Literal[
    "none", "internal", "regulated", "special_category"
]

_DISRUPTION_ORDER: Tuple[DisruptionSeverity, ...] = (
    "none",
    "minor",
    "major",
    "severe",
)
_DISRUPTION_INDEX = {name: i for i, name in enumerate(_DISRUPTION_ORDER)}


class IntakeSignals(BaseModel):
    """Typed intake-event signals the classification policy consumes.

    Frozen so the verdict pins against a single immutable input
    bundle; ``extra='forbid'`` so a forged signal with a phantom
    field fails closed at the validation boundary.

    Attributes:
        affected_essential_service_count: Number of distinct
            essential / important services (NIS2 Annex I/II) the
            incident materially affected. Non-negative.
        member_states_affected_count: Number of EU member states
            whose users / operators were materially affected.
            Non-negative; >= 2 is the multi-state significance and
            cross-border gate.
        disruption_severity: Operator-graded severity of the
            service disruption. Closed alphabet —
            :data:`DisruptionSeverity`.
        data_classification: Most sensitive classification of data
            the incident touched. Closed alphabet —
            :data:`DataClassification`.
        cross_border_supply_chain: True when the operator's supply
            chain crosses a border even if the in-territory effect
            is single-state. Establishes cross-border under the
            NIS2 Art 23(6) supply-chain reading.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    affected_essential_service_count: NonNegativeInt = Field(
        description=(
            "Distinct essential / important services materially "
            "affected by the incident."
        ),
    )
    member_states_affected_count: NonNegativeInt = Field(
        description=(
            "EU member states whose users or operators were "
            "materially affected."
        ),
    )
    disruption_severity: DisruptionSeverity = Field(
        description=(
            "Operator-graded severity of the service disruption."
        ),
    )
    data_classification: DataClassification = Field(
        description=(
            "Most sensitive classification of data the incident "
            "touched."
        ),
    )
    cross_border_supply_chain: bool = Field(
        default=False,
        description=(
            "True when the operator's supply chain crosses a "
            "border even if the in-territory effect is "
            "single-state."
        ),
    )


@dataclass(frozen=True)
class ClassificationVerdict:
    """Verdict of the deterministic classification policy.

    Frozen so the per-target compilers pin against a single handle
    on the audit trail.

    Attributes:
        significant: NIS2 Art 23(3) significance flag.
        cross_border: NIS2 Art 23(6) cross-border-scope flag.
        significance_rule: Stable id of the significance rule that
            fired (always present — the default row fires when no
            other rule matches).
        cross_border_rule: Stable id of the cross-border rule that
            fired.
        reasons: Ordered tuple of human-readable reasons.
        inputs_digest: Short hex digest (16 lower-hex chars) over
            the canonical inputs so a replay-vs-original comparison
            is a single string-equal check.
    """

    significant: bool
    cross_border: bool
    significance_rule: str
    cross_border_rule: str
    reasons: Tuple[str, ...]
    inputs_digest: str


# ---------------------------------------------------------------------------
# Policy loader
# ---------------------------------------------------------------------------


def policy_path() -> Path:
    """Return the on-disk path to the policy YAML."""
    return Path(__file__).resolve().with_name("classification_policy.yaml")


def load_policy(path: Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the classification policy YAML.

    Args:
        path: Optional override for testing. Defaults to the YAML
            sibling of this module.

    Returns:
        Dict with two keys, ``significance_rules`` and
        ``cross_border_rules``, each a list of rule dicts in
        declaration order.

    Raises:
        ValueError: The YAML does not declare the expected schema
            shape, an unknown key surfaces in a ``when`` block, or
            an alphabet value is outside the closed set.
    """
    target = path or policy_path()
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"classification policy {target} must parse to a mapping; "
            f"got {type(raw).__name__}"
        )
    if raw.get("version") != 1:
        raise ValueError(
            "classification policy version mismatch: expected 1, "
            f"got {raw.get('version')!r}"
        )
    for section in ("significance_rules", "cross_border_rules"):
        rules = raw.get(section)
        if not isinstance(rules, list) or not rules:
            raise ValueError(
                f"classification policy section {section!r} must be a "
                "non-empty list"
            )
        for rule in rules:
            _validate_rule_shape(section, rule)
    return raw


_ALLOWED_WHEN_KEYS = {
    "affected_essential_service_count_at_least",
    "member_states_affected_count_at_least",
    "disruption_severity",
    "disruption_severity_at_least",
    "data_classification",
    "cross_border_supply_chain",
}


def _validate_rule_shape(section: str, rule: Any) -> None:
    if not isinstance(rule, dict):
        raise ValueError(
            f"{section} entry must be a mapping; got {type(rule).__name__}"
        )
    for key in ("id", "description", "when", "then"):
        if key not in rule:
            raise ValueError(
                f"{section} entry missing required key {key!r}: {rule!r}"
            )
    when = rule["when"]
    if when is None:
        rule["when"] = {}
        when = rule["when"]
    if not isinstance(when, dict):
        raise ValueError(
            f"{section}[{rule['id']!r}].when must be a mapping or null; "
            f"got {type(when).__name__}"
        )
    unknown = set(when) - _ALLOWED_WHEN_KEYS
    if unknown:
        raise ValueError(
            f"{section}[{rule['id']!r}].when carries unknown keys "
            f"{sorted(unknown)!r}; allowed keys are "
            f"{sorted(_ALLOWED_WHEN_KEYS)!r}"
        )
    if "disruption_severity" in when and when["disruption_severity"] not in _DISRUPTION_INDEX:
        raise ValueError(
            f"{section}[{rule['id']!r}].when.disruption_severity "
            f"{when['disruption_severity']!r} outside closed alphabet "
            f"{_DISRUPTION_ORDER!r}"
        )
    if (
        "disruption_severity_at_least" in when
        and when["disruption_severity_at_least"] not in _DISRUPTION_INDEX
    ):
        raise ValueError(
            f"{section}[{rule['id']!r}].when.disruption_severity_at_least "
            f"{when['disruption_severity_at_least']!r} outside closed "
            f"alphabet {_DISRUPTION_ORDER!r}"
        )


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------


def _rule_matches(when: Mapping[str, Any], signals: IntakeSignals) -> bool:
    for key, expected in when.items():
        if key == "affected_essential_service_count_at_least":
            if signals.affected_essential_service_count < int(expected):
                return False
        elif key == "member_states_affected_count_at_least":
            if signals.member_states_affected_count < int(expected):
                return False
        elif key == "disruption_severity":
            if signals.disruption_severity != expected:
                return False
        elif key == "disruption_severity_at_least":
            if (
                _DISRUPTION_INDEX[signals.disruption_severity]
                < _DISRUPTION_INDEX[expected]
            ):
                return False
        elif key == "data_classification":
            if signals.data_classification != expected:
                return False
        elif key == "cross_border_supply_chain":
            if signals.cross_border_supply_chain is not bool(expected):
                return False
        else:  # pragma: no cover — guarded at load time
            raise AssertionError(
                f"unknown when key {key!r} survived load-time validation"
            )
    return True


def _digest(signals: IntakeSignals) -> str:
    """Short hex digest over the canonical classification inputs."""
    payload = "\u001f".join(
        [
            str(signals.affected_essential_service_count),
            str(signals.member_states_affected_count),
            signals.disruption_severity,
            signals.data_classification,
            "1" if signals.cross_border_supply_chain else "0",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def classify_significance(
    signals: IntakeSignals, *, policy: dict[str, Any] | None = None
) -> ClassificationVerdict:
    """Apply the deterministic significance + cross-border policy.

    Args:
        signals: Typed :class:`IntakeSignals` extracted from the
            intake event.
        policy: Optional pre-loaded policy dict (for tests). Defaults
            to :func:`load_policy`.

    Returns:
        :class:`ClassificationVerdict` carrying both flags, the rule
        ids that fired, every reason that fired (ordered), and a
        digest of the canonical inputs.

    Raises:
        TypeError: ``signals`` is not an :class:`IntakeSignals`.
    """
    if not isinstance(signals, IntakeSignals):
        raise TypeError(
            f"signals must be IntakeSignals, got {type(signals).__name__}"
        )
    pol = policy or load_policy()

    sig_rule = _evaluate_first_match(pol["significance_rules"], signals)
    cb_rule = _evaluate_first_match(pol["cross_border_rules"], signals)

    significant = bool(sig_rule["then"]["significant"])
    cross_border = bool(cb_rule["then"]["cross_border"])

    reasons: Tuple[str, ...] = (
        f"significance_rule={sig_rule['id']}: {sig_rule['then']['reason']}",
        f"cross_border_rule={cb_rule['id']}: {cb_rule['then']['reason']}",
    )

    return ClassificationVerdict(
        significant=significant,
        cross_border=cross_border,
        significance_rule=sig_rule["id"],
        cross_border_rule=cb_rule["id"],
        reasons=reasons,
        inputs_digest=_digest(signals),
    )


def _evaluate_first_match(
    rules: list[dict[str, Any]], signals: IntakeSignals
) -> dict[str, Any]:
    for rule in rules:
        if _rule_matches(rule["when"], signals):
            return rule
    # The policy contributors are required to leave a default row at
    # the end of every section; failing to do so is a load-time bug,
    # not a runtime one. Defence in depth: surface a clear error here
    # rather than letting an UnboundLocalError leak.
    raise AssertionError(  # pragma: no cover — guarded by load_policy
        "classification policy section has no matching rule and no "
        "default row; the load_policy validator should have caught this"
    )
