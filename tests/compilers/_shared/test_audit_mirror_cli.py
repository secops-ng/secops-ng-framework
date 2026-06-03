"""Tests for ``compilers._shared.audit_mirror_cli`` (F-CR-04 CORE-LG-CLI).

Covers the two contracts the CLI must hold for the regenerate.sh
co-location pipeline:

* :func:`materialize` and ``main(--out)`` produce byte-identical output
  from the same input, and that output matches
  :func:`compilers._shared.observability.render_audit_mirror_module`.
* A second invocation overwrites the existing sibling with byte-identical
  content (the regenerate.sh idempotency contract: re-run + diff empty).

These tests intentionally do not touch the LangGraph emitter or any
golden file under ``examples/`` — that work lives in the EMITTER and
GOLDENS siblings of the CORE-LG split.

Sovereign-stack guard: the CLI imports only stdlib + the shared
observability helper; this test additionally asserts the rendered
source carries no vendor SDK substring and no hard-coded OTLP endpoint.
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import pytest

from compilers._shared import audit_mirror_cli
from compilers._shared.observability import render_audit_mirror_module


# ---------------------------------------------------------------------------
# materialize() — same input → byte-identical output
# ---------------------------------------------------------------------------


def test_materialize_writes_render_audit_mirror_module_bytes(tmp_path: Path) -> None:
    out = tmp_path / "_audit_mirror.py"
    returned = audit_mirror_cli.materialize(out)

    assert returned == out
    assert out.read_text(encoding="utf-8") == render_audit_mirror_module()


def test_materialize_is_deterministic_across_calls(tmp_path: Path) -> None:
    a = tmp_path / "a" / "_audit_mirror.py"
    b = tmp_path / "b" / "_audit_mirror.py"
    a.parent.mkdir(parents=True)
    b.parent.mkdir(parents=True)

    audit_mirror_cli.materialize(a)
    audit_mirror_cli.materialize(b)

    assert a.read_bytes() == b.read_bytes()


def test_materialize_is_idempotent(tmp_path: Path) -> None:
    """Re-running materialize() against the same path leaves zero diff."""
    out = tmp_path / "_audit_mirror.py"
    audit_mirror_cli.materialize(out)
    first = out.read_bytes()

    audit_mirror_cli.materialize(out)
    second = out.read_bytes()

    assert first == second


# ---------------------------------------------------------------------------
# main(--out) — same byte guarantee through the argparse entrypoint
# ---------------------------------------------------------------------------


def test_main_out_writes_byte_identical_to_helper(tmp_path: Path) -> None:
    out = tmp_path / "_audit_mirror.py"
    rc = audit_mirror_cli.main(["--out", str(out)])

    assert rc == 0
    assert out.read_text(encoding="utf-8") == render_audit_mirror_module()


def test_main_out_is_idempotent(tmp_path: Path) -> None:
    out = tmp_path / "_audit_mirror.py"
    assert audit_mirror_cli.main(["--out", str(out)]) == 0
    first = out.read_bytes()
    assert audit_mirror_cli.main(["--out", str(out)]) == 0
    second = out.read_bytes()
    assert first == second


def test_main_stdout_emits_helper_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = audit_mirror_cli.main([])
    captured = capsys.readouterr()

    assert rc == 0
    assert captured.out == render_audit_mirror_module()
    assert captured.err == ""


# ---------------------------------------------------------------------------
# Module CLI form — `python -m compilers._shared.audit_mirror_cli`
# ---------------------------------------------------------------------------


def test_module_invocation_writes_byte_identical_file(tmp_path: Path) -> None:
    """Calling the module via ``-m`` (as regenerate.sh does) is byte-identical."""
    out = tmp_path / "_audit_mirror.py"
    repo_root = Path(__file__).resolve().parents[3]

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compilers._shared.audit_mirror_cli",
            "--out",
            str(out),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == render_audit_mirror_module()


def test_module_invocation_is_idempotent(tmp_path: Path) -> None:
    """Two `python -m` invocations against the same path produce byte-identical output.

    This is the regenerate.sh contract: re-running the script leaves
    ``git diff`` empty on the sibling ``_audit_mirror.py``.
    """
    out = tmp_path / "_audit_mirror.py"
    repo_root = Path(__file__).resolve().parents[3]
    argv = [
        sys.executable,
        "-m",
        "compilers._shared.audit_mirror_cli",
        "--out",
        str(out),
    ]

    subprocess.run(argv, cwd=repo_root, check=True, capture_output=True)
    first = out.read_bytes()

    subprocess.run(argv, cwd=repo_root, check=True, capture_output=True)
    second = out.read_bytes()

    assert first == second


# ---------------------------------------------------------------------------
# Sovereign-stack guard
# ---------------------------------------------------------------------------


_FORBIDDEN_VENDOR_SUBSTRINGS = (
    # vendor SDK package roots that would couple the emitted mirror to a
    # specific tracing backend
    "datadog",
    "newrelic",
    "honeycomb",
    "lightstep",
    "splunk",
    "dynatrace",
    "elasticapm",
    # endpoint shapes that would hard-code an OTLP collector
    "http://otel",
    "https://otel",
    "http://collector",
    "https://collector",
    "4317",
    "4318",
)


def test_cli_source_has_no_vendor_substring() -> None:
    src = Path(audit_mirror_cli.__file__).read_text(encoding="utf-8")
    for needle in _FORBIDDEN_VENDOR_SUBSTRINGS:
        assert needle not in src, f"vendor/collector substring leaked into CLI: {needle!r}"


def test_rendered_module_has_no_vendor_substring() -> None:
    src = render_audit_mirror_module()
    for needle in _FORBIDDEN_VENDOR_SUBSTRINGS:
        assert needle not in src, f"vendor/collector substring leaked into mirror: {needle!r}"
