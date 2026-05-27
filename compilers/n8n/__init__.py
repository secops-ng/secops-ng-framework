"""CACAO v2 → n8n workflow JSON reference compiler.

Public API:

    from compilers.n8n import compile_playbook, CompileResult

    result = compile_playbook(cacao_doc)
    json.dump(result.workflow, open("workflow.json", "w"), indent=2)

The compiler is deliberately self-contained: stdlib only, no n8n
dependency. The emitted JSON matches the shape the n8n UI accepts via
the "Import from File" workflow menu (n8n >= 1.0).

See ``README.md`` in this directory for the supported CACAO subset and
the documented lossy translations.
"""

from compilers.n8n.compiler import (
    CompileResult,
    CompilerWarning,
    compile_playbook,
)

__all__ = ["CompileResult", "CompilerWarning", "compile_playbook"]
