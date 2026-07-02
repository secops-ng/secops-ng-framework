"""Shared primitives for the mfa_secured_comms (F-WF-MFA) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.probe` -- :func:`probe_mfa_coverage`
  (probe-mfa-coverage). Walks a per-principal record set (enrolment
  state, enforcement state, last-successful-MFA-event timestamp) and
  emits the deterministic MFA-coverage snapshot the assess- and
  attestation steps consume. Read-only-by-contract: no enrolment, no
  factor reset, no policy mutation is represented.

* :mod:`.assess` -- :func:`assess_continuous_auth`
  (assess-continuous-auth). Compares per-session age against the
  operator's declared re-authentication cadence and returns the
  session-staleness verdict list. Policy-gap branch (session in a
  scope with no declared cadence) is reported as a policy gap rather
  than a stale session.

* :mod:`.verify` -- :func:`verify_oob_channel`
  (verify-oob-channels). Reads a per-channel reachability observation
  set (reachable, independence-path-observed, last-tested-at) and
  emits the deterministic OOB-channel status list. The primitive
  models a documented test transaction against the channel; it does
  not deliver a real emergency notification.

* :mod:`.artifact` --
  :func:`build_mfa_posture_attestation_artifact`
  (evidence-capture). Assembles the JSON-native
  authentication-and-secured-communications posture attestation
  record. The deterministic ``artifact_id`` derives from
  ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` --
  ``compile_target`` is intentionally NOT part of the id so the three
  reference compilers re-derive byte-identical bytes (CORE-FANOUT
  byte-parity contract).

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/asset_management/primitives/__init__.py`` and
``content/playbooks/iam_auditor/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidMfaPostureAttestationArtifactError,
    build_mfa_posture_attestation_artifact,
    derive_mfa_posture_attestation_artifact_id,
)
from .assess import (
    InvalidContinuousAuthAssessmentError,
    assess_continuous_auth,
)
from .probe import (
    InvalidMfaCoverageProbeError,
    probe_mfa_coverage,
)
from .verify import (
    InvalidOobChannelVerificationError,
    verify_oob_channel,
)

__all__ = [
    "InvalidContinuousAuthAssessmentError",
    "InvalidMfaCoverageProbeError",
    "InvalidMfaPostureAttestationArtifactError",
    "InvalidOobChannelVerificationError",
    "assess_continuous_auth",
    "build_mfa_posture_attestation_artifact",
    "derive_mfa_posture_attestation_artifact_id",
    "probe_mfa_coverage",
    "verify_oob_channel",
]
