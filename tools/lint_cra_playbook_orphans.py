"""CRA orphan-CI assertion — defends the G-02 KRI for CRA coverage.

Walks `content/playbooks/` and `content/mappings/cra/` and reports any
finalized playbook (one carrying ``playbook.cacao.json`` or
``playbook.cacao.yaml``) that does not appear in any inbound
``playbook_refs:`` list under a CRA mapping YAML.

Two firing modes:

* **Hard fail (immediate).** A playbook that was previously mapped
  loses its only inbound CRA citation in the current diff — the
  remediation MUST land in the same PR. The assertion checks the
  index against ``--baseline-ref`` (default ``origin/main``) when the
  pointer resolves; if it does not (e.g. shallow checkout, first run),
  the check falls back to "current tree only" and the regression lane
  is a no-op.

* **Grace-period fail (7-day soft).** A playbook with no inbound
  citation at all trips when its CACAO finalization marker is older
  than 7 days. New playbooks under the grace window are tolerated so
  the CORE per-edge cards can land in their own PRs without forcing
  the EXTEND mapping into the same change.

Slugs listed in ``content/mappings/cra/_orphan_skip.yaml`` are
deliberate, audited exclusions and never trip either lane. The skip
manifest itself is sanity-checked (every listed slug must point at a
finalized playbook directory).

Output formats:

* ``--format text`` (default): one line per finding, exit non-zero
  iff any HIGH finding fired.
* ``--format json``: machine-readable for the dashboard ingest.
* ``--format kri``: G-02 KRI emission shape — a single JSON object
  with ``kri_id``, ``status`` (``ok|degraded|tripped``), a
  ``coverage`` summary, and a ``findings`` list. Exit code is the
  same as ``text``.

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

PLAYBOOKS_RELPATH = Path("content") / "playbooks"
CRA_RELPATH = Path("content") / "mappings" / "cra"

CACAO_FILENAMES = ("playbook.cacao.json", "playbook.cacao.yaml")
SKIP_FILENAME = "_orphan_skip.yaml"

# Inbound citation lines look like ``- playbook.<slug>@v<n>`` under a
# ``playbook_refs:`` list. We match the slug between ``playbook.`` and
# the first non-identifier character so the linter does not depend on
# version pinning conventions.
PLAYBOOK_REF_RE = re.compile(
    r"^\s*-\s*playbook\.([A-Za-z0-9_]+)(?:@[A-Za-z0-9_.\-]+)?\s*$"
)

# Default grace window for net-new playbooks without any inbound CRA
# citation. The spec is "within 7 days"; we read seconds-since-mtime
# of the CACAO finalization marker.
GRACE_DAYS_DEFAULT = 7

# G-02 KRI tag — re-used in the test suite and dashboard ingest.
KRI_ID = "G-02"
KRI_NAME = "regulatory-mapping-coverage-cra"


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    slug: str
    code: str  # ORPHAN_NEW | ORPHAN_REGRESSION | SKIP_INVALID
    severity: str  # HIGH | LOW
    message: str
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "detail": dict(self.detail),
        }

    def format_text(self) -> str:
        return f"[{self.severity}] [{self.code}] {self.slug}: {self.message}"


# ---------------------------------------------------------------------------
# Filesystem walk
# ---------------------------------------------------------------------------


def _finalized_slugs(root: Path) -> dict[str, Path]:
    """Map ``slug -> path-to-CACAO-marker`` for every finalized playbook."""
    out: dict[str, Path] = {}
    base = root / PLAYBOOKS_RELPATH
    if not base.is_dir():
        return out
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        for fname in CACAO_FILENAMES:
            marker = d / fname
            if marker.is_file():
                out[d.name] = marker
                break
    return out


def _cra_inbound_slugs(root: Path) -> set[str]:
    """Return the set of slugs that appear inside any ``playbook_refs:``
    block under a CRA mapping YAML. Parser is regex-only on purpose:
    the YAML files are hand-curated and the linter must keep running
    when one of them is mid-edit and not yet parseable.
    """
    out: set[str] = set()
    base = root / CRA_RELPATH
    if not base.is_dir():
        return out
    for yml in sorted(base.glob("*.yaml")):
        if yml.name.startswith("_"):
            continue
        in_block = False
        try:
            text = yml.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("playbook_refs:"):
                in_block = True
                # inline ``playbook_refs: []`` closes the block
                if "[]" in stripped:
                    in_block = False
                continue
            if not in_block:
                continue
            if not stripped or stripped.startswith("#"):
                continue
            m = PLAYBOOK_REF_RE.match(line)
            if m:
                out.add(m.group(1))
                continue
            # any other content (next key, blank, dedent) closes the
            # block — keep the parser conservative.
            if not line.startswith((" ", "\t")):
                in_block = False
                continue
            if stripped and not stripped.startswith("-"):
                in_block = False
    return out


def _load_skip_manifest(root: Path) -> tuple[set[str], list[Finding]]:
    """Read ``_orphan_skip.yaml`` and return (allowed-slugs, findings).

    A malformed manifest is a HIGH SKIP_INVALID finding so the
    assertion fails loudly rather than silently widening coverage.
    """
    path = root / CRA_RELPATH / SKIP_FILENAME
    if not path.is_file():
        return set(), []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return set(), [
            Finding(
                slug=str(path.relative_to(root)),
                code="SKIP_INVALID",
                severity="HIGH",
                message=f"skip manifest is not valid YAML: {exc}",
            )
        ]
    entries = raw.get("skip") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        return set(), [
            Finding(
                slug=str(path.relative_to(root)),
                code="SKIP_INVALID",
                severity="HIGH",
                message="skip manifest is missing a top-level 'skip:' list",
            )
        ]
    finalized = _finalized_slugs(root)
    allowed: set[str] = set()
    findings: list[Finding] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            findings.append(
                Finding(
                    slug=f"_orphan_skip[{i}]",
                    code="SKIP_INVALID",
                    severity="HIGH",
                    message="skip entry must be a mapping with 'slug' and 'rationale'",
                )
            )
            continue
        slug = entry.get("slug")
        rationale = entry.get("rationale")
        if not isinstance(slug, str) or not slug:
            findings.append(
                Finding(
                    slug=f"_orphan_skip[{i}]",
                    code="SKIP_INVALID",
                    severity="HIGH",
                    message="skip entry missing 'slug'",
                )
            )
            continue
        if not isinstance(rationale, str) or not rationale.strip():
            findings.append(
                Finding(
                    slug=slug,
                    code="SKIP_INVALID",
                    severity="HIGH",
                    message="skip entry missing 'rationale'",
                )
            )
            continue
        if slug not in finalized:
            findings.append(
                Finding(
                    slug=slug,
                    code="SKIP_INVALID",
                    severity="HIGH",
                    message=(
                        "skip entry points at a slug with no finalized "
                        "playbook under content/playbooks/"
                    ),
                )
            )
            continue
        allowed.add(slug)
    return allowed, findings


# ---------------------------------------------------------------------------
# Baseline / regression lane
# ---------------------------------------------------------------------------


def _baseline_inbound_slugs(root: Path, ref: str) -> set[str] | None:
    """Return the inbound slug set as of ``ref`` in git, or None if the
    ref does not resolve (shallow checkout, first commit, etc.).
    """
    try:
        rev = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", ref + "^{commit}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    try:
        listing = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-r", "--name-only", rev,
             str(CRA_RELPATH)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except subprocess.CalledProcessError:
        return None
    out: set[str] = set()
    for relpath in listing:
        if not relpath.endswith(".yaml"):
            continue
        if Path(relpath).name.startswith("_"):
            continue
        try:
            blob = subprocess.run(
                ["git", "-C", str(root), "show", f"{rev}:{relpath}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except subprocess.CalledProcessError:
            continue
        in_block = False
        for line in blob.splitlines():
            stripped = line.strip()
            if stripped.startswith("playbook_refs:"):
                in_block = True
                if "[]" in stripped:
                    in_block = False
                continue
            if not in_block:
                continue
            if not stripped or stripped.startswith("#"):
                continue
            m = PLAYBOOK_REF_RE.match(line)
            if m:
                out.add(m.group(1))
                continue
            if not line.startswith((" ", "\t")) or (
                stripped and not stripped.startswith("-")
            ):
                in_block = False
    return out


# ---------------------------------------------------------------------------
# Grace window
# ---------------------------------------------------------------------------


def _marker_age_days(marker: Path, now: _dt.datetime) -> float:
    """Age of a CACAO marker file in days. Uses mtime — the file's
    landing time is the project's clock for the grace window."""
    mtime = _dt.datetime.fromtimestamp(marker.stat().st_mtime, tz=_dt.timezone.utc)
    delta = now - mtime
    return delta.total_seconds() / 86400.0


