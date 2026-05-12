"""LangGraph workflow templates.

This package holds the ``StateGraph`` definitions that orchestrate SecOps
reasoning. Every node receives and returns an immutable
:class:`secops_ng.tool_io.ToolIO` subclass; LLM-facing steps are implemented
as DSPy modules so the prompts are versioned, testable code rather than
opaque strings.

Side-effecting integrations (SIEM lookups, ticketing, etc.) live in
``secops_ng.activities`` and are invoked from graph nodes.
"""
