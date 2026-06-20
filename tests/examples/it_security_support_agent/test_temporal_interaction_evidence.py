"""F-WF-12 CORE-FANOUT-TEMPORAL — interaction-evidence byte-parity.

The committed
``examples/temporal/it_security_support_agent/evidence/interaction-evidence.json``
is the Temporal activity adapter's output for the payload pinned in
the example's ``regenerate.py``. This module re-drives the activity
from that payload and pins the on-disk bytes against the committed
example AND against the immutable fixture under
``tests/fixtures/it_security_support_agent/`` — so a refactor of the
workflow-local interaction-evidence primitive or the Temporal activity
that silently changes serialisation gets caught at the byte level.

Cross-target byte parity with the n8n sibling is pinned here too:
the interaction-evidence artifact is target-agnostic on the wire
(the schema carries no ``compile_target`` field), so the n8n adapter
and the Temporal activity must emit byte-identical records for the
same canonical payload. The committed n8n fixture under
``tests/fixtures/it_security_support_agent/n8n.interaction-evidence-record.json``
is the reference; the Temporal fixture must match it byte-for-byte.
Both adapters delegate to the workflow-local
:func:`content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact`
primitive — that's the F-WF-12 CORE invariant.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/temporal/it_security_support_agent/regenerate.py

and copy the new bytes into
``tests/fixtures/it_security_support_agent/temporal.interaction-evidence-record.json``
alongside the activity / primitive change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers.temporal.evidence import (
    emit_interaction_evidence_artifact_activity,
)

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "it_security_support_agent"
SNAPSHOT = EXAMPLE / "evidence" / "interaction-evidence.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "it_security_support_agent"
    / "temporal.interaction-evidence-record.json"
)
N8N_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "it_security_support_agent"
    / "n8n.interaction-evidence-record.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_it_security_support_agent_temporal_regen", REGEN
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
        "examples/temporal/it_security_support_agent/evidence/"
        "interaction-evidence.json drifted from the immutable fixture "
        "at tests/fixtures/it_security_support_agent/"
        "temporal.interaction-evidence-record.json. Refresh both "
        "together via "
        "`./examples/temporal/it_security_support_agent/regenerate.sh` "
        "and copy the snapshot into the fixture dir."
    )


def test_temporal_fixture_matches_n8n_fixture() -> None:
    """Cross-target byte parity invariant.

    The interaction-evidence artifact is target-agnostic on the wire —
    the schema carries no ``compile_target`` field. Every CORE-FANOUT
    target must therefore emit byte-identical records for the same
    canonical payload. Both fixtures here are produced from
    byte-identical payloads driven through the same workflow-local
    primitive at
    ``content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact``.
    """
    assert FIXTURE.read_bytes() == N8N_FIXTURE.read_bytes(), (
        "Temporal and n8n it_security_support_agent fixtures drifted — "
        "the target-agnostic CORE invariant says they must be "
        "byte-identical for the canonical worked-example payload. "
        "Refresh both together via the per-target regenerate scripts."
    )


def test_example_snapshot_matches_temporal_activity(tmp_path: Path) -> None:
    payload = _load_payload()
    written_str = asyncio.run(
        emit_interaction_evidence_artifact_activity(payload, tmp_path)
    )
    written = Path(written_str)
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/it_security_support_agent/evidence/"
        "interaction-evidence.json drifted from the Temporal activity "
        "adapter. If intentional, regenerate via `PYTHONPATH=. python "
        "examples/temporal/it_security_support_agent/regenerate.py` "
        "and commit the new bytes."
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


def test_temporal_activity_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same payload → same artifact_id → byte-identical re-emission.

    Re-emission inside the same execution is the F-WF-12 primitive's
    contract: the deterministic ``incident_id`` (UUIDv5 of
    ``<workflow_id>|<execution_id>``) and ``artifact_id`` (SHA-256 of
    ``<incident_id>|<execution_id>``) collapse to the same bytes.
    """
    payload = _load_payload()
    first = Path(
        asyncio.run(
            emit_interaction_evidence_artifact_activity(payload, tmp_path)
        )
    )
    second = Path(
        asyncio.run(
            emit_interaction_evidence_artifact_activity(payload, tmp_path)
        )
    )
    assert first.name == second.name
    assert first.read_bytes() == second.read_bytes()


def test_responder_queue_is_role_shaped() -> None:
    """Personal handles are rejected at the primitive boundary.

    The pinned payload's handoff envelope carries a role-shaped
    responder_queue (``soc-tier-2-rota``); this test asserts the
    fixture wasn't smuggled with a personal handle via a refactor.
    """
    payload = _load_payload()
    handle = payload["handoff_envelope"]["responder_queue"]
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
