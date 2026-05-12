# NIS2 Control Mapping

This directory maps SecOps-NG capabilities to the **EU NIS2 Directive**
(Directive (EU) 2022/2555 of the European Parliament and of the Council of
14 December 2022 on measures for a high common level of cybersecurity across
the Union).

The mapping is scoped to **Articles 20–23**, which together define what an
essential or important entity must actually *do* about cybersecurity. Other
articles (definitions, scope, supervisory powers, sanctions) are referenced
where relevant but are not the focus of this scaffold.

## Articles covered

| Article | Subject                                                       | File |
|---------|---------------------------------------------------------------|------|
| 20      | Governance — management body responsibilities and training   | [article-20-governance.md](article-20-governance.md) |
| 21      | Cybersecurity risk-management measures (10 sub-items, a–j)   | [article-21-risk-management.md](article-21-risk-management.md) |
| 22      | Union-level coordinated risk assessments of critical supply chains | [article-22-supply-chain.md](article-22-supply-chain.md) |
| 23      | Reporting obligations — early warning, incident notification, final report | [article-23-reporting.md](article-23-reporting.md) |

## How to read these documents

Each article file follows the same structure:

1. **Obligation** — what the directive actually requires, with paragraph
   citations.
2. **SecOps-NG mapping** — which framework capabilities, workflows, or
   operational practices contribute to satisfying the obligation.
3. **Evidence stream** — what concrete artefact in `../evidence/` (or what
   workflow output) demonstrates that the control is operating.
4. **Gaps** — honest accounting of where the framework does not yet help,
   so operators know what they have to cover by other means.

## A note on legal weight

These documents are **operator-to-operator guidance**, not legal advice. The
authoritative text of NIS2 is the directive itself and the national
transposition laws of each Member State. Operators remain responsible for
their own compliance posture. The Custodian role in this project reviews
mappings for honesty, not for legal sufficiency.

## NIS2 implementation deadline

Member States were required to transpose NIS2 into national law by
**17 October 2024** (Article 41). Operators should consult the transposition
in their jurisdiction of establishment for the binding text.

<!-- coder:wire — evidence-stream pointers in each article file will become
     live references once Coder implements the workflow emitters in the
     `secops_ng.evidence` module. -->
