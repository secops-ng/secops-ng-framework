"""Shared primitives for the dora_tpr_management playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the DORA Chapter V third-party lifecycle (Regulation (EU) 2022/2554,
Art. 28 to 30):

* :mod:`.assessment` — :func:`assess_onboarding_risk`
  (onboarding risk assessment). Criticality read from the operator's
  function register, the Art. 28(4) and (5) preconditions, and the Art. 29
  concentration and subcontracting findings.
* :mod:`.provisions` — :func:`check_contractual_provisions`
  (contractual provisions check). The Art. 30(1) and 30(2) clauses for
  every arrangement, Art. 30(3) for a critical or important function.
* :mod:`.register` — :func:`compose_register_entry` (register entry). One
  Art. 28(3) register row per arrangement, compliant or not.
* :mod:`.review` — :func:`review_arrangement` (periodic review). Criticality
  re-read, runtime supply-chain drift, and the Art. 28(7) termination
  grounds identified without acting on them.
* :mod:`.exit` — :func:`compose_exit_assessment` (exit assessment). The
  Art. 28(8) exit-strategy readiness every cycle, and the basis of an exit
  the entity invoked.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. The function register, the contract repository,
the register sink, the supply-chain stream and the evidence store stay
adapter-bound operator surfaces.
"""

from __future__ import annotations

from ._common import EU_EEA
from .assessment import CRITICALITY, InvalidRiskAssessmentError, assess_onboarding_risk
from .exit import TRIGGERS, InvalidExitAssessmentError, compose_exit_assessment
from .provisions import CLAUSES, STATUSES, InvalidProvisionsCheckError, check_contractual_provisions
from .register import InvalidRegisterEntryError, compose_register_entry
from .review import CHANGE_KINDS, VERDICTS, InvalidPeriodicReviewError, review_arrangement

__all__ = [
    "CHANGE_KINDS",
    "CLAUSES",
    "CRITICALITY",
    "EU_EEA",
    "STATUSES",
    "TRIGGERS",
    "VERDICTS",
    "InvalidExitAssessmentError",
    "InvalidPeriodicReviewError",
    "InvalidProvisionsCheckError",
    "InvalidRegisterEntryError",
    "InvalidRiskAssessmentError",
    "assess_onboarding_risk",
    "check_contractual_provisions",
    "compose_exit_assessment",
    "compose_register_entry",
    "review_arrangement",
]
