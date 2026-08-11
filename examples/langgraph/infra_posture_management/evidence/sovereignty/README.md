# examples/langgraph/infra_posture_management/evidence/sovereignty/

Committed worked example for the F-SV-04 sovereignty posture evidence
stream on the langgraph target. `sovereignty-posture-attestation.json`
is one deterministic record — one observation per sovereignty-cluster
indicator, no aggregate — emitted through the langgraph adapter by
`regenerate.py` (run from the repo root with `PYTHONPATH=.`). The
byte-parity golden lives at
`tests/examples/langgraph/infra_posture_management/evidence/sovereignty/test_golden.py`.
