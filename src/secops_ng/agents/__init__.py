"""LangGraph agent definitions.

This package contains the reasoning graphs that drive agent decisions inside
SecOps-NG activities. Each agent is an explicit state machine: nodes are
deterministic reasoning steps, edges encode allowed transitions, and the full
trace is auditable after the fact.

Agents are invoked *from* Temporal activities — they never own durability
themselves. Keep agent state serialisable so it can be inspected, replayed,
and compared across runs.
"""
