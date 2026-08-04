"""Unit tests for the forward-public hygiene linter.

Each rule has a positive fixture (must produce findings) and a negative
fixture (must not produce findings). CLI behaviour is covered with
``runpy``-style invocations through the ``main`` entrypoint.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.hygiene_linter.cli import main
from tools.hygiene_linter.findings import Finding, Severity, redact
from tools.hygiene_linter.rules import commercial, credentials

FIXTURES = Path(__file__).parent / "fixtures"


def _read(fixture: str) -> list[str]:
    return (FIXTURES / fixture).read_text().splitlines()


# --- credentials rule -------------------------------------------------------


def test_credentials_positive_fires_all_shapes() -> None:
    lines = _read("credentials_positive.txt")
    findings = list(credentials.scan("credentials_positive.txt", lines))
    rules_hit = {f.rule for f in findings}
    assert "credentials.aws_access_key" in rules_hit
    assert "credentials.github_token" in rules_hit
    assert "credentials.slack_token" in rules_hit
    # API_TOKEN / DATABASE_PASSWORD lines should hit py_constant via secret-named key
    assert "credentials.py_constant" in rules_hit
    # all credential findings are HIGH severity
    assert all(f.severity is Severity.HIGH for f in findings)


def test_credentials_env_style_assignment_fires() -> None:
    """Canonical .env-style line (no spaces around `=`) is flagged."""
    findings = list(credentials.scan("x", [
        "AWS_SECRET_ACCESS_KEY=aBcDeFgHiJkLmNoP",
    ]))
    rules_hit = {f.rule for f in findings}
    assert "credentials.env_assignment" in rules_hit


def test_credentials_python_constant_with_slug_value_not_flagged() -> None:
    """Python identifier-style constants (slugs) are not secrets."""
    findings = list(credentials.scan("x", [
        'TASK_QUEUE = "vulnerability-triage"',
        'MODEL = "openai/gpt-4o-mini"',
    ]))
    assert findings == [], f"unexpected findings: {findings}"


def test_credentials_positive_redacts_snippet() -> None:
    lines = _read("credentials_positive.txt")
    findings = list(credentials.scan("p.txt", lines))
    aws = next(f for f in findings if f.rule == "credentials.aws_access_key")
    # Snippet must not contain the full original token (20 chars).
    assert "AKIAIOSFODNN7EXAMPLE" not in aws.snippet
    assert "AKIA" in aws.snippet  # fingerprint is okay


def test_credentials_negative_silent() -> None:
    lines = _read("credentials_negative.txt")
    findings = list(credentials.scan("credentials_negative.txt", lines))
    assert findings == [], f"unexpected findings: {findings}"


def test_credentials_pem_header() -> None:
    findings = list(credentials.scan("x", [
        "-----BEGIN RSA PRIVATE KEY-----",
    ]))
    assert len(findings) == 1
    assert findings[0].rule == "credentials.private_key_pem"
    assert findings[0].severity is Severity.HIGH


def test_credentials_env_secret_named_key() -> None:
    """A secret-named key fires even on lower-entropy values."""
    findings = list(credentials.scan("x", [
        'AWS_SECRET_ACCESS_KEY=somelongishbutwordy',
    ]))
    assert any(f.rule == "credentials.env_assignment" for f in findings)


# --- commercial rule --------------------------------------------------------


def test_commercial_positive_fires() -> None:
    lines = _read("commercial_positive.txt")
    findings = list(commercial.scan("commercial_positive.txt", lines))
    rules_hit = {f.rule for f in findings}
    # Spot-check several of the patterns
    expected = {
        "commercial.pricing_language",
        "commercial.customer_language",
        "commercial.b2b_language",
        "commercial.consulting_language",
        "commercial.sales_language",
        "commercial.gtm_language",
        "commercial.client_reference",
        "commercial.revenue_language",
        "commercial.strategy_doc_reference",
    }
    missing = expected - rules_hit
    assert not missing, f"missing commercial hits: {missing}"
    assert all(f.severity is Severity.MEDIUM for f in findings)


def test_commercial_negative_silent() -> None:
    lines = _read("commercial_negative.txt")
    findings = list(commercial.scan("commercial_negative.txt", lines))
    assert findings == [], f"unexpected findings: {findings}"


# --- redact helper ----------------------------------------------------------


def test_redact_short_string_is_starred() -> None:
    assert redact("abc") == "***"


def test_redact_long_string_is_fingerprinted() -> None:
    out = redact("supersecretpassword")
    assert "supersecretpassword" not in out
    assert out.startswith("supe")
    assert "19 chars" in out


# --- CLI --------------------------------------------------------------------


def test_cli_exit_nonzero_on_high_finding(tmp_path: Path) -> None:
    (tmp_path / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n")
    rc = main([str(tmp_path), "--format", "json"])
    assert rc == 1


def test_cli_exit_zero_when_no_findings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "clean.md").write_text("# Welcome to the SecOps-NG community.\n")
    rc = main([str(tmp_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "no findings" in captured.out


def test_cli_medium_only_does_not_gate(tmp_path: Path) -> None:
    """MEDIUM commercial findings alone must not gate the default build."""
    (tmp_path / "doc.md").write_text("Our pricing tiers are competitive.\n")
    rc = main([str(tmp_path), "--format", "json"])
    assert rc == 0  # gate default is HIGH


def test_cli_json_output_is_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "x.txt").write_text("ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789ab\n")
    rc = main([str(tmp_path), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert rc == 1
    assert isinstance(data, list) and data
    assert data[0]["severity"] == "HIGH"
    assert data[0]["rule"] == "credentials.github_token"


def test_cli_gate_severity_lowered_to_medium_blocks_on_commercial(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text("Our pricing tiers are competitive.\n")
    rc = main([str(tmp_path), "--gate-severity", "MEDIUM"])
    assert rc == 1


def test_cli_excludes_skip_paths(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "fixture.txt").write_text("AKIAIOSFODNN7EXAMPLE\n")
    rc = main([str(tmp_path), "--exclude", "tests/*"])
    assert rc == 0


def test_cli_skips_binary_files(tmp_path: Path) -> None:
    (tmp_path / "bin.dat").write_bytes(b"AKIAIOSFODNN7EXAMPLE\x00\x01\x02")
    rc = main([str(tmp_path)])
    assert rc == 0


def test_cli_module_entrypoint_runs(tmp_path: Path) -> None:
    """``python -m tools.hygiene_linter`` is the documented invocation."""
    (tmp_path / "clean.txt").write_text("community framework\n")
    proc = subprocess.run(
        [sys.executable, "-m", "tools.hygiene_linter", str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "no findings" in proc.stdout


# --- scan scope -------------------------------------------------------------
#
# The linter must be clean on the repository it lives in. It was not: a bare
# root run reported 24 HIGH credential findings — this suite's own planted
# fixtures, plus a second copy of them from a git worktree under
# .claude/worktrees/ — and exited 1. CI passed only because the workflow
# carried an `--exclude` the documented local command does not, so the command
# contributors are told to run before every PR was the broken one.


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_root_scan_passes_the_gate() -> None:
    """A bare scan of this repository must exit 0.

    This is the command CLAUDE.md requires before a framework PR. If it fails
    here, either a real HIGH-severity leak has landed — in which case fix the
    leak, not this test — or the scan scope has regressed again.
    """
    rc = main([str(REPO_ROOT), "--format", "json"])
    assert rc == 0


def test_self_test_corpus_excluded_without_any_flag() -> None:
    """The fixtures are skipped intrinsically, not via a CI-only flag.

    Passing --min-severity LOW is the strongest form of the check: it would
    surface the MEDIUM commercial fixtures too, if they were being read.
    """
    from tools.hygiene_linter.cli import _iter_files

    scanned = {p.resolve() for p in _iter_files([REPO_ROOT], [])}
    corpus = (REPO_ROOT / "tests" / "hygiene_linter").resolve()
    assert not [p for p in scanned if corpus in p.parents], (
        "the linter is reading its own positive fixtures again"
    )
    # sanity: the walk still reaches real content
    assert (REPO_ROOT / "ROADMAP.md").resolve() in scanned


@pytest.mark.parametrize(
    "marker_is_dir",
    [pytest.param(False, id="worktree-or-submodule-git-file"),
     pytest.param(True, id="clone-git-directory")],
)
def test_nested_checkout_is_pruned(tmp_path: Path, marker_is_dir: bool) -> None:
    """A subtree carrying its own .git belongs to another checkout.

    A worktree and a submodule mark themselves with a ``.git`` *file*; a clone
    uses a directory. Both must prune, or an agent working in a worktree sees
    every finding twice.
    """
    nested = tmp_path / "wt" / "copy"
    nested.mkdir(parents=True)
    if marker_is_dir:
        (nested / ".git").mkdir()
    else:
        (nested / ".git").write_text("gitdir: /elsewhere/.git/worktrees/copy\n")
    (nested / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n")

    assert main([str(tmp_path), "--format", "json"]) == 0

    # the same file outside a nested checkout still fires, so the prune is
    # scoped to the marker and has not silently disabled the rule
    (tmp_path / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n")
    assert main([str(tmp_path), "--format", "json"]) == 1


def test_scan_root_itself_is_never_pruned_for_being_a_checkout(tmp_path: Path) -> None:
    """Only *nested* checkouts prune — pointing the linter at a repo root
    must still scan it, or scanning any clone would return nothing."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n")
    assert main([str(tmp_path), "--format", "json"]) == 1


