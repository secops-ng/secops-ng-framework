#!/usr/bin/env bash
# Regenerate the committed worked-example artefacts from the CACAO playbook.
# Run from the repo root after any change to compilers/langgraph/*.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
PLAYBOOK="${HERE}/playbook.cacao.json"

# Mirror the canonical playbook byte-for-byte; the golden test
# (test_mirrored_cacao_matches_canonical_source) points here, so this
# script must actually refresh the mirror it is blamed for.
cp "${REPO_ROOT}/content/playbooks/data_exfil/playbook.cacao.json" "${PLAYBOOK}"

python -m compilers.langgraph.emit  "${PLAYBOOK}" > "${HERE}/graph_spec.json"
python -m compilers.langgraph.state "${PLAYBOOK}" > "${HERE}/state_bindings.py"

# Materialise the dependency-free audit-mirror sibling. See
# docs/observability/audit-mirror.md for the co-location rationale.
python -m compilers._shared.audit_mirror_cli --out "${HERE}/_audit_mirror.py"
