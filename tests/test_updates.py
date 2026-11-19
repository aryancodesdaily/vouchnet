import tempfile

from core import store
from core.updates import apply_analysis, apply_mark


def test_mark_and_clamp():
    store.set_data_dir(tempfile.mkdtemp())
    assert apply_mark("P", 1, "vouch") == 100
    assert apply_mark("P", 1, "vouch") == 100
    assert apply_mark("P", 1, "vouch") == 100
    assert apply_mark("P", 2, "denounce") == 0
    assert len(store.load_org("P")["events"]) == 4


def test_analysis_cannot_cross_cap():
    store.set_data_dir(tempfile.mkdtemp())
    for _ in range(5):
        s = apply_analysis("P", 1, 5)
    assert s == 60


def test_pr_history_and_status_update():
    store.set_data_dir(tempfile.mkdtemp())
    store.add_submission({
        "org": "B", "user_id": "p", "pr_id": "287", "time": "2026-11-19T10:00:00",
        "title": "Fix login", "body": "Fix validation", "status": "open",
        "rejection_reason": None, "fingerprint": None,
    })
    profile = store.load_contributor("p")
    assert profile["pull_requests"][0]["project_id"] == "B"
    assert profile["pull_requests"][0]["status"] == "open"
    store.update_pull_request_status("p", "B", "287", "rejected", "tests failing")
    updated = store.load_contributor("p")["pull_requests"][0]
    assert updated["status"] == "rejected"
    assert updated["rejection_reason"] == "tests failing"
