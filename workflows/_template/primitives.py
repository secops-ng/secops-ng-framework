"""Primitives for the <workflow-name> workflow.

Re-export the canonical graph nodes, DSPy signatures, and state types
from the library module under ``src/secops_ng/workflows/``. The library
module owns the implementation; this file is a stable surface the
cookbook example imports from so adapters can swap the underlying
graph without rewriting the example.

Replace the imports below when you copy this template.
"""

from __future__ import annotations

# TODO: re-export from the matching library module, e.g.
#
# from secops_ng.workflows.<workflow_name> import (
#     <StateType>,
#     build_graph,
#     configure_default_lm,
#     graph,
# )
#
# __all__ = [
#     "<StateType>",
#     "build_graph",
#     "configure_default_lm",
#     "graph",
# ]
