"""Log retention and cycle evidence for the eu_ai_act_deployer_obligations playbook.

Backs the ``retain_logs_and_evidence`` step. Regulation (EU) 2024/1689
Art. 26(6): deployers keep the logs the high-risk AI system generates
automatically, to the extent those logs are under their control, for a
period appropriate to the intended purpose, of at least six months — unless
applicable Union or national law, in particular personal-data protection
law, provides otherwise.

So the record states the control determination first; logs outside the
deployer's control carry no retention duty here. Under control, six months
is the floor, not the target, and a shorter period is accepted only with a
reference to the provision of law that requires it — the "unless provided
otherwise" limb cuts both ways, and the record says which applied. The log
store itself stays an operator-owned surface.

The cycle-evidence artifact joins the intended-use determination, the
oversight assignment, the monitoring observation and the fundamental-rights
record for one deployment, refusing records from another deployment.
``artifact_id`` is SHA-256(workflow_id | execution_id | captured_at), so the
three reference compilers derive byte-identical records.
"""

from __future__ import annotations

from ._common import add_months, boolean, digest, exact_keys, optional_pointer, pointer, proceeding, text, zulu

__all__ = ["FLOOR_MONTHS", "InvalidRetentionEvidenceError", "compose_retention_evidence"]

FLOOR_MONTHS = 6


class InvalidRetentionEvidenceError(ValueError):
    """The retention record or a joined record is malformed or inconsistent."""


def _retention(value: object, captured) -> dict:
    r = exact_keys(value, {"logs_under_deployer_control", "retention_months", "legal_basis_ref"},
                   "log_retention", InvalidRetentionEvidenceError)
    control = boolean(r["logs_under_deployer_control"], "log_retention.logs_under_deployer_control",
                      InvalidRetentionEvidenceError)
    legal = optional_pointer(r["legal_basis_ref"], "log_retention.legal_basis_ref", InvalidRetentionEvidenceError)
    if not control:
        if r["retention_months"] is not None or legal is not None:
            raise InvalidRetentionEvidenceError(
                "logs outside the deployer's control carry no Art. 26(6) retention period"
            )
        return {"logs_under_deployer_control": False, "retention_months": None, "retain_until": None,
                "basis": "not_under_deployer_control", "legal_basis_ref": None}
    months = r["retention_months"]
    if isinstance(months, bool) or not isinstance(months, int) or months <= 0:
        raise InvalidRetentionEvidenceError(f"log_retention.retention_months must be a positive integer, got {months!r}")
    if months < FLOOR_MONTHS and legal is None:
        raise InvalidRetentionEvidenceError(
            f"{months} months is below the Art. 26(6) floor of {FLOOR_MONTHS}; a shorter period needs the "
            "legal_basis_ref of the Union or national law that provides otherwise"
        )
    basis = "applicable_law_provides_otherwise" if legal is not None else "art_26_6_floor_or_longer"
    return {"logs_under_deployer_control": True, "retention_months": months,
            "retain_until": text(add_months(captured, months)), "basis": basis, "legal_basis_ref": legal}


def compose_retention_evidence(intended_use: dict, oversight: dict, observation: dict, fria: dict,
                               log_retention: dict, workflow_id: str, execution_id: str,
                               captured_at: str) -> dict:
    """Compose the dated cycle-evidence artifact and the retention disposition.

    Parameters
    ----------
    intended_use / oversight / observation / fria
        The four earlier step outputs for the same deployment; reachable only
        when the deployment may proceed.
    log_retention
        Exactly ``logs_under_deployer_control`` (a real boolean),
        ``retention_months`` (a positive integer under control, ``None``
        otherwise) and ``legal_basis_ref`` (the provision of law that sets a
        different period, or unset).
    workflow_id / execution_id / captured_at
        Folded into the deterministic ``artifact_id``.
    """
    iu = proceeding(intended_use, InvalidRetentionEvidenceError, "retain logs and evidence")
    joins = {"oversight": (oversight, "assignment_id"), "observation": (observation, "observation_id"),
             "fria": (fria, "fria_id")}
    for name, (record, key) in joins.items():
        if not isinstance(record, dict) or not {key, "deployment_id"} <= set(record):
            raise InvalidRetentionEvidenceError(f"{name} must be the corresponding step output")
        if record["deployment_id"] != iu["deployment_id"]:
            raise InvalidRetentionEvidenceError(f"the {name} record belongs to a different deployment")
    wid = pointer(workflow_id, "workflow_id", InvalidRetentionEvidenceError)
    eid = pointer(execution_id, "execution_id", InvalidRetentionEvidenceError)
    captured = zulu(captured_at, "captured_at", InvalidRetentionEvidenceError)
    return {
        "artifact_id": digest(wid, eid, captured_at),
        "deployment_id": iu["deployment_id"],
        "determination_id": iu["determination_id"],
        "assignment_id": oversight["assignment_id"],
        "observation_id": observation["observation_id"],
        "fria_id": fria["fria_id"],
        "oversight_complete": oversight.get("complete") is True,
        "escalation_trigger_class": observation.get("escalation_trigger_class"),
        "fria_in_scope": fria.get("in_scope"),
        "fria_complete": fria.get("complete"),
        "log_retention": _retention(log_retention, captured),
        "workflow_id": wid,
        "execution_id": eid,
        "captured_at": captured_at,
        "metric_stamps": [],
    }
