import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('comment_ban', REPO / 'tools/comment-ban.py')
ban = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ban)


def check(files, excuses=''):
    return ban.violations(list(files), files.__getitem__, ban.load_allowlist(excuses))


class CommentBanTests(unittest.TestCase):
    def test_repository_is_clean(self):
        allowlist = ban.load_allowlist((REPO / ban.EXCUSES).read_text(encoding='utf-8'))
        bad = ban.violations(ban.scanned_files(), lambda p: (REPO / p).read_text(encoding='utf-8'), allowlist)
        self.assertEqual(bad, [])

    def test_every_excuse_matches_a_comment(self):
        allowlist = ban.load_allowlist((REPO / ban.EXCUSES).read_text(encoding='utf-8'))
        present = {(p, u[0], u[1]) for p in ban.scanned_files()
                   for u in ban.units(p, (REPO / p).read_text(encoding='utf-8'))}
        self.assertEqual(allowlist - present, set())

    def test_new_plain_comments_fail(self):
        files = {
            'a.cs': 'class A\n{\n    // explains\n    int x = 1; /* more */\n}\n',
            'b.py': 'x = 1  # explains\n',
            'c.sh': '#!/usr/bin/env bash\necho hi # explains\n',
            'd.ps1': '<# explains #>\nWrite-Host hi\n',
            'e.cmd': '@echo off\nrem explains\n',
            '.gitignore': '# explains\nbuild/\n',
        }
        self.assertEqual(check(files), [('a.cs', 3, 3), ('a.cs', 4, 4), ('b.py', 1, 1), ('c.sh', 2, 2),
                                        ('d.ps1', 1, 1), ('e.cmd', 2, 2), ('.gitignore', 1, 1)])

    def test_listed_excuse_passes_only_for_its_exact_span(self):
        files = {'a.cs': 'class A\n{\n    // workaround: one\n    // two\n}\n'}
        self.assertEqual(check(files, '- `a.cs:3-4`: workaround\n'), [])
        self.assertEqual(check(files, '- `a.cs:3`: workaround\n'), [('a.cs', 3, 4)])
        files['a.cs'] = files['a.cs'].replace('// two\n', '// two\n    // sneaked in\n')
        self.assertEqual(check(files, '- `a.cs:3-4`: workaround\n'), [('a.cs', 3, 5)])

    def test_directives_and_strings_pass(self):
        files = {
            'a.cs': '#if UNITY_EDITOR\nusing X;\n#endif\nclass A { string s = "http://x"; string v = @"a\\"" + $"{b["//"]}"; char c = \'/\'; }\n',
            'b.py': '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nurl = "a # b"\nimport x  # noqa: F401\n',
            'c.sh': '#!/usr/bin/env bash\n# shellcheck disable=SC2086\necho "$# ${#x} a#b \'#\'"\ncat <<EOF\n# body\nEOF\n',
            'd.ps1': "#Requires -Version 5\n$s = 'it''s # not'\n$t = @\"\n# here\n\"@\n",
        }
        self.assertEqual(check(files), [])

    def test_directive_lookalikes_and_appended_text_fail(self):
        files = {
            'a.py': '# pragmatic explanation\nx = 1  # noqa because reasons\ny = 2  # type: ignore  kept for now\n',
            'b.sh': '#!/bin/sh\n# shellcheck disable=SC2086 because quoting\n# shellchecked by hand\n',
            'c.ps1': '#Requires -Version 5 because old hosts\n#requiresfoo\n',
        }
        self.assertEqual(check(files), [('a.py', 1, 1), ('a.py', 2, 2), ('a.py', 3, 3), ('b.sh', 2, 3),
                                        ('c.ps1', 1, 2)])
        excuses = '- `a.py:2`: workaround\n- `b.sh:2-3`: workaround\n'
        self.assertEqual(check(files, excuses), [('a.py', 1, 1), ('a.py', 3, 3), ('c.ps1', 1, 2)])

    def test_comments_inside_command_substitutions_fail(self):
        files = {
            'a.sh': 'value="$(\n    # new explanation\n    printf hello\n)"\n',
            'b.sh': 'x=`echo hi # explains`\ny="`echo hi # explains`"\n',
            'c.ps1': '$s = "$(\n# explains\nGet-Date)"\n',
            'd.sh': 'value="$(case x in x)\n    # explanation\n    printf hello;;\nesac)"\n',
        }
        self.assertEqual(check(files), [('a.sh', 2, 2), ('b.sh', 1, 1), ('b.sh', 2, 2), ('c.ps1', 2, 2),
                                        ('d.sh', 2, 2)])

    def test_literal_hashes_in_substitutions_and_lengths_pass(self):
        files = {
            'a.sh': 'echo "$(printf \'a # b\' "c # d") e # f"\necho ${#a[@]} "${#a[@]}" $(( 16#ff ))\n',
            'b.ps1': '$s = "$(\'a # b\') c # d"\n',
            'c.sh': 'v="$(case x in (x) printf \'a # b\';; y) echo "#y";; esac) c # d"\n',
        }
        self.assertEqual(check(files), [])


if __name__ == '__main__':
    unittest.main()
