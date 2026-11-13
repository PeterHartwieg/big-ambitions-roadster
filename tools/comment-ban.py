#!/usr/bin/env python3
"""Fail on code comments that are neither tool directives nor listed in docs/comment-excuses.md.

Scope: tracked .cs, .py, .sh, .ps1, .cmd/.bat files and .gitignore/.gitattributes,
outside art/ and docs/. A unit is a run of consecutive own-line comments, one trailing
comment, or one block comment. Directives pass only when the whole comment matches
DIRECTIVE_PATTERNS: a shebang on line 1, a Python coding line, bare `noqa[: codes]`,
`type: ignore[...]` or `pragma: no cover|branch`, `shellcheck key=value...`, or
PowerShell `#Requires -Flag value...`. A directive with appended text is an ordinary
unit and needs its own excuse entry. C# preprocessor lines are code,
not comments. An excuse passes when docs/comment-excuses.md has a list item starting
with `path:line` (single-line unit) or `path:start-end` (multi-line unit) matching the
unit exactly. Shell and PowerShell `$(...)` (and shell backticks) are scanned as code,
also inside double quotes. Python docstrings are string literals and are not scanned.
"""
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXCUSES = 'docs/comment-excuses.md'
EXCLUDED_DIRS = ('art/', 'docs/')
CODE_SUFFIXES = {'.cs': 'cs', '.py': 'py', '.sh': 'sh', '.ps1': 'ps', '.psm1': 'ps', '.cmd': 'cmd', '.bat': 'cmd'}
CONFIG_NAMES = {'.gitignore', '.gitattributes'}
DIRECTIVE_PATTERNS = {
    'py': re.compile(r'#!.*|#\s*-\*-\s*coding:\s*[-\w.]+\s*-\*-\s*|#\s*coding[:=]\s*[-\w.]+\s*|#\s*noqa(?::\s*[A-Z]+\d+(?:\s*,\s*[A-Z]+\d+)*)?\s*'
                     r'|#\s*type:\s*ignore(?:\[[\w-]+(?:\s*,\s*[\w-]+)*\])?\s*|#\s*pragma:\s*no\s+(?:cover|branch)\s*'),
    'sh': re.compile(r'#!.*|#\s*shellcheck(?:\s+(?:disable|enable|source|source-path|shell|external-sources)=[\w,./:-]+)+\s*'),
    'ps': re.compile(r'#requires(?:\s+-(?:Version|Modules|PSEdition|RunAsAdministrator|ShellId|Assembly)'
                     r'(?:\s+[^\s#-][^\s,#]*(?:\s*,\s*[^\s#-][^\s,#]*)*)?)+\s*', re.I),
}


def language(path):
    name = Path(path).name
    if name in CONFIG_NAMES:
        return 'conf'
    return CODE_SUFFIXES.get(Path(path).suffix.lower())


def line_of(text, offset):
    return text.count('\n', 0, offset) + 1


def cs_spans(text):
    spans = []
    n = len(text)

    def skip_string(i, verbatim, interpolated):
        while i < n:
            c = text[i]
            if verbatim and c == '"':
                if text.startswith('""', i):
                    i += 2
                    continue
                return i + 1
            if not verbatim and c == '\\':
                i += 2
                continue
            if not verbatim and c in '"\n':
                return i + 1
            if interpolated and c == '{':
                if text.startswith('{{', i):
                    i += 2
                    continue
                i = code(i + 1, True)
                continue
            i += 1
        return i

    def code(i, in_hole):
        depth = 0
        line_start = True
        while i < n:
            c = text[i]
            if c == '\n':
                line_start = True
                i += 1
                continue
            if c in ' \t\r':
                i += 1
                continue
            if line_start and c == '#' and not in_hole:
                while i < n and text[i] != '\n' and not text.startswith('//', i):
                    i += 1
                continue
            line_start = False
            if text.startswith('//', i):
                end = text.find('\n', i)
                end = n if end < 0 else end
                spans.append((i, end))
                i = end
            elif text.startswith('/*', i):
                end = text.find('*/', i + 2)
                end = n if end < 0 else end + 2
                spans.append((i, end))
                i = end
            elif text.startswith(('$@"', '@$"'), i):
                i = skip_string(i + 3, True, True)
            elif text.startswith('$"', i):
                i = skip_string(i + 2, False, True)
            elif text.startswith('@"', i):
                i = skip_string(i + 2, True, False)
            elif c == '"':
                i = skip_string(i + 1, False, False)
            elif c == "'":
                i += 1
                if i < n and text[i] == '\\':
                    i += 2
                while i < n and text[i] != "'":
                    i += 1
                i += 1
            elif in_hole and c == '{':
                depth += 1
                i += 1
            elif in_hole and c == '}':
                if depth == 0:
                    return i + 1
                depth -= 1
                i += 1
            else:
                i += 1
        return i

    code(0, False)
    return spans


