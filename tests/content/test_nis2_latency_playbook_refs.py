"""Playbook back-reference assertion for the NIS2 Art. 23 latency KRI triad.

Follows the F-MET-CRA-LATENCY back-reference pattern (SKELETON #622,
CORE #641). Each of the three NIS2 Article 23 dispatch-latency KRIs
must carry a non-empty ``playbook_refs`` block, and every entry must
resolve to one of the three anchor playbooks the notification chain
runs through:

* ``playbook.incident_management@v1`` — primary Art. 23 dispatch chain
  (24h early warning / 72h notification / one-month final report).
* ``playbook.ransomware_containment@v1`` — regulator early-warning
  pre-notification drafted within the 24-hour clock on ransomware
  events (staged for human sign-off before dispatch through the
  incident-management chain).
* ``playbook.nis2_self_assessment@v1`` — whole-Article-21 attestation
  that records the operator's readiness posture the Art. 23 dispatch
  depends on.

Pins the step-scoped anchor for each of the three KRIs against the
notification-dispatch step on ``playbook.incident_management@v1`` so a
future refactor cannot silently drop the primary link.

Pure stdlib + PyYAML. No network, no schema dependency.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = REPO_ROOT / "content" / "metrics"


ALLOWED_PLAYBOOK_IDS = frozenset(
    {
        "playbook.incident_management@v1",
        "playbook.ransomware_containment@v1",
        "playbook.nis2_self_assessment@v1",
    }
)


# Per-KRI structural anchor on the incident-management dispatch chain.
NIS2_LATENCY_KRIS: dict[str, tuple[str, str]] = {
    "nis2_incident_early_warning_latency_hours": (
        "kri.nis2_incident_early_warning_latency_hours@v1",
        "action--50000000-0000-4000-8000-000000000006",
    ),
    "nis2_incident_notification_latency_hours": (
        "kri.nis2_incident_notification_latency_hours@v1",
        "action--50000000-0000-4000-8000-000000000007",
    ),
    "nis2_incident_final_report_latency_days": (
        "kri.nis2_incident_final_report_latency_days@v1",
        "action--50000000-0000-4000-8000-000000000009",
    ),
}


def _load(name: str) -> dict:
    return yaml.safe_load(
        (METRICS_DIR / f"{name}.yaml").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("metric_name", sorted(NIS2_LATENCY_KRIS))
def test_nis2_latency_kri_has_non_empty_playbook_refs(
    metric_name: str,
) -> None:
    """Each NIS2 Art. 23 latency KRI declares at least one back-reference."""
    doc = _load(metric_name)
    expected_sid, _ = NIS2_LATENCY_KRIS[metric_name]
    assert doc.get("stable_id") == expected_sid, (
        f"{metric_name}.yaml stable_id drifted: got {doc.get('stable_id')!r} "
        f"expected {expected_sid!r}"
    )
    refs = doc.get("playbook_refs") or []
    assert refs, (
        f"{metric_name}.yaml has empty playbook_refs — the NIS2 Art. 23 "
        "latency KRI triad must back-reference the regulator-notification "
        "playbook chain (F-MET-NIS2-LATENCY CORE)."
    )


@pytest.mark.parametrize("metric_name", sorted(NIS2_LATENCY_KRIS))
def test_nis2_latency_kri_playbook_refs_are_in_allowed_set(
    metric_name: str,
) -> None:
    """Every back-reference points to one of the three NIS2 anchor playbooks."""
    doc = _load(metric_name)
    refs = doc.get("playbook_refs") or []
    stray = [
        r.get("playbook_id")
        for r in refs
        if isinstance(r, dict)
        and r.get("playbook_id") not in ALLOWED_PLAYBOOK_IDS
    ]
    assert not stray, (
        f"{metric_name}.yaml playbook_refs points outside the NIS2 Art. 23 "
        f"notification anchor set {sorted(ALLOWED_PLAYBOOK_IDS)}: {stray}"
    )


@pytest.mark.parametrize("metric_name", sorted(NIS2_LATENCY_KRIS))
def test_nis2_latency_kri_pins_incident_management_dispatch_step(
    metric_name: str,
) -> None:
    """Each KRI pins its Art. 23 dispatch step on incident_management.

    Structural anchor against silent regression: a future refactor
    that drops the primary dispatch step from playbook_refs would
    otherwise leave the "non-empty" gate satisfied by adjacent
    surfaces alone.
    """
    doc = _load(metric_name)
    _, expected_step = NIS2_LATENCY_KRIS[metric_name]
    tuples = {
        (r.get("playbook_id"), r.get("step_id"))
        for r in (doc.get("playbook_refs") or [])
        if isinstance(r, dict)
    }
    assert ("playbook.incident_management@v1", expected_step) in tuples, (
        f"{metric_name}.yaml no longer pins the primary Art. 23 dispatch "
        f"anchor (playbook.incident_management@v1, {expected_step}); the "
        "F-MET-NIS2-LATENCY CORE back-reference has regressed."
    )
