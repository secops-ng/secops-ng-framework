"""Monitoring window for the eu_ai_act_deployer_obligations playbook.

Backs the ``monitor_operation`` step: Regulation (EU) 2024/1689 Art. 26(4)
and 26(5). Watching the system is the adapters' work; what this module
fixes is what each finding obliges the deployer to do, because the three
triggers in Art. 26(5) carry different legal consequences and must not be
collapsed:

* **routine** observations feed the provider's post-market monitoring
  (Art. 26(5), "where relevant", in accordance with Art. 72);
* **a risk within the meaning of Art. 79(1)** obliges the deployer, without
  undue delay, to inform the provider or distributor *and* the relevant
  market-surveillance authority, *and* to suspend use of the system. The
  hours from determination to recorded suspension are
  ``kri.eu_ai_act_deployer_suspension_latency_hours@v1``; an unrecorded
  suspension is reported as outstanding, never assumed;
* **a serious incident** (Art. 3(49)) obliges the deployer to inform
  immediately, in sequence: first the provider, then the importer or
  distributor and the market-surveillance authorities. The provider's
  Art. 73 report runs from awareness on a severity-classed clock — 2 days
  for a widespread infringement or a serious and irreversible disruption of
  critical infrastructure (Art. 73(3)), 10 days where a person died
  (Art. 73(4)), otherwise 15 days (Art. 73(2)); where more than one applies,
  the shortest governs. If the deployer cannot reach the provider, Art. 73
  applies to the deployer mutatis mutandis (Art. 26(5)), so the deployer
  reports on the same clock. The margin to that deadline is
  ``kri.eu_ai_act_report_clock_margin_days@v1``.

Art. 26(4) is recorded for the same window: where the deployer controls the
input data, that it is relevant and sufficiently representative; where it
does not, the dated determination of non-control is itself the evidence.
"""

from __future__ import annotations

from datetime import timedelta

from ._common import boolean, choice, digest, exact_keys, pointer, proceeding, text, zulu

__all__ = ["FINDING_KINDS", "INCIDENT_OUTCOMES", "InvalidMonitoringWindowError", "classify_monitoring_window"]

FINDING_KINDS: tuple[str, ...] = ("routine", "art_79_risk", "serious_incident")
INCIDENT_OUTCOMES: tuple[str, ...] = (
    "death",                                    # Art. 3(49)(a), and the Art. 73(4) clock
    "serious_harm_to_health",                   # Art. 3(49)(a)
    "critical_infrastructure_disruption",       # Art. 3(49)(b), and the Art. 73(3) clock
    "fundamental_rights_infringement",          # Art. 3(49)(c)
    "serious_harm_to_property_or_environment",  # Art. 3(49)(d)
)
_SEVERITY = {kind: rank for rank, kind in enumerate(FINDING_KINDS)}
_LATENCY = "kri.eu_ai_act_deployer_suspension_latency_hours@v1"
_MARGIN = "kri.eu_ai_act_report_clock_margin_days@v1"
_KIND_KEYS = {
    "routine": set(),
    "art_79_risk": {"suspended_at"},
    "serious_incident": {"aware_at", "outcomes", "widespread_infringement", "provider_reachable"},
}


class InvalidMonitoringWindowError(ValueError):
    """The window, the input-data record or a finding is malformed or inconsistent."""


def _art_73_bound(outcomes: list[str], widespread: bool) -> tuple[int, str]:
    bounds = [(15, "Art. 73(2)")]
    if "death" in outcomes:
        bounds.append((10, "Art. 73(4)"))
    if widespread or "critical_infrastructure_disruption" in outcomes:
        bounds.append((2, "Art. 73(3)"))
    return min(bounds)


