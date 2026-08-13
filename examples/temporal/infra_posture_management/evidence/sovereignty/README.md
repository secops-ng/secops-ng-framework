# examples/temporal/infra_posture_management/evidence/sovereignty/

Committed worked example for the F-SV-04 sovereignty posture evidence
stream on the temporal target. `sovereignty-posture-attestation.json`
is one deterministic record — one observation per sovereignty-cluster
indicator, no aggregate — emitted through the temporal adapter by
`regenerate.py` (run from the repo root with `PYTHONPATH=.`). The
byte-parity golden lives at
`tests/examples/temporal/infra_posture_management/evidence/sovereignty/test_golden.py`.

`disclosure-pack.json` is the F-ADOPT-02 disclosure pack rendered
from this record against the shipped baseline
(`python -m tools.render_disclosure_pack <record> --baseline
content/profiles/sovereignty_conformance.yaml`). It carries the
record's true verdict — the reference posture does not (yet) hold —
and regenerates byte-identically via
`tests/content/test_sovereignty_disclosure_pack.py`. Format and
redaction contract: `content/evidence/sovereignty/DISCLOSURE.md`.
