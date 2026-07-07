"""Temporal compile-target dispatch bindings for the F-WF-CRYPTOMGMT playbook.

CORE placeholder. Following the compilers/temporal/business_continuity/
convention, the Temporal compile target for the cryptographic-controls
lifecycle playbook (``playbook.cryptographic_controls@v1``) is served
by the generic ``compilers.temporal.emit`` emitter. This module is
retained as an import anchor for future ``@activity.defn`` wrappers.

Symmetry with the sibling targets
---------------------------------

Any activity declared here on a later card will have an
exact-signature sibling under ``compilers.n8n.cryptographic_controls``
and ``compilers.langgraph.cryptographic_controls``. The three-target
parity contract is on dispatch signature and return shape.

Determinism note
----------------

Temporal workflow code must be deterministic across replay. Any
future non-deterministic boundary — the concrete KMS backend, CA
backend, storage-encryption backend, or TLS-endpoint backend the
lifecycle branches call into — will live on the activity side of the
``@activity.defn`` line, not inside the workflow.

The sibling EXTEND card lands the adapter Protocols under
``patterns.cryptographic_controls`` these activities will bind
against.
"""
from __future__ import annotations

__all__: list[str] = []
