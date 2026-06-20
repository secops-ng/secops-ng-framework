#!/usr/bin/env bash
# Regenerate the committed LangGraph worked-example artifact for the
# F-SV-02 EUDIW typed-input pattern. Run from the repo root after any
# change to ``patterns/eidas2_wallet/`` or the LangGraph node under
# ``compilers/langgraph/patterns/``.
#
# Unlike F-WF-* worked examples this script does not emit a workflow
# graph: the F-SV-02 pattern is input-only (it describes the bundle a
# workflow ACCEPTS, not the graph it runs), so the example covers the
# input-side materialisation only. The materialised bundle under
# ``typed_input/`` is produced by the sibling ``regenerate.py``.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"

# Materialise the representative typed-input bundle under
# typed_input/ via the LangGraph pattern node.
PYTHONPATH="${REPO_ROOT}" python "${HERE}/regenerate.py"
