"""Tests for scripts/render_roadmap.py — public-card filter."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_roadmap as rr  # noqa: E402


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE tasks ("
        "id TEXT PRIMARY KEY, title TEXT, body TEXT, status TEXT, "
        "priority INTEGER DEFAULT 0, created_at INTEGER NOT NULL)"
    )
    rows = [
        ("t_pub_marker", "Open card with marker", "Body text\n<public-roadmap/>", "todo", 0, 1),
        ("t_pub_repo", "Ship docs to secops-ng-framework", "Body refs the repo.", "running", 0, 2),
        ("t_priv_plain", "Internal strategy doc", "Private body about leads.", "todo", 0, 3),
        ("t_priv_repo", "Update secops-ng-business memory", "secops-ng-deployment infra notes", "todo", 0, 4),
        ("t_done", "Released X", "<public-roadmap/>", "done", 0, 5),
        ("t_triage", "Triage me", "<public-roadmap/>", "triage", 0, 6),
    ]
    conn.executemany(
        "INSERT INTO tasks (id, title, body, status, priority, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def test_is_public_card_marker():
    assert rr.is_public_card("any", "blah <public-roadmap/> blah")


def test_is_public_card_repo_ref():
    assert rr.is_public_card("Update secops-ng-framework", "")
    assert rr.is_public_card("", "see secops-ng-website")


def test_is_public_card_rejects_private():
    assert not rr.is_public_card("Internal note", "private body")
    assert not rr.is_public_card("Update secops-ng-business", "")
    assert not rr.is_public_card("Update secops-ng-deployment", "")


def test_load_public_cards_filters(tmp_path: Path):
    db = tmp_path / "kanban.db"
    _make_db(db)
    buckets = rr.load_public_cards(db)
    rendered = rr.render(buckets)

    assert "Open card with marker" in rendered
    assert "Ship docs to secops-ng-framework" in rendered
    assert "Released X" in rendered

    assert "Internal strategy doc" not in rendered
    assert "Update secops-ng-business memory" not in rendered
    assert "Triage me" not in rendered

    for priv_id in ("t_priv_plain", "t_priv_repo", "t_triage"):
        assert priv_id not in rendered
