"""Posture evidence for the network_security playbook.

Backs the ``generate_posture_evidence_artifact`` step, which always runs: the
dated record that joins one reconciliation window's inventory, policy
snapshot, violation set and remediation dispatch, shaped after an OSCAL
assessment result.

* **One chain, checked.** The policy evaluation must be of this inventory,
  the detection of this inventory and snapshot, and the dispatch of this
  violation set. A record from another window or another run is refused.
* **A finding per violation, each with its action.** Every finding names the
  surface it was dispatched to and the identifier that surface returned. An
  empty set says so explicitly: ``no_findings`` is true and the dispatch
  record may be unset.
* **What the window leaves open is carried, not dropped.** Undocumented
  segments, source disagreements, overlapping address space and the policy's
  own findings are listed as open items, so a clean violation set over an
  incomplete inventory does not read as a clean window.

``posture_evidence_id`` is a digest of the record's content.
"""

from __future__ import annotations

from ._common import canonical, digest, step_output, unset, zulu

__all__ = ["InvalidPostureEvidenceError", "compose_posture_evidence"]


class InvalidPostureEvidenceError(ValueError):
    """The records do not form one reconciliation chain."""


def compose_posture_evidence(inventory: dict, policy: dict, detection: dict, remediation: dict | None,
                             produced_at: str) -> dict:
    """Compose the dated network-security posture evidence for one window.

    Parameters
    ----------
    inventory, policy, detection
        The inventory, policy-evaluation and violation-detection outputs.
    remediation
        The enforce-remediation output; may be unset when the violation set
        is empty.
    produced_at
        Zulu instant of publication.
    """
    err = InvalidPostureEvidenceError
    inv = step_output(inventory, {"window_ref", "segment_inventory_id", "segments", "undocumented_segments",
                                  "disagreements", "overlaps"}, "inventory", err)
    pol = step_output(policy, {"window_ref", "segment_inventory_id", "policy_snapshot_id", "policy_ref", "revision",
                               "findings"}, "policy", err)
    det = step_output(detection, {"window_ref", "segment_inventory_id", "policy_snapshot_id", "violation_set_id",
                                  "violations", "detected_at"}, "detection", err)
    if not inv["window_ref"] == pol["window_ref"] == det["window_ref"]:
        raise err("the records belong to different reconciliation windows")
    if not inv["segment_inventory_id"] == pol["segment_inventory_id"] == det["segment_inventory_id"]:
        raise err("the policy evaluation or the detection was made against a different inventory")
    if det["policy_snapshot_id"] != pol["policy_snapshot_id"]:
        raise err("the detection was made against a different policy snapshot")
    last = zulu(det["detected_at"], "detection.detected_at", err)

    rows: dict[str, dict] = {}
    action_id = None
    if unset(remediation):
        if det["violations"]:
            raise err("violations were detected, so the remediation dispatch record is required")
    else:
        rem = step_output(remediation, {"violation_set_id", "remediation_action_id", "dispatch_table",
                                        "dispatched_at"}, "remediation", err)
        if rem["violation_set_id"] != det["violation_set_id"]:
            raise err("the remediation dispatch belongs to a different violation set")
        rows = {r["violation_id"]: r for r in rem["dispatch_table"]}
        if set(rows) != {v["violation_id"] for v in det["violations"]}:
            raise err("the dispatch table does not cover exactly the detected violations")
        action_id = rem["remediation_action_id"]
        last = zulu(rem["dispatched_at"], "remediation.dispatched_at", err)
    if zulu(produced_at, "produced_at", err) < last:
        raise err("produced_at is before the step that precedes it")

    findings = [{"violation_id": v["violation_id"], "classification": v["classification"], "from_ref": v["from_ref"],
                 "to_ref": v["to_ref"], "service": v["service"], "critical": v["critical"],
                 "surface": rows[v["violation_id"]]["surface"], "action_ref": rows[v["violation_id"]]["action_ref"]}
                for v in det["violations"]]
    open_items = ([f"undocumented_segment:{ref}" for ref in inv["undocumented_segments"]]
                  + sorted({f"source_disagreement:{d['segment_ref']}:{d['field']}" for d in inv["disagreements"]})
                  + [f"overlapping_segments:{a}:{b}" for a, b in inv["overlaps"]]
                  + [f"policy:{f}" for f in pol["findings"]])
    body = {
        "window_ref": inv["window_ref"],
        "assessment_subject": {"segment_inventory_id": inv["segment_inventory_id"],
                               "segment_count": len(inv["segments"]),
                               "critical_segment_count": sum(1 for s in inv["segments"] if s["critical"])},
        "assessment_activity": {"policy_snapshot_id": pol["policy_snapshot_id"], "policy_ref": pol["policy_ref"],
                                "revision": pol["revision"]},
        "violation_set_id": det["violation_set_id"],
        "remediation_action_id": action_id,
        "findings": findings,
        "no_findings": not findings,
        "open_items": open_items,
        "produced_at": produced_at,
    }
    return {"posture_evidence_id": digest("network_security_posture", canonical(body)), **body, "metric_stamps": []}
