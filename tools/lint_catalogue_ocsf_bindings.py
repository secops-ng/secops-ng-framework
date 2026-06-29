"""Catalogue-wide OCSF source-data-shape binding assertion (G-04).

Floor + CORE-tier catalogue guard for the OCSF source-data-shape
dimension of the G-04 KPI/KRI catalogue-maturity acceptance bar. The
per-cluster linters (``tools/lint_posture_ocsf_bindings.py``,
``tools/lint_detection_ocsf_bindings.py``) defend their own clusters
deeply — but a freshly-added operator-telemetry metric that belongs to
*neither* cluster would currently ship with no OCSF source-data shape
and nothing would trip. This catalogue-wide guard closes that gap at
the floor.

Two-layer rule:

1. **Presence (SKELETON floor).** Every metric under
   ``content/metrics/*.yaml`` whose ``measurement.source`` is an
   operator-telemetry source (i.e. anything other than ``composite``)
   MUST declare at least one ``telemetry.ocsf.*`` entry in its
   ``telemetry_refs`` list.
2. **Resolution (CORE).** Each declared ``telemetry.ocsf.*`` entry on
   such a metric MUST resolve to a real artifact under
   ``content/telemetry/``. The shipped tree uses files named
   ``content/telemetry/<ref>.json`` (e.g.
   ``telemetry.ocsf.device_inventory_info@v1.json``). A
   present-but-dangling ref — pointing at an OCSF class that does not
   actually exist on disk — fails the guard. This catches the failure
   mode where a contributor declares an OCSF binding but the
   referenced class artifact is missing or misnamed.

Exemption: metrics whose ``measurement.source == "composite"`` are
explicitly exempt. Composite metrics are computed from the project's
own CI/governance signal (compiler byte-parity, replay determinism,
forward-public hygiene, GDPR lawful-basis coverage, LM endpoint EU
residency coverage, etc.) — not from operator OCSF telemetry — so an
OCSF source-data shape is not the right binding for them. The
exemption is keyed on ``measurement.source`` exactly, with no
metric-id allowlist, so newly-added composite governance metrics are
covered without a list update.

Output formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML,
no network. Reuses ``has_ocsf_binding`` / ``OCSF_TELEMETRY_PREFIX`` /
``DEFAULT_METRICS_DIR`` / ``REPO_ROOT`` from the shared per-cluster
helper to keep the binding key check in one place.

Future sibling (EXTEND, separate card): wire as a job stanza in
``.github/workflows/orphan-ci.yml`` alongside ``posture-ocsf-bindings``
/ ``detection-ocsf-bindings``, plus a README note.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from tools.ocsf_cluster_lint import (
    DEFAULT_METRICS_DIR as METRICS_DIR,
    OCSF_TELEMETRY_PREFIX,
    REPO_ROOT,
    has_ocsf_binding,
)

# Default location for OCSF class artifacts the catalogue resolves
# ``telemetry.ocsf.*`` refs against. Per-ref filename convention is
# ``<ref>.json`` (e.g. ``telemetry.ocsf.patch_state@v1.json``); this
# is the on-disk shape the shipped tree already uses.
DEFAULT_TELEMETRY_DIR = REPO_ROOT / "content" / "telemetry"

# Sentinel for the ``measurement.source`` value that exempts a metric
# from the OCSF source-data-shape requirement. Composite metrics are
# computed from the project's own CI / governance signal, not from
# operator OCSF telemetry, so an OCSF binding is not the right shape.
COMPOSITE_SOURCE = "composite"

# Finding reason codes — keep machine-readable so downstream dashboards
# can split presence vs resolution failures without parsing prose.
REASON_NO_BINDING = "no_ocsf_binding"
REASON_DANGLING_REF = "dangling_ocsf_ref"

CLI_NAME = "catalogue-ocsf-bindings"


@dataclass(frozen=True)
class CatalogueFinding:
    metric_stable_id: str
    metric_path: Path
    measurement_source: str
    telemetry_refs: tuple[str, ...]
    reason: str = REASON_NO_BINDING
    unresolved_refs: tuple[str, ...] = field(default_factory=tuple)

    def _rel_path(self) -> str:
        try:
            return str(self.metric_path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.metric_path)

    def as_text(self) -> str:
        if self.reason == REASON_DANGLING_REF:
            return (
                f"{self._rel_path()}: metric {self.metric_stable_id} "
                f"(measurement.source={self.measurement_source!r}) has "
                f"dangling OCSF telemetry_ref(s) "
                f"{list(self.unresolved_refs)} — no matching artifact "
                f"under content/telemetry/"
            )
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
            "reason": self.reason,
            "unresolved_refs": list(self.unresolved_refs),
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


def _ocsf_refs(telemetry_refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(r for r in telemetry_refs if r.startswith(OCSF_TELEMETRY_PREFIX))


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


def resolve_ocsf_ref(ref: str, telemetry_dir: Path = DEFAULT_TELEMETRY_DIR) -> bool:
    """Return True iff the OCSF telemetry ref resolves to a real
    artifact under ``telemetry_dir``.

    Filename convention matches the shipped tree: each ref
    ``telemetry.ocsf.<class>@v<n>`` is backed by a file
    ``<ref>.json`` under ``content/telemetry/``. Refs that do not
    start with ``OCSF_TELEMETRY_PREFIX`` are not OCSF refs and are
    treated as unresolved by this helper (callers should filter
    first).
    """
    if not ref.startswith(OCSF_TELEMETRY_PREFIX):
        return False
    return (telemetry_dir / f"{ref}.json").is_file()


def scan(
    metrics_dir: Path = METRICS_DIR,
    telemetry_dir: Path = DEFAULT_TELEMETRY_DIR,
) -> list[CatalogueFinding]:
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
        stable_id = doc.get("stable_id") or path.stem
        if not has_ocsf_binding(tr):
            findings.append(
                CatalogueFinding(
                    metric_stable_id=stable_id,
                    metric_path=path,
                    measurement_source=src,
                    telemetry_refs=tr,
                    reason=REASON_NO_BINDING,
                )
            )
            continue
        # CORE: every OCSF-prefixed ref on this metric must resolve
        # to a real artifact under content/telemetry/. A
        # present-but-dangling ref fails.
        unresolved = tuple(
            r for r in _ocsf_refs(tr)
            if not resolve_ocsf_ref(r, telemetry_dir)
        )
        if unresolved:
            findings.append(
                CatalogueFinding(
                    metric_stable_id=stable_id,
                    metric_path=path,
                    measurement_source=src,
                    telemetry_refs=tr,
                    reason=REASON_DANGLING_REF,
                    unresolved_refs=unresolved,
                )
            )
    return findings


def _emit_text(findings: list[CatalogueFinding]) -> None:
    if not findings:
        print(
            f"{CLI_NAME}: PASS "
            f"(every operator-telemetry metric carries an OCSF "
            f"source-data shape that resolves under "
            f"content/telemetry/; composite metrics exempt)"
        )
        return
    print(
        f"{CLI_NAME}: FAIL — {len(findings)} operator-telemetry "
        "metric(s) with OCSF source-data-shape issues:"
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
            "telemetry_ref that resolves to a real artifact under "
            "content/telemetry/ (G-04 OCSF catalogue-wide dimension). "
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
    parser.add_argument(
        "--telemetry-dir",
        type=Path,
        default=DEFAULT_TELEMETRY_DIR,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    findings = scan(args.metrics_dir, args.telemetry_dir)
    if args.format == "json":
        _emit_json(findings)
    else:
        _emit_text(findings)
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
