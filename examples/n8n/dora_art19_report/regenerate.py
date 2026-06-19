"""Regenerate the committed DORA Article 19 report-variant worked example (n8n).

n8n-side sibling of ``examples/temporal/dora_art19_report/`` — the
identical JSON-shaped payload is handed to the n8n adapter at
``compilers.n8n.evidence.emit_dora_art19_report_n8n`` so the
per-target bytes are byte-identical to the Temporal and LangGraph
siblings. The DORA Art. 19 report variant has no per-target compile
context (no ``compile_target`` field on the schema) — the F-SV-03
invariant is one shared helper / three thin adapters / byte-identical
output across the three reference targets.

Run from the repo root::

    PYTHONPATH=. python examples/n8n/dora_art19_report/regenerate.py
"""
from __future__ import annotations

import importlib.util
import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from compilers.n8n.evidence import emit_dora_art19_report_n8n

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


def _ctx_to_payload(ctx) -> dict:
    """Convert a typed DoraArt19ReportContext into an n8n-shaped JSON payload."""
    payload = asdict(ctx)
    # n8n's node-process boundary cannot carry datetime — stringify
    # every UTC-aware datetime through the same canonical ISO-8601 ``Z``
    # representation the shared helper writes.
    def _iso(dt: datetime) -> str:
        return dt.astimezone(dt.tzinfo).replace(microsecond=0).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    payload["submitted_at"] = _iso(ctx.submitted_at)
    payload["timeline_refs"]["clock_started_at"] = _iso(
        ctx.timeline_refs.clock_started_at
    )
    return payload


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    contexts = _load_temporal_contexts()
    for variant, ctx in contexts.items():
        payload = _ctx_to_payload(ctx)
        result = emit_dora_art19_report_n8n(payload, EVIDENCE_DIR)
        written = Path(result["report_path"])
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
