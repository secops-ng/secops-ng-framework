"""Regenerate the committed DORA Article 19 report-variant worked example (LangGraph).

LangGraph-side sibling of the Temporal and n8n worked examples. The
identical typed :class:`DoraArt19ReportContext` is threaded onto a
state mapping and handed to the LangGraph node at
``compilers.langgraph.evidence.emit_dora_art19_report_node`` so the
per-target bytes are byte-identical to the Temporal and n8n siblings.

Run from the repo root::

    PYTHONPATH=. python examples/langgraph/dora_art19_report/regenerate.py
"""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

from compilers.langgraph.evidence import emit_dora_art19_report_node

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
REPO = HERE.parents[2]
TEMPORAL_REGEN = (
    REPO / "examples" / "temporal" / "dora_art19_report" / "regenerate.py"
)


def _load_temporal_contexts() -> dict:
    """Import the Temporal sibling's CONTEXTS without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_dora_art19_report_temporal_regen", TEMPORAL_REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CONTEXTS


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    contexts = _load_temporal_contexts()
    for variant, ctx in contexts.items():
        state = {
            "dora_art19_report_context": ctx,
            "evidence_output_dir": EVIDENCE_DIR,
        }
        update = emit_dora_art19_report_node(state)
        written = Path(update["dora_art19_report_path"])
        snapshot = EVIDENCE_DIR / f"{variant}.report.json"
        shutil.copyfile(written, snapshot)
        written.unlink()
        record = json.loads(snapshot.read_text("utf-8"))
        assert record["schema_version"] == "1.0.0"
        assert record["report_variant"] == variant
        print(
            f"wrote {snapshot} (report_id={record['report_id']})"
        )


if __name__ == "__main__":
    main()
