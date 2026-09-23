"""CACAO variable values are strings; n8n's initial-assignment slots are typed.

The emitter coerces integer, long and float strings into numbers for the
manual trigger's ``values`` block and passes everything else through, so a
playbook that says ``"value": "70"`` (the only shape the CACAO schema allows)
lands in n8n as the number 70.
"""
from __future__ import annotations

import pytest

from compilers.n8n.emit import _typed_variable_value


@pytest.mark.parametrize(
    ("cacao_type", "value", "expected"),
    [
        ("integer", "70", 70),
        ("long", " 42 ", 42),
        ("float", "0.5", 0.5),
        ("integer", "not-a-number", "not-a-number"),
        ("string", "70", "70"),
        ("boolean", "true", "true"),
        ("dictionary", None, ""),
        ("integer", 70, 70),
    ],
)
def test_typed_variable_value(cacao_type: str, value, expected) -> None:
    assert _typed_variable_value(cacao_type, value) == expected
