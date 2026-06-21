#!/usr/bin/env bash
# Regenerate the committed LangGraph worked-example artefacts for the
# supply-chain-security workflow from the canonical CACAO playbook.
# Run from the repo root after any change to the playbook source, the
# LangGraph compiler, the F-WF-SCS primitives, or the LangGraph
# supply-chain evidence node adapter.
#
# The per-execution supply-chain-evidence artefact under ``evidence/``
# is materialised by the sibling ``regenerate.py`` script in this
# directory; that artefact targets the LangGraph supply-chain evidence
# node adapter rather than the whole workflow graph.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/supply_chain_security/playbook.cacao.json"
MIRROR="${HERE}/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${MIRROR}"

# Emit GraphSpec + generated state bindings from the canonical playbook.
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.emit  "${CANON}" > "${HERE}/graph_spec.json"
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.state "${CANON}" > "${HERE}/state_bindings.py"

# Materialise the dependency-free audit-mirror sibling. See
# docs/observability/audit-mirror.md for the co-location rationale.
PYTHONPATH="${REPO_ROOT}" python -m compilers._shared.audit_mirror_cli \
    --out "${HERE}/_audit_mirror.py"

# Materialise the representative supply-chain-evidence artefact under
# evidence/ via the LangGraph supply-chain node adapter.
PYTHONPATH="${REPO_ROOT}" python "${HERE}/regenerate.py"
