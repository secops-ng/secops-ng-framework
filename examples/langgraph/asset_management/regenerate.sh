#!/usr/bin/env bash
# Regenerate the committed asset_management LangGraph worked-example
# artefacts from the canonical CACAO playbook. Run from the repo root
# after any change to the playbook source, to compilers/langgraph/*,
# or to the LangGraph asset-inventory-delta node adapter.
#
# F-WF-ASSET CORE-FANOUT-LANGGRAPH: the per-execution asset-inventory-
# delta artefact under evidence/ is materialised by the sibling
# ``regenerate.py`` script in this directory; that artefact targets
# the LangGraph asset-inventory-delta node adapter rather than the
# whole graph topology.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/asset_management/playbook.cacao.json"
MIRROR="${HERE}/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${MIRROR}"

# Emit GraphSpec + generated state bindings from the mirrored playbook.
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.emit  "${MIRROR}" > "${HERE}/graph_spec.json"
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.state "${MIRROR}" > "${HERE}/state_bindings.py"

# Materialise the dependency-free audit-mirror sibling. See
# docs/observability/audit-mirror.md for the co-location rationale.
PYTHONPATH="${REPO_ROOT}" python -m compilers._shared.audit_mirror_cli \
    --out "${HERE}/_audit_mirror.py"

# Materialise the representative asset-inventory-delta artefact under
# evidence/ via the LangGraph asset-inventory-delta node adapter.
PYTHONPATH="${REPO_ROOT}" python "${HERE}/regenerate.py"
