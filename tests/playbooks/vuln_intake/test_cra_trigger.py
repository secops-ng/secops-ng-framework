"""Unit tests for the CRA Article 14 trigger and notification chain.

The behaviours worth pinning, because each encodes a regulatory reading that a
later refactor could plausibly get wrong:

* **Observed exploitation is the only trigger.** A 0.99 EPSS forecast with no
  observed exploitation must NOT engage Art. 14(1) — inventing an obligation
  puts an operator into a regulator conversation they do not owe.
* **The 24h/72h clocks run from awareness**, and the 14-day final-report clock
  runs from *remedy availability*, not awareness.
* **Naive timestamps are rejected** — a deadline that silently adopts the
  runtime's timezone is a wrong deadline.
* **Destination resolution is fail-closed** — an owed stage with no configured
  recipient raises rather than defaulting somewhere.
"""
from __future__ import annotations

import pytest

from content.playbooks.vuln_intake.primitives import (
    CRATriggerVerdict,
    NotificationChainPlan,
    assess_cra_reporting_trigger,
    build_notification_chain,
)
from content.playbooks.vuln_intake.primitives.cra_trigger import (
    EARLY_WARNING_REF,
    FINAL_REPORT_REF,
    NOTIFICATION_REF,
)

_AWARE = "2026-08-03T10:00:00Z"
_BASE = dict(cve_id="CVE-2026-0001", awareness_at=_AWARE)

_DESTS = {
    "early_warning": "csirt-coordinator-nl",
    "notification": "csirt-coordinator-nl",
    "final_report": "enisa-srp",
}


class TestTriggerEngagement:
    @pytest.mark.parametrize(
        "evidence",
        ["public_exploit_observed", "incident_confirmed", "kev_listed", "vendor_confirmed"],
    )
    def test_observed_exploitation_engages_article_14(self, evidence: str) -> None:
        v = assess_cra_reporting_trigger(**_BASE, exploitation_evidence=evidence)
        assert isinstance(v, CRATriggerVerdict)
        assert v.actively_exploited is True
        assert v.reporting_required is True
        assert v.early_warning_due_at == "2026-08-04T10:00:00Z"   # +24h
        assert v.notification_due_at == "2026-08-06T10:00:00Z"    # +72h
        assert EARLY_WARNING_REF in v.mapping_refs
        assert NOTIFICATION_REF in v.mapping_refs

    def test_no_evidence_engages_nothing(self) -> None:
        v = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="none")
        assert v.actively_exploited is False
        assert v.reporting_required is False
        assert v.early_warning_due_at is None
        assert v.notification_due_at is None
        assert v.mapping_refs == ()

    def test_high_epss_alone_does_not_engage_article_14(self) -> None:
        """A forecast is not an observation. This is the load-bearing case."""
        v = assess_cra_reporting_trigger(
            **_BASE, exploitation_evidence="none",
            cvss_base_score=9.8, epss_value="0.99",
        )
        assert v.reporting_required is False
        assert v.early_warning_due_at is None
        # ...but what was known is still on the record.
        joined = " ".join(v.reasons)
        assert "0.99" in joined and "9.8" in joined

    def test_scores_are_recorded_when_obligation_engaged(self) -> None:
        v = assess_cra_reporting_trigger(
            **_BASE, exploitation_evidence="kev_listed",
            cvss_base_score=7.5, epss_value="0.42",
        )
        joined = " ".join(v.reasons)
        assert "7.5" in joined and "0.42" in joined

    def test_verdict_is_frozen(self) -> None:
        v = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        with pytest.raises(AttributeError):
            v.reporting_required = False  # type: ignore[misc]


class TestFinalReportClock:
    def test_anchored_to_remedy_not_awareness(self) -> None:
        v = assess_cra_reporting_trigger(
            **_BASE, exploitation_evidence="kev_listed",
            remedy_available_at="2026-09-01T00:00:00Z",
        )
        assert v.final_report_due_at == "2026-09-15T00:00:00Z"   # +14d from remedy
        assert FINAL_REPORT_REF in v.mapping_refs

    def test_absent_until_remedy_known(self) -> None:
        v = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        assert v.final_report_due_at is None
        assert FINAL_REPORT_REF not in v.mapping_refs
        assert any("clock not started" in r for r in v.reasons)


