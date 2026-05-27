"""SecOps-NG reference compilers.

Each compiler reads a SecOps-NG content artifact (currently: a CACAO v2
playbook) and emits an orchestrator-native definition. The artifact is
the source of truth; the emitted definition is the build output.

Launch targets:

- ``compilers.n8n`` — n8n workflow JSON (importable via the n8n UI).
- ``compilers.temporal`` — planned.
- ``compilers.langgraph`` — planned.
"""
