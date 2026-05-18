"""Incident-timeline pattern — durable append-only incident timeline builder.

Operators (or upstream detectors) append events to an in-flight incident
via signal. The workflow canonicalises them (sorted, deduplicated) and on
``close`` persists a single timeline artifact to disk. The workflow body
is deterministic; all disk I/O lives in the activity layer.
"""
