#!/usr/bin/env bash
# Regenerate the committed Temporal worked-example artefacts for the
# IT and security support-agent workflow from the canonical CACAO
# playbook. Run from the repo root after any change to the playbook
# source, the Temporal compiler, or the Temporal interaction-evidence
# activity adapter.
#
# The per-execution interaction-evidence artefact under ``evidence/``
# is materialised by the sibling ``regenerate.py`` script in this
# directory; that artefact targets the Temporal interaction-evidence
# activity (reused F-CP-02 incidents stream) rather than the whole
# workflow graph.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/it_security_support_agent/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

# Emit the Temporal workflow stub from the canonical playbook via the
# unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${CANON}" \
    --target temporal \
    --out "${HERE}/workflow.temporal.py"

# Materialise the representative interaction-evidence artefact under
# evidence/ via the Temporal interaction-evidence activity adapter.
PYTHONPATH="${REPO_ROOT}" python "${HERE}/regenerate.py"
