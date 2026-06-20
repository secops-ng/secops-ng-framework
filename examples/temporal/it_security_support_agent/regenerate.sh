#!/usr/bin/env bash
# SKELETON scaffold for examples/temporal/it_security_support_agent.
#
# At the SKELETON layer this script only keeps the local CACAO mirror
# byte-identical to the canonical playbook source. The Temporal workflow
# emitter binding, the per-execution interaction-evidence artefact, and
# the byte-parity golden land in the CORE-FANOUT-TMP sibling that
# follows this SKELETON.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/it_security_support_agent/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

echo "it_security_support_agent (temporal): playbook mirror refreshed."
echo "Workflow emission deferred to CORE-FANOUT-TMP."
