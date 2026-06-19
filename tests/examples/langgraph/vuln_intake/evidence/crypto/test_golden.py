"""F-CP-05 EXTEND-tests-goldens (LangGraph) — byte-parity replay golden.

Pins the committed crypto-attestation worked example for the LangGraph
target under ``examples/langgraph/vuln_intake/evidence/crypto/`` against
a fresh re-emission driven through the LangGraph node adapter at
:func:`compilers.langgraph.evidence.emit_crypto_attestation_artifact_node`.

The committed snapshot — ``secret-handling-attestation.json`` — is the
human-friendly rename of the deterministic ``<artifact_id>.json`` file
the shared emitter writes. This test re-runs the node adapter the way
a ``StateGraph`` would (state mapping in, partial state update out),
schema-validates the result against
``schemas/evidence/crypto-attestation.schema.json``, and asserts
byte-equality with the committed snapshot.

Coverage axes:

1. **Schema-conformant emit.** The re-emitted artifact validates
   against the crypto-attestation schema before the byte comparison
   runs, so a shape regression in the LangGraph adapter surfaces with
   a precise diagnostic.
2. **Byte-parity with the committed example.** The re-emitted
   artifact's on-disk bytes match the committed
   ``secret-handling-attestation.json`` exactly. If the shared emitter
   or LangGraph node adapter intentionally changes serialisation, the
   example must be regenerated via
   ``PYTHONPATH=. python examples/langgraph/vuln_intake/evidence/crypto/regenerate.py``
   and the new bytes committed alongside the change.
3. **env-only-injection assertion shape.** ``secret_handling`` carries
   the F-CP-05 mechanical assertions (``secrets_baked_in=False``,
   ``injection_mode='env'``, UPPER_SNAKE_CASE ``env_var_refs``).

Sibling note: ``CTX`` below is kept byte-identical to ``CTX`` in
``examples/langgraph/vuln_intake/evidence/crypto/regenerate.py``. The
filename in that path contains a hyphen, so the regenerate module
cannot be imported by ``import`` — the context is duplicated here on
purpose and the byte-parity assertion catches drift on either side.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
)
from compilers.langgraph.evidence import emit_crypto_attestation_artifact_node

REPO = Path(__file__).resolve().parents[6]
SCHEMA = REPO / "schemas" / "evidence" / "crypto-attestation.schema.json"
EXAMPLE_DIR = REPO / "examples" / "langgraph" / "vuln_intake" / "evidence" / "crypto"
GOLDEN = EXAMPLE_DIR / "secret-handling-attestation.json"


# Mirrors CTX in examples/langgraph/vuln_intake/evidence/crypto/regenerate.py.
# Kept byte-identical on purpose; the byte-parity test below catches
# drift on either side. Sorted keys in the on-disk record come from the
# shared emitter, not from this context — the input is intentionally in
# the same field order the bootstrap node that assembles
# CryptoAttestationContext would marshal.
CTX = CryptoAttestationContext(
    workflow_id="vulnerability_triage",
    execution_id="langgraph:vuln_intake_example_0001",
    compile_target="langgraph",
    regulation_refs=("nis2:art-21-2-h",),
    control_refs=(
        "control.crypto_policy_inventory@v1",
        "control.secret_injection_env_only@v1",
    ),
    secret_handling=SecretHandling(
        env_var_refs=(
            "CVE_FEED_API_TOKEN",
            "EPSS_FEED_API_TOKEN",
            "RISK_SUMMARY_LLM_API_KEY",
        ),
        secret_count=3,
    ),
    owner_role="platform-security-wg",
    owner_assigned_at="2026-01-15",
    captured_at=datetime(2026, 6, 7, 6, 0, 0, tzinfo=timezone.utc),
    source_url="https://example.org/runs/vuln_intake_example_0001",
    retention="P1Y",
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    """Schema validator for the crypto-attestation record.

    The crypto-attestation schema is self-contained — all enum / pattern
    constraints (including the env-var name regex and the const-pinned
    ``secrets_baked_in`` / ``injection_mode`` shape) live inline, so
    unlike the supply-chain stream this validator does not need an
    external ``referencing`` registry.
    """
    return Draft202012Validator(_load_json(SCHEMA))


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_committed_example_exists() -> None:
    assert GOLDEN.exists(), f"missing committed example: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty committed example: {GOLDEN}"


# --------------------------------------------------------------------------- #
# Coverage axis 1: schema-conformant emit                                     #
# --------------------------------------------------------------------------- #


def test_committed_example_validates_against_schema() -> None:
    _validator().validate(_load_json(GOLDEN))


def test_replay_artifact_validates_against_schema(tmp_path: Path) -> None:
    """Schema cross-check before byte-comparison.

    The acceptance criterion is explicit: replay must validate against
    ``schemas/evidence/crypto-attestation.schema.json`` before the
    byte-parity assertion runs, so a shape regression in the LangGraph
    node adapter surfaces with a JSON Schema diagnostic instead of a
    bytes-differ message.
    """
    update = emit_crypto_attestation_artifact_node(
        {"crypto_attestation_context": CTX, "evidence_output_dir": tmp_path}
    )
    written = Path(update["crypto_attestation_artifact_path"])
    _validator().validate(_load_json(written))


# --------------------------------------------------------------------------- #
# Coverage axis 2: byte-parity replay against the committed example           #
# --------------------------------------------------------------------------- #


def _drift_hint() -> str:
    return (
        "LangGraph crypto-attestation example drifted from a fresh "
        "adapter replay. If the change is intentional, regenerate the "
        "example via `PYTHONPATH=. python examples/langgraph/vuln_intake/"
        "evidence/crypto/regenerate.py` and commit the new bytes "
        "alongside the emitter / adapter change."
    )


def test_langgraph_replay_matches_committed_example(tmp_path: Path) -> None:
    """Replay the LangGraph node adapter, then assert byte-equality.

    The shared emitter writes ``<artifact_id>.json`` under ``tmp_path``;
    ``examples/.../regenerate.py`` copies that to the
    ``secret-handling-attestation.json`` snapshot for human-friendly
    diffing. We compare the adapter's freshly-written bytes against the
    committed snapshot bytes; the rename is a pure copy in
    ``regenerate.py`` (``shutil.copyfile``) so the on-disk bytes are
    identical at the two paths.
    """
    update = emit_crypto_attestation_artifact_node(
        {"crypto_attestation_context": CTX, "evidence_output_dir": tmp_path}
    )
    written = Path(update["crypto_attestation_artifact_path"])
    assert written.read_bytes() == GOLDEN.read_bytes(), _drift_hint()


# --------------------------------------------------------------------------- #
# Coverage axis 3: env-only-injection assertion shape                         #
# --------------------------------------------------------------------------- #


def test_committed_example_carries_env_only_injection_assertion() -> None:
    """The F-CP-05 mechanical assertions are present on the artifact.

    ``secrets_baked_in`` must be ``false``, ``injection_mode`` must be
    ``"env"``, and every ``env_var_refs`` entry must be an
    UPPER_SNAKE_CASE name (the schema rejects anything else; we pin
    the shape here too so a future regression that silently broadens
    the regex trips both the schema test and this one).
    """
    record = _load_json(GOLDEN)
    sh = record["secret_handling"]
    assert sh["secrets_baked_in"] is False
    assert sh["injection_mode"] == "env"
    assert sh["env_var_refs"], "expected at least one declared env-var reference"
    import re

    name_re = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
    for ref in sh["env_var_refs"]:
        assert name_re.match(ref), (
            f"env_var_refs entry {ref!r} is not UPPER_SNAKE_CASE — values, "
            "fragments of values, or credential-shaped strings are out of "
            "scope per AGENTS.md §3 and Core Directive #6"
        )


def test_artifact_id_is_deterministic_sha256(tmp_path: Path) -> None:
    """``artifact_id`` on the committed record matches
    SHA-256(``<workflow_id>|<execution_id>|<compile_target>``).

    Schema contract — and the property that lets re-emissions of the
    same execution land on byte-identical content. Replay-side: the
    fresh node adapter emission re-derives the same id and surfaces
    it on the partial state update under
    ``crypto_attestation_artifact_id``.
    """
    import hashlib

    record = _load_json(GOLDEN)
    expected = hashlib.sha256(
        f"{record['workflow_id']}|{record['execution_id']}|"
        f"{record['compile_target']}".encode("utf-8")
    ).hexdigest()
    assert record["artifact_id"] == expected

    update = emit_crypto_attestation_artifact_node(
        {"crypto_attestation_context": CTX, "evidence_output_dir": tmp_path}
    )
    assert update["crypto_attestation_artifact_id"] == expected
