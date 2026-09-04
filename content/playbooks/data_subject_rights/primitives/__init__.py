"""Shared primitives for the GDPR Chapter III DSR (F-WF-DSR) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.intake` -- :func:`open_dsr_case` (receive_request step).
  Content-derived case identity over the closed intake-channel enum;
  the Article 12(3) clock anchors on the supplied received instant,
  never a clock read; subject data carried opaquely.

* :mod:`.verification` -- :func:`record_identity_verification`
  (verify_identity step). Closed method vocabulary (sovereign IdP SSO
  primary, three out-of-band paths); a false outcome is a first-class
  branch; the envelope stores no subject-supplied attribute
  (sovereign-stack constraint), only the evidence pointer.

* :mod:`.classification` -- :func:`classify_request`
  (classify_request step). The closed Chapter III taxonomy, the
  calendar-month deadline arithmetic (end-of-month clamped), the
  justification-required Article 12(3) extension shape, and the
  Article 22 human-review handoff flag.

* :mod:`.routing` -- :func:`resolve_data_owner_manifest`
  (route_to_data_owners step). The contractual per-request-type
  evidence ask and the deterministic per-owner acknowledgement
  manifest.

* :mod:`.fulfilment` -- :func:`compile_fulfilment_pack`
  (compile_fulfilment_evidence step). Completeness fails loud;
  lawful qualifications (Art. 17(3) exemptions, Art. 21(1)
  determinations) are data; content-derived pack identity.

* :mod:`.response` -- :func:`compose_controller_response`
  (send_controller_response step). Refusal always carries the
  Art. 77 / Art. 79 remedies; refusal and fulfilment are exclusive;
  lateness is recorded, never absorbed. Composition only — secure
  delivery is the messaging surface's.

* :mod:`.outcome` -- :func:`record_case_outcome` (record_outcome
  step). The closed seven-code vocabulary and the signed
  deadline delta the Article 5(2) accountability posture reads.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/cra_cvd/primitives/__init__.py`` and
``content/playbooks/ddos_response/primitives/__init__.py``.
"""

from __future__ import annotations

from .classification import (
    InvalidClassificationError,
    classify_request,
)
from .fulfilment import (
    IncompleteFulfilmentError,
    InvalidOwnerReturnError,
    compile_fulfilment_pack,
)
from .intake import (
    InvalidDsrRequestError,
    open_dsr_case,
)
from .outcome import (
    InvalidOutcomeRecordError,
    record_case_outcome,
)
from .response import (
    InvalidResponseCompositionError,
    compose_controller_response,
)
from .routing import (
    InvalidRoutingInputError,
    resolve_data_owner_manifest,
)
from .verification import (
    InvalidVerificationRecordError,
    record_identity_verification,
)

__all__ = [
    "IncompleteFulfilmentError",
    "InvalidClassificationError",
    "InvalidDsrRequestError",
    "InvalidOutcomeRecordError",
    "InvalidOwnerReturnError",
    "InvalidResponseCompositionError",
    "InvalidRoutingInputError",
    "InvalidVerificationRecordError",
    "classify_request",
    "compile_fulfilment_pack",
    "compose_controller_response",
    "open_dsr_case",
    "record_case_outcome",
    "record_identity_verification",
    "resolve_data_owner_manifest",
]
