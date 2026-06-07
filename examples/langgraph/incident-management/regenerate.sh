#!/usr/bin/env bash
# Regenerate the committed LangGraph worked-example artefacts from the
# canonical CACAO playbook. Run from the repo root after any change to
# the playbook, to compilers/langgraph/*, or to this directory's
# core_body.overlay.json.
#
# SKELETON-wave seam (F-WF-05 CORE-WIRE-LG): the LangGraph mirror is
# the canonical CACAO playbook with the per-step core_body bindings
# declared in core_body.overlay.json applied on top. The canonical
# source itself carries no core_body blocks yet — it gains them in a
# subsequent card that promotes the three-target parity wave (n8n,
# Temporal, LangGraph) upward to a single source of truth. See
# core_body.overlay.json _meta for the binding layout and the
# wave-seam closure condition.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON="${REPO_ROOT}/content/playbooks/incident-management/playbook.cacao.json"
OVERLAY="${HERE}/core_body.overlay.json"
MIRROR="${HERE}/playbook.cacao.json"

# Apply the SKELETON-wave per-step core_body overlay onto the canonical
# CACAO source to produce the LangGraph mirror. Pure-stdlib Python so
# the regeneration has no extra runtime deps.
python "${HERE}/apply_overlay.py" \
    --canonical "${CANON}" \
    --overlay "${OVERLAY}" \
    --out "${MIRROR}"

# Emit GraphSpec + generated state bindings from the mirrored
# (overlay-applied) playbook. The state emitter picks up the per-step
# core_body bindings and renders tool bodies that call the named
# primitives.
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.emit  "${MIRROR}" > "${HERE}/graph_spec.json"
PYTHONPATH="${REPO_ROOT}" python -m compilers.langgraph.state "${MIRROR}" > "${HERE}/state_bindings.py"

# Materialise the dependency-free audit-mirror sibling. See
# docs/observability/audit-mirror.md for the co-location rationale.
PYTHONPATH="${REPO_ROOT}" python -m compilers._shared.audit_mirror_cli \
    --out "${HERE}/_audit_mirror.py"
