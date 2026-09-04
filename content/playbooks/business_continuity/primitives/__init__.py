"""Shared primitives for the business-continuity (F-WF-BCM) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.declaration` -- :func:`declare_bcm_event`
  (detect_and_declare_bcm_event step). Content-derived event identity
  over the closed trigger vocabulary; the NIS2 Art. 23 clock anchors
  on the supplied declaration instant, never a clock read.

* :mod:`.activation` -- :func:`activate_bcm_plan` (activate_bcm_plan
  step). Resolves the operator-owned plan register and the declared
  significance-threshold policy. **No plan on file is data, not a
  wall** — the roadmap's no-plan criterion, deliberately the opposite
  of the ddos_response detect gate; ambiguity still fails loud.

* :mod:`.isolation` -- :func:`resolve_isolation_scope`
  (isolate_affected_systems step). Deterministic scope identity;
  skipping (no documented isolation targets) is a recorded decision
  with the empty ``__isolation_scope__`` the step text specifies.

* :mod:`.failover` -- :func:`select_failover_target`
  (switch_to_backup step). Honours the plan's documented preference
  order; no target is recorded with its reason, never a stall.

* :mod:`.notification` -- :func:`compose_authority_notification`
  (notify_competent_authority step). The Art. 23 cascade arithmetic
  (24h / 72h exact, one calendar month clamped) and the two exclusive
  dispositions — an unjustified no-notification is not representable.

* :mod:`.recovery` -- :func:`evaluate_recovery` (restore_and_verify
  step). Recovered means observed (cutback + health), objective misses
  are signed compliance deltas, undocumented objectives are reported
  as such.

* :mod:`.review` -- :func:`compose_pir_record` (post_incident_review
  step). Lessons mandatory, revisions optional, ``ran_without_plan``
  marked, content-derived identity.

* :mod:`.milestones` -- :func:`compose_milestone_record` and
  :func:`compose_incident_finding_record` (all steps). The OCSF
  API Activity (6003) / Incident Finding (2005) milestone records
  keyed to the event id — the house binding pinned by #875/#877 and
  this playbook's mappings.yaml.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/cra_cvd/primitives/__init__.py`` and
``content/playbooks/data_subject_rights/primitives/__init__.py``.
"""

from __future__ import annotations

from .activation import (
    AmbiguousPlanRegisterError,
    InvalidActivationInputError,
    activate_bcm_plan,
)
from .declaration import (
    InvalidBcmTriggerError,
    declare_bcm_event,
)
from .failover import (
    InvalidFailoverInputError,
    select_failover_target,
)
from .isolation import (
    InvalidIsolationScopeError,
    resolve_isolation_scope,
)
from .milestones import (
    InvalidMilestoneInputError,
    compose_incident_finding_record,
    compose_milestone_record,
)
from .notification import (
    InvalidNotificationInputError,
    compose_authority_notification,
)
from .recovery import (
    InvalidRecoveryObservationError,
    evaluate_recovery,
)
from .review import (
    InvalidPirRecordError,
    compose_pir_record,
)

__all__ = [
    "AmbiguousPlanRegisterError",
    "InvalidActivationInputError",
    "InvalidBcmTriggerError",
    "InvalidFailoverInputError",
    "InvalidIsolationScopeError",
    "InvalidMilestoneInputError",
    "InvalidNotificationInputError",
    "InvalidPirRecordError",
    "InvalidRecoveryObservationError",
    "activate_bcm_plan",
    "compose_authority_notification",
    "compose_incident_finding_record",
    "compose_milestone_record",
    "compose_pir_record",
    "declare_bcm_event",
    "evaluate_recovery",
    "resolve_isolation_scope",
    "select_failover_target",
]
