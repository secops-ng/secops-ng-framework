"""Pydantic-typed tool contracts.

Tools are the leaf-level capabilities exposed to LangGraph agents (e.g. "fetch
CVE details", "look up asset owner", "open ticket"). Every tool in SecOps-NG
declares its inputs and outputs as Pydantic models — see
`secops_ng.tool_io.ToolIO` for the base class.

This boundary is intentional: it is the single place where untyped data from
external systems is forced through schema validation before it reaches an
agent or a workflow.
"""
