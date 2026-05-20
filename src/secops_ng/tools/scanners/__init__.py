"""Scanner adapters: thin wrappers, env-var configured.

Each adapter exposes a ``scan`` coroutine returning artifact paths.
Adapters are signature-only at this stage — wire-up is follow-on work.
"""

from secops_ng.tools.scanners import nessus, nikto, openvas, wapiti

__all__ = ["nessus", "nikto", "openvas", "wapiti"]
