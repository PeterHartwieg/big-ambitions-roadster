"""Exercise the strict release packager without shipping any game binaries."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_release', REPO / 'tools/package-release.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root / 'build/Roadster'
        self.packaging = self.root / 'packaging'
        self.files = {
            'Roadster.dll': b'offline fixture, not a DLL',
            'Locales/en.json': json.dumps({'hello': 'Roadster'}).encode(),
            'Dependencies/0Harmony.dll': b'offline dependency fixture',
            'Dependencies/Harmony-LICENSE.txt': b'fixture licence',
            'README.md': b'fixture readme',
        }
        for platform in ('Windows', 'Mac'):
            for suffix in ('', '.manifest'):
                self.files[f'AssetBundles/{platform}/roadster.unity3d{suffix}'] = platform.encode()
        for name, data in self.files.items():
            path = self.build / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        manifest = self.root / 'unity/Roadster/ModManifest.asset'
        manifest.parent.mkdir(parents=True)
        manifest.write_text('  Version: 0.0.3\n')
        self.packaging.mkdir()
        for name in ('INSTALL.txt', 'RELEASE-NOTES.txt'):
            (self.packaging / name).write_text(name)
        self.write_checksums()
        self.patch = patch.multiple(package, ROOT=self.root, BUILD=self.build, PACKAGING=self.packaging)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.archive = self.root / 'build/releases/Roadster-0.0.3-preview.zip'

    def write_checksums(self):
        (self.root / 'build/Roadster.sha256').write_text(''.join(
            f'{hashlib.sha256(data).hexdigest()}  ./{name}\n' for name, data in sorted(self.files.items())))

    def run_package(self):
        with contextlib.redirect_stdout(io.StringIO()):
            package.main()

    def test_round_trip_and_checksums(self):
        self.run_package()
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(11, len(archive.namelist()))
            self.assertNotIn('Roadster/README.md', archive.namelist())
            for line in archive.read('SHA256SUMS.txt').decode().splitlines():
                digest, name = line.split(maxsplit=1)
                self.assertEqual(digest, hashlib.sha256(archive.read(name)).hexdigest())
            self.assertEqual(b'RELEASE-NOTES.txt', archive.read('Roadster/RELEASE-NOTES.txt'))
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                         self.archive.with_suffix('.zip.sha256').read_text().split()[0])

    def test_missing_file_refused(self):
        (self.build / 'Roadster.dll').unlink()
        with self.assertRaisesRegex(SystemExit, 'contents differ'):
            self.run_package()

    def test_extra_file_refused(self):
        (self.build / 'unreviewed.dll').write_bytes(b'extra')
        with self.assertRaisesRegex(SystemExit, 'contents differ'):
            self.run_package()

    def test_tampered_bytes_refused(self):
        (self.build / 'Roadster.dll').write_bytes(b'changed')
        with self.assertRaisesRegex(SystemExit, 'checksum mismatch'):
            self.run_package()

    def test_missing_checksum_refused(self):
        del self.files['Roadster.dll']
        self.write_checksums()
        with self.assertRaisesRegex(SystemExit, 'contents differ'):
            self.run_package()

    def test_symlink_refused_even_if_bytes_match(self):
        original = self.build / 'Roadster.dll'
        data = original.read_bytes()
        original.unlink()
        target = self.root / 'external.dll'
        target.write_bytes(data)
        original.symlink_to(target)
        with self.assertRaisesRegex(SystemExit, 'Refusing symlink'):
            self.run_package()

    def test_existing_archive_preserved(self):
        self.run_package()
        before = self.archive.read_bytes()
        with self.assertRaisesRegex(SystemExit, 'Already exists'):
            self.run_package()
        self.assertEqual(before, self.archive.read_bytes())

    def test_invalid_locale_refused(self):
        name = 'Locales/en.json'
        self.files[name] = b'not json'
        (self.build / name).write_bytes(self.files[name])
        self.write_checksums()
        with self.assertRaises(json.JSONDecodeError):
            self.run_package()
        self.assertFalse(self.archive.exists())


if __name__ == '__main__':
    unittest.main()
