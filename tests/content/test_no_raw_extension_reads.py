"""Guard: tests read SecOps-NG data through ``secops_extension()``, not raw keys.

#1032 moved the SecOps-NG payload of every canonical playbook from a
private ``x_secops_ng`` key into the CACAO 2.0 extension slots. A test that
still reads ``step.get("x_secops_ng")`` from a canonical document gets
nothing back, and every check built on it passes without checking anything
— 35 reads did exactly that until #1038. ``secops_extension()`` reads either
placement, so a test that uses it cannot fall silent this way.

Raw reads stay legitimate where a test deliberately builds or mutates a
document in the legacy placement, which the parser keeps reading until
#1031. Those files are listed below with the reason, and the list is
checked both ways: a raw read anywhere else fails, and an allowlisted file
that no longer reads raw fails too, so the list cannot go stale.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS = REPO_ROOT / "tests"
RAW_READ = re.compile(r"""\.get\(\s*["']x_secops_ng["']|\[\s*["']x_secops_ng["']\s*\]""")

ALLOWED = {
    "tests/compilers/_shared/test_secops_extension_placement.py":
        "rebuilds and compares the legacy placement on purpose",
    "tests/compilers/_shared/test_cacao_parser.py":
        "mutates a legacy-placement fixture to exercise parser errors",
    "tests/compilers/langgraph/test_state.py":
        "mutates a legacy-placement fixture",
    "tests/content_model/test_playbook_schema.py":
        "validates legacy-placement documents against the content-model schema",
    "tests/content_model/test_ransomware_containment_example.py":
        "reads the content-model example format, which keeps the legacy key",
    "tests/content_model/test_vuln_intake_example.py":
        "reads the content-model example format, which keeps the legacy key",
}


def raw_reads(root: Path) -> dict[str, list[int]]:
    found: dict[str, list[int]] = {}
    for path in sorted(root.rglob("*.py")):
        lines = [n for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
                 if RAW_READ.search(line)]
        if lines:
            found[path.relative_to(root.parent).as_posix()] = lines
    return found


def test_no_test_reads_the_extension_payload_by_raw_key() -> None:
    found = raw_reads(TESTS)
    found.pop(Path(__file__).relative_to(REPO_ROOT).as_posix(), None)
    stray = {f: lines for f, lines in found.items() if f not in ALLOWED}
    assert not stray, (
        "raw x_secops_ng reads outside the legacy-fixture allowlist; use "
        "compilers._shared.cacao_parser.secops_extension(): " + str(stray)
    )


@pytest.mark.parametrize("path", sorted(ALLOWED))
def test_every_allowlisted_file_still_needs_its_exception(path: str) -> None:
    assert path in raw_reads(TESTS), f"{path} no longer reads x_secops_ng raw; drop it from ALLOWED"


def test_the_guard_bites(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    (tests / "examples").mkdir(parents=True)
    (tests / "examples" / "test_x.py").write_text('x = step.get("x_secops_ng") or {}\n', encoding="utf-8")
    (tests / "examples" / "test_y.py").write_text("x = secops_extension(step) or {}\n", encoding="utf-8")
    assert raw_reads(tests) == {"tests/examples/test_x.py": [1]}
