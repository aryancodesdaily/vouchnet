"""Terminal se chalao (project root se):
  python cli.py gen                       fake network banao (data/ mein)
  python cli.py check --org ORG01 --user 9001 --title "..." --body "..."
  python cli.py mark  --org ORG01 --user 1001 --type vouch|denounce --reason spam
  python cli.py resolve-pr --project ORG01 --user 1001 --pr-id 123 --status rejected --reason tests-failing
  python cli.py import --org ORG01 --file data/imports/VOUCHED.td
  python cli.py demo [ring|hostile|indirect|newcomer|campaign|all]
"""
import argparse
import json

from core import store
from importer.td_parser import import_td
from service import check_pr as svc
from simulator import generate_data, scenarios


def show(r):
    v = r["verdict"].upper()
    if r["verdict"] == "unknown":
        print("UNKNOWN: koi trusted org ke paas record nahi")
    else:
        direct = " (direct)" if r["via"] and len(r["via"]) == 2 else " (indirect)"
        print(f"{v}{direct}  trust={r['trust']:.2f}  confidence={r['confidence']}")
        print("  rasta:", " -> ".join(r["via"]))
        if r.get("trust_score") is not None:
            print(f"  contributor trust score: {r['trust_score']:.1f}/100")
        for source in r.get("sources", []):
            print(f"  {source['project']}: score={source['score']:.1f}, path-trust={source['project_trust']:.2f}, path={' -> '.join(source['path'])}")
    if r["best_vouch"] and r["verdict"] != "vouched":
        print(f"  positive signal: {r['best_vouch']['project']} score {r['best_vouch']['score']}")
    if r["best_flag"] and r["verdict"] != "flagged":
        print(f"  negative signal: {r['best_flag']['project']} score {r['best_flag']['score']}")
    c = r["campaign"]
    print("CAMPAIGN ALERT:" if c["alert"] else "Campaign: clean", c["level"], c["reason"])
    print("  mark karo: vouch / denounce. reasons:", ", ".join(r["suggested_reasons"]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("gen")
    c = sub.add_parser("check")
    c.add_argument("--org", required=True); c.add_argument("--user", required=True)
    c.add_argument("--title", default=""); c.add_argument("--body", default="")
    c.add_argument("--pr-id", default=None)
    m = sub.add_parser("mark")
    m.add_argument("--org", required=True); m.add_argument("--user", required=True)
    m.add_argument("--type", choices=["vouch", "denounce", "flag"], required=True); m.add_argument("--reason", default="")
    u = sub.add_parser("resolve-pr")
    u.add_argument("--project", required=True); u.add_argument("--user", required=True)
    u.add_argument("--pr-id", required=True); u.add_argument("--status", choices=["merged", "rejected", "open"], required=True)
    u.add_argument("--reason", default="")
    i = sub.add_parser("import")
    i.add_argument("--org", required=True); i.add_argument("--file", required=True)
    d = sub.add_parser("demo")
    d.add_argument("name", nargs="?", default="all", choices=list(scenarios.ALL) + ["all"])
    a = ap.parse_args()

    if a.cmd == "gen":
        generate_data.generate()
        print("fake network ban gaya:", store.get_data_dir())
    elif a.cmd == "check":
        show(svc.check_pr(a.org, a.user, a.title, a.body, pr_id=a.pr_id))
    elif a.cmd == "mark":
        print("naya score:", svc.mark(a.org, a.user, a.type, a.reason))
    elif a.cmd == "resolve-pr":
        svc.update_pr_status(a.user, a.project, a.pr_id, a.status, a.reason or None)
        print("PR status updated")
    elif a.cmd == "import":
        print("imported:", import_td(a.org, a.file))
    elif a.cmd == "demo":
        names = list(scenarios.ALL) if a.name == "all" else [a.name]
        for n in names:
            r = scenarios.ALL[n]()
            print(("PASS" if r["passed"] else "FAIL"), "-", r["name"])
            if a.name != "all":
                print(json.dumps(r["result"], indent=2, default=str)[:1500])


if __name__ == "__main__":
    main()
