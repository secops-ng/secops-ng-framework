"""Catalogue-wide OCSF source-data-shape binding assertion (G-04).

Floor-level catalogue guard for the OCSF source-data-shape dimension of
the G-04 KPI/KRI catalogue-maturity acceptance bar. The per-cluster
linters (``tools/lint_posture_ocsf_bindings.py``,
``tools/lint_detection_ocsf_bindings.py``) defend their own clusters
deeply — but a freshly-added operator-telemetry metric that belongs to
*neither* cluster would currently ship with no OCSF source-data shape
and nothing would trip. This catalogue-wide guard closes that gap at
the floor.

Rule: every metric under ``content/metrics/*.yaml`` whose
``measurement.source`` is an operator-telemetry source (i.e. anything
other than ``composite``) MUST declare at least one ``telemetry.ocsf.*``
entry in its ``telemetry_refs`` list.

Exemption: metrics whose ``measurement.source == "composite"`` are
explicitly exempt. Composite metrics are computed from the project's
own CI/governance signal (compiler byte-parity, replay determinism,
forward-public hygiene, GDPR lawful-basis coverage, LM endpoint EU
residency coverage, etc.) — not from operator OCSF telemetry — so an
OCSF source-data shape is not the right binding for them. The
exemption is keyed on ``measurement.source`` exactly, with no
metric-id allowlist, so newly-added composite governance metrics are
covered without a list update.

Fires when any non-composite metric has no ``telemetry.ocsf.*`` entry
in its ``telemetry_refs`` list, or has no ``telemetry_refs`` at all.
Output formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML,
no network. Reuses ``has_ocsf_binding`` /
``OCSF_TELEMETRY_PREFIX`` / ``DEFAULT_METRICS_DIR`` / ``REPO_ROOT``
from the shared per-cluster helper to keep the binding key check in
one place.

This is the SKELETON tier. Future siblings:

* CORE: deepen the guard so each ``telemetry.ocsf.*`` ref actually
  resolves to a real OCSF class under ``content/telemetry/``, not
  just presence.
* EXTEND: wire as a job stanza in ``.github/workflows/orphan-ci.yml``
  alongside ``posture-ocsf-bindings`` /
  ``detection-ocsf-bindings``, plus a README note.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from tools.ocsf_cluster_lint import (
    DEFAULT_METRICS_DIR as METRICS_DIR,
    OCSF_TELEMETRY_PREFIX,
    REPO_ROOT,
    has_ocsf_binding,
)

# Sentinel for the ``measurement.source`` value that exempts a metric
# from the OCSF source-data-shape requirement. Composite metrics are
# computed from the project's own CI / governance signal, not from
# operator OCSF telemetry, so an OCSF binding is not the right shape.
COMPOSITE_SOURCE = "composite"

CLI_NAME = "catalogue-ocsf-bindings"


@dataclass(frozen=True)
class CatalogueFinding:
    metric_stable_id: str
    metric_path: Path
    measurement_source: str
    telemetry_refs: tuple[str, ...]

    def _rel_path(self) -> str:
        try:
            return str(self.metric_path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.metric_path)

    def as_text(self) -> str:
        return (
            f"{self._rel_path()}: metric {self.metric_stable_id} "
            f"(measurement.source={self.measurement_source!r}) has no "
            f"OCSF telemetry_ref "
            f"(telemetry_refs={list(self.telemetry_refs)})"
        )

    def as_dict(self) -> dict:
        return {
            "metric_stable_id": self.metric_stable_id,
            "metric_path": self._rel_path(),
            "measurement_source": self.measurement_source,
            "telemetry_refs": list(self.telemetry_refs),
        }


def _load_metric(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _measurement_source(doc: dict) -> str:
    measurement = doc.get("measurement") or {}
    src = measurement.get("source")
    return src if isinstance(src, str) else ""


def _telemetry_refs(doc: dict) -> tuple[str, ...]:
    refs = doc.get("telemetry_refs") or []
    return tuple(r for r in refs if isinstance(r, str))


def is_operator_telemetry_source(measurement_source: str) -> bool:
    """Return True if the metric's ``measurement.source`` is an
    operator-telemetry source — i.e. anything other than the
    project-internal ``composite`` source.

    The exemption is keyed strictly on ``measurement.source ==
    'composite'``; any other value (siem_event_stream,
    posture_evidence_pull, etc.) is operator telemetry and must carry
    an OCSF source-data shape.
    """
    return bool(measurement_source) and measurement_source != COMPOSITE_SOURCE


def scan(metrics_dir: Path = METRICS_DIR) -> list[CatalogueFinding]:
    findings: list[CatalogueFinding] = []
    for path in sorted(metrics_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = _load_metric(path)
        src = _measurement_source(doc)
        if not is_operator_telemetry_source(src):
            # Exempt: composite source, or missing measurement block
            # entirely (a separate schema lint catches the latter).
            continue
        tr = _telemetry_refs(doc)
        if not has_ocsf_binding(tr):
            stable_id = doc.get("stable_id") or path.stem
            findings.append(
                CatalogueFinding(
                    metric_stable_id=stable_id,
                    metric_path=path,
                    measurement_source=src,
                    telemetry_refs=tr,
                )
            )
    return findings


def _emit_text(findings: list[CatalogueFinding]) -> None:
    if not findings:
        print(
            f"{CLI_NAME}: PASS "
            f"(every operator-telemetry metric carries an OCSF "
            f"source-data shape; composite metrics exempt)"
        )
        return
    print(
        f"{CLI_NAME}: FAIL — {len(findings)} operator-telemetry "
        "metric(s) missing OCSF source-data-shape binding:"
    )
    for f in findings:
        print(f"  {f.as_text()}")


def _emit_json(findings: list[CatalogueFinding]) -> None:
    payload = {
        "exempt_source": COMPOSITE_SOURCE,
        "finding_count": len(findings),
        "findings": [f.as_dict() for f in findings],
        "status": "fail" if findings else "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assert every operator-telemetry metric in "
            "content/metrics/ carries an OCSF source-data-shape "
            "telemetry_ref (G-04 OCSF catalogue-wide dimension). "
            "Composite-source metrics are exempt."
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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
