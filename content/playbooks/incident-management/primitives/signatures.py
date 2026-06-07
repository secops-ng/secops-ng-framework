"""DSPy signatures for the incident-management playbook.

DSPy is used **only** for free-text fields per
``docs/FOUNDATION.md`` § LLM determinism. Stage-clock arithmetic,
significance / cross-border classification, regulator-submission
dispatch, and the F-PT-02 binding are all deterministic code; this
module is the home for the single LM-backed surface this workflow
takes — the three narrative fields on the one-month final-report
submission (NIS2 Article 23(4)(d)).

The signature class itself is the contract: a frozen
``dspy.Signature`` subclass with one structured input
(``incident_evidence``, the operator-assembled evidence rendering
the workflow has already gathered deterministically) and three
free-text outputs (``narrative``, ``root_cause``,
``applied_mitigations``). No hosted-SaaS default — the operator
picks the LM provider at the compile target's config layer; the
signature itself names no provider.

``dspy`` is imported lazily so the rest of the primitives package
remains usable in environments where dspy is not installed (the
deterministic primitives — stage-clock, classification,
regulator-submission contract, F-PT-02 binding — carry the rest of
the workflow). The schema-introspection helper mirrors the F-WF-03
shape so contract tests across the two workflows read identically.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "FinalReportNarrative",
    "signature_schema",
]


def _load_dspy() -> Any:
    """Import ``dspy`` on demand.

    Raises :class:`ImportError` with an actionable message if dspy is
    not installed. The rest of the primitives package does not import
    dspy at module load time, so contributors who only need the
    deterministic helpers (stage-clock, classification,
    regulator-submission contract, F-PT-02 binding) are not forced to
    pull the LM extras.
    """
    try:
        import dspy  # noqa: PLC0415 — lazy import is intentional
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise ImportError(
            "dspy is required for incident-management DSPy signatures; "
            "install the LM extras (`pip install dspy`) to use "
            "FinalReportNarrative."
        ) from exc
    return dspy


def _build_final_report_narrative() -> type:
    dspy = _load_dspy()

    class FinalReportNarrative(dspy.Signature):  # type: ignore[misc, valid-type]
        """Produce the free-text fields on the one-month final report.

        Input is the operator-assembled evidence rendering for the
        incident — verbatim, deterministic, gathered by the workflow
        ahead of this call. Output is the three narrative fields
        NIS2 Article 23(4)(d) requires: a detailed description of
        the incident, the type of threat or root cause, and the
        applied / ongoing mitigation measures.

        The classification flags (significance, cross-border) are
        **not** carried on this signature — they live in
        :mod:`.classification` as deterministic code. The
        regulator-submission dispatch (destination, timing) is also
        not on the signature — it lives in
        :mod:`.regulator_submission` and :mod:`.stage_clock` as
        deterministic code.
        """

        incident_evidence: str = dspy.InputField(
            desc=(
                "Operator-assembled evidence rendering for the "
                "incident: intake event, timeline of stages, "
                "classification verdict reasons, observed effects. "
                "Verbatim — do not rewrite or interpret."
            ),
        )
        narrative: str = dspy.OutputField(
            desc=(
                "Detailed description of the incident in the "
                "operator's voice (4–8 sentences). Plain prose, no "
                "markdown. Names what happened, in what order, on "
                "which surface; does not assign blame and does not "
                "prescribe future controls."
            ),
        )
        root_cause: str = dspy.OutputField(
            desc=(
                "Operator-readable root-cause description (2–4 "
                "sentences). Names the type of threat or the "
                "technical root cause as understood at the "
                "one-month gate. Plain prose, no markdown. If the "
                "root cause is not yet fully understood at the "
                "one-month gate, says so explicitly rather than "
                "speculating."
            ),
        )
        applied_mitigations: str = dspy.OutputField(
            desc=(
                "Summary of applied and ongoing mitigation measures "
                "(2–5 sentences). Lists the steps already taken "
                "and the steps still in flight. Plain prose, no "
                "markdown, no future-tense commitments beyond the "
                "next 30 days."
            ),
        )

    return FinalReportNarrative


def __getattr__(name: str) -> Any:
    if name == "FinalReportNarrative":
        return _build_final_report_narrative()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def signature_schema(signature_cls: Any) -> dict[str, dict[str, str]]:
    """Introspect a DSPy signature into a stable, ordered schema dict.

    Returns ``{"inputs": {name: desc, ...}, "outputs": {name: desc, ...}}``,
    walking the underlying Pydantic v2 ``model_fields`` in declaration
    order. DSPy stores the field role (``"input"`` or ``"output"``) in
    the ``json_schema_extra`` payload under ``__dspy_field_type`` and
    the description under ``desc``; we read both and fall back to
    ``FieldInfo.description`` when ``desc`` is empty.

    No live language model is instantiated; this is a pure-Pydantic
    walk. Mirrors the F-WF-03 helper so contract tests across the two
    workflows read identically.
    """
    inputs: dict[str, str] = {}
    outputs: dict[str, str] = {}

    fields = getattr(signature_cls, "fields", None)
    if fields is None:
        fields = getattr(signature_cls, "model_fields", {})

    for name, info in fields.items():
        extra = getattr(info, "json_schema_extra", None) or {}
        if callable(extra):
            schema: dict[str, Any] = {}
            extra(schema)
            extra = schema
        role = str(extra.get("__dspy_field_type", "")).lower()
        desc = str(
            extra.get("desc", "")
            or getattr(info, "description", "")
            or ""
        )
        if role == "input":
            inputs[name] = desc
        elif role == "output":
            outputs[name] = desc

    return {"inputs": inputs, "outputs": outputs}
