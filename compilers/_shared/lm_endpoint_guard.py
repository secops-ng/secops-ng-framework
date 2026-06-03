"""EU-resident LM endpoint guard — shared compile-time hook + renderable runtime module.

SecOps-NG is a sovereign-security Digital Commons. Its default posture is that
any Language Model (LM) endpoint reached from a compiled workflow lives in the
European Union. This module enforces that posture in two places:

1. **Compile time.** The reference compilers (``compilers.n8n``,
   ``compilers.temporal``, ``compilers.langgraph``) walk a parsed playbook and,
   for every LM endpoint they would emit into the generated example, call
   :func:`assert_eu_resident_endpoint`. If the endpoint resolves to a non-EU
   region under the heuristic below and the operator has not set the documented
   override env var, the compile fails fast with a clear error pointing at the
   override.

2. **Runtime.** Emitted examples co-locate a generated ``_lm_endpoint_guard.py``
   sibling module (rendered by :func:`render_lm_endpoint_guard_module`) that
   re-applies the same check at process startup. If an operator hand-edits
   the compiled artifact to swap in a non-EU endpoint without setting the
   override env var, the artifact raises ``NonEUEndpointError`` at startup
   instead of silently exfiltrating prompts.

Heuristic
---------
An endpoint URL or hostname is treated as **non-EU** when ANY of the following
hold (after lowercasing):

* The hostname has a leading region segment matching ``us-*`` or ``apac-*``
  (typical for cloud-provider regional subdomains, e.g. ``us-east-1...``,
  ``apac-southeast-1...``).
* The hostname ends in ``.openai.com`` or ``.anthropic.com`` *without* an
  explicit EU subdomain prefix (``eu-*.openai.com`` or ``eu.openai.com``
  pass; ``api.openai.com`` does not).

It is treated as **EU-resident** when:

* The hostname matches any entry in :data:`EU_ALLOWLIST_SUFFIXES` (Mistral EU,
  Aleph Alpha, OVHcloud AI Endpoints, Scaleway Generative APIs).
* The hostname has a leading region segment matching ``eu-*`` (e.g.
  ``eu-west-1.example.com``).

Anything that is neither explicitly non-EU nor explicitly EU is treated as
**unknown**. Unknown endpoints currently pass the guard — we are deliberately
not blocking self-hosted deployments, private gateways, or operator-owned
hostnames the project cannot enumerate. The override env var exists so an
operator who knowingly wires a non-EU endpoint can document the trade-off
once, in the open, rather than work around the guard by obfuscating hostnames.

Override
--------
Set ``SECOPS_NG_LM_ENDPOINT_NON_EU_ACK=1`` in the operator environment to
acknowledge a non-EU endpoint. The override is per-process: it covers every
endpoint the compiled artifact reaches, but it does not change residency posture
— the workflow simply loses its EU-residency guarantee, and that fact should be
disclosed in the operator's own deployment notes.

This module is dependency-free (stdlib only) so it can be imported and the
runtime variant rendered with no third-party packages installed.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

__all__ = [
    "ACK_ENV_VAR",
    "EU_ALLOWLIST_SUFFIXES",
    "EndpointResidency",
    "LMEndpoint",
    "NonEUEndpointError",
    "assert_eu_resident_endpoint",
    "classify_endpoint",
    "extract_lm_endpoints",
    "render_lm_endpoint_guard_module",
]

#: Override env var name. Documented at docs/sovereignty/eu-resident-lm-guard.md.
ACK_ENV_VAR = "SECOPS_NG_LM_ENDPOINT_NON_EU_ACK"

#: Known EU-hosted LM provider hostname suffixes. Maintained as a small,
#: hand-curated allowlist — extending it is a deliberate community decision,
#: not an automated probe. Suffixes are matched against the lower-cased
#: hostname; both bare hostnames and full URLs are accepted by the heuristic
#: helpers below.
#:
#: Entries:
#:   * Mistral EU — ``api.mistral.ai`` (Mistral states EU residency on
#:     ``api.mistral.ai``; the ``*.mistral.ai`` umbrella covers regional
#:     subdomains they may add later).
#:   * Aleph Alpha — ``api.aleph-alpha.com`` (German provider).
#:   * OVHcloud AI Endpoints — ``ai-endpoints.eu-*.endpoints.ai.cloud.ovh.net``
#:     and the parent ``endpoints.ai.cloud.ovh.net`` (OVHcloud EU regions only
#:     currently expose AI endpoints).
#:   * Scaleway Generative APIs — ``*.scw.cloud`` (Scaleway is EU-only).
EU_ALLOWLIST_SUFFIXES: tuple[str, ...] = (
    "api.mistral.ai",
    ".mistral.ai",
    "api.aleph-alpha.com",
    ".aleph-alpha.com",
    "endpoints.ai.cloud.ovh.net",
    ".scw.cloud",
)

# Hostname patterns that mark an endpoint as non-EU. ``us-*`` and ``apac-*``
# are matched as the leading region label of the hostname; the openai /
# anthropic suffixes are matched at the end. EU prefixes are tested first so
# ``eu-west-1.api.openai.com`` (hypothetical) classifies EU, not non-EU.
_NON_EU_REGION_PREFIX = re.compile(r"^(us|apac)-[a-z0-9-]+\.")
_EU_REGION_PREFIX = re.compile(r"^eu(-[a-z0-9-]+)?\.")
_NON_EU_SUFFIXES: tuple[str, ...] = (
    ".openai.com",
    ".anthropic.com",
)


class EndpointResidency:
    """Symbolic residency labels returned by :func:`classify_endpoint`."""

    EU = "eu"
    NON_EU = "non_eu"
    UNKNOWN = "unknown"


class NonEUEndpointError(RuntimeError):
    """Raised when a non-EU LM endpoint is reached without the operator override.

    The error message names the offending endpoint and points at the env-var
    override so an operator can either fix the endpoint or document the
    deliberate non-EU choice in one step.
    """


@dataclass(frozen=True)
class LMEndpoint:
    """A single LM endpoint found in a playbook.

    Attributes
    ----------
    endpoint:
        The endpoint URL or bare hostname as recorded in the playbook.
    source_path:
        Dotted path into the playbook JSON where the endpoint was found,
        for error messages — e.g. ``playbook_variables.LM_ENDPOINT.value``
        or ``workflow.classify.x_secops_ng.lm.endpoint``.
    """

    endpoint: str
    source_path: str


def _hostname(endpoint: str) -> str:
    """Return the lower-cased hostname for an endpoint URL or bare hostname.

    Accepts schemed URLs (``https://api.openai.com/v1``), schemeless URLs
    (``api.openai.com/v1``), and bare hostnames (``api.openai.com``).
    """
    text = endpoint.strip().lower()
    if not text:
        return ""
    # urlparse needs a scheme to populate ``hostname``; if there's no ``://``
    # treat the input as a bare hostname (possibly with a path tail).
    if "://" not in text:
        text = text.split("/", 1)[0]
        return text
    parsed = urlparse(text)
    return (parsed.hostname or "").lower()


def classify_endpoint(endpoint: str) -> str:
    """Classify ``endpoint`` as ``EU``, ``NON_EU``, or ``UNKNOWN``.

    See module docstring for the heuristic. The function is pure — no DNS,
    no network, no env-var reads.
    """
    host = _hostname(endpoint)
    if not host:
        return EndpointResidency.UNKNOWN

    # EU allowlist (most specific) wins outright.
    for suffix in EU_ALLOWLIST_SUFFIXES:
        if suffix.startswith("."):
            if host.endswith(suffix) or host == suffix.lstrip("."):
                return EndpointResidency.EU
        else:
            if host == suffix or host.endswith("." + suffix):
                return EndpointResidency.EU

    # Explicit EU region prefix.
    if _EU_REGION_PREFIX.match(host):
        return EndpointResidency.EU

    # Non-EU region prefix (us-*, apac-*).
    if _NON_EU_REGION_PREFIX.match(host):
        return EndpointResidency.NON_EU

    # Generic non-EU provider suffix.
    for suffix in _NON_EU_SUFFIXES:
        if host.endswith(suffix):
            return EndpointResidency.NON_EU

    return EndpointResidency.UNKNOWN


def assert_eu_resident_endpoint(
    endpoint: str,
    *,
    env: Mapping[str, str] | None = None,
    source_path: str = "<unknown>",
) -> None:
    """Raise :class:`NonEUEndpointError` if ``endpoint`` is non-EU and override is unset.

    Parameters
    ----------
    endpoint:
        Endpoint URL or hostname to check.
    env:
        Environment mapping to read the override from. Defaults to
        ``os.environ`` when ``None``. Passing a dict makes the function
        deterministic in tests.
    source_path:
        Optional dotted path describing where this endpoint came from in
        the playbook — surfaced in the error message so operators can find
        and fix the offending entry quickly.
    """
    if classify_endpoint(endpoint) != EndpointResidency.NON_EU:
        return
    src = os.environ if env is None else env
    if src.get(ACK_ENV_VAR, "").strip() in ("1", "true", "TRUE", "True"):
        return
    raise NonEUEndpointError(
        f"LM endpoint {endpoint!r} (at {source_path}) resolves to a non-EU region. "
        f"SecOps-NG defaults to EU-resident LM endpoints. To acknowledge a deliberate "
        f"non-EU choice (and forfeit the workflow's EU-residency posture), set "
        f"{ACK_ENV_VAR}=1 in the operator environment. See "
        f"docs/sovereignty/eu-resident-lm-guard.md for the full posture and the "
        f"current EU allowlist."
    )


def extract_lm_endpoints(playbook: Mapping[str, Any]) -> list[LMEndpoint]:
    """Walk a parsed CACAO playbook dict and return every LM endpoint found.

    Endpoints are discovered in two conventional locations:

    * ``playbook_variables.<name>.value`` where the variable's ``name`` (or
      key) hints at an LM endpoint (``LM_ENDPOINT``, ``LLM_ENDPOINT``,
      ``MODEL_ENDPOINT``, case-insensitive).
    * ``workflow.<step_id>.x_secops_ng.lm.endpoint`` where a step explicitly
      records the LM endpoint it would call.

    Returns endpoints in deterministic order — playbook_variables first
    (sorted by key), then workflow steps (sorted by step id).
    """
    found: list[LMEndpoint] = []

    pv = playbook.get("playbook_variables") or {}
    if isinstance(pv, Mapping):
        for key in sorted(pv):
            entry = pv[key]
            if not isinstance(entry, Mapping):
                continue
            name = str(entry.get("name") or key).upper()
            if not _looks_like_lm_endpoint_name(name):
                continue
            value = entry.get("value")
            if isinstance(value, str) and value:
                found.append(
                    LMEndpoint(
                        endpoint=value,
                        source_path=f"playbook_variables.{key}.value",
                    )
                )

    workflow = playbook.get("workflow") or {}
    if isinstance(workflow, Mapping):
        for step_id in sorted(workflow):
            step = workflow[step_id]
            if not isinstance(step, Mapping):
                continue
            xs = step.get("x_secops_ng") or {}
            if not isinstance(xs, Mapping):
                continue
            lm = xs.get("lm") or {}
            if not isinstance(lm, Mapping):
                continue
            endpoint = lm.get("endpoint")
            if isinstance(endpoint, str) and endpoint:
                found.append(
                    LMEndpoint(
                        endpoint=endpoint,
                        source_path=f"workflow.{step_id}.x_secops_ng.lm.endpoint",
                    )
                )

    return found


def _looks_like_lm_endpoint_name(name: str) -> bool:
    """True when a playbook-variable name conventionally holds an LM endpoint."""
    upper = name.upper()
    return upper in {"LM_ENDPOINT", "LLM_ENDPOINT", "MODEL_ENDPOINT"} or upper.endswith(
        "_LM_ENDPOINT"
    ) or upper.endswith("_LLM_ENDPOINT")


def assert_playbook_eu_resident(
    playbook: Mapping[str, Any],
    *,
    env: Mapping[str, str] | None = None,
) -> list[LMEndpoint]:
    """Compile-time hook: assert every LM endpoint in ``playbook`` is EU-resident.

    Returns the list of endpoints that were inspected (so emitters can log
    or surface them). Raises :class:`NonEUEndpointError` on the first
    non-EU endpoint with the override unset.
    """
    endpoints = extract_lm_endpoints(playbook)
    for ep in endpoints:
        assert_eu_resident_endpoint(
            ep.endpoint, env=env, source_path=ep.source_path
        )
    return endpoints


# ---------------------------------------------------------------------------
# Renderable runtime module
# ---------------------------------------------------------------------------

# This source is co-located by emitters alongside the generated artifact so
# the compiled example re-checks endpoint residency at process startup. It is
# stdlib-only and deterministic — same input → byte-identical bytes.
_RUNTIME_GUARD_SOURCE = '''\
"""EU-resident LM endpoint guard (runtime sibling).

