"""n8n compile-target dispatch bindings for the F-NIS2-BCP playbook.

SKELETON stub. Placeholder module for the n8n compile target of the
business-continuity plan-lifecycle playbook
(``playbook.business_continuity@v1``). The sibling CORE card lands the
adapter Protocols under ``patterns.business_continuity`` and the
dispatchers that route an n8n-side call (from an ``executeCommand`` /
``Code`` node) to whichever operator-bound adapter the operator's
runtime carries: BCM-plan store, isolation surface, failover surface,
and competent-authority notification surface. Runtime-neutral over
the adapter choice: the framework does not import any specific NCA
client, isolation controller, or failover orchestrator.

Symmetry with the sibling targets
---------------------------------

Each dispatcher declared by the CORE card here will have an
exact-signature sibling under ``compilers.temporal.business_continuity``
(``@activity.defn`` wrapper) and
``compilers.langgraph.business_continuity`` (LangGraph node function).
The three-target parity contract is on dispatch signature and return
shape, not on any worked example — those land in EXTEND.

See :mod:`patterns.business_continuity` (CORE card scope) for the
protocols these dispatchers will bind against.
"""
from __future__ import annotations

__all__: list[str] = []
