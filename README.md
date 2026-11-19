# Vouchnet

Dummy-data prototype for a project-to-project trust network. When a new PR arrives, the local project evaluates the contributor using only project scores reachable through its directed trust graph. The contributor's complete PR history across all projects is separately scanned for repeated-content and burst campaigns.

## Data model

- `data/trust_graph.json`: directed trust weights, e.g. `A -> B: 0.9`.
- `data/contributors.json`: one profile per contributor, containing GitHub ID/username, complete PR history, and project-wise scores.
- `data/orgs/*.json`: legacy project-local score/event records, kept in sync for compatibility with the importer and older data.
- `data/submissions.json`: searchable PR index used by older code paths.

PR history records project ID, PR ID, title, description, timestamp, status (`open`, `merged`, `rejected`), and rejection reason.

## Trust rules

- Trust is directional.
- A path can contain at most 3 projects (2 edges), e.g. `A -> B -> C`.
- Edge weights multiply. The configurable decay factor applies to indirect hops, not the first direct edge.
- Only scores from projects reachable from the current project are used in contributor scoring.
- Campaign detection scans all PRs in the contributor profile, including PRs from projects outside the current trust network.
- Vouch adds 50 points; denounce subtracts 50 points. Scores are clamped to 0-100.

The current decay factor is `0.8` in `config.json`; it is a prototype default, not a learned or validated constant.

## Run

From the project root:

```bash
pip install -r requirements.txt
python -m pytest -q
python cli.py gen
python cli.py demo all
python cli.py check --org ORG01 --user 9001 --pr-id 123 --title "Docs update" --body "..."
python cli.py resolve-pr --project ORG01 --user 9001 --pr-id 123 --status rejected --reason "tests failing"
python cli.py mark --org ORG01 --user 9001 --type denounce --reason spam
```

`gen` creates deterministic dummy projects, contributor profiles, project scores, and PR histories. The campaign detector currently identifies near-duplicate PR text and unusual bursts. It does not prove that text was AI-generated; any AI-generated label must be treated as a suspicion/heuristic, not a reliable classifier.
