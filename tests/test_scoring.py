import tempfile

from core import store
from core.graph import trust_info
from core.scoring import evaluate


def _setup(graph, orgs):
    store.set_data_dir(tempfile.mkdtemp())
    for o, rows in orgs.items():
        store.save_org(o, {"org": o, "contributors": {str(k): {"score": v} for k, v in rows.items()}, "events": []})
    return trust_info(graph, "P")


def test_vouched():
    info = _setup({"P": {"S": 0.8}}, {"S": {1: 90}})
    assert evaluate(info, 1)["verdict"] == "vouched"


def test_unknown_when_no_record():
    info = _setup({"P": {"S": 0.8}}, {"S": {}})
    assert evaluate(info, 1)["verdict"] == "unknown"


def test_mixed_when_close():
    info = _setup({"P": {"S": 0.5, "T": 0.5}}, {"S": {1: 90}, "T": {1: 10}})
    assert evaluate(info, 1)["verdict"] == "mixed"


def test_higher_strength_wins():
    info = _setup({"P": {"S": 0.9, "T": 0.2}}, {"S": {1: 90}, "T": {1: 0}})
    assert evaluate(info, 1)["verdict"] == "vouched"
