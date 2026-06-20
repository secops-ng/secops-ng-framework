"""F-WF-12 CORE-FANOUT-N8N-GOLDEN — interaction-evidence byte-parity.

The committed
``examples/n8n/it_security_support_agent/evidence/interaction-evidence.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This module re-drives the adapter from that payload
and pins the on-disk bytes against the committed example AND against
the immutable fixture under
``tests/fixtures/it_security_support_agent/`` — so a refactor of the
shared support-agent interaction-evidence primitive or the n8n adapter
that silently changes serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/it_security_support_agent/regenerate.py

and copy the new bytes into ``tests/fixtures/it_security_support_agent/``
alongside the primitive / adapter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_interaction_evidence_artifact_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "it_security_support_agent"
SNAPSHOT = EXAMPLE / "evidence" / "interaction-evidence.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "it_security_support_agent"
    / "n8n.interaction-evidence-record.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_it_security_support_agent_n8n_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_payload()


def test_example_snapshot_is_committed() -> None:
    assert SNAPSHOT.exists(), f"missing example snapshot: {SNAPSHOT}"
    assert SNAPSHOT.stat().st_size > 0


def test_fixture_is_committed() -> None:
    assert FIXTURE.exists(), f"missing byte-parity fixture: {FIXTURE}"
    assert FIXTURE.stat().st_size > 0


def test_example_snapshot_matches_fixture() -> None:
    """The committed worked example and the immutable fixture must agree.

    A drift here means the worked example was regenerated without the
    fixture being refreshed — both must move together.
    """
    assert SNAPSHOT.read_bytes() == FIXTURE.read_bytes(), (
        "examples/n8n/it_security_support_agent/evidence/"
        "interaction-evidence.json drifted from the immutable fixture "
        "at tests/fixtures/it_security_support_agent/"
        "n8n.interaction-evidence-record.json. Refresh both together "
        "via `./examples/n8n/it_security_support_agent/regenerate.sh` "
        "and copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_interaction_evidence_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/it_security_support_agent/evidence/"
        "interaction-evidence.json drifted from the n8n adapter. If "
        "intentional, regenerate via `PYTHONPATH=. python "
        "examples/n8n/it_security_support_agent/regenerate.py` and "
        "commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # F-CP-02 incidents-stream shape, schema-version pin.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "incidents"
    # The id is deterministic on (incident_id, execution_id).
    assert len(record["artifact_id"]) == 64
    # incident_id is a UUID per the schema (UUIDv5 of
    # <workflow_id>|<execution_id> per the support-agent primitive).
    assert len(record["incident_id"]) == 36
    # NIS2 Article 21(2)(b) anchor — the support-agent workflow shares
    # the F-WF-05 anchor.
    assert "nis2:art-21-2-b" in record["regulation_refs"]
    assert (
        "control.incident_handling_capability@v1" in record["control_refs"]
    )
    # Significant=true on the handoff path, with the sig.* rule_id
    # vocabulary pinned by the primitive.
    assert record["classification"]["significant"] is True
    assert record["classification"]["rule_ids"] == [
        "sig.support_incident_handoff"
    ]
    # Schema's intake-only audit-close branch is not used on this
    # significant execution; notification_timeline carries no entries
    # because no Article 23(4) milestone has been submitted yet.
    assert record["notification_timeline"] == []


def test_n8n_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same payload → same artifact_id → byte-identical re-emission.

    Re-emission inside the same execution is the F-WF-12 primitive's
    contract: the deterministic ``incident_id`` (UUIDv5 of
    ``<workflow_id>|<execution_id>``) and ``artifact_id`` (SHA-256 of
    ``<incident_id>|<execution_id>``) collapse to the same bytes.
    """
    payload = _load_payload()
    first = emit_interaction_evidence_artifact_n8n(payload, tmp_path)
    second = emit_interaction_evidence_artifact_n8n(payload, tmp_path)
    assert first["artifact_id"] == second["artifact_id"]
    assert (
        Path(first["artifact_path"]).read_bytes()
        == Path(second["artifact_path"]).read_bytes()
    )


def test_responder_queue_is_role_shaped() -> None:
    """Personal handles are rejected at the primitive boundary.

    The pinned payload's handoff envelope carries a role-shaped
    responder_queue (``soc-tier-2-rota``); this test asserts the
    fixture wasn't smuggled with a personal handle via a refactor.
    The primitive's regex rejects personal handles upstream, but we
    pin the public-bar invariant on the committed bytes too.
    """
    payload = _load_payload()
    handle = payload["handoff_envelope"]["responder_queue"]
    # Role-shaped handles are lowercase, hyphen / dot / @-segmented;
    # personal handles typically carry name fragments. We accept the
    # closed set the fixture pins and refuse anything that smells
    # personal.
    assert handle == "soc-tier-2-rota"


def test_handoff_fired_path_drives_significant_true() -> None:
    """The incident-shaped classification pins the handoff path.

    The closed decision rule in the handoff primitive: an
    ``incident-shaped`` classification forces ``handoff_fired=true``
    with ``trigger_reason='incident_shaped_classification'``, which
    the artifact primitive maps to ``significant=true`` +
    ``rule_ids=['sig.support_incident_handoff']``.
    """
    payload = _load_payload()
    assert payload["classification_verdict"]["category"] == "incident-shaped"
    assert payload["handoff_envelope"]["handoff_fired"] is True
    assert (
        payload["handoff_envelope"]["trigger_reason"]
        == "incident_shaped_classification"
    )
