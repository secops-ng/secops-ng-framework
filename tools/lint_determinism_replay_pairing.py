"""Determinism-cluster replay coverage/drift residual-risk pairing (G-04).

Defends the **determinism corner** of the G-04 KPI/KRI catalogue-maturity
acceptance bar: every determinism-cluster replay coverage/health KPI
must ship alongside a determinism-cluster replay drift residual-risk
KRI so the residual-risk reading cannot silently regress out of the
catalogue.

The shipped pairing this lint locks in (F-MET-DET earlier waves):

* ``kpi.same_target_replay_determinism_rate@v1`` (coverage KPI)
* ``kri.same_target_replay_drift@v1``             (residual-risk KRI)

This lint is the determinism-corner sibling of
``tools/lint_sovereignty_lm_endpoint_pairing.py`` (F-MET-SOV CORE, PR
#543), which encoded the same residual-risk pairing invariant for the
sovereignty corner of FOUNDATION. The sovereignty lane's semantics are
intentionally NOT shared from this module — the sovereignty lint
ships its own locked CLI and is reviewed separately; this module
mirrors the pattern at the cost of some duplication so the
determinism corner can be reasoned about (and reviewed) in isolation.

Rule.
1. **Identify determinism-cluster replay coverage KPIs.** A metric
   under ``content/metrics/*.yaml`` matches when ALL of:

   * ``kind == 'kpi'``
   * ``foundation_property`` includes ``determinism``
   * ``stable_id`` matches
     ``kpi.*replay*_(determinism|parity)_rate@v<N>``

2. **Require a determinism-cluster replay drift KRI at the same
   version family.** For each such KPI at version ``vN``, at least
   one metric in ``content/metrics/*.yaml`` must match ALL of:

   * ``kind == 'kri'``
   * ``foundation_property`` includes ``determinism``
   * ``stable_id`` matches ``kri.*replay*_drift@v<N>``

A coverage KPI without such a KRI fails the lint. The pairing is
keyed on version family (not on a fixed name) so the lint generalises
cleanly when a second determinism-corner replay coverage KPI lands
and ships its own paired drift KRI; the rule says "carry the
pairing", not "carry *this* fixed name".

Scope note: today the determinism corner contains exactly one shipped
replay coverage/drift pair (``same_target_replay_*@v1``). The lint
therefore holds non-vacuously on the LHS (one coverage KPI exercised)
and is wired so future replay coverage KPIs cannot silently drop the
paired drift signal. Non-replay determinism KPIs
(``cross_target_audit_envelope_parity_rate``,
``span_block_emitter_determinism_rate``) are out of scope of this
EXTEND card — they currently lack paired drift KRIs and have been
flagged for separate sibling work.

Output formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML,
no network.
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

DETERMINISM_PROPERTY = "determinism"

# Stable-id patterns. Captured group is the version number so the
# pairing is matched per version family — a v2 KPI requires a v2 KRI,
# not just any drift KRI.
COVERAGE_KPI_RE = re.compile(
    r"^kpi\.[a-z0-9_]*replay[a-z0-9_]*_(?:determinism|parity)_rate@v(?P<ver>\d+)$"
)
DRIFT_KRI_RE = re.compile(
    r"^kri\.[a-z0-9_]*replay[a-z0-9_]*_drift@v(?P<ver>\d+)$"
)

CLI_NAME = "determinism-replay-pairing"


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
            f"{self._rel()}: determinism-cluster replay coverage "
            f"KPI {self.kpi_stable_id} has no paired determinism-cluster "
            f"replay drift KRI at @v{self.kpi_version} — expected "
            f"a metric matching "
            f"kri.*replay*_drift@v{self.kpi_version} "
            f"with foundation_property including 'determinism'"
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


def is_determinism(doc: dict) -> bool:
    return DETERMINISM_PROPERTY in _foundation_properties(doc)


def coverage_kpi_match(doc: dict) -> re.Match[str] | None:
    if _kind(doc) != "kpi":
        return None
    if not is_determinism(doc):
        return None
    return COVERAGE_KPI_RE.match(_stable_id(doc))


def drift_kri_match(doc: dict) -> re.Match[str] | None:
    if _kind(doc) != "kri":
        return None
    if not is_determinism(doc):
        return None
    return DRIFT_KRI_RE.match(_stable_id(doc))


def scan(metrics_dir: Path = DEFAULT_METRICS_DIR) -> list[PairingFinding]:
    coverage_kpis: list[tuple[Path, dict, re.Match[str]]] = []
    drift_kris_by_ver: dict[str, list[str]] = {}
    for path in sorted(metrics_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = _load_metric(path)
        m_kpi = coverage_kpi_match(doc)
        if m_kpi is not None:
            coverage_kpis.append((path, doc, m_kpi))
            continue
        m_kri = drift_kri_match(doc)
        if m_kri is not None:
            ver = m_kri.group("ver")
            drift_kris_by_ver.setdefault(ver, []).append(_stable_id(doc))

    findings: list[PairingFinding] = []
    for path, doc, m_kpi in coverage_kpis:
        ver = m_kpi.group("ver")
        candidates = tuple(drift_kris_by_ver.get(ver, ()))
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
            f"(every determinism-cluster replay coverage KPI carries "
            f"a paired drift KRI at the same version family)"
        )
        return
    print(
        f"{CLI_NAME}: FAIL — {len(findings)} determinism-cluster "
        "replay coverage KPI(s) without a drift pairing:"
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
            "Assert every determinism-cluster replay coverage KPI "
            "(kpi.*replay*_(determinism|parity)_rate@vN with "
            "foundation_property including 'determinism') is paired "
            "with a determinism-cluster replay drift KRI "
            "(kri.*replay*_drift@vN) at the same version family "
            "(G-04 determinism corner)."
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
