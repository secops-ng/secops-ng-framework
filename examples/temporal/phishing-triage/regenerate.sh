#!/usr/bin/env bash
# Regenerate the committed Temporal worked-example artefact from the
# canonical CACAO playbook. Run from the repo root after any change to
# the playbook or to compilers/temporal/*.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/phishing-triage/playbook.cacao.json"

# Keep the mirrored CACAO source byte-identical to the canonical playbook.
cp "${CANON}" "${HERE}/playbook.cacao.json"

# Emit the Temporal workflow stub from the canonical playbook via the
# unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${CANON}" \
    --target temporal \
    --out "${HERE}/workflow.temporal.py"