class TestTimestampStrictness:
    def test_naive_awareness_rejected(self) -> None:
        with pytest.raises(ValueError, match="explicit UTC offset"):
            assess_cra_reporting_trigger(
                cve_id="CVE-2026-1", awareness_at="2026-08-03T10:00:00",
                exploitation_evidence="kev_listed",
            )

    def test_non_utc_offset_is_normalised(self) -> None:
        v = assess_cra_reporting_trigger(
            cve_id="CVE-2026-1", awareness_at="2026-08-03T12:00:00+02:00",
            exploitation_evidence="kev_listed",
        )
        assert v.early_warning_due_at == "2026-08-04T10:00:00Z"

    def test_garbage_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError, match="not a valid ISO-8601"):
            assess_cra_reporting_trigger(
                cve_id="CVE-2026-1", awareness_at="last tuesday",
                exploitation_evidence="none",
            )


class TestTriggerRejection:
    def test_unknown_evidence_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown exploitation_evidence"):
            assess_cra_reporting_trigger(**_BASE, exploitation_evidence="probably")  # type: ignore[arg-type]

    def test_empty_cve_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="cve_id"):
            assess_cra_reporting_trigger(
                cve_id="  ", awareness_at=_AWARE, exploitation_evidence="none")

    @pytest.mark.parametrize("bad", ["9.8", True, [9.8]])
    def test_non_numeric_cvss_rejected(self, bad: object) -> None:
        with pytest.raises(TypeError, match="cvss_base_score"):
            assess_cra_reporting_trigger(
                **_BASE, exploitation_evidence="none", cvss_base_score=bad)  # type: ignore[arg-type]


class TestTriggerDigest:
    def test_same_inputs_same_digest(self) -> None:
        a = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        b = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        assert a.inputs_digest == b.inputs_digest
        assert len(a.inputs_digest) == 16

    @pytest.mark.parametrize("override", [
        {"cve_id": "CVE-2026-0002"},
        {"awareness_at": "2026-08-03T11:00:00Z"},
        {"exploitation_evidence": "incident_confirmed"},
        {"cvss_base_score": 5.0},
        {"epss_value": "0.10"},
        {"remedy_available_at": "2026-09-01T00:00:00Z"},
    ])
    def test_single_input_change_changes_digest(self, override: dict) -> None:
        base = dict(**_BASE, exploitation_evidence="kev_listed")
        assert (
            assess_cra_reporting_trigger(**base).inputs_digest
            != assess_cra_reporting_trigger(**{**base, **override}).inputs_digest
        )


class TestNotificationChain:
    def test_plans_owed_stages_in_regulatory_order(self) -> None:
        t = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        plan = build_notification_chain(
            cve_id="CVE-2026-0001", trigger=t, destinations=_DESTS)
        assert isinstance(plan, NotificationChainPlan)
        assert plan.stages == ("early_warning", "notification")
        assert dict(plan.destinations)["early_warning"] == "csirt-coordinator-nl"

    def test_includes_final_report_once_remedy_known(self) -> None:
        t = assess_cra_reporting_trigger(
            **_BASE, exploitation_evidence="kev_listed",
            remedy_available_at="2026-09-01T00:00:00Z")
        plan = build_notification_chain(
            cve_id="CVE-2026-0001", trigger=t, destinations=_DESTS)
        assert plan.stages == ("early_warning", "notification", "final_report")

    def test_nothing_owed_plans_nothing(self) -> None:
        t = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="none")
        plan = build_notification_chain(
            cve_id="CVE-2026-0001", trigger=t, destinations={})
        assert plan.stages == ()
        assert any("no Art. 14 obligation" in r for r in plan.reasons)

    def test_missing_destination_fails_closed(self) -> None:
        t = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        with pytest.raises(ValueError, match="no destination configured"):
            build_notification_chain(
                cve_id="CVE-2026-0001", trigger=t,
                destinations={"early_warning": "csirt-nl"})

    def test_rejects_non_verdict_trigger(self) -> None:
        with pytest.raises(TypeError, match="CRATriggerVerdict"):
            build_notification_chain(
                cve_id="CVE-2026-1", trigger={"reporting_required": True},  # type: ignore[arg-type]
                destinations=_DESTS)

    def test_rejects_non_mapping_destinations(self) -> None:
        t = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        with pytest.raises(TypeError, match="destinations must be a mapping"):
            build_notification_chain(
                cve_id="CVE-2026-1", trigger=t, destinations=[("early_warning", "x")])  # type: ignore[arg-type]

    def test_plan_digest_covers_destinations(self) -> None:
        t = assess_cra_reporting_trigger(**_BASE, exploitation_evidence="kev_listed")
        a = build_notification_chain(cve_id="C", trigger=t, destinations=_DESTS)
        b = build_notification_chain(
            cve_id="C", trigger=t,
            destinations={**_DESTS, "notification": "csirt-other"})
        assert a.inputs_digest != b.inputs_digest
