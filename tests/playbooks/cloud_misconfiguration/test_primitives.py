from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import secops_extension
from content.playbooks.cloud_misconfiguration.primitives import (
    CLASSES,
    CONTROL_ANCHORS,
    SEVERITIES,
    InvalidEscalationError,
    InvalidOwnerNotificationError,
    InvalidPostureFindingError,
    InvalidRemediationAttemptError,
    InvalidResourceContextError,
    InvalidSuppressionError,
    InvalidVerificationError,
    compose_escalation,
    compose_owner_notification,
    compose_suppression_closure,
    normalise_posture_finding,
    record_remediation_attempt,
    resolve_resource_context,
    verify_remediation,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = REPO_ROOT / "content" / "playbooks" / "cloud_misconfiguration" / "playbook.cacao.json"
RULE = "rule:storage-public-read"
RES = "urn:cloud:storage:eu-central:payroll-exports"
BASELINE = "baseline:cis-storage:v3"
ACCOUNT = "account:finance-prod"
POOL = "team:cloud-platform"
POLICY = {"restricted": 2, "confidential": 1, "internal": 0, "public": -1}
ROUTING = {"informational": "ticket:queue-posture", "low": "ticket:queue-posture", "medium": "chat:cloud-sec",
           "high": "page:cloud-owner", "critical": "page:cloud-owner"}


def raw(**over) -> dict:
    f = {"finding_id": "finding:cspm-0001", "rule_ref": RULE, "resource_ref": RES, "baseline_ref": BASELINE,
         "misconfiguration_class": "public_exposure", "upstream_severity": "high", "source": "cspm_scan",
         "first_observed_at": "2026-10-20T09:30:00Z", "changed_at": "2026-10-20T09:05:00Z"}
    return {**f, **over}


def case(**over) -> dict:
    return normalise_posture_finding(raw(**over), "2026-10-20T09:31:00Z")


def inventory(classification="confidential", resource=RES, container=ACCOUNT) -> dict:
    return {"resource_ref": resource, "container_ref": container, "region": "eu-central",
            "resource_type": "object-store", "classification": classification}


def exc(ref="exc:1", kind="time_boxed_exception", rule=RULE, resource=RES, valid_from="2026-10-01T00:00:00Z",
        expires="2026-11-01T00:00:00Z", attestation=None) -> dict:
    return {"exception_ref": ref, "kind": kind, "rule_ref": rule, "resource_ref": resource,
            "owner_ref": "person:ciso-delegate", "valid_from": valid_from, "expires_at": expires,
            "attestation_ref": attestation}


def closure(ref="case:0900", outcome="verified", closed="2026-09-12T10:00:00Z", rule=RULE, container=ACCOUNT) -> dict:
    return {"case_ref": ref, "rule_ref": rule, "container_ref": container, "outcome": outcome, "closed_at": closed}


def context(c=None, inv="default", owner="default", exceptions=(), closures=(), policy=POLICY) -> dict:
    c = c or case()
    return resolve_resource_context(
        c, inventory() if inv == "default" else inv,
        {"owner_ref": "team:finance-platform", "active": True} if owner == "default" else owner,
        POOL, policy, list(exceptions), list(closures), "2026-10-20T09:32:00Z")


def notify(c=None, x=None) -> dict:
    c = c or case()
    return compose_owner_notification(c, x or context(c), ROUTING, "runbook:storage-public-read",
                                      "2026-10-20T09:35:00Z")


def attempt(mode="iac_change", change="change:pr-4411", approver="person:platform-lead",
            applied="2026-10-20T11:00:00Z") -> dict:
    return {"mode": mode, "change_ref": change, "approved_by": approver, "actor_ref": "person:finance-eng",
            "applied_at": applied}


def remediate(c=None, a=None) -> dict:
    c = c or case()
    return record_remediation_attempt(c, notify(c), a or attempt(), "2026-10-20T11:05:00Z")


def rescan(result="pass", evaluated="2026-10-20T11:20:00Z", baseline=BASELINE, rule=RULE, resource=RES) -> dict:
    return {"rule_ref": rule, "resource_ref": resource, "baseline_ref": baseline, "result": result,
            "evaluated_at": evaluated}


def verify(c=None, r=None, s=None) -> dict:
    c = c or case()
    return verify_remediation(c, r or remediate(c), s or rescan(), "2026-10-20T11:21:00Z")


# --------------------------------------------------------------------------- ingest finding


def test_a_finding_becomes_a_case_fingerprinted_by_rule_and_resource() -> None:
    c = case()
    assert c["fingerprint"] == hashlib.sha256(f"{RULE}\u001f{RES}".encode()).hexdigest()
    assert c["detection_latency_minutes"] == 25
    assert c["metric_stamps"] == ["kpi.mttd_cloud_misconfig@v1"]


@pytest.mark.parametrize("unset", [None, ""])
def test_detection_latency_is_left_unset_when_the_introducing_change_is_unknown(unset) -> None:
    c = case(changed_at=unset)
    assert c["changed_at"] is None and c["detection_latency_minutes"] is None
    assert c["metric_stamps"] == []


def test_the_same_deviation_from_a_guardrail_has_the_same_fingerprint() -> None:
    assert case(source="iac_guardrail", finding_id="finding:iac-77")["fingerprint"] == case()["fingerprint"]


def test_path_style_resource_identifiers_are_accepted() -> None:
    path = "/subscriptions/0000/resourceGroups/finance/providers/storage/accounts/payroll"
    assert case(resource_ref=path)["resource_ref"] == path


@pytest.mark.parametrize("over", [
    {"changed_at": "2026-10-20T09:31:00Z"},
    {"first_observed_at": "2026-10-20T09:40:00Z", "changed_at": None},
    {"misconfiguration_class": "drift"},
    {"upstream_severity": "severe"},
    {"source": "manual"},
    {"resource_ref": "not a resource"},
])
def test_a_malformed_or_out_of_order_finding_is_refused(over) -> None:
    with pytest.raises(InvalidPostureFindingError):
        case(**over)


def test_a_finding_with_extra_fields_is_refused() -> None:
    with pytest.raises(InvalidPostureFindingError):
        normalise_posture_finding({**raw(), "extra": 1}, "2026-10-20T09:31:00Z")


# --------------------------------------------------------------------------- enrich: owner and severity


def test_an_active_owner_is_used_and_the_classification_lifts_severity() -> None:
    x = context()
    assert x["owner_id"] == "team:finance-platform" and x["owner_fallback"] is None
    assert (x["upstream_severity"], x["severity"], x["severity_shift"], x["severity_basis"]) == \
        ("high", "critical", 1, "classification")
    assert x["resource_id"] == RES and x["container_ref"] == ACCOUNT and x["inventory_gap"] is False
    assert x["metric_stamps"] == ["kpi.cloud_posture_coverage@v1"]


@pytest.mark.parametrize(("owner", "reason"), [
    (None, "no_owner_record"),
    ("", "no_owner_record"),
    ({"owner_ref": "team:finance-platform", "active": False}, "owner_inactive"),
])
def test_a_missing_or_inactive_owner_falls_back_to_the_default_pool(owner, reason) -> None:
    x = context(owner=owner)
    assert x["owner_id"] == POOL and x["owner_fallback"] == reason


@pytest.mark.parametrize(("classification", "upstream", "severity"), [
    ("restricted", "high", "critical"),
    ("public", "medium", "low"),
    ("public", "informational", "informational"),
    ("internal", "low", "low"),
])
def test_the_classification_policy_shifts_severity_within_the_scale(classification, upstream, severity) -> None:
    x = context(c=case(upstream_severity=upstream), inv=inventory(classification))
    assert x["severity"] == severity


def test_an_unknown_resource_is_an_inventory_gap_and_is_never_lowered() -> None:
    x = context(inv=None, closures=[closure()])
    assert x["inventory_gap"] is True and x["container_ref"] is None
    assert (x["severity"], x["severity_basis"]) == ("high", "inventory_gap")
    assert x["recurrence"] is None and x["metric_stamps"] == []


def test_an_unmapped_classification_leaves_severity_as_reported() -> None:
    x = context(inv=inventory("secret"))
    assert (x["severity"], x["severity_shift"], x["severity_basis"]) == ("high", 0, "unmapped_classification")


@pytest.mark.parametrize("policy", [{"confidential": True}, {"confidential": 3}, {"confidential": 1.0}, []])
def test_a_malformed_severity_policy_is_refused(policy) -> None:
    with pytest.raises(InvalidResourceContextError):
        context(policy=policy)


def test_an_inventory_record_for_another_resource_is_refused() -> None:
    with pytest.raises(InvalidResourceContextError, match="different resource"):
        context(inv=inventory(resource="urn:cloud:storage:eu-central:other"))


# --------------------------------------------------------------------------- enrich: suppression


def test_a_live_exact_exception_marks_a_known_false_positive() -> None:
    x = context(exceptions=[exc()])
    assert x["known_false_positive"] is True
    assert x["suppression"]["exception_ref"] == "exc:1" and x["rejected_exceptions"] == []


def test_no_matching_entry_is_a_real_false() -> None:
    x = context(exceptions=[exc(resource="urn:cloud:storage:eu-central:other"), exc("exc:2", rule="rule:other")])
    assert x["known_false_positive"] is False and x["suppression"] is None and x["rejected_exceptions"] == []


@pytest.mark.parametrize(("entry", "reason"), [
    (exc(expires="2026-10-15T00:00:00Z"), "expired"),
    (exc(expires=None), "open_ended"),
    (exc(expires=""), "open_ended"),
    (exc(valid_from="2026-10-25T00:00:00Z", expires="2026-12-01T00:00:00Z"), "not_yet_valid"),
    (exc(kind="compensating_control"), "unattested"),
])
def test_a_matching_entry_that_is_not_live_is_rejected_with_its_reason(entry, reason) -> None:
    x = context(exceptions=[entry])
    assert x["known_false_positive"] is False
    assert x["rejected_exceptions"] == [{"exception_ref": "exc:1", "kind": entry["kind"], "reason": reason}]


def test_an_attested_compensating_control_suppresses() -> None:
    x = context(exceptions=[exc(kind="compensating_control", attestation="attest:waf-shield")])
    assert x["known_false_positive"] is True and x["suppression"]["attestation_ref"] == "attest:waf-shield"


def test_of_several_live_entries_the_longest_running_is_linked() -> None:
    x = context(exceptions=[exc("exc:a"), exc("exc:b", expires="2026-12-01T00:00:00Z"), exc("exc:c")])
    assert x["suppression"]["exception_ref"] == "exc:b"


def test_a_duplicate_ledger_reference_is_refused() -> None:
    with pytest.raises(InvalidResourceContextError, match="twice"):
        context(exceptions=[exc(), exc()])


def test_an_entry_that_expires_before_it_starts_is_refused() -> None:
    with pytest.raises(InvalidResourceContextError):
        context(exceptions=[exc(valid_from="2026-11-02T00:00:00Z")])


# --------------------------------------------------------------------------- enrich: recurrence


def test_a_finding_after_a_verified_remediation_on_the_same_container_recurs() -> None:
    x = context(closures=[closure(), closure("case:0950", closed="2026-10-01T10:00:00Z")])
    assert x["recurrence"] is True and x["recurs_after_case_ref"] == "case:0950"


@pytest.mark.parametrize("prior", [
    closure(outcome="suppressed"),
    closure(outcome="escalated"),
    closure(closed="2026-10-21T00:00:00Z"),
    closure(container="account:other"),
    closure(rule="rule:other"),
])
def test_only_a_prior_verified_remediation_of_the_same_rule_and_container_counts(prior) -> None:
    x = context(closures=[prior])
    assert x["recurrence"] is False and x["recurs_after_case_ref"] is None


def test_resolution_before_ingestion_is_refused() -> None:
    with pytest.raises(InvalidResourceContextError):
        resolve_resource_context(case(), inventory(), None, POOL, POLICY, [], [], "2026-10-20T09:00:00Z")


# --------------------------------------------------------------------------- suppress and close


def test_a_suppression_closes_on_the_matched_entry_without_paging() -> None:
    c = case()
    x = context(c, exceptions=[exc()])
    s = compose_suppression_closure(c, x, "2026-10-20T09:33:00Z")
    assert s["exception_ref"] == "exc:1" and s["exception_expires_at"] == "2026-11-01T00:00:00Z"
    assert s["pages"] is False and s["remediation_attempted"] is False
    assert s["metric_stamps"] == ["kri.recurring_cloud_misconfig@v1"]
    assert s == compose_suppression_closure(c, x, "2026-10-20T09:33:00Z")


@pytest.mark.parametrize("flag", [False, "true", 1])
def test_suppression_is_refused_unless_the_gate_cleared_the_finding(flag) -> None:
    c = case()
    x = {**context(c, exceptions=[exc()]), "known_false_positive": flag}
    with pytest.raises(InvalidSuppressionError):
        compose_suppression_closure(c, x, "2026-10-20T09:33:00Z")


def test_a_closure_after_the_exception_lapsed_is_refused() -> None:
    c = case()
    with pytest.raises(InvalidSuppressionError, match="expired"):
        compose_suppression_closure(c, context(c, exceptions=[exc()]), "2026-11-01T00:00:00Z")


def test_a_context_for_another_finding_is_refused() -> None:
    with pytest.raises(InvalidSuppressionError, match="different finding"):
        compose_suppression_closure(case(finding_id="finding:other"), context(exceptions=[exc()]),
                                    "2026-10-20T09:33:00Z")


# --------------------------------------------------------------------------- notify owner


def test_the_owner_is_notified_on_the_channel_bound_to_the_resolved_severity() -> None:
    n = notify()
    assert n["severity"] == "critical" and n["channel_ref"] == "page:cloud-owner"
    assert n["owner_id"] == "team:finance-platform" and n["runbook_ref"] == "runbook:storage-public-read"
    assert n["baseline_ref"] == BASELINE and n["metric_stamps"] == []


def test_a_default_pool_notification_says_so() -> None:
    c = case()
    n = notify(c, context(c, owner=None))
    assert n["owner_id"] == POOL and n["owner_fallback"] == "no_owner_record"


def test_a_routing_table_missing_a_severity_is_refused() -> None:
    c = case()
    routing = {k: v for k, v in ROUTING.items() if k != "informational"}
    with pytest.raises(InvalidOwnerNotificationError):
        compose_owner_notification(c, context(c), routing, "runbook:x", "2026-10-20T09:35:00Z")


def test_a_suppressed_finding_is_not_notified() -> None:
    c = case()
    with pytest.raises(InvalidOwnerNotificationError, match="suppressed"):
        notify(c, context(c, exceptions=[exc()]))


# --------------------------------------------------------------------------- guided remediation


def test_an_attested_automated_change_is_recorded_with_its_control_anchors() -> None:
    r = remediate()
    assert r["mode"] == "iac_change" and r["change_ref"] == "change:pr-4411"
    assert r["approved_by"] == "person:platform-lead" and r["control_anchors"] == ["CM-6", "AC-3", "AC-6"]


def test_a_manual_change_needs_no_approver_but_names_its_actor() -> None:
    r = remediate(a=attempt(mode="manual_change", approver=None))
    assert r["approved_by"] is None and r["actor_ref"] == "person:finance-eng"


@pytest.mark.parametrize("a", [
    attempt(change=None),
    attempt(change=""),
    attempt(approver=None),
    attempt(mode="runbook_execution", approver=""),
    attempt(applied="2026-10-20T09:00:00Z"),
    attempt(applied="2026-10-20T11:06:00Z"),
    attempt(mode="hotfix"),
])
def test_an_unattested_or_out_of_order_attempt_is_refused(a) -> None:
    with pytest.raises(InvalidRemediationAttemptError):
        remediate(a=a)


@pytest.mark.parametrize(("cls", "anchors"), [
    ("network_exposure", ["CM-6", "SC-7"]),
    ("missing_encryption", ["CM-6", "SC-28"]),
    ("baseline_deviation", ["CM-6"]),
])
def test_the_control_anchors_follow_the_misconfiguration_class(cls, anchors) -> None:
    assert remediate(c=case(misconfiguration_class=cls))["control_anchors"] == anchors


# --------------------------------------------------------------------------- re-scan


def test_a_pass_of_the_same_rule_after_the_change_verifies_the_remediation() -> None:
    v = verify()
    assert v["remediation_verified"] is True and v["reason"] is None
    assert v["remediation_latency_minutes"] == 110
    assert v["metric_stamps"] == ["kpi.mttr_cloud_misconfig@v1", "kpi.cloud_posture_coverage@v1"]


@pytest.mark.parametrize(("s", "reason", "stamps"), [
    (rescan("fail"), "rule_still_fires", ["kpi.cloud_posture_coverage@v1"]),
    (rescan("not_evaluated"), "not_evaluated", []),
    (rescan("not_evaluated", evaluated="2026-10-20T10:00:00Z"), "not_evaluated", []),
    (rescan("pass", evaluated="2026-10-20T10:59:00Z"), "evaluated_before_change", ["kpi.cloud_posture_coverage@v1"]),
    (rescan("pass", evaluated="2026-10-20T11:00:00Z"), "evaluated_before_change", ["kpi.cloud_posture_coverage@v1"]),
    (rescan("pass", baseline="baseline:cis-storage:v4"), "baseline_changed", ["kpi.cloud_posture_coverage@v1"]),
    (rescan("fail", baseline="baseline:cis-storage:v4"), "baseline_changed", ["kpi.cloud_posture_coverage@v1"]),
])
def test_anything_short_of_a_fresh_pass_on_the_same_baseline_is_unverified(s, reason, stamps) -> None:
    v = verify(s=s)
    assert v["remediation_verified"] is False and v["reason"] == reason
    assert v["remediation_latency_minutes"] is None and v["metric_stamps"] == stamps


@pytest.mark.parametrize("s", [rescan(rule="rule:other"), rescan(resource="urn:cloud:storage:eu-central:other")])
def test_a_re_scan_of_another_rule_or_resource_is_refused(s) -> None:
    with pytest.raises(InvalidVerificationError, match="different rule or resource"):
        verify(s=s)


def test_a_verdict_before_the_evaluation_is_refused() -> None:
    c = case()
    with pytest.raises(InvalidVerificationError):
        verify_remediation(c, remediate(c), rescan(), "2026-10-20T11:10:00Z")


# --------------------------------------------------------------------------- escalate


def escalate(c, x, r, v) -> dict:
    return compose_escalation(c, x, r, v, "page:security-engineering", "2026-10-20T11:22:00Z")


def test_an_unverified_remediation_escalates_with_the_attempt_and_the_evidence() -> None:
    c = case()
    x = context(c, closures=[closure()])
    r = remediate(c)
    v = verify(c, r, rescan("fail"))
    e = escalate(c, x, r, v)
    assert e["attempted_remediation"]["change_ref"] == "change:pr-4411"
    assert e["failing_evidence"]["reason"] == "rule_still_fires" and e["failing_evidence"]["result"] == "fail"
    assert e["recurrence"] is True and e["recurs_after_case_ref"] == "case:0900"
    assert e["paging_channel_ref"] == "page:security-engineering" and e["severity"] == "critical"
    assert e["metric_stamps"] == ["kri.recurring_cloud_misconfig@v1"]


def test_a_verified_remediation_is_not_escalated() -> None:
    c = case()
    r = remediate(c)
    with pytest.raises(InvalidEscalationError, match="remediation_verified is False"):
        escalate(c, context(c), r, verify(c, r))


def test_a_verification_of_another_attempt_is_refused() -> None:
    c = case()
    r = remediate(c)
    other = remediate(c, attempt(change="change:pr-4412"))
    with pytest.raises(InvalidEscalationError, match="different remediation"):
        escalate(c, context(c), other, verify(c, r, rescan("fail")))


# --------------------------------------------------------------------------- catalogue contract


def test_each_step_stamps_only_metrics_it_declares() -> None:
    doc = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
    declared = set(secops_extension(doc)["metric_refs"])
    steps = {s["name"]: set((secops_extension(s) or {}).get("metric_refs") or []) for s in doc["workflow"].values()}
    c = case()
    x = context(c)
    r = remediate(c)
    v = verify(c, r)
    failed = verify(c, r, rescan("fail"))
    suppressed_context = context(c, exceptions=[exc()])
    for step, out in (("ingest finding", c), ("enrich resource and owner", x),
                      ("suppress and close", compose_suppression_closure(c, suppressed_context,
                                                                         "2026-10-20T09:33:00Z")),
                      ("notify owner", notify(c)), ("guided remediation", r), ("re-scan", v),
                      ("escalate", escalate(c, x, r, failed))):
        assert set(out["metric_stamps"]) <= declared and set(out["metric_stamps"]) <= steps[step], step


def test_the_classes_and_anchors_are_the_cookbook_branches() -> None:
    assert CLASSES == ("public_exposure", "over_permissive_identity", "network_exposure", "missing_encryption",
                       "baseline_deviation")
    assert all(anchors[0] == "CM-6" for anchors in CONTROL_ANCHORS.values())
    assert SEVERITIES == ("informational", "low", "medium", "high", "critical")
