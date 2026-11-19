import pytest

from simulator.scenarios import ALL


@pytest.mark.parametrize("name", list(ALL))
def test_scenario(name):
    r = ALL[name]()
    assert r["passed"], r
