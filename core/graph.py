"""Directed weighted project trust graph with hop decay."""


def trust_info(graph, start, max_hops=3, decay_factor=0.8):
    """Return strongest trust path to each project.

    Each edge weight is multiplied by decay_factor for every hop. The start
    project's own trust is 1.0. Cycles cannot improve the start node.
    """
    best = {start: {"trust": 1.0, "path": [start], "hops": 0}}
    frontier = [start]
    for depth in range(1, max_hops + 1):
        updated = []
        for u in frontier:
            for v, raw_weight in graph.get(u, {}).items():
                if v in best[u]["path"]:
                    continue
                weight = max(0.0, min(1.0, float(raw_weight)))
                trust = best[u]["trust"] * weight * (decay_factor ** (depth - 1))
                if v not in best or trust > best[v]["trust"] + 1e-12:
                    best[v] = {
                        "trust": trust,
                        "path": best[u]["path"] + [v],
                        "hops": depth,
                    }
                    updated.append(v)
        frontier = updated
        if not frontier:
            break
    return best


def trusted_orgs(graph, start, max_hops=3, decay_factor=0.8):
    return {o: i["trust"] for o, i in trust_info(graph, start, max_hops, decay_factor).items()}
