"""Golden test for the Temporal compiler — on-call-rotation.

Pins the emitted Temporal workflow stub for the on-call-rotation
fixture; mirrors ``test_golden.py`` (vuln-intake) so any drift surfaces
in review.

Regenerate via::

    python -m compilers.temporal \\
        tests/compilers/_shared/fixtures/on_call_rotation.cacao.json \\
        > tests/compilers/temporal/golden/on_call_rotation.expected.py
"""
from __future__ import annotations

from pathlib import Path

from compilers.temporal.emit import emit_file

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "on_call_rotation.cacao.json"
)
GOLDEN = (
    Path(__file__).resolve().parent
    / "golden"
    / "on_call_rotation.expected.py"
)


def test_on_call_rotation_matches_golden() -> None:
    actual = emit_file(FIXTURE)
    expected = GOLDEN.read_text(encoding="utf-8")
    assert actual == expected, (
        "Temporal emitter output drifted from the golden file. "
        "If this change is intentional, regenerate "
        f"{GOLDEN.relative_to(Path(__file__).resolve().parents[3])} "
        "and review the diff before committing."
    )


def test_golden_file_is_committed() -> None:
    assert GOLDEN.exists(), f"missing golden file: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty golden file: {GOLDEN}"


def test_emit_is_deterministic() -> None:
    assert emit_file(FIXTURE) == emit_file(FIXTURE)
