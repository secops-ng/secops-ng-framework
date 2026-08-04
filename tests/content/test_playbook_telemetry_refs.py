"""CI gate for the playbook-layer OCSF telemetry-reference linter.

``tools/lint_catalogue_ocsf_bindings.py`` guards the metrics layer. This
guards the two playbook-side layers it deliberately does not walk:
``x_secops_ng.telemetry_refs`` (playbook and per step) and the outbound
overlay's ``ocsf[].id``.

Both finding codes are HARD and asserted at zero. ``bare_ocsf_ref`` is the
regression net for #873: before it, 63 of the overlay's 91 refs spelled the
class without the ``ocsf`` segment and nothing checked.
``undefined_telemetry_class`` is the regression net for #875: it began as a
SOFT count pinned at a ceiling of 36 while the refs named classes the
catalogue did not ship; #875 closed all 36 — four artifacts authored against
the verified OCSF 1.4.0 class list, the rest rebound to classes that exist —
and the ceiling test that lived here was replaced by the zero assertion
below. A new binding must ship its telemetry artifact in the same change.
"""
from __future__ import annotations

from pathlib import Path

from tools.lint_playbook_telemetry_refs import HARD, SOFT, check

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_no_hard_findings() -> None:
    """Every ref uses the namespaced spelling AND resolves to an artifact."""
    findings, summary = check(REPO_ROOT)
    hard = [f for f in findings if f.severity == "HARD"]
    assert not hard, "unresolvable telemetry refs:\n" + "\n".join(
        f"  {f.slug}/{f.where} [{f.code}] {f.message}" for f in hard
    )
    assert summary["hard"] == 0


def test_refs_are_actually_present() -> None:
    """Fixture sanity: a linter over zero refs would pass trivially."""
    _, summary = check(REPO_ROOT)
    assert summary["refs"] > 0
    assert summary["telemetry_artifacts"] > 0


def test_soft_set_is_empty() -> None:
    """#875 promoted the last SOFT code to HARD; nothing may demote silently.

    If a future change adds a genuinely-SOFT code, update this test with the
    reasoning — the point is that demotion is a decision, not a drive-by.
    """
    assert SOFT == ()
    _, summary = check(REPO_ROOT)
    assert summary["soft"] == 0


def test_finding_codes_are_partitioned() -> None:
    assert not set(HARD) & set(SOFT)
    findings, _ = check(REPO_ROOT)
    for f in findings:
        assert f.code in (HARD if f.severity == "HARD" else SOFT)
