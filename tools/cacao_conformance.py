"""Validate every canonical playbook against the official OASIS CACAO 2.0 schemas.

The framework publishes its playbooks as CACAO v2 documents. This tool checks
that claim against the JSON Schema files the OASIS CACAO Technical Committee
publishes (vendored, unmodified, under ``schemas/vendor/cacao-2.0/``), and
turns the result into a ratchet: a committed baseline records the error count
per document, CI fails when any document gets worse, and an improvement has
to be recorded by re-writing the baseline in the same pull request.

Usage
-----

    python -m tools.cacao_conformance                       # report
    python -m tools.cacao_conformance --show 5              # report + first 5 errors per document
    python -m tools.cacao_conformance --baseline tests/content/cacao_conformance_baseline.json
    python -m tools.cacao_conformance --write-baseline tests/content/cacao_conformance_baseline.json
    python -m tools.cacao_conformance --dialect 2020-12     # stricter reading, see below
    python -m tools.cacao_conformance --json                # machine-readable report on stdout

Dialects
--------

The upstream schema files declare JSON Schema Draft-07 but also use the
``unevaluatedProperties`` keyword, which Draft-07 validators ignore. The
default (``--dialect declared``) validates under Draft-07, which is what the
files say they are and what downstream CACAO tooling applies. ``--dialect
2020-12`` evaluates the root ``playbook.json`` under the newer dialect, so the
root-level ``unevaluatedProperties: false`` is enforced and non-standard
top-level properties are reported; the referenced files keep their declared
dialect so step-type dispatch is unchanged. It reports a superset of the
declared reading and is informational.

Exit codes
----------

    0   no errors (without a baseline) or exactly the baselined error counts
    1   errors found (without a baseline), a regression, or a stale baseline
    2   usage or environment problem (missing schemas, unreadable playbook)

Standard library plus ``jsonschema`` (with ``referencing``) and ``PyYAML``,
all of which the ``[dev]`` extra already installs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "schemas" / "vendor" / "cacao-2.0" / "schemas"
PLAYBOOK_ROOT = REPO_ROOT / "content" / "playbooks"
DEFAULT_BASELINE = REPO_ROOT / "tests" / "content" / "cacao_conformance_baseline.json"

# The upstream ``$id`` values point at the ``main`` branch of the OASIS repo.
# Older copies referenced ``master``; register both so relative ``$ref``s
# resolve whichever spelling a schema file carries.
_ID_PREFIXES = (
    "https://raw.githubusercontent.com/oasis-open/cacao-json-schemas/main/schemas/",
    "https://raw.githubusercontent.com/oasis-open/cacao-json-schemas/master/schemas/",
)

DIALECTS = ("declared", "2020-12")


# --------------------------------------------------------------------------- #
# Discovery                                                                   #
# --------------------------------------------------------------------------- #

def discover_playbooks(root: Path = PLAYBOOK_ROOT) -> list[Path]:
    """Every canonical playbook document, across the source layouts in use.

    * ``content/playbooks/<slug>/playbook.cacao.json`` (canonical JSON)
    * ``content/playbooks/<slug>/*.cacao.yaml``          (YAML-authored)
    * ``content/playbooks/<slug>.cacao.yaml``            (flat YAML)

    The ``_template`` scaffold is excluded: it carries ``TODO_`` markers by
    design and has its own conformance lane.
    """
    found: set[Path] = set()
    found.update(root.glob("*/playbook.cacao.json"))
    found.update(root.glob("*/*.cacao.yaml"))
    found.update(root.glob("*.cacao.yaml"))
    return sorted(p for p in found if "_template" not in p.parts and not p.name.startswith("_template"))


