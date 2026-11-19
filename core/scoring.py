"""Estimate a contributor's trust using only projects reachable from the local project."""
from core import store


def _project_score(project_id, user_id):
    contributor = store.load_contributor(user_id)
    if contributor:
        score = contributor.get("project_scores", {}).get(str(project_id))
        if score is not None:
            return float(score)
    # Backward compatibility with the original per-project org JSON files.
    row = store.load_org(project_id)["contributors"].get(str(user_id))
    return float(row["score"]) if row and row.get("score") is not None else None


def evaluate(info, user_id, cfg=None):
    """Weighted mean of project scores, weighted by propagated project trust."""
    cfg = cfg or store.load_config()
    entries = []
    weighted_total = 0.0
    total_weight = 0.0
    for project_id, path_info in info.items():
        if project_id == path_info["path"][0]:
            continue
        score = _project_score(project_id, user_id)
        if score is None:
            continue
        weight = float(path_info["trust"])
        if weight <= 0:
            continue
        entry = {
            "project": project_id,
            "score": round(score, 2),
            "project_trust": round(weight, 4),
            "contribution": round(score * weight, 4),
            "path": path_info["path"],
        }
        entries.append(entry)
        weighted_total += score * weight
        total_weight += weight

    if not entries or total_weight == 0:
        return {
            "verdict": "unknown", "confidence": None, "trust_score": None,
            "trust": None, "via": None, "sources": [],
            "best_vouch": None, "best_flag": None,
        }

    trust_score = weighted_total / total_weight
    # Keep the old verdict labels for CLI compatibility; score is now explicit.
    neutral = cfg["score"]["neutral"]
    verdict = "vouched" if trust_score > neutral else "flagged" if trust_score < neutral else "mixed"
    strongest = max(entries, key=lambda x: x["project_trust"])
    confidence = "weak" if strongest["project_trust"] < cfg["trust"]["weak_below"] else "strong"
    return {
        "verdict": verdict,
        "confidence": confidence,
        "trust_score": round(trust_score, 2),
        "trust": strongest["project_trust"],
        "via": strongest["path"],
        "sources": entries,
        "best_vouch": max((e for e in entries if e["score"] > neutral), key=lambda x: x["project_trust"], default=None),
        "best_flag": max((e for e in entries if e["score"] < neutral), key=lambda x: x["project_trust"], default=None),
    }
