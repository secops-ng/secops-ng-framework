# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.temporal <playbook.cacao.json>`.
#
# This file is a stub. Workflow control flow and activity bodies are
# intentionally NotImplementedError until a human integrator wires them
# to the operator's runtime.
"""Generated Temporal stub. See module-level metadata in the workflow docstring."""
from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

@activity.defn
async def triage_signal(signal_id: str, hydrated_signal: dict[str, object], edr_status: dict[str, object], analyst_verdict: str) -> dict[str, object]:
    """Decide whether the hydrated signal confirms ransomware, by an explicit evidence rule: a decisive artifact, mass file-extension rename with a corroborating indicator, or shadow copies and the backup catalogue deleted together. An analyst verdict decides when present, and a disagreement is recorded as an override. Also decides whether EDR can isolate. Produces __triage_record__, from which __affected_host__, __affected_identity__, __ransomware_confirmed__ and __edr_available__ are extracted.

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage_signal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage_signal'})
        )
        from content.playbooks.ransomware_containment.primitives.triage import triage_ransomware_signal
        __triage_record__ = triage_ransomware_signal(signal=__hydrated_signal__, edr_status=__edr_status__, analyst_verdict=__analyst_verdict__)

TRIAGE_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def endpoint_isolation_edr_isolate(triage_record: dict[str, object], authorisation_policy: dict[str, object], requested_at: str) -> dict[str, object]:
    """Compose the EDR isolate directive for __affected_host__: cut the host off everywhere except the EDR management channel, so responders can keep investigating it. Re-checks both gates behind it; a protected host, or a policy without auto-isolation, waits for approval. Primary path. Produces __edr_isolation_directive__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'endpoint isolation — EDR isolate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'endpoint_isolation_edr_isolate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'endpoint isolation — EDR isolate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'endpoint_isolation_edr_isolate'})
        )
        from content.playbooks.ransomware_containment.primitives.isolation import compose_edr_isolation
        __edr_isolation_directive__ = compose_edr_isolation(triage=__triage_record__, authorisation_policy=__authorisation_policy__, requested_at=__requested_at__)

ENDPOINT_ISOLATION_EDR_ISOLATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def endpoint_isolation_network_acl_deny_fallback(triage_record: dict[str, object], authorisation_policy: dict[str, object], chokepoint_ref: str, requested_at: str) -> dict[str, object]:
    """EDR fallback: compose a deny-all directive for __affected_host__ at __chokepoint_ref__, ingress and egress (firewall rule, switchport disable, or SDN policy). Used when the EDR agent is unreachable or cannot isolate. Re-checks both gates behind it and applies the same approval policy. Produces __network_isolation_directive__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'endpoint isolation — network ACL deny (fallback)', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'endpoint_isolation_network_acl_deny_fallback'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'endpoint isolation — network ACL deny (fallback)', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'endpoint_isolation_network_acl_deny_fallback'})
        )
        from content.playbooks.ransomware_containment.primitives.isolation import compose_network_isolation
        __network_isolation_directive__ = compose_network_isolation(triage=__triage_record__, authorisation_policy=__authorisation_policy__, chokepoint_ref=__chokepoint_ref__, requested_at=__requested_at__)

ENDPOINT_ISOLATION_NETWORK_ACL_DENY_FALLBACK_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def identity_revocation(triage_record: dict[str, object], idp_capabilities: dict[str, object], protected_identities: str, requested_at: str) -> dict[str, object]:
    """Compose the revocation directive for __affected_identity__: disable the account and revoke its sessions, plus token revocation and Kerberos ticket invalidation where the IdP supports them; what it cannot revoke is listed, not claimed. A protected principal waits for approval; with no principal implicated the directive is empty. Produces __identity_revocation_directive__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identity revocation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identity_revocation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identity revocation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identity_revocation'})
        )
        from content.playbooks.ransomware_containment.primitives.identity import compose_identity_revocation
        __identity_revocation_directive__ = compose_identity_revocation(triage=__triage_record__, idp_capabilities=__idp_capabilities__, protected_identities=__protected_identities__, requested_at=__requested_at__)

IDENTITY_REVOCATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def backup_verification(snapshots: str, backup_catalogue: dict[str, object], compromise_window_start: str) -> dict[str, object]:
    """Select the newest snapshot taken before __compromise_window_start__ whose digest matches the backup-catalogue record, listing the newer candidates it rejected and why. Produces __backup_selection__, from which __latest_known_good_snapshot__ and __snapshot_integrity_ok__ are extracted. Does NOT restore; restore is a separate, out-of-scope recovery playbook.

    CACAO step_id: action--30000000-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'backup verification', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'backup_verification'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'backup verification', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'backup_verification'})
        )
        from content.playbooks.ransomware_containment.primitives.backup import select_known_good_snapshot
        __backup_selection__ = select_known_good_snapshot(snapshots=__snapshots__, catalogue=__backup_catalogue__, compromise_window_start=__compromise_window_start__)

BACKUP_VERIFICATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def comms_plan(triage_record: dict[str, object], backup_selection: dict[str, object], comms_channels: dict[str, object], drafted_at: str) -> dict[str, object]:
    """Compose the notifications to the IR lead and comms officer along __comms_channels__, and stage the regulator early warning per NIS2 Article 23(4)(a), due 24 hours from detection, for human sign-off; it is never auto-sent. Because this step is the handoff point that closes the incident timeline and trips the statutory reporting clocks, it stamps the timeline-completeness KPI alongside the notification-SLA KPI and the regulator-notification-overrun KRI. Produces __comms_plan__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000009
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000009',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'comms plan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'comms_plan'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000009', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'comms plan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'comms_plan'})
        )
        from content.playbooks.ransomware_containment.primitives.comms import compose_comms_plan
        __comms_plan__ = compose_comms_plan(triage=__triage_record__, backup_selection=__backup_selection__, channels=__comms_channels__, drafted_at=__drafted_at__)

COMMS_PLAN_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookRansomwareContainmentV1Workflow:
    """Contain an in-progress or just-detected ransomware event on an endpoint or identity. Triage the originating signal; if confirmed, isolate the affected host (EDR primary, network ACL fallback), revoke the implicated identity and its active sessions, verify the latest known-good backup snapshot, and drive a notification step that pages the IR lead, the comms officer, and drafts the NIS2 Article 23 early-warning pre-notification within the 24-hour clock. CACAO v2 + SecOps-NG content-model extensions. Forward-public artifact: detection bindings reference upstream SigmaHQ rule IDs only; SecOps-NG does not re-author Sigma rules.

    CACAO playbook id : playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8
    stable_id         : playbook.ransomware_containment@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : triage_signal, endpoint_isolation_edr_isolate, endpoint_isolation_network_acl_deny_fallback, identity_revocation, backup_verification, comms_plan
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.ransomware_containment@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.ransomware_containment@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.ransomware_containment@v1'"
            )

WORKFLOW = PlaybookRansomwareContainmentV1Workflow
ACTIVITIES = (triage_signal, endpoint_isolation_edr_isolate, endpoint_isolation_network_acl_deny_fallback, identity_revocation, backup_verification, comms_plan,)
RETRY_POLICIES = (TRIAGE_SIGNAL_RETRY_POLICY, ENDPOINT_ISOLATION_EDR_ISOLATE_RETRY_POLICY, ENDPOINT_ISOLATION_NETWORK_ACL_DENY_FALLBACK_RETRY_POLICY, IDENTITY_REVOCATION_RETRY_POLICY, BACKUP_VERIFICATION_RETRY_POLICY, COMMS_PLAN_RETRY_POLICY,)
