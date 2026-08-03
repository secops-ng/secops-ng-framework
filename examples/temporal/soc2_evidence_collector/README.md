# examples/temporal/soc2_evidence_collector

Worked example emitted from
`content/playbooks/soc2_evidence_collector/playbook.cacao.json` by the
reference temporal compiler. **Generated — do not hand-edit.**

Regenerate after any change to the canonical source or to the compiler:

```sh
./examples/temporal/soc2_evidence_collector/regenerate.sh
```

All four action steps carry a `core_body` binding into
`content/playbooks/soc2_evidence_collector/primitives/`, so the emitted
artifact carries no operator-TODO notes. The four bodies are pure and offline:
no clock reads, no network, no LLM.

What the workflow does: reads the AICPA Trust Services Criteria crosswalk under
`content/mappings/soc2/`, joins the evidence references available for the
window onto the criteria they support, scores each criterion
`covered` / `draft_backed` / `uncovered`, and emits one dated readiness
document. It is readiness input for an auditor, never an audit opinion — see the
playbook README for the three boundaries this playbook deliberately does not
cross.
