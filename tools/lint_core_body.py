"""CORE primitive-binding resolution linter.

``content-model/playbook.schema.json`` says of ``x_secops_ng.core_body``:

    Resolution against the primitives contract is enforced by the
    linter, not the schema.

No such linter existed. This is it.

A ``core_body`` block declares the deterministic primitive a step compiles
to, and the compilers turn it directly into source: the Temporal emitter
renders ``from <module> import <callable>`` followed by
``<out> = <callable>(<arg>=<expr>, ...)``. Nothing verified that the
module imported, that the callable existed, or that the argument names
were real parameters — so a typo in a dotted path shipped as an
``ImportError`` inside committed worked examples, which is exactly what
happened to ``alert_triage`` (8 bindings) and ``vuln_intake`` (2).

## Two severities, on purpose

**HARD** findings fail the build. Each is a defect with no judgement
attached — the binding cannot execute and there is exactly one correct
answer:

* ``unresolvable_module``  — the dotted module does not import.
* ``missing_callable``     — the module imports; the callable is absent.
* ``unknown_argument``     — an ``in`` key is not a parameter of the
  callable, so the generated call raises ``TypeError``.

**SOFT** findings are reported with a count and do not fail. Each needs a
content decision (usually: declare a new playbook variable, or decide the
value is runtime context the harness injects) and there is no single
mechanical fix:

* ``unbound_required_argument`` — a required parameter has no ``in`` entry.
* ``unknown_in_variable``       — an ``in`` expression names a ``__var__``
  the playbook does not declare.
* ``unknown_out_variable``      — ``out`` names a ``__var__`` the playbook
  does not declare.

Promoting the soft set to hard is the point of the follow-up work; until
those decisions land, failing on them would only mean the guard is
switched off entirely, which is how the hard defects survived.

Usage:

    python -m tools.lint_core_body                # walk default tree
    python tools/lint_core_body.py                # equivalent
    python -m tools.lint_core_body --json         # machine-readable
    python -m tools.lint_core_body --strict       # soft findings fail too
    python -m tools.lint_core_body --root /path   # lints that tree, imports from it

Invocation-independent: the linted ``--root`` is placed on ``sys.path`` so
the dotted ``content.playbooks.*`` primitive paths resolve however the
linter is started. See ``_ensure_importable``.

Exit code is non-zero iff at least one HARD finding is emitted (or any
finding, under ``--strict``).

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

HARD = ("unresolvable_module", "missing_callable", "unknown_argument")
SOFT = ("unbound_required_argument", "unknown_in_variable", "unknown_out_variable")

VAR_RE = re.compile(r"^__[a-z0-9_]+__$")


@dataclass(frozen=True)
class Finding:
    slug: str
    step: str
    code: str
    severity: str
    message: str


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _canonical_source(root: Path, slug: str) -> Path | None:
    """Prefer the dir-level YAML when present — it is the canonical form.

    ``alert_triage`` ships both ``content/playbooks/alert_triage.cacao.yaml``
    and a directory JSON transcode of it. #850 established the YAML as the
    source of truth, so lint that and the transcode inherits the verdict.
    """
    for candidate in (
        root / "content" / "playbooks" / f"{slug}.cacao.yaml",
        root / "content" / "playbooks" / slug / "playbook.cacao.json",
        root / "content" / "playbooks" / slug / "playbook.cacao.yaml",
    ):
        if candidate.is_file():
            return candidate
    return None


def _check_binding(
    slug: str, step_name: str, core_body: dict, declared: set[str]
) -> list[Finding]:
    out: list[Finding] = []

    def hard(code: str, msg: str) -> None:
        out.append(Finding(slug, step_name, code, "HARD", msg))

    def soft(code: str, msg: str) -> None:
        out.append(Finding(slug, step_name, code, "SOFT", msg))

    dotted = core_body.get("primitive") or ""
    module_path, _, callable_name = dotted.rpartition(".")
    in_map = core_body.get("in") or {}

    fn = None
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # ImportError and anything raised at import time
        hard(
            "unresolvable_module",
            f"{dotted}: module {module_path!r} does not import "
            f"({type(exc).__name__}). The compilers emit this path verbatim, "
            f"so the generated code will not load.",
        )
    else:
        fn = getattr(module, callable_name, None)
        if fn is None:
            hard(
                "missing_callable",
                f"{dotted}: module imports but has no attribute "
                f"{callable_name!r}.",
            )

    if fn is not None:
        signature = inspect.signature(fn)
        params = set(signature.parameters)
        required = {
            name
            for name, p in signature.parameters.items()
            if p.default is inspect.Parameter.empty
            and p.kind
            not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        }
        unknown = sorted(set(in_map) - params)
        if unknown:
            hard(
                "unknown_argument",
                f"{dotted}: `in` names {unknown} which are not parameters; "
                f"the generated call would raise TypeError.",
            )
        unbound = sorted(required - set(in_map))
        if unbound:
            soft(
                "unbound_required_argument",
                f"{dotted}: {len(unbound)} required parameter(s) unbound "
                f"{unbound}.",
            )

    for key, expr in in_map.items():
        if isinstance(expr, str) and VAR_RE.match(expr) and expr not in declared:
            soft(
                "unknown_in_variable",
                f"{dotted}: `in.{key}` references {expr} which the playbook "
                f"does not declare in playbook_variables.",
            )

    target = core_body.get("out")
    if isinstance(target, str) and VAR_RE.match(target) and target not in declared:
        soft(
            "unknown_out_variable",
            f"{dotted}: `out` writes {target} which the playbook does not "
            f"declare in playbook_variables.",
        )

    return out


def _ensure_importable(root: Path) -> None:
    """Put ``root`` on ``sys.path`` so ``content.playbooks.*`` resolves.

    Primitive paths are dotted from the repo root (``content.playbooks.<slug>
    .primitives.<mod>``), so resolving them requires the linted tree itself on
    the import path. Without this the linter is invocation-sensitive: it works
    under ``python -m tools.lint_core_body`` from the repo root, because that
    puts the working directory on ``sys.path``, and reports *every* binding as
    ``unresolvable_module`` when run as ``python tools/lint_core_body.py``,
    from another directory, or against a ``--root`` that is not the cwd.

    That is a false-positive mode worth naming: 46 spurious HARD findings
    invite someone to "fix" content that was never broken. Tying the import
    root to ``--root`` also makes that flag mean what it says.
    """
    resolved = str(root.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def check(root: Path) -> tuple[list[Finding], dict]:
    _ensure_importable(root)
    findings: list[Finding] = []
    bindings = 0
    slugs = sorted(
        p.name
        for p in (root / "content" / "playbooks").iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )
    for slug in slugs:
        source = _canonical_source(root, slug)
        if source is None:
            continue
        playbook = _load(source)
        declared = set(playbook.get("playbook_variables") or {})
        for step in (playbook.get("workflow") or {}).values():
            if not isinstance(step, dict):
                continue
            core_body = (step.get("x_secops_ng") or {}).get("core_body")
            if not isinstance(core_body, dict) or not core_body.get("primitive"):
                continue
            bindings += 1
            findings.extend(
                _check_binding(slug, step.get("name") or "?", core_body, declared)
            )
    summary = {
        "playbooks": len(slugs),
        "bindings": bindings,
        "hard": sum(1 for f in findings if f.severity == "HARD"),
        "soft": sum(1 for f in findings if f.severity == "SOFT"),
        "by_code": {
            code: sum(1 for f in findings if f.code == code) for code in HARD + SOFT
        },
    }
    return findings, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--strict", action="store_true", help="SOFT findings also fail the run"
    )
    args = ap.parse_args(argv)

    findings, summary = check(Path(args.root))

    if args.json:
        json.dump(
            {"summary": summary, "findings": [asdict(f) for f in findings]},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        for f in sorted(findings, key=lambda x: (x.severity != "HARD", x.slug, x.code)):
            print(f"{f.severity:5} {f.slug}/{f.step}  [{f.code}]  {f.message}")
        print(
            f"\ncore-body linter: {summary['bindings']} binding(s) across "
            f"{summary['playbooks']} playbook(s) — "
            f"{summary['hard']} hard, {summary['soft']} soft"
        )
        if not summary["hard"]:
            print("HARD findings: none — every binding imports and its arguments are real.")

    failing = summary["hard"] + (summary["soft"] if args.strict else 0)
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