Emitted alongside the compiled example. Re-applies the SecOps-NG
EU-residency heuristic at process startup so that hand-edits to the
artifact (or runtime endpoint overrides) do not silently route prompts
to a non-EU region without the operator explicitly acknowledging the
trade-off.

Override: set the environment variable
``SECOPS_NG_LM_ENDPOINT_NON_EU_ACK=1`` to acknowledge a non-EU endpoint.
See ``docs/sovereignty/eu-resident-lm-guard.md`` in the framework for
the full posture.

This module is stdlib-only.
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse

ACK_ENV_VAR = "SECOPS_NG_LM_ENDPOINT_NON_EU_ACK"

EU_ALLOWLIST_SUFFIXES = (
    "api.mistral.ai",
    ".mistral.ai",
    "api.aleph-alpha.com",
    ".aleph-alpha.com",
    "endpoints.ai.cloud.ovh.net",
    ".scw.cloud",
)

_NON_EU_REGION_PREFIX = re.compile(r"^(us|apac)-[a-z0-9-]+\\.")
_EU_REGION_PREFIX = re.compile(r"^eu(-[a-z0-9-]+)?\\.")
_NON_EU_SUFFIXES = (".openai.com", ".anthropic.com")


class NonEUEndpointError(RuntimeError):
    """Raised at startup when a non-EU LM endpoint is reached without the override."""


