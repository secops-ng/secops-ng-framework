"""Temporal compile-target dispatch bindings for the F-NIS2-BCP playbook.

SKELETON stub. Placeholder module for the Temporal compile target of
the business-continuity plan-lifecycle playbook
(``playbook.business_continuity@v1``). The sibling CORE card lands the
``@activity.defn`` wrappers that route a Temporal worker-side activity
call to whichever operator-bound adapter the worker's runtime
carries: BCM-plan store, isolation surface, failover surface, and
competent-authority notification surface. Runtime-neutral over the
adapter choice.

Symmetry with the sibling targets
---------------------------------

Each activity declared by the CORE card here will have an
exact-signature sibling under ``compilers.n8n.business_continuity`` and
``compilers.langgraph.business_continuity``. The three-target parity
contract is on dispatch signature and return shape.

Determinism note
----------------

Temporal workflow code must be deterministic across replay. The
CORE-time activities are the non-deterministic boundary the workflow
crosses to reach the concrete BCM-plan store / isolation / failover /
notification transport. Adapter I/O lives on the activity side of the
``@activity.defn`` line, not inside the workflow.

See :mod:`patterns.business_continuity` (CORE card scope) for the
protocols these activities will bind against.
"""
from __future__ import annotations

__all__: list[str] = []