def test_egg_info_directory_is_pruned(tmp_path: Path) -> None:
    """The module docstring has always promised this; now it is true."""
    egg = tmp_path / "secops_ng.egg-info"
    egg.mkdir()
    (egg / "SOURCES.txt").write_text("AKIAIOSFODNN7EXAMPLE\n")
    assert main([str(tmp_path), "--format", "json"]) == 0


# --- inline suppression pragmas ---------------------------------------------
#
# #892: two files must contain the vocabulary the commercial rules detect —
# the rule definitions themselves, and SOUL.md quoting the phrasing it warns
# against. They stood as 15 permanent MEDIUM findings, a floor a reviewer had
# to remember was "normal". Pragmas exempt them by name; the tests below pin
# the properties that keep that from becoming a way to silence real findings.


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def _findings(target: Path) -> list[dict]:
    """Scan ``target`` at the lowest severity and return parsed findings.

    Captures stdout directly rather than taking ``capsys``, so the assertions
    below read as one expression per test.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main([str(target), "--min-severity", "LOW", "--format", "json"])
    return json.loads(buf.getvalue())


def test_line_pragma_suppresses_its_own_line(tmp_path: Path) -> None:
    _write(tmp_path, "d.md",
           "Our customers matter.  <!-- hygiene-linter: allow commercial.customer_language -->\n")
    assert main([str(tmp_path), "--min-severity", "LOW", "--format", "json"]) == 0
    assert not _findings(tmp_path)


def test_line_pragma_suppresses_the_following_line(tmp_path: Path) -> None:
    """So a pragma can sit above a line with no room for a trailing comment."""
    _write(tmp_path, "d.md",
           "<!-- hygiene-linter: allow commercial.revenue_language -->\n"
           "Revenue framing appears here.\n")
    assert not _findings(tmp_path)


def test_line_pragma_does_not_reach_two_lines_down(tmp_path: Path) -> None:
    _write(tmp_path, "d.md",
           "<!-- hygiene-linter: allow commercial.revenue_language -->\n"
           "nothing to see\n"
           "Revenue framing appears here.\n")
    assert [f["line"] for f in _findings(tmp_path)] == [3]


def test_pragma_is_rule_specific_not_a_wildcard(tmp_path: Path) -> None:
    """Naming one rule must not exempt a different rule on the same line."""
    _write(tmp_path, "d.md",
           "Our customers and our pricing.  "
           "<!-- hygiene-linter: allow commercial.customer_language -->\n")
    rules = {f["rule"] for f in _findings(tmp_path)}
    assert rules == {"commercial.pricing_language"}


def test_pragma_cannot_suppress_a_high_finding(tmp_path: Path) -> None:
    """The property that makes this mechanism safe: a credential pragma is inert.

    HIGH findings are irreversible leaks once public, so no pragma may hide
    one — otherwise this becomes the easiest way to land a key.
    """
    _write(tmp_path, "leak.txt",
           "AKIAIOSFODNN7EXAMPLE  # hygiene-linter: allow credentials.aws_access_key\n")
    assert main([str(tmp_path), "--format", "json"]) == 1
    assert [f["rule"] for f in _findings(tmp_path)] == ["credentials.aws_access_key"]


def test_file_pragma_suppresses_throughout_the_file(tmp_path: Path) -> None:
    _write(tmp_path, "m.py",
           "# hygiene-linter: allow-file commercial.revenue_language\n"
           + "x = 1\n" * 40
           + "# revenue framing far below the header\n")
    assert not _findings(tmp_path)


def test_file_pragma_below_the_header_is_ignored(tmp_path: Path) -> None:
    """Kept in the header so a reader meets it, rather than buried mid-file."""
    _write(tmp_path, "m.py",
           "x = 1\n" * 25
           + "# hygiene-linter: allow-file commercial.revenue_language\n"
           + "# revenue framing here\n")
    assert [f["rule"] for f in _findings(tmp_path)] == ["commercial.revenue_language"]


def test_file_pragma_is_still_rule_specific(tmp_path: Path) -> None:
    _write(tmp_path, "m.py",
           "# hygiene-linter: allow-file commercial.revenue_language\n"
           "# revenue and B2B framing\n")
    assert [f["rule"] for f in _findings(tmp_path)] == ["commercial.b2b_language"]


def test_repo_root_scan_is_clean_at_lowest_severity() -> None:
    """Stronger than the gate check: zero findings at --min-severity LOW.

    Before #892 this reported 15 MEDIUM findings that were all legitimate
    content. A standing floor is what hides the next real finding, so the
    floor is now zero and this test keeps it there.
    """
    findings = _findings(REPO_ROOT)
    assert findings == [], f"repo root is no longer clean at LOW: {findings}"


# --- Finding dataclass ------------------------------------------------------


def test_finding_to_dict_serialises_severity_as_string() -> None:
    f = Finding(
        path="x", line=1, rule="r", severity=Severity.HIGH, message="m",
    )
    d = f.to_dict()
    assert d["severity"] == "HIGH"
    assert json.dumps(d)  # round-trips through JSON