def _hostname(endpoint):
    text = (endpoint or "").strip().lower()
    if not text:
        return ""
    if "://" not in text:
        return text.split("/", 1)[0]
    return (urlparse(text).hostname or "").lower()


def classify_endpoint(endpoint):
    host = _hostname(endpoint)
    if not host:
        return "unknown"
    for suffix in EU_ALLOWLIST_SUFFIXES:
        if suffix.startswith("."):
            if host.endswith(suffix) or host == suffix.lstrip("."):
                return "eu"
        else:
            if host == suffix or host.endswith("." + suffix):
                return "eu"
    if _EU_REGION_PREFIX.match(host):
        return "eu"
    if _NON_EU_REGION_PREFIX.match(host):
        return "non_eu"
    for suffix in _NON_EU_SUFFIXES:
        if host.endswith(suffix):
            return "non_eu"
    return "unknown"


def assert_eu_resident_endpoint(endpoint, source_path="<runtime>"):
    """Raise NonEUEndpointError if ``endpoint`` is non-EU and override is unset."""
    if classify_endpoint(endpoint) != "non_eu":
        return
    if os.environ.get(ACK_ENV_VAR, "").strip() in ("1", "true", "TRUE", "True"):
        return
    raise NonEUEndpointError(
        "LM endpoint " + repr(endpoint) + " (at " + source_path + ") resolves to a "
        "non-EU region. SecOps-NG defaults to EU-resident LM endpoints. To "
        "acknowledge a deliberate non-EU choice (and forfeit the workflow's "
        "EU-residency posture), set " + ACK_ENV_VAR + "=1 in the operator "
        "environment. See docs/sovereignty/eu-resident-lm-guard.md."
    )


__all__ = [
    "ACK_ENV_VAR",
    "EU_ALLOWLIST_SUFFIXES",
    "NonEUEndpointError",
    "assert_eu_resident_endpoint",
    "classify_endpoint",
]
'''


def render_lm_endpoint_guard_module() -> str:
    """Return the source of the runtime guard module to co-locate with the artifact.

    The output is stdlib-only and deterministic so emitters can write it
    next to generated code in any deployment target without pulling in
    third-party packages.
    """
    return _RUNTIME_GUARD_SOURCE


def _iter_known_eu_hosts() -> Iterable[str]:
    """Internal helper used by tests to assert the allowlist tuple is honoured."""
    yield from EU_ALLOWLIST_SUFFIXES
