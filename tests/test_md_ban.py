import importlib.util
from pathlib import Path
import subprocess
import unittest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('md_ban', REPO / 'tools/md-ban.py')
ban = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ban)


def has_base():
    return subprocess.run(['git', 'rev-parse', '--verify', '-q', 'origin/master'], cwd=REPO,
                          capture_output=True).returncode == 0


class MdBanTests(unittest.TestCase):
    @unittest.skipUnless(has_base(), 'origin/master not available')
    def test_branch_adds_no_markdown(self):
        self.assertEqual(ban.new_markdown(ban.branch_entries('origin/master')), [])

    def test_added_and_copied_markdown_fail(self):
        entries = ban.parse_name_status('A\0notes.md\0A\0docs/x.MDX\0C100\0docs/plan.md\0docs/plan2.md\0A\0a.py\0')
        self.assertEqual(ban.new_markdown(entries), ['notes.md', 'docs/x.MDX', 'docs/plan2.md'])

    def test_no_new_markdown_passes(self):
        entries = ban.parse_name_status('A\0tools/x.py\0R100\0docs/plan.md\0docs/old/plan.md\0')
        self.assertEqual(ban.new_markdown(entries), [])

    def test_rename_from_non_markdown_fails(self):
        entries = ban.parse_name_status('R090\0notes.txt\0notes.md\0')
        self.assertEqual(ban.new_markdown(entries), ['notes.md'])

    def test_docs_approved_label_allows(self):
        payload = {'pull_request': {'labels': [{'name': 'bug'}, {'name': 'docs-approved'}]}}
        entries = [('A', None, 'review.md')]
        self.assertEqual(ban.new_markdown(entries, ban.labels_from_event(payload)), [])
        self.assertEqual(ban.new_markdown(entries, ban.labels_from_event({'pull_request': {'labels': []}})), ['review.md'])
