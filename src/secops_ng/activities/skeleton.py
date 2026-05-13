"""Activities for the canonical skeleton workflow.

Activities are the side-effect boundary. Workflows must stay deterministic;
anything that calls the network, touches the disk, reads a clock, or otherwise
varies between runs belongs here.

The skeleton's activity is intentionally trivial — it returns a formatted
string and nothing more. It exists to establish the *shape* of the boundary,
not to do real work. Real activities in downstream workflows will call SIEMs,
ticketing systems, model backends, and so on, and will rely on Temporal's
retry policies for resilience.
"""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def process_item(item: str) -> str:
    """Process a single item.

    For the skeleton this is a pure formatter; the activity boundary is what
    matters. Replace the body with real side effects (network calls, database
    writes, LLM invocations) in derived workflows.
    """
    activity.logger.info("processing item: %s", item)
    return f"processed:{item}"
