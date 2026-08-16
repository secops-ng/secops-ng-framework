"""Unit tests for the codebase_vuln_management primitives.

Closes the #937 audit's coverage gap for this playbook: the golden tests
pinned the emitters' *output* (and asserted the emitted source imports
these primitives — as strings) while nothing executed the primitives
themselves. The behaviours pinned here are the ones a later change could
quietly reverse:

* ``pin_sbom_content_hash`` is format-gated — a typo'd or unknown SBOM
  format fails loud rather than silently pinning the wrong bytes.
* ``normalise_findings`` never coerces a missing or unrecognised
  severity to ``low`` — ``unknown`` is an explicit sink, anything else
  raises. Replays are byte-identical: input order does not survive into
  the output.
* ``resolve_disclosure_window`` gives ``info`` / ``unknown`` findings an
  *empty* window with the ``policy_ref`` still echoed — the policy was
  consulted, no deadline was borrowed. Policy hours must be real
  non-negative integers (``True`` is not ``1``).
* ``build_disclosure_timeline_stub`` refuses empty windows and
  non-windowed severities — no disclosure-timeline record ever exists
  without a real clock — and its record ``id`` is a pure function of
  ``workflow|sbom_hash|purl|advisory`` so the same finding replays to
  the same identity.

One test runs the whole ingest → review → assess → track chain end to
end so the four primitives are exercised against each other's real
output shapes, not hand-built fixtures.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.codebase_vuln_management.primitives import (
    InvalidDisclosurePolicyError,
    SBOMContentHashError,
    build_disclosure_timeline_stub,
    normalise_findings,
    pin_sbom_content_hash,
    resolve_disclosure_window,
)
from content.playbooks.codebase_vuln_management.primitives.timeline import (
    InvalidDisclosureRecordError,
)

SBOM_BYTES = b'{"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}'
SBOM_HASH = hashlib.sha256(SBOM_BYTES).hexdigest()

CVD_POLICY = {
    "policy_ref": "policy.cvd@v1",
    "windows": {
        "critical": {"acknowledge_h": 4, "fix_h": 24, "disclose_h": 72},
        "high": {"acknowledge_h": 24, "fix_h": 312, "disclose_h": 672},
        "medium": {"acknowledge_h": 72, "fix_h": 720, "disclose_h": 1440},
        "low": {"acknowledge_h": 72, "fix_h": 2160, "disclose_h": 4320},
    },
}

AWARENESS_AT = "2026-06-19T01:00:00Z"


def _raw_finding(**overrides) -> dict:
    base = {
        "advisory_id": "GHSA-aaaa-bbbb-cccc",
        "purl": "pkg:pypi/example-lib",
        "version": "1.2.3",
        "severity": "high",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# sbom.pin_sbom_content_hash                                                  #
# --------------------------------------------------------------------------- #


def test_pin_sbom_content_hash_is_sha256_of_bytes() -> None:
    assert pin_sbom_content_hash(SBOM_BYTES, "cyclonedx_json") == SBOM_HASH


def test_pin_sbom_content_hash_normalises_format_spelling() -> None:
    """Case and surrounding whitespace do not fail a legitimate format."""
    assert (
        pin_sbom_content_hash(SBOM_BYTES, "  CycloneDX_JSON ")
        == SBOM_HASH
    )


def test_pin_sbom_content_hash_rejects_unknown_format() -> None:
    with pytest.raises(SBOMContentHashError, match="not one of"):
        pin_sbom_content_hash(SBOM_BYTES, "sarif")


def test_pin_sbom_content_hash_rejects_empty_and_non_bytes() -> None:
    with pytest.raises(SBOMContentHashError, match="empty"):
        pin_sbom_content_hash(b"", "spdx_json")
    with pytest.raises(SBOMContentHashError, match="must be bytes"):
        pin_sbom_content_hash("not-bytes", "spdx_json")  # type: ignore[arg-type]
    with pytest.raises(SBOMContentHashError, match="must be a string"):
        pin_sbom_content_hash(SBOM_BYTES, None)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# sbom.normalise_findings                                                     #
# --------------------------------------------------------------------------- #


def test_normalise_findings_replay_is_byte_identical() -> None:
    """Input order does not survive into the output — two replays of the
    same scan serialise to the same bytes."""
    first = _raw_finding(advisory_id="GHSA-zzzz-0000-0001", purl="pkg:pypi/zlib-x")
    second = _raw_finding(advisory_id="GHSA-aaaa-0000-0001", purl="pkg:pypi/alib")
    forward = normalise_findings([first, second], SBOM_HASH)
    reversed_ = normalise_findings([second, first], SBOM_HASH)
    assert json.dumps(forward, sort_keys=True) == json.dumps(
        reversed_, sort_keys=True
    )
    assert [f["advisory_id"] for f in forward] == [
        "GHSA-aaaa-0000-0001",
        "GHSA-zzzz-0000-0001",
    ]


def test_normalise_findings_canonicalises_and_pins_hash() -> None:
    rows = normalise_findings(
        [_raw_finding(severity="HIGH", version=" 1.2.3 ")], SBOM_HASH
    )
    assert rows[0]["severity"] == "high"
    assert rows[0]["version"] == "1.2.3"
    assert rows[0]["sbom_content_hash"] == SBOM_HASH


def test_normalise_findings_never_coerces_unrecognised_severity() -> None:
    """``unknown`` is an explicit sink; anything else raises rather than
    silently becoming ``low``."""
    rows = normalise_findings([_raw_finding(severity="unknown")], SBOM_HASH)
    assert rows[0]["severity"] == "unknown"
    with pytest.raises(ValueError, match="severity"):
        normalise_findings([_raw_finding(severity="moderate")], SBOM_HASH)
    with pytest.raises(ValueError, match="severity"):
        normalise_findings([dict(_raw_finding(), severity="")], SBOM_HASH)


def test_normalise_findings_source_data_passthrough_and_unknown_keys() -> None:
    raw = _raw_finding(
        source_data={"scanner": "osv-scanner", "score": 8.1},
        operator_note="ignored-extra-key",
    )
    rows = normalise_findings([raw], SBOM_HASH)
    assert rows[0]["source_data"] == {"scanner": "osv-scanner", "score": 8.1}
    assert "operator_note" not in rows[0]


def test_normalise_findings_validates_hash_shape() -> None:
    with pytest.raises(ValueError, match="64-char"):
        normalise_findings([_raw_finding()], "deadbeef")
    with pytest.raises(ValueError, match="not valid hex"):
        normalise_findings([_raw_finding()], "z" * 64)


def test_normalise_findings_names_the_offending_row() -> None:
    """A missing key on row N is reported against row N, not generically."""
    good = _raw_finding()
    bad = _raw_finding(advisory_id="")
    with pytest.raises(ValueError, match=r"raw_findings\[1\]\.advisory_id"):
        normalise_findings([good, bad], SBOM_HASH)


# --------------------------------------------------------------------------- #
# disclosure_window.resolve_disclosure_window                                 #
# --------------------------------------------------------------------------- #


def test_resolve_disclosure_window_critical_absolutes() -> None:
    window = resolve_disclosure_window("critical", AWARENESS_AT, CVD_POLICY)
    assert window == {
        "policy_ref": "policy.cvd@v1",
        "acknowledge_by": "2026-06-19T05:00:00Z",
        "fix_by": "2026-06-20T01:00:00Z",
        "disclose_by": "2026-06-22T01:00:00Z",
    }


def test_resolve_disclosure_window_empty_for_info_and_unknown() -> None:
    """No deadline is borrowed for findings without a real severity — but
    the policy_ref still echoes so consumers can prove it was consulted."""
    for severity in ("info", "unknown"):
        window = resolve_disclosure_window(severity, AWARENESS_AT, CVD_POLICY)
        assert window["policy_ref"] == "policy.cvd@v1"
        assert (
            window["acknowledge_by"] == window["fix_by"] == window["disclose_by"] == ""
        )


def test_resolve_disclosure_window_rejects_unrecognised_severity() -> None:
    with pytest.raises(InvalidDisclosurePolicyError, match="not a recognised"):
        resolve_disclosure_window("moderate", AWARENESS_AT, CVD_POLICY)


def test_resolve_disclosure_window_truncates_fractional_seconds() -> None:
    """Second-precision output regardless of sub-second awareness input, so
    cross-target byte-parity cannot drift on microsecond formatting."""
    window = resolve_disclosure_window(
        "critical", "2026-06-19T01:00:00.734512Z", CVD_POLICY
    )
    assert window["acknowledge_by"] == "2026-06-19T05:00:00Z"


def test_resolve_disclosure_window_requires_utc_z_timestamp() -> None:
    with pytest.raises(InvalidDisclosurePolicyError, match="ending in 'Z'"):
        resolve_disclosure_window("high", "2026-06-19T01:00:00+02:00", CVD_POLICY)
    with pytest.raises(InvalidDisclosurePolicyError, match="not a parsable"):
        resolve_disclosure_window("high", "yesterdayZ", CVD_POLICY)


def test_resolve_disclosure_window_policy_shape_is_enforced() -> None:
    missing_band = {
        "policy_ref": "policy.cvd@v1",
        "windows": {k: v for k, v in CVD_POLICY["windows"].items() if k != "low"},
    }
    with pytest.raises(InvalidDisclosurePolicyError, match=r"windows\.low"):
        resolve_disclosure_window("high", AWARENESS_AT, missing_band)

    negative = json.loads(json.dumps(CVD_POLICY))
    negative["windows"]["high"]["fix_h"] = -1
    with pytest.raises(InvalidDisclosurePolicyError, match=r"high\.fix_h"):
        resolve_disclosure_window("high", AWARENESS_AT, negative)

    with pytest.raises(InvalidDisclosurePolicyError, match="policy_ref"):
        resolve_disclosure_window(
            "high", AWARENESS_AT, {"policy_ref": " ", "windows": CVD_POLICY["windows"]}
        )


def test_resolve_disclosure_window_bool_hours_are_not_integers() -> None:
    """``True`` satisfies ``isinstance(x, int)`` — the primitive must still
    reject it, or a YAML ``fix_h: true`` typo becomes a 1-hour deadline."""
    boolish = json.loads(json.dumps(CVD_POLICY))
    boolish["windows"]["critical"]["acknowledge_h"] = True
    with pytest.raises(
        InvalidDisclosurePolicyError, match=r"critical\.acknowledge_h"
    ):
        resolve_disclosure_window("critical", AWARENESS_AT, boolish)


# --------------------------------------------------------------------------- #
# timeline.build_disclosure_timeline_stub                                     #
# --------------------------------------------------------------------------- #


def _stub_inputs() -> dict:
    finding = normalise_findings([_raw_finding()], SBOM_HASH)[0]
    window = resolve_disclosure_window("high", AWARENESS_AT, CVD_POLICY)
    return {
        "finding": finding,
        "disclosure_window": window,
        "captured_at": "2026-06-19T01:05:00Z",
        "ref_viz": "viz.disclosure_timeline@v1",
        "source_data": {"kind": "ocsf", "ocsf_class_uid": 2002},
    }


def test_stub_identity_is_deterministic_and_documented() -> None:
    """``id`` is SHA-256 of ``workflow|sbom_hash|purl|advisory`` exactly —
    the replay-identity contract the module docstring promises."""
    record = build_disclosure_timeline_stub(**_stub_inputs())
    expected = hashlib.sha256(
        (
            "codebase_vuln_management|"
            f"{SBOM_HASH}|pkg:pypi/example-lib|GHSA-aaaa-bbbb-cccc"
        ).encode("utf-8")
    ).hexdigest()
    assert record["id"] == expected
    assert record["id"] == build_disclosure_timeline_stub(**_stub_inputs())["id"]


def test_stub_carries_schema_shape() -> None:
    record = build_disclosure_timeline_stub(**_stub_inputs())
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "codebase_vuln_management"
    assert record["workflow_id"] == "codebase_vuln_management"
    assert record["component"] == {"purl": "pkg:pypi/example-lib", "version": "1.2.3"}
    assert record["severity"] == "high"
    assert record["disclosure_window"]["fix_by"] == "2026-07-02T01:00:00Z"
    assert record["source_data"] == {"kind": "ocsf", "ocsf_class_uid": 2002}


def test_stub_refuses_empty_window() -> None:
    """No disclosure-timeline record without a real clock."""
    inputs = _stub_inputs()
    inputs["disclosure_window"] = resolve_disclosure_window(
        "info", AWARENESS_AT, CVD_POLICY
    )
    with pytest.raises(InvalidDisclosureRecordError, match="ISO-8601|empty"):
        build_disclosure_timeline_stub(**inputs)


def test_stub_refuses_non_windowed_severity() -> None:
    inputs = _stub_inputs()
    inputs["finding"] = dict(inputs["finding"], severity="unknown")
    with pytest.raises(InvalidDisclosureRecordError, match="info/unknown"):
        build_disclosure_timeline_stub(**inputs)


def test_stub_validates_reference_patterns() -> None:
    inputs = _stub_inputs()
    inputs["ref_viz"] = "disclosure_timeline"
    with pytest.raises(InvalidDisclosureRecordError, match="ref_viz"):
        build_disclosure_timeline_stub(**inputs)

    inputs = _stub_inputs()
    inputs["finding"] = dict(inputs["finding"], purl="example-lib")
    with pytest.raises(InvalidDisclosureRecordError, match="PURL"):
        build_disclosure_timeline_stub(**inputs)

    inputs = _stub_inputs()
    inputs["disclosure_window"] = dict(
        inputs["disclosure_window"], policy_ref="cvd-policy"
    )
    with pytest.raises(InvalidDisclosureRecordError, match="policy_ref"):
        build_disclosure_timeline_stub(**inputs)


def test_stub_source_data_kinds_are_gated() -> None:
    inputs = _stub_inputs()
    inputs["source_data"] = {"kind": "none"}
    assert build_disclosure_timeline_stub(**inputs)["source_data"] == {"kind": "none"}

    inputs["source_data"] = {"kind": "telemetry", "telemetry_ref": "telemetry.ocsf.x@v1"}
    assert build_disclosure_timeline_stub(**inputs)["source_data"] == {
        "kind": "telemetry",
        "telemetry_ref": "telemetry.ocsf.x@v1",
    }

    inputs["source_data"] = {"kind": "ocsf", "ocsf_class_uid": True}
    with pytest.raises(InvalidDisclosureRecordError, match="ocsf_class_uid"):
        build_disclosure_timeline_stub(**inputs)

    inputs["source_data"] = {"kind": "sarif"}
    with pytest.raises(InvalidDisclosureRecordError, match="kind"):
        build_disclosure_timeline_stub(**inputs)


# --------------------------------------------------------------------------- #
# The whole chain: ingest-sbom → review-deps → assess-disclosure →            #
# track-timeline, exercised against each other's real output shapes.          #
# --------------------------------------------------------------------------- #


def test_full_chain_replays_byte_identically() -> None:
    sbom_hash = pin_sbom_content_hash(SBOM_BYTES, "cyclonedx_json")

    def run_chain() -> str:
        findings = normalise_findings(
            [
                _raw_finding(severity="critical"),
                _raw_finding(
                    advisory_id="GHSA-dddd-eeee-ffff",
                    purl="pkg:npm/other-lib",
                    version="4.5.6",
                    severity="info",
                ),
            ],
            sbom_hash,
        )
        records = []
        for finding in findings:
            window = resolve_disclosure_window(
                finding["severity"], AWARENESS_AT, CVD_POLICY
            )
            if finding["severity"] in ("info", "unknown"):
                # Empty window: audit-channel row only, no timeline record.
                assert window["disclose_by"] == ""
                continue
            records.append(
                build_disclosure_timeline_stub(
                    finding=finding,
                    disclosure_window=window,
                    captured_at="2026-06-19T01:05:00Z",
                    ref_viz="viz.disclosure_timeline@v1",
                    source_data={"kind": "ocsf", "ocsf_class_uid": 2002},
                )
            )
        return json.dumps(records, sort_keys=True)

    first = run_chain()
    second = run_chain()
    assert first == second
    records = json.loads(first)
    assert len(records) == 1  # the info finding produced no record
    assert records[0]["severity"] == "critical"
    assert records[0]["disclosure_window"]["disclose_by"] == "2026-06-22T01:00:00Z"
