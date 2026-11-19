"""Sab ko jodta hai: naya PR aaya -> maintainer ke liye result dict."""
from core import analyzer, campaign, graph, scoring, store, updates

SUGGESTED_REASONS = ["spam", "ai-generated", "low-quality", "other"]


def check_pr(org_id, user_id, title="", body="", now=None, pr_id=None, status="open", rejection_reason=None):
    cfg = store.load_config()
    info = graph.trust_info(store.load_graph(), org_id, cfg["trust"]["max_hops"], cfg["trust"]["decay_factor"])
    result = scoring.evaluate(info, user_id, cfg)

    when = (now or campaign._utcnow()).isoformat(timespec="seconds")
    store.add_submission({
        "org": org_id, "user_id": str(user_id), "time": when,
        "pr_id": pr_id, "title": title, "body": body, "status": status,
        "rejection_reason": rejection_reason,
        "fingerprint": campaign.fingerprint(f"{title} {body}", cfg["campaign"]["min_words"]),
    })
    camp = campaign.check(user_id, None, cfg, now=now)

    return {
        "user_id": str(user_id),
        "verdict": result["verdict"],          # vouched | flagged | mixed | unknown
        "confidence": result["confidence"],    # strong | weak | None
        "trust": result["trust"],
        "trust_score": result["trust_score"],
        "sources": result["sources"],
        "via": result["via"],
        "best_vouch": result["best_vouch"],
        "best_flag": result["best_flag"],
        "campaign": {"level": camp["level"], "alert": camp["alert"], "reason": camp["reason"]},
        "suggested_reasons": SUGGESTED_REASONS,
    }


def mark(org_id, user_id, mark_type, reason=""):
    """Maintainer ka faisla: 'vouch' ya 'denounce'."""
    return updates.apply_mark(org_id, user_id, mark_type, reason)


def analyze_and_update(org_id, user_id, stats):
    """stats = {"merged": n, "rejected": n}. Last campaign result ke saath score update."""
    cfg = store.load_config()
    camp = campaign.check(user_id, None, cfg)
    delta = analyzer.score_delta(stats, camp, cfg)
    return updates.apply_analysis(org_id, user_id, delta, cfg)


def update_pr_status(user_id, project_id, pr_id, status, rejection_reason=None):
    """Record whether a submitted PR was merged or rejected by its project."""
    return store.update_pull_request_status(user_id, project_id, pr_id, status, rejection_reason)
