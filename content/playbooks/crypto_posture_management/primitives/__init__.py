"""Shared primitives for the NIS2 Art. 21(2)(h) crypto-posture playbook.

Single source of truth for the deterministic, replay-friendly helpers the
per-target CORE action bodies (n8n, Temporal, LangGraph) all bind against.

* :mod:`.policy` -- :func:`inventory_crypto_policy`. Composes the policy
  inventory and, crucially, declares which *concern* each clause governs.
  That is what makes every downstream finding interpretable: a posture that
  contradicts a stated clause is a **drift**, one the policy is silent about
  is a **gap**, and the two have different owners and different fixes.
  :func:`classify_against_policy` is the shared helper both probes use.

* :mod:`.certificates` -- :func:`probe_cert_posture`. Judges supplied
  certificate and cipher observations. Refuses PEM-shaped input at the
  boundary: findings carry references and observed parameters only.

* :mod:`.rotation` -- :func:`check_key_rotation`. Judges last-rotation dates
  against the interval clause. ``never_rotated`` is distinct from
  ``missed_rotation`` — the absence of a schedule is not a lapse in one.

* :mod:`.evidence` -- :func:`capture_crypto_evidence`. Assembles the dated
  attestation, carrying drift and gap as separate top-level counts because
  they route to different owners. ``posture_conforming`` is the conjunction,
  never an average.

* :mod:`.notify` -- :func:`plan_crypto_owner_notification`. Composes the
  owner notification and marks it ``dispatched: False``. Delivery is
  adapter-bound; a clean posture still produces a plan, because silence is
  indistinguishable from the run never happening.

Every primitive is pure: no clock reads, no network, no LLM. Every date and
instant is supplied. Nothing rotates a key, reissues a certificate, changes a
cipher suite or sends a message — the playbook is read-only against operator
infrastructure by construction, not by convention.
"""

from __future__ import annotations

__all__: list[str] = []
