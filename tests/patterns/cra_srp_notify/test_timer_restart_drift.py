"""G-03 restart-drift parity test — CRA SRP notify timer cascade.

Row on the compile-target parity gate (G-03) for the CRA Article 14
notification workflow (``playbook.cra_srp_notify@v1``): the 24h / 72h
/ 14d-or-30d timer cascade must survive worker restart on each of the
three reference compile targets (n8n, Temporal, LangGraph) without
drift.

SecOps-NG ships **content + compilers**, not a live runtime — so the
"restart-drift" contract is asserted structurally, not by spinning up
each target's engine and killing it. The invariant we pin here is the
*anchor* every restart-drift bug in a real runtime would violate:

  Every durable-delay step in the CRA SRP notify workflow MUST derive
  its deadline from the ``__awareness_ts__`` playbook variable (an
  external, playbook-scoped input), NOT from the compile target's
  emitter clock (``now()``, ``datetime.utcnow()``, ``Date.now()``,
  ``$now``, hard-coded timestamps).

A timer anchored on an external input re-hydrates to the same deadline
after any number of restarts. A timer anchored on emitter-time drifts
by exactly (restart_at - original_start), which is the class of bug
this test rules out.

The row also asserts:

* Each target names the awareness anchor consistently
  (``awareness_ts`` / ``__awareness_ts__``).
* Each target expresses the 24h / 72h / 14d-or-30d cadence somewhere
  the emitted artifact can be read (playbook doc, node body, timer
  attribute) — no target may silently drop a gate.

If a future emitter change makes one target sleep for a hard-coded
duration from ``now()`` rather than sleeping until an
awareness-anchored deadline, this test fails.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

CACAO_SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "cra_srp_notify"
    / "playbook.cacao.json"
)
N8N_ARTIFACT = (
    REPO_ROOT / "examples" / "n8n" / "cra_srp_notify" / "workflow.n8n.json"
)
TEMPORAL_ARTIFACT = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "cra_srp_notify"
    / "workflow.temporal.py"
)
LANGGRAPH_ARTIFACT = (
    REPO_ROOT / "examples" / "langgraph" / "cra_srp_notify" / "graph_spec.json"
)
# The LangGraph target's timer bodies live in the sibling
# ``state_bindings.py`` — the delay signature and awareness-anchor
# consumption are asserted there because ``graph_spec.json`` is the
# topology, not the node bodies.
LANGGRAPH_BINDINGS = (
    REPO_ROOT / "examples" / "langgraph" / "cra_srp_notify" / "state_bindings.py"
)

# Emitter-clock patterns that would cause restart drift if any timer
# in the CRA SRP notify workflow depended on them. Match is
# case-insensitive; the intent is that a restart-drift bug shows up as
# "the emitter reached for now() when computing a deadline".
EMITTER_CLOCK_PATTERNS = (
    r"\bnow\s*\(\s*\)",
    r"\bdatetime\.utcnow\b",
    r"\bdatetime\.now\b",
    r"\btime\.time\s*\(",
    r"\bDate\.now\s*\(",
    r"\$now\b",
    r"\{\{\s*\$now",
)


# --------------------------------------------------------------------- #
# CACAO source — anchor invariant                                       #
# --------------------------------------------------------------------- #


def _cacao_workflow() -> dict:
    return json.loads(CACAO_SOURCE.read_text(encoding="utf-8"))["workflow"]


def _delay_steps() -> dict:
    """Return the two durable-delay action steps of the CRA SRP notify workflow."""
    wf = _cacao_workflow()
    return {
        step_id: step
        for step_id, step in wf.items()
        if step.get("type") == "action" and step.get("name", "").startswith("wait until")
    }


def test_cacao_delay_steps_anchor_on_awareness_ts() -> None:
    """Every durable-delay step must consume ``__awareness_ts__`` as input.

    A delay step that does not name ``__awareness_ts__`` in its
    ``in_args`` cannot re-derive its deadline from playbook-scoped
    input after a worker restart, so it would drift by exactly
    (restart_at - original_start) on any target implementing the
    delay against the emitter clock.
    """
    delays = _delay_steps()
    assert delays, "CRA SRP notify workflow has no durable-delay steps to check"
    for step_id, step in delays.items():
        in_args = step.get("in_args") or []
        assert "__awareness_ts__" in in_args, (
            f"CACAO delay step {step_id} ({step.get('name')!r}) does not "
            f"declare `__awareness_ts__` in in_args; its deadline cannot "
            f"re-hydrate deterministically after restart. Got in_args="
            f"{in_args!r}."
        )


def test_cacao_source_expresses_full_cadence() -> None:
    """CACAO source must express 24h + 72h + (14d | 30d) somewhere.

    The three windows are the CRA Article 14 clock triad; a target
    that silently drops one of them regresses the parity contract.
    """
    text = CACAO_SOURCE.read_text(encoding="utf-8")
    assert "24-hour" in text or "24 hour" in text or "24h" in text
    assert "72-hour" in text or "72 hour" in text or "72h" in text
    assert "14 days" in text or "14-day" in text or "14d" in text
    assert "1 month" in text or "30 day" in text or "30-day" in text


# --------------------------------------------------------------------- #
# Per-target restart-drift contract                                     #
# --------------------------------------------------------------------- #


def _target_paths() -> dict[str, tuple[Path, ...]]:
    """Files each target emits that must jointly satisfy the drift contract.

    A target may split its output across multiple files (LangGraph
    splits the topology from the node bodies); every check reads the
    concatenation so an anchor or a cadence marker in any of the
    target's committed artifacts counts.
    """
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
            f"{target} artifact missing at {path.relative_to(REPO_ROOT)}; the "
            f"G-03 restart-drift row can only pin what is committed."
        )


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_references_awareness_anchor(target: str, paths: tuple[Path, ...]) -> None:
    """Each target artifact must reference the awareness anchor.

    The anchor is what makes the delay restart-safe: on rehydration
    the target re-reads ``__awareness_ts__`` (or its per-target alias
    ``awareness_ts``) and re-computes the same deadline. A target that
    does not name the anchor anywhere in its emitted bytes cannot
    honour the invariant — the deadline would have to come from
    somewhere else (emitter clock, hard-coded offset), which drifts on
    restart.
    """
    text = _target_text(paths)
    # Match either the raw playbook-variable form (`__awareness_ts__`,
    # kept by n8n as its notes/context) or the per-target
    # sanitised-identifier form (`awareness_ts`) — Temporal activities
    # strip the CACAO underscore prefix / suffix.
    assert "__awareness_ts__" in text or "awareness_ts" in text, (
        f"{target} artifact set does not reference the awareness anchor "
        f"(either `__awareness_ts__` or `awareness_ts`); a delay that "
        f"does not name the anchor cannot re-derive its deadline after "
        f"restart. Scanned: {[str(p.relative_to(REPO_ROOT)) for p in paths]}."
    )


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_free_of_emitter_clock_references(
    target: str, paths: tuple[Path, ...]
) -> None:
    """No target may reach for the emitter clock to compute a deadline.

    A delay expressed as ``now() + 72h`` drifts by exactly
    (restart_at - original_start) after a worker restart, because the
    ``now()`` reading at restart is not the ``now()`` at original
    start. The same delay expressed as ``__awareness_ts__ + 72h``
    re-hydrates cleanly.

    We assert the absence of every common emitter-clock idiom across
    the three-target emitters. The SKELETON emitters do not reach
    for these; this test is the regression net that stops a future
    CORE (which lands the concrete delay bodies once the SRP schema
    is public) from wiring a restart-unsafe delay.
    """
    text = _target_text(paths)
    hits: list[str] = []
    for pat in EMITTER_CLOCK_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append(pat)
    assert not hits, (
        f"{target} artifact set references an emitter-clock idiom that "
        f"would cause restart drift on the CRA Article 14 timer cascade: "
        f"{hits}. Anchor deadlines on `__awareness_ts__` (external "
        f"playbook input) instead. Scanned: "
        f"{[str(p.relative_to(REPO_ROOT)) for p in paths]}."
    )


# --------------------------------------------------------------------- #
# Cadence-parity across the three targets                               #
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_carries_72h_gate(target: str, paths: tuple[Path, ...]) -> None:
    """Every target must name the 72-hour full-notification gate.

    Silently dropping a gate on one target while the others keep it
    is exactly the kind of parity regression G-03 pins.
    """
    text = _target_text(paths).lower()
    assert "72h" in text or "72-hour" in text or "72 hour" in text, (
        f"{target} artifact set does not name the 72h full-notification "
        f"gate; the timer cascade is broken on this target."
    )


@pytest.mark.parametrize(
    "target,paths",
    list(_target_paths().items()),
    ids=list(_target_paths().keys()),
)
def test_target_carries_final_report_gate(
    target: str, paths: tuple[Path, ...]
) -> None:
    """Every target must name the final-report gate (14d/30d branch)."""
    text = _target_text(paths).lower()
    assert "final_report" in text or "final-report" in text or "final report" in text, (
        f"{target} artifact set does not name the final-report gate; the "
        f"14d/30d branch of the CRA Article 14 timer cascade is missing "
        f"on this target."
    )