def load_document(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


# --------------------------------------------------------------------------- #
# Validator                                                                   #
# --------------------------------------------------------------------------- #

def build_validator(dialect: str = "declared", schema_root: Path = SCHEMA_ROOT):
    """Compile the vendored schema set into a single validator for ``playbook.json``."""
    if dialect not in DIALECTS:
        raise ValueError(f"dialect must be one of {DIALECTS}, got {dialect!r}")
    if not (schema_root / "playbook.json").is_file():
        raise FileNotFoundError(
            f"official CACAO schemas not found under {schema_root}; "
            "see schemas/vendor/cacao-2.0/README.md"
        )
    # Referenced files always keep the dialect they declare (Draft-07); only
    # the root validator changes with ``dialect``. Forcing 2020-12 onto the
    # referenced files changes how ``$ref`` siblings are evaluated and makes
    # step-type dispatch silently skip the per-type schemas.
    registry = Registry()
    for path in sorted(schema_root.rglob("*.json")):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents, default_specification=DRAFT7)
        rel = path.relative_to(schema_root).as_posix()
        for prefix in _ID_PREFIXES:
            registry = registry.with_resource(prefix + rel, resource)
        if "$id" in contents:
            registry = registry.with_resource(contents["$id"], resource)
    root_schema = json.loads((schema_root / "playbook.json").read_text(encoding="utf-8"))
    cls = Draft7Validator if dialect == "declared" else Draft202012Validator
    return cls(root_schema, registry=registry)


# --------------------------------------------------------------------------- #
# Reporting                                                                   #
# --------------------------------------------------------------------------- #

def classify(error: ValidationError) -> str:
    """A short, stable label for an error so counts can be compared across runs."""
    path = [str(p) for p in error.absolute_path]
    leaf = path[-1] if path else "<root>"
    message = error.message
    if "is a required property" in message:
        return "required:" + message.split("'")[1]
    if "is not one of" in message:
        return "enum:" + leaf
    if "is not of type" in message:
        return "type:" + leaf
    if "is not valid under any of the given schemas" in message:
        return "anyOf:" + (path[-2] if len(path) >= 2 else leaf)
    if "Unevaluated properties" in message or "Additional properties" in message:
        names = re.findall(r"'([^']+)'", message)
        return "extra-property:" + (",".join(names) if names else leaf)
    if "does not match" in message:
        return "pattern:" + leaf
    return "other:" + message[:60]


@dataclass
class DocumentResult:
    path: str
    errors: int
    kinds: Counter = field(default_factory=Counter)
    samples: list[str] = field(default_factory=list)


@dataclass
class Report:
    dialect: str
    documents: list[DocumentResult]

    @property
    def total_errors(self) -> int:
        return sum(d.errors for d in self.documents)

    @property
    def failing(self) -> int:
        return sum(1 for d in self.documents if d.errors)

    def kinds(self) -> Counter:
        total: Counter = Counter()
        for d in self.documents:
            total.update(d.kinds)
        return total

    def to_json(self) -> dict[str, Any]:
        return {
            "dialect": self.dialect,
            "documents": {
                d.path: {"errors": d.errors, "kinds": dict(sorted(d.kinds.items()))}
                for d in self.documents
            },
            "totals": {
                "documents": len(self.documents),
                "failing": self.failing,
                "errors": self.total_errors,
                "kinds": dict(self.kinds().most_common()),
            },
        }


def run(dialect: str = "declared", *, samples: int = 0, repo_root: Path = REPO_ROOT) -> Report:
    validator = build_validator(dialect, repo_root / "schemas" / "vendor" / "cacao-2.0" / "schemas")
    results: list[DocumentResult] = []
    for path in discover_playbooks(repo_root / "content" / "playbooks"):
        document = load_document(path)
        errors = sorted(validator.iter_errors(document), key=lambda e: (list(map(str, e.absolute_path)), e.message))
        result = DocumentResult(path=path.relative_to(repo_root).as_posix(), errors=len(errors))
        for error in errors:
            result.kinds[classify(error)] += 1
        for error in errors[:samples]:
            where = "/".join(str(p) for p in error.absolute_path) or "<root>"
            result.samples.append(f"{where}: {error.message[:140]}")
        results.append(result)
    return Report(dialect=dialect, documents=results)