# ---------------------------------------------------------------------------
# Top-level check
# ---------------------------------------------------------------------------


def check(
    root: Path,
    *,
    baseline_ref: str | None,
    grace_days: int,
    now: _dt.datetime | None = None,
) -> tuple[list[Finding], dict]:
    now = now or _dt.datetime.now(tz=_dt.timezone.utc)

    finalized = _finalized_slugs(root)
    inbound = _cra_inbound_slugs(root)
    allowed, skip_findings = _load_skip_manifest(root)

    findings: list[Finding] = list(skip_findings)

    baseline_inbound: set[str] | None = None
    if baseline_ref:
        baseline_inbound = _baseline_inbound_slugs(root, baseline_ref)

    mapped: list[str] = []
    orphans: list[str] = []
    grace: list[dict] = []
    skipped: list[str] = []

    for slug, marker in finalized.items():
        if slug in allowed:
            skipped.append(slug)
            continue
        if slug in inbound:
            mapped.append(slug)
            continue
        # Orphan. Check regression vs baseline first — that lane is
        # immediate-fail and ignores the grace window.
        if baseline_inbound is not None and slug in baseline_inbound:
            findings.append(
                Finding(
                    slug=slug,
                    code="ORPHAN_REGRESSION",
                    severity="HIGH",
                    message=(
                        "previously had an inbound CRA citation; the current "
                        "diff drops it back to orphan status — restore the "
                        "edge or add an audited entry to "
                        "content/mappings/cra/_orphan_skip.yaml in the same PR"
                    ),
                    detail={"baseline_ref": baseline_ref or ""},
                )
            )
            continue
        # Net-new orphan: tolerate up to grace_days from CACAO landing.
        age = _marker_age_days(marker, now)
        if age <= grace_days:
            grace.append({"slug": slug, "age_days": round(age, 2)})
            continue
        findings.append(
            Finding(
                slug=slug,
                code="ORPHAN_NEW",
                severity="HIGH",
                message=(
                    f"finalized playbook has no inbound CRA citation and is "
                    f"{age:.1f} days past the {grace_days}-day grace window; "
                    "add a per-clause yaml under content/mappings/cra/ that "
                    "lists playbook." + slug + "@v1 under playbook_refs:"
                ),
                detail={"age_days": round(age, 2), "grace_days": grace_days},
            )
        )
        orphans.append(slug)

    summary = {
        "finalized": len(finalized),
        "mapped": len(mapped),
        "orphans": len(orphans),
        "grace_window": grace,
        "skipped": skipped,
        "baseline_ref": baseline_ref or None,
        "baseline_resolved": baseline_inbound is not None,
        "grace_days": grace_days,
    }
    return findings, summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_text(findings: Iterable[Finding], summary: dict, stream) -> None:
    findings = list(findings)
    if findings:
        for f in findings:
            print(f.format_text(), file=stream)
    print(
        f"CRA orphan-CI: finalized={summary['finalized']} "
        f"mapped={summary['mapped']} "
        f"orphans={summary['orphans']} "
        f"grace={len(summary['grace_window'])} "
        f"skipped={len(summary['skipped'])}",
        file=stream,
    )


