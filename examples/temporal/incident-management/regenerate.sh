#!/usr/bin/env bash
# Regenerate the committed Temporal worked-example artefact from the
# canonical CACAO playbook. Run from the repo root after any change to
# the playbook, to compilers/temporal/*, or to this directory's
# core_body.overlay.json.
#
# SKELETON-wave seam (F-WF-05 CORE-WIRE-TMPRL): the Temporal mirror is
# the canonical CACAO playbook with the per-step core_body bindings
# declared in core_body.overlay.json applied on top. The canonical
# source itself carries no core_body blocks yet — it gains them when
# the sibling CORE-WIRE-LG card lands and a single source of truth is
# promoted upward. See core_body.overlay.json _meta for the binding
# layout and the wave-seam closure condition.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/incident-management/playbook.cacao.json"
OVERLAY="${HERE}/core_body.overlay.json"
MIRROR="${HERE}/playbook.cacao.json"

# Apply the SKELETON-wave per-step core_body overlay onto the canonical
# CACAO source to produce the Temporal mirror. Pure-stdlib Python so the
# regeneration has no extra runtime deps.
python "${HERE}/apply_overlay.py" \
    --canonical "${CANON}" \
    --overlay "${OVERLAY}" \
    --out "${MIRROR}"

# Emit the Temporal workflow stub from the mirrored (overlay-applied)
# playbook via the unified CLI. The compiler picks up the per-step
# core_body bindings and renders activity bodies that call the named
# primitives.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${MIRROR}" \
    --target temporal \
    --out "${HERE}/workflow.temporal.py"
