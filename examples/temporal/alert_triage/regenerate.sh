#!/usr/bin/env bash
# Regenerate the committed Temporal worked-example artefacts from the
# canonical alert_triage CACAO source. Run from the repo root after any
# change to the source playbook or to compilers/temporal/*.
#
# The canonical source is content/playbooks/alert_triage.cacao.yaml.
# This script mirrors it into a JSON form alongside the worked example
# (the Temporal emitter consumes JSON via the CACAO parser) and then
# re-emits workflow.temporal.py from that JSON mirror via the unified
# tools.compile CLI.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON_YAML="${REPO_ROOT}/content/playbooks/alert_triage.cacao.yaml"
MIRROR_JSON="${HERE}/playbook.cacao.json"

# Mirror the YAML source to a byte-deterministic JSON form (sorted keys,
# 2-space indent, trailing newline). The two formats round-trip through
# `yaml.safe_load` + `json.dumps`; the schema is format-agnostic.
python -c "
import json, yaml
from pathlib import Path
src = Path('${CANON_YAML}')
dst = Path('${MIRROR_JSON}')
data = yaml.safe_load(src.read_text(encoding='utf-8'))
dst.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
"

# Emit the Temporal workflow stub from the JSON mirror via the unified
# CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${MIRROR_JSON}" \
    --target temporal \
    --out "${HERE}/workflow.temporal.py"
