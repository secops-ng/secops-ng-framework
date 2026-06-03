"""DSPy signatures for the vulnerability-intake playbook.

DSPy is used **only** for free-text fields per ``docs/FOUNDATION.md``
§LLM determinism. Severity, dedup, CVSS, and EPSS are deterministic
code; this module is the exhaustive home for the LM-backed fields the
vuln-intake CORE action bodies need:

* :class:`ReporterNarrativeSummary` — summarise a free-text reporter
  disclosure into a fixed-shape output (one-line summary plus newline-
  separated indicators).
* :class:`AdvisoryExcerptSynthesis` — synthesise a vendor or CSIRT
  advisory excerpt into a one-paragraph operator-facing brief plus
  newline-separated affected component identifiers.

``dspy`` is imported lazily so the rest of the primitives package
remains usable in environments where it is not installed (the per-
target compilers can read other primitives without forcing the LM
extras onto contributors). The signatures themselves are still
**Pydantic v2 models under the hood** (DSPy 3.x's ``Signature``
metaclass is a ``pydantic.BaseModel`` subclass), so the schema
introspection helper :func:`signature_schema` returns a stable contract
dict by walking the underlying ``model_fields`` — no live language
model is instantiated and no network call is made.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "AdvisoryExcerptSynthesis",
    "ReporterNarrativeSummary",
    "signature_schema",
]


# ---------------------------------------------------------------------------
# Lazy dspy access
# ---------------------------------------------------------------------------


def _load_dspy() -> Any:
    """Import ``dspy`` on demand.

    Raises :class:`ImportError` with an actionable message if dspy is not
    installed. The rest of the primitives package does not import dspy at
    module load time so contributors who only need the deterministic
    helpers (CVSS, EPSS, severity, dedup) are not forced to pull the LM
    extras.
    """
    try:
        import dspy  # noqa: PLC0415 — lazy import is intentional
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise ImportError(
            "dspy is required for vuln-intake DSPy signatures; install the "
            "LM extras (`pip install dspy`) to use ReporterNarrativeSummary "
            "or AdvisoryExcerptSynthesis."
        ) from exc
    return dspy


# ---------------------------------------------------------------------------
# Signature factories
# ---------------------------------------------------------------------------
#
# DSPy signatures are built lazily inside factory functions so importing
# this module does not trigger the dspy import. Module-level ``__getattr__``
# binds the public class names to the factory output on first access.


def _build_reporter_narrative_summary() -> type:
    dspy = _load_dspy()

    class ReporterNarrativeSummary(dspy.Signature):  # type: ignore[misc, valid-type]
        """Summarise a free-text vulnerability-disclosure narrative.

        Input is the verbatim reporter narrative as received through the
        coordinated-disclosure channel; output is a one-line operator
        summary plus a newline-separated list of indicators extracted
        from the narrative. The summary feeds downstream into the
        CRA Article 14 early-warning submission and the operator-facing
        case view.
        """

        narrative: str = dspy.InputField(
            desc="Verbatim reporter narrative as received through the CVD channel.",
        )
        summary: str = dspy.OutputField(
            desc="One-line operator-facing summary of the disclosure.",
        )
        indicators: str = dspy.OutputField(
            desc=(
                "Newline-separated indicators extracted from the narrative "
                "(CVE ids, affected component names, observed exploit "
                "signals). Empty string when none are present."
            ),
        )

    return ReporterNarrativeSummary


def _build_advisory_excerpt_synthesis() -> type:
    dspy = _load_dspy()

    class AdvisoryExcerptSynthesis(dspy.Signature):  # type: ignore[misc, valid-type]
        """Synthesise a vendor or CSIRT advisory excerpt into an operator brief.

        Input is the raw excerpt from a vendor or CSIRT advisory; output
        is a one-paragraph brief sized for the operator's case view, plus
        the list of affected component identifiers (PURLs or vendor
        identifiers) that the triage step will correlate against the SBOM.
        """

        advisory_excerpt: str = dspy.InputField(
            desc="Raw vendor or CSIRT advisory excerpt.",
        )
        brief: str = dspy.OutputField(
            desc="One-paragraph operator-facing brief synthesising the advisory.",
        )
        affected_components: str = dspy.OutputField(
            desc=(
                "Newline-separated affected component identifiers (PURLs or "
                "vendor identifiers). Empty string when the advisory does "
                "not enumerate components."
            ),
        )

    return AdvisoryExcerptSynthesis


# ---------------------------------------------------------------------------
# Public lazy attributes
# ---------------------------------------------------------------------------


def __getattr__(name: str) -> Any:
    if name == "ReporterNarrativeSummary":
        return _build_reporter_narrative_summary()
    if name == "AdvisoryExcerptSynthesis":
        return _build_advisory_excerpt_synthesis()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ---------------------------------------------------------------------------
# Schema introspection — the contract the tests pin against
# ---------------------------------------------------------------------------


def signature_schema(signature_cls: Any) -> dict[str, dict[str, str]]:
    """Introspect a DSPy signature into a stable, ordered schema dict.

    Returns ``{"inputs": {name: desc, ...}, "outputs": {name: desc, ...}}``,
    walking the underlying Pydantic v2 ``model_fields`` in declaration order.
    DSPy stores the field role (``"input"`` or ``"output"``) in the
    ``json_schema_extra`` payload under the ``__dspy_field_type`` key and
    the human-readable description under ``desc``; we read both and fall
    back to ``FieldInfo.description`` when ``desc`` is empty.

    No live language model is instantiated; this is a pure-Pydantic walk.
    The unit tests use this to assert contract stability without pulling
    a network dependency into the test matrix.
    """
    inputs: dict[str, str] = {}
    outputs: dict[str, str] = {}

    # DSPy 3.x signatures are Pydantic BaseModel subclasses, so
    # ``model_fields`` is always present and ordered. Older releases
    # exposed a ``fields`` attribute; check it first for forward / back
    # compatibility.
    fields = getattr(signature_cls, "fields", None)
    if fields is None:
        fields = getattr(signature_cls, "model_fields", {})

    for name, info in fields.items():
        extra = getattr(info, "json_schema_extra", None) or {}
        if callable(extra):
            # Pydantic v2 callable extra — materialise by calling with
            # an empty dict and reading the populated payload back out.
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
