"""Supply-chain evidence-artifact builder primitive (emit-supply-chain-
evidence).

Builds the JSON-native supply-chain-evidence record by wiring through
the F-CP-03 shared emitter at
:mod:`compilers._shared.evidence.supply_chain` (schema:
``schemas/evidence/supply-chain.schema.json``, stream:
``supply-chain``). The deterministic ``artifact_id`` derives from
``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per the
schema contract.

This primitive owns the JSON-native ↔ dataclass marshalling so the
playbook's CACAO action body stays portable (n8n Code node, Temporal
activity, LangGraph node all marshal identically). The shared emitter
is the schema gate; this primitive is the supply-chain-security-side
join that pins the assessed-supplier integrity guarantee: the closed
assessment block produced upstream by :func:`...primitives.assess.
assess_supplier_signal` MUST reference a supplier whose ``provider_id``
appears among the declared ``dependencies[]`` on this execution, so
the artifact actually documents the implicated surface. A signal that
points at a supplier the operator has never declared as a dependency
fails loud here rather than producing a silently-orphaned artifact.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  ``captured_at`` timestamp is supplied by the caller; the upstream
  workflow runtime is the source of truth.
* **Determinism.** Same inputs ⇒ byte-identical output. Same
  ``(workflow_id, execution_id, captured_at)`` ⇒ same ``artifact_id``.
* **Public-bar safe.** All identifiers re-validated through the
  shared emitter's regex gates so a personal-name or
  credential-shaped string fails loud before any I/O.

The primitive only produces the JSON-native record. Durable emitter
wiring (artifact-path, content-addressed filename, atomic write) is
owned by the per-target adapters under
``compilers.{n8n,temporal,langgraph}.evidence`` and lands with the
CORE-FANOUT sibling card.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from compilers._shared.evidence.supply_chain import (
    Aggregates,
    Attestation,
    Dependency,
    EmitError,
    SovereigntyClassification,
    SupplyChainContext,
    render_supply_chain_artifact,
)

__all__ = [
    "InvalidSupplyChainEvidenceArtifactError",
    "build_supply_chain_evidence_artifact",
]


_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class InvalidSupplyChainEvidenceArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _parse_iso_z(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not _ISO_Z_RE.match(value):
        raise InvalidSupplyChainEvidenceArtifactError(
            f"{field} {value!r} is not ISO-8601 UTC "
            "'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def _require_dict(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise InvalidSupplyChainEvidenceArtifactError(
            f"{field} must be an object, got {type(value).__name__}"
        )
    return value


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidSupplyChainEvidenceArtifactError(
            f"{field} must be a non-empty string, got "
            f"{type(value).__name__}"
        )
    return value


def _build_classification(
    raw: dict, where: str
) -> SovereigntyClassification:
    sub_chain = raw.get("sub_processor_chain")
    if sub_chain is not None:
        if not isinstance(sub_chain, list):
            raise InvalidSupplyChainEvidenceArtifactError(
                f"{where}.sub_processor_chain must be a list when "
                "present"
            )
        sub_chain = tuple(sub_chain)
    return SovereigntyClassification(
        residency=_require_str(raw.get("residency"), f"{where}.residency"),
        ownership=_require_str(raw.get("ownership"), f"{where}.ownership"),
        sovereignty_band=_require_str(
            raw.get("sovereignty_band"), f"{where}.sovereignty_band"
        ),
        sub_processor_chain=sub_chain,
        band_rationale=raw.get("band_rationale"),
        kb_ref=raw.get("kb_ref"),
    )


def _build_attestation(raw: dict, where: str) -> Attestation:
    return Attestation(
        state=_require_str(raw.get("state"), f"{where}.state"),
        last_reattested_at=_parse_iso_z(
            raw.get("last_reattested_at"),
            f"{where}.last_reattested_at",
        ),
        next_due_at=_parse_iso_z(
            raw.get("next_due_at"), f"{where}.next_due_at"
        ),
        attestation_ref=raw.get("attestation_ref"),
    )


def _build_dependency(raw: dict, idx: int) -> Dependency:
    where = f"dependencies[{idx}]"
    _require_dict(raw, where)
    call_count = raw.get("call_count")
    if not isinstance(call_count, int) or isinstance(call_count, bool):
        raise InvalidSupplyChainEvidenceArtifactError(
            f"{where}.call_count must be an integer"
        )
    cls_raw = _require_dict(
        raw.get("sovereignty_classification"),
        f"{where}.sovereignty_classification",
    )
    att_raw = _require_dict(
        raw.get("attestation"), f"{where}.attestation"
    )
    return Dependency(
        provider_id=_require_str(
            raw.get("provider_id"), f"{where}.provider_id"
        ),
        kind=_require_str(raw.get("kind"), f"{where}.kind"),
        call_count=call_count,
        sovereignty_classification=_build_classification(
            cls_raw, f"{where}.sovereignty_classification"
        ),
        attestation=_build_attestation(att_raw, f"{where}.attestation"),
        version=raw.get("version"),
        risk_notes=raw.get("risk_notes"),
    )


def _build_aggregates(raw: object) -> Aggregates | None:
    if raw is None:
        return None
    data = _require_dict(raw, "aggregates")
    return Aggregates(
        total_providers=data.get("total_providers"),
        sovereign_count=data.get("sovereign_count"),
        eu_hosted_count=data.get("eu_hosted_count"),
        non_eu_count=data.get("non_eu_count"),
        ai_provider_count=data.get("ai_provider_count"),
    )


def _validate_assessment_join(
    assessment: dict, dependencies: list[Dependency]
) -> None:
    """Pin the SCS-side join: the assessed supplier must be declared.

    The assessment block produced by ``assess_supplier_signal`` carries
    an ``affected_supplier_handle`` in ``provider.<id>@v<n>`` shape.
    The supply-chain-evidence artifact this primitive emits is the
    F-CP-03 audit-trail record for that execution; if the implicated
    supplier is not in the declared dependency surface, the artifact
    would document a different surface than the one the signal points
    at — a silent-orphan failure mode. Reject up front.
    """
    handle = assessment.get("affected_supplier_handle")
    if not isinstance(handle, str) or not handle:
        raise InvalidSupplyChainEvidenceArtifactError(
            "assessment.affected_supplier_handle is missing or empty; "
            "the upstream assess-supplier-signal primitive should have "
            "produced a provider.<id>@v<n>-shaped handle"
        )
    declared = {dep.provider_id for dep in dependencies}
    if handle not in declared:
        raise InvalidSupplyChainEvidenceArtifactError(
            f"assessment.affected_supplier_handle {handle!r} is not "
            "among the declared dependencies on this execution "
            f"({sorted(declared)!r}); the artifact would document a "
            "surface that does not include the implicated supplier"
        )


def build_supply_chain_evidence_artifact(
    workflow_id: str,
    execution_id: str,
    regulation_refs: list,
    control_refs: list,
    assessment: dict,
    dependencies: list,
    owner_role: str,
    owner_assigned_at: str,
    captured_at: str,
    source_url: str,
    aggregates: dict | None = None,
    commit_sha: str | None = None,
    retention: str | None = None,
) -> dict[str, Any]:
    """Build the supply-chain-evidence record.

    Inputs are JSON-native — the playbook's CACAO action body marshals
    the same dict shape on every compile target.

    Parameters
    ----------
    workflow_id
        Stable lower-snake-case workflow stable-id; pinned to
        ``supply_chain_security`` for this playbook.
    execution_id
        Per-execution identifier from the compile target's runtime.
    regulation_refs
        Schema-shaped reference list (e.g. ``["nis2:art-21-2-d"]``).
    control_refs
        Schema-shaped reference list
        (e.g. ``["control.supplier_inventory@v1"]``).
    assessment
        The closed assessment block produced upstream by
        :func:`...primitives.assess.assess_supplier_signal`. Used to
        join the implicated supplier handle against the declared
        dependency surface.
    dependencies
        JSON-native list of dependency objects matching the F-CP-03
        ``dependencies[]`` shape. One entry per external surface the
        execution resolved against; the affected supplier handle on
        ``assessment`` MUST appear here.
    owner_role, owner_assigned_at
        Owner-block fields per the F-CP-03 schema. ``owner_role`` is
        a non-empty role-shaped string; ``owner_assigned_at`` is an
        ISO-8601 date (``YYYY-MM-DD``).
    captured_at
        ISO-8601 UTC second-precision timestamp (``...Z``).
    source_url
        URL of the workflow run that produced this artifact.
    aggregates
        Optional pre-computed counts forwarded verbatim.
    commit_sha
        Optional 7..64-char hex commit pin.
    retention
        Optional ISO-8601 duration retention hint.

    Returns
    -------
    JSON-native dict matching
    ``schemas/evidence/supply-chain.schema.json``. The deterministic
    ``artifact_id`` derives from the three pinned fields per the
    schema contract.
    """
    _require_dict(assessment, "assessment")
    if not isinstance(dependencies, list):
        raise InvalidSupplyChainEvidenceArtifactError(
            f"dependencies must be a list, got "
            f"{type(dependencies).__name__}"
        )
    if not isinstance(regulation_refs, list):
        raise InvalidSupplyChainEvidenceArtifactError(
            "regulation_refs must be a list"
        )
    if not isinstance(control_refs, list):
        raise InvalidSupplyChainEvidenceArtifactError(
            "control_refs must be a list"
        )

    deps = [_build_dependency(dep, idx) for idx, dep in enumerate(dependencies)]
    _validate_assessment_join(assessment, deps)

    captured_at_dt = _parse_iso_z(captured_at, "captured_at")

    context = SupplyChainContext(
        workflow_id=_require_str(workflow_id, "workflow_id"),
        execution_id=_require_str(execution_id, "execution_id"),
        regulation_refs=tuple(regulation_refs),
        control_refs=tuple(control_refs),
        dependencies=tuple(deps),
        owner_role=_require_str(owner_role, "owner_role"),
        owner_assigned_at=_require_str(
            owner_assigned_at, "owner_assigned_at"
        ),
        captured_at=captured_at_dt,
        source_url=_require_str(source_url, "source_url"),
        aggregates=_build_aggregates(aggregates),
        commit_sha=commit_sha,
        retention=retention,
    )

    try:
        return render_supply_chain_artifact(context)
    except EmitError as exc:
        # Re-raise under the primitive's own error class so the action
        # body's exception handling stays uniform across primitives.
        raise InvalidSupplyChainEvidenceArtifactError(str(exc)) from exc
