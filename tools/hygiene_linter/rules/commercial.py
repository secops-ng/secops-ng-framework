# hygiene-linter: allow-file commercial.customer_language,commercial.pricing_language,commercial.b2b_language,commercial.gtm_language,commercial.consulting_language,commercial.sales_language,commercial.revenue_language,commercial.client_reference,commercial.strategy_doc_reference
"""Commercial-intent / strategy-language detection.

This rule is the defensive counterpart to the human Custodian's
semantic review. It does NOT try to be exhaustive — real semantic
review remains with the reviewer (AGENTS.md §5.7). What this rule
catches is the obvious set: terms whose mere presence in a
will-be-public file is a strong signal of strategy/commercial framing
that belongs in the private repo instead.

Severity is MEDIUM. The CLI exit code is only driven by HIGH findings,
so MEDIUM hits surface as warnings the reviewer should resolve but do
not block the build on their own. This keeps the false-positive cost
proportional to the certainty of the signal.

Each pattern is a word-boundary match against case-folded line text.
Multi-word patterns (``go-to-market``) are matched on the raw line so
hyphens are preserved.

This module necessarily contains every term it detects, so it matched its
own patterns eleven times. The ``allow-file`` pragma on line 1 exempts
those nine rules **by name**, rather than excluding the path: ``rules/`` is
production code where a genuine credential leak would still matter, so the
``credentials.*`` rules stay live here, and HIGH findings are
unsuppressable by any pragma in any case.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from tools.hygiene_linter.findings import Finding, Severity

# (pattern, rule_id_suffix, message)
_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\b(our|the)\s+customers?\b", re.IGNORECASE),
     "customer_language",
     "'our/the customer(s)' is commercial framing — community voice in public repos"),
    (re.compile(r"\b(pricing|price\s+tiers?|paid\s+tier|enterprise\s+tier)\b", re.IGNORECASE),
     "pricing_language",
     "pricing/tier language belongs in the private strategy repo"),
    (re.compile(r"\bB2B\b"),
     "b2b_language",
     "'B2B' is commercial framing — community voice in public repos"),
    (re.compile(r"\bgo-to-market\b", re.IGNORECASE),
     "gtm_language",
     "go-to-market language is internal strategy — keep in private repo"),
    (re.compile(r"\b(consulting|consultancy|consultant)\b", re.IGNORECASE),
     "consulting_language",
     "consulting framing is not the public NGO voice — Custodian must review"),
    (re.compile(r"\bsales(?:\s+pipeline|\s+funnel|\s+lead)?\b", re.IGNORECASE),
     "sales_language",
     "sales/funnel language is internal — keep in private repo"),
    (re.compile(r"\brevenue\b", re.IGNORECASE),
     "revenue_language",
     "revenue framing is internal — keep in private repo"),
    (re.compile(r"\bclient\s+(name|list|engagement|account)s?\b", re.IGNORECASE),
     "client_reference",
     "client/lead references must not appear in public repos"),
    (re.compile(r"\b(roadmap|strategy)\s+(deck|memo|doc)\b", re.IGNORECASE),
     "strategy_doc_reference",
     "strategy/roadmap doc references are internal — keep in private repo"),
]


def scan(path: str, lines: list[str]) -> Iterable[Finding]:
    for i, line in enumerate(lines, start=1):
        for pat, suffix, msg in _PATTERNS:
            m = pat.search(line)
            if m:
                yield Finding(
                    path=path, line=i,
                    rule=f"commercial.{suffix}",
                    severity=Severity.MEDIUM,
                    message=msg,
                    snippet=m.group(0),
                )
