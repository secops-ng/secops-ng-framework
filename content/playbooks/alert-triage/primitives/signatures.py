"""DSPy signatures for the alert-triage playbook.

DSPy is used **only** for free-text fields per ``docs/FOUNDATION.md``
§LLM determinism. Prioritisation, suppression, and payload validation
are deterministic code; this module is the home for the LM-backed
field the triage CORE action body produces:

* :class:`AnalystNarrativeSummary` — summarise an enriched alert into
  an operator-facing one-line summary plus a short narrative paragraph
  for the case view. The priority decision is **not** carried on the
  signature output (that lives in :mod:`.prioritisation`), only the
  free-text fields a human analyst would otherwise hand-write.

``dspy`` is imported lazily so the rest of the primitives package
remains usable in environments where it is not installed. The
signature class is still a Pydantic v2 model under the hood (DSPy
3.x's ``Signature`` metaclass is a ``pydantic.BaseModel`` subclass),
so :func:`signature_schema` returns a stable contract dict by walking
the underlying ``model_fields`` — no live LM is instantiated and no
network call is made.

The schema-introspection helper mirrors the F-WF-01 shape so contract
tests across the two workflows read identically.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "AnalystNarrativeSummary",
    "signature_schema",
]


# ---------------------------------------------------------------------------
# Lazy dspy access
# ---------------------------------------------------------------------------


def _load_dspy() -> Any:
    """Import ``dspy`` on demand.

    Raises :class:`ImportError` with an actionable message if dspy is
    not installed. The rest of the primitives package does not import
    dspy at module load time so contributors who only need the
    deterministic helpers (prioritisation, suppression, payloads) are
    not forced to pull the LM extras.
    """
    try:
        import dspy  # noqa: PLC0415 — lazy import is intentional
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise ImportError(
            "dspy is required for alert-triage DSPy signatures; install "
            "the LM extras (`pip install dspy`) to use "
            "AnalystNarrativeSummary."
        ) from exc
    return dspy


# ---------------------------------------------------------------------------
# Signature factory
# ---------------------------------------------------------------------------


def _build_analyst_narrative_summary() -> type:
    dspy = _load_dspy()

    class AnalystNarrativeSummary(dspy.Signature):  # type: ignore[misc, valid-type]
        """Summarise an enriched alert into an operator-facing narrative.

        Input is the assembled alert envelope (the typed payload
        rendered to its operator-readable form, plus the telemetry
        evidence the enrichment step pulled in). Output is a one-line
        summary sized for queue rows, plus a short narrative paragraph
        for the case view.

        The priority decision is **deterministic code** and is not
        carried on this signature — the per-target compilers route the
        priority off the ``prioritise`` verdict, not off the LM
        output.
        """

        alert_envelope: str = dspy.InputField(
            desc=(
                "Operator-readable rendering of the typed alert payload "
                "plus the enrichment evidence. Verbatim — do not "
                "rewrite or interpret."
            ),
        )
        summary: str = dspy.OutputField(
            desc=(
                "One-line operator-facing summary of the alert, sized "
                "for the queue row (target ≤ 120 chars). Plain prose, "
                "no markdown."
            ),
        )
        narrative: str = dspy.OutputField(
            desc=(
                "Short narrative paragraph for the case view "
                "(2–4 sentences). Explains the alert in the operator's "
                "voice — what fired, what evidence backs it, what is "
                "worth checking first. No priority decision and no "
                "remediation recommendation."
            ),
        )

    return AnalystNarrativeSummary


# ---------------------------------------------------------------------------
# Public lazy attributes
# ---------------------------------------------------------------------------


def __getattr__(name: str) -> Any:
    if name == "AnalystNarrativeSummary":
        return _build_analyst_narrative_summary()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ---------------------------------------------------------------------------
# Schema introspection — the contract the tests pin against
# ---------------------------------------------------------------------------


def signature_schema(signature_cls: Any) -> dict[str, dict[str, str]]:
    """Introspect a DSPy signature into a stable, ordered schema dict.

    Returns ``{"inputs": {name: desc, ...}, "outputs": {name: desc, ...}}``,
    walking the underlying Pydantic v2 ``model_fields`` in declaration
    order. DSPy stores the field role (``"input"`` or ``"output"``) in
    the ``json_schema_extra`` payload under ``__dspy_field_type`` and
    the description under ``desc``; we read both and fall back to
    ``FieldInfo.description`` when ``desc`` is empty.

    No live language model is instantiated; this is a pure-Pydantic
    walk. Mirrors the F-WF-01 helper signature so contract tests across
    the two workflows read identically.
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