def py_spans(text):
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    spans = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            start = offsets[tok.start[0] - 1] + tok.start[1]
            spans.append((start, start + len(tok.string)))
    return spans


def hash_spans(text, powershell):
    spans = []
    n = len(text)
    heredocs = []
    escape = '`' if powershell else '\\'

    def double_quoted(i):
        while i < n and text[i] != '"':
            if text[i] == escape:
                i += 2
            elif text.startswith('$(', i):
                i = code(i + 2, ')')
            elif text[i] == '`':
                i = code(i + 1, '`')
            else:
                i += 1
        return i + 1

    def command_start(i):
        head = text[:i].rstrip(' \t')
        if not head or head[-1] in '\n;&|(`':
            return True
        m = re.search(r'(?:^|(?<=[\s;&|(`]))(?:then|do|else|elif|if|while|until|!|\{)\Z', head)
        return m is not None and command_start(m.start())

    def code(i, stop):
        depth = 0
        cases = 0
        state = 0
        while i < n:
            c = text[i]
            if c == '\n':
                i += 1
                for word, strip_tabs in heredocs:
                    while i < n:
                        end = text.find('\n', i)
                        end = n if end < 0 else end
                        body = text[i:end]
                        i = end + 1
                        if (body.lstrip('\t') if strip_tabs else body) == word:
                            break
                heredocs.clear()
                continue
            prev = text[i - 1] if i else '\n'
            if not powershell and (prev.isspace() or prev in ';|&()`{'):
                word = re.match(r'(case|esac|in)(?=[\s;|&()]|$)', text[i:])
                word = word.group(1) if word else None
                if word == 'case' and state == 0 and command_start(i):
                    cases += 1
                    state = 1
                    i += 4
                    continue
                if word == 'in' and state == 1:
                    state = 2
                    i += 2
                    continue
                if word == 'esac' and cases and ((state == 2 and prev != '|') or (state == 0 and command_start(i))):
                    cases -= 1
                    state = 0
                    i += 4
                    continue
            if not powershell and cases and state == 0 and text.startswith((';;', ';&'), i):
                state = 2
                i += 2
                continue
            if not powershell and state == 2 and c in '()':
                state = 0 if c == ')' else 2
                i += 1
                continue
            if c == stop and (stop == '`' or depth == 0) and not (stop == ')' and cases > 0):
                return i + 1
            if powershell and text.startswith('<#', i):
                end = text.find('#>', i + 2)
                end = n if end < 0 else end + 2
                spans.append((i, end))
                i = end
            elif c == '#' and (prev.isspace() or prev in ';|&(){}') and not text.startswith('${#', i - 2):
                end = text.find('\n', i)
                end = n if end < 0 else end
                spans.append((i, end))
                i = end
            elif powershell and text.startswith(('@"\n', "@'\n", '@"\r\n', "@'\r\n"), i):
                close = '\n' + text[i + 1] + '@'
                end = text.find(close, i)
                i = n if end < 0 else end + len(close)
            elif c == "'":
                while True:
                    end = text.find("'", i + 1)
                    i = n if end < 0 else end + 1
                    if not (powershell and text.startswith("'", i)):
                        break
            elif c == '"':
                i = double_quoted(i + 1)
            elif c == '`' and powershell:
                i += 2
            elif c == '`':
                i = code(i + 1, '`')
            elif c == '\\':
                i += 2
            elif c == '(':
                depth += 1
                i += 1
            elif c == ')':
                depth -= 1 if depth or not cases else 0
                i += 1
            elif not powershell and text.startswith('<<', i) and not text.startswith('<<<', i):
                m = re.match(r'<<(-?)\s*([\'"]?)([A-Za-z_][A-Za-z0-9_]*)\2', text[i:])
                if m:
                    heredocs.append((m.group(3), bool(m.group(1))))
                    i += m.end()
                else:
                    i += 2
            else:
                i += 1
        return i

    code(0, None)
    return spans


