"""LangGraph compile-target dispatch bindings for the F-WF-CRYPTOMGMT playbook.

CORE placeholder. Following the compilers/langgraph/business_continuity/
convention, the LangGraph compile target for the cryptographic-controls
lifecycle playbook (``playbook.cryptographic_controls@v1``) is served
by the generic ``compilers.langgraph.emit`` /
``compilers.langgraph.state`` emitters. This module is retained as an
import anchor for future node-function wrappers.

Symmetry with the sibling targets
---------------------------------

Any node function declared here on a later card will have an
exact-signature sibling under ``compilers.n8n.cryptographic_controls``
and ``compilers.temporal.cryptographic_controls``. The three-target
parity contract is on dispatch signature and return shape.

Node-function convention
------------------------

LangGraph nodes conventionally take and return a state mapping, but
the SKELETON / CORE scope is *adapter dispatch* — not full
state-plumbing into a specific graph. Any future dispatchers accept
the adapter and the request directly and return the response,
mirroring the n8n and Temporal siblings exactly. The worked example
under ``examples/langgraph/cryptographic_controls/`` wraps the node
call in the usual ``state -> state`` signature alongside its
``state_bindings.py`` and ``graph_spec.json``.

The sibling EXTEND card lands the adapter Protocols under
``patterns.cryptographic_controls`` these dispatchers will bind
against.
"""
from __future__ import annotations

__all__: list[str] = []
