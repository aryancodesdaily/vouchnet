import json
from collections import defaultdict
from pathlib import Path

INPUT_FILE = Path('contributors_with_dummy_outcomes.json')
OUTPUT_FILE = Path('contributors_with_organization_performance.json')

POINTS = {
    'good_accepted': 10,
    'normal_accepted': 5,
    'minor_rejection': -2,
    'bad_rejection': -8,
}

COUNT_FIELDS = (
    'good_accepted',
    'normal_accepted',
    'minor_rejection',
    'bad_rejection',
    'open_prs',
)


def calculate_organization_performance(pull_requests):
    """Recalculate organization-wise performance from the complete PR history."""
    organizations = defaultdict(lambda: {
        'total_prs': 0,
        'good_accepted': 0,
        'normal_accepted': 0,
        'minor_rejection': 0,
        'bad_rejection': 0,
        'open_prs': 0,
        'raw_score': 0,
    })

    for pr in pull_requests:
        organization_id = pr.get('project_id')
        if not organization_id:
            raise ValueError(f"PR {pr.get('pr_id', '<unknown>')} has no project_id")

        outcome = pr.get('outcome')
        stats = organizations[organization_id]
        stats['total_prs'] += 1

        if outcome == 'open' or (outcome is None and pr.get('status') == 'open'):
            stats['open_prs'] += 1
            continue

        if outcome not in POINTS:
            raise ValueError(
                f"PR {pr.get('pr_id', '<unknown>')} has unsupported outcome: {outcome!r}"
            )

        stats[outcome] += 1
        stats['raw_score'] += POINTS[outcome]

    # Keep organization IDs as keys and make the result JSON serializable.
    return dict(organizations)


def main():
    with INPUT_FILE.open('r', encoding='utf-8') as file:
        contributors = json.load(file)

    if not isinstance(contributors, dict):
        raise TypeError('Expected contributors.json to be an object keyed by contributor ID')

    for contributor_id, contributor in contributors.items():
        pull_requests = contributor.get('pull_requests', [])
        contributor['organization_performance'] = calculate_organization_performance(
            pull_requests
        )

    with OUTPUT_FILE.open('w', encoding='utf-8') as file:
        json.dump(contributors, file, indent=2, ensure_ascii=False)
        file.write('\n')

    print(f'Updated {len(contributors)} contributors.')
    print(f'Output: {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
