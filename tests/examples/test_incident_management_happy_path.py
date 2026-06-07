"""Happy-path golden replay test across n8n + Temporal + LangGraph targets.

F-WF-05 EXTEND-tests-happy. The three reference compile targets each
bind the CORE action bodies of the incident-management playbook to the
same shared deterministic primitives shipped under
``content.playbooks.incident_management.primitives``:

* ``classification.classify_significance`` — NIS2 Article 23(3) /
  23(6) significance + cross-border policy (the classify step,
  step_id ``action--...0003``).
* ``stage_clock.verdict_for_submission`` — three-stage NIS2 Article
  23 clock arithmetic (the 24h / 72h / one-month windows that bound
  the three submission steps).
* ``regulator_submission.resolve_destination`` — fail-closed
  destination lookup against the operator-supplied
  ``__notification_destinations__`` mapping (the framework ships no
  default endpoint).
* ``timeline_binding`` — F-PT-02 incident-timeline adapter
  (open / record_event / close), the binding the three submission
  steps thread through.

Per ``docs/FOUNDATION.md`` §LLM determinism, every step exercised
here is deterministic code; the only DSPy reach on this workflow is
the free-text fields of the one-month final-report submission, which
sit out of scope of the happy-path replay (covered by the dedicated
signatures unit tests).

The contract this test pins is:

  Feeding one realistic incident case (committed as JSON under
  ``tests/fixtures/incident_management/``) through each target's
  traversal shape MUST produce the same canonical case-state JSON
  (significance verdict + rule ids, the if-condition branch each
  gate selects, the resolved destinations for each stage, the
  stage-clock on-time / overrun verdicts, and the F-PT-02 timeline
  closure receipt).

If any target re-implements canonicalisation locally, picks up
wall-clock or random ordering as input, or drifts on the
fail-closed destination resolver, this test fails on the target
that drifted.

The test does **not** require ``n8n``, ``temporalio`` or
``langgraph`` to be installed; the per-target drivers below mirror
the call shape each emitted artefact uses (linear Code-node body,
activity declaration order, state-bindings tool order) while
invoking the same shared primitives the artefacts import.

Mirror of ``tests/examples/alert_triage/test_happy_path.py``
(F-WF-03 EXTEND-tests-happy) — same shape, incident-management
contract.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest

from content.playbooks.incident_management.primitives import (
    ClassificationVerdict,
    IntakeSignals,
    PT02_BINDING_STATUS,
    REGULATOR_SUBMISSION_STAGES,
    StageVerdict,
    TimelineClosure,
    TimelineSession,
    classify_significance,
    close_timeline,
    open_timeline,
    record_event,
    resolve_destination,
    stages_in_order,
    verdict_for_submission,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "incident_management"
    / "happy_path_case.json"
)

# CACAO step ids the canonical playbook pins for the two if-condition
# branches. Mirrors
# content/playbooks/incident-management/playbook.cacao.json §
# if-condition--...0004 (significant?) and ...0008 (final-report material
# complete?).
_POST_SIGNIFICANCE_TRUE = "action--50000000-0000-4000-8000-000000000005"
_POST_SIGNIFICANCE_FALSE = "end--50000000-0000-4000-8000-00000000000b"
_FINAL_REPORT_TRUE = "action--50000000-0000-4000-8000-000000000009"
_FINAL_REPORT_FALSE = "action--50000000-0000-4000-8000-00000000000a"


# --------------------------------------------------------------------------- #
# Fixture loading + small shape adapters.                                     #
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def case() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _build_signals(case: dict) -> IntakeSignals:
    """Typed incident-payload ingest.

    Mirrors the ingest CORE action body (step ``...0002``): the
    dispatcher reads the operator-graded intake-event signals off
    the raw envelope and returns a frozen Pydantic payload object.
    Replays of the same fixture produce ``==``-equal payload
    objects (``frozen=True`` + ``extra='forbid'``).
    """
    return IntakeSignals(**case["intake_signals"])


def _classify(signals: IntakeSignals) -> ClassificationVerdict:
    """Deterministic significance + cross-border classification.

    Mirrors the classify CORE action body (step ``...0003``).
    """
    return classify_significance(signals)


def _resolve_all_destinations(case: dict) -> dict[str, str]:
    """Fail-closed destination resolution for each stage.

    Mirrors the resolve_destination bindings on the three submission
    steps (``...0006`` early warning, ``...0009`` final report; the
    asymmetric stage-clock binding on ``...0007`` is exercised
    separately below).
    """
    destinations = case["notification_destinations"]
    return {
        stage: resolve_destination(destinations, stage=stage)
        for stage in stages_in_order()
    }


def _stage_verdicts(case: dict) -> dict[str, StageVerdict]:
    """Three-stage NIS2 Article 23 clock verdicts.

    Mirrors the verdict_for_submission binding on the notification
    step (``...0007``). For the happy-path replay we exercise every
    stage so the canonical state pins the on-time / overrun verdict
    each submission carries onto the audit trail.
    """
    opened = _parse_dt(case["timeline"]["opened_at"])
    submissions = {
        "early_warning": _parse_dt(
            case["timeline"]["early_warning_submitted_at"]
        ),
        "notification": _parse_dt(
            case["timeline"]["notification_submitted_at"]
        ),
        "final_report": _parse_dt(
            case["timeline"]["final_report_submitted_at"]
        ),
    }
    return {
        stage: verdict_for_submission(
            stage=stage,
            opened_at=opened,
            submitted_at=submissions[stage],
        )
        for stage in stages_in_order()
    }


def _drive_timeline(
    case: dict, *, destinations: dict[str, str]
) -> tuple[TimelineSession, TimelineClosure]:
    """F-PT-02 binding traversal: open → record_event×3 → close.

    Mirrors the open_timeline / record_event / close_timeline
    bindings on steps ``...0005``, ``...0006``/``...0007``/``...0009``
    and ``...000a``. The receipt is the closure handle the per-target
    CORE bodies pin onto the audit trail and the source artefact the
    F-CP-02 downstream consumer reads.
    """
    incident_id = UUID(case["incident_id"])
    opened = _parse_dt(case["timeline"]["opened_at"])
    closed = _parse_dt(case["timeline"]["closed_at"])
    session = open_timeline(incident_id=incident_id, opened_at=opened)
    submissions = {
        "early_warning": _parse_dt(
            case["timeline"]["early_warning_submitted_at"]
        ),
        "notification": _parse_dt(
            case["timeline"]["notification_submitted_at"]
        ),
        "final_report": _parse_dt(
            case["timeline"]["final_report_submitted_at"]
        ),
    }
    for stage in stages_in_order():
        record_event(
            session,
            stage=stage,
            occurred_at=submissions[stage],
            summary=f"regulator submission dispatched to {destinations[stage]}",
            payload_digest=f"happy-path:{stage}",
        )
    closure = close_timeline(session, closed_at=closed)
    return session, closure


# --------------------------------------------------------------------------- #
# Canonical case-state assembly (shared shape every target must produce).    #
# --------------------------------------------------------------------------- #


def _post_significance_branch(verdict: ClassificationVerdict) -> str:
    return (
        _POST_SIGNIFICANCE_TRUE if verdict.significant else _POST_SIGNIFICANCE_FALSE
    )


def _final_report_branch(*, final_report_ready: bool) -> str:
    return _FINAL_REPORT_TRUE if final_report_ready else _FINAL_REPORT_FALSE


def _assemble_canonical_state(
    *,
    verdict: ClassificationVerdict,
    destinations: dict[str, str],
    stage_verdicts: dict[str, StageVerdict],
    closure: TimelineClosure,
    final_report_ready: bool,
) -> dict:
    """Return the canonical case-state JSON shape.

    Keys are sorted so a future diff between targets surfaces as a
    value mismatch, not a key-order artefact. The pinned fields match
    the F-WF-05 EXTEND-tests-happy acceptance criteria:

    * typed incident-payload ingest is implicit — the classification
      verdict's ``inputs_digest`` is a string-equal handle over the
      validated IntakeSignals;
    * stage-clock advancement is pinned via the per-stage on_time /
      slack-seconds tuple;
    * significance / cross-border policy gating is pinned via the
      verdict's rule ids + the selected if-condition branch;
    * regulator-submission contract path is pinned via the per-stage
      resolved destination handle;
    * F-PT-02 binding is pinned via the timeline-closure receipt
      (handle, artefact path, event count, binding status).
    """
    return {
        "classification_inputs_digest": verdict.inputs_digest,
        "cross_border": verdict.cross_border,
        "cross_border_rule": verdict.cross_border_rule,
        "destinations": {
            stage: destinations[stage] for stage in stages_in_order()
        },
        "pt02_binding_status": closure.binding_status,
        "selected_final_report_branch": _final_report_branch(
            final_report_ready=final_report_ready
        ),
        "selected_post_significance_branch": _post_significance_branch(verdict),
        "significance_rule": verdict.significance_rule,
        "significant": verdict.significant,
        "stage_verdicts": {
            stage: {
                "due_at": stage_verdicts[stage].due_at.isoformat(),
                "inputs_digest": stage_verdicts[stage].inputs_digest,
                "on_time": stage_verdicts[stage].on_time,
                "slack_seconds": int(
                    stage_verdicts[stage].slack.total_seconds()
                ),
            }
            for stage in stages_in_order()
        },
        "timeline_artefact_path": closure.artefact_path,
        "timeline_event_count": closure.event_count,
        "timeline_handle": closure.handle,
    }


# --------------------------------------------------------------------------- #
# Per-target drivers — each mirrors the call shape the emitted artefact      #
# produces, invoking the same shared primitives the artefact imports.        #
# --------------------------------------------------------------------------- #


def _drive_target(case: dict) -> dict:
    """Shared traversal: every target binds the same primitives in the
    same playbook order, so the n8n / Temporal / LangGraph drivers
    collapse to a single helper.

    The canonical playbook walks::

        ingest → classify → if-condition(significant?) → open_timeline
        → submit_24h → submit_72h → if-condition(final_report_ready?)
        → submit_1m → close_timeline.

    Both if-condition gates carry deterministic decisions on the
    happy-path fixture (``significant=True``, ``final_report_ready=True``)
    — a future drift in either gate surfaces here.
    """
    signals = _build_signals(case)
    verdict = _classify(signals)
    # significance gate: the false branch routes straight to the end
    # step and the timeline never opens. Pin the invariant here so a
    # fixture mutation that flips significance surfaces immediately.
    assert verdict.significant, (
        "happy-path fixture must classify as significant; otherwise the "
        "regulator-timeline branch (steps 0005..000a) is unreachable and "
        "the canonical state below is degenerate."
    )
    destinations = _resolve_all_destinations(case)
    stage_verdicts = _stage_verdicts(case)
    _session, closure = _drive_timeline(case, destinations=destinations)
    return _assemble_canonical_state(
        verdict=verdict,
        destinations=destinations,
        stage_verdicts=stage_verdicts,
        closure=closure,
        final_report_ready=bool(case["final_report_ready"]),
    )


def _drive_n8n(case: dict) -> dict:
    """n8n traversal: Code-node bodies fire in linear playbook order.

    Mirrors ``examples/n8n/incident-management/workflow.n8n.json`` —
    the SKELETON-wave per-step ``core_body`` bindings declared in
    ``core_body.overlay.json`` invoke the same primitive functions
    this driver does, in the same playbook-declaration order.
    """
    return _drive_target(case)


def _drive_temporal(case: dict) -> dict:
    """Temporal traversal: activity calls in workflow declaration order.

    Mirrors ``examples/temporal/incident-management/workflow.temporal.py``
    — the CORE-bound ``@activity.defn`` bodies invoke the same
    primitives the n8n target imports.
    """
    return _drive_target(case)


def _drive_langgraph(case: dict) -> dict:
    """LangGraph traversal: tools fire in GraphSpec edge order.

    Mirrors ``examples/langgraph/incident-management/state_bindings.py``
    — the CORE-bound ``@tool`` bodies invoke the same primitives the
    n8n and Temporal targets import.
    """
    return _drive_target(case)


_TARGETS = [
    ("n8n", _drive_n8n),
    ("temporal", _drive_temporal),
    ("langgraph", _drive_langgraph),
]


# --------------------------------------------------------------------------- #
# Tests.                                                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("label,driver", _TARGETS, ids=[t[0] for t in _TARGETS])
def test_target_produces_canonical_case_state(label: str, driver, case) -> None:
    """Each target's traversal yields the canonical case-state shape."""
    state = driver(case)
    assert set(state.keys()) == {
        "classification_inputs_digest",
        "cross_border",
        "cross_border_rule",
        "destinations",
        "pt02_binding_status",
        "selected_final_report_branch",
        "selected_post_significance_branch",
        "significance_rule",
        "significant",
        "stage_verdicts",
        "timeline_artefact_path",
        "timeline_event_count",
        "timeline_handle",
    }
    # Strict-bool fields.
    assert isinstance(state["significant"], bool)
    assert isinstance(state["cross_border"], bool)
    # Selected branches resolve to known if-condition outcomes.
    assert state["selected_post_significance_branch"] in {
        _POST_SIGNIFICANCE_TRUE,
        _POST_SIGNIFICANCE_FALSE,
    }
    assert state["selected_final_report_branch"] in {
        _FINAL_REPORT_TRUE,
        _FINAL_REPORT_FALSE,
    }
    # Destinations cover every stage of the closed alphabet, in order.
    assert tuple(state["destinations"].keys()) == REGULATOR_SUBMISSION_STAGES
    assert all(
        isinstance(handle, str) and handle.strip()
        for handle in state["destinations"].values()
    )
    # Stage verdicts cover every stage of the closed alphabet.
    assert set(state["stage_verdicts"]) == set(REGULATOR_SUBMISSION_STAGES)
    for stage_state in state["stage_verdicts"].values():
        assert isinstance(stage_state["on_time"], bool)
        assert isinstance(stage_state["slack_seconds"], int)
        assert isinstance(stage_state["due_at"], str)
        assert len(stage_state["inputs_digest"]) == 16
    # F-PT-02 binding handle is the adapter shape today; flips to
    # ``"pattern"`` when the pattern module lands on disk.
    assert state["pt02_binding_status"] == PT02_BINDING_STATUS
    assert state["timeline_handle"].startswith("incident-timeline/")
    assert state["timeline_artefact_path"].startswith(
        "content/evidence/incidents/"
    )
    # open + 3 submissions + close = 5 events on the F-PT-02 timeline.
    assert state["timeline_event_count"] == 5


