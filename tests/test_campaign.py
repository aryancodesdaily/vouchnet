from datetime import datetime, timedelta

from core.campaign import check, fingerprint
from simulator.generate_data import GENUINE, spam_variants

BASE = datetime(2026, 11, 19, 8, 0)


def _sub(org, text, user, minutes):
    return {"org": org, "user_id": str(user), "fingerprint": fingerprint(text),
            "time": (BASE + timedelta(minutes=minutes)).isoformat()}


def test_spammer_caught():
    subs = [_sub(f"O{i}", t, 9001, i * 10) for i, t in enumerate(spam_variants(8))]
    r = check(9001, subs)
    assert r["alert"] and r["repeat"]


def test_genuine_not_flagged():
    subs = [_sub(f"O{i}", t + " in module", 1001, i * 180) for i, t in enumerate(GENUINE)]
    assert not check(1001, subs)["alert"]


def test_burst_detected():
    subs = [_sub(f"O{i}", f"unique change number {i} about topic {i * 7} and area {i * 13}", 5, i * 3) for i in range(12)]
    r = check(5, subs)
    assert r["burst"]


def test_short_text_ignored():
    assert fingerprint("Docs") is None
