"""Per-control evaluator primitive (evaluate-controls).

Classifies each declared control against the collected posture-state
snapshot, producing one entry per ``(control_ref, scoped-resource-id)``
pair with the attestation state and the deviation list. Pure /
deterministic: re-evaluation under the same inputs re-derives the same
result set so a reviewer can replay the evaluation off the committed
artifact.

The classifier is intentionally minimal at this layer — it operates
against an operator-supplied policy that declares, per control, the
required configuration baseline keys/values per resource. Resources
whose configuration matches the baseline exactly are ``effective``;
resources missing any required key or carrying a non-matching value are
``ineffective`` and contribute one deviation each. The
``partially_effective`` band falls out of the aggregation when *some*
in-scope resources match and some do not. The EXTEND-evaluator sibling
card will tighten this against
``schemas/attestation_state.json`` and pin a richer deviation list
shape; the SKELETON enum is what this primitive returns today.

Design constraints
------------------

* **Pure / replayable.** No network, no clock, no LLMs.
* **Deterministic.** Output is sorted by ``control_ref`` so two replays
  of the same inputs collapse to byte-identical bytes.
* **Sovereign-stack neutral.** Policy is operator-side JSON-native;
  no vendor SDK is imported.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidControlEvaluationError",
    "evaluate_controls",
]


_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)


class InvalidControlEvaluationError(ValueError):
    """Raised when the inputs cannot produce a valid evaluation result set."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidControlEvaluationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidControlEvaluationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _evaluate_one_control(
    control_ref: str,
    baseline: dict[str, Any],
    resources: list[dict[str, Any]],
) -> dict[str, Any]:
    required: dict[str, Any] = baseline.get("required", {})
    if not isinstance(required, dict):
        raise InvalidControlEvaluationError(
            f"policy[{control_ref!r}].required must be an object, got "
            f"{type(required).__name__}"
        )
    deviations: list[dict[str, Any]] = []
    matched = 0
    for resource in resources:
        rid = resource["resource_id"]
        config = resource.get("configuration", {})
        miss: list[str] = []
        bad: list[dict[str, Any]] = []
        for key, expected in required.items():
            if key not in config:
                miss.append(key)
            elif config[key] != expected:
                bad.append(
                    {"key": key, "expected": expected, "observed": config[key]}
                )
        if miss or bad:
            deviations.append(
                {
                    "resource_id": rid,
                    "missing_keys": sorted(miss),
                    "mismatched_values": sorted(
                        bad, key=lambda d: d["key"]
                    ),
                }
            )
        else:
            matched += 1
    if not resources:
        # No in-scope resources to evaluate against this control: report
        # ineffective with zero deviations so the entry is auditable
        # rather than silently absent.
        state = "ineffective"
    elif not deviations:
        state = "effective"
    elif matched == 0:
        state = "ineffective"
    else:
        state = "partially_effective"
    return {
        "control_ref": control_ref,
        "attestation_state": state,
        "deviation_count": len(deviations),
        "deviations": deviations,
    }


def evaluate_controls(
    posture_state: dict,
    posture_policy: dict,
) -> list[dict[str, Any]]:
    """Build the per-control evaluation result set.

    Inputs
    ------
    posture_state
        Output of :func:`...primitives.collect.collect_posture_state` —
        carries the canonical ``resources`` list keyed by resource_id.
    posture_policy
        Operator-supplied policy object. Required shape:
        ``{"controls": {"control.<id>@v<n>": {"required": {"<key>":
        "<expected>", ...}}}}``.

    Returns
    -------
    JSON-native list of evaluation entries, one per declared control,
    sorted by ``control_ref`` for byte-stable replay.
    """
    if not isinstance(posture_state, dict):
        raise InvalidControlEvaluationError(
            f"posture_state must be an object, got "
            f"{type(posture_state).__name__}"
        )
    resources = posture_state.get("resources", [])
    if not isinstance(resources, list):
        raise InvalidControlEvaluationError(
            "posture_state.resources must be a list"
        )

    if not isinstance(posture_policy, dict):
        raise InvalidControlEvaluationError(
            f"posture_policy must be an object, got "
            f"{type(posture_policy).__name__}"
        )
    controls = posture_policy.get("controls", {})
    if not isinstance(controls, dict) or not controls:
        raise InvalidControlEvaluationError(
            "posture_policy.controls must be a non-empty object keyed by "
            "control_ref"
        )

    out: list[dict[str, Any]] = []
    for raw_ref, baseline in controls.items():
        ref = _canonical_text(raw_ref, "posture_policy.controls[*]")
        if not _CONTROL_REF_RE.match(ref):
            raise InvalidControlEvaluationError(
                f"posture_policy.controls key {raw_ref!r} does not match "
                "the control.<id>@v<n> shape pinned by the schema"
            )
        if not isinstance(baseline, dict):
            raise InvalidControlEvaluationError(
                f"posture_policy.controls[{ref!r}] must be an object, got "
                f"{type(baseline).__name__}"
            )
        out.append(_evaluate_one_control(ref, baseline, resources))

    out.sort(key=lambda entry: entry["control_ref"])
    return out
