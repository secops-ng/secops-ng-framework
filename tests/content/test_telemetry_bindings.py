"""Resolution tests for content/telemetry/ OCSF bindings.

Asserts each binding JSON parses, validates against the
content-model telemetry schema, and carries the OCSF v1.4.0 class_uid
the phishing-triage playbook references. Class UIDs are pinned against
the upstream OCSF v1.4.0 schema; do not change without verifying at
https://schema.ocsf.io/1.4.0/.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_DIR = REPO_ROOT / "content" / "telemetry"
SCHEMA_PATH = REPO_ROOT / "content-model" / "telemetry.schema.json"

# Pinned OCSF v1.4.0 class UIDs. Verified against schema.ocsf.io 2026-05-30.
EXPECTED_BINDINGS = {
    "telemetry.ocsf.account_change@v1": {
        "class_uid": 3001,
        "class_name": "Account Change",
        "category_uid": 3,
    },
    "telemetry.ocsf.api_activity@v1": {
        "class_uid": 6003,
        "class_name": "API Activity",
        "category_uid": 6,
    },
    "telemetry.ocsf.authentication@v1": {
        "class_uid": 3002,
        "class_name": "Authentication",
        "category_uid": 3,
    },
    "telemetry.ocsf.email_activity@v1": {
        "class_uid": 4009,
        "class_name": "Email Activity",
        "category_uid": 4,
    },
    "telemetry.ocsf.email_url_activity@v1": {
        "class_uid": 4012,
        "class_name": "Email URL Activity",
        "category_uid": 4,
    },
    "telemetry.ocsf.file_activity@v1": {
        "class_uid": 1001,
        "class_name": "File System Activity",
        "category_uid": 1,
    },
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize("stable_id", sorted(EXPECTED_BINDINGS))
def test_binding_resolves_and_matches_ocsf_v1_4_0(
    stable_id: str, validator: Draft202012Validator
) -> None:
    path = TELEMETRY_DIR / f"{stable_id}.json"
    assert path.is_file(), f"missing telemetry binding file: {path}"

    doc = _load(path)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    assert not errors, "\n".join(
        f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"
        for e in errors
    )

    assert doc["stable_id"] == stable_id

    ocsf = doc["ocsf"]
    expected = EXPECTED_BINDINGS[stable_id]
    assert ocsf["version"] == "1.4.0", (
        f"{stable_id}: OCSF version must be pinned to 1.4.0"
    )
    assert ocsf["class_uid"] == expected["class_uid"], (
        f"{stable_id}: class_uid {ocsf['class_uid']} != OCSF v1.4.0 "
        f"{expected['class_uid']}"
    )
    assert ocsf["class_name"] == expected["class_name"]
    assert ocsf["category_uid"] == expected["category_uid"]
