#!/usr/bin/env bash
# SKELETON scaffold for examples/temporal/infra_posture_management.
#
# At the SKELETON layer this script only keeps the local CACAO mirror
# byte-identical to the canonical playbook source. The Temporal workflow
# emitter binding, the per-execution posture-evidence artefact, and
# the byte-parity golden land in the F-WF-06 CORE-FANOUT-TMP sibling
# card queued as a follow-up after this SKELETON merges.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/infra_posture_management/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

echo "infra_posture_management (temporal): playbook mirror refreshed."
echo "Workflow emission deferred to F-WF-06 CORE-FANOUT-TMP."
