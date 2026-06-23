"""G-04 catalog DoD — committed reference-visualisation presence.

The catalog G-04 definition-of-done requires every `content/metrics/*`
entry to carry at least one *committed* reference-visualisation
artifact alongside the YAML. The artifact contract is encoded in the
exemplars at `content/metrics/detection_coverage.viz.md` and
`content/metrics/breach_notification_clock_margin.viz.md`.

This test is the regression net so the next cluster lands without
re-litigating the contract. It is intentionally lightweight:

* allow-listed YAMLs (cluster-by-cluster catch-up wave) must have a
  sibling `<stem>.viz.md` next to the YAML;
* the sibling viz.md must back-reference the YAML's `stable_id` so
  the two cannot drift silently;
* the catalog YAML's `measurement.formula` must mention the viz file
  path so a YAML-only consumer of the catalog can find the artifact.

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = REPO_ROOT / "content" / "metrics"

# Allow-list of metric YAMLs that have shipped their G-04 reference
# visualisation. Cluster-by-cluster catch-up wave: each F-MET
# SKELETON / CORE / EXTEND card extends this list as the artifacts
# land. The remaining mttd_* domain variants
# (cloud_misconfig / exfil / identity_compromise / threat_intel_indicator)
# land in the CORE sibling.
VIZ_REQUIRED_STEMS = (
    # F-MET CORE breach-notification-clock-margin (#447)
    "breach_notification_clock_margin",
    # F-MET SKELETON detection_coverage (#448)
    "detection_coverage",
    # F-MET SKELETON mttd detection-latency cluster (#449)
    "mttd",
    "mttd_phishing",
    "mttd_ransomware",
    # F-MET SKELETON mttr remediation-latency cluster (this card)
    "mttr",
    "mttr_containment",
    "mttr_phishing_triage",
)


def _yaml_path(stem: str) -> Path:
    return METRICS_DIR / f"{stem}.yaml"


def _viz_path(stem: str) -> Path:
    return METRICS_DIR / f"{stem}.viz.md"


@pytest.mark.parametrize("stem", VIZ_REQUIRED_STEMS)
def test_viz_md_present_for_required_metric(stem: str) -> None:
    """A committed `<stem>.viz.md` artifact must sit beside the YAML."""
    viz = _viz_path(stem)
    assert viz.exists(), (
        f"G-04 def-of-done: missing committed reference visualisation "
        f"for {stem}.yaml; expected {viz.relative_to(REPO_ROOT)}."
    )
    assert viz.stat().st_size > 0, (
        f"G-04 def-of-done: reference visualisation {viz.relative_to(REPO_ROOT)} "
        "is empty; the artifact must carry the chart-kind contract, a "
        "Mermaid reference rendering, a threshold-band table, and an "
        "OCSF source-data-shape section."
    )


@pytest.mark.parametrize("stem", VIZ_REQUIRED_STEMS)
def test_viz_md_back_references_stable_id(stem: str) -> None:
    """`<stem>.viz.md` must mention the YAML's `stable_id` verbatim.

    Prevents silent drift between the YAML and the visualisation
    artifact — e.g. a YAML bumped to @v2 without the viz keeping up,
    or a viz copied from another metric and not retargeted.
    """
    yaml_path = _yaml_path(stem)
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    stable_id = doc["stable_id"]
    assert isinstance(stable_id, str) and stable_id, (
        f"{yaml_path.relative_to(REPO_ROOT)}: missing or non-string stable_id"
    )

    viz_text = _viz_path(stem).read_text(encoding="utf-8")
    assert stable_id in viz_text, (
        f"{_viz_path(stem).relative_to(REPO_ROOT)} does not back-reference "
        f"the YAML's stable_id `{stable_id}`; the two artifacts must not "
        "drift."
    )


@pytest.mark.parametrize("stem", VIZ_REQUIRED_STEMS)
def test_yaml_formula_points_at_viz_md(stem: str) -> None:
    """The YAML `measurement.formula` must cite the viz.md path.

    Mirrors the exemplars at `detection_coverage.yaml` /
    `breach_notification_clock_margin.yaml`, so a downstream consumer
    reading the catalog YAML alone can find the contract for the
    chart shape without grepping the repo.
    """
    yaml_path = _yaml_path(stem)
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    formula = doc.get("measurement", {}).get("formula", "")
    expected = f"content/metrics/{stem}.viz.md"
    assert expected in formula, (
        f"{yaml_path.relative_to(REPO_ROOT)}: measurement.formula does not "
        f"cite `{expected}`; downstream consumers reading the YAML alone "
        "cannot locate the committed reference visualisation."
    )


def test_viz_md_contains_mermaid_block() -> None:
    """Every required viz.md must carry at least one ```mermaid block.

    The contract for the chart shape is encoded as an in-tree Mermaid
    reference rendering — see the exemplars. A viz.md with no Mermaid
    block fails the G-04 DoD even if every other section is present.
    """
    mermaid_open = re.compile(r"^```mermaid\b", re.MULTILINE)
    missing: list[str] = []
    for stem in VIZ_REQUIRED_STEMS:
        text = _viz_path(stem).read_text(encoding="utf-8")
        if not mermaid_open.search(text):
            missing.append(stem)
    assert not missing, (
        "G-04 def-of-done: missing ```mermaid reference rendering in: "
        f"{missing}"
    )
