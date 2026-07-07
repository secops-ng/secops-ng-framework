#!/usr/bin/env bash
# Regenerate the committed Temporal worked-example artefact from the
# canonical CACAO playbook. Run from the repo root after any change to
# the playbook or to compilers/temporal/*.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON_YAML="${REPO_ROOT}/content/playbooks/business_continuity/playbook.cacao.yaml"
MIRROR_JSON="${HERE}/playbook.cacao.json"

# Mirror the canonical CACAO YAML into a byte-deterministic JSON form.
PYTHONPATH="${REPO_ROOT}" python -c "
import json
from pathlib import Path
import yaml
src = Path('${CANON_YAML}')
dst = Path('${MIRROR_JSON}')
data = yaml.safe_load(src.read_text(encoding='utf-8'))
dst.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
"

# Emit the Temporal workflow stub from the JSON mirror via the unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${MIRROR_JSON}" \
    --target temporal \
    --out "${HERE}/workflow.temporal.py"
