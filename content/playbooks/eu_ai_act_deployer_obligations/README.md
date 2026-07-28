# eu_ai_act_deployer_obligations

**Status:** SKELETON · **Stable id:** `playbook.eu_ai_act_deployer_obligations@v1`

Operator-side EU AI Act **Article 26 deployer-obligation lifecycle**, gated
by the **Article 27 fundamental-rights impact assessment**.

## Why this playbook exists

Every other EU AI Act artifact in this catalogue anchors on the
**provider** — Art. 9 risk management, Art. 11 technical documentation,
Art. 13 transparency, Art. 15 robustness, Art. 72 post-market monitoring,
Art. 73 serious-incident reporting.

This is the first on the **deployer** side: the operator who runs a
third-party high-risk AI system in production rather than placing one on
the market. Most organisations reading this framework are deployers, not
providers.

## Lifecycle

| Step | Discharges | Notes |
|---|---|---|
| `confirm_intended_use` | Art. 26(1), Art. 26(7) | Reconciles the declared deployment context against the intended purpose in the provider's instructions for use. Gates on the worker-representative notice where the deployer is an employer — a precondition, not a parallel task. |
| `assign_human_oversight` | Art. 26(2) | Records a named person or role against each of the four limbs: competence, training, authority, support. |
| `monitor_operation` | Art. 26(4), Art. 26(5) | Per-window monitoring, plus the input-data relevance determination where the deployer controls the input surface. Carries the lifecycle's only escalation edge. |
| `assess_fundamental_rights_impact` | Art. 27(1)(a)–(f), Art. 27(4) | In-scope determination first; then the six-element assessment, complementing any existing GDPR DPIA; closes on notification to the market-surveillance authority. |
| `retain_logs_and_evidence` | Art. 26(6) | Log-control determination and applied retention period; emits the dated cycle-evidence artifact. |

## Three things to get right

**The escalation edge has three triggers, not one.** Art. 26(5) folds
together routine monitoring that feeds the provider's Art. 72 loop; a
risk determination under Art. 79(1), which compels notification **and
suspension of use**; and identification of a serious incident, which
compels immediate *sequenced* notification — provider first, then
importer or distributor, then the market-surveillance authorities.
Collapsing them loses the suspension duty.

**The FRIA complements a DPIA; it does not repeat or replace one.**
Art. 27(4) is explicit. The DPIA asks what the processing does to
personal data; the FRIA asks what the deployment does to fundamental
rights, and the affected populations are not necessarily the same. Where
the operator holds a DPIA, this playbook reads it and assesses only the
remainder — it never composes one. That is
`playbook.data_protection_impact_assessment@v1`.

**Two obligations are hard pre-deployment gates.** The Art. 26(7) worker
notice must be given *before* putting the system into service, and the
Art. 27 assessment is performed *prior to deploying*. Neither can be
remediated retrospectively, so both are modelled as preconditions rather
than as steps that can run late.

## SKELETON scope

Step bodies are **declared, not bound**. The deployment register, the
oversight-assignment record, the input-data control surface, the
monitoring signal source, the FRIA template and the log store are all
operator-owned adapter-bound surfaces. `compile_targets` is empty; the
CORE sibling binds the deterministic primitives and lands the
three-target compile examples with byte-parity goldens.

Two things are deliberately deferred rather than guessed:

- **The Art. 27(5) notification template** has not been published by the
  AI Office. The step declares the submission contract and emits a dated
  notification record instead of inventing a template shape.
- **No per-step D3FEND pin.** These are compliance-governance
  disciplines over a third-party system, not countermeasures on the
  operator's estate. `mappings.yaml` names `D3-OAM` as the one candidate
  worth re-examining at CORE, so the analysis is not re-derived.

## Inbound mappings

- [`content/mappings/eu_ai_act/article-26-deployer-obligations.yaml`](../../mappings/eu_ai_act/article-26-deployer-obligations.yaml) — six atoms, one per obligation limb
- [`content/mappings/eu_ai_act/article-27-fria.yaml`](../../mappings/eu_ai_act/article-27-fria.yaml) — assessment elements and the Art. 27(4) complementarity rule

## Related

- `playbook.data_protection_impact_assessment@v1` — the GDPR Art. 35 DPIA the FRIA complements
- `playbook.eu_ai_act_risk_management@v1` — the provider-side Art. 9 lifecycle
- `eu_ai_act:art-73-serious-incident-reporting` — the provider-side chain the serious-incident branch hands off to

## References

- EU AI Act — [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj), Articles 26, 27, and 79(1)
- GDPR — [Regulation (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj), Article 35
- OASIS CACAO v2.0 specification
