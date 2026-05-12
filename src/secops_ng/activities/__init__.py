"""Side-effecting tool / integration adapters.

Activities are where SecOps-NG touches the outside world: calling
vulnerability scanners, querying SIEMs, posting to ticketing systems,
invoking LLM backends. They may fail, retry, and time out.

LangGraph nodes call into this package; the node itself stays thin and the
side effect is encapsulated here so it can be mocked in tests.
"""
