"""Regenerate the committed auditor-bundle worked example (Temporal).

The incident_management playbook compiled to Temporal exercises the
incidents (F-CP-02) evidence stream during one representative
execution of the NIS2 Article 23 three-stage timeline — 24h early
warning, 72h incident notification, one-month final report. This
script assembles the F-WF-09 auditor-handover bundle that indexes
*that* artifact as a single auditor-ready directory of plain files.

The bundle directory IS the auditor handover surface — a self-contained
mini ``content_root`` carrying ``bundle.manifest.json`` at its root and
the per-stream JSON artifact under ``content/evidence/incidents/``.
Streams the incident_management workflow does not exercise
(risk-analysis, supply-chain, vulns, crypto, access, effectiveness)
remain in the manifest as ``present: false`` empty slots so a reviewer
sees the closed seven-stream surface, not a quietly-omitted stream —
exactly the SKELETON contract pinned at
``compilers/_shared/evidence/bundle.py``.

This script drives the Temporal activity at
``compilers.temporal.evidence.emit_bundle_manifest_activity`` exactly
as a Temporal workflow would: the activity takes a typed
:class:`BundleContext` and an output directory, awaits the result, and
writes ``bundle.manifest.json`` atomically into the bundle root. The
inlined incidents artifact is rebuilt from the same typed context the
per-target byte-parity golden pins, so the bundle directory's content
tree is reproducible end-to-end.

Run from the repo root after any change to the bundle shared collector,
the incidents emitter, or the Temporal activity::

    PYTHONPATH=. python examples/temporal/incident_management/evidence/bundle/regenerate.py

Re-runs with the same
``(generated_at, bundle_window_start, bundle_window_end)`` tuple
reproduce the same ``bundle_id`` and the same manifest byte-for-byte
per F-WF-09 determinism. The manifest is also byte-identical across
the three reference compile targets (n8n, Temporal, LangGraph) because
the same shared collector renders it from the same evidence surface —
the existing cross-target equivalence test at
``tests/content_model/test_bundle_evidence_collector.py`` pins that
property.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    AccessContext,
    BundleContext,
    CallerIdentity,
    ClassificationVerdict,
    IncidentsContext,
    KpiWindows,
    Lifecycle,
    NotificationMilestone,
    emit_incidents_artifact,
)
from compilers.temporal.evidence import (
    emit_access_artifact_activity,
    emit_bundle_manifest_activity,
)

HERE = Path(__file__).resolve().parent


def _incidents_ctx() -> IncidentsContext:
    """Typed incidents context for the inlined per-stream artifact.

    Matches the canonical fixture pinned by
    ``tests/examples/incidents_evidence/test_golden.py`` so the
    bundle's inlined artifact is byte-identical to the per-target
    incidents goldens. A reviewer can therefore cross-check the file
    under ``content/evidence/incidents/`` against the EXTEND-tests
    golden without leaving the bundle directory.
    """
    started = datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc)
    return IncidentsContext(
        incident_id="1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
        execution_id="temporal:wf-run-incident-001",
        regulation_refs=(
            "nis2:art-21-2-b",
            "nis2:art-23-early-warning",
            "nis2:art-23-notification-72h",
            "nis2:art-23-final-report",
        ),
        control_refs=(
            "control.incident_handling_capability@v1",
            "control.incident_timeline_signals@v1",
        ),
        classification=ClassificationVerdict(
            significant=True,
            cross_border=False,
            reasons=(
                "Severe disruption to availability of an essential service.",
            ),
            rule_ids=("sig.severe_disruption",),
            severity="High",
            summary=(
                "Authentication-edge availability lost for 47 minutes; "
                "containment via failover to standby region; root cause "
                "scoped to misapplied configuration change."
            ),
        ),
        lifecycle=Lifecycle(
            first_observation_at=datetime(
                2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc
            ),
            detected_at=datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc),
            triaged_at=datetime(2026, 6, 5, 12, 45, 0, tzinfo=timezone.utc),
            contained_at=datetime(2026, 6, 5, 13, 17, 0, tzinfo=timezone.utc),
            eradicated_at=datetime(2026, 6, 5, 14, 0, 0, tzinfo=timezone.utc),
            recovered_at=datetime(2026, 6, 5, 14, 30, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc),
        ),
        owner_role="csirt@example.org",
        owner_assigned_at="2026-06-05",
        captured_at=datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/incident-001",
        notification_timeline=(
            NotificationMilestone(
                milestone="early_warning_24h",
                clock_started_at=started,
                submitted_at=datetime(
                    2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-early_warning_24h",
                on_time=True,
            ),
            NotificationMilestone(
                milestone="incident_notification_72h",
                clock_started_at=started,
                submitted_at=datetime(
                    2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-incident_notification_72h",
                on_time=True,
            ),
            NotificationMilestone(
                milestone="final_report_1mo",
                clock_started_at=started,
                submitted_at=datetime(
                    2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-final_report_1mo",
                on_time=True,
            ),
        ),
        kpi_windows=KpiWindows(
            mttd_minutes=30.0,
            mttr_minutes=47.0,
            containment_window_minutes=43.0,
            eradication_window_minutes=30.0,
        ),
        commit_sha="deadbeef0123456789",
    )


def _access_ctx() -> AccessContext:
    """Typed access context for the F-CP-07 SKELETON Temporal write-path.

    One execution of the incident_management Temporal worked example
    invokes the workflow runtime under a role-shaped caller identity
    holding a closed ``verb.resource`` capability list. The shared
    helper renders that into one record conforming to
    ``schemas/evidence/access.schema.json``. The typed shape mirrors
    ``_ctx()`` in ``tests/examples/access_evidence/test_golden.py`` so
    the bundle's inlined access artifact lands on the same surface a
    reviewer cross-checks against the EXTEND-tests golden once the
    n8n + LangGraph CORE-FANOUT-EXAMPLES sibling closes byte-parity.
    """
    return AccessContext(
        workflow_id="incident_management",
        execution_id="temporal:wf-run-access-001",
        compile_target="temporal",
        regulation_refs=("nis2:art-21-2-i",),
        control_refs=(
            "control.jml_evidence@v1",
            "control.privileged_access_review@v1",
        ),
        caller_identity=CallerIdentity(
            principal_type="workflow_runtime",
            principal_id="temporal-worker-incident-mgmt",
            identity_provider="temporal",
        ),
        capabilities=(
            "secrets.read",
            "workflows.execute",
            "incidents.classify",
        ),
        capability_count=3,
        captured_at=datetime(2026, 6, 9, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/access-001",
        owner_role="identity-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
        retention="P2Y",
    )


def _stage_bundle_tree() -> None:
    """Reset and re-emit the bundle's ``content/evidence/`` tree.

    The bundle directory is the auditor handover unit, so the inlined
    artifacts under ``content/evidence/<stream>/`` are rebuilt from the
    same typed contexts the per-target goldens pin. A reviewer can walk
    each manifest ``artifact_paths`` entry to a JSON file that validates
    against its stream schema without leaving the bundle root.

    The access artifact is emitted via the Temporal activity wrapper
    (``emit_access_artifact_activity``) rather than the shared helper
    directly — this is the F-CP-07 SKELETON write-path that wires the
    Temporal access emitter into the incident_management worked example.
    The n8n + LangGraph fan-out is a named CORE-FANOUT sibling.
    """
    content_evidence = HERE / "content" / "evidence"
    if content_evidence.exists():
        shutil.rmtree(content_evidence)
    incidents_dir = content_evidence / "incidents"
    emit_incidents_artifact(_incidents_ctx(), incidents_dir)
    access_dir = content_evidence / "access"
    asyncio.run(emit_access_artifact_activity(_access_ctx(), str(access_dir)))


# Typed context — exactly what a Temporal workflow would hand the
# activity. The shape mirrors compilers._shared.evidence.BundleContext;
# ``content_root`` is the bundle directory itself so the collector walks
# ``content/evidence/<stream>/`` under that root and the resulting
# ``artifact_paths`` are bundle-relative.
CTX = BundleContext(
    content_root=HERE,
    generated_at=datetime(2026, 7, 5, 13, 0, 0, tzinfo=timezone.utc),
    regulation_refs=(
        "nis2:art-20",
        "nis2:art-21-2-b",
        "nis2:art-22",
        "nis2:art-23",
    ),
    source_url="https://example.org/runs/incident_management_example_0001",
    bundle_window_start=datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
    bundle_window_end=datetime(
        2026, 7, 31, 23, 59, 59, tzinfo=timezone.utc
    ),
    commit_sha="d31a3a7",
    owner_role="compliance-wg",
    owner_assigned_at="2026-01-15",
    retention="P2Y",
)


def main() -> None:
    _stage_bundle_tree()
    written_str = asyncio.run(emit_bundle_manifest_activity(CTX, HERE))
    manifest_path = Path(written_str)
    record = json.loads(manifest_path.read_text("utf-8"))

    # Sanity checks — the bundle is the auditor handover unit, so a
    # reviewer should be able to walk from manifest entry to the
    # bundle-relative artifact file without leaving the directory.
    assert manifest_path == HERE / "bundle.manifest.json"
    present = {entry["stream"] for entry in record["streams"] if entry["present"]}
    assert present == {"incidents", "access"}, (
        f"expected incidents + access present, got {present}"
    )
    for entry in record["streams"]:
        for rel in entry["artifact_paths"]:
            on_disk = HERE / rel
            assert on_disk.is_file(), (
                f"manifest references {rel!s} but it is not present in the bundle"
            )

    print(
        f"wrote {manifest_path} (bundle_id={record['bundle_id']}, "
        f"streams_present={sorted(present)})"
    )


if __name__ == "__main__":
    main()
