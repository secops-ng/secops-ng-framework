"""Unit coverage for content/playbooks/phishing_triage/primitives (CORE-PRIM)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from content.playbooks.phishing_triage.primitives import (
    InvalidIntentResolutionError,
    InvalidMessageAssessmentError,
    InvalidReportedMessageError,
    InvalidResponseDirectiveError,
    InvalidSuppressionError,
    assess_reported_message,
    bec_response,
    case_fingerprint,
    compose_suppression_record,
    credential_harvest_response,
    malware_attachment_response,
    manual_review_route,
    phishing_response,
    resolve_intent,
    validate_reported_message,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SHA_A = "a" * 64
SHA_B = "b" * 64

RAW = {
    "message_id": "<lure-0001@mail.example>",
    "sender": "Billing@Pay-Portal.Example",
    "recipients": ["bob@corp.example", "alice@corp.example", "bob@corp.example"],
    "subject": "  Your   invoice\tis overdue ",
    "received_at": "2026-09-23T08:00:00Z",
    "urls": ["HTTPS://Login.Pay-Portal.Example/Reset?id=7#frag", "https://brand.example/help"],
    "attachments": [
        {"filename": "invoice.pdf.exe", "sha256": SHA_A.upper(), "size_bytes": 4096},
        {"filename": "logo.png", "sha256": SHA_B, "size_bytes": 512},
    ],
}
LURE = "https://login.pay-portal.example/Reset?id=7"
BRAND = "https://brand.example/help"
AUTH_PASS = {"spf": "pass", "dkim": "pass", "dmarc": "pass"}
AUTH_FAIL = {"spf": "fail", "dkim": "none", "dmarc": "fail"}


def envelope(**overrides) -> dict:
    raw = copy.deepcopy(RAW)
    raw.update(overrides)
    return validate_reported_message(raw, "user_report")


def assess(message=None, *, auth=AUTH_PASS, urls=None, atts=None, benign=(), seen=(),
           as_of="2026-09-23T09:00:00Z", window=24) -> dict:
    return assess_reported_message(
        message or envelope(), dict(auth),
        {LURE: "malicious", BRAND: "clean"} if urls is None else urls,
        {SHA_A: "malicious", SHA_B: "clean"} if atts is None else atts,
        list(benign), list(seen), as_of, window,
    )


def intent(label: str) -> dict:
    return resolve_intent({"label": label, "confidence": 0.99}, 80)


# --------------------------------------------------------------------------- intake


def test_intake_canonicalises_the_envelope() -> None:
    env = envelope()
    assert env["sender"] == "Billing@pay-portal.example"      # local part kept, domain lowered
    assert env["sender_domain"] == "pay-portal.example"
    assert env["recipients"] == ["alice@corp.example", "bob@corp.example"]
    assert env["subject"] == "Your invoice is overdue"
    assert env["urls"] == [BRAND, LURE]                          # sorted; fragment dropped; path case kept
    assert [a["sha256"] for a in env["attachments"]] == [SHA_A, SHA_B]
    assert env["report_source"] == "user_report"


def test_intake_is_independent_of_listing_order() -> None:
    raw = copy.deepcopy(RAW)
    raw["recipients"].reverse(); raw["urls"].reverse(); raw["attachments"].reverse()
    assert validate_reported_message(raw, "user_report") == envelope()


def test_intake_keeps_userinfo_so_the_real_host_stays_visible() -> None:
    env = envelope(urls=["http://brand.example@EVIL.example/x"])
    assert env["urls"] == ["http://brand.example@evil.example/x"]


def test_intake_rejects_a_misspelled_key_instead_of_ignoring_it() -> None:
    raw = copy.deepcopy(RAW)
    raw["attachements"] = raw.pop("attachments")
    with pytest.raises(InvalidReportedMessageError, match="unknown \\['attachements'\\]"):
        validate_reported_message(raw, "user_report")


@pytest.mark.parametrize("bad", [
    {"urls": ["mailto:x@y.example"]},
    {"urls": ["https:///no-host"]},
    {"sender": "not-an-address"},
    {"recipients": []},
    {"received_at": "2026-09-23 08:00:00"},
    {"attachments": [{"filename": "a", "sha256": SHA_A, "size_bytes": True}]},
    {"attachments": [{"filename": "a", "sha256": SHA_A, "size_bytes": 1},
                     {"filename": "b", "sha256": SHA_A, "size_bytes": 2}]},
])
def test_intake_rejects_grammar_violations(bad: dict) -> None:
    with pytest.raises(InvalidReportedMessageError):
        envelope(**bad)


def test_intake_accepts_an_empty_subject_and_a_closed_report_source() -> None:
    assert envelope(subject="   ")["subject"] == ""
    with pytest.raises(InvalidReportedMessageError, match="report_source"):
        validate_reported_message(copy.deepcopy(RAW), "helpdesk_ticket")


# --------------------------------------------------------------------------- enrichment


def test_fingerprint_names_the_case_not_the_delivery() -> None:
    base = case_fingerprint(envelope())
    assert case_fingerprint(envelope(recipients=["carol@corp.example"],
                                     received_at="2026-09-24T00:00:00Z")) == base
    assert case_fingerprint(envelope(subject="Different lure")) != base
    assert case_fingerprint(envelope(sender="Other@pay-portal.example")) != base


def test_already_seen_collapses_even_when_the_message_is_malicious() -> None:
    fp = case_fingerprint(envelope())
    result = assess(seen=[{"fingerprint": fp, "case_ref": "case:1", "seen_at": "2026-09-23T01:00:00Z"}])
    assert result["benign_or_seen"] is True
    assert result["suppression"] == {"reason": "already_seen", "matched_ref": "case:1",
                                     "refused_benign_claim": None}
    assert LURE in result["flagged_indicators"]


def test_seen_window_boundary_and_most_recent_match() -> None:
    fp = case_fingerprint(envelope())
    edge = {"fingerprint": fp, "case_ref": "case:old", "seen_at": "2026-09-22T09:00:00Z"}   # exactly 24h
    newer = {"fingerprint": fp, "case_ref": "case:new", "seen_at": "2026-09-23T08:30:00Z"}
    stale = {"fingerprint": fp, "case_ref": "case:stale", "seen_at": "2026-09-22T08:59:59Z"}
    assert assess(seen=[edge])["suppression"]["matched_ref"] == "case:old"
    assert assess(seen=[edge, newer])["suppression"]["matched_ref"] == "case:new"
    assert assess(seen=[stale])["benign_or_seen"] is False


def test_a_seen_case_recorded_after_as_of_fails_loud() -> None:
    fp = case_fingerprint(envelope())
    with pytest.raises(InvalidMessageAssessmentError, match="after as_of"):
        assess(seen=[{"fingerprint": fp, "case_ref": "case:1", "seen_at": "2026-09-23T10:00:00Z"}])


def test_known_benign_sender_needs_dmarc_pass_and_clean_indicators() -> None:
    clean_urls, clean_atts = {LURE: "clean", BRAND: "clean"}, {SHA_A: "clean", SHA_B: "clean"}
    ok = assess(benign=["pay-portal.example"], urls=clean_urls, atts=clean_atts)
    assert ok["benign_or_seen"] is True
    assert ok["suppression"]["reason"] == "known_benign_sender"
    assert ok["suppression"]["matched_ref"] == "pay-portal.example"

    spoofed = assess(benign=["Billing@pay-portal.example"], auth=AUTH_FAIL,
                     urls=clean_urls, atts=clean_atts)
    assert spoofed["benign_or_seen"] is False
    assert spoofed["suppression"]["refused_benign_claim"] == "dmarc_not_pass"

    compromised = assess(benign=["pay-portal.example"], urls={LURE: "suspicious", BRAND: "clean"},
                         atts=clean_atts)
    assert compromised["benign_or_seen"] is False
    assert compromised["suppression"]["refused_benign_claim"] == "flagged_indicator"


def test_verdict_join() -> None:
    joined = assess(urls={"https://LOGIN.pay-portal.example/Reset?id=7": "Malicious"}, atts={})
    assert {u["url"]: u["verdict"] for u in joined["urls"]} == {BRAND: "unknown", LURE: "malicious"}
    assert all(a["verdict"] == "unknown" for a in joined["attachments"])
    with pytest.raises(InvalidMessageAssessmentError, match="does not carry"):
        assess(urls={"https://elsewhere.example/": "clean"})


@pytest.mark.parametrize("kwargs", [
    {"auth": {"spf": "pass", "dkim": "pass"}},
    {"auth": {"spf": "pass", "dkim": "pass", "dmarc": "maybe"}},
    {"window": True},
    {"window": 0},
    {"as_of": "yesterday"},
    {"benign": ["not a domain"]},
])
def test_enrichment_rejects_malformed_inputs(kwargs: dict) -> None:
    with pytest.raises(InvalidMessageAssessmentError):
        assess(**kwargs)


# --------------------------------------------------------------------------- suppression


def test_suppression_record_for_each_lane() -> None:
    fp = case_fingerprint(envelope())
    seen = assess(seen=[{"fingerprint": fp, "case_ref": "case:1", "seen_at": "2026-09-23T01:00:00Z"}])
    record = compose_suppression_record(seen, "2026-09-23T09:05:00Z")
    assert record["linked_case_ref"] == "case:1" and record["benign_sender_ref"] is None
    assert record["pages"] is False and record["notifications"] == []
    assert record == compose_suppression_record(seen, "2026-09-23T09:05:00Z")
    assert record["suppression_id"] != compose_suppression_record(seen, "2026-09-23T09:06:00Z")["suppression_id"]

    benign = assess(benign=["pay-portal.example"], urls={LURE: "clean", BRAND: "clean"},
                    atts={SHA_A: "clean", SHA_B: "clean"})
    record = compose_suppression_record(benign, "2026-09-23T09:05:00Z")
    assert record["benign_sender_ref"] == "pay-portal.example" and record["linked_case_ref"] is None


@pytest.mark.parametrize("gate", [False, "true", 1, None])
def test_suppression_refuses_unless_the_gate_cleared_the_report(gate) -> None:
    fp = case_fingerprint(envelope())
    cleared = assess(seen=[{"fingerprint": fp, "case_ref": "case:1", "seen_at": "2026-09-23T01:00:00Z"}])
    cleared["benign_or_seen"] = gate
    with pytest.raises(InvalidSuppressionError, match="only when benign_or_seen is True"):
        compose_suppression_record(cleared, "2026-09-23T09:05:00Z")


# --------------------------------------------------------------------------- classification


@pytest.mark.parametrize(("output", "expected_intent", "reason"), [
    ({"label": "credential_harvest", "confidence": 0.9}, "credential_harvest", "accepted"),
    ({"label": "Phishing ", "confidence": 0.8}, "phishing", "accepted"),               # at threshold
    ({"label": "phishing", "confidence": 0.79}, "unknown", "below_confidence_threshold"),
    ({"label": "spam", "confidence": 1.0}, "unknown", "label_outside_enumeration"),
    ({"label": "unknown", "confidence": 1.0}, "unknown", "classifier_abstained"),
])
def test_intent_resolution(output: dict, expected_intent: str, reason: str) -> None:
    result = resolve_intent(output, 80)
    assert (result["intent"], result["reason"]) == (expected_intent, reason)


def test_an_out_of_enumeration_label_is_kept_for_diagnosis() -> None:
    assert resolve_intent({"label": "SPAM", "confidence": 1.0}, 50)["classifier_label"] == "spam"


@pytest.mark.parametrize(("output", "threshold"), [
    ({"label": "phishing", "confidence": True}, 80),
    ({"label": "phishing", "confidence": float("nan")}, 80),
    ({"label": "phishing", "confidence": 1.5}, 80),
    ({"label": "phishing", "confidence": 0.9}, 0),
    ({"label": "phishing", "confidence": 0.9}, 101),
    ({"label": "phishing", "confidence": 0.9}, True),
    ({"label": "phishing", "confidence": 0.9}, 0.8),
    ({"label": "phishing", "confidence": 0.9}, "80"),
    ({"label": "phishing", "confidence": 0.9, "extra": 1}, 80),
    ({"label": 7, "confidence": 0.9}, 80),
])
def test_malformed_classifier_output_fails_loud(output: dict, threshold) -> None:
    with pytest.raises(InvalidIntentResolutionError):
        resolve_intent(output, threshold)


# --------------------------------------------------------------------------- response


def test_every_branch_refuses_an_intent_the_switch_did_not_route_to_it() -> None:
    a = assess()
    wrong = intent("phishing")
    for call in (
        lambda: credential_harvest_response(a, wrong, []),
        lambda: malware_attachment_response(a, wrong, []),
        lambda: bec_response(a, wrong, []),
        lambda: manual_review_route(a, wrong, "queue:soc"),
    ):
        with pytest.raises(InvalidResponseDirectiveError, match="route on intent sent 'phishing'"):
            call()
    with pytest.raises(InvalidResponseDirectiveError):
        phishing_response(a, intent("credential_harvest"))


def test_phishing_blocks_only_flagged_urls() -> None:
    d = phishing_response(assess(urls={LURE: "suspicious", BRAND: "unknown"}), intent("phishing"))
    assert d["actions"][0] == {"action": "quarantine_message", "message_id": "<lure-0001@mail.example>",
                               "mailboxes": ["alice@corp.example", "bob@corp.example"]}
    assert {"action": "block_sender", "sender": "Billing@pay-portal.example"} in d["actions"]
    assert [x["url"] for x in d["actions"] if x["action"] == "block_url"] == [LURE]


def test_credential_harvest_blocks_unverdicted_pages_and_resets_clickers() -> None:
    clicks = [{"identity": "bob@corp.example", "url": LURE, "clicked_at": "2026-09-23T08:10:00Z"},
              {"identity": "alice@corp.example", "url": LURE.upper().replace("RESET?ID=7", "Reset?id=7"),
               "clicked_at": "2026-09-23T08:11:00Z"},
              {"identity": "bob@corp.example", "url": LURE, "clicked_at": "2026-09-23T08:12:00Z"}]
    d = credential_harvest_response(assess(urls={LURE: "unknown", BRAND: "clean"}),
                                    intent("credential_harvest"), clicks)
    assert [x["url"] for x in d["actions"] if x["action"] == "block_url"] == [LURE]
    assert [x["identity"] for x in d["actions"] if x["action"] == "force_credential_reset"] == [
        "alice@corp.example", "bob@corp.example"]
    assert d["simulation"] is False and d["notify"] == ["identity_team"]
    with pytest.raises(InvalidResponseDirectiveError, match="does not carry"):
        credential_harvest_response(assess(), intent("credential_harvest"),
                                    [{"identity": "x", "url": "https://other.example/",
                                      "clicked_at": "2026-09-23T08:10:00Z"}])


def test_an_empty_campaign_ref_is_not_a_simulation() -> None:
    """n8n surfaces an unset playbook variable as the empty string."""
    clicks = [{"identity": "bob@corp.example", "url": LURE, "clicked_at": "2026-09-23T08:10:00Z"}]
    d = credential_harvest_response(assess(), intent("credential_harvest"), clicks,
                                    simulation_campaign_ref="")
    assert d["simulation"] is False
    assert any(x["action"] == "force_credential_reset" for x in d["actions"])


def test_the_threshold_boundary_holds_for_decimal_confidences() -> None:
    """0.29 * 100 is 28.999999999999996; comparing against 29 / 100 is exact."""
    at_boundary = resolve_intent({"label": "phishing", "confidence": 0.29}, 29)
    assert (at_boundary["intent"], at_boundary["reason"]) == ("phishing", "accepted")


def test_a_sanctioned_simulation_records_clicks_and_contains_nothing() -> None:
    clicks = [{"identity": "bob@corp.example", "url": LURE, "clicked_at": "2026-09-23T08:10:00Z"}]
    d = credential_harvest_response(assess(), intent("credential_harvest"), clicks,
                                    simulation_campaign_ref="sim:2026-q3")
    assert d["actions"] == [{"action": "record_simulation_clicks", "campaign_ref": "sim:2026-q3",
                             "identities": ["bob@corp.example"]}]
    assert d["simulation"] is True and d["metric_stamps"] == ["kpi.phishing_sim_click_rate@v1"]


def test_malware_blocks_non_clean_attachments_and_hands_off_opened_hosts() -> None:
    opens = [{"identity": "bob@corp.example", "host_ref": "host:lt-42", "sha256": SHA_A.upper(),
              "opened_at": "2026-09-23T08:20:00Z"},
             {"identity": "bob@corp.example", "host_ref": "host:lt-42", "sha256": SHA_B,
              "opened_at": "2026-09-23T08:21:00Z"}]
    d = malware_attachment_response(assess(atts={SHA_A: "unknown", SHA_B: "clean"}),
                                    intent("malware_attached"), opens)
    assert [x["sha256"] for x in d["actions"] if x["action"] == "block_attachment"] == [SHA_A]
    assert [x for x in d["actions"] if x["action"] == "hand_off_host_investigation"] == [
        {"action": "hand_off_host_investigation", "host_ref": "host:lt-42",
         "identity": "bob@corp.example", "sha256s": [SHA_A, SHA_B]}]
    with pytest.raises(InvalidResponseDirectiveError, match="not an attachment"):
        malware_attachment_response(assess(), intent("malware_attached"),
                                    [dict(opens[0], sha256="c" * 64)])
    no_attachments = assess(envelope(attachments=[]), atts={})
    with pytest.raises(InvalidResponseDirectiveError, match="carries no attachment"):
        malware_attachment_response(no_attachments, intent("malware_attached"), [])


def test_bec_distinguishes_compromise_from_impersonation() -> None:
    real = bec_response(assess(), intent("business_email_compromise"), ["pay:9", "pay:3", "pay:9"])
    assert real["sender_assessment"] == "compromised_sender_account"
    assert [x["payment_ref"] for x in real["actions"] if x["action"] == "freeze_payment_instruction"] == [
        "pay:3", "pay:9"]
    assert real["actions"][-1]["playbook"] == "playbook.identity_compromise@v1"
    spoofed = bec_response(assess(auth=AUTH_FAIL), intent("business_email_compromise"), [])
    assert spoofed["sender_assessment"] == "impersonated_sender"
    assert "kri.regulator_notification_overrun@v1" in real["metric_stamps"]


def test_manual_review_tells_the_analyst_why_it_is_theirs() -> None:
    resolution = resolve_intent({"label": "spam", "confidence": 1.0}, 80)
    d = manual_review_route(assess(), resolution, "queue:soc-l2")
    step = d["actions"][0]
    assert step["queue_ref"] == "queue:soc-l2"
    assert step["classifier"]["reason"] == "label_outside_enumeration"
    assert step["evidence"]["flagged_indicators"] == sorted([LURE, SHA_A])
    assert d["label_feedback_requested"] is True


def test_directive_ids_are_deterministic_and_intent_specific() -> None:
    a = assess()
    first = phishing_response(a, intent("phishing"))
    assert first == phishing_response(a, intent("phishing"))
    assert first["directive_id"] != bec_response(a, intent("business_email_compromise"), [])["directive_id"]


def _all_outputs() -> list[dict]:
    a = assess()
    fp = case_fingerprint(envelope())
    seen = assess(seen=[{"fingerprint": fp, "case_ref": "case:1", "seen_at": "2026-09-23T01:00:00Z"}])
    click = [{"identity": "bob@corp.example", "url": LURE, "clicked_at": "2026-09-23T08:10:00Z"}]
    return [
        compose_suppression_record(seen, "2026-09-23T09:05:00Z"),
        phishing_response(a, intent("phishing")),
        credential_harvest_response(a, intent("credential_harvest"), click),
        credential_harvest_response(a, intent("credential_harvest"), click, "sim:q3"),
        malware_attachment_response(a, intent("malware_attached"), []),
        bec_response(a, intent("business_email_compromise"), []),
        manual_review_route(a, resolve_intent({"label": "unknown", "confidence": 1}, 50), "queue:x"),
    ]


def test_every_stamped_metric_is_declared_by_the_playbook() -> None:
    playbook = json.loads((REPO_ROOT / "content/playbooks/phishing_triage/playbook.cacao.json")
                          .read_text(encoding="utf-8"))
    declared = set(playbook["x_secops_ng"]["metric_refs"])
    stamped = {m for out in _all_outputs() for m in out["metric_stamps"]}
    assert stamped <= declared, f"undeclared metrics stamped: {sorted(stamped - declared)}"


def test_outputs_are_json_native() -> None:
    for out in _all_outputs():
        assert json.loads(json.dumps(out)) == out


def test_end_to_end_a_report_flows_from_intake_to_a_directive() -> None:
    env = validate_reported_message(copy.deepcopy(RAW), "mailbox_sweep")
    a = assess_reported_message(env, AUTH_FAIL, {LURE: "malicious"}, {SHA_A: "malicious"},
                                ["pay-portal.example"], [], "2026-09-23T09:00:00Z", 24)
    assert a["benign_or_seen"] is False                    # spoofed benign sender refused
    resolution = resolve_intent({"label": "malware_attached", "confidence": 0.95}, 80)
    d = malware_attachment_response(a, resolution, [])
    assert d["message_id"] == env["message_id"] and d["fingerprint"] == case_fingerprint(env)
    assert [x["sha256"] for x in d["actions"] if x["action"] == "block_attachment"] == [SHA_A, SHA_B]
