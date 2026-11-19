"""Central JSON storage for project trust, contributors, and PR history."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_data_dir = os.path.join(ROOT, "data")


def set_data_dir(path):
    global _data_dir
    _data_dir = path


def get_data_dir():
    return _data_dir


def _read(rel, default):
    try:
        with open(os.path.join(_data_dir, rel), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def _write(rel, obj):
    full = os.path.join(_data_dir, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_config():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def load_graph():
    """Directed graph: {project_id: {trusted_project_id: trust_weight}}."""
    return _read("trust_graph.json", {})


def save_graph(graph):
    _write("trust_graph.json", graph)


def load_org(org_id):
    """Compatibility store for project-local score/event records."""
    org = _read(f"orgs/{org_id}.json", {})
    org.setdefault("org", org_id)
    org.setdefault("contributors", {})
    org.setdefault("events", [])
    return org


def save_org(org_id, data):
    _write(f"orgs/{org_id}.json", data)


def load_contributors():
    return _read("contributors.json", {})


def load_contributor(user_id):
    return load_contributors().get(str(user_id))


def save_contributor(user_id, contributor):
    data = load_contributors()
    data[str(user_id)] = contributor
    _write("contributors.json", data)


def ensure_contributor(user_id, username=None):
    """Create or return the canonical contributor profile."""
    uid = str(user_id)
    all_data = load_contributors()
    row = all_data.setdefault(uid, {
        "contributor_id": uid,
        "github_username": username or uid,
        "pull_requests": [],
        "project_scores": {},
    })
    if username:
        row["github_username"] = username
    row.setdefault("pull_requests", [])
    row.setdefault("project_scores", {})
    all_data[uid] = row
    _write("contributors.json", all_data)
    return row


def add_submission(sub):
    """Store complete PR data in contributor profile and legacy global index."""
    subs = _read("submissions.json", [])
    subs.append(sub)
    _write("submissions.json", subs)

    contributor = ensure_contributor(sub["user_id"])
    # Keep one canonical copy per project + PR ID; timestamp is fallback key.
    pr_id = sub.get("pr_id")
    key = (str(sub.get("org")), str(pr_id if pr_id is not None else sub.get("time")))
    existing = {
        (str(p.get("project_id")), str(p.get("pr_id") if p.get("pr_id") is not None else p.get("created_at")))
        for p in contributor["pull_requests"]
    }
    if key not in existing:
        contributor["pull_requests"].append({
            "pr_id": pr_id,
            "project_id": sub.get("org"),
            "title": sub.get("title", ""),
            "description": sub.get("body", ""),
            "created_at": sub.get("time"),
            "status": sub.get("status", "open"),
            "rejection_reason": sub.get("rejection_reason"),
            "fingerprint": sub.get("fingerprint"),
        })
        save_contributor(sub["user_id"], contributor)


def update_project_score(org_id, user_id, score):
    contributor = ensure_contributor(user_id)
    contributor["project_scores"][str(org_id)] = score
    save_contributor(user_id, contributor)



def update_pull_request_status(user_id, project_id, pr_id, status, rejection_reason=None):
    """Update a PR outcome in the contributor's canonical history and index."""
    if status not in {"open", "merged", "rejected"}:
        raise ValueError("status must be open, merged, or rejected")
    contributor = load_contributor(user_id)
    if not contributor:
        raise KeyError(f"Unknown contributor: {user_id}")
    matched = False
    for pr in contributor.get("pull_requests", []):
        if str(pr.get("project_id")) == str(project_id) and str(pr.get("pr_id")) == str(pr_id):
            pr["status"] = status
            pr["rejection_reason"] = rejection_reason if status == "rejected" else None
            matched = True
    if not matched:
        raise KeyError(f"PR {pr_id} for project {project_id} not found")
    save_contributor(user_id, contributor)

    submissions = _read("submissions.json", [])
    for sub in submissions:
        if (str(sub.get("user_id")) == str(user_id)
                and str(sub.get("org")) == str(project_id)
                and str(sub.get("pr_id")) == str(pr_id)):
            sub["status"] = status
            sub["rejection_reason"] = rejection_reason if status == "rejected" else None
    _write("submissions.json", submissions)
    return True


def load_submissions(user_id=None):
    subs = _read("submissions.json", [])
    if user_id is None:
        return subs
    return [s for s in subs if str(s["user_id"]) == str(user_id)]


def save_submissions(subs):
    _write("submissions.json", subs)
