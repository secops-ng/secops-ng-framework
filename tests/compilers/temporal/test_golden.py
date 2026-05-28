"""Golden test for the Temporal compiler.

Locks down the exact emitted Python source for the ``vuln-intake`` worked
example. Any change to the emitter that alters output for this fixture
must update the golden file in lockstep, surfacing regressions in code
review rather than letting silent drift land on main.

Regenerate the golden via::

    python -m compilers.temporal tests/compilers/_shared/fixtures/vuln_intake.cacao.json \\
        > tests/compilers/temporal/golden/vuln_intake.expected.py

A reviewer should inspect the diff before accepting an update.
"""
from __future__ import annotations

from pathlib import Path

from compilers.temporal.emit import emit_file

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)
GOLDEN = Path(__file__).resolve().parent / "golden" / "vuln_intake.expected.py"


def test_vuln_intake_matches_golden() -> None:
    actual = emit_file(FIXTURE)
    expected = GOLDEN.read_text(encoding="utf-8")
    assert actual == expected, (
        "Temporal emitter output drifted from the golden file. "
        "If this change is intentional, regenerate "
        f"{GOLDEN.relative_to(Path(__file__).resolve().parents[3])} "
        "and review the diff before committing."
    )


def test_golden_file_is_committed() -> None:
    # Guards against an empty / missing golden landing on main.
    assert GOLDEN.exists(), f"missing golden file: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty golden file: {GOLDEN}"
