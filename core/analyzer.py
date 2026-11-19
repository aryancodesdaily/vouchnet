"""Contribution stats + campaign result se score ka chhota badlav (±limit)."""
from core import store


def score_delta(stats, campaign_result, cfg=None):
    """stats = {"merged": n, "rejected": n}  ->  int delta."""
    s = (cfg or store.load_config())["score"]
    delta = stats.get("merged", 0) * s["merged_points"] + stats.get("rejected", 0) * s["rejected_points"]
    level = campaign_result.get("level", "none")
    if level == "none":
        delta += s["clean_check_points"]
    elif level == "medium":
        delta += s["alert_points"] // 2
    else:
        delta += s["alert_points"]
    return max(-s["max_down_per_update"], min(s["max_up_per_update"], delta))
