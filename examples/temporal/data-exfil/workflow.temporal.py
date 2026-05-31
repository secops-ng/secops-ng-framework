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


@activity.defn
async def triage_signal(signal_id: str) -> None:
    """Receive the DLP / egress signal, hydrate it with originating user / asset / destination context, and decide whether the signal warrants scope assessment or is a known benign egress pattern.

    CACAO step_id: action--20000000-0000-4000-8000-000000000002
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--20000000-0000-4000-8000-000000000002'"
    )

TRIAGE_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def scope_assessment(signal_id: str) -> dict[str, object]:
    """Determine the volume and classification of data observed leaving the boundary, the count of distinct data subjects affected, and whether actual exfiltration occurred or was prevented by an in-line control. Produces __data_classification__, __affected_subjects_count__, and __exfil_confirmed__.

    CACAO step_id: action--20000000-0000-4000-8000-000000000003
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--20000000-0000-4000-8000-000000000003'"
    )

SCOPE_ASSESSMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def containment(data_classification: str, affected_subjects_count: int) -> None:
    """Apply containment proportionate to data classification and scope: revoke session tokens, isolate the originating identity / host, force a credential rotation, and tighten the egress policy on the destination(s) named in the signal. Bounded by the operator-supplied authorisation policy.

    CACAO step_id: action--20000000-0000-4000-8000-000000000005
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--20000000-0000-4000-8000-000000000005'"
    )

CONTAINMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_regulator(data_classification: str, affected_subjects_count: int) -> None:
    """Compose and send the regulator notification along the operator's pre-bound channel (national CSIRT for NIS2, competent authority for DORA, supervisory authority for GDPR). The notification payload is a structured incident finding sourced from the scope-assessment outputs.

    CACAO step_id: action--20000000-0000-4000-8000-000000000007
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--20000000-0000-4000-8000-000000000007'"
    )

NOTIFY_REGULATOR_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_customer(data_classification: str, affected_subjects_count: int) -> None:
    """Notify affected customers / data subjects via the operator's pre-bound channel. Tracked separately from regulator notification so the SLA-compliance KPI can report the two timelines independently.

    CACAO step_id: action--20000000-0000-4000-8000-000000000008
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--20000000-0000-4000-8000-000000000008'"
    )

NOTIFY_CUSTOMER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDataExfilV1Workflow:
    """Respond to a DLP / egress signal that indicates possible exfiltration of sensitive data. The playbook triages the signal, assesses scope and data classification, contains confirmed exfiltration, and gates regulator / customer notification on the affected-subjects threshold so EU operators can meet NIS2 Article 23 and DORA Article 19 reporting obligations. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7
    stable_id         : playbook.data_exfil@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--20000000-0000-4000-8000-000000000001
    activities        : triage_signal, scope_assessment, containment, notify_regulator, notify_customer
    """

    @workflow.run
    async def run(self) -> None:
        raise NotImplementedError(
            f"CACAO workflow lowering not implemented: stable_id='playbook.data_exfil@v1'"
        )

WORKFLOW = PlaybookDataExfilV1Workflow
ACTIVITIES = (triage_signal, scope_assessment, containment, notify_regulator, notify_customer,)
RETRY_POLICIES = (TRIAGE_SIGNAL_RETRY_POLICY, SCOPE_ASSESSMENT_RETRY_POLICY, CONTAINMENT_RETRY_POLICY, NOTIFY_REGULATOR_RETRY_POLICY, NOTIFY_CUSTOMER_RETRY_POLICY,)
