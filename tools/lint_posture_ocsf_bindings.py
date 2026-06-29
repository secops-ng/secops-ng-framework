"""Posture-cluster OCSF source-data-shape binding assertion (G-04).

Defends the OCSF source-data-shape dimension of the G-04 KPI/KRI
catalogue-maturity acceptance bar: every metric in the asset/patch
**posture** cluster must declare at least one OCSF ``telemetry_ref``
so the upstream source-data shape is pinned alongside the internal
evidence-artifact field binding.

A metric is treated as posture-class when its ``playbook_refs`` resolve
**exclusively** to playbooks in the posture cluster (currently the
asset_management and patch_management reconciliation surfaces). That
exclusivity gate intentionally excludes pipeline/sovereignty metrics
(compiler byte-parity, replay determinism, forward-public hygiene,
EU-residency coverage) whose source-data shape is correctly non-OCSF
even though they fan out to asset_management as one fan-out among
several. The boundary mirrors the cluster the F-MET-OCSF-POSTURE
SKELETON used to ship the first four bindings.

Fires when any posture-cluster metric has no ``telemetry.ocsf.*``
entry in its ``telemetry_refs`` list. Output formats: ``text`` (default)
and ``json``. Pure stdlib + PyYAML, no network.
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
METRICS_DIR = REPO_ROOT / "content" / "metrics"

# Posture cluster: playbooks whose primary purpose is to emit
# posture/inventory telemetry against an authoritative source. Metrics
# whose playbook_refs resolve EXCLUSIVELY to these playbooks are
# considered posture-class and must declare an OCSF source-data shape.
#
# Extending the cluster is a deliberate governance act — add a playbook
# id here only when the new posture surface lands with at least one
# OCSF telemetry binding artifact under content/telemetry/.
POSTURE_PLAYBOOK_IDS: frozenset[str] = frozenset(
    {
        "playbook.asset_management@v1",
        "playbook.patch_management@v1",
    }
)

OCSF_TELEMETRY_PREFIX = "telemetry.ocsf."


@dataclass(frozen=True)
class Finding:
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
            f"{self._rel_path()}: posture-cluster "
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


def is_posture_metric(playbook_ids: Iterable[str]) -> bool:
    """Return True if ``playbook_ids`` are non-empty and a subset of
    the posture-cluster playbook set.

    The exclusivity gate is what keeps pipeline/sovereignty metrics
    (which fan out across many playbooks) out of the posture cluster.
    """
    ids = tuple(playbook_ids)
    if not ids:
        return False
    return all(pid in POSTURE_PLAYBOOK_IDS for pid in ids)


def has_ocsf_binding(telemetry_refs: Iterable[str]) -> bool:
    return any(r.startswith(OCSF_TELEMETRY_PREFIX) for r in telemetry_refs)


def scan(metrics_dir: Path = METRICS_DIR) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(metrics_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = _load_metric(path)
        pb = _playbook_ids(doc)
        if not is_posture_metric(pb):
            continue
        tr = _telemetry_refs(doc)
        if not has_ocsf_binding(tr):
            stable_id = doc.get("stable_id") or path.stem
            findings.append(
                Finding(
                    metric_stable_id=stable_id,
                    metric_path=path,
                    playbook_refs=pb,
                    telemetry_refs=tr,
                )
            )
    return findings


def _emit_text(findings: list[Finding]) -> None:
    if not findings:
        print(
            "posture-ocsf-bindings: PASS "
            f"(posture cluster = {sorted(POSTURE_PLAYBOOK_IDS)})"
        )
        return
    print(
        f"posture-ocsf-bindings: FAIL — {len(findings)} posture-cluster "
        "metric(s) missing OCSF source-data-shape binding:"
    )
    for f in findings:
        print(f"  {f.as_text()}")


def _emit_json(findings: list[Finding]) -> None:
    payload = {
        "posture_cluster": sorted(POSTURE_PLAYBOOK_IDS),
        "finding_count": len(findings),
        "findings": [f.as_dict() for f in findings],
        "status": "fail" if findings else "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assert every posture-cluster metric carries an OCSF "
            "source-data-shape telemetry_ref (G-04 OCSF dimension)."
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


if __name__ == "__main__":
    sys.exit(main())
