# NIS2 Article 22 — Union-Level Coordinated Risk Assessments of Critical Supply Chains

**Directive (EU) 2022/2555, Article 22**

## Obligation

Article 22(1) provides that the Cooperation Group, in cooperation with the
Commission and ENISA, may carry out **coordinated security risk assessments
of specific critical ICT services, ICT systems or ICT product supply chains**,
taking into account technical and, where relevant, non-technical risk
factors.

Article 22(2) requires the Commission, after consulting the Cooperation
Group and ENISA, to identify the specific critical ICT services, systems or
products that may be subject to those coordinated risk assessments.

This article does not place a direct duty on individual entities. It is a
**Union-level coordination instrument**. However, the outputs of these
assessments inform the supply-chain risk decisions an entity must make
under Article 21(2)(d), and entities that operate critical ICT services
themselves may be consulted as part of an assessment.

## SecOps-NG mapping

| Article 22 element | SecOps-NG contribution |
|--------------------|------------------------|
| Union-level coordinated risk assessment input | The Sovereign Provider KB in `secops-ng-deployment` is a public, community-maintained dataset of European providers with verifiable claims. It is suitable as **input material** to a coordinated risk assessment exercise. |
| Acting on assessment outputs (linking to 21(2)(d)) | When the Cooperation Group publishes findings, operators can encode those findings as filters or required-claim fields in the KB schema (e.g. via a schema bump). |

## Evidence stream

- The Sovereign Provider KB itself is the evidence — it is public, versioned,
  and verifiable.
- `../evidence/supply-chain/coordinated-assessment-alignment.md` —
  operator-authored statement of how their supply-chain decisions take
  Article 22 outputs into account.
  <!-- coder:wire — alignment-statement template TBD. -->

## Gaps

- The framework cannot substitute for participation in the Cooperation
  Group process.
- Non-technical risk factors (geopolitical, regulatory, jurisdictional)
  are captured in the KB schema only at a coarse-grained level today.

## References

- Directive (EU) 2022/2555, Article 22(1), (2).
- Recital (90) on the rationale for Union-level coordinated assessments.
