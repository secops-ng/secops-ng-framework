# executive_metrics

CACAO v2 starter playbook for the executive metrics rollup: resolve the
operator's pinned KPI/KRI catalog → evaluate each entry against its
thresholds over the rollup window → score control effectiveness → emit a
structured board-ready summary (with a board-attention flag when any
metric hits its breach band). The playbook formalises effectiveness
review into auditable, restartable state; it does not prescribe a board
template or own the distribution channel.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.executive_metrics@v1`).

## Regulatory anchors

The rollup pins NIS2 Article 21(2)(f) (policies and procedures to
assess the effectiveness of cybersecurity risk-management measures)
and DORA Article 6 (ICT risk-management framework, periodic review).
The scoring shape mirrors OSCAL CA-2 (Control Assessments) and PM-6
(Measures of Performance) so an operator's existing GRC anchors carry
through to the emitted summary. No Sigma rule IDs are pinned — the
workflow is a reporting workflow, not a detection workflow.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Worked
examples, fixtures, and the per-playbook mappings overlay are
intentionally omitted from this skeleton card and will land in the
CORE / EXTEND siblings against the shared CACAO fixture at
`tests/compilers/_shared/fixtures/executive_metrics_rollup.cacao.json`.
This directory ships the portable content only.

## Sources

- OASIS CACAO v2.0 specification
- NIS2 Directive (EU) 2022/2555, Article 21(2)(f)
- DORA Regulation (EU) 2022/2554, Article 6
- ENISA — Good practices for incident reporting and metrics
- OSCAL — CA-2 (Control Assessments) and PM-6 (Measures of Performance)
