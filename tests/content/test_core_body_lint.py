"""CI gate for the CORE primitive-binding resolution linter.

``content-model/playbook.schema.json`` defers ``core_body`` resolution to
"the linter, not the schema". This is the test that makes that true.

The HARD assertion is the regression net. It passed vacuously for as long
as nothing checked: ``alert_triage`` shipped 8 bindings and ``vuln_intake``
2 whose dotted module path did not import, and the broken
``from <module> import <callable>`` line was committed into the worked
examples under ``examples/{temporal,langgraph,n8n}/`` where an operator
would copy it.

SOFT findings are asserted as a *ceiling* rather than zero. They need
content decisions — declare a new playbook variable, or accept the value
as harness-injected runtime context — and pinning the current count means
the number can only go down without someone editing this file, while a
new binding that repeats the mistake still trips the assertion.
"""
from __future__ import annotations

from pathlib import Path

from tools.lint_core_body import HARD, SOFT, check

REPO_ROOT = Path(__file__).resolve().parents[2]

# Ceiling, not a target. Lower it as the follow-up decisions land; never
# raise it to accommodate a new binding.
MAX_SOFT_FINDINGS = 32


def test_no_hard_findings() -> None:
    """Every core_body binding must import and take the arguments it is given."""
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


def test_soft_findings_do_not_regress() -> None:
    """SOFT findings may fall, never rise."""
    findings, summary = check(REPO_ROOT)
    soft = summary["soft"]
    assert soft <= MAX_SOFT_FINDINGS, (
        f"core_body SOFT findings rose to {soft} (ceiling {MAX_SOFT_FINDINGS}). "
        "A new binding references an undeclared playbook variable or leaves a "
        "required parameter unbound:\n"
        + "\n".join(
            f"  {f.slug}/{f.step} [{f.code}] {f.message}"
            for f in findings
            if f.severity == "SOFT"
        )
    )


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
