"""Tests for compilers/_shared/lm_endpoint_guard.

Covers:
- The classification heuristic (EU / non-EU / unknown).
- The override env var (SECOPS_NG_LM_ENDPOINT_NON_EU_ACK) flips a non-EU
  fail-loud into a no-op.
- extract_lm_endpoints walks both playbook_variables and per-step
  x_secops_ng.lm.endpoint hooks.
- assert_playbook_eu_resident fires on the first non-EU endpoint with
  the override unset, and passes when the override is set or the
  endpoints are EU.
- render_lm_endpoint_guard_module renders deterministic, ast.parse-able
  Python that itself exposes assert_eu_resident_endpoint with the same
  raise / no-raise behaviour as the compile-time helper.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

from compilers._shared.lm_endpoint_guard import (
    ACK_ENV_VAR,
    EU_ALLOWLIST_SUFFIXES,
    EndpointResidency,
    LMEndpoint,
    NonEUEndpointError,
    assert_eu_resident_endpoint,
    assert_playbook_eu_resident,
    classify_endpoint,
    extract_lm_endpoints,
    render_lm_endpoint_guard_module,
)


# ---------------------------------------------------------------------------
# Classification heuristic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.mistral.ai/v1/chat/completions",
        "api.mistral.ai",
        "https://eu-west-1.foo.example.com",
        "https://eu.example.com",
        "https://api.aleph-alpha.com/complete",
        "https://endpoints.ai.cloud.ovh.net/v1",
        "https://generative.scw.cloud/v1",
        "https://EU-CENTRAL-1.example.com",  # case-insensitive
    ],
)
def test_classify_endpoint_eu(endpoint: str) -> None:
    assert classify_endpoint(endpoint) == EndpointResidency.EU


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.openai.com/v1/chat/completions",
        "api.anthropic.com",
        "https://us-east-1.example.com/v1",
        "https://apac-southeast-1.example.com",
        "https://API.OPENAI.COM/v1",  # case-insensitive
    ],
)
def test_classify_endpoint_non_eu(endpoint: str) -> None:
    assert classify_endpoint(endpoint) == EndpointResidency.NON_EU


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://my-private-gateway.internal/v1",
        "https://lm.operator.example/v1",
        "",
        "   ",
        "https://localhost:8080",
    ],
)
def test_classify_endpoint_unknown(endpoint: str) -> None:
    assert classify_endpoint(endpoint) == EndpointResidency.UNKNOWN


def test_eu_subdomain_of_openai_classifies_eu_not_non_eu() -> None:
    """``eu-frankfurt-1.api.openai.com`` should pass; the EU prefix wins."""
    assert classify_endpoint("https://eu-frankfurt-1.api.openai.com") == EndpointResidency.EU


# ---------------------------------------------------------------------------
# Override env var
# ---------------------------------------------------------------------------


def test_assert_raises_on_non_eu_without_override() -> None:
    with pytest.raises(NonEUEndpointError) as excinfo:
        assert_eu_resident_endpoint(
            "https://api.openai.com/v1",
            env={},
            source_path="workflow.classify.x_secops_ng.lm.endpoint",
        )
    msg = str(excinfo.value)
    assert "api.openai.com" in msg
    assert ACK_ENV_VAR in msg
    assert "workflow.classify.x_secops_ng.lm.endpoint" in msg
    assert "docs/sovereignty/eu-resident-lm-guard.md" in msg


def test_assert_passes_on_non_eu_with_override_set() -> None:
    # Should not raise.
    assert_eu_resident_endpoint(
        "https://api.openai.com/v1",
        env={ACK_ENV_VAR: "1"},
    )
    assert_eu_resident_endpoint(
        "https://api.openai.com/v1",
        env={ACK_ENV_VAR: "true"},
    )


def test_assert_passes_on_eu_endpoint() -> None:
    assert_eu_resident_endpoint("https://api.mistral.ai/v1/chat/completions", env={})


def test_assert_passes_on_unknown_endpoint() -> None:
    # Unknown hostnames are not blocked — self-hosted gateways must work.
    assert_eu_resident_endpoint("https://my-private-gateway.internal/v1", env={})


def test_override_empty_string_does_not_count() -> None:
    with pytest.raises(NonEUEndpointError):
        assert_eu_resident_endpoint("https://api.openai.com/v1", env={ACK_ENV_VAR: ""})


# ---------------------------------------------------------------------------
# Playbook walk
# ---------------------------------------------------------------------------


def _playbook(variables=None, workflow=None) -> dict[str, Any]:
    return {
        "playbook_variables": variables or {},
        "workflow": workflow or {},
    }


def test_extract_lm_endpoints_from_playbook_variables() -> None:
    pb = _playbook(
        variables={
            "LM_ENDPOINT": {"name": "LM_ENDPOINT", "value": "https://api.mistral.ai/v1"},
            "OTHER": {"name": "OTHER", "value": "irrelevant"},
            "MODEL_ENDPOINT": {"name": "MODEL_ENDPOINT", "value": "https://api.openai.com/v1"},
        }
    )
    eps = extract_lm_endpoints(pb)
    paths = {ep.source_path for ep in eps}
    assert paths == {
        "playbook_variables.LM_ENDPOINT.value",
        "playbook_variables.MODEL_ENDPOINT.value",
    }


def test_extract_lm_endpoints_from_workflow_steps() -> None:
    pb = _playbook(
        workflow={
            "classify": {
                "x_secops_ng": {"lm": {"endpoint": "https://api.openai.com/v1"}}
            },
            "summarise": {
                "x_secops_ng": {"lm": {"endpoint": "https://api.mistral.ai/v1"}}
            },
            "plain_step": {"x_secops_ng": {}},
        }
    )
    eps = extract_lm_endpoints(pb)
    # Deterministic ordering — sorted by step id.
    assert [ep.source_path for ep in eps] == [
        "workflow.classify.x_secops_ng.lm.endpoint",
        "workflow.summarise.x_secops_ng.lm.endpoint",
    ]


def test_extract_lm_endpoints_ignores_non_string_values() -> None:
    pb = _playbook(
        variables={
            "LM_ENDPOINT": {"name": "LM_ENDPOINT", "value": None},
            "LLM_ENDPOINT": {"name": "LLM_ENDPOINT", "value": 42},
        }
    )
    assert extract_lm_endpoints(pb) == []


# ---------------------------------------------------------------------------
# Whole-playbook hook (the compile-time contract)
# ---------------------------------------------------------------------------


def test_assert_playbook_raises_on_first_non_eu_without_override() -> None:
    pb = _playbook(
        variables={
            "LM_ENDPOINT": {
                "name": "LM_ENDPOINT",
                "value": "https://api.openai.com/v1",
            }
        }
    )
    with pytest.raises(NonEUEndpointError):
        assert_playbook_eu_resident(pb, env={})


def test_assert_playbook_passes_with_override() -> None:
    pb = _playbook(
        variables={
            "LM_ENDPOINT": {
                "name": "LM_ENDPOINT",
                "value": "https://api.openai.com/v1",
            }
        }
    )
    inspected = assert_playbook_eu_resident(pb, env={ACK_ENV_VAR: "1"})
    assert [ep.endpoint for ep in inspected] == ["https://api.openai.com/v1"]


def test_assert_playbook_passes_when_all_endpoints_eu() -> None:
    pb = _playbook(
        variables={
            "LM_ENDPOINT": {
                "name": "LM_ENDPOINT",
                "value": "https://api.mistral.ai/v1",
            }
        },
        workflow={
            "classify": {
                "x_secops_ng": {"lm": {"endpoint": "https://endpoints.ai.cloud.ovh.net/v1"}}
            }
        },
    )
    inspected = assert_playbook_eu_resident(pb, env={})
    assert len(inspected) == 2


def test_assert_playbook_passes_on_empty_playbook() -> None:
    assert assert_playbook_eu_resident({}, env={}) == []


# ---------------------------------------------------------------------------
# Renderable runtime module
# ---------------------------------------------------------------------------


def test_render_lm_endpoint_guard_module_is_deterministic() -> None:
    a = render_lm_endpoint_guard_module()
    b = render_lm_endpoint_guard_module()
    assert a == b


def test_render_lm_endpoint_guard_module_parses_as_python() -> None:
    src = render_lm_endpoint_guard_module()
    ast.parse(src)


def test_runtime_module_classifies_and_raises(monkeypatch, tmp_path: Path) -> None:
    """The rendered runtime module is importable and enforces the same posture."""
    src = render_lm_endpoint_guard_module()
    target = tmp_path / "_lm_endpoint_guard_runtime.py"
    target.write_text(src, encoding="utf-8")

    spec = importlib.util.spec_from_file_location(
        "_secops_ng_lm_endpoint_guard_runtime_test", target
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)

        assert mod.classify_endpoint("https://api.openai.com/v1") == "non_eu"
        assert mod.classify_endpoint("https://api.mistral.ai/v1") == "eu"
        assert mod.classify_endpoint("https://internal.local") == "unknown"

        monkeypatch.delenv(mod.ACK_ENV_VAR, raising=False)
        with pytest.raises(mod.NonEUEndpointError):
            mod.assert_eu_resident_endpoint("https://api.openai.com/v1")

        monkeypatch.setenv(mod.ACK_ENV_VAR, "1")
        mod.assert_eu_resident_endpoint("https://api.openai.com/v1")  # no raise

        mod.assert_eu_resident_endpoint("https://api.mistral.ai/v1")  # always passes
    finally:
        sys.modules.pop(spec.name, None)


def test_runtime_module_does_not_import_third_party() -> None:
    """The rendered runtime module must be stdlib-only."""
    src = render_lm_endpoint_guard_module()
    tree = ast.parse(src)
    third_party_markers = (
        "opentelemetry",
        "requests",
        "httpx",
        "datadog",
        "honeycomb",
        "newrelic",
    )
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                names = [node.module]
        for n in names:
            for marker in third_party_markers:
                assert not n.startswith(marker), (n, marker)


def test_runtime_module_carries_allowlist_in_sync() -> None:
    """The runtime sibling must enumerate exactly the same allowlist suffixes."""
    src = render_lm_endpoint_guard_module()
    for suffix in EU_ALLOWLIST_SUFFIXES:
        assert suffix in src, suffix


# ---------------------------------------------------------------------------
# LMEndpoint dataclass shape
# ---------------------------------------------------------------------------


def test_lmendpoint_is_frozen() -> None:
    ep = LMEndpoint(endpoint="https://api.mistral.ai/v1", source_path="x")
    with pytest.raises(Exception):
        ep.endpoint = "mutated"  # type: ignore[misc]
