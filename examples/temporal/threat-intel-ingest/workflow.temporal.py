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
async def pull_upstream_feed(feed_url: str, feed_id: str) -> None:
    """Poll the configured TAXII collection or STIX 2.1 endpoint and capture the raw bundle. The endpoint is operator-supplied; the content model does not embed feed URLs.

    CACAO step_id: action--10000000-0000-4000-8000-000000000002
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--10000000-0000-4000-8000-000000000002'"
    )

PULL_UPSTREAM_FEED_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def normalise_stix_to_ocsf() -> dict[str, object]:
    """Map STIX 2.1 SDOs (Indicator, Malware, Threat-Actor) into the playbook's canonical normalised-indicator record. The released OCSF v1.3.0 catalogue does not contain a dedicated threat-intel ingest event class, so no OCSF class is asserted here on the consumed side (see mappings.yaml — ocsf section). Persist normalised records keyed by indicator value; deduplicate against records seen within the last 24 hours.

    CACAO step_id: action--10000000-0000-4000-8000-000000000003
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--10000000-0000-4000-8000-000000000003'"
    )

NORMALISE_STIX_TO_OCSF_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def propagate_to_blocklist(indicator_count: int) -> None:
    """Push high-confidence indicators (IPs, domains, file hashes) to the operator's enforcement plane: perimeter firewall, DNS sinkhole, EDR allow/deny list. Records the propagation event so MTTR-to-block can be measured.

    CACAO step_id: action--10000000-0000-4000-8000-000000000005
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--10000000-0000-4000-8000-000000000005'"
    )

PROPAGATE_TO_BLOCKLIST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def activate_detection_rule() -> None:
    """Activate or refresh the corresponding upstream Sigma rule(s) in the operator's SIEM so subsequent telemetry matching the indicator generates an alert. Sigma rule IDs are pinned to upstream SigmaHQ — the framework does not re-author rule bodies (see README for the upstream rule ID list).

    CACAO step_id: action--10000000-0000-4000-8000-000000000006
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--10000000-0000-4000-8000-000000000006'"
    )

ACTIVATE_DETECTION_RULE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookThreatIntelIngestV1Workflow:
    """Portable response for ingesting external cyber threat intelligence. Pulls an upstream STIX 2.1 / TAXII feed, normalises indicators into a canonical record (cross-references in mappings.yaml; the released OCSF v1.3.0 catalogue has no dedicated threat-intel ingest class), and propagates the result to detection (Sigma rule activation in the operator's SIEM, emitting OCSF Detection Finding class_uid 2004 on match) and blocking (perimeter / DNS / EDR blocklist) controls. CACAO v2 portable artifact; runtime is the operator's choice — n8n, Temporal, or LangGraph.

    CACAO playbook id : playbook--7c1e2b3a-4d5f-4a8b-9c0d-1e2f3a4b5c6d
    stable_id         : playbook.threat_intel_ingest@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--10000000-0000-4000-8000-000000000001
    activities        : pull_upstream_feed, normalise_stix_to_ocsf, propagate_to_blocklist, activate_detection_rule
    """

    @workflow.run
    async def run(self) -> None:
        raise NotImplementedError(
            f"CACAO workflow lowering not implemented: stable_id='playbook.threat_intel_ingest@v1'"
        )

WORKFLOW = PlaybookThreatIntelIngestV1Workflow
ACTIVITIES = (pull_upstream_feed, normalise_stix_to_ocsf, propagate_to_blocklist, activate_detection_rule,)
RETRY_POLICIES = (PULL_UPSTREAM_FEED_RETRY_POLICY, NORMALISE_STIX_TO_OCSF_RETRY_POLICY, PROPAGATE_TO_BLOCKLIST_RETRY_POLICY, ACTIVATE_DETECTION_RULE_RETRY_POLICY,)
