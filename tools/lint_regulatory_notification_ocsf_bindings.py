"""Regulatory-notification-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar for the **regulatory-notification**
metric family: every metric in the cluster must declare at least one
OCSF ``telemetry_ref`` so the upstream source-data shape is pinned
alongside the internal evidence-artifact field binding.

Cluster scope: metrics whose behaviour tracks a regulator-facing
notification clock (CRA Article 14 early-warning / 72h notification /
severe-incident / final report). Classification is **step-scoped**
rather than playbook-scoped: a metric is regulatory-notification-class
when every one of its ``playbook_refs`` resolves to a ``(playbook_id,
step_id)`` tuple in the ``REGULATORY_NOTIFICATION_STEPS`` allowlist.
The step-scoped gate keeps fan-out metrics that touch the same host
playbook via other steps (e.g. the vuln_intake intake step for CVD
disclosure, or the incident_management containment step for breach
clock margin) out of the cluster — their source-data shape is
correctly captured by other cluster-lints and playbook-scoped gating
here would sweep them in for the wrong reason.

All four currently shipping CRA on-time metrics carry the
``telemetry.ocsf.incident_finding@v1`` source-data shape, which is
what arms this SKELETON.

Fires when any regulatory-notification-cluster metric has no
``telemetry.ocsf.*`` entry in its ``telemetry_refs`` list. Output
formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML, no
network.

Implementation note: the ``Finding`` dataclass, ``has_ocsf_binding``
helper, and ``OCSF_TELEMETRY_PREFIX`` constant are reused from
``tools.ocsf_cluster_lint``. The scan/CLI drivers there are
playbook-scoped; this module carries a small step-scoped scan loop and
CLI wrapper so the shared driver stays a single-responsibility
playbook-scoped helper. Any consolidation of playbook-scoped +
step-scoped gates is a governance decision for a follow-on CORE.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import yaml

from tools.ocsf_cluster_lint import (
    DEFAULT_METRICS_DIR as METRICS_DIR,
    Finding,
    OCSF_TELEMETRY_PREFIX,
    REPO_ROOT,
    has_ocsf_binding,
)

# Regulatory-notification cluster: (playbook_id, step_id) tuples of
# playbook steps whose primary purpose is to dispatch a regulator-
# facing notification against a legally-defined clock. Metrics whose
# playbook_refs resolve EXCLUSIVELY to these tuples are considered
# regulatory-notification-class and must declare an OCSF source-data
# shape.
#
# Extending the cluster is a deliberate governance act — add a step
# tuple here only when the new notification surface lands with at
# least one OCSF telemetry binding artifact under content/telemetry/.
REGULATORY_NOTIFICATION_STEPS: frozenset[tuple[str, str]] = frozenset(
    {
        # CRA Article 14 regulator-notification step on the vuln_intake
        # playbook — dispatches the early-warning / 72h notification /
        # severe-incident / final report envelopes.
        (
            "playbook.vuln_intake@v1",
            "action--01a17a01-0000-4000-8000-000000000006",
        ),
    }
)


CLI_NAME = "regulatory-notification-ocsf-bindings"
CLUSTER_LABEL = "regulatory-notification-cluster"
CLUSTER_DESCR = "regulatory-notification cluster"
JSON_CLUSTER_KEY = "regulatory_notification_cluster"


def _playbook_ref_tuples(doc: dict) -> tuple[tuple[str, str], ...]:
    refs = doc.get("playbook_refs") or []
    out: list[tuple[str, str]] = []
    for r in refs:
        if not isinstance(r, dict):
            continue
        pid = r.get("playbook_id")
        sid = r.get("step_id")
        if isinstance(pid, str) and isinstance(sid, str):
            out.append((pid, sid))
    return tuple(out)


def _playbook_ids(doc: dict) -> tuple[str, ...]:
    return tuple(pid for pid, _sid in _playbook_ref_tuples(doc))


def _telemetry_refs(doc: dict) -> tuple[str, ...]:
    refs = doc.get("telemetry_refs") or []
    return tuple(r for r in refs if isinstance(r, str))


def is_regulatory_notification_metric(
    playbook_ref_tuples: Iterable[tuple[str, str]],
) -> bool:
    """Return True if ``playbook_ref_tuples`` is non-empty and every
    ``(playbook_id, step_id)`` pair lies in
    ``REGULATORY_NOTIFICATION_STEPS``.

    The step-scoped exclusivity gate keeps fan-out metrics that touch
    the same host playbook via other steps out of the cluster.
    """
    tuples = tuple(playbook_ref_tuples)
    if not tuples:
        return False
    return all(t in REGULATORY_NOTIFICATION_STEPS for t in tuples)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(metrics_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tuples = _playbook_ref_tuples(doc)
        if not is_regulatory_notification_metric(tuples):
            continue
        tr = _telemetry_refs(doc)
        if not has_ocsf_binding(tr):
            stable_id = doc.get("stable_id") or path.stem
            findings.append(
                Finding(
                    cluster_label=CLUSTER_LABEL,
                    metric_stable_id=stable_id,
                    metric_path=path,
                    playbook_refs=_playbook_ids(doc),
                    telemetry_refs=tr,
                )
            )
    return findings


def _emit_text(findings: list[Finding]) -> None:
    if not findings:
        print(
            f"{CLI_NAME}: PASS "
            f"({CLUSTER_DESCR} = {sorted(REGULATORY_NOTIFICATION_STEPS)})"
        )
        return
    print(
        f"{CLI_NAME}: FAIL — {len(findings)} {CLUSTER_LABEL} "
        "metric(s) missing OCSF source-data-shape binding:"
    )
    for f in findings:
        print(f"  {f.as_text()}")


def _emit_json(findings: list[Finding]) -> None:
    payload = {
        JSON_CLUSTER_KEY: [
            {"playbook_id": pid, "step_id": sid}
            for pid, sid in sorted(REGULATORY_NOTIFICATION_STEPS)
        ],
        "finding_count": len(findings),
        "findings": [f.as_dict() for f in findings],
        "status": "fail" if findings else "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assert every regulatory-notification-cluster metric carries "
            "an OCSF source-data-shape telemetry_ref (G-04 OCSF dimension)."
        )
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=METRICS_DIR,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    findings = scan(args.metrics_dir)
    if args.format == "json":
        _emit_json(findings)
    else:
        _emit_text(findings)
    return 1 if findings else 0


__all__ = [
    "REGULATORY_NOTIFICATION_STEPS",
    "OCSF_TELEMETRY_PREFIX",
    "Finding",
    "has_ocsf_binding",
    "is_regulatory_notification_metric",
    "scan",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
