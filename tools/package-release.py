#!/usr/bin/env python3
"""Package the existing, checksum-verified build as a local preview release."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build/Roadster'
PACKAGING = ROOT / 'packaging'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    version = re.search(r'^  Version: ([0-9.]+)$',
                        (ROOT / 'unity/Roadster/ModManifest.asset').read_text(), re.M).group(1)
    runtime = {
        'Roadster.dll', 'Locales/en.json', 'Dependencies/0Harmony.dll',
        'Dependencies/Harmony-LICENSE.txt',
        *[f'AssetBundles/{platform}/roadster.unity3d{suffix}'
          for platform in ('Windows', 'Mac') for suffix in ('', '.manifest')],
    }
    expected = {}
    for line in (ROOT / 'build/Roadster.sha256').read_text().splitlines():
        sha, name = line.split(maxsplit=1)
        expected[name.removeprefix('./')] = sha
    actual = {p.relative_to(BUILD).as_posix() for p in BUILD.rglob('*') if p.is_file()}
    if actual != runtime | {'README.md'} or set(expected) != actual:
        raise SystemExit('Build contents differ from the expected package; inspect before releasing.')
    payload = {}
    for name in sorted(actual):
        path = BUILD / name
        if path.is_symlink():
            raise SystemExit(f'Refusing symlink: {name}')
        data = path.read_bytes()
        if digest(data) != expected[name]:
            raise SystemExit(f'Build checksum mismatch: {name}')
        if name in runtime:
            payload['Roadster/' + name] = data
    json.loads(payload['Roadster/Locales/en.json'])
    for name in ('INSTALL.txt', 'RELEASE-NOTES.txt'):
        payload['Roadster/' + name] = (PACKAGING / name).read_bytes()
    checksums = ''.join(f'{digest(data)}  {name}\n' for name, data in sorted(payload.items()))
    payload['SHA256SUMS.txt'] = checksums.encode()
    out = ROOT / 'build/releases'
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f'Roadster-{version}-preview.zip'
    # Exclusive creation preserves earlier deliverables.
    if archive.exists():
        raise SystemExit(f'Already exists: {archive}. Move it aside before packaging another build.')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(payload.items()):
            z.writestr(name, data)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or set(z.namelist()) != set(payload):
            raise SystemExit('Archive integrity check failed.')
        for name, data in payload.items():
            if z.read(name) != data:
                raise SystemExit(f'Archive round-trip mismatch: {name}')
    archive.with_suffix('.zip.sha256').write_text(f'{digest(archive.read_bytes())}  {archive.name}\n')
    print(f'Checked {len(actual)} build files; verified {len(payload)} ZIP entries.')
    print(f'{archive} ({archive.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
