"""Schema-introspection tests for the alert-triage DSPy signature.

Asserts contract stability of the single free-text signature
(:class:`AnalystNarrativeSummary`) without instantiating a live
language model. Mirrors the F-WF-01 ``test_signatures.py`` shape so
contract drift across the two workflows is one diff away.

A separate test pins the lazy-import contract: importing
``content.playbooks.alert_triage.primitives`` does not pull ``dspy``
into ``sys.modules`` until a signature class is actually accessed.
"""

from __future__ import annotations

import importlib
import sys

import pytest

pytest.importorskip(
    "dspy",
    reason=(
        "dspy is an optional LM extra; the deterministic primitives "
        "(prioritisation, suppression, payloads) do not require it, "
        "but the signatures module under test does."
    ),
)


# ---------------------------------------------------------------------------
# Lazy-import contract
# ---------------------------------------------------------------------------


def test_primitives_package_does_not_eagerly_import_dspy() -> None:
    """Importing the primitives package must not pull dspy in.

    The deterministic primitives must be usable without the LM extras.
    Re-import the package fresh and assert ``dspy`` is absent from
    ``sys.modules`` until a signature is touched.
    """
    for name in list(sys.modules):
        if (
            name.startswith("content.playbooks.alert_triage.primitives")
            or name == "dspy"
        ):
            del sys.modules[name]

    importlib.import_module("content.playbooks.alert_triage.primitives")
    assert "dspy" not in sys.modules, (
        "Importing the primitives package must not eagerly import dspy; "
        "the signatures module is expected to defer the import until a "
        "signature class is accessed."
    )


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------


def _load_schema() -> dict[str, dict[str, str]]:
    from content.playbooks.alert_triage.primitives.signatures import (
        AnalystNarrativeSummary,
        signature_schema,
    )

    return signature_schema(AnalystNarrativeSummary)


class TestAnalystNarrativeSummarySchema:
    def test_input_fields(self) -> None:
        schema = _load_schema()
        assert list(schema["inputs"].keys()) == ["alert_envelope"]

    def test_output_fields_in_declaration_order(self) -> None:
        schema = _load_schema()
        assert list(schema["outputs"].keys()) == ["summary", "narrative"]

    def test_input_descriptions_nonempty(self) -> None:
        schema = _load_schema()
        for name, desc in schema["inputs"].items():
            assert desc.strip(), (
                f"AnalystNarrativeSummary.{name} input description "
                "must not be empty."
            )

    def test_output_descriptions_nonempty(self) -> None:
        schema = _load_schema()
        for name, desc in schema["outputs"].items():
            assert desc.strip(), (
                f"AnalystNarrativeSummary.{name} output description "
                "must not be empty."
            )

    def test_no_field_appears_as_both_input_and_output(self) -> None:
        schema = _load_schema()
        overlap = set(schema["inputs"]) & set(schema["outputs"])
        assert not overlap, (
            f"field(s) {sorted(overlap)!r} appear as both input and "
            "output — DSPy signature roles must be disjoint."
        )

    def test_signature_has_docstring(self) -> None:
        from content.playbooks.alert_triage.primitives.signatures import (
            AnalystNarrativeSummary,
        )

        assert (
            AnalystNarrativeSummary.__doc__
            and AnalystNarrativeSummary.__doc__.strip()
        ), (
            "AnalystNarrativeSummary must carry a docstring — DSPy uses "
            "it as the signature instruction."
        )

    def test_priority_is_not_a_signature_output(self) -> None:
        """The priority decision is deterministic code, not LM-backed.

        Pin this explicitly so a future refactor that tries to route
        priority through DSPy fails this test first.
        """
        schema = _load_schema()
        forbidden = {"priority", "__priority__", "priority_band"}
        leaked = forbidden & set(schema["outputs"])
        assert not leaked, (
            f"priority-shaped field(s) {sorted(leaked)!r} appear on "
            "the AnalystNarrativeSummary outputs; the priority "
            "decision must remain deterministic code, not LM-backed."
        )


# ---------------------------------------------------------------------------
# Public attribute hygiene
# ---------------------------------------------------------------------------


def test_unknown_attribute_raises_attribute_error() -> None:
    from content.playbooks.alert_triage.primitives import signatures

    with pytest.raises(AttributeError):
        signatures.NotASignature  # type: ignore[attr-defined]


def test_signature_schema_handles_empty_extras() -> None:
    from content.playbooks.alert_triage.primitives.signatures import (
        signature_schema,
    )

    class _Empty:
        model_fields: dict[str, object] = {}

    assert signature_schema(_Empty) == {"inputs": {}, "outputs": {}}
