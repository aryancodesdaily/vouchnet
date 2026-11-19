"""Maintainer ka mark / analysis -> score update + event log."""
from datetime import datetime, timezone

from core import store


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def _clamp(x):
    return max(0, min(100, x))


def _log(org, user_id, etype, points, reason, old, new):
    org["events"].append({"user_id": str(user_id), "type": etype, "points": points,
                          "reason": reason, "from": old, "to": new, "date": _now()})


def apply_mark(org_id, user_id, mark, reason="", cfg=None):
    """mark = 'vouch' ya 'flag'. Record na ho to neutral se shuru."""
    s = (cfg or store.load_config())["score"]
    points = s["vouch_points"] if mark == "vouch" else s["flag_points"]
    event_type = "denounce" if mark in ("denounce", "flag") else "vouch"
    org = store.load_org(org_id)
    row = org["contributors"].setdefault(str(user_id), {"score": s["neutral"]})
    old = row["score"]
    row["score"] = _clamp(old + points)
    row["updated"] = _now()
    _log(org, user_id, event_type, points, reason, old, row["score"])
    store.save_org(org_id, org)
    store.update_project_score(org_id, user_id, row["score"])
    return row["score"]


def apply_analysis(org_id, user_id, delta, cfg=None):
    """Analysis se badhna 'analysis_cap' tak hi; usse upar sirf maintainer ka vouch le jaata hai."""
    s = (cfg or store.load_config())["score"]
    org = store.load_org(org_id)
    row = org["contributors"].setdefault(str(user_id), {"score": s["neutral"]})
    old = row["score"]
    new = old + delta
    if delta > 0:
        new = min(new, max(old, s["analysis_cap"]))
    row["score"] = _clamp(new)
    row["updated"] = _now()
    _log(org, user_id, "analysis", delta, "auto", old, row["score"])
    store.save_org(org_id, org)
    store.update_project_score(org_id, user_id, row["score"])
    return row["score"]
