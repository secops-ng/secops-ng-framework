#!/usr/bin/env bash
# Regenerate the committed n8n worked-example artefacts for the
# IT and security support-agent workflow from the canonical CACAO
# playbook. Run from the repo root after any change to the playbook
# source or the n8n compiler.
#
# This CORE-FANOUT-N8N-WIRE script emits the workflow graph only —
# the per-execution interaction-evidence artefact under ``evidence/``
# is materialised by the GOLDEN sibling that follows this WIRE and is
# left as a placeholder at this layer.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/it_security_support_agent/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

# Emit the n8n workflow from the canonical playbook via the unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${CANON}" \
    --target n8n \
    --out "${HERE}/workflow.n8n.json"

# Defer interaction-evidence artefact materialisation to the GOLDEN sibling.
PYTHONPATH="${REPO_ROOT}" python "${HERE}/regenerate.py"
