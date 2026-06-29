"""Sovereignty-cluster LM-endpoint coverage/UNKNOWN-exposure pairing (G-04).

Defends the **sovereignty corner** of the G-04 KPI/KRI catalogue-maturity
acceptance bar: every sovereignty-cluster LM-endpoint coverage KPI must
ship alongside a sovereignty-cluster UNKNOWN-exposure residual-risk KRI
so the residual-risk reading cannot silently regress out of the
catalogue.

The shipped pairing this lint locks in (F-MET-SOV SKELETON, PR #542):

* ``kpi.lm_endpoint_eu_residency_coverage@v1`` (coverage KPI)
* ``kri.lm_endpoint_unknown_residency_exposure@v1``     (residual-risk KRI)

Rule.
1. **Identify sovereignty-cluster LM-endpoint coverage KPIs.** A metric
   under ``content/metrics/*.yaml`` matches when ALL of:

   * ``kind == 'kpi'``
   * ``foundation_property`` includes ``sovereignty``
   * ``stable_id`` matches ``kpi.lm_endpoint_*_coverage@v<N>``

2. **Require a sovereignty-cluster UNKNOWN-exposure KRI at the same
   version family.** For each such KPI at version ``vN``, at least one
   metric in ``content/metrics/*.yaml`` must match ALL of:

   * ``kind == 'kri'``
   * ``foundation_property`` includes ``sovereignty``
   * ``stable_id`` matches ``kri.lm_endpoint_*_unknown_*_exposure@v<N>``

A coverage KPI without such a KRI fails the lint. The pairing is
keyed on version family (not on a fixed name) so the lint generalises
cleanly when a second sovereignty LM-endpoint coverage KPI lands and
ships its own paired UNKNOWN-exposure KRI; the rule says "carry the
pairing", not "carry *this* fixed name".

Output formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML,
no network.

Future sibling (EXTEND, separate card): extend the pairing invariant
to the determinism corner or to non-LM-endpoint sovereignty metrics.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS_DIR = REPO_ROOT / "content" / "metrics"

SOVEREIGNTY_PROPERTY = "sovereignty"

# Stable-id patterns. Captured group is the version number so the
# pairing is matched per version family — a v2 KPI requires a v2 KRI,
# not just any UNKNOWN-exposure KRI.
COVERAGE_KPI_RE = re.compile(
    r"^kpi\.lm_endpoint_[a-z0-9_]+_coverage@v(?P<ver>\d+)$"
)
UNKNOWN_EXPOSURE_KRI_RE = re.compile(
    r"^kri\.lm_endpoint_(?:[a-z0-9_]+_)?unknown_[a-z0-9_]*exposure@v(?P<ver>\d+)$"
)

CLI_NAME = "sovereignty-lm-endpoint-pairing"


@dataclass(frozen=True)
class PairingFinding:
    kpi_stable_id: str
    kpi_path: Path
    kpi_version: str
    candidate_kri_ids: tuple[str, ...]

    def _rel(self) -> str:
        try:
            return str(self.kpi_path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.kpi_path)

    def as_text(self) -> str:
        return (
            f"{self._rel()}: sovereignty-cluster LM-endpoint coverage "
            f"KPI {self.kpi_stable_id} has no paired sovereignty-cluster "
            f"UNKNOWN-exposure KRI at @v{self.kpi_version} — expected "
            f"a metric matching "
            f"kri.lm_endpoint_*_unknown_*_exposure@v{self.kpi_version} "
            f"with foundation_property including 'sovereignty'"
        )

    def as_dict(self) -> dict:
        return {
            "kpi_stable_id": self.kpi_stable_id,
            "kpi_path": self._rel(),
            "kpi_version": self.kpi_version,
            "candidate_kri_ids": list(self.candidate_kri_ids),
        }


def _load_metric(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _foundation_properties(doc: dict) -> tuple[str, ...]:
    fp = doc.get("foundation_property") or []
    if isinstance(fp, str):
        return (fp,)
    return tuple(p for p in fp if isinstance(p, str))


def _kind(doc: dict) -> str:
    k = doc.get("kind")
    return k if isinstance(k, str) else ""


def _stable_id(doc: dict) -> str:
    sid = doc.get("stable_id")
    return sid if isinstance(sid, str) else ""


def is_sovereignty(doc: dict) -> bool:
    return SOVEREIGNTY_PROPERTY in _foundation_properties(doc)


def coverage_kpi_match(doc: dict) -> re.Match[str] | None:
    if _kind(doc) != "kpi":
        return None
    if not is_sovereignty(doc):
        return None
    return COVERAGE_KPI_RE.match(_stable_id(doc))


def unknown_exposure_kri_match(doc: dict) -> re.Match[str] | None:
    if _kind(doc) != "kri":
        return None
    if not is_sovereignty(doc):
        return None
    return UNKNOWN_EXPOSURE_KRI_RE.match(_stable_id(doc))


def scan(metrics_dir: Path = DEFAULT_METRICS_DIR) -> list[PairingFinding]:
    coverage_kpis: list[tuple[Path, dict, re.Match[str]]] = []
    unknown_kris_by_ver: dict[str, list[str]] = {}
    for path in sorted(metrics_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = _load_metric(path)
        m_kpi = coverage_kpi_match(doc)
        if m_kpi is not None:
            coverage_kpis.append((path, doc, m_kpi))
            continue
        m_kri = unknown_exposure_kri_match(doc)
        if m_kri is not None:
            ver = m_kri.group("ver")
            unknown_kris_by_ver.setdefault(ver, []).append(_stable_id(doc))

    findings: list[PairingFinding] = []
    for path, doc, m_kpi in coverage_kpis:
        ver = m_kpi.group("ver")
        candidates = tuple(unknown_kris_by_ver.get(ver, ()))
        if not candidates:
            findings.append(
                PairingFinding(
                    kpi_stable_id=_stable_id(doc),
                    kpi_path=path,
                    kpi_version=ver,
                    candidate_kri_ids=candidates,
                )
            )
    return findings


def _emit_text(findings: list[PairingFinding]) -> None:
    if not findings:
        print(
            f"{CLI_NAME}: PASS "
            f"(every sovereignty-cluster LM-endpoint coverage KPI "
            f"carries a paired UNKNOWN-exposure KRI at the same "
            f"version family)"
        )
        return
    print(
        f"{CLI_NAME}: FAIL — {len(findings)} sovereignty-cluster "
        "LM-endpoint coverage KPI(s) without an UNKNOWN-exposure "
        "pairing:"
    )
    for f in findings:
        print(f"  {f.as_text()}")


def _emit_json(findings: list[PairingFinding]) -> None:
    payload = {
        "finding_count": len(findings),
        "findings": [f.as_dict() for f in findings],
        "status": "fail" if findings else "pass",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assert every sovereignty-cluster LM-endpoint coverage KPI "
            "(kpi.lm_endpoint_*_coverage@vN with foundation_property "
            "including 'sovereignty') is paired with a "
            "sovereignty-cluster UNKNOWN-exposure KRI "
            "(kri.lm_endpoint_*_unknown_*_exposure@vN) at the same "
            "version family (G-04 sovereignty corner)."
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
        default=DEFAULT_METRICS_DIR,
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
