"""Bidirectional link linter for the KPI/KRI catalog.

Closes the loop introduced by CORE link-closure (v0):

a. Every ``metric_ref`` carried by a shipped CACAO playbook under
   ``content/playbooks/*/playbook.cacao.json`` MUST resolve to an
   existing catalog ``stable_id`` under ``content/metrics/*.yaml``.

b. Every ``playbook_refs[].playbook_id`` declared on a catalog entry
   MUST resolve to an existing playbook ``stable_id`` — and when the
   entry pins a ``step_id``, that step MUST exist in the referenced
   playbook's ``workflow``.

c. The ``kpi.*`` / ``kri.*`` namespace prefix on every catalog entry
   MUST agree with its declared ``kind`` (already enforced at schema
   load time; asserted here at the link level too so a future schema
   relaxation does not silently break the catalog's namespace
   contract).

Pure stdlib + PyYAML. No network, no schema dependency.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = REPO_ROOT / "content" / "metrics"
PLAYBOOKS_DIR = REPO_ROOT / "content" / "playbooks"


def _catalog_entries() -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in sorted(METRICS_DIR.glob("*.yaml")):
        if not p.is_file():
            continue
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and "stable_id" in doc:
            out.append((p, doc))
    return out


def _playbook_files() -> list[Path]:
    return sorted(PLAYBOOKS_DIR.glob("*/playbook.cacao.json"))


@pytest.fixture(scope="module")
def catalog_ids() -> set[str]:
    return {doc["stable_id"] for _, doc in _catalog_entries()}


@pytest.fixture(scope="module")
def playbooks() -> dict[str, dict]:
    """Map playbook stable_id -> parsed CACAO document."""
    out: dict[str, dict] = {}
    for pf in _playbook_files():
        pb = json.loads(pf.read_text(encoding="utf-8"))
        sid = pb.get("x_secops_ng", {}).get("stable_id")
        assert sid, f"{pf} is missing x_secops_ng.stable_id"
        assert sid not in out, f"duplicate playbook stable_id {sid}"
        out[sid] = pb
    return out


# ---------------------------------------------------------------------------
# (a) Playbook -> catalog
# ---------------------------------------------------------------------------


def _collect_playbook_metric_refs(pb: dict) -> list[tuple[str, str]]:
    """Return list of (origin, metric_ref).

    Origin is ``"<playbook>:<step_id>"`` for workflow-step refs and
    ``"<playbook>:#top"`` for top-level x_secops_ng.metric_refs.
    """
    sid = pb["x_secops_ng"]["stable_id"]
    out: list[tuple[str, str]] = []
    for mref in pb.get("x_secops_ng", {}).get("metric_refs", []) or []:
        out.append((f"{sid}:#top", mref))
    for step_id, step in (pb.get("workflow") or {}).items():
        x = step.get("x_secops_ng") or {}
        for mref in x.get("metric_refs", []) or []:
            out.append((f"{sid}:{step_id}", mref))
        # Single-valued metric_ref variant (defensive: schema allows
        # either shape on different layers).
        single = x.get("metric_ref")
        if isinstance(single, str):
            out.append((f"{sid}:{step_id}", single))
    return out


@pytest.mark.parametrize(
    "playbook_path",
    _playbook_files(),
    ids=lambda p: p.parent.name,
)
def test_playbook_metric_refs_resolve_to_catalog(
    playbook_path: Path, catalog_ids: set[str]
) -> None:
    pb = json.loads(playbook_path.read_text(encoding="utf-8"))
    refs = _collect_playbook_metric_refs(pb)
    dangling = [(origin, mref) for origin, mref in refs if mref not in catalog_ids]
    assert not dangling, (
        f"{playbook_path.relative_to(REPO_ROOT)} carries metric_refs that do "
        f"not resolve to any content/metrics/*.yaml stable_id: {dangling}"
    )


# ---------------------------------------------------------------------------
# (b) Catalog -> playbook (+ step pin)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "yaml_path",
    [p for p, _ in _catalog_entries()],
    ids=lambda p: p.name,
)
def test_catalog_playbook_refs_resolve(
    yaml_path: Path, playbooks: dict[str, dict]
) -> None:
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    refs = doc.get("playbook_refs", []) or []
    errors: list[str] = []
    for entry in refs:
        pbid = entry.get("playbook_id")
        if pbid not in playbooks:
            errors.append(
                f"playbook_id {pbid!r} does not resolve to any shipped "
                f"playbook under content/playbooks/*/playbook.cacao.json"
            )
            continue
        step_id = entry.get("step_id")
        if step_id is not None:
            wf = playbooks[pbid].get("workflow") or {}
            if step_id not in wf:
                errors.append(
                    f"playbook_id {pbid} step_id {step_id!r} does not exist "
                    f"in that playbook's workflow"
                )
    assert not errors, (
        f"{yaml_path.relative_to(REPO_ROOT)} has dangling playbook_refs: "
        + "; ".join(errors)
    )


# ---------------------------------------------------------------------------
# (c) Namespace-prefix <-> kind agreement, asserted at link level
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "yaml_path",
    [p for p, _ in _catalog_entries()],
    ids=lambda p: p.name,
)
def test_catalog_namespace_matches_kind(yaml_path: Path) -> None:
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    sid = doc["stable_id"]
    kind = doc["kind"]
    prefix = sid.split(".", 1)[0]
    assert prefix == kind, (
        f"{yaml_path.relative_to(REPO_ROOT)} namespace/kind disagree: "
        f"stable_id={sid!r} starts with {prefix!r} but kind={kind!r}"
    )


# ---------------------------------------------------------------------------
# Belt-and-braces: at least one bidirectional link landed.
# ---------------------------------------------------------------------------


def test_at_least_one_catalog_entry_has_playbook_backref() -> None:
    """Sanity check: the CORE link-closure layer is supposed to populate
    back-references. If every entry still ships an empty playbook_refs,
    something has regressed in the link-closure pipeline (or all the
    metric_ref-carrying playbooks were removed)."""
    has_any = any(
        (doc.get("playbook_refs") or []) for _, doc in _catalog_entries()
    )
    assert has_any, (
        "no catalog entry under content/metrics/*.yaml has any "
        "playbook_refs back-reference populated — CORE link-closure "
        "appears to have regressed"
    )
