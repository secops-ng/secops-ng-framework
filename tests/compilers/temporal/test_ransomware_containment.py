"""Golden test for the Temporal compiler — ransomware-containment.

Pins the emitted Temporal workflow stub for the ransomware-containment
fixture; mirrors ``test_golden.py`` (vuln-intake) so any drift surfaces
in review.

Regenerate via::

    python -m compilers.temporal \\
        tests/compilers/_shared/fixtures/ransomware_containment.cacao.json \\
        > tests/compilers/temporal/golden/ransomware_containment.expected.py
"""
from __future__ import annotations

from pathlib import Path

from compilers.temporal.emit import emit_file

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "ransomware_containment.cacao.json"
)
GOLDEN = (
    Path(__file__).resolve().parent
    / "golden"
    / "ransomware_containment.expected.py"
)


def test_ransomware_containment_matches_golden() -> None:
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
