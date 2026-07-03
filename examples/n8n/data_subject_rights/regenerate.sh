#!/usr/bin/env bash
# Regenerate the committed n8n worked-example artefact from the
# canonical CACAO playbook. Run from the repo root after any change to
# the playbook or to compilers/n8n/*.
#
# The canonical source is YAML so it can carry inline commentary
# alongside the schema-valid document the parser consumes. The n8n
# emitter reads either format via the CACAO parser; the worked example
# mirrors the source into a byte-deterministic JSON form
# (sorted keys, 2-space indent, trailing newline) so the parity test
# has a stable JSON companion to compare against the sibling targets.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
CANON_YAML="${REPO_ROOT}/content/playbooks/data_subject_rights/playbook.cacao.yaml"
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

# Emit the n8n workflow from the JSON mirror via the unified CLI.
PYTHONPATH="${REPO_ROOT}" python -m tools.compile \
    "${MIRROR_JSON}" \
    --target n8n \
    --out "${HERE}/workflow.n8n.json"
