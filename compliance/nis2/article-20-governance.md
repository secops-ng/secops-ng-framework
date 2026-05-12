# NIS2 Article 20 — Governance

**Directive (EU) 2022/2555, Article 20 — Governance**

## Obligation

Article 20(1) requires Member States to ensure that the **management bodies**
of essential and important entities **approve** the cybersecurity
risk-management measures taken by those entities to comply with Article 21,
**oversee** their implementation, and **can be held liable** for
infringements by the entity of that article.

Article 20(2) requires Member States to ensure that members of the
management bodies of essential and important entities are required to
**follow training**, and to encourage essential and important entities to
offer similar training to their employees on a regular basis, so that they
gain sufficient knowledge and skills to enable them to identify risks and
assess cybersecurity risk-management practices and their impact on the
services provided by the entity.

## SecOps-NG mapping

SecOps-NG is a technical framework; it cannot make a management body
accountable. What it can do is produce **evidence that a management body had
a real basis on which to approve and oversee** the cybersecurity programme.

| Article 20 element | SecOps-NG contribution |
|--------------------|------------------------|
| Management body approval (20(1)) | Each Temporal workflow's deterministic replay log gives the management body a reviewable record of how risk-management measures behaved in practice. The community-maintained `workflows/` directory makes the *measures themselves* inspectable, not just their outputs. |
| Oversight of implementation (20(1)) | Durable workflow state means the management body can ask, at any time, "what is currently running, what decided what, on whose authority" and receive a deterministic answer. |
| Liability (20(1)) | Out of technical scope. The framework does not change legal accountability; it makes the factual record auditable. |
| Training (20(2)) | Out of technical scope. The project does, however, publish workflow walkthroughs that double as training material for security teams. |

## Evidence stream

- `../evidence/governance/approvals/` — operator-authored records of
  management-body approval events (date, scope, signatures or equivalent).
  Format TBD; will be JSON keyed by approval-decision id.
  <!-- coder:wire — emitter not yet implemented. -->
- Workflow replay logs (Temporal-native) — already produced by every
  workflow execution. The compliance layer will collect pointers, not
  duplicate the logs.

## Gaps

- The framework provides no opinion on **what** a management body should
  approve. That is a governance decision for each operator.
- No automation for training-completion tracking. This is intentionally out
  of scope; operators should use their existing HR / LMS tooling.

## References

- Directive (EU) 2022/2555, Article 20(1), (2).
- Recital (78) on the need for management-body engagement.
