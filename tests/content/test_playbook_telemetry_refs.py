"""CI gate for the playbook-layer OCSF telemetry-reference linter.

``tools/lint_catalogue_ocsf_bindings.py`` guards the metrics layer. This
guards the two playbook-side layers it deliberately does not walk:
``x_secops_ng.telemetry_refs`` (playbook and per step) and the outbound
overlay's ``ocsf[].id``.

The HARD assertion is the regression net for #873. Before it, 63 of the
overlay's 91 refs spelled the class without the ``ocsf`` segment —
``telemetry.api_activity@v1`` against a committed
``telemetry.ocsf.api_activity@v1`` — and nothing checked. It surfaced only
because a contributor (me) copied the bare spelling out of an overlay into a
new metric, where the metrics guard caught it.

SOFT findings are asserted as a ceiling rather than zero. They name OCSF
classes the catalogue does not ship, so closing them means authoring the
telemetry artifact or dropping the claim — content work with a judgement in
it. Pinning the count lets it fall without editing this file while still
tripping on a new binding that repeats the mistake.
"""
from __future__ import annotations

from pathlib import Path

from tools.lint_playbook_telemetry_refs import HARD, SOFT, check

REPO_ROOT = Path(__file__).resolve().parents[2]

# Ceiling, not a target. Lower it as telemetry artifacts land; never raise it.
MAX_SOFT_FINDINGS = 36


def test_no_hard_findings() -> None:
    """Every telemetry ref must use the namespaced OCSF spelling."""
    findings, summary = check(REPO_ROOT)
    hard = [f for f in findings if f.severity == "HARD"]
    assert not hard, "telemetry refs using the bare spelling:\n" + "\n".join(
        f"  {f.slug}/{f.where} [{f.code}] {f.message}" for f in hard
    )
    assert summary["hard"] == 0


def test_refs_are_actually_present() -> None:
    """Fixture sanity: a linter over zero refs would pass trivially."""
    _, summary = check(REPO_ROOT)
    assert summary["refs"] > 0
    assert summary["telemetry_artifacts"] > 0


def test_soft_findings_do_not_regress() -> None:
    """SOFT findings may fall, never rise."""
    findings, summary = check(REPO_ROOT)
    assert summary["soft"] <= MAX_SOFT_FINDINGS, (
        f"undefined-telemetry-class findings rose to {summary['soft']} "
        f"(ceiling {MAX_SOFT_FINDINGS}):\n"
        + "\n".join(
            f"  {f.slug}/{f.where} {f.ref}" for f in findings if f.severity == "SOFT"
        )
    )


def test_finding_codes_are_partitioned() -> None:
    assert not set(HARD) & set(SOFT)
    findings, _ = check(REPO_ROOT)
    for f in findings:
        assert f.code in (HARD if f.severity == "HARD" else SOFT)
