"""F-WF-11 CORE-FANOUT-TEMPORAL — committed worked example pins the Temporal adapter.

The committed
``examples/temporal/onboarding_offboarding_tracker/evidence/access-evidence.json``
is the Temporal activity adapter's output for the typed
:class:`AccessContext` pinned in the example's ``regenerate.py``.
This test re-drives the activity from that context and pins the
on-disk bytes against the committed example AND against the
immutable fixture under
``tests/fixtures/onboarding_offboarding_tracker/`` — so a refactor
of the shared access-evidence emitter or the Temporal activity
adapter that silently changes serialisation gets caught at the byte
level.

Per the F-CP-07 access schema the artifact carries a
``compile_target`` discriminator and the schema's ``artifact_id``
derivation joins on ``(workflow_id, execution_id, compile_target)``
— so the Temporal and n8n fixtures differ on those three fields by
design. The remaining anchors
(``workflow_id``, ``stream``, ``schema_version``, ``regulation_refs``,
``control_refs``, ``caller_identity``, ``capabilities``,
``capability_count``, ``captured_at``, ``provenance``, ``owner``,
``retention``) are pinned identical to the n8n sibling so a
cross-target reviewer sees the same envelope on both sides — that
cross-target shape parity is the F-WF-11 CORE invariant the
per-target adapters carry through.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/temporal/onboarding_offboarding_tracker/regenerate.py

and copy the new bytes into
``tests/fixtures/onboarding_offboarding_tracker/temporal.access-evidence-record.json``
alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers.temporal.evidence import emit_access_artifact_activity

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "onboarding_offboarding_tracker"
SNAPSHOT = EXAMPLE / "evidence" / "access-evidence.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "onboarding_offboarding_tracker"
    / "temporal.access-evidence-record.json"
)
N8N_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "onboarding_offboarding_tracker"
    / "n8n.access-evidence-record.json"
)

# Fields the schema's ``artifact_id`` derivation joins on (and
# therefore intentionally differ per compile target). Everything else
# in the record must be byte-identical across targets — that is the
# F-WF-11 CORE cross-target shape-parity invariant.
_TARGET_DISCRIMINATORS = frozenset(
    {"artifact_id", "execution_id", "compile_target"}
)


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_onboarding_offboarding_tracker_temporal_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


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
        "examples/temporal/onboarding_offboarding_tracker/evidence/"
        "access-evidence.json drifted from the immutable fixture at "
        "tests/fixtures/onboarding_offboarding_tracker/"
        "temporal.access-evidence-record.json. Refresh both together "
        "via `./examples/temporal/onboarding_offboarding_tracker/"
        "regenerate.sh` and copy the snapshot into the fixture dir."
    )


def test_temporal_and_n8n_fixtures_agree_on_target_agnostic_fields() -> None:
    """Cross-target shape parity invariant.

    The access record carries a ``compile_target`` discriminator and
    the schema's ``artifact_id`` derivation joins on
    ``(workflow_id, execution_id, compile_target)`` — so those three
    fields differ per target by design. Every other field must be
    byte-identical across targets — both adapters drive the same
    shared helper from the same primitive chain, so a drift here
    means one adapter started rewriting payload fields the shared
    helper does not.
    """
    temporal_record = json.loads(FIXTURE.read_text("utf-8"))
    n8n_record = json.loads(N8N_FIXTURE.read_text("utf-8"))
    temporal_shared = {
        k: v for k, v in temporal_record.items()
        if k not in _TARGET_DISCRIMINATORS
    }
    n8n_shared = {
        k: v for k, v in n8n_record.items()
        if k not in _TARGET_DISCRIMINATORS
    }
    assert temporal_shared == n8n_shared, (
        "Temporal and n8n access-evidence fixtures drifted on the "
        "target-agnostic fields. The CORE invariant says every "
        "non-discriminator field must agree byte-for-byte across "
        "compile targets — both adapters drive the same shared helper "
        "from the same primitive chain. Refresh both together via the "
        "per-target regenerate scripts."
    )
    # Sanity check: the discriminators themselves DO differ.
    assert temporal_record["compile_target"] == "temporal"
    assert n8n_record["compile_target"] == "n8n"
    assert temporal_record["artifact_id"] != n8n_record["artifact_id"]


def test_example_snapshot_matches_temporal_activity(tmp_path: Path) -> None:
    ctx = _load_ctx()
    written_str = asyncio.run(
        emit_access_artifact_activity(ctx, tmp_path)
    )
    written = Path(written_str)
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/onboarding_offboarding_tracker/evidence/"
        "access-evidence.json drifted from the Temporal activity "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/temporal/onboarding_offboarding_tracker/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    assert record["workflow_id"] == "onboarding_offboarding_tracker"
    assert record["compile_target"] == "temporal"
    # The id is deterministic on the three pinned inputs (see schema).
    assert len(record["artifact_id"]) == 64
    assert "nis2:art-21-2-i" in record["regulation_refs"]
    assert "control.jml_evidence@v1" in record["control_refs"]
    assert "control.privileged_access_review@v1" in record["control_refs"]
    assert (
        "control.cloud_identity_least_privilege@v1" in record["control_refs"]
    )
    # Caller is role-shaped, not a personal name.
    assert record["caller_identity"]["principal_type"] in {
        "service_account",
        "workflow_runtime",
        "automation_role",
    }
    # capabilities is the closed observed list; uniqueness + verb.resource
    # shape are pinned by the schema.
    assert len(record["capabilities"]) >= 1
    assert len(record["capabilities"]) == len(set(record["capabilities"]))
    assert record["capability_count"] == len(record["capabilities"])


def test_temporal_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same context → same artifact_id → byte-identical re-emission."""
    ctx = _load_ctx()
    first = Path(
        asyncio.run(emit_access_artifact_activity(ctx, tmp_path))
    )
    second = Path(
        asyncio.run(emit_access_artifact_activity(ctx, tmp_path))
    )
    assert first.name == second.name
    assert first.read_bytes() == second.read_bytes()
