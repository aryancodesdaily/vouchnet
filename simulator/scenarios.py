"""5 demo scenarios. Har ek apne temp folder mein chalta hai, asli data/ nahi chhedta."""
import tempfile
from datetime import datetime, timedelta

from core import graph, store
from service.check_pr import check_pr


def _fresh():
    store.set_data_dir(tempfile.mkdtemp(prefix="vouchnet_"))


def _org(name, scores):
    store.save_org(name, {"org": name, "contributors": {str(k): {"score": v} for k, v in scores.items()}, "events": []})


def ring():
    """200 fake orgs ek dusre ko vouch karte hain; P ke trust graph se juda nahi -> unknown."""
    _fresh()
    g = {"P": {"Q": 0.6}, "Q": {}}
    n = 200
    for i in range(n):
        g[f"F{i}"] = {f"F{(i + 1) % n}": 1.0, f"F{(i + 2) % n}": 1.0}
        _org(f"F{i}", {7000 + j: 100 for j in range(n)})
    _org("Q", {})
    store.save_graph(g)
    r = check_pr("P", 7005, "Fix a bug in the parser module", "Small fix with tests included here")
    return {"name": "200-account vouch ring", "passed": r["verdict"] == "unknown", "result": r}


def hostile():
    """Bura org H akela kisi ko flag se block nahi kar paata."""
    _fresh()
    store.save_graph({"P": {"S": 0.8, "H": 0.1}})
    _org("S", {1001: 90})
    _org("H", {1001: 0, 1002: 0})          # H dono ko flag karta hai
    a = check_pr("P", 1001, "Fix crash on startup when config missing", "Adds a default config fallback")
    b = check_pr("P", 1002, "Add docs for the build script", "Explains the environment variables used")
    ok = a["verdict"] == "vouched" and b["confidence"] == "weak"
    return {"name": "hostile org alone", "passed": ok, "result": {"legit_user": a, "only_flagged_by_H": b}}


def indirect():
    """P -> Q (0.5) -> S (0.8): A sirf S mein vouched -> P ko 0.4 trust dikhe."""
    _fresh()
    store.save_graph({"P": {"Q": 0.5}, "Q": {"S": 0.8}})
    _org("S", {1001: 90})
    r = check_pr("P", 1001, "Fix crash on startup when config missing", "Adds a default config fallback")
    ok = r["verdict"] == "vouched" and abs(r["trust"] - 0.32) < 1e-9 and r["via"] == ["P", "Q", "S"]
    return {"name": "indirect trust 0.5 x 0.8 with 0.7 decay", "passed": ok, "result": r}


def newcomer():
    """Naya student, koi record nahi -> unknown, campaign clean."""
    _fresh()
    store.save_graph({"P": {"Q": 0.5}})
    r = check_pr("P", 5555, "Add a CONTRIBUTING section to the readme", "First contribution from our hackathon team")
    ok = r["verdict"] == "unknown" and not r["campaign"]["alert"]
    return {"name": "new student", "passed": ok, "result": r}


def campaign():
    """Spammer 8 orgs mein almost-same PR bhejta hai; genuine banda alert nahi paata."""
    _fresh()
    store.save_graph({f"O{i}": {} for i in range(8)} | {"P": {}})
    from simulator.generate_data import spam_variants
    base = datetime(2026, 11, 19, 8, 0)
    last = None
    for i, text in enumerate(spam_variants(8)):
        last = check_pr(f"O{i}", 9001, "Docs", text, now=base + timedelta(minutes=15 * i))
    clean = check_pr("O0", 1001, "Fix crash when config file is missing",
                     "Adds a fallback to defaults and a regression test", now=base)
    ok = last["campaign"]["alert"] and not clean["campaign"]["alert"]
    return {"name": "spam campaign", "passed": ok, "result": {"spammer": last, "genuine": clean}}


ALL = {"ring": ring, "hostile": hostile, "indirect": indirect, "newcomer": newcomer, "campaign": campaign}
