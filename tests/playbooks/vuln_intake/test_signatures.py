"""Schema-introspection tests for the vulnerability-intake DSPy signatures.

Asserts contract stability of the two free-text signatures
(:class:`ReporterNarrativeSummary`, :class:`AdvisoryExcerptSynthesis`)
without instantiating a live language model. The introspection helper
walks the underlying Pydantic v2 ``model_fields`` so these tests run
purely on the schema layer — no network calls, no LM provider
configuration, no ``dspy.configure`` side effects.

A separate test pins the lazy-import contract: importing
``content.playbooks.vuln_intake.primitives`` does not pull ``dspy``
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
        "(CVSS, EPSS, severity, dedup) do not require it, but the "
        "signatures module under test does."
    ),
)


# ---------------------------------------------------------------------------
# Lazy-import contract
# ---------------------------------------------------------------------------


def test_primitives_package_does_not_eagerly_import_dspy() -> None:
    """Importing the primitives package must not pull dspy in.

    Per the F-WF-01 gap inventory, the deterministic primitives must be
    usable without the LM extras. Re-import the package fresh and assert
    ``dspy`` is absent from ``sys.modules`` until a signature is touched.
    """
    for name in list(sys.modules):
        if name.startswith("content.playbooks.vuln_intake.primitives") or name == "dspy":
            del sys.modules[name]

    importlib.import_module("content.playbooks.vuln_intake.primitives")
    assert "dspy" not in sys.modules, (
        "Importing the primitives package must not eagerly import dspy; "
        "the signatures module is expected to defer the import until a "
        "signature class is accessed."
    )


# ---------------------------------------------------------------------------
# Schema introspection — input / output contract pins
# ---------------------------------------------------------------------------


def _load_schemas() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    from content.playbooks.vuln_intake.primitives.signatures import (
        AdvisoryExcerptSynthesis,
        ReporterNarrativeSummary,
        signature_schema,
    )

    return signature_schema(ReporterNarrativeSummary), signature_schema(
        AdvisoryExcerptSynthesis
    )


class TestReporterNarrativeSummarySchema:
    def test_input_fields(self) -> None:
        rep, _ = _load_schemas()
        assert list(rep["inputs"].keys()) == ["narrative"]

    def test_output_fields_in_declaration_order(self) -> None:
        rep, _ = _load_schemas()
        assert list(rep["outputs"].keys()) == ["summary", "indicators"]

    def test_input_descriptions_nonempty(self) -> None:
        rep, _ = _load_schemas()
        for name, desc in rep["inputs"].items():
            assert desc.strip(), (
                f"ReporterNarrativeSummary.{name} input description "
                "must not be empty; the operator-facing prompt depends "
                "on the field doc."
            )

    def test_output_descriptions_nonempty(self) -> None:
        rep, _ = _load_schemas()
        for name, desc in rep["outputs"].items():
            assert desc.strip(), (
                f"ReporterNarrativeSummary.{name} output description "
                "must not be empty; downstream operators read the desc."
            )


class TestAdvisoryExcerptSynthesisSchema:
    def test_input_fields(self) -> None:
        _, adv = _load_schemas()
        assert list(adv["inputs"].keys()) == ["advisory_excerpt"]

    def test_output_fields_in_declaration_order(self) -> None:
        _, adv = _load_schemas()
        assert list(adv["outputs"].keys()) == ["brief", "affected_components"]

    def test_input_descriptions_nonempty(self) -> None:
        _, adv = _load_schemas()
        for name, desc in adv["inputs"].items():
            assert desc.strip(), (
                f"AdvisoryExcerptSynthesis.{name} input description "
                "must not be empty."
            )

    def test_output_descriptions_nonempty(self) -> None:
        _, adv = _load_schemas()
        for name, desc in adv["outputs"].items():
            assert desc.strip(), (
                f"AdvisoryExcerptSynthesis.{name} output description "
                "must not be empty."
            )


# ---------------------------------------------------------------------------
# Cross-signature properties
# ---------------------------------------------------------------------------


class TestCrossSignatureContract:
    def test_no_field_appears_as_both_input_and_output(self) -> None:
        rep, adv = _load_schemas()
        for label, schema in (("reporter", rep), ("advisory", adv)):
            overlap = set(schema["inputs"]) & set(schema["outputs"])
            assert not overlap, (
                f"{label}: field(s) {sorted(overlap)!r} appear as both "
                "input and output — DSPy signature roles must be disjoint."
            )

    def test_signatures_have_docstrings(self) -> None:
        from content.playbooks.vuln_intake.primitives.signatures import (
            AdvisoryExcerptSynthesis,
            ReporterNarrativeSummary,
        )

        for cls in (ReporterNarrativeSummary, AdvisoryExcerptSynthesis):
            assert cls.__doc__ and cls.__doc__.strip(), (
                f"{cls.__name__} must carry a docstring — DSPy uses it as "
                "the signature instruction."
            )


# ---------------------------------------------------------------------------
# Public attribute hygiene
# ---------------------------------------------------------------------------


def test_unknown_attribute_raises_attribute_error() -> None:
    from content.playbooks.vuln_intake.primitives import signatures

    with pytest.raises(AttributeError):
        signatures.NotASignature  # type: ignore[attr-defined]


def test_signature_schema_handles_empty_extras() -> None:
    """``signature_schema`` should not crash on stripped-down inputs.

    Used as a defensive contract test so the introspection helper stays
    robust against minor DSPy upstream churn (e.g. an upstream change in
    where the ``__dspy_field_type`` extra is stored). The schema dict
    should still come back well-formed, even if empty.
    """
    from content.playbooks.vuln_intake.primitives.signatures import signature_schema

    class _Empty:
        model_fields: dict[str, object] = {}

    result = signature_schema(_Empty)
    assert result == {"inputs": {}, "outputs": {}}
