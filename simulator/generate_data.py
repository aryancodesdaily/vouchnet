"""Generate deterministic dummy projects, contributors, trust edges, and PR history."""
import random
from datetime import datetime, timedelta

from core import campaign, store

SPAM_TEXT = ("Improve documentation and fix typos across the project. "
             "This change updates the readme wording and formatting")
GENUINE = [
    "Fix crash when config file is missing on startup",
    "Add retry logic to the network client with exponential backoff",
    "Handle unicode filenames correctly in the archive extractor",
    "Speed up the parser by caching compiled regular expressions",
    "Add unit tests for the date formatting helpers",
    "Document the environment variables used by the build script",
]


def spam_variants(n=8):
    return [f"{SPAM_TEXT} number {i}" for i in range(n)]


def generate(data_dir=None, n_orgs=30, seed=7):
    if data_dir:
        store.set_data_dir(data_dir)
    rnd = random.Random(seed)
    orgs = [f"ORG{i:02d}" for i in range(1, n_orgs + 1)]
    graph = {}
    for org in orgs:
        others = [x for x in orgs if x != org]
        graph[org] = {x: round(rnd.uniform(0.3, 0.9), 2) for x in rnd.sample(others, rnd.randint(2, 4))}
    store.save_graph(graph)

    # Each contributor has one canonical profile with PR history and project scores.
    contributors = {}
    for idx in range(1, 61):
        uid = str(1000 + idx)
        contributors[uid] = {
            "contributor_id": uid,
            "github_username": f"contributor_{uid}",
            "pull_requests": [],
            "project_scores": {},
        }
        contributed_projects = rnd.sample(orgs, rnd.randint(1, 5))
        for org in contributed_projects:
            score = rnd.randint(60, 95) if rnd.random() < 0.85 else rnd.randint(10, 35)
            contributors[uid]["project_scores"][org] = score
            n_prs = rnd.randint(1, 5)
            for j in range(n_prs):
                merged = rnd.random() < score / 100
                created = datetime(2026, 10, 1) + timedelta(days=rnd.randint(0, 45), hours=rnd.randint(0, 23))
                contributors[uid]["pull_requests"].append({
                    "pr_id": f"{org}-{uid}-{j+1}", "project_id": org,
                    "title": f"{('Improve' if merged else 'Attempt')} {['parser','documentation','tests','validation','network client'][j % 5]}",
                    "description": f"Contribution {j+1} by {uid} to {org}",
                    "created_at": created.isoformat(timespec="seconds"),
                    "status": "merged" if merged else "rejected",
                    "rejection_reason": None if merged else rnd.choice(["tests failing", "out of scope", "incomplete implementation"]),
                })
    # A deliberate cross-project campaign account for demo.
    uid = "9001"
    contributors[uid] = {"contributor_id": uid, "github_username": "suspicious_user", "pull_requests": [], "project_scores": {}}
    base = datetime(2026, 11, 19, 8, 0)
    for i, text in enumerate(spam_variants(8)):
        org = orgs[i]
        contributors[uid]["pull_requests"].append({
            "pr_id": f"SPAM-{i+1}", "project_id": org, "title": "Documentation cleanup",
            "description": text,
            "created_at": (base + timedelta(minutes=15 * i)).isoformat(timespec="seconds"),
            "status": "open", "rejection_reason": None,
        })
    store._write("contributors.json", contributors)

    # Keep project-local score files for compatibility with the existing CLI/importer.
    for org in orgs:
        local = {uid: {"score": score} for uid, profile in contributors.items()
                 if (score := profile["project_scores"].get(org)) is not None}
        store.save_org(org, {"org": org, "contributors": local, "events": []})
    return orgs


if __name__ == "__main__":
    generate()
    print("data/ mein dummy projects aur contributors ban gaye")
