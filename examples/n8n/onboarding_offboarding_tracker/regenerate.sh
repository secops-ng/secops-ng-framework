#!/usr/bin/env bash
# SKELETON scaffold for examples/n8n/onboarding_offboarding_tracker.
#
# At the SKELETON layer this script only keeps the local CACAO mirror
# byte-identical to the canonical playbook source. The n8n workflow
# emitter binding, the per-execution access-evidence artefact, and
# the byte-parity golden land in the F-WF-11 CORE-FANOUT-N8N sibling
# card queued after this SKELETON merges.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

echo "onboarding_offboarding_tracker (n8n): playbook mirror refreshed."
echo "Workflow emission deferred to F-WF-11 CORE-FANOUT-N8N."
