# compilers/

Reference compilers that consume canonical `../content/` artifacts and emit
orchestrator-native definitions. The artifact is the source of truth; the
emitted definition is the build output.

Launch targets:

- `n8n/`        emits n8n workflow JSON from CACAO
- `temporal/`   emits Temporal workflow stubs (Python) from CACAO
- `langgraph/`  emits LangGraph agent graphs from CACAO

Shared infrastructure:

- `_shared/`    CACAO parser, mapping resolver, common test harness

Out-of-launch-scope targets (community-contributed):

- `community/`  placeholders and contributor guide for MindStudio, Make,
                Zapier, StackAI, CrewAI
