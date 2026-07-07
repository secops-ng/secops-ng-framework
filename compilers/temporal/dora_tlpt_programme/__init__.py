"""Temporal compile-target dispatch bindings for the F-WF-DORA-TLPT playbook.

CORE placeholder. Following the compilers/temporal/business_continuity/
convention, the Temporal compile target for the DORA digital operational
resilience testing / TLPT programme playbook
(``playbook.dora_tlpt_programme@v1``) is served by the generic
``compilers.temporal.emit`` emitter. This module is retained as an
import anchor for future ``@activity.defn`` wrappers.

Symmetry with the sibling targets
---------------------------------

Any activity declared here on a later card will have an
exact-signature sibling under ``compilers.n8n.dora_tlpt_programme``
and ``compilers.langgraph.dora_tlpt_programme``. The three-target
parity contract is on dispatch signature and return shape.

Determinism note
----------------

Temporal workflow code must be deterministic across replay. Any
future non-deterministic boundary — the concrete competent-authority
notification channel, scoping-submission dispatcher, findings-register
store, or evidence-store publisher the TLPT lifecycle steps call into
— will live on the activity side of the ``@activity.defn`` line, not
inside the workflow.

The sibling EXTEND card lands the adapter Protocols under
``patterns.dora_tlpt_programme`` these activities will bind against.
"""
from __future__ import annotations

__all__: list[str] = []