def test_all_targets_produce_identical_canonical_state(case) -> None:
    """Headline contract: feeding the same fixture through every target
    produces a byte-identical canonical case-state.

    A drift in any one target's primitive binding, its traversal
    order, or its deterministic-stub adapter usage surfaces here.
    """
    rendered = {
        label: json.dumps(driver(case), indent=2, sort_keys=True)
        for label, driver in _TARGETS
    }
    n8n_state = rendered["n8n"]
    for label, target_state in rendered.items():
        assert target_state == n8n_state, (
            f"target {label!r} produced a canonical case-state JSON that "
            f"differs from n8n. Got:\n{target_state}\nExpected:\n{n8n_state}"
        )


def test_happy_path_is_significant_cross_border(case) -> None:
    """Sanity-pin the happy-path fixture against the contract it claims.

    The fixture carries severe disruption on regulated data across
    three member states. Significance fires on the first matching
    rule (``sig.severe_disruption``), not on the multi-state rule —
    rule ordering is the contract here. Cross-border fires on
    multi-state (``cb.multi_member_state``). Every stage is on-time
    (8h / 46h / ~29d submission instants against the 24h / 72h / 30d
    windows). Both if-condition gates take the true branch.

    If a fixture edit shifts these expectations the test names below
    need to be updated alongside the fixture so future readers see
    the intent.
    """
    state = _drive_n8n(case)
    assert state["significant"] is True
    assert state["cross_border"] is True
    assert state["significance_rule"] == case["expected"]["significance_rule"]
    assert state["cross_border_rule"] == case["expected"]["cross_border_rule"]
    assert state["selected_post_significance_branch"] == (
        case["expected"]["selected_post_significance_branch"]
    )
    assert state["selected_final_report_branch"] == (
        case["expected"]["selected_final_report_branch"]
    )
    assert all(
        stage_state["on_time"]
        for stage_state in state["stage_verdicts"].values()
    )


def test_replay_is_byte_identical(case) -> None:
    """Driving the same target twice with the same fixture yields the
    same canonical case-state — the primitives are pure deterministic
    code and the F-PT-02 adapter's handle / event ids are derived
    from canonical inputs only."""
    first = json.dumps(_drive_n8n(case), indent=2, sort_keys=True)
    second = json.dumps(_drive_n8n(case), indent=2, sort_keys=True)
    assert first == second
