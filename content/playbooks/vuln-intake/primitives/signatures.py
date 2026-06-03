"""DSPy signatures for the vulnerability intake playbook.

DSPy is used **only** for free-text fields (reporter narrative summarisation,
advisory excerpt synthesis) per FOUNDATION.md §LLM determinism. Severity is
deterministic code; see :mod:`.severity`.

This module imports ``dspy`` lazily so the rest of the primitives package
remains usable in environments where ``dspy`` is not installed. Tests
introspect the signature schema via :func:`signature_schema` without
instantiating a live LM.

Signatures defined here:

* :class:`ReporterNarrativeSummary` — summarise a free-text reporter
  disclosure into a fixed-shape Pydantic-friendly output (one-line summary
  plus extracted indicators).
* :class:`AdvisoryExcerptSynthesis` — synthesise a vendor-advisory excerpt
  into a one-paragraph operator-facing brief.
"""

from __future__ import annotations

from typing import Any


def _load_dspy() -> Any:
    """Import dspy on demand.

    Raises :class:`ImportError` with a clear message if dspy is not installed.
    """
    try:
        import dspy  # noqa: PLC0415 — lazy import is intentional
    except ImportError as exc:  # pragma: no cover - import-error path is environment-dependent
        raise ImportError(
            "dspy is required for vuln-intake DSPy signatures; "
            "install the LM extras to use ReporterNarrativeSummary / AdvisoryExcerptSynthesis"
        ) from exc
    return dspy


def _build_reporter_narrative_summary() -> type:
    dspy = _load_dspy()

    class ReporterNarrativeSummary(dspy.Signature):  # type: ignore[misc, valid-type]
        """Summarise a free-text vulnerability disclosure narrative.

        Input is the verbatim reporter narrative as received through the
        coordinated-disclosure channel; output is a one-line summary plus a
        short list of indicators extracted from the narrative. The summary is
        used downstream in the CRA Article 14 early-warning submission and in
        operator-facing case views.
        """

        narrative: str = dspy.InputField(
            desc="Verbatim reporter narrative as received through the CVD channel."
        )
        summary: str = dspy.OutputField(
            desc="One-line operator-facing summary of the disclosure."
        )
        indicators: str = dspy.OutputField(
            desc=(
                "Newline-separated indicators extracted from the narrative "
                "(CVE ids, affected component names, observed exploit signals). "
                "Empty string when none are present."
            )
        )

    return ReporterNarrativeSummary


def _build_advisory_excerpt_synthesis() -> type:
    dspy = _load_dspy()

    class AdvisoryExcerptSynthesis(dspy.Signature):  # type: ignore[misc, valid-type]
        """Synthesise a vendor-advisory excerpt into an operator-facing brief.

        Input is the raw excerpt from a vendor or CSIRT advisory; output is a
        one-paragraph brief sized for the operator's case view, plus the list
        of affected component identifiers (PURLs or vendor identifiers) that
        the triage step will correlate against the SBOM.
        """

        advisory_excerpt: str = dspy.InputField(
            desc="Raw vendor / CSIRT advisory excerpt."
        )
        brief: str = dspy.OutputField(
            desc="One-paragraph operator-facing brief synthesising the advisory."
        )
        affected_components: str = dspy.OutputField(
            desc=(
                "Newline-separated affected component identifiers (PURLs or "
                "vendor identifiers). Empty string when the advisory does not "
                "enumerate components."
            )
        )

    return AdvisoryExcerptSynthesis


# Public attribute hooks — accessing either name triggers the lazy build.
def __getattr__(name: str) -> Any:
    if name == "ReporterNarrativeSummary":
        return _build_reporter_narrative_summary()
    if name == "AdvisoryExcerptSynthesis":
        return _build_advisory_excerpt_synthesis()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def signature_schema(signature_cls: Any) -> dict[str, dict[str, str]]:
    """Introspect a DSPy signature into a stable schema dict.

    Returns ``{"inputs": {name: desc, ...}, "outputs": {name: desc, ...}}``.
    Used by the unit tests to assert the signature shape without instantiating
    a live LM. Order is preserved.
    """
    inputs: dict[str, str] = {}
    outputs: dict[str, str] = {}
    fields = getattr(signature_cls, "fields", None)
    if fields is None:
        # Fall back to model_fields on the underlying Pydantic model.
        fields = getattr(signature_cls, "model_fields", {})
    for name, info in fields.items():
        # dspy stores the field role in the json_schema_extra under
        # ``__dspy_field_type`` ("input" or "output"). Fall back to the
        # ``desc`` extra for the description.
        extra = getattr(info, "json_schema_extra", None) or {}
        if callable(extra):
            # Pydantic v2 callable extra — call with empty dict to materialise.
            schema: dict[str, Any] = {}
            extra(schema)
            extra = schema
        role = str(extra.get("__dspy_field_type", "")).lower()
        desc = str(extra.get("desc", "") or getattr(info, "description", "") or "")
        if role == "input":
            inputs[name] = desc
        elif role == "output":
            outputs[name] = desc
    return {"inputs": inputs, "outputs": outputs}
