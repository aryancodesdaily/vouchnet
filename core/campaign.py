"""Campaign detection: SimHash fingerprint + repeat rule + burst rule."""
import hashlib
import re
from datetime import datetime, timedelta, timezone

from core import store


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fingerprint(text, min_words=5, bits=64):
    """Text -> 64-bit SimHash. Bahut chhota text -> None (ignore)."""
    words = re.findall(r"\w+", (text or "").lower())
    if len(words) < min_words:
        return None
    shingles = [" ".join(words[i:i + 3]) for i in range(max(1, len(words) - 2))]
    v = [0] * bits
    for s in shingles:
        h = int(hashlib.md5(s.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i in range(bits) if v[i] > 0)


def distance(a, b):
    return bin(a ^ b).count("1")


def _t(s):
    return datetime.fromisoformat(s)


def check(user_id, submissions=None, cfg=None, now=None):
    """Scan the contributor's complete PR history across all projects."""
    cfg = cfg or store.load_config()
    c = cfg["campaign"]
    if submissions is None:
        profile = store.load_contributor(user_id) or {}
        submissions = []
        for pr in profile.get("pull_requests", []):
            text = f"{pr.get('title', '')} {pr.get('description', '')}"
            submissions.append({
                "org": pr.get("project_id"), "user_id": str(user_id),
                "time": pr.get("created_at"),
                "fingerprint": pr.get("fingerprint") or fingerprint(text, c["min_words"]),
            })
    subs = [s for s in submissions if str(s["user_id"]) == str(user_id)]
    none = {"level": "none", "alert": False, "reason": "", "repeat": False, "burst": False}
    if not subs:
        return none

    now = now or max(_t(s["time"]) for s in subs)
    win = [s for s in subs if now - _t(s["time"]) <= timedelta(hours=c["window_hours"])]

    # Repeat rule: almost-same text, kai orgs mein
    fps = [s for s in win if s.get("fingerprint") is not None]
    best = []
    for s in fps:
        group = [o for o in fps if distance(s["fingerprint"], o["fingerprint"]) <= c["simhash_distance"]]
        if len(group) > len(best):
            best = group
    orgs = {s["org"] for s in best}
    repeat = len(best) >= c["repeat_min"] and len(orgs) >= c["repeat_min_orgs"]

    # Burst rule: kam time mein bahut PRs
    ts = sorted(_t(s["time"]) for s in win)
    burst_n, j = 0, 0
    for i, t in enumerate(ts):
        while t - ts[j] > timedelta(hours=c["burst_hours"]):
            j += 1
        burst_n = max(burst_n, i - j + 1)
    burst = burst_n >= c["burst_limit"]

    level = "high" if (repeat and burst) else "medium" if (repeat or burst) else "none"
    reasons = []
    if repeat:
        reasons.append(f"{len(best)} almost-same PRs in {len(orgs)} orgs")
    if burst:
        reasons.append(f"{burst_n} PRs within {c['burst_hours']}h")
    return {"level": level, "alert": level != "none", "reason": ", ".join(reasons),
            "repeat": repeat, "burst": burst}
