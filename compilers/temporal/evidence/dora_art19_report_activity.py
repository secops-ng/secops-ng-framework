"""Temporal activity wrapper for the DORA Article 19 report-variant emitter.

One ``@activity.defn`` that delegates to
``compilers._shared.evidence.emit_dora_art19_report``. The activity is
intentionally a thin adapter so the shared helper stays the source of
truth.

The F-WF-05 incident_management workflow drives one emission per DORA
Article 19 reporting milestone (Regulation (EU) 2022/2554):

* Article 19(4)(a) initial notification (4h from major classification)
  → ``initial_4h`` variant from the ``early_warning`` stage's
  regulator-submission event.
* Article 19(4)(b) intermediate report (72h from major classification)
  → ``intermediate_72h`` variant from the ``notification`` stage.
* Article 19(4)(c) final report (one month from intermediate)
  → ``final_1mo`` variant from the ``final_report`` stage.
* Article 19(2) voluntary cyber-threat notification → operator-driven
  ``voluntary_cyber_threat`` variant (no F-WF-05 stage analogue).

Each emission shares the same ``incident_id`` (set by
``open_timeline``) and a distinct ``report_id`` derived from
``SHA-256(<incident_id>|<report_variant>|<submitted_at>)`` so the
chain reads re-submissions as evidentiary signal rather than dedup
waste.
"""
from __future__ import annotations

import os
from dataclasses import asdict

from temporalio import activity

from compilers._shared.evidence import (
    DoraArt19ReportContext,
    emit_dora_art19_report,
)

__all__ = ["emit_dora_art19_report_activity"]


@activity.defn
async def emit_dora_art19_report_activity(
    ctx: DoraArt19ReportContext,
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one DORA Art. 19 report-variant artifact under ``output_dir``.

    Returns the absolute path of the written record as a string so the
    Temporal-side caller can attach it to subsequent activity inputs
    (e.g. the close-timeline step, the F-CP-02 incidents-evidence join,
    or downstream replay-vs-original checks) and to the workflow's
    audit trail.

    The shared helper is responsible for the deterministic ``report_id``,
    the schema-conforming shape, and the atomic write.
    """
    if not isinstance(ctx, DoraArt19ReportContext):
        ctx = DoraArt19ReportContext(**dict(ctx))  # type: ignore[arg-type]
    written = emit_dora_art19_report(ctx, output_dir)
    # asdict is referenced to keep the import wired for future
    # serializer work without introducing a separate code path.
    _ = asdict
    return str(written)
