#!/usr/bin/env python3
"""Fail when the branch adds a new .md/.mdx path compared with its base.

Added and copied markdown paths fail. A rename passes only when the old path is
markdown too. The label `docs-approved` on the pull request lifts the ban; locally
there is no label. Usage: md-ban.py [--base REF] [--event GITHUB_EVENT.json].
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LABEL = 'docs-approved'
SUFFIXES = ('.md', '.mdx')


def is_markdown(path):
    return path.lower().endswith(SUFFIXES)


def parse_name_status(text):
    fields = text.split('\0')
    entries, i = [], 0
    while i < len(fields) and fields[i]:
        status = fields[i]
        if status[0] in 'RC':
            entries.append((status[0], fields[i + 1], fields[i + 2]))
            i += 3
        else:
            entries.append((status[0], None, fields[i + 1]))
            i += 2
    return entries


def new_markdown(entries, labels=()):
    if LABEL in labels:
        return []
    found = []
    for status, old, new in entries:
        if not is_markdown(new):
            continue
        if status in 'AC' or (status == 'R' and not is_markdown(old)):
            found.append(new)
    return found


def labels_from_event(payload):
    return {label.get('name') for label in payload.get('pull_request', {}).get('labels', [])}


def branch_entries(base):
    out = subprocess.run(['git', 'diff', '-z', '--name-status', '-M', '-C', '--diff-filter=ACR', f'{base}...HEAD'],
                         cwd=REPO, capture_output=True, text=True, check=True).stdout
    return parse_name_status(out)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='origin/master')
    parser.add_argument('--event')
    args = parser.parse_args(argv)
    labels = labels_from_event(json.loads(Path(args.event).read_text(encoding='utf-8'))) if args.event else set()
    bad = new_markdown(branch_entries(args.base), labels)
    for path in bad:
        print(f'{path}: new markdown file not allowed')
    if bad:
        print(f'{len(bad)} new markdown file(s). Put status in the PR or issue, or ask Peter for `{LABEL}`; see AGENTS.md.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
