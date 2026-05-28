"""Exception hierarchy raised by the CACAO parser.

All errors derive from CacaoParseError so callers can catch the family with a
single except clause.  The two subclasses distinguish *what kind* of contract
was broken so emitters can surface useful diagnostics to the operator.

- CacaoSchemaError    — the JSON does not satisfy the playbook JSON Schema
                        (structural / type / pattern violations).
- CacaoSemanticError  — the JSON is schema-valid but breaks a cross-reference
                        invariant the schema can't express (e.g. `workflow_start`
                        names a step that isn't in `workflow`, an `on_completion`
                        edge points at a non-existent step, a step type is
                        unsupported by the AST surface).
"""

from __future__ import annotations


class CacaoParseError(Exception):
    """Base class for any parser failure. Callers SHOULD catch this."""


class CacaoSchemaError(CacaoParseError):
    """JSON Schema validation failed.

    ``errors`` carries the raw list of jsonschema ValidationError messages so
    downstream tooling can render rich diagnostics. ``args[0]`` is a single
    human-readable summary.
    """

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors: list[str] = list(errors or [])


class CacaoSemanticError(CacaoParseError):
    """Cross-reference / semantic invariant violated after schema validation."""