def _print_json(findings: Iterable[Finding], summary: dict, stream) -> None:
    json.dump(
        {"findings": [f.to_dict() for f in findings], "summary": summary},
        stream,
        indent=2,
        sort_keys=True,
    )
    stream.write("\n")


def _print_kri(
    findings: Iterable[Finding], summary: dict, stream
) -> None:
    """G-02 KRI emission. Shape:

        {
          "kri_id": "G-02",
          "kri_name": "regulatory-mapping-coverage-cra",
          "regime": "cra",
          "status": "ok | degraded | tripped",
          "coverage": {finalized, mapped, orphans, grace_window, skipped},
          "findings": [...],
          "emitted_at": "<iso8601>"
        }

    ``status`` is ``tripped`` if any HIGH finding fired, ``degraded``
    if any playbook is inside the grace window, ``ok`` otherwise.
    """
    findings = list(findings)
    high = any(f.severity == "HIGH" for f in findings)
    in_grace = bool(summary.get("grace_window"))
    status = "tripped" if high else ("degraded" if in_grace else "ok")
    emission = {
        "kri_id": KRI_ID,
        "kri_name": KRI_NAME,
        "regime": "cra",
        "status": status,
        "coverage": {
            "finalized": summary["finalized"],
            "mapped": summary["mapped"],
            "orphans": summary["orphans"],
            "grace_window": summary["grace_window"],
            "skipped": summary["skipped"],
        },
        "findings": [f.to_dict() for f in findings],
        "baseline_ref": summary.get("baseline_ref"),
        "baseline_resolved": summary.get("baseline_resolved", False),
        "grace_days": summary.get("grace_days"),
        "emitted_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
    }
    json.dump(emission, stream, indent=2, sort_keys=True)
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="tools.lint_cra_playbook_orphans",
        description=(
            "G-02 KRI assertion: every finalized playbook under "
            "content/playbooks/ must carry an inbound playbook_refs: "
            "citation under content/mappings/cra/ (or appear in the "
            "audited _orphan_skip.yaml manifest)."
        ),
    )
    ap.add_argument(
        "--root",
        default=str(DEFAULT_ROOT),
        help="repository root (default: this file's parent)",
    )
    ap.add_argument(
        "--baseline-ref",
        default=os.environ.get("CRA_ORPHAN_BASELINE_REF", "origin/main"),
        help=(
            "git ref to diff against for the regression lane (default: "
            "origin/main, override via CRA_ORPHAN_BASELINE_REF). "
            "Pass an empty string to disable the regression lane."
        ),
    )
    ap.add_argument(
        "--grace-days",
        type=int,
        default=GRACE_DAYS_DEFAULT,
        help=f"net-new orphan grace window in days (default: {GRACE_DAYS_DEFAULT})",
    )
    ap.add_argument(
        "--format",
        choices=("text", "json", "kri"),
        default="text",
    )
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    baseline = args.baseline_ref or None

    findings, summary = check(
        root,
        baseline_ref=baseline,
        grace_days=args.grace_days,
    )

    if args.format == "json":
        _print_json(findings, summary, sys.stdout)
    elif args.format == "kri":
        _print_kri(findings, summary, sys.stdout)
    else:
        _print_text(findings, summary, sys.stdout)

    return 1 if any(f.severity == "HIGH" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
