#!/usr/bin/env bash
# Regenerate the committed worked-example artefacts from the canonical
# alert_triage CACAO source. Run from the repo root after any change to
# the source playbook or to compilers/langgraph/*.
#
# The canonical source is content/playbooks/alert_triage.cacao.yaml.
# This script mirrors it into a JSON form alongside the worked example
# (the LangGraph emitter consumes JSON via the CACAO parser) and then
# re-emits the GraphSpec + state bindings from that JSON mirror.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON_YAML="${REPO_ROOT}/content/playbooks/alert_triage.cacao.yaml"
MIRROR_JSON="${HERE}/playbook.cacao.json"

# Mirror the YAML source to a byte-deterministic JSON form (sorted keys,
# 2-space indent, trailing newline). The two formats round-trip through
# `yaml.safe_load` + `json.dumps`; the schema is format-agnostic.
python -c "
import json, sys, yaml
from pathlib import Path
src = Path('${CANON_YAML}')
dst = Path('${MIRROR_JSON}')
data = yaml.safe_load(src.read_text(encoding='utf-8'))
dst.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
"

# Emit GraphSpec + generated state bindings from the JSON mirror.
python -m compilers.langgraph.emit  "${MIRROR_JSON}" > "${HERE}/graph_spec.json"
python -m compilers.langgraph.state "${MIRROR_JSON}" > "${HERE}/state_bindings.py"

# Materialise the dependency-free audit-mirror sibling. See
# docs/observability/audit-mirror.md for the co-location rationale.
PYTHONPATH="${REPO_ROOT}" python -m compilers._shared.audit_mirror_cli \
    --out "${HERE}/_audit_mirror.py"
