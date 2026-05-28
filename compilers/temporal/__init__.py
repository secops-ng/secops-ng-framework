"""Temporal (Python SDK) reference compiler for SecOps-NG CACAO v2 playbooks.

Public API re-exported from :mod:`compilers.temporal.emit`. See that module
for the contract and scope of the stub emitter.
"""
from __future__ import annotations

from .emit import DEFAULT_HEADER, emit, emit_file

__all__ = ["DEFAULT_HEADER", "emit", "emit_file"]
