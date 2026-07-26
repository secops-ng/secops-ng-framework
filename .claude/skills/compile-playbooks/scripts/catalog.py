#!/usr/bin/env python3
"""Read the CACAO playbook catalog and report what an operator needs to choose.

Emits JSON to stdout. Read-only: touches no file outside the repo checkout and
writes nothing.

Why this exists rather than reading the playbooks by hand: the catalog has two
traps that hand-derivation walks into every time.

  1. Canonical sources come in three layouts, and a
     ``content/playbooks/*/playbook.cacao.json`` glob silently misses two of
     them: ``alert-triage`` is stored as
     ``content/playbooks/alert-triage.cacao.yaml`` (YAML, at directory level),
     and five more keep an in-directory ``<slug>/playbook.cacao.yaml``. All
     three layouts are collected below.
  2. ``codebase-vuln-management`` carries four ``core_body`` blocks shaped
     ``{"placeholder": true, "note": "..."}``. They look like bindings and are
     not; the schema requires ``{primitive, in, out}``. That playbook also fails
     validation outright, so it cannot be compiled by any target.

Both are handled here so the caller never has to remember them.

Usage:
    python .claude/skills/compile-playbooks/scripts/catalog.py            # all
    python .claude/skills/compile-playbooks/scripts/catalog.py --slug alert-triage
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Step types that branch. The n8n emitter records a TODO for each one whose
# CACAO source carries no machine-readable expression — which is currently all
# of them, in every playbook.
# Includes "parallel": the n8n emitter records a note for it too ("n8n parallelism
# is implicit"), so it counts toward remaining operator work like any branch step.
_CONTROL_FLOW = {"if-condition", "switch-condition", "while-condition", "parallel"}

# A core_body block is a real binding only with all three keys. See
# content-model/playbook.schema.json (required: [primitive, in, out],
# additionalProperties: false).
_BINDING_KEYS = ("primitive", "in", "out")


def _repo_root() -> Path:
    """Walk up from this script to the checkout root."""
    # .claude/skills/compile-playbooks/scripts/catalog.py -> up 5
    return Path(__file__).resolve().parents[4]


def _load(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        import yaml  # declared dep (pyyaml>=6.0)

        return yaml.safe_load(text) or {}
    return json.loads(text)


def _is_binding(core_body: Any) -> bool:
    return isinstance(core_body, dict) and all(k in core_body for k in _BINDING_KEYS)


def _core_body(step: dict[str, Any]) -> Any:
    return (step.get("x_secops_ng") or {}).get("core_body")


def _validate(playbook: dict[str, Any], schema_path: Path) -> tuple[bool, int, str]:
    """Validate against the repo's own schema. Returns (ok, error_count, first_error).

    Degrades to ``(True, 0, "unvalidated: ...")`` when jsonschema is missing so a
    missing dep never masquerades as invalid content — the caller's preflight is
    responsible for installing it.
    """
    try:
        import jsonschema  # declared dep (jsonschema>=4.21)
    except ImportError as exc:  # noqa: BLE001
        return True, 0, f"unvalidated: {exc}"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(playbook), key=lambda e: list(e.path))
    if not errors:
        return True, 0, ""
    first = errors[0]
    loc = "/".join(str(p) for p in first.path) or "(root)"
    return False, len(errors), f"{loc}: {first.message}"[:200]


def _overlay_bindings(root: Path, slug: str) -> dict[str, Any]:
    """Per-example core_body overlays — where incident-management's bindings live.

    The canonical playbook intentionally carries none yet; the overlay is the
    documented seam (examples/<target>/<slug>/core_body.overlay.json).
    """
    found: dict[str, int] = {}
    for target in ("n8n", "temporal", "langgraph"):
        p = root / "examples" / target / slug / "core_body.overlay.json"
        if not p.is_file():
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        # Overlays key their step map under "workflow_overlays", and each entry
        # carries the core_body block (directly, or under x_secops_ng).
        steps = doc.get("workflow_overlays") or doc.get("workflow") or {}
        n = 0
        for s in steps.values():
            if not isinstance(s, dict):
                continue
            if _is_binding(s.get("core_body")) or _is_binding(_core_body(s)) or _is_binding(s):
                n += 1
        found[target] = n
    return found


def _entry(root: Path, source: Path, slug: str, schema_path: Path) -> dict[str, Any]:
    playbook = _load(source)
    x = playbook.get("x_secops_ng") or {}
    workflow = playbook.get("workflow") or {}

    step_types: dict[str, int] = {}
    bindings = 0
    placeholder_bodies = 0
    unbound_actions = 0
    blank_predicates: list[str] = []

    for step_id, step in workflow.items():
        if not isinstance(step, dict):
            continue
        stype = step.get("type", "?")
        step_types[stype] = step_types.get(stype, 0) + 1
        body = _core_body(step)
        if stype == "action":
            if _is_binding(body):
                bindings += 1
            else:
                unbound_actions += 1
                if isinstance(body, dict):
                    placeholder_bodies += 1
        if stype in _CONTROL_FLOW:
            # Every branch step in this catalog needs operator attention, and a
            # raw expression is not sufficient to avoid it: vuln-intake's
            # switch-condition carries switch='__severity__' yet the n8n emitter
            # still records "no cases parsed". So flag all of them, and record
            # whether a raw expression exists so the hand-off can be precise.
            blank_predicates.append({
                "step_id": step_id,
                "type": stype,
                "raw_expression": step.get("condition") or step.get("switch") or None,
            })

    ok, err_count, first_err = _validate(playbook, schema_path)

    # The n8n emitter writes one meta.secops_ng_notes entry per unbound action
    # plus one per control-flow step. Verified exact against all 12 committed n8n
    # examples, so the remaining-work figure needs no compile to compute.
    overlays_now = _overlay_bindings(root, slug)
    overlay_now = max(overlays_now.values()) if overlays_now else 0
    predicted_todos = unbound_actions + len(blank_predicates)
    # Applying the per-example overlay binds that many more actions. The committed
    # incident-management example is built this way (9 canonical -> 5 with overlay).
    predicted_todos_with_overlay = max(predicted_todos - overlay_now, len(blank_predicates))

    has_cookbook = (root / "docs" / "cookbook" / f"{slug}.md").is_file()
    prim_dir = root / "content" / "playbooks" / slug / "primitives"
    has_primitives = prim_dir.is_dir()
    has_signatures = (prim_dir / "signatures.py").is_file()
    overlays = overlays_now
    overlay_bindings = overlay_now

    if not ok:
        tier = "C"  # cannot compile — exclude from the menu
    elif has_cookbook and has_primitives and (bindings or overlay_bindings):
        tier = "A"  # reference: narrative + primitive source + a worked binding
    else:
        tier = "B"  # compiles, topology only

    return {
        "slug": slug,
        "source": str(source.relative_to(root)),
        "source_format": "yaml" if source.suffix in (".yaml", ".yml") else "json",
        "stable_id": x.get("stable_id"),
        "content_version": x.get("content_version"),
        "maturity": x.get("maturity"),
        "compile_targets": x.get("compile_targets") or [],
        "playbook_types": playbook.get("playbook_types") or [],
        "steps": len(workflow),
        "step_types": step_types,
        "action_steps": step_types.get("action", 0),
        "real_bindings": bindings,
        "placeholder_bodies": placeholder_bodies,
        "overlay_bindings": overlay_bindings,
        "overlay_targets": overlays,
        "blank_predicates": blank_predicates,
        "predicted_n8n_todos": predicted_todos,
        "predicted_n8n_todos_with_overlay": predicted_todos_with_overlay if overlay_bindings else None,
        "has_cookbook": has_cookbook,
        "has_primitives": has_primitives,
        "has_dspy_signatures": has_signatures,
        "compilable": ok,
        "schema_errors": err_count,
        "schema_first_error": first_err,
        "tier": tier,
        # alert-triage's canonical source is YAML but tools.compile consumes
        # JSON, so its regenerate.sh needs a mirror step first.
        "needs_yaml_mirror": source.suffix in (".yaml", ".yml"),
    }


def collect(root: Path | None = None) -> dict[str, Any]:
    root = root or _repo_root()
    schema_path = root / "content-model" / "playbook.schema.json"
    pb_dir = root / "content" / "playbooks"

    sources: list[tuple[Path, str]] = []
    for p in sorted(pb_dir.glob("*/playbook.cacao.json")):
        sources.append((p, p.parent.name))
    # Trap 1a: in-directory YAML sources. Five shipped playbooks keep their
    # canonical source as <slug>/playbook.cacao.yaml rather than .json
    # (business_continuity, data_protection_impact_assessment,
    # data_subject_rights, detection_engineering, network_security), so a
    # JSON-only directory glob silently drops them from the catalog.
    # `_template` and `__pycache__` are scaffolding, not playbooks.
    for p in sorted(pb_dir.glob("*/playbook.cacao.yaml")):
        if p.parent.name.startswith("_"):
            continue
        sources.append((p, p.parent.name))
    # Trap 1b: the dir-level YAML canonical source a */playbook.cacao.json glob misses.
    for p in sorted(pb_dir.glob("*.cacao.yaml")):
        sources.append((p, p.name.replace(".cacao.yaml", "")))

    # A slug can now be reachable twice: content/playbooks/<slug>/playbook.cacao.json
    # and a dir-level <slug>.cacao.yaml. Prefer the directory form (it carries the
    # README, primitives and fixtures) and record that a YAML mirror exists.
    seen: set[str] = set()
    deduped: list[tuple[Path, str]] = []
    yaml_mirrors: set[str] = set()
    for path, slug in sources:
        if slug in seen:
            yaml_mirrors.add(slug)
            continue
        seen.add(slug)
        deduped.append((path, slug))
    sources = deduped

    entries: list[dict[str, Any]] = []
    for path, slug in sources:
        try:
            e = _entry(root, path, slug, schema_path)
            e["yaml_mirror_exists"] = slug in yaml_mirrors
            entries.append(e)
        except Exception as exc:  # noqa: BLE001 - one bad file must not blind the catalog
            entries.append({
                "slug": slug, "source": str(path.relative_to(root)),
                "tier": "C", "compilable": False, "schema_errors": -1,
                "schema_first_error": f"{type(exc).__name__}: {exc}"[:200],
            })

    # Tier A first, then B by ascending remaining work, then C.
    order = {"A": 0, "B": 1, "C": 2}
    entries.sort(key=lambda e: (
        order.get(e.get("tier", "C"), 3),
        e.get("predicted_n8n_todos", 999),
        e.get("slug", ""),
    ))
    return {
        "repo_root": str(root),
        "counts": {
            "total": len(entries),
            "tier_a": sum(1 for e in entries if e.get("tier") == "A"),
            "tier_b": sum(1 for e in entries if e.get("tier") == "B"),
            "tier_c": sum(1 for e in entries if e.get("tier") == "C"),
            "stable": sum(1 for e in entries if e.get("maturity") == "stable"),
        },
        "playbooks": entries,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report the CACAO playbook catalog as JSON.")
    ap.add_argument("--slug", help="restrict output to one playbook")
    ap.add_argument("--table", action="store_true", help="human-readable table instead of JSON")
    args = ap.parse_args(argv)

    data = collect()
    if args.slug:
        data["playbooks"] = [p for p in data["playbooks"] if p.get("slug") == args.slug]
        if not data["playbooks"]:
            print(f"error: no playbook with slug {args.slug!r}", file=sys.stderr)
            return 1

    if args.table:
        print(f"{'tier':5} {'slug':26} {'maturity':13} {'steps':6} {'bound':6} {'todo':5} cookbook")
        print("-" * 84)
        for p in data["playbooks"]:
            bound = p.get("real_bindings", 0) or p.get("overlay_bindings", 0)
            mark = "" if p.get("compilable", True) else "  DOES NOT COMPILE"
            print(
                f"{p.get('tier','?'):5} {p.get('slug',''):26} {str(p.get('maturity')):13} "
                f"{str(p.get('steps','')):6} {str(bound):6} {str(p.get('predicted_n8n_todos','')):5} "
                f"{'yes' if p.get('has_cookbook') else '-'}{mark}"
            )
        c = data["counts"]
        print(f"\n{c['total']} playbooks — tier A:{c['tier_a']} B:{c['tier_b']} C:{c['tier_c']} · "
              f"maturity=stable: {c['stable']}")
        return 0

    json.dump(data, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
