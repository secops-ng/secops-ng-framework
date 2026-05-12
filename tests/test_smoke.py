"""Smoke test — keeps CI honest from day one."""

from __future__ import annotations


def test_package_imports_and_has_version() -> None:
    """The package must import cleanly and expose a non-empty __version__."""
    import secops_ng

    assert hasattr(secops_ng, "__version__")
    assert isinstance(secops_ng.__version__, str)
    assert secops_ng.__version__  # non-empty
