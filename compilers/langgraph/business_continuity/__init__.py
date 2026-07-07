"""LangGraph compile-target dispatch bindings for the F-NIS2-BCP playbook.

SKELETON stub. Placeholder module for the LangGraph compile target of
the business-continuity plan-lifecycle playbook
(``playbook.business_continuity@v1``). The sibling CORE card lands the
node-function wrappers that route a LangGraph node-side call to
whichever operator-bound adapter the graph's runtime carries:
BCM-plan store, isolation surface, failover surface, and competent-
authority notification surface. Runtime-neutral over the adapter
choice.

Symmetry with the sibling targets
---------------------------------

Each node function declared by the CORE card here will have an
exact-signature sibling under ``compilers.n8n.business_continuity`` and
``compilers.temporal.business_continuity``. The three-target parity
contract is on dispatch signature and return shape.

Node-function convention
------------------------

LangGraph nodes conventionally take and return a state mapping, but
the SKELETON / CORE scope is *adapter dispatch* — not full
state-plumbing into a specific graph. Dispatchers accept the adapter
and the request directly and return the response, mirroring the n8n
and Temporal siblings exactly. The EXTEND-time worked example under
``examples/langgraph/business_continuity/`` wraps this call in the
usual node signature (``state -> state``) alongside its
``state_bindings.py`` and ``graph_spec.json``.

See :mod:`patterns.business_continuity` (CORE card scope) for the
protocols these dispatchers will bind against.
"""
from __future__ import annotations

__all__: list[str] = []
