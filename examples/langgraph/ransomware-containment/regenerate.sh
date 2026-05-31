#!/usr/bin/env bash
# Regenerate the committed LangGraph worked-example artefacts from the
# canonical CACAO playbook. Run from the repo root after any change to
# the playbook or to compilers/langgraph/*.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/ransomware-containment/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

# Emit GraphSpec + generated state bindings from the canonical playbook.
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.emit  "${CANON}" > "${HERE}/graph_spec.json"
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.state "${CANON}" > "${HERE}/state_bindings.py"
