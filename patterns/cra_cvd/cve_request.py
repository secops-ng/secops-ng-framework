"""CVE-request adapter interface — SKELETON.

Protocol-only surface for the CVE-request adapter the
``playbook.cra_cvd@v1`` ``publish_advisory`` step depends on. The
adapter obtains a CVE identifier for a validated, fix-ready
vulnerability from a Certificate Numbering Authority (CNA) the
*operator* has bound at runtime.

CNA-agnosticism (this is the hinge)
-----------------------------------

The CVE program is a federation of numbering authorities rooted at
MITRE (US) with ENISA operating an EU root and downstream EU
national / sector CNAs affiliated under it. The preferred operator
binding for an EU manufacturer running this playbook is an
ENISA-affiliated EU CNA; a US-root binding is available as a fallback.
The choice is an operator decision, not a framework decision:

* This module does not import any CNA-specific client library.
* This module does not carry an authority URL, a shortlist, or a
  default authority string.
* This module does not pre-select the fallback. If the operator wants
  the US root as their binding, they wire it at runtime; the
  framework does not silently downgrade to it.

The :class:`CNARole` enum distinguishes the *role* the bound CNA
plays in the operator's runtime graph (``eu_preferred`` /
``non_eu_fallback``) so the compile-target adapter can log which
lane was taken for audit and so a runtime graph can hold both
bindings and route between them by policy — without hard-coding
either.

Regulatory anchors
------------------

* Cyber Resilience Act (EU) 2024/2847, Article 14 §1 — operator CVD
  policy; a CVE identifier is the conventional public identifier for
  the resulting advisory.
* ENISA CVD guidance and the ENISA CVE authority mandate — anchors
  the ``eu_preferred`` operator binding.
* OASIS CSAF 2.0 — the advisory format the CVE identifier gets
  embedded into; template selection is Sibling A's concern.

Failure surface
---------------

:class:`CVERequestError` is the single re-raise the adapter surfaces
so the compile-target wrapper (Temporal activity, LangGraph node, n8n
Code node) sees one exception class regardless of the bound CNA. A
concrete EXTEND-time binding wraps CNA-specific errors in this class.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping, Protocol, runtime_checkable

__all__ = [
    "CNARole",
    "CVEIdentifier",
    "CVERequest",
    "CVERequestAdapter",
    "CVERequestError",
    "CVERequestResponse",
]


#: Role the bound CNA plays in the operator's runtime graph. The
#: framework does not pre-select; both surfaces are first-class and
#: the operator wires which one this playbook run dispatches to.
#:
#: * ``eu_preferred`` — an ENISA-affiliated EU CNA (ENISA root or a
#:   downstream EU national / sector CNA operating under it). Named
#:   *preferred* because the CRA disclosure lifecycle runs by an EU
#:   manufacturer under EU-sovereignty framing; the framework
#:   documents the preference, does not enforce it.
#: * ``non_eu_fallback`` — a non-EU CNA (MITRE root or a downstream
#:   authority). First-class fallback, not a default.
CNARole = Literal["eu_preferred", "non_eu_fallback"]


class CVERequestError(Exception):
    """Wraps any CNA-side failure the concrete adapter binding hit.

    Concrete EXTEND-time bindings (an ENISA-affiliated EU CNA client,
    a MITRE fallback client) wrap their CNA-specific errors in this
    class so the compile-target adapter surface sees one exception
    regardless of the bound authority. Carries the ``cna_role`` of the
    binding that failed so the audit stream can log which lane raised.
    """

    def __init__(
        self,
        message: str,
        *,
        cna_role: CNARole,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.cna_role: CNARole = cna_role
        self.__cause__ = cause


@dataclass(frozen=True)
class CVERequest:
    """Payload the ``publish_advisory`` step hands the adapter.

    Structural only; the shape pins what the adapter *needs* to
    request a CVE, not how any specific CNA models its intake form.
    Concrete EXTEND-time bindings translate this into the CNA-specific
    request shape (CVE Automation Working Group JSON, an authority's
    portal form, etc.).

    Fields
    ------
    case_id
        Correlation key from the playbook's ``__case_id__`` variable.
        Used only for adapter-side audit correlation; not forwarded
        to the CNA verbatim (the case id is internal to the operator).
    product
        Free-text product name the advisory is for. Rendered into
        the CNA's ``product_name`` slot by the binding.
    affected_versions
        Enumeration of the affected-version identifiers the operator
        confirmed at validation. Format is operator-choice (semver,
        CPE, build id); the adapter passes them through opaquely.
    fix_ref
        Reference to the validated fix (patch commit, build id,
        signed release attestation). Populated from the playbook's
        ``__fix_ref__``. Attached to the CVE request so the CNA has
        a citable fix pointer alongside the advisory.
    summary
        One-sentence advisory summary. The concrete binding rejects
        empty / whitespace-only strings; SKELETON does not enforce
        (validation lives with the binding).
    """

    case_id: str
    product: str
    affected_versions: tuple[str, ...]
    fix_ref: str
    summary: str
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CVEIdentifier:
    """The identifier the CNA returned.

    Structural only; carries the CVE id string and the role of the
    authority that assigned it so downstream advisory-publication and
    audit can distinguish an EU-preferred assignment from a fallback
    assignment.

    Fields
    ------
    cve_id
        The assigned identifier (``CVE-YYYY-NNNNN`` format). Validated
        at the concrete-binding boundary; SKELETON does not enforce.
    assigning_cna_role
        Which lane the assignment came from, mirroring the
        :data:`CNARole` the adapter was bound to. Carried into the
        advisory-audit trail so a reviewer can join the id back to
        the operator's runtime binding policy.
    """

    cve_id: str
    assigning_cna_role: CNARole


@dataclass(frozen=True)
class CVERequestResponse:
    """Return value the adapter surfaces to the compile-target wrapper.

    Fields
    ------
    identifier
        The :class:`CVEIdentifier` the bound CNA returned.
    receipt_ref
        Opaque reference to the CNA-side receipt / case number for
        the request. Written to the audit stream so a reviewer can
        cross-check the operator's advisory against the CNA-side
        record without re-querying.
    """

    identifier: CVEIdentifier
    receipt_ref: str


@runtime_checkable
class CVERequestAdapter(Protocol):
    """Dispatch surface a compile-target adapter binds against.

    A concrete EXTEND-time binding — an ENISA-affiliated EU CNA
    client, a MITRE fallback client, a manual-mediator stub — realises
    this protocol. The compile-target adapter dispatches to whatever
    binding the operator's runtime carries; the framework does not
    pre-select. Runtime-neutral (no ``temporalio`` / ``langgraph`` /
    n8n imports).
    """

    #: The role the bound CNA plays in the operator's runtime graph.
    #: Immutable per instance; the operator picks the role at bind
    #: time and the compile-target adapter's dispatch reads it to log
    #: which lane was taken. Two bindings with different roles are
    #: two distinct adapter instances.
    cna_role: CNARole

    def request_cve(self, request: CVERequest) -> CVERequestResponse:
        """Request one CVE identifier from the bound CNA.

        Raises
        ------
        CVERequestError
            On any CNA-side failure. The concrete binding wraps its
            own exception in :class:`CVERequestError` and re-raises
            so the compile-target adapter has one exception class to
            observe regardless of the bound authority.
        """
        ...
