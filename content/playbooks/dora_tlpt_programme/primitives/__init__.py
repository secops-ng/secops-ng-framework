"""Shared primitives for the DORA Chapter IV DORT / TLPT programme playbook.

Single source of truth for the deterministic, replay-friendly helpers the
per-target CORE action bodies (n8n, Temporal, LangGraph) all bind against.
Each primitive lands as its own module so the per-target compilers depend
only on what they need:

* :mod:`.scope` -- :func:`define_dort_scope` (define DORT scope). Composes
  the Art. 24 catalogue from the operator's business-service, ICT-asset and
  ICT third-party registers. A critical function the asset register cannot
  resolve is reported as a scope gap rather than silently dropped.

* :mod:`.trigger` -- :func:`evaluate_tlpt_trigger` (TLPT trigger and
  planning gate). Decides only what is deterministic — whether the Art. 26(1)
  interval has elapsed. Identification and the significance tier are the
  operator's declaration and the authority's determination, so they are read,
  never judged. An entity out of scope emits a positive ``tlpt_due: false``
  record, because an absent record proves nothing.

* :mod:`.scoping` -- :func:`approve_red_team_scoping` (red-team scoping
  approval). Packages the Art. 26(3) submission and binds the outcome.
  Internal testers must carry the Art. 27 independence attestation and
  external testers a certification; the wrong evidence for the posture is
  refused. Providers inside the testing boundary are participants or
  reasoned carve-outs, never silent omissions.

* :mod:`.remediation` -- :func:`track_remediation` (remediation tracking).
  Derives each finding's deadline from the operator's severity rubric rather
  than accepting an asserted date, and assembles the dated Art. 26(8)
  attestation with the register embedded — an attestation cannot exist
  without the register it attests to.

Every primitive is pure: no clock reads, no network, no LLM. Every date and
instant is supplied as an input, which is what lets a run be replayed and
lets the byte-parity goldens exist. Nothing is dispatched: the
competent-authority channel and the evidence store are adapter-bound
surfaces the sibling EXTEND card binds.
"""

from __future__ import annotations

__all__: list[str] = []