# --------------------------------------------------------------------------- #
# Baseline                                                                    #
# --------------------------------------------------------------------------- #

def baseline_from(report: Report) -> dict[str, Any]:
    return {
        "dialect": report.dialect,
        "documents": {d.path: d.errors for d in report.documents},
    }


def compare(report: Report, baseline: dict[str, Any]) -> list[str]:
    """Return human-readable problems; empty means the report matches the baseline exactly.

    Regressions and improvements are both reported. An improvement is a
    problem on purpose: the baseline is a ratchet, and a pull request that
    fixes conformance records the new floor by re-writing the baseline.
    """
    problems: list[str] = []
    if baseline.get("dialect") != report.dialect:
        problems.append(
            f"baseline was written for dialect {baseline.get('dialect')!r}, report is {report.dialect!r}"
        )
    expected: dict[str, int] = dict(baseline.get("documents", {}))
    seen: set[str] = set()
    for d in report.documents:
        seen.add(d.path)
        if d.path not in expected:
            if d.errors:
                problems.append(f"new document with {d.errors} error(s), not in baseline: {d.path}")
            continue
        if d.errors > expected[d.path]:
            problems.append(f"regression: {d.path} has {d.errors} error(s), baseline {expected[d.path]}")
        elif d.errors < expected[d.path]:
            problems.append(f"improved: {d.path} has {d.errors} error(s), baseline {expected[d.path]} (re-write the baseline)")
    for path in sorted(set(expected) - seen):
        problems.append(f"baselined document no longer exists: {path} (re-write the baseline)")
    return problems


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #

def _print_report(report: Report, *, show: int) -> None:
    width = max((len(d.path) for d in report.documents), default=20)
    print(f"CACAO 2.0 official-schema conformance (dialect: {report.dialect})")
    print(f"{'document':{width}}  errors")
    for d in report.documents:
        print(f"{d.path:{width}}  {d.errors}")
        for line in d.samples[:show]:
            print(f"    - {line}")
    print()
    print(f"documents: {len(report.documents)}   failing: {report.failing}   errors: {report.total_errors}")
    if report.total_errors:
        print("error kinds:")
        for kind, n in report.kinds().most_common():
            print(f"  {n:5}  {kind}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.cacao_conformance", description=__doc__.split("\n\n")[0])
    parser.add_argument("--dialect", choices=DIALECTS, default="declared")
    parser.add_argument("--baseline", type=Path, help="compare against this baseline file and fail on any difference")
    parser.add_argument("--write-baseline", type=Path, metavar="PATH", help="write the current counts to PATH and exit 0")
    parser.add_argument("--json", action="store_true", help="print the full report as JSON instead of a table")
    parser.add_argument("--show", type=int, default=0, metavar="N", help="print the first N errors per document")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = run(args.dialect, samples=args.show)
    except (FileNotFoundError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.write_baseline:
        args.write_baseline.write_text(json.dumps(baseline_from(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"baseline written: {args.write_baseline} ({report.failing} failing document(s), {report.total_errors} error(s))")
        return 0

    if args.json:
        print(json.dumps(report.to_json(), indent=2, sort_keys=True))
    else:
        _print_report(report, show=args.show)

    if args.baseline:
        try:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read baseline {args.baseline}: {exc}", file=sys.stderr)
            return 2
        problems = compare(report, baseline)
        if problems:
            print()
            print("baseline check FAILED:")
            for p in problems:
                print(f"  - {p}")
            print()
            print("If the change is intended, record the new floor with:")
            print(f"  python -m tools.cacao_conformance --write-baseline {args.baseline}")
            return 1
        print()
        print("baseline check OK: every document matches its recorded error count")
        return 0

    return 0 if report.total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