def line_spans(text, pattern):
    spans = []
    offset = 0
    for line in text.splitlines(keepends=True):
        m = pattern.match(line)
        if m:
            spans.append((offset + m.start(1), offset + len(line.rstrip('\r\n'))))
        offset += len(line)
    return spans


def comment_spans(lang, text):
    if lang == 'cs':
        return cs_spans(text)
    if lang == 'py':
        return py_spans(text)
    if lang in ('sh', 'ps'):
        return hash_spans(text, lang == 'ps')
    if lang == 'cmd':
        return line_spans(text, re.compile(r'\s*@?((?:rem\b|::).*)', re.I))
    if lang == 'conf':
        return line_spans(text, re.compile(r'\s*(#.*)'))
    return []


def units(path, text):
    """Group comment spans into units: (start_line, end_line, start, end, own_line, directive)."""
    lang = language(path)
    result = []
    for start, end in comment_spans(lang, text):
        line_start = text.rfind('\n', 0, start) + 1
        own_line = text[line_start:start].strip() == ''
        first, last = line_of(text, start), line_of(text, end)
        body = text[start:end]
        pattern = DIRECTIVE_PATTERNS.get(lang)
        directive = bool(pattern and pattern.fullmatch(body) and (not body.startswith('#!') or start == 0))
        prev = result[-1] if result else None
        line_comment = lang != 'cs' or body.startswith('//')
        prev_line_comment = prev and (lang != 'cs' or text.startswith('//', prev[2]))
        if (prev and own_line and prev[4] and not directive and not prev[5]
                and line_comment and prev_line_comment and first == prev[1] + 1):
            result[-1] = (prev[0], last, prev[2], end, True, False)
        else:
            result.append((first, last, start, end, own_line, directive))
    return result


def scanned_files():
    out = subprocess.run(['git', 'ls-files'], cwd=REPO, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if language(p) and not p.startswith(EXCLUDED_DIRS)]


def load_allowlist(text):
    allowed = set()
    for m in re.finditer(r'^[-*]\s+`?([^\s`:]+):(\d+)(?:-(\d+))?`?', text, re.M):
        allowed.add((m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))))
    return allowed


def violations(files, read, allowlist):
    found = []
    for path in files:
        for first, last, _, _, _, directive in units(path, read(path)):
            if not directive and (path, first, last) not in allowlist:
                found.append((path, first, last))
    return found


def main():
    excuses = REPO / EXCUSES
    allowlist = load_allowlist(excuses.read_text(encoding='utf-8')) if excuses.exists() else set()
    bad = violations(scanned_files(), lambda p: (REPO / p).read_text(encoding='utf-8'), allowlist)
    for path, first, last in bad:
        print(f'{path}:{first}' + (f'-{last}' if last != first else '') + ': comment not allowed')
    if bad:
        print(f'{len(bad)} comment(s). Fix the code or open an issue; see AGENTS.md.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
