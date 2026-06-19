"""Regenerate the committed auditor-bundle worked example (LangGraph).

The incident_management playbook compiled to LangGraph exercises the
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

This script drives the LangGraph node adapter at
``compilers.langgraph.evidence.emit_bundle_manifest_node`` exactly as
an integrator's ``StateGraph`` would: the node is invoked with a state
mapping carrying the typed :class:`BundleContext` and the output
directory, and the returned partial state update is inspected for the
bundle path and deterministic ``bundle_id``. The inlined incidents
artifact is rebuilt from the same typed context the per-target
byte-parity golden pins, so the bundle directory's content tree is
reproducible end-to-end.

Run from the repo root after any change to the bundle shared collector,
the incidents emitter, or the LangGraph node adapter::

    PYTHONPATH=. python examples/langgraph/incident_management/evidence/bundle/regenerate.py

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

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    BundleContext,
    ClassificationVerdict,
    IncidentsContext,
    KpiWindows,
    Lifecycle,
    NotificationMilestone,
    emit_incidents_artifact,
)
from compilers.langgraph.evidence import emit_bundle_manifest_node

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


def _stage_bundle_tree() -> None:
    """Reset and re-emit the bundle's ``content/evidence/`` tree.

    The bundle directory is the auditor handover unit, so the inlined
    artifact under ``content/evidence/incidents/`` is rebuilt from the
    same typed context the per-target golden pins. A reviewer can
    walk the manifest's ``artifact_paths`` entry to a JSON file that
    validates against ``schemas/evidence/incidents.schema.json``
    without leaving the bundle root.
    """
    content_evidence = HERE / "content" / "evidence"
    if content_evidence.exists():
        shutil.rmtree(content_evidence)
    incidents_dir = content_evidence / "incidents"
    emit_incidents_artifact(_incidents_ctx(), incidents_dir)


# Typed context — exactly what a preceding LangGraph node (the
# bootstrap node that resolves the workflow run's content surface
# under ``content/evidence/<stream>/``) would assemble and place on the
# running state under the ``bundle_context`` key. The shape mirrors
# compilers._shared.evidence.BundleContext; ``content_root`` is the
# bundle directory itself so the collector walks
# ``content/evidence/<stream>/`` under that root.
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
    update = emit_bundle_manifest_node(
        {"bundle_context": CTX, "evidence_output_dir": HERE}
    )
    manifest_path = Path(update["bundle_manifest_path"])
    record = json.loads(manifest_path.read_text("utf-8"))

    # Sanity checks — the bundle is the auditor handover unit, so a
    # reviewer should be able to walk from manifest entry to the
    # bundle-relative artifact file without leaving the directory.
    assert manifest_path == HERE / "bundle.manifest.json"
    assert record["bundle_id"] == update["bundle_id"]
    present = {entry["stream"] for entry in record["streams"] if entry["present"]}
    assert present == {"incidents"}, (
        f"expected exactly incidents present, got {present}"
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
