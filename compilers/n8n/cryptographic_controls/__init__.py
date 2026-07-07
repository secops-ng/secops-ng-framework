"""n8n compile-target dispatch bindings for the F-WF-CRYPTOMGMT playbook.

CORE placeholder. Following the compilers/n8n/business_continuity/
convention, the n8n compile target for the cryptographic-controls
lifecycle playbook (``playbook.cryptographic_controls@v1``) is served
by the generic ``compilers.n8n.emit`` emitter — the CACAO source is
authored plainly enough that no per-playbook emitter uplift is
required at this tier. This module is retained as an import anchor
for future adapter-Protocol dispatchers.

Symmetry with the sibling targets
---------------------------------

Any dispatcher declared here on a later card will have an
exact-signature sibling under ``compilers.temporal.cryptographic_controls``
(``@activity.defn`` wrapper) and
``compilers.langgraph.cryptographic_controls`` (LangGraph node function).
The three-target parity contract is on dispatch signature and return
shape, not on any worked example — the worked examples under
``examples/{n8n,temporal,langgraph}/cryptographic_controls/`` carry
the byte-parity contract for the CORE tier.

The sibling EXTEND card lands the adapter Protocols under
``patterns.cryptographic_controls`` (KMS backend, CA backend,
storage-encryption backend, TLS-endpoint backend) and the concrete
dispatchers that route an n8n-side call from an ``executeCommand`` /
``Code`` node to whichever operator-bound adapter the runtime carries.
Runtime-neutral over the adapter choice.
"""
from __future__ import annotations

__all__: list[str] = []
