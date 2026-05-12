"""Temporal workflow templates.

This package holds the durable, replayable workflow definitions that orchestrate
SecOps activities. Workflows here must remain deterministic: all side effects
belong in `secops_ng.activities`, all type contracts in `secops_ng.contracts`.

Workflows declared with `@workflow.defn` survive process restarts and can be
replayed from history — keep them pure.
"""
