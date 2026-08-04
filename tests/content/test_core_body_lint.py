"""CI gate for the CORE primitive-binding resolution linter.

``content-model/playbook.schema.json`` defers ``core_body`` resolution to
"the linter, not the schema". This is the test that makes that true.

The HARD assertion is the regression net. It passed vacuously for as long
as nothing checked: ``alert_triage`` shipped 8 bindings and ``vuln_intake``
2 whose dotted module path did not import, and the broken
``from <module> import <callable>`` line was committed into the worked
examples under ``examples/{temporal,langgraph,n8n}/`` where an operator
would copy it.

Every finding code is HARD now. The three variable/argument codes
(``unbound_required_argument``, ``unknown_in_variable``,
``unknown_out_variable``) started SOFT with a pinned ceiling of 32 because
each needed a content decision — declare a variable, or accept the value as
runtime context. #866 settled both decisions: Decision 1 established the
runtime-context convention (declared as ordinary ``playbook_variables``,
#871), Decision 2 declared or rebound everything that remained, and the
ceiling test that lived here was replaced by the zero assertion. A new
binding must declare its variables and bind its required parameters in the
same change.
"""
from __future__ import annotations

from pathlib import Path

from tools.lint_core_body import HARD, SOFT, check

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_no_hard_findings() -> None:
    """Every binding imports, takes its arguments, and resolves its variables."""
    findings, summary = check(REPO_ROOT)
    hard = [f for f in findings if f.severity == "HARD"]
    assert not hard, "core_body bindings that cannot execute:\n" + "\n".join(
        f"  {f.slug}/{f.step} [{f.code}] {f.message}" for f in hard
    )
    assert summary["hard"] == 0


def test_bindings_are_actually_present() -> None:
    """Fixture sanity: a linter over zero bindings would pass trivially."""
    _, summary = check(REPO_ROOT)
    assert summary["bindings"] > 0, (
        "no core_body bindings discovered — the linter would pass vacuously, "
        "so this assertion guards the discovery path itself."
    )


def test_soft_set_is_empty() -> None:
    """#866 promoted the last three SOFT codes to HARD; none may demote silently.

    If a future change adds a genuinely-SOFT code, update this test with the
    reasoning — demotion is a decision, not a drive-by.
    """
    assert SOFT == ()
    _, summary = check(REPO_ROOT)
    assert summary["soft"] == 0


def test_finding_codes_are_partitioned() -> None:
    """Every emitted code belongs to exactly one severity class."""
    assert not set(HARD) & set(SOFT)
    findings, _ = check(REPO_ROOT)
    for f in findings:
        assert f.code in (HARD if f.severity == "HARD" else SOFT), (
            f"{f.code} emitted at severity {f.severity} but is not in that class"
        )


def test_linter_is_invocation_independent(tmp_path) -> None:
    """The linter must give the same verdict however it is started.

    Regression net for a false-positive mode shipped in #865: primitive paths
    are dotted from the repo root, so resolving them needs that root on
    ``sys.path``. Running as ``python -m tools.lint_core_body`` from the repo
    root supplied it accidentally via the working directory; running as
    ``python tools/lint_core_body.py``, from another directory, or against a
    ``--root`` that was not the cwd reported all 46 bindings as
    ``unresolvable_module`` — 46 spurious HARD findings inviting someone to
    "fix" content that was never broken.
    """
    import subprocess
    import sys

    script = REPO_ROOT / "tools" / "lint_core_body.py"
    invocations = [
        ([sys.executable, "-m", "tools.lint_core_body"], REPO_ROOT),
        ([sys.executable, str(script)], REPO_ROOT),
        ([sys.executable, str(script), "--root", str(REPO_ROOT)], tmp_path),
    ]
    for argv, cwd in invocations:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        assert proc.returncode == 0, (
            f"linter failed when run as {argv[1:]} from {cwd}:\n{proc.stdout}"
        )
        assert "0 hard" in proc.stdout, (
            f"invocation {argv[1:]} from {cwd} disagreed on HARD count:\n"
            f"{proc.stdout}"
        )
