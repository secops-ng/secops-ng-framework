"""Unit tests for the forward-public hygiene linter.

Each rule has a positive fixture (must produce findings) and a negative
fixture (must not produce findings). CLI behaviour is covered with
``runpy``-style invocations through the ``main`` entrypoint.
"""

from __future__ import annotations

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


# --- Finding dataclass ------------------------------------------------------


def test_finding_to_dict_serialises_severity_as_string() -> None:
    f = Finding(
        path="x", line=1, rule="r", severity=Severity.HIGH, message="m",
    )
    d = f.to_dict()
    assert d["severity"] == "HIGH"
    assert json.dumps(d)  # round-trips through JSON
