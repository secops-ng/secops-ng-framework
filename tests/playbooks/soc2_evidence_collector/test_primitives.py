"""Unit tests for the soc2_evidence_collector primitives.

The behaviours pinned here are the ones that keep a readiness report honest, and
each is a decision a later change could quietly reverse:

* ``draft_backed`` never collapses into ``covered`` — every SOC 2 crosswalk entry
  is draft today, so that collapse would turn "intent is mapped" into "we have an
  audit trail".
* The rollup carries counts, never a percentage.
* Evidence naming a criterion the crosswalk does not carry is reported as
  unmatched, never dropped.
* Scoring over an empty criteria set raises rather than reporting a vacuous pass.
* The attestation carries its disclaimer and ``document_kind`` unconditionally.

One test runs the whole chain against the **real** crosswalk under
``content/mappings/soc2/`` rather than a fixture, so a criterion added or renamed
there is exercised by this suite instead of drifting past it.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from content.playbooks.soc2_evidence_collector.primitives import (
    ATTESTATION_DISCLAIMER,
    CriterionAtom,
    InvalidAttestationError,
    InvalidCrosswalkEntryError,
    InvalidEvidenceRefError,
    InvalidScoringInputError,
    build_readiness_attestation,
    collect_criteria_atoms,
    derive_attestation_id,
    map_evidence_to_criteria,
    score_criterion_coverage,
)

REPO = pathlib.Path(__file__).resolve().parents[3]
CROSSWALK = REPO / "content" / "mappings" / "soc2"

_WINDOW = "2026-07-01T00:00:00Z/2026-07-31T23:59:59Z"
_CAPTURED = "2026-08-03T12:00:00Z"


def _entry(cid: str, status: str = "draft", **over) -> dict:
    base = {
        "id": cid, "status": status,
        "control_refs": ["control.evidence_pipeline@v1"],
        "playbook_refs": ["playbook.iam_auditor@v1"],
    }
    return {**base, **over}


def _atoms(*entries) -> tuple[CriterionAtom, ...]:
    return collect_criteria_atoms(crosswalk_entries=list(entries))


def _real_entries() -> list[dict]:
    out: list[dict] = []
    for path in sorted(CROSSWALK.glob("tsc-*.yaml")):
        out += (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("entries") or []
    return out


# --------------------------------------------------------------------------- #
# criteria                                                                    #
# --------------------------------------------------------------------------- #


class TestCriteriaAtoms:
    def test_category_resolved_from_prefix(self) -> None:
        atoms = _atoms(
            _entry("soc2:cc6-1-logical-access-controls"),
            _entry("soc2:a1-2-availability-monitoring"),
            _entry("soc2:c1-1-confidential-information"),
            _entry("soc2:pi1-1-quality-of-information"),
            _entry("soc2:p1-1-privacy-notice"),
        )
        got = {a.criterion: a.category for a in atoms}
        assert got == {
            "CC6.1": "security", "A1.2": "availability", "C1.1": "confidentiality",
            "PI1.1": "processing_integrity", "P1.1": "privacy",
        }

    def test_longest_prefix_wins(self) -> None:
        """``cc`` must beat ``c`` and ``pi`` must beat ``p``."""
        atoms = _atoms(
            _entry("soc2:cc1-1-integrity-and-ethical-values"),
            _entry("soc2:pi1-4-output-completeness"),
        )
        assert [a.category for a in atoms] == ["security", "processing_integrity"]

    def test_draft_is_not_audit_ready(self) -> None:
        atom = _atoms(_entry("soc2:cc6-1-logical-access-controls"))[0]
        assert atom.status == "draft"
        assert atom.audit_ready is False

    def test_live_is_audit_ready(self) -> None:
        atom = _atoms(_entry("soc2:cc6-1-logical-access-controls", status="live"))[0]
        assert atom.audit_ready is True

    def test_atoms_are_sorted_for_stability(self) -> None:
        a = _atoms(_entry("soc2:cc9-2-vendor-risk"), _entry("soc2:cc1-1-ethics"))
        b = _atoms(_entry("soc2:cc1-1-ethics"), _entry("soc2:cc9-2-vendor-risk"))
        assert [x.criterion_ref for x in a] == [x.criterion_ref for x in b]

    def test_duplicate_criterion_rejected(self) -> None:
        with pytest.raises(InvalidCrosswalkEntryError, match="duplicate criterion"):
            _atoms(_entry("soc2:cc6-1-x"), _entry("soc2:cc6-1-x"))

    def test_unknown_status_rejected(self) -> None:
        with pytest.raises(InvalidCrosswalkEntryError, match="status"):
            _atoms(_entry("soc2:cc6-1-x", status="probably"))

    @pytest.mark.parametrize("bad", [
        "cc6-1-missing-prefix", "soc2:CC6-1-uppercase", "soc2:zz1-1-unknown-prefix",
        "soc2:cc6-logical", "",
    ])
    def test_malformed_ids_rejected(self, bad: str) -> None:
        with pytest.raises(InvalidCrosswalkEntryError):
            _atoms(_entry(bad))

    def test_bad_control_ref_rejected(self) -> None:
        with pytest.raises(InvalidCrosswalkEntryError, match="control_refs"):
            _atoms(_entry("soc2:cc6-1-x", control_refs=["evidence_pipeline"]))

    def test_bad_playbook_ref_rejected(self) -> None:
        with pytest.raises(InvalidCrosswalkEntryError, match="playbook_refs"):
            _atoms(_entry("soc2:cc6-1-x", playbook_refs=["iam_auditor"]))

    def test_missing_refs_default_empty(self) -> None:
        atom = collect_criteria_atoms(
            crosswalk_entries=[{"id": "soc2:cc6-1-x", "status": "draft"}])[0]
        assert atom.control_refs == () and atom.playbook_refs == ()

    def test_non_sequence_rejected(self) -> None:
        with pytest.raises(InvalidCrosswalkEntryError, match="sequence of objects"):
            collect_criteria_atoms(crosswalk_entries="soc2:cc6-1-x")  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# mapping                                                                     #
# --------------------------------------------------------------------------- #


class TestEvidenceMapping:
    def test_evidence_joins_to_its_criterion(self) -> None:
        atoms = _atoms(_entry("soc2:cc6-1-x"), _entry("soc2:cc7-2-y"))
        m = map_evidence_to_criteria(atoms=atoms, evidence_refs=[
            {"artifact_id": "a1", "stream": "access",
             "criteria_refs": ["soc2:cc6-1-x"]}])
        assert len(m.supported) == 1
        assert m.supported[0].artifact_ids == ("a1",)
        assert m.unsupported_refs == ("soc2:cc7-2-y",)

    def test_unmatched_claim_is_reported_not_dropped(self) -> None:
        atoms = _atoms(_entry("soc2:cc6-1-x"))
        m = map_evidence_to_criteria(atoms=atoms, evidence_refs=[
            {"artifact_id": "a1", "stream": "access",
             "criteria_refs": ["soc2:cc9-9-nope"]}])
        assert m.unmatched == (("a1", "soc2:cc9-9-nope"),)
        assert any("unmatched" in r for r in m.reasons)

    def test_multiple_artifacts_dedupe_and_keep_order(self) -> None:
        atoms = _atoms(_entry("soc2:cc6-1-x"))
        m = map_evidence_to_criteria(atoms=atoms, evidence_refs=[
            {"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]},
            {"artifact_id": "a2", "stream": "vulns", "criteria_refs": ["soc2:cc6-1-x"]},
            {"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]},
        ])
        assert m.supported[0].artifact_ids == ("a1", "a2")
        assert m.supported[0].streams == ("access", "vulns")

    def test_draft_backing_flagged_at_the_join(self) -> None:
        atoms = _atoms(_entry("soc2:cc6-1-x"))
        m = map_evidence_to_criteria(atoms=atoms, evidence_refs=[
            {"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]}])
        assert m.supported[0].draft_backed is True
        assert any("draft crosswalk entry" in r for r in m.reasons)

    def test_missing_required_field_rejected(self) -> None:
        atoms = _atoms(_entry("soc2:cc6-1-x"))
        for ref in ({"stream": "access", "criteria_refs": []},
                    {"artifact_id": "a1", "criteria_refs": []}):
            with pytest.raises(InvalidEvidenceRefError, match="non-empty string"):
                map_evidence_to_criteria(atoms=atoms, evidence_refs=[ref])

    def test_non_atom_rejected(self) -> None:
        with pytest.raises(InvalidEvidenceRefError, match="CriterionAtom"):
            map_evidence_to_criteria(atoms=[{"criterion_ref": "x"}], evidence_refs=[])  # type: ignore[list-item]


# --------------------------------------------------------------------------- #
# scoring                                                                     #
# --------------------------------------------------------------------------- #


def _scored(entries, evidence):
    atoms = collect_criteria_atoms(crosswalk_entries=entries)
    return atoms, score_criterion_coverage(
        atoms=atoms,
        mapping=map_evidence_to_criteria(atoms=atoms, evidence_refs=evidence))


class TestScoring:
    def test_draft_support_scores_draft_backed_not_covered(self) -> None:
        """The load-bearing distinction of this whole playbook."""
        _, s = _scored(
            [_entry("soc2:cc6-1-x")],
            [{"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]}])
        assert [x.state for x in s.scores] == ["draft_backed"]
        assert s.readiness == "draft_only"

    def test_live_support_scores_covered_and_ready(self) -> None:
        _, s = _scored(
            [_entry("soc2:cc6-1-x", status="live")],
            [{"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]}])
        assert [x.state for x in s.scores] == ["covered"]
        assert s.readiness == "ready"

    def test_no_evidence_is_uncovered_and_not_ready(self) -> None:
        _, s = _scored([_entry("soc2:cc6-1-x")], [])
        assert [x.state for x in s.scores] == ["uncovered"]
        assert s.readiness == "not_ready"
        assert s.uncovered_refs == ("soc2:cc6-1-x",)

    def test_mixed_live_and_draft_is_not_ready(self) -> None:
        _, s = _scored(
            [_entry("soc2:cc6-1-x", status="live"), _entry("soc2:cc7-2-y")],
            [{"artifact_id": "a1", "stream": "access",
              "criteria_refs": ["soc2:cc6-1-x", "soc2:cc7-2-y"]}])
        assert s.readiness == "not_ready"
        assert any("until those mappings are promoted" in r for r in s.reasons)

    def test_rollup_counts_per_category(self) -> None:
        _, s = _scored(
            [_entry("soc2:cc6-1-x"), _entry("soc2:cc7-2-y"), _entry("soc2:a1-1-z")],
            [{"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]}])
        rollup = {r.category: r for r in s.rollups}
        assert rollup["security"].total == 2
        assert rollup["security"].draft_backed == 1
        assert rollup["security"].uncovered == 1
        assert rollup["availability"].uncovered == 1

    def test_rollup_carries_no_percentage(self) -> None:
        """A score invites 'we are 87% compliant', which is not defensible."""
        _, s = _scored([_entry("soc2:cc6-1-x")], [])
        fields = set(vars(s.rollups[0]))
        assert fields == {"category", "total", "covered", "draft_backed", "uncovered"}

    def test_empty_criteria_set_refuses_to_score(self) -> None:
        atoms = _atoms(_entry("soc2:cc6-1-x"))
        empty = map_evidence_to_criteria(atoms=(), evidence_refs=[])
        with pytest.raises(InvalidScoringInputError, match="vacuous pass"):
            score_criterion_coverage(atoms=(), mapping=empty)

    def test_mapping_from_a_different_criteria_set_rejected(self) -> None:
        other = _atoms(_entry("soc2:cc9-1-other"))
        mapping = map_evidence_to_criteria(atoms=other, evidence_refs=[
            {"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc9-1-other"]}])
        with pytest.raises(InvalidScoringInputError, match="one criteria set"):
            score_criterion_coverage(atoms=_atoms(_entry("soc2:cc6-1-x")), mapping=mapping)

    def test_unmatched_claims_carried_into_reasons(self) -> None:
        _, s = _scored(
            [_entry("soc2:cc6-1-x")],
            [{"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:zz9-9-nope"]}])
        assert any("unmatched evidence claim" in r for r in s.reasons)


# --------------------------------------------------------------------------- #
# attestation                                                                 #
# --------------------------------------------------------------------------- #


def _attest(**over):
    _, s = _scored(
        [_entry("soc2:cc6-1-x")],
        [{"artifact_id": "a1", "stream": "access", "criteria_refs": ["soc2:cc6-1-x"]}])
    base = dict(
        workflow_id="soc2_evidence_collector", execution_id="exec-1",
        captured_at=_CAPTURED, assessment_window=_WINDOW, scoring=s,
        owner_role="security_engineering")
    return build_readiness_attestation(**{**base, **over})


class TestAttestation:
    def test_carries_disclaimer_and_document_kind(self) -> None:
        doc = _attest()
        assert doc["disclaimer"] == ATTESTATION_DISCLAIMER
        assert doc["document_kind"] == "soc2_readiness_input"
        assert "not a SOC 2 report" in doc["disclaimer"]

    def test_gap_is_surfaced_at_top_level(self) -> None:
        _, s = _scored([_entry("soc2:cc6-1-x"), _entry("soc2:cc7-2-y")],
                       [{"artifact_id": "a1", "stream": "access",
                         "criteria_refs": ["soc2:cc6-1-x"]}])
        doc = _attest(scoring=s)
        assert doc["uncovered_refs"] == ["soc2:cc7-2-y"]

    def test_attestation_id_matches_the_convention(self) -> None:
        doc = _attest()
        assert doc["attestation_id"] == derive_attestation_id(
            "soc2_evidence_collector", "exec-1", _CAPTURED)

    def test_owner_is_a_role_never_a_person(self) -> None:
        assert _attest()["owner"]["role"] == "security_engineering"
        with pytest.raises(InvalidAttestationError, match="owner_role"):
            _attest(owner_role="Jane Doe")

    def test_wrong_workflow_id_rejected(self) -> None:
        with pytest.raises(InvalidAttestationError, match="workflow_id"):
            _attest(workflow_id="nis2_self_assessment")

    @pytest.mark.parametrize("bad", [
        "2026-07-01/2026-07-31", "2026-07-01T00:00:00Z", ""])
    def test_malformed_window_rejected(self, bad: str) -> None:
        with pytest.raises(InvalidAttestationError, match="assessment_window"):
            _attest(assessment_window=bad)

    def test_optional_source_url_must_be_https(self) -> None:
        doc = _attest(source_url="https://example.invalid/run/1")
        assert doc["provenance"]["source_url"] == "https://example.invalid/run/1"
        with pytest.raises(InvalidAttestationError, match="source_url"):
            _attest(source_url="http://example.invalid/run/1")

    def test_rejects_non_scoring(self) -> None:
        with pytest.raises(InvalidAttestationError, match="CoverageScoring"):
            _attest(scoring={"readiness": "ready"})

    def test_deterministic_across_identical_runs(self) -> None:
        assert _attest() == _attest()


# --------------------------------------------------------------------------- #
# the real crosswalk                                                          #
# --------------------------------------------------------------------------- #


class TestAgainstRealCrosswalk:
    """Runs the chain against content/mappings/soc2/ so a change there is caught."""

    def test_every_committed_criterion_normalises(self) -> None:
        atoms = collect_criteria_atoms(crosswalk_entries=_real_entries())
        assert len(atoms) == len(_real_entries())
        assert {a.category for a in atoms} == {
            "security", "availability", "confidentiality",
            "processing_integrity", "privacy"}

    def test_whole_crosswalk_is_draft_today(self) -> None:
        """If this fails, a mapping was promoted — update the README claim too."""
        atoms = collect_criteria_atoms(crosswalk_entries=_real_entries())
        assert not any(a.audit_ready for a in atoms)

    def test_zero_evidence_reports_every_criterion_uncovered(self) -> None:
        entries = _real_entries()
        atoms, s = _scored(entries, [])
        assert s.readiness == "not_ready"
        assert len(s.uncovered_refs) == len(atoms)
        doc = _attest(scoring=s)
        assert doc["criteria_total"] == len(atoms)
        assert sum(r["total"] for r in doc["categories"]) == len(atoms)
