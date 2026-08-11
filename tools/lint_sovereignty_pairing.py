"""Sovereignty-cluster coverage/residual-risk pairing invariant (G-04, F-SV-06).

A coverage ratio reports what is confirmed good. It cannot report the exposure
hiding in the part it could not classify — the operator-supplied, self-hosted
or private-gateway shape that a residency check reads as "unknown" rather than
as "non-EU". So a coverage KPI is only honest when a residual-risk KRI reads
the same population alongside it.

`tools/lint_sovereignty_lm_endpoint_pairing.py` enforced that for exactly one
indicator family, matching `kpi.lm_endpoint_*_coverage@vN` against
`kri.lm_endpoint_*_unknown_*_exposure@vN` **by name**. This module replaces it
and changes two things:

* **Scope** — every sovereignty-cluster coverage KPI, not one family. The
  cluster carries 15 KPIs against 6 KRIs, so most coverage indicators had no
  residual-risk counterpart under any rule.
* **Mechanism** — the pairing is *declared* in `residual_risk_refs` rather
  than inferred from a naming convention, so it survives a rename on either
  side. Several KRIs already named their counterpart in prose
  (`kri.lm_endpoint_unknown_residency_exposure@v1` opens "Residual-risk
  indicator paired with …"); this promotes that prose into a checked field.

Two severities, following the house pattern for an invariant that cannot be
satisfied everywhere on the day it lands:

**HARD** — a declared pairing that does not hold. Always gates.

  * ``unresolved_residual_risk_ref`` — the ref names no shipped metric.
  * ``residual_risk_ref_not_kri`` — it resolves, but is not a ``kri``.
  * ``residual_risk_ref_version_mismatch`` — different version family. A v2
    coverage KPI paired against a v1 KRI is reading a different population.
  * ``residual_risk_ref_property_gap`` — the KRI does not declare
    ``sovereignty``, so a per-property audit of the cluster would not see the
    pairing. Deliberately *not* "declares every property the KPI declares":
    ``kpi.lm_endpoint_eu_residency_coverage@v1`` serves both sovereignty and
    determinism while its counterparts honestly serve only sovereignty, and
    the stricter rule would have pushed contributors to add untrue property
    claims to make the lint pass.
  * ``lm_endpoint_pairing_regressed`` — an ``lm_endpoint_*_coverage`` KPI with
    no declaration at all. This is the retired module's invariant, kept HARD
    rather than folded into the SOFT population below: it shipped green and
    must not regress just because the rule around it got wider.

  * ``coverage_kpi_without_residual_risk`` — a sovereignty coverage KPI that
    declares no counterpart at all. This started SOFT under a ceiling of 5
    while the missing KRIs did not exist; F-SV-06 stage 2 authored all five
    and promoted the code, deleting the ceiling rather than leaving it at 0 —
    a dead ceiling invites someone to raise it. Every sovereignty coverage
    KPI now ships with its residual-risk counterpart or the gate is red.

Output formats: ``text`` (default) and ``json``. Pure stdlib + PyYAML, no
network.
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

CLI_NAME = "sovereignty-pairing"

# A coverage KPI is one whose stable id names a coverage reading. Matched on
# the id rather than a curated list so a new coverage KPI is in scope the
# moment it lands, instead of silently escaping the invariant.
COVERAGE_KPI_RE = re.compile(r"^kpi\.[a-z0-9_]*coverage@v(?P<ver>\d+)$")

# The family the retired linter guarded; kept HARD so it cannot regress.
LM_ENDPOINT_COVERAGE_RE = re.compile(
    r"^kpi\.lm_endpoint_[a-z0-9_]+_coverage@v(?P<ver>\d+)$"
)

VERSION_RE = re.compile(r"@v(?P<ver>\d+)$")

HARD_CODES = frozenset({
    "unresolved_residual_risk_ref",
    "residual_risk_ref_not_kri",
    "residual_risk_ref_version_mismatch",
    "residual_risk_ref_property_gap",
    "lm_endpoint_pairing_regressed",
    "coverage_kpi_without_residual_risk",
})
# Promoted empty by F-SV-06 stage 2; kept so the severity partition stays
# explicit and a future SOFT code is a decision, not a drive-by.
SOFT_CODES = frozenset()


@dataclass(frozen=True)
class PairingFinding:
    code: str
    kpi_stable_id: str
    kpi_path: Path
    detail: str

    @property
    def severity(self) -> str:
        return "HARD" if self.code in HARD_CODES else "SOFT"

    def _rel(self) -> str:
        try:
            return str(self.kpi_path.relative_to(REPO_ROOT))
        except ValueError:
            return str(self.kpi_path)

    def as_text(self) -> str:
        return (
            f"{self.severity}  {self._rel()}: [{self.code}] "
            f"{self.kpi_stable_id} — {self.detail}"
        )

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "kpi_stable_id": self.kpi_stable_id,
            "kpi_path": self._rel(),
            "detail": self.detail,
        }


def _load_metric(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _foundation_properties(doc: dict) -> frozenset[str]:
    fp = doc.get("foundation_property") or []
    if isinstance(fp, str):
        return frozenset({fp})
    return frozenset(p for p in fp if isinstance(p, str))


def _str_field(doc: dict, key: str) -> str:
    v = doc.get(key)
    return v if isinstance(v, str) else ""


def is_sovereignty(doc: dict) -> bool:
    return SOVEREIGNTY_PROPERTY in _foundation_properties(doc)


def _version(stable_id: str) -> str:
    m = VERSION_RE.search(stable_id)
    return m.group("ver") if m else ""


def _residual_refs(doc: dict) -> tuple[str, ...]:
    refs = doc.get("residual_risk_refs") or []
    if isinstance(refs, str):
        return (refs,)
    return tuple(r for r in refs if isinstance(r, str))


def is_coverage_kpi(doc: dict) -> bool:
    return (
        _str_field(doc, "kind") == "kpi"
        and is_sovereignty(doc)
        and COVERAGE_KPI_RE.match(_str_field(doc, "stable_id")) is not None
    )


def scan(metrics_dir: Path = DEFAULT_METRICS_DIR) -> list[PairingFinding]:
    docs: dict[str, tuple[dict, Path]] = {}
    for path in sorted(metrics_dir.glob("*.yaml")):
        doc = _load_metric(path)
        if not isinstance(doc, dict):
            continue
        sid = _str_field(doc, "stable_id")
        if sid:
            docs[sid] = (doc, path)

    findings: list[PairingFinding] = []
    for sid, (doc, path) in docs.items():
        if not is_coverage_kpi(doc):
            continue
        refs = _residual_refs(doc)
        kpi_ver = _version(sid)

        if not refs:
            is_lm = LM_ENDPOINT_COVERAGE_RE.match(sid) is not None
            findings.append(PairingFinding(
                code=("lm_endpoint_pairing_regressed" if is_lm
                      else "coverage_kpi_without_residual_risk"),
                kpi_stable_id=sid, kpi_path=path,
                detail=(
                    "declares no residual_risk_refs; a coverage ratio without "
                    "a residual-risk counterpart cannot report the exposure "
                    "in the population it could not classify"
                    + (" — this family shipped with the pairing enforced and "
                       "must not regress" if is_lm else "")
                ),
            ))
            continue

        for ref in refs:
            target = docs.get(ref)
            if target is None:
                findings.append(PairingFinding(
                    code="unresolved_residual_risk_ref",
                    kpi_stable_id=sid, kpi_path=path,
                    detail=f"residual_risk_refs names {ref}, which resolves "
                           f"to no metric under {metrics_dir.name}/",
                ))
                continue
            tdoc, _ = target
            if _str_field(tdoc, "kind") != "kri":
                findings.append(PairingFinding(
                    code="residual_risk_ref_not_kri",
                    kpi_stable_id=sid, kpi_path=path,
                    detail=f"{ref} has kind="
                           f"{_str_field(tdoc, 'kind') or '(unset)'}; a "
                           f"residual-risk counterpart must be a kri",
                ))
            if _version(ref) != kpi_ver:
                findings.append(PairingFinding(
                    code="residual_risk_ref_version_mismatch",
                    kpi_stable_id=sid, kpi_path=path,
                    detail=f"{ref} is @v{_version(ref) or '?'} against a KPI "
                           f"at @v{kpi_ver}; the pair would read different "
                           f"population definitions",
                ))
            if not is_sovereignty(tdoc):
                findings.append(PairingFinding(
                    code="residual_risk_ref_property_gap",
                    kpi_stable_id=sid, kpi_path=path,
                    detail=f"{ref} does not declare foundation_property "
                           f"'{SOVEREIGNTY_PROPERTY}'; a per-property audit "
                           f"of the sovereignty cluster would not see the "
                           f"pairing",
                ))
    return sorted(findings, key=lambda f: (f.severity != "HARD", f.code, f.kpi_stable_id))


def partition(findings: list[PairingFinding]) -> tuple[list[PairingFinding], list[PairingFinding]]:
    hard = [f for f in findings if f.severity == "HARD"]
    soft = [f for f in findings if f.severity == "SOFT"]
    return hard, soft


def _emit_text(findings: list[PairingFinding]) -> None:
    hard, soft = partition(findings)
    print(f"{CLI_NAME} — {len(hard)} HARD, {len(soft)} SOFT")
    for f in findings:
        print(f"  {f.as_text()}")
    if not findings:
        print("  OK — every sovereignty coverage KPI declares a resolvable "
              "residual-risk counterpart.")



def _emit_json(findings: list[PairingFinding]) -> None:
    hard, soft = partition(findings)
    print(json.dumps({
        "tool": CLI_NAME,
        "hard": len(hard),
        "soft": len(soft),
        "findings": [f.as_dict() for f in findings],
    }, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description="Assert every sovereignty-cluster coverage KPI declares a "
                    "resolvable residual-risk KRI counterpart.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--metrics-dir", type=Path, default=DEFAULT_METRICS_DIR,
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    findings = scan(args.metrics_dir)
    (_emit_json if args.format == "json" else _emit_text)(findings)

    hard, _ = partition(findings)
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
