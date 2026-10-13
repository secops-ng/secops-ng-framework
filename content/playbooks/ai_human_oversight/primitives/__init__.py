"""Shared primitives for the ai_human_oversight playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the Regulation (EU) 2024/1689 Art. 14 oversight loop:

* :mod:`.roster` — :func:`resolve_oversight_roster` (establish oversight
  roster). Who is on watch for the window; an entry counts as empowered
  only as a natural person with a delegation record and all four
  Art. 14(4)(d)-(e) powers, and the roster is effective only with one such
  person reachable.
* :mod:`.briefing` — :func:`compose_briefing_record` (brief oversight
  personnel). The Art. 14(4)(a)-(c) competence limbs, per overseer, per
  system and per current instructions; briefings for another deployment or
  superseded instructions do not count.
* :mod:`.review` — :func:`review_flagged_decisions` (review flagged
  decisions). Every flagged decision ends upheld, intervened or unreviewed;
  only a qualified overseer's review counts; the Art. 14(5) two-person
  verification for Annex III point 1(a) systems, with the exemption's legal
  basis recorded when relied on.
* :mod:`.intervention` — :func:`record_interventions` (record
  intervention). The four Art. 14(4)(d)-(e) exercises told apart, with
  latency and the system output, or the window's dated nil record.
* :mod:`.evidence` — :func:`compose_oversight_evidence` (emit oversight
  evidence). Assigned versus exercised, for one deployment and window.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. The governance and rota surfaces, the briefing
records, the review queue and the evidence store stay adapter-bound
operator surfaces.
"""

from __future__ import annotations

from ._common import CAPABILITIES, POWERS
from .briefing import InvalidBriefingRecordError, compose_briefing_record
from .evidence import InvalidOversightEvidenceError, compose_oversight_evidence
from .intervention import InvalidInterventionRecordError, record_interventions
from .review import DISPOSITIONS, InvalidReviewError, review_flagged_decisions
from .roster import InvalidOversightRosterError, resolve_oversight_roster

__all__ = [
    "CAPABILITIES",
    "DISPOSITIONS",
    "POWERS",
    "InvalidBriefingRecordError",
    "InvalidInterventionRecordError",
    "InvalidOversightEvidenceError",
    "InvalidOversightRosterError",
    "InvalidReviewError",
    "compose_briefing_record",
    "compose_oversight_evidence",
    "record_interventions",
    "resolve_oversight_roster",
    "review_flagged_decisions",
]
