"""Shared OCSF source-data-shape cluster-binding linter helper (G-04).

Backs the per-cluster linters (``tools/lint_posture_ocsf_bindings.py``,
``tools/lint_detection_ocsf_bindings.py``) with a single Finding
dataclass + YAML loader + scan loop + CLI driver. Each per-cluster
linter remains a thin wrapper that supplies a ``ClusterSpec`` and
re-exports the helpers under the names its tests already import — the
CLI's text+json output shape is preserved verbatim so downstream
dashboards keep working.

Consolidating here was deferred in the F-MET-OCSF-DETECT SKELETON to
keep that PR small and reviewable; the F-MET-OCSF-DETECT CORE wave
extracts the shared shape now that posture + detection have proven
the contract holds across two clusters.

A metric is treated as cluster-class when its ``playbook_refs``
resolve **exclusively** to playbooks in the cluster set. The
exclusivity gate keeps fan-out pipeline/sovereignty metrics — whose
source-data shape is correctly non-OCSF — out of the cluster.

Fires when any cluster-class metric has no ``telemetry.ocsf.*`` entry
in its ``telemetry_refs`` list. Output formats: ``text`` (default) and
``json``. Pure stdlib + PyYAML, no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS_DIR = REPO_ROOT / "content" / "metrics"

OCSF_TELEMETRY_PREFIX = "telemetry.ocsf."


@dataclass(frozen=True)
class ClusterSpec:
    """Per-cluster configuration handed to the shared scan/CLI driver.

    ``cli_name`` is the leading label printed on PASS/FAIL lines (so
    contributors grepping CI logs know which linter spoke).
    ``cluster_label`` is used in finding text and in the FAIL summary
    line ("N <cluster_label> metric(s) ..."). ``cluster_descr`` is the
    PASS-line descriptor ("<cluster_descr> = [...]"). ``json_cluster_key``
    names the cluster member-list under the JSON payload.
    """

    cli_name: str
    cluster_label: str
    cluster_descr: str
    json_cluster_key: str
    playbook_ids: frozenset[str]
    cli_description: str


@dataclass(frozen=True)
class Finding:
    cluster_label: str
    metric_stable_id: str
    metric_path: Path
    playbook_refs: tuple[str, ...]
    telemetry_refs: tuple[str, ...]

    def _rel_path(self) -> str:
        try:
            return str(self.metric_path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.metric_path)

    def as_text(self) -> str:
        return (
            f"{self._rel_path()}: {self.cluster_label} "
            f"metric {self.metric_stable_id} has no OCSF telemetry_ref "
            f"(playbook_refs={list(self.playbook_refs)}, "
            f"telemetry_refs={list(self.telemetry_refs)})"
        )

    def as_dict(self) -> dict:
        return {
            "metric_stable_id": self.metric_stable_id,
            "metric_path": self._rel_path(),
            "playbook_refs": list(self.playbook_refs),
            "telemetry_refs": list(self.telemetry_refs),
        }


def _load_metric(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _playbook_ids(doc: dict) -> tuple[str, ...]:
    refs = doc.get("playbook_refs") or []
    out: list[str] = []
    for r in refs:
        if isinstance(r, dict):
            pid = r.get("playbook_id")
            if isinstance(pid, str):
                out.append(pid)
    return tuple(out)


def _telemetry_refs(doc: dict) -> tuple[str, ...]:
    refs = doc.get("telemetry_refs") or []
    return tuple(r for r in refs if isinstance(r, str))


def is_cluster_metric(
    playbook_ids: Iterable[str], cluster_ids: Iterable[str]
) -> bool:
    """Return True if ``playbook_ids`` is non-empty and a subset of
    the cluster's playbook set.

    The exclusivity gate keeps fan-out metrics out of the cluster.
    """
    ids = tuple(playbook_ids)
    if not ids:
        return False
    cluster = frozenset(cluster_ids)
    return all(pid in cluster for pid in ids)


def has_ocsf_binding(telemetry_refs: Iterable[str]) -> bool:
    return any(r.startswith(OCSF_TELEMETRY_PREFIX) for r in telemetry_refs)


def scan_cluster(
    metrics_dir: Path, spec: ClusterSpec
) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(metrics_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = _load_metric(path)
        pb = _playbook_ids(doc)
        if not is_cluster_metric(pb, spec.playbook_ids):
            continue
        tr = _telemetry_refs(doc)
        if not has_ocsf_binding(tr):
            stable_id = doc.get("stable_id") or path.stem
            findings.append(
                Finding(
                    cluster_label=spec.cluster_label,
                    metric_stable_id=stable_id,
                    metric_path=path,
                    playbook_refs=pb,
                    telemetry_refs=tr,
                )
            )
    return findings


def _emit_text(findings: list[Finding], spec: ClusterSpec) -> None:
    if not findings:
        print(
            f"{spec.cli_name}: PASS "
            f"({spec.cluster_descr} = {sorted(spec.playbook_ids)})"
        )
        return
    print(
        f"{spec.cli_name}: FAIL — {len(findings)} {spec.cluster_label} "
        "metric(s) missing OCSF source-data-shape binding:"
    )
    for f in findings:
        print(f"  {f.as_text()}")


def _emit_json(findings: list[Finding], spec: ClusterSpec) -> None:
    payload = {
        spec.json_cluster_key: sorted(spec.playbook_ids),
        "finding_count": len(findings),
        "findings": [f.as_dict() for f in findings],
        "status": "fail" if findings else "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def run_cli(argv: list[str] | None, spec: ClusterSpec) -> int:
    """Shared argparse driver. Per-cluster linters call this from
    their own ``main``."""
    parser = argparse.ArgumentParser(description=spec.cli_description)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=DEFAULT_METRICS_DIR,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    findings = scan_cluster(args.metrics_dir, spec)
    if args.format == "json":
        _emit_json(findings, spec)
    else:
        _emit_text(findings, spec)
    return 1 if findings else 0


__all__ = [
    "ClusterSpec",
    "Finding",
    "OCSF_TELEMETRY_PREFIX",
    "DEFAULT_METRICS_DIR",
    "REPO_ROOT",
    "has_ocsf_binding",
    "is_cluster_metric",
    "scan_cluster",
    "run_cli",
]
