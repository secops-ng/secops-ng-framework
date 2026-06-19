#!/usr/bin/env bash
# SKELETON scaffold for examples/langgraph/contractual_obligations_tracker.
#
# At the SKELETON layer this script only keeps the local CACAO mirror
# byte-identical to the canonical playbook source. The LangGraph workflow
# emitter binding, the per-execution obligation-evidence artefact, and
# the byte-parity golden land in the F-WF-10 CORE-FANOUT-LG sibling
# card Aurora queues after this SKELETON merges.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/contractual_obligations_tracker/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

echo "contractual_obligations_tracker (langgraph): playbook mirror refreshed."
echo "Workflow emission deferred to F-WF-10 CORE-FANOUT-LG."
