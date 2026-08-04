"""Playbook-layer OCSF telemetry-reference resolution linter.

``tools/lint_catalogue_ocsf_bindings.py`` guards the metrics layer: every
operator-telemetry metric must declare a ``telemetry.ocsf.*`` ref and that ref
must resolve under ``content/telemetry/``. It deliberately does not walk
playbooks, so the two playbook-side layers were unguarded:

* ``x_secops_ng.telemetry_refs`` on the playbook and on each step;
* ``id`` on each ``ocsf[]`` entry of the outbound ``mappings.yaml`` overlay.

Both were left to drift. Before #873 the overlay layer alone carried 70
unresolved refs out of 91, because 63 of them spelled the class without the
``ocsf`` segment — ``telemetry.api_activity@v1`` where the committed artifact
is ``telemetry.ocsf.api_activity@v1``. The metrics guard caught this only when
a contributor copied the bare spelling out of an overlay and into a metric,
which is exactly how it was found.

## Two finding codes, both HARD

* ``bare_ocsf_ref`` — the ref omits the ``ocsf`` segment while the namespaced
  form has a committed artifact. Purely a spelling regression on the
  normalisation done in #873.
* ``undefined_telemetry_class`` — the ref names a class with no artifact under
  either spelling. Every ref must resolve to a committed artifact under
  ``content/telemetry/``; assert a new class by authoring its artifact in the
  same change.

``undefined_telemetry_class`` started as a SOFT count with a pinned ceiling:
36 refs named classes the catalogue did not ship, and failing on them would
have meant a guard that was red until all that content landed. #875 closed
all 36 — four artifacts authored against the verified OCSF 1.4.0 class list,
the rest rebound to classes that exist — and promoted the code to HARD, as
that issue's sequencing prescribed. The SOFT tuple is kept (empty) so the
severity partition stays explicit.

Usage:

    python -m tools.lint_playbook_telemetry_refs
    python tools/lint_playbook_telemetry_refs.py
    python -m tools.lint_playbook_telemetry_refs --json
    python -m tools.lint_playbook_telemetry_refs --strict   # soft fails too
    python -m tools.lint_playbook_telemetry_refs --root /path

Exit code is non-zero iff a HARD finding is emitted (or any, under
``--strict``; vestigial now that every code is HARD, kept for interface
stability).

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

HARD = ("bare_ocsf_ref", "undefined_telemetry_class")
SOFT = ()

TELEMETRY_RE = re.compile(r"^telemetry\.(?P<rest>[a-z][a-z0-9_.]*)@v\d+(?:\.\d+){0,2}$")


@dataclass(frozen=True)
class Finding:
    slug: str
    where: str
    ref: str
    code: str
    severity: str
    message: str


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _canonical_playbook(root: Path, slug: str) -> Path | None:
    """Dir-level YAML wins where present — #850 made it the canonical form."""
    for c in (
        root / "content" / "playbooks" / f"{slug}.cacao.yaml",
        root / "content" / "playbooks" / slug / "playbook.cacao.json",
        root / "content" / "playbooks" / slug / "playbook.cacao.yaml",
    ):
        if c.is_file():
            return c
    return None


def _classify(slug: str, where: str, ref: str, have: set[str]) -> Finding | None:
    if not TELEMETRY_RE.match(ref) or ref in have:
        return None
    namespaced = (
        ref if ref.startswith("telemetry.ocsf.") else ref.replace("telemetry.", "telemetry.ocsf.", 1)
    )
    if namespaced in have:
        return Finding(
            slug,
            where,
            ref,
            "bare_ocsf_ref",
            "HARD",
            f"{ref} omits the `ocsf` segment; the committed artifact is "
            f"{namespaced}. Normalise the spelling.",
        )
    return Finding(
        slug,
        where,
        ref,
        "undefined_telemetry_class",
        "HARD",
        f"{ref} names a class with no artifact under content/telemetry/ in "
        f"either spelling. Author the artifact (against the upstream OCSF "
        f"class list) or drop the claim.",
    )


def check(root: Path) -> tuple[list[Finding], dict]:
    have = {p.name.replace(".json", "") for p in (root / "content" / "telemetry").glob("*.json")}
    findings: list[Finding] = []
    refs = 0

    playbook_dir = root / "content" / "playbooks"
    slugs = sorted(p.name for p in playbook_dir.iterdir() if p.is_dir() and not p.name.startswith("_"))

    for slug in slugs:
        source = _canonical_playbook(root, slug)
        if source is not None:
            doc = _load(source)
            for ref in (doc.get("x_secops_ng") or {}).get("telemetry_refs") or []:
                refs += 1
                if f := _classify(slug, "playbook.telemetry_refs", ref, have):
                    findings.append(f)
            for step in (doc.get("workflow") or {}).values():
                if not isinstance(step, dict):
                    continue
                name = step.get("name") or "?"
                for ref in (step.get("x_secops_ng") or {}).get("telemetry_refs") or []:
                    refs += 1
                    if f := _classify(slug, f"step:{name}", ref, have):
                        findings.append(f)

        overlay = playbook_dir / slug / "mappings.yaml"
        if overlay.is_file():
            for entry in (_load(overlay).get("ocsf") or []):
                if not isinstance(entry, dict):
                    continue
                ref = entry.get("id")
                if not isinstance(ref, str):
                    continue
                refs += 1
                if f := _classify(slug, "overlay.ocsf[].id", ref, have):
                    findings.append(f)

    summary = {
        "playbooks": len(slugs),
        "telemetry_artifacts": len(have),
        "refs": refs,
        "hard": sum(1 for f in findings if f.severity == "HARD"),
        "soft": sum(1 for f in findings if f.severity == "SOFT"),
        "by_code": {c: sum(1 for f in findings if f.code == c) for c in HARD + SOFT},
    }
    return findings, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="SOFT findings also fail")
    args = ap.parse_args(argv)

    findings, summary = check(Path(args.root))

    if args.json:
        json.dump({"summary": summary, "findings": [asdict(f) for f in findings]}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for f in sorted(findings, key=lambda x: (x.severity != "HARD", x.slug, x.where)):
            print(f"{f.severity:5} {f.slug}/{f.where}  [{f.code}]  {f.message}")
        print(
            f"\nplaybook-telemetry-refs: {summary['refs']} ref(s) across "
            f"{summary['playbooks']} playbook(s) against "
            f"{summary['telemetry_artifacts']} artifact(s) — "
            f"{summary['hard']} hard, {summary['soft']} soft"
        )
        if not summary["hard"]:
            print(
                "HARD findings: none — every ref uses the namespaced OCSF "
                "spelling and resolves to a committed artifact."
            )

    return 1 if summary["hard"] + (summary["soft"] if args.strict else 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
