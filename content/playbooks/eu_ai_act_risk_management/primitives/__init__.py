"""Shared primitives for the EU AI Act Art. 9 risk-management playbook.

Single source of truth for the deterministic, replay-friendly helpers the
per-target CORE action bodies (n8n, Temporal, LangGraph) all bind against.
Each primitive lands as its own module so the per-target compilers depend
only on what they need:

* :mod:`.classification` -- :func:`classify_high_risk_system`
  (identify high-risk AI system). Resolves which of Art. 6's three paths
  applies and pins the Annex III area. Carries the Art. 6(3) derogation
  explicitly, and refuses to emit one without the Art. 6(4) documented
  assessment behind it.

* :mod:`.assessment` -- :func:`assess_art9_risks`
  (assess risk under Art. 9(2)). Scores one iteration's risks against the
  operator's area-scoped acceptability threshold. Acceptability is per risk
  because Art. 9(5) is per risk; re-scored observations within an iteration
  collapse so a breach is not double-reported.

* :mod:`.documentation` -- :func:`assemble_technical_documentation`
  (assemble technical documentation). Assembles the Art. 11 / Annex IV
  bundle and pins the two commit anchors
  ``kri.transparency_doc_freshness_age@v1`` reads. Annex IV(5) must
  reference the register the assessment produced.

* :mod:`.post_market` -- :func:`record_post_market_signal`
  (monitor post-market signals). Records one Art. 72 observation and derives
  whether it reopens the Art. 9(2) cycle. Flags Art. 73 escalation without
  performing it — that notification has its own clock and its own artifact.

Every primitive is pure: no clock reads, no network, no LLM. Every instant
and date the lifecycle needs is supplied as an input, which is what lets a
run be replayed and lets the byte-parity goldens exist at all.
"""

from __future__ import annotations

__all__: list[str] = []
