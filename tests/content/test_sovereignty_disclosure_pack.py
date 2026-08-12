"""F-ADOPT-02 — sovereignty conformance disclosure pack.

Pins, mapped to the ROADMAP acceptance criteria:

1. The committed worked example regenerates byte-identically from the
   committed record and shipped baseline (deterministic renderer), and
   validates against the pack schema.
2. The redaction contract holds three ways: the serialised pack
   carries no forbidden marker; the schema structurally rejects a pack
   smuggling an ``observed_value``; and the renderer's own backstop
   refuses to serialise a leaking pack.
3. The honesty contract: the example pack carries its true failing
   rows and a boolean roll-up — all 26 indicators present, no
   score-shaped key anywhere.
4. ``--baseline`` refuses a quietly relaxed profile before rendering
   (exit 2), so a pack cannot be flattered by profile drift.
5. The two adoption surfaces (USED-BY.md, the self-attestation guide)
   point at the pack, so the feature is discoverable where operators
   actually look.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.render_disclosure_pack import (
    FORBIDDEN_MARKERS,
    RedactionError,
    render_pack,
    serialise_pack,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = REPO_ROOT / "content" / "profiles" / "sovereignty_conformance.yaml"
RECORD_PATH = (
    REPO_ROOT / "examples" / "temporal" / "infra_posture_management"
    / "evidence" / "sovereignty" / "sovereignty-posture-attestation.json"
)
PACK_PATH = RECORD_PATH.parent / "disclosure-pack.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "sovereignty-disclosure-pack.schema.json"


def _render_cli(*extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, "-m", "tools.render_disclosure_pack",
            str(RECORD_PATH), "--profile", str(PROFILE_PATH), *extra,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# 1. determinism + schema validity of the committed example
# ---------------------------------------------------------------------------


def test_committed_pack_regenerates_byte_identically() -> None:
    proc = _render_cli("--baseline", str(PROFILE_PATH))
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == PACK_PATH.read_text(encoding="utf-8"), (
        "committed disclosure-pack.json is stale — regenerate with "
        "python -m tools.render_disclosure_pack"
    )


def test_cli_is_byte_deterministic() -> None:
    assert _render_cli().stdout == _render_cli().stdout


def test_committed_pack_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(pack), key=str)
    assert not errors, [e.message for e in errors]


# ---------------------------------------------------------------------------
# 2. the redaction contract, three ways
# ---------------------------------------------------------------------------


def test_serialised_pack_carries_no_forbidden_marker() -> None:
    text = PACK_PATH.read_text(encoding="utf-8")
    for marker in FORBIDDEN_MARKERS:
        assert marker not in text, f"pack leaks {marker!r}"


def test_schema_rejects_smuggled_observed_value() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    )
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    sid = next(iter(pack["indicators"]))
    smuggled = copy.deepcopy(pack)
    smuggled["indicators"][sid]["observed_value"] = 0.97
    assert list(validator.iter_errors(smuggled)), (
        "schema accepted an indicator entry carrying observed_value — "
        "additionalProperties must stay false"
    )


def test_renderer_backstop_refuses_a_leaking_pack() -> None:
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    profile = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    pack = render_pack(record, profile, RECORD_PATH.read_bytes())
    pack["leak"] = "https://internal.example/endpoint"
    with pytest.raises(RedactionError, match="forbidden marker"):
        serialise_pack(pack)


# ---------------------------------------------------------------------------
# 3. the honesty contract
# ---------------------------------------------------------------------------


def test_pack_carries_the_true_failing_rows() -> None:
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    assert len(pack["indicators"]) == 26
    by = pack["indicators"]
    assert by["kpi.lm_endpoint_eu_residency_coverage@v1"]["outcome"] == "fail"
    assert by["kri.non_eu_critical_dependency_count@v1"]["outcome"] == "fail"
    assert pack["pass"] is False


def test_pack_is_scoreless() -> None:
    flat = PACK_PATH.read_text(encoding="utf-8").lower()
    for w in ("score", "ratio_of", "percent"):
        assert f'"{w}' not in flat, f"pack grew a {w}-shaped key"


def test_record_digest_matches_committed_record_bytes() -> None:
    import hashlib

    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    assert pack["record_sha256"] == hashlib.sha256(
        RECORD_PATH.read_bytes()
    ).hexdigest()


# ---------------------------------------------------------------------------
# 4. profile drift cannot flatter a pack
# ---------------------------------------------------------------------------


def test_relaxed_profile_without_override_is_refused(tmp_path: Path) -> None:
    profile = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    profile["stable_id"] = "profile.operator_derived@v1"
    profile["indicators"]["kpi.lm_endpoint_eu_residency_coverage@v1"][
        "max_band"
    ] = "warn"
    loosened = tmp_path / "loosened.yaml"
    loosened.write_text(yaml.safe_dump(profile), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, "-m", "tools.render_disclosure_pack",
            str(RECORD_PATH),
            "--profile", str(loosened),
            "--baseline", str(PROFILE_PATH),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, proc.stdout
    assert "lm_endpoint_eu_residency_coverage" in proc.stderr


# ---------------------------------------------------------------------------
# 5. the adoption surfaces point here
# ---------------------------------------------------------------------------


def test_adoption_surfaces_name_the_pack() -> None:
    for rel in ("USED-BY.md", "docs/contributing/self-attesting-adoption.md"):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "disclosure" in text.lower() and "DISCLOSURE.md" in text, (
            f"{rel} no longer points at the disclosure pack"
        )
