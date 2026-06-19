"""Schema-introspection tests for the incident_management DSPy signature.

Mirrors the F-WF-03 ``test_signatures.py`` shape — contract drift
across the two workflows is one diff away.
"""

from __future__ import annotations

import importlib
import sys

import pytest

pytest.importorskip(
    "dspy",
    reason=(
        "dspy is an optional LM extra; the deterministic primitives "
        "(stage_clock, classification, regulator_submission, "
        "timeline_binding) do not require it, but the signatures "
        "module under test does."
    ),
)


def test_primitives_package_does_not_eagerly_import_dspy() -> None:
    for name in list(sys.modules):
        if (
            name.startswith(
                "content.playbooks.incident_management.primitives"
            )
            or name == "dspy"
        ):
            del sys.modules[name]

    importlib.import_module(
        "content.playbooks.incident_management.primitives"
    )
    assert "dspy" not in sys.modules, (
        "Importing the primitives package must not eagerly import "
        "dspy; the signatures module is expected to defer the import "
        "until a signature class is accessed."
    )


def _load_schema() -> dict[str, dict[str, str]]:
    from content.playbooks.incident_management.primitives.signatures import (
        FinalReportNarrative,
        signature_schema,
    )

    return signature_schema(FinalReportNarrative)


class TestFinalReportNarrativeSchema:
    def test_input_fields(self) -> None:
        schema = _load_schema()
        assert list(schema["inputs"].keys()) == ["incident_evidence"]

    def test_output_fields_in_declaration_order(self) -> None:
        schema = _load_schema()
        assert list(schema["outputs"].keys()) == [
            "narrative",
            "root_cause",
            "applied_mitigations",
        ]

    def test_input_descriptions_nonempty(self) -> None:
        schema = _load_schema()
        for name, desc in schema["inputs"].items():
            assert desc.strip(), (
                f"FinalReportNarrative.{name} input description must "
                "not be empty."
            )

    def test_output_descriptions_nonempty(self) -> None:
        schema = _load_schema()
        for name, desc in schema["outputs"].items():
            assert desc.strip(), (
                f"FinalReportNarrative.{name} output description must "
                "not be empty."
            )

    def test_no_field_appears_as_both_input_and_output(self) -> None:
        schema = _load_schema()
        overlap = set(schema["inputs"]) & set(schema["outputs"])
        assert not overlap, (
            f"field(s) {sorted(overlap)!r} appear as both input and "
            "output — DSPy signature roles must be disjoint."
        )

    def test_signature_has_docstring(self) -> None:
        from content.playbooks.incident_management.primitives.signatures import (
            FinalReportNarrative,
        )

        assert (
            FinalReportNarrative.__doc__
            and FinalReportNarrative.__doc__.strip()
        ), (
            "FinalReportNarrative must carry a docstring — DSPy uses "
            "it as the signature instruction."
        )

    def test_regulated_fields_are_not_signature_outputs(self) -> None:
        """Classification, stage clock, dispatch are deterministic code.

        Pin this explicitly so a future refactor that tries to route
        any regulated-decision field through DSPy fails this test.
        """
        schema = _load_schema()
        forbidden = {
            "significant",
            "cross_border",
            "stage",
            "destination",
            "due_at",
            "submitted_at",
            "opened_at",
            "on_time",
        }
        leaked = forbidden & set(schema["outputs"])
        assert not leaked, (
            f"regulated-decision field(s) {sorted(leaked)!r} appear "
            "on the FinalReportNarrative outputs; those decisions "
            "must remain deterministic code, not LM-backed."
        )


def test_unknown_attribute_raises_attribute_error() -> None:
    from content.playbooks.incident_management.primitives import (
        signatures,
    )

    with pytest.raises(AttributeError):
        signatures.NotASignature  # type: ignore[attr-defined]


def test_signature_schema_handles_empty_extras() -> None:
    from content.playbooks.incident_management.primitives.signatures import (
        signature_schema,
    )

    class _Empty:
        model_fields: dict[str, object] = {}

    assert signature_schema(_Empty) == {"inputs": {}, "outputs": {}}
