from core.graph import trust_info, trusted_orgs


def test_two_hop_multiplies():
    g = {"P": {"Q": 0.5}, "Q": {"S": 0.8}}
    assert abs(trusted_orgs(g, "P")["S"] - 0.32) < 1e-9
    assert trust_info(g, "P")["S"]["path"] == ["P", "Q", "S"]


def test_direct_beats_longer_path():
    g = {"P": {"S": 0.9, "Q": 0.9}, "Q": {"S": 0.9}}
    assert trusted_orgs(g, "P")["S"] == 0.9


def test_three_project_chain_limit():
    g = {"P": {"Q": 1.0}, "Q": {"R": 1.0}, "R": {"S": 1.0}}
    t = trusted_orgs(g, "P", max_hops=2)
    assert "Q" in t and "R" in t and "S" not in t


def test_cycle_safe():
    g = {"P": {"Q": 0.5}, "Q": {"P": 0.9}}
    assert trusted_orgs(g, "P")["P"] == 1.0
