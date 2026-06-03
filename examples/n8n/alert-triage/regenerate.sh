#!/usr/bin/env bash
# Regenerate the committed n8n worked-example artefact from the canonical
# alert-triage CACAO source. Run from the repo root after any change to
# the source playbook or to compilers/n8n/*.
#
# The canonical source is content/playbooks/alert-triage.cacao.yaml.
# This script mirrors it into a byte-deterministic JSON form alongside
# the worked example (the n8n emitter consumes JSON via the CACAO parser)
# and then emits workflow.n8n.json from that JSON mirror.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON_YAML="${REPO_ROOT}/content/playbooks/alert-triage.cacao.yaml"
MIRROR_JSON="${HERE}/playbook.cacao.json"

# Mirror the YAML source to a byte-deterministic JSON form (sorted keys,
# 2-space indent, trailing newline). The two formats round-trip through
# `yaml.safe_load` + `json.dumps`; the schema is format-agnostic.
python - "${CANON_YAML}" "${MIRROR_JSON}" <<'PY'
import json, sys, yaml
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
data = yaml.safe_load(src.read_text(encoding='utf-8'))
dst.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

# Emit n8n workflow JSON from the JSON mirror via the unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${MIRROR_JSON}" \
    --target n8n \
    --out "${HERE}/workflow.n8n.json"
