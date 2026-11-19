""".td (Vouch jaisa) format: seedha naam = vouch, '-naam reason' = denounce, '#' = comment."""
from core import store
from core.updates import _now


def parse_td(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            kind = "vouch"
            if line.startswith("-"):
                kind, line = "denounce", line[1:].strip()
            parts = line.split(None, 1)
            user = parts[0]
            if ":" in user:                      # github:alice -> alice
                user = user.split(":", 1)[1]
            out.append({"user": user, "type": kind, "reason": parts[1] if len(parts) > 1 else ""})
    return out


def import_td(org_id, path, resolve=None, cfg=None):
    """Starting score set karo. resolve(username)->user_id (nahi diya to username hi key).
    Vouch: sirf jab record na ho. Denounce: score ko denounce_start tak gira deta hai."""
    s = (cfg or store.load_config())["score"]
    org = store.load_org(org_id)
    count = 0
    for e in parse_td(path):
        uid = str(resolve(e["user"]) if resolve else e["user"])
        row = org["contributors"].get(uid)
        old = row["score"] if row else None
        if e["type"] == "vouch":
            if row is not None:
                continue
            new = s["vouch_start"]
        else:
            new = s["denounce_start"] if old is None else min(old, s["denounce_start"])
        org["contributors"][uid] = {"score": new, "updated": _now()}
        org["events"].append({"user_id": uid, "type": f"import-{e['type']}", "points": 0,
                              "reason": e["reason"], "from": old, "to": new, "date": _now()})
        count += 1
    store.save_org(org_id, org)
    return count
