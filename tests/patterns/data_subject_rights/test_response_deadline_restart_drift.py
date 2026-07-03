"""G-03 restart-drift parity test — data_subject_rights response window.

Row on the compile-target parity gate (G-03) for the GDPR data subject
rights workflow (``playbook.data_subject_rights@v1``): the Article
12(3) one-month response window must survive worker restart on each
of the three reference compile targets (n8n, Temporal, LangGraph)
without drift.

SecOps-NG ships **content + compilers**, not a live runtime — so the
"restart-drift" contract is asserted structurally, not by spinning up
each target's engine and killing it. The invariant we pin here is the
*anchor* every restart-drift bug in a real runtime would violate:

  The response deadline MUST derive from the ``__request_received_ts__``
  playbook variable (an external, playbook-scoped input), NOT from the
  compile target's emitter clock (``now()``, ``datetime.utcnow()``,
  ``Date.now()``, ``$now``, hard-coded timestamps).

A deadline anchored on an external input re-hydrates to the same
value after any number of restarts. A deadline anchored on
emitter-time drifts by exactly (restart_at - original_start), which
is the class of bug this test rules out.

The row also asserts:

* Each target names the request-received anchor consistently
  (``request_received_ts`` / ``__request_received_ts__``) and the
  derived deadline (``response_deadline`` /
  ``__response_deadline__``).
* Each target expresses the one-month / 30-day cadence somewhere the
  emitted artifact can be read — no target may silently drop the
  Article 12(3) window.

If a future emitter change makes one target compute the deadline from
``now()`` rather than from the external anchor, this test fails.

See ``tests/patterns/cra_srp_notify/test_timer_restart_drift.py`` for
the sibling row on the CRA Article 14 SRP notify cascade.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

CACAO_YAML_SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "data_subject_rights"
    / "playbook.cacao.yaml"
)
N8N_ARTIFACT = (
    REPO_ROOT / "examples" / "n8n" / "data_subject_rights" / "workflow.n8n.json"
)
TEMPORAL_ARTIFACT = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "data_subject_rights"
    / "workflow.temporal.py"
)
LANGGRAPH_ARTIFACT = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "data_subject_rights"
    / "graph_spec.json"
)
LANGGRAPH_BINDINGS = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "data_subject_rights"
    / "state_bindings.py"
)

# Emitter-clock patterns that would cause restart drift if the DSR
# response deadline depended on them.
EMITTER_CLOCK_PATTERNS = (
    r"\bnow\s*\(\s*\)",
    r"\bdatetime\.utcnow\b",
    r"\bdatetime\.now\b",
    r"\btime\.time\s*\(",
    r"\bDate\.now\s*\(",
    r"\$now\b",
    r"\{\{\s*\$now",
)


def _cacao_workflow() -> dict:
    return yaml.safe_load(CACAO_YAML_SOURCE.read_text(encoding="utf-8"))["workflow"]


def _step_by_name(name: str) -> tuple[str, dict]:
    wf = _cacao_workflow()
    for step_id, step in wf.items():
        if step.get("name") == name:
            return step_id, step
    raise AssertionError(f"CACAO step named {name!r} not found in workflow")


# --------------------------------------------------------------------- #
# CACAO source — anchor invariant                                       #
# --------------------------------------------------------------------- #


def test_classify_request_consumes_request_received_ts() -> None:
    """``classify_request`` must consume ``__request_received_ts__``.

    The Article 12(3) deadline is defined as
    ``__request_received_ts__ + one month``. A classify step that does
    not name the anchor in its ``in_args`` cannot re-derive the
    deadline deterministically after a worker restart.
    """
    _step_id, step = _step_by_name("classify_request")
    in_args = step.get("in_args") or []
    assert "__request_received_ts__" in in_args, (
        f"CACAO step classify_request does not declare "
        f"`__request_received_ts__` in in_args; its Article 12(3) "
        f"deadline cannot re-hydrate deterministically after restart. "
        f"Got in_args={in_args!r}."
    )


def test_classify_request_emits_response_deadline() -> None:
    _step_id, step = _step_by_name("classify_request")
    out_args = step.get("out_args") or []
    assert "__response_deadline__" in out_args, (
        f"CACAO step classify_request must declare `__response_deadline__` "
        f"in out_args so downstream steps consume the derived deadline "
        f"rather than recomputing from an emitter clock. Got out_args="
        f"{out_args!r}."
    )


def test_send_controller_response_consumes_response_deadline() -> None:
    _step_id, step = _step_by_name("send_controller_response")
    in_args = step.get("in_args") or []
    assert "__response_deadline__" in in_args, (
        f"CACAO step send_controller_response must consume "
        f"`__response_deadline__` in in_args; sending on the Article "
        f"12(3) deadline requires reading the externally-derived "
        f"deadline, not `now()`. Got in_args={in_args!r}."
    )


def test_cacao_source_expresses_article_12_3_cadence() -> None:
    """CACAO source must express the one-month response window.

    The controller has a one-month baseline plus an optional two-month
    extension under Article 12(3). A target that silently drops the
    window regresses the parity contract.
    """
    text = CACAO_YAML_SOURCE.read_text(encoding="utf-8")
    lower = text.lower()
    assert (
        "one month" in lower
        or "1 month" in lower
        or "30 day" in lower
        or "30-day" in lower
    ), "CACAO source does not name the Article 12(3) response window"


# --------------------------------------------------------------------- #
# Per-target restart-drift contract                                     #
# --------------------------------------------------------------------- #


def _target_paths() -> dict[str, tuple[Path, ...]]:
    return {
        "n8n": (N8N_ARTIFACT,),
        "temporal": (TEMPORAL_ARTIFACT,),
        "langgraph": (LANGGRAPH_ARTIFACT, LANGGRAPH_BINDINGS),
    }


def _target_text(paths: tuple[Path, ...]) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in paths)


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_artifact_exists(target: str, paths: tuple[Path, ...]) -> None:
    for path in paths:
        assert path.exists(), (
            f"{target} artifact missing at {path.relative_to(REPO_ROOT)}; "
            f"the G-03 restart-drift row can only pin what is committed."
        )


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_references_request_received_anchor(
    target: str, paths: tuple[Path, ...]
) -> None:
    """Each target artifact must reference the request-received anchor.

    On rehydration the target re-reads ``__request_received_ts__`` (or
    its per-target alias ``request_received_ts``) and re-computes the
    same deadline. A target that does not name the anchor anywhere in
    its emitted bytes cannot honour the invariant.
    """
    text = _target_text(paths)
    assert "__request_received_ts__" in text or "request_received_ts" in text, (
        f"{target} artifact set does not reference the request-received "
        f"anchor (either `__request_received_ts__` or "
        f"`request_received_ts`); the deadline cannot re-derive after "
        f"restart. Scanned: "
        f"{[str(p.relative_to(REPO_ROOT)) for p in paths]}."
    )


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_references_response_deadline(
    target: str, paths: tuple[Path, ...]
) -> None:
    """Each target artifact must reference the derived deadline."""
    text = _target_text(paths)
    assert "__response_deadline__" in text or "response_deadline" in text, (
        f"{target} artifact set does not reference the derived "
        f"`response_deadline`; send_controller_response cannot honour "
        f"the Article 12(3) deadline. Scanned: "
        f"{[str(p.relative_to(REPO_ROOT)) for p in paths]}."
    )


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_free_of_emitter_clock_references(
    target: str, paths: tuple[Path, ...]
) -> None:
    """No target may reach for the emitter clock to compute the deadline.

    A deadline expressed as ``now() + 30d`` drifts by exactly
    (restart_at - original_start) after a worker restart. The same
    deadline expressed as ``__request_received_ts__ + 30d`` re-hydrates
    cleanly.
    """
    text = _target_text(paths)
    hits: list[str] = []
    for pat in EMITTER_CLOCK_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append(pat)
    assert not hits, (
        f"{target} artifact set references an emitter-clock idiom that "
        f"would cause restart drift on the Article 12(3) response "
        f"deadline: {hits}. Anchor deadlines on "
        f"`__request_received_ts__` (external playbook input) instead. "
        f"Scanned: {[str(p.relative_to(REPO_ROOT)) for p in paths]}."
    )