def _input_data(value: object) -> dict:
    d = exact_keys(value, {"deployer_controls_input_data", "relevant", "sufficiently_representative"},
                   "input_data", InvalidMonitoringWindowError)
    controls = boolean(d["deployer_controls_input_data"], "input_data.deployer_controls_input_data",
                       InvalidMonitoringWindowError)
    if not controls:
        if d["relevant"] is not None or d["sufficiently_representative"] is not None:
            raise InvalidMonitoringWindowError(
                "input data the deployer does not control carries no Art. 26(4) assessment; "
                "relevant and sufficiently_representative must be null"
            )
        return {"deployer_controls_input_data": False, "relevant": None, "sufficiently_representative": None,
                "art_26_4_ok": None, "basis": "not_under_deployer_control"}
    relevant = boolean(d["relevant"], "input_data.relevant", InvalidMonitoringWindowError)
    representative = boolean(d["sufficiently_representative"], "input_data.sufficiently_representative",
                             InvalidMonitoringWindowError)
    return {"deployer_controls_input_data": True, "relevant": relevant,
            "sufficiently_representative": representative, "art_26_4_ok": relevant and representative,
            "basis": "assessed_by_deployer"}


def classify_monitoring_window(intended_use: dict, oversight: dict, window: dict, input_data: dict,
                               findings: list, evaluated_at: str) -> dict:
    """Resolve one monitoring window into its escalation class and the duties it triggers.

    Parameters
    ----------
    intended_use / oversight
        The confirm-intended-use and assign-human-oversight outputs for the
        same deployment; reachable only when the deployment may proceed.
    window
        Exactly ``window_start`` and ``window_end`` (Zulu).
    input_data
        Exactly ``deployer_controls_input_data`` (a real boolean) and
        ``relevant`` / ``sufficiently_representative`` — real booleans where
        the deployer controls the input data, ``None`` where it does not.
    findings
        Each exactly ``finding_ref``, ``kind`` (:data:`FINDING_KINDS`) and
        ``determined_at`` (Zulu, inside the window), plus, for
        ``art_79_risk``, ``suspended_at`` (Zulu, or ``None`` / ``""`` while
        unrecorded) and, for ``serious_incident``, ``aware_at`` (Zulu),
        ``outcomes`` (a non-empty list from :data:`INCIDENT_OUTCOMES`),
        ``widespread_infringement`` and ``provider_reachable`` (real
        booleans).
    evaluated_at
        Zulu instant the window is evaluated at, no earlier than its end;
        the Art. 73 margin is measured from here.
    """
    iu = proceeding(intended_use, InvalidMonitoringWindowError, "monitor operation")
    if not isinstance(oversight, dict) or not {"assignment_id", "deployment_id", "complete"} <= set(oversight):
        raise InvalidMonitoringWindowError("oversight must be the assign-human-oversight output")
    if oversight["deployment_id"] != iu["deployment_id"]:
        raise InvalidMonitoringWindowError("the oversight assignment belongs to a different deployment")
    w = exact_keys(window, {"window_start", "window_end"}, "window", InvalidMonitoringWindowError)
    start = zulu(w["window_start"], "window.window_start", InvalidMonitoringWindowError)
    end = zulu(w["window_end"], "window.window_end", InvalidMonitoringWindowError)
    if end < start:
        raise InvalidMonitoringWindowError("window_end is before window_start")
    evaluated = zulu(evaluated_at, "evaluated_at", InvalidMonitoringWindowError)
    if evaluated < end:
        raise InvalidMonitoringWindowError("a window cannot be evaluated before it ends")
    data = _input_data(input_data)
    if not isinstance(findings, list):
        raise InvalidMonitoringWindowError("findings must be a list")

    normalised, seen = [], set()
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            raise InvalidMonitoringWindowError(f"findings[{i}] must be an object")
        kind = choice(f.get("kind"), FINDING_KINDS, f"findings[{i}].kind", InvalidMonitoringWindowError)
        e = exact_keys(f, {"finding_ref", "kind", "determined_at"} | _KIND_KEYS[kind], f"findings[{i}]",
                       InvalidMonitoringWindowError)
        ref = pointer(e["finding_ref"], f"findings[{i}].finding_ref", InvalidMonitoringWindowError)
        if ref in seen:
            raise InvalidMonitoringWindowError(f"finding {ref!r} listed twice")
        seen.add(ref)
        determined = zulu(e["determined_at"], f"findings[{i}].determined_at", InvalidMonitoringWindowError)
        if not start <= determined <= end:
            raise InvalidMonitoringWindowError(f"finding {ref!r} was determined outside the window")
        item = {"finding_ref": ref, "kind": kind, "determined_at": e["determined_at"]}
        if kind == "art_79_risk":
            suspended = None
            if e["suspended_at"] not in (None, ""):
                suspended = zulu(e["suspended_at"], f"findings[{i}].suspended_at", InvalidMonitoringWindowError)
                if suspended < determined:
                    raise InvalidMonitoringWindowError(f"finding {ref!r} was suspended before it was determined")
            item["suspended_at"] = None if suspended is None else e["suspended_at"]
            item["suspension_latency_hours"] = (None if suspended is None
                                                else int((suspended - determined).total_seconds() // 3600))
        elif kind == "serious_incident":
            aware = zulu(e["aware_at"], f"findings[{i}].aware_at", InvalidMonitoringWindowError)
            if aware > evaluated:
                raise InvalidMonitoringWindowError(f"finding {ref!r} has an awareness instant after evaluation")
            outcomes = e["outcomes"]
            if not isinstance(outcomes, list) or not outcomes:
                raise InvalidMonitoringWindowError(f"findings[{i}].outcomes must be a non-empty list")
            outcomes = sorted({choice(o, INCIDENT_OUTCOMES, f"findings[{i}].outcomes[{j}]",
                                      InvalidMonitoringWindowError) for j, o in enumerate(outcomes)})
            widespread = boolean(e["widespread_infringement"], f"findings[{i}].widespread_infringement",
                                 InvalidMonitoringWindowError)
            reachable = boolean(e["provider_reachable"], f"findings[{i}].provider_reachable",
                                InvalidMonitoringWindowError)
            days, basis = _art_73_bound(outcomes, widespread)
            due = aware + timedelta(days=days)
            item |= {"aware_at": e["aware_at"], "outcomes": outcomes, "widespread_infringement": widespread,
                     "provider_reachable": reachable,
                     "art_73_clock": {"bound_days": days, "basis": basis, "report_due_at": text(due),
                                      "margin_hours": int((due - evaluated).total_seconds() // 3600),
                                      "reported_by": "provider" if reachable else "deployer"}}
        normalised.append(item)
    normalised.sort(key=lambda x: (x["determined_at"], x["finding_ref"]))

    actions = []
    routine = [x["finding_ref"] for x in normalised if x["kind"] == "routine"]
    if routine:
        actions.append({"action": "inform_provider_post_market_monitoring", "basis": "Art. 26(5), Art. 72",
                        "finding_refs": routine})
    for x in normalised:
        if x["kind"] == "art_79_risk":
            for action in ("inform_provider_or_distributor", "inform_market_surveillance_authority", "suspend_use"):
                actions.append({"action": action, "basis": "Art. 26(5), Art. 79(1)", "timing": "without_undue_delay",
                                "finding_refs": [x["finding_ref"]]})
        elif x["kind"] == "serious_incident":
            sequence = ["inform_provider", "inform_importer_or_distributor", "inform_market_surveillance_authorities"]
            if not x["provider_reachable"]:
                sequence.append("report_to_market_surveillance_authority_under_art_73")
            for order, action in enumerate(sequence, start=1):
                actions.append({"action": action, "basis": "Art. 26(5), Art. 73", "timing": "immediately",
                                "order": order, "finding_refs": [x["finding_ref"]]})

    trigger = max((x["kind"] for x in normalised), key=_SEVERITY.__getitem__, default="routine")
    stamps = ([_LATENCY] if any(x["kind"] == "art_79_risk" for x in normalised) else []) + \
             ([_MARGIN] if any(x["kind"] == "serious_incident" for x in normalised) else [])
    return {
        "observation_id": digest(iu["deployment_id"], w["window_start"], w["window_end"]),
        "deployment_id": iu["deployment_id"],
        "assignment_id": oversight["assignment_id"],
        "oversight_complete": oversight["complete"] is True,
        "window": {"window_start": w["window_start"], "window_end": w["window_end"]},
        "input_data": data,
        "findings": normalised,
        "escalation_trigger_class": trigger,
        "actions": actions,
        "suspensions_outstanding": [x["finding_ref"] for x in normalised
                                    if x["kind"] == "art_79_risk" and x["suspended_at"] is None],
        "evaluated_at": evaluated_at,
        "metric_stamps": sorted(stamps),
    }
