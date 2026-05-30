"""Control cross-reference resolution linter.

Walks every mapping YAML under ``content/mappings/<regime>/`` and asserts
that each ``control_ref`` resolves to a populated cross-reference file
under ``content/controls/`` that conforms to
``content-model/control_xref.schema.json``.

A mapping's ``control_ref`` is considered *resolved* when:

1. ``content/controls/<ref>.yaml`` exists;
2. the file validates against ``control_xref.schema.json``
   (Draft 2020-12);
3. it carries at least one ``oscal_refs`` entry and at least one
   ``d3fend_refs`` entry;
4. ``provenance.source_url`` and ``provenance.captured_at`` are both
   present.

The schema already enforces (2), (3), and (4) at minItems=1 /
required-property level; we re-check them here so the linter's failure
mode names the actual under-population condition rather than emitting
a raw JSON Schema error.

Usage:

    python -m tools.lint_control_xref            # walk default tree
    python -m tools.lint_control_xref --json     # machine-readable
    python -m tools.lint_control_xref --root /path/to/repo

Exit code is non-zero iff at least one finding is emitted.

Pure stdlib + PyYAML + jsonschema. No network.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

#: Repository root resolved from this file's location (``<root>/tools/<file>``).
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_RELPATH = Path("content-model") / "control_xref.schema.json"
CONTROLS_RELPATH = Path("content") / "controls"
MAPPINGS_RELPATH = Path("content") / "mappings"


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """A single resolution failure surfaced by the linter."""

    control_ref: str
    code: str
    message: str
    referenced_from: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "control_ref": self.control_ref,
            "code": self.code,
            "message": self.message,
            "referenced_from": list(self.referenced_from),
        }

    def format(self) -> str:
        head = f"[{self.code}] {self.control_ref}: {self.message}"
        if self.referenced_from:
            refs = "\n    - ".join(self.referenced_from)
            head += f"\n    referenced from:\n    - {refs}"
        return head


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def _collect_mapping_refs(mappings_dir: Path) -> dict[str, list[str]]:
    """Return ``{control_ref: [<mapping/entry coordinates>, ...]}``.

    Walks ``mappings_dir/<regime>/*.yaml`` and indexes every ``control_ref``
    by the entry ids that reference it, so a failure can name where the
    unresolved ref came from.
    """
    refs: dict[str, list[str]] = {}
    for path in sorted(mappings_dir.glob("*/*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise RuntimeError(f"{path}: YAML parse error: {exc}") from exc
        if not isinstance(doc, dict):
            continue
        entries = doc.get("entries") or []
        for entry in entries:
            entry_id = entry.get("id", "<no-id>")
            for ref in entry.get("control_refs") or []:
                refs.setdefault(ref, []).append(
                    f"{path.parent.name}/{path.name}#{entry_id}"
                )
    return refs


def _validate_xref_file(
    control_ref: str,
    path: Path,
    validator: Draft202012Validator,
) -> list[Finding]:
    """Validate one control cross-reference file."""
    findings: list[Finding] = []

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [
            Finding(
                control_ref=control_ref,
                code="yaml_parse_error",
                message=f"{path.name}: YAML parse error: {exc}",
            )
        ]

    if not isinstance(doc, dict):
        return [
            Finding(
                control_ref=control_ref,
                code="not_a_mapping",
                message=f"{path.name}: top-level YAML is not a mapping",
            )
        ]

    schema_errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    for err in schema_errors:
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        findings.append(
            Finding(
                control_ref=control_ref,
                code="schema_violation",
                message=f"{path.name}: schema violation at {loc}: {err.message}",
            )
        )

    # Belt-and-braces semantic checks. These overlap with the schema but
    # produce a clearer failure message for the most common under-population
    # gaps (the conditions the EXTEND scope calls out explicitly).
    if not doc.get("oscal_refs"):
        findings.append(
            Finding(
                control_ref=control_ref,
                code="missing_oscal_refs",
                message=f"{path.name}: requires at least one oscal_refs entry",
            )
        )
    if not doc.get("d3fend_refs"):
        findings.append(
            Finding(
                control_ref=control_ref,
                code="missing_d3fend_refs",
                message=f"{path.name}: requires at least one d3fend_refs entry",
            )
        )

    provenance = doc.get("provenance") or {}
    if not provenance.get("source_url"):
        findings.append(
            Finding(
                control_ref=control_ref,
                code="missing_provenance_source_url",
                message=f"{path.name}: provenance.source_url is required",
            )
        )
    if not provenance.get("captured_at"):
        findings.append(
            Finding(
                control_ref=control_ref,
                code="missing_provenance_captured_at",
                message=f"{path.name}: provenance.captured_at is required",
            )
        )

    return findings


def lint(root: Path | None = None) -> list[Finding]:
    """Run the linter and return all findings.

    Empty list = clean tree. Order is stable: findings are sorted by
    ``(control_ref, code)``.
    """
    base = (root or DEFAULT_ROOT).resolve()
    schema_path = base / SCHEMA_RELPATH
    controls_dir = base / CONTROLS_RELPATH
    mappings_dir = base / MAPPINGS_RELPATH

    if not schema_path.is_file():
        raise FileNotFoundError(f"schema not found at {schema_path}")
    if not controls_dir.is_dir():
        raise FileNotFoundError(f"controls directory not found at {controls_dir}")
    if not mappings_dir.is_dir():
        raise FileNotFoundError(f"mappings directory not found at {mappings_dir}")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    refs = _collect_mapping_refs(mappings_dir)

    findings: list[Finding] = []
    for control_ref in sorted(refs):
        xref_path = controls_dir / f"{control_ref}.yaml"
        if not xref_path.is_file():
            findings.append(
                Finding(
                    control_ref=control_ref,
                    code="missing_xref_file",
                    message=(
                        f"content/controls/{control_ref}.yaml does not exist; "
                        "every control_ref used by content/mappings/ must "
                        "resolve to a populated cross-reference file."
                    ),
                    referenced_from=tuple(refs[control_ref]),
                )
            )
            continue

        file_findings = _validate_xref_file(control_ref, xref_path, validator)
        for f in file_findings:
            findings.append(
                Finding(
                    control_ref=f.control_ref,
                    code=f.code,
                    message=f.message,
                    referenced_from=tuple(refs[control_ref]),
                )
            )

    findings.sort(key=lambda f: (f.control_ref, f.code))
    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m tools.lint_control_xref",
        description=(
            "Assert every content/mappings/*/*.yaml control_ref resolves to a "
            "populated content/controls/<ref>.yaml cross-reference file."
        ),
    )
    p.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: parent of tools/).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as a single JSON document on stdout.",
    )
    return p


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        findings = lint(args.root)
    except FileNotFoundError as exc:
        print(f"lint_control_xref: {exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {
            "ok": not findings,
            "finding_count": len(findings),
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if findings:
            print(
                f"control-xref linter: {len(findings)} finding(s) "
                "— mapping references with unresolved or under-populated "
                "cross-reference files:\n"
            )
            for f in findings:
                print(f.format())
                print()
        else:
            print("control-xref linter: clean")

    return 0 if not findings else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
