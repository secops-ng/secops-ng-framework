"""CSIRT-coordination adapter + embargo-hold state machine — SKELETON.

Protocol-only surface for the CSIRT-coordination adapter the
``playbook.cra_cvd@v1`` ``coordinate_disclosure`` and
``publish_advisory`` steps depend on, plus a pure state machine that
governs how the ``publish_advisory`` step waits for the agreed
disclosure window to open.

Scope
-----

Two responsibilities in one module because they are one contract:

1. Adapter interface — how the coordinate-disclosure step sends the
   coordination request to a CSIRT (national CSIRT, sector CSIRT, or
   a coordinating CSIRT the reporter has pre-engaged) and how it
   receives the CSIRT-side coordination outcome (agreed disclosure
   date, hold extensions, embargo terms).
2. Embargo-hold state machine — the small, pure state machine the
   ``publish_advisory`` step consults before it publishes so an
   embargo the CSIRT set or a hold the operator honoured on their
   own initiative is respected across process restarts and replay.

Runtime-neutral (no ``temporalio`` / ``langgraph`` / n8n imports).
The state machine is deterministic: same transitions in → same
terminal state out. That determinism is what makes the machine safe
to replay from an event log in a Temporal worker, a LangGraph
checkpoint, or an n8n resumed workflow.

Regulatory anchors
------------------

* Cyber Resilience Act (EU) 2024/2847, Article 14 §1 — operator CVD
  policy expected to include coordination with the coordinating
  CSIRT where applicable.
* ISO/IEC 29147:2018 §6 — coordinated disclosure practice, embargo
  handling, extension request handling.
* ENISA / national CSIRT coordinated-vulnerability-disclosure
  guidance — anchors the operator's expected CSIRT interaction
  pattern.

Out of SKELETON scope
---------------------

Concrete CSIRT wiring (MISP, SMTP-with-PGP, a national CSIRT portal
API, an ISAC hand-off) lands in EXTEND cards, one binding per PR.
This SKELETON pins only the shape and the state machine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Mapping, Protocol, Sequence, runtime_checkable

__all__ = [
    "CSIRTCoordinationAdapter",
    "CSIRTCoordinationRequest",
    "CSIRTCoordinationResponse",
    "EmbargoHoldError",
    "EmbargoHoldState",
    "EmbargoStateMachine",
    "EmbargoTransition",
]


#: State of the embargo hold on a case at any point after
#: coordinate_disclosure runs.
#:
#: * ``no_embargo`` — coordination did not attach a hold. The
#:   ``publish_advisory`` step may proceed as soon as its own
#:   preconditions are met (fix validated, disclosure date reached).
#: * ``pending`` — coordination set an embargo and the disclosure
#:   date has not yet arrived. ``publish_advisory`` blocks.
#: * ``extended`` — an extension request was accepted; the hold is
#:   still in force under a new target date. Distinct state from
#:   ``pending`` so audit can count extensions per case (a KRI).
#: * ``released`` — the hold has been released (target date reached,
#:   or the CSIRT / operator agreed to bring publication forward).
#:   Terminal *positive* state; ``publish_advisory`` may proceed.
#: * ``broken`` — a party (typically the reporter or a third-party
#:   discloser) disclosed publicly before the agreed target date.
#:   Terminal *negative* state that forces ``publish_advisory`` to
#:   race the leak; the state machine surfaces the condition so the
#:   audit stream distinguishes an orderly release from a break.
EmbargoHoldState = Literal[
    "no_embargo",
    "pending",
    "extended",
    "released",
    "broken",
]


#: Transitions the state machine accepts. Structural only; the
#: machine enforces which transitions are legal from which states.
#:
#: * ``set`` — coordination attached an embargo; only valid from
#:   ``no_embargo``.
#: * ``extend`` — an extension request was accepted; valid from
#:   ``pending`` or ``extended``.
#: * ``release`` — the hold has been released cleanly; valid from
#:   ``pending`` or ``extended`` (or a no-op from ``no_embargo``).
#: * ``break_`` — the hold was broken by an out-of-band disclosure;
#:   valid from ``pending`` or ``extended``. Trailing underscore
#:   avoids the Python ``break`` keyword clash.
EmbargoTransition = Literal["set", "extend", "release", "break_"]


class EmbargoHoldError(Exception):
    """Raised when a transition is not legal from the current state.

    The state machine is strict on purpose: replaying a Temporal
    workflow, a LangGraph checkpoint, or an n8n resumed run must not
    silently accept an illegal transition. Test the ``current`` and
    ``requested`` attributes to route recovery.
    """

    def __init__(
        self,
        message: str,
        *,
        current: EmbargoHoldState,
        requested: EmbargoTransition,
    ) -> None:
        super().__init__(message)
        self.current: EmbargoHoldState = current
        self.requested: EmbargoTransition = requested


#: Legal transitions per source state. Frozen mapping — the state
#: machine reads it at construction time and never mutates it.
_LEGAL_TRANSITIONS: Mapping[EmbargoHoldState, frozenset[EmbargoTransition]] = {
    "no_embargo": frozenset({"set", "release"}),
    "pending": frozenset({"extend", "release", "break_"}),
    "extended": frozenset({"extend", "release", "break_"}),
    "released": frozenset(),
    "broken": frozenset(),
}


#: Target state per (source state, transition) tuple. Deterministic
#: by construction — the state machine is a pure function of its
#: transitions.
_TRANSITION_TARGET: Mapping[
    tuple[EmbargoHoldState, EmbargoTransition], EmbargoHoldState
] = {
    ("no_embargo", "set"): "pending",
    ("no_embargo", "release"): "no_embargo",
    ("pending", "extend"): "extended",
    ("pending", "release"): "released",
    ("pending", "break_"): "broken",
    ("extended", "extend"): "extended",
    ("extended", "release"): "released",
    ("extended", "break_"): "broken",
}


@dataclass
class EmbargoStateMachine:
    """Pure, replay-safe embargo-hold state machine.

    Deterministic: constructing an instance in the initial state and
    replaying an ordered sequence of transitions always converges to
    the same terminal state. That property is what makes it safe to
    live inside a Temporal workflow (which replays deterministically)
    or a LangGraph checkpoint (which is re-derived from the event
    log). No wall-clock reads, no random state, no I/O.

    The machine tracks the target disclosure date because ``extend``
    transitions carry a new date, and ``publish_advisory`` reads
    ``target_date`` alongside ``state`` before proceeding.
    """

    state: EmbargoHoldState = "no_embargo"
    target_date: date | None = None

    def apply(
        self,
        transition: EmbargoTransition,
        *,
        target_date: date | None = None,
    ) -> EmbargoHoldState:
        """Apply one transition. Return the new state.

        Raises
        ------
        EmbargoHoldError
            If the transition is not legal from the current state.

        Parameters
        ----------
        transition
            One of :data:`EmbargoTransition`.
        target_date
            When ``transition`` is ``set`` or ``extend``, the new
            target disclosure date. Required for those transitions;
            ignored for ``release`` and ``break_``.
        """
        legal = _LEGAL_TRANSITIONS[self.state]
        if transition not in legal:
            raise EmbargoHoldError(
                f"illegal transition {transition!r} from state {self.state!r}",
                current=self.state,
                requested=transition,
            )
        if transition in ("set", "extend"):
            if target_date is None:
                raise EmbargoHoldError(
                    f"transition {transition!r} requires target_date",
                    current=self.state,
                    requested=transition,
                )
            self.target_date = target_date
        new_state = _TRANSITION_TARGET.get((self.state, transition), self.state)
        self.state = new_state
        return new_state

    def may_publish(self) -> bool:
        """Return True iff ``publish_advisory`` may proceed on this hold.

        The state machine's positional invariant for the publish
        gate: ``no_embargo`` and ``released`` allow publication;
        ``broken`` also allows it (the operator races the leak);
        ``pending`` and ``extended`` block it.
        """
        return self.state in ("no_embargo", "released", "broken")


@dataclass(frozen=True)
class CSIRTCoordinationRequest:
    """Payload the ``coordinate_disclosure`` step hands the adapter.

    Structural only; the shape pins what the adapter needs to
    coordinate with a CSIRT, not how any specific CSIRT models its
    intake. Concrete EXTEND-time bindings translate this into the
    CSIRT-specific request shape (MISP event, PGP-signed email,
    national CSIRT portal form).

    Fields
    ------
    case_id
        Correlation key from the playbook's ``__case_id__`` variable.
    product
        Free-text product name the coordination is for.
    reporter_credit_consent
        Whether the reporter has consented to attribution. Concrete
        bindings translate to the CSIRT's expected credit shape.
    proposed_target_date
        The operator's proposed disclosure date entering the
        coordination. The CSIRT may agree, extend, or the negotiation
        may converge elsewhere; the returned response carries the
        agreed date.
    """

    case_id: str
    product: str
    reporter_credit_consent: bool
    proposed_target_date: date
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CSIRTCoordinationResponse:
    """Return value the adapter surfaces to the compile-target wrapper.

    Fields
    ------
    agreed_target_date
        The disclosure date the CSIRT and the operator agreed on.
        Stamped into the playbook's ``__disclosure_target_date__``
        variable.
    hold_transitions
        Ordered sequence of embargo-hold transitions the coordination
        established. Typically ``("set",)`` for a fresh embargo, or
        ``()`` when the CSIRT chose not to attach a hold. Replayed
        into the :class:`EmbargoStateMachine` before
        ``publish_advisory`` reads the state.
    coordinator_ref
        Opaque reference to the CSIRT-side coordination record.
        Written to the audit stream so a reviewer can cross-check.
    """

    agreed_target_date: date
    hold_transitions: Sequence[EmbargoTransition]
    coordinator_ref: str


@runtime_checkable
class CSIRTCoordinationAdapter(Protocol):
    """Dispatch surface a compile-target adapter binds against.

    A concrete EXTEND-time binding — a national-CSIRT portal client,
    an MTA-with-PGP channel, a MISP feed — realises this protocol.
    Runtime-neutral.
    """

    def coordinate(
        self, request: CSIRTCoordinationRequest
    ) -> CSIRTCoordinationResponse:
        """Coordinate the disclosure with the bound CSIRT.

        Concrete bindings translate CSIRT-side errors into their own
        exception classes and re-raise; SKELETON does not pin a
        single exception surface here because CSIRT interactions vary
        more than CNA interactions (portal vs email vs MISP), and a
        one-size wrapper would over-constrain the EXTEND design
        space. EXTEND bindings choose their own exception discipline.
        """
        ...
