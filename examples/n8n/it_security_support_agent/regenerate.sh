#!/usr/bin/env bash
# SKELETON scaffold for examples/n8n/it_security_support_agent.
#
# At the SKELETON layer this script only keeps the local CACAO mirror
# byte-identical to the canonical playbook source. The n8n workflow
# emitter binding, the per-execution interaction-evidence artefact, and
# the byte-parity golden land in the CORE-FANOUT-N8N sibling that
# follows this SKELETON.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/it_security_support_agent/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

echo "it_security_support_agent (n8n): playbook mirror refreshed."
echo "Workflow emission deferred to CORE-FANOUT-N8N."
