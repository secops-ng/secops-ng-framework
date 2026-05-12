"""Temporal activities — the side-effecting units.

Activities are where SecOps-NG touches the outside world: calling vulnerability
scanners, querying SIEMs, posting to ticketing systems, invoking LLMs. They
may fail, retry, time out, and run on heterogeneous workers.

Anything non-deterministic, network-bound, or stateful belongs here — never in
`secops_ng.workflows`.
"""
