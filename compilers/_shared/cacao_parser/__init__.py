"""Shared CACAO v2 playbook parser + AST for the SecOps-NG reference compilers.

This package is the single ingest path used by every reference compiler
(`compilers/n8n`, `compilers/temporal`, `compilers/langgraph`). It accepts a
CACAO v2 playbook (the SecOps-NG superset, see
`content-model/playbook.schema.json`) and returns an in-memory AST built from
plain frozen dataclasses. The AST is the only contract downstream emitters
depend on — they MUST NOT re-parse the raw JSON.

This module is parse + validate only. It emits nothing.

Quick start::

    from compilers._shared.cacao_parser import parse, parse_file

    playbook = parse_file("content/playbooks/vuln-intake/playbook.cacao.json")
    for step_id, step in playbook.workflow.items():
        ...

Public API:
    - parse(data: dict) -> Playbook
    - parse_file(path: str | Path) -> Playbook
    - Playbook, WorkflowStep, Variable, SecOpsExtensions, StepSecOpsExtensions
    - StepType (enum)
    - CacaoParseError, CacaoSchemaError, CacaoSemanticError
"""

from __future__ import annotations

from .ast import (
    CoreBody,
    Playbook,
    SecOpsExtensions,
    StepSecOpsExtensions,
    StepType,
    Variable,
    WorkflowStep,
)
from .errors import CacaoParseError, CacaoSchemaError, CacaoSemanticError
from .parser import parse, parse_file

__all__ = [
    "CacaoParseError",
    "CacaoSchemaError",
    "CacaoSemanticError",
    "CoreBody",
    "Playbook",
    "SecOpsExtensions",
    "StepSecOpsExtensions",
    "StepType",
    "Variable",
    "WorkflowStep",
    "parse",
    "parse_file",
]
