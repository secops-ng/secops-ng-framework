"""Obligation-evidence artifact builder primitive (emit-obligation-evidence).

Builds the JSON-native obligation-evidence record shaped against
``schemas/evidence/contractual-obligations.schema.json`` (stream:
``contractual-obligations``). The deterministic ``artifact_id`` derives
from
``SHA-256(<workflow_id>|<execution_id>|<contract.contract_id>|<captured_at>)``
per the schema's ``artifact_id`` contract; re-emissions inside the same
execution at the same captured_at against the same contract produce
byte-identical bytes.

The primitive only produces the JSON-native payload — the durable
emitter wiring (artifact-path, content-addressed filename, atomic
write) is owned by
``compilers._shared.evidence.contractual_obligations`` and the
per-target adapters at ``compilers.{n8n,temporal,langgraph}.evidence``.
The per-target CORE binding writes the primitive's output to
``__obligation_artifact_ref__`` and the operator's compile target
wires the durable emitter in its native idiom.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. The
  ``captured_at`` timestamp is supplied by the caller; the upstream
  workflow runtime is the source of truth.
* **Determinism.** Same inputs ⇒ byte-identical output. Same
  ``(workflow_id, execution_id, contract.contract_id, captured_at)``
  ⇒ same ``artifact_id``.
* **Public-bar safe.** Contract id, supplier ref, owner role and
  obligation text are expected to arrive from upstream primitives
  that already canonicalised them; this primitive re-validates
  shape so a direct caller cannot bypass the per-step guards.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidObligationArtifactError",
    "build_obligation_artifact",
    "derive_obligation_artifact_id",
]


_SCHEMA_VERSION = "0.1.0"
_STREAM = "contractual-obligations"

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_Z_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_ISO_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_ISO_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")
_OBLIGATION_ID_RE = re.compile(r"^obligation\.[a-z][a-z0-9_-]*$")
_REVIEW_STATES = frozenset(
    {"current", "due_soon", "overdue", "waived", "unknown"}
)


class InvalidObligationArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidObligationArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidObligationArtifactError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidObligationArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _require_iso_date(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_DATE_RE.match(text):
        raise InvalidObligationArtifactError(
            f"{field} {text!r} is not an ISO-8601 date (YYYY-MM-DD)"
        )
    return text


def _validate_refs(
    value: object, field: str, pattern: re.Pattern[str], max_len: int = 200
) -> list[str]:
    if not isinstance(value, list) or not value:
        raise InvalidObligationArtifactError(
            f"{field} must be a non-empty list"
        )
    out: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        text = _require_str(item, f"{field}[{index}]")
        if len(text) > max_len:
            raise InvalidObligationArtifactError(
                f"{field}[{index}] {text!r} exceeds the {max_len}-char "
                "schema cap"
            )
        if not pattern.match(text):
            raise InvalidObligationArtifactError(
                f"{field}[{index}] {text!r} does not match the expected shape"
            )
        if text in seen:
            raise InvalidObligationArtifactError(
                f"{field} carries duplicate entry {text!r}; the schema "
                "requires uniqueItems"
            )
        seen.add(text)
        out.append(text)
    return out


def _validate_contract(contract: object) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise InvalidObligationArtifactError(
            f"contract must be an object, got {type(contract).__name__}"
        )
    if "contract_id" not in contract or "supplier_ref" not in contract:
        raise InvalidObligationArtifactError(
            "contract must carry contract_id and supplier_ref"
        )
    if "effective_at" not in contract:
        raise InvalidObligationArtifactError(
            "contract.effective_at is required by the schema"
        )
    # The upstream ingest primitive already canonicalised the contract;
    # accept the block as-is but check shape so a direct caller cannot
    # bypass the schema.
    out: dict[str, Any] = {
        "contract_id": _require_str(contract["contract_id"], "contract.contract_id"),
        "supplier_ref": _require_str(
            contract["supplier_ref"], "contract.supplier_ref"
        ),
        "effective_at": _require_iso_date(
            contract["effective_at"], "contract.effective_at"
        ),
    }
    if "expires_at" in contract:
        if contract["expires_at"] is None:
            out["expires_at"] = None
        else:
            out["expires_at"] = _require_iso_date(
                contract["expires_at"], "contract.expires_at"
            )
    if "jurisdiction" in contract:
        j = _require_str(contract["jurisdiction"], "contract.jurisdiction")
        if not re.match(r"^[A-Z]{2}$", j):
            raise InvalidObligationArtifactError(
                f"contract.jurisdiction {j!r} is not ISO-3166 alpha-2"
            )
        out["jurisdiction"] = j
    return out


def _validate_obligations(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise InvalidObligationArtifactError(
            "obligations must be a non-empty list"
        )
    out: list[dict[str, Any]] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise InvalidObligationArtifactError(
                f"obligations[{index}] must be an object"
            )
        oid = _require_str(
            entry.get("obligation_id"), f"obligations[{index}].obligation_id"
        )
        if not _OBLIGATION_ID_RE.match(oid):
            raise InvalidObligationArtifactError(
                f"obligations[{index}].obligation_id {oid!r} is not "
                "role-shaped"
            )
        rec: dict[str, Any] = {
            "obligation_id": oid,
            "clause_ref": _require_str(
                entry.get("clause_ref"), f"obligations[{index}].clause_ref"
            ),
            "obligation_kind": _require_str(
                entry.get("obligation_kind"),
                f"obligations[{index}].obligation_kind",
            ),
            "text": _require_str(
                entry.get("text"), f"obligations[{index}].text"
            ),
        }
        if "cadence" in entry and entry["cadence"] is not None:
            c = _require_str(entry["cadence"], f"obligations[{index}].cadence")
            if not _ISO_DURATION_RE.match(c):
                raise InvalidObligationArtifactError(
                    f"obligations[{index}].cadence {c!r} is not an ISO-8601 "
                    "duration"
                )
            rec["cadence"] = c
        out.append(rec)
    return out


def _validate_review_schedule(
    value: object, obligation_ids: list[str]
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise InvalidObligationArtifactError(
            "review_schedule must be a non-empty list"
        )
    if len(value) != len(obligation_ids):
        raise InvalidObligationArtifactError(
            "review_schedule must be the same length as obligations and "
            "paired one-to-one in the same order"
        )
    out: list[dict[str, Any]] = []
    for index, (entry, expected_oid) in enumerate(zip(value, obligation_ids)):
        if not isinstance(entry, dict):
            raise InvalidObligationArtifactError(
                f"review_schedule[{index}] must be an object"
            )
        oid = _require_str(
            entry.get("obligation_id"),
            f"review_schedule[{index}].obligation_id",
        )
        if oid != expected_oid:
            raise InvalidObligationArtifactError(
                f"review_schedule[{index}].obligation_id {oid!r} does not "
                f"match obligations[{index}].obligation_id "
                f"{expected_oid!r}; the schema pins the one-to-one pairing"
            )
        state = _require_str(
            entry.get("state"), f"review_schedule[{index}].state"
        )
        if state not in _REVIEW_STATES:
            raise InvalidObligationArtifactError(
                f"review_schedule[{index}].state {state!r} is not one of "
                f"{sorted(_REVIEW_STATES)}"
            )
        next_due = _require_iso_z(
            entry.get("next_review_due_at"),
            f"review_schedule[{index}].next_review_due_at",
        )
        rec: dict[str, Any] = {
            "obligation_id": oid,
            "state": state,
            "next_review_due_at": next_due,
        }
        last = entry.get("last_reviewed_at", None)
        if last is None:
            rec["last_reviewed_at"] = None
        else:
            rec["last_reviewed_at"] = _require_iso_z(
                last, f"review_schedule[{index}].last_reviewed_at"
            )
        out.append(rec)
    return out


def derive_obligation_artifact_id(
    workflow_id: str,
    execution_id: str,
    contract_id: str,
    captured_at: str,
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<contract_id>|<captured_at>``).

    Per the schema's ``artifact_id`` contract. Two executions of the
    same workflow at the same instant against the same contract
    collide deliberately; the same execution re-emitted at the same
    captured_at stays byte-identical.
    """
    payload = (
        f"{workflow_id}|{execution_id}|{contract_id}|{captured_at}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_obligation_artifact(
    workflow_id: str,
    execution_id: str,
    regulation_refs: list,
    control_refs: list,
    contract: dict,
    obligations: list,
    review_schedule: list,
    owner_role: str,
    owner_assigned_at: str,
    captured_at: str,
    source_url: str,
    commit_sha: str | None = None,
    retention: str | None = None,
) -> dict[str, Any]:
    """Build the JSON-native obligation-evidence record.

    Inputs are flat JSON-native values mirroring the CACAO core_body
    binding convention used by the infra_posture_management and
    iam_auditor CORE primitives — one CACAO variable per scalar arg.
    Returns one record validating against
    ``schemas/evidence/contractual-obligations.schema.json``.
    """
    wf_id = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wf_id) or len(wf_id) > 200:
        raise InvalidObligationArtifactError(
            f"workflow_id {wf_id!r} does not match the expected shape"
        )
    exec_id = _require_str(execution_id, "execution_id")
    if len(exec_id) > 200:
        raise InvalidObligationArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )
    reg_refs = _validate_refs(
        regulation_refs, "regulation_refs", _REGULATION_REF_RE, max_len=120
    )
    ctrl_refs = _validate_refs(
        control_refs, "control_refs", _CONTROL_REF_RE
    )
    contract_block = _validate_contract(contract)
    obligation_block = _validate_obligations(obligations)
    obligation_ids = [item["obligation_id"] for item in obligation_block]
    schedule_block = _validate_review_schedule(review_schedule, obligation_ids)

    owner_role_text = _require_str(owner_role, "owner_role")
    if len(owner_role_text) > 200:
        raise InvalidObligationArtifactError(
            "owner_role must be <= 200 chars per the schema"
        )
    owner_assigned_at_text = _require_iso_date(
        owner_assigned_at, "owner_assigned_at"
    )
    captured = _require_iso_z(captured_at, "captured_at")
    url = _require_str(source_url, "source_url")

    artifact_id = derive_obligation_artifact_id(
        wf_id, exec_id, contract_block["contract_id"], captured
    )

    record: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "stream": _STREAM,
        "workflow_id": wf_id,
        "execution_id": exec_id,
        "regulation_refs": reg_refs,
        "control_refs": ctrl_refs,
        "contract": contract_block,
        "obligations": obligation_block,
        "review_schedule": schedule_block,
        "owner": {"role": owner_role_text, "assigned_at": owner_assigned_at_text},
        "captured_at": captured,
        "provenance": {
            "source_url": url,
            "captured_at": captured,
        },
    }
    if commit_sha is not None:
        cs = _require_str(commit_sha, "commit_sha")
        if not _COMMIT_SHA_RE.match(cs):
            raise InvalidObligationArtifactError(
                f"commit_sha {cs!r} must be 7..64 lowercase hex chars"
            )
        record["provenance"]["commit_sha"] = cs
    if retention is not None:
        r = _require_str(retention, "retention")
        if not _ISO_DURATION_RE.match(r):
            raise InvalidObligationArtifactError(
                f"retention {r!r} is not an ISO-8601 duration"
            )
        record["retention"] = r

    return record
