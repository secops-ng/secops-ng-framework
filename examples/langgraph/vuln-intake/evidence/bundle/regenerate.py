"""Regenerate the committed auditor-bundle worked example (LangGraph).

The vulnerability-intake playbook compiled to LangGraph exercises the
supply-chain (F-CP-03) and crypto-attestation (F-CP-05) evidence
streams during one representative execution — those are the streams
whose per-run worked-example artifacts are already shipped under
``examples/langgraph/vuln-intake/evidence/{supply-chain,crypto}/``.
This script assembles the F-WF-09 auditor-handover bundle that indexes
*those* artifacts as a single auditor-ready directory of plain files.

The bundle directory IS the auditor handover surface — a self-contained
mini ``content_root`` carrying ``bundle.manifest.json`` at its root and
the per-stream JSON artifacts under ``content/evidence/<stream>/``.
Streams the vuln-intake workflow does not exercise (risk-analysis,
incidents, vulns, access, effectiveness) remain in the manifest as
``present: false`` empty slots so a reviewer sees the closed seven-stream
surface, not a quietly-omitted stream — exactly the SKELETON contract
pinned at ``compilers/_shared/evidence/bundle.py``.

This script drives the LangGraph node adapter at
``compilers.langgraph.evidence.emit_bundle_manifest_node`` exactly as
an integrator's ``StateGraph`` would: the node is invoked with a state
mapping carrying the typed :class:`BundleContext` and the output
directory, and the returned partial state update is inspected for the
bundle path and deterministic ``bundle_id``.

Run from the repo root after any change to the bundle shared collector
or the LangGraph node adapter::

    PYTHONPATH=. python examples/langgraph/vuln-intake/evidence/bundle/regenerate.py

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

from compilers._shared.evidence import BundleContext
from compilers.langgraph.evidence import emit_bundle_manifest_node

HERE = Path(__file__).resolve().parent

# Sibling per-stream worked-example artifacts already shipped for the
# LangGraph vuln-intake compile target. The bundle inlines copies of
# these under its own ``content/evidence/<stream>/`` tree so the bundle
# directory is the auditor handover unit, not a directory of pointers.
SIBLINGS = {
    "crypto": HERE.parent / "crypto" / "secret-handling-attestation.json",
    "supply-chain": HERE.parent
    / "supply-chain"
    / "dependencies-snapshot.json",
}


def _stage_bundle_tree() -> None:
    """Reset the bundle's ``content/evidence/`` tree from the siblings."""
    content_evidence = HERE / "content" / "evidence"
    if content_evidence.exists():
        shutil.rmtree(content_evidence)
    for stream, source in SIBLINGS.items():
        if not source.is_file():
            raise FileNotFoundError(
                f"expected sibling worked-example artifact at {source}; "
                "regenerate the per-stream example first"
            )
        dest_dir = content_evidence / stream
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest_dir / source.name)


# Typed context — exactly what a preceding LangGraph node (the
# bootstrap node that resolves the workflow run's content surface
# under ``content/evidence/<stream>/``) would assemble and place on the
# running state under the ``bundle_context`` key. The shape mirrors
# compilers._shared.evidence.BundleContext; ``content_root`` is the
# bundle directory itself so the collector walks
# ``content/evidence/<stream>/`` under that root.
CTX = BundleContext(
    content_root=HERE,
    generated_at=datetime(2026, 6, 17, 10, 0, 0, tzinfo=timezone.utc),
    regulation_refs=(
        "nis2:art-20",
        "nis2:art-21-2-d",
        "nis2:art-21-2-h",
        "nis2:art-22",
        "nis2:art-23",
    ),
    source_url="https://example.org/runs/vuln-intake-example-0001",
    bundle_window_start=datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
    bundle_window_end=datetime(
        2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc
    ),
    commit_sha="322421b",
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
    assert present == {"crypto", "supply-chain"}, (
        f"expected exactly crypto + supply-chain present, got {present}"
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
