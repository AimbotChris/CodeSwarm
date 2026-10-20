"""Audit regression tests use constructed synthetic values, never real secrets."""
import pathlib
import runpy
import subprocess
import tempfile
import unittest

audit = runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1] / 'builder/audit-source.py'))


class SourceAuditTests(unittest.TestCase):
    def test_redacts_values_and_rejects_artifacts(self):
        candidate = b'gh' + b'p_' + b'X' * 36
        result = audit['inspect']('source.py', candidate)
        self.assertIn('redacted', result)
        self.assertNotIn(candidate.decode(), result)
        for name in ['vendor/app.deb', 'private/authkey', 'archive.tgz', '.env.local']:
            self.assertIsNotNone(audit['inspect'](name, b'content'))
        self.assertIsNotNone(audit['inspect']('source', b'', '120000'))
        self.assertIsNotNone(audit['inspect']('source.py', b'a' * (audit['LIMIT'] + 1)))
        self.assertIsNone(audit['inspect']('source.py', b'ordinary source'))
        for fixture in audit['FIXTURES']:
            self.assertIsNone(audit['inspect']('tests/fixture.py', fixture))

    def test_working_index_and_history_use_different_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            def git(*args):
                return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
            git('init', '-q')
            git('config', 'user.name', 'Synthetic test')
            git('config', 'user.email', 'synthetic@example.invalid')
            path = root / 'source.py'
            path.write_text('committed')
            git('add', '.')
            git('commit', '-qm', 'Synthetic history')
            path.write_text('staged')
            git('add', '.')
            path.write_text('working')
            (root / 'new.py').write_text('untracked')
            self.assertEqual(dict((n, d) for n, d, _ in audit['entries']('working', root)),
                             {'source.py': b'working', 'new.py': b'untracked'})
            self.assertEqual(list(audit['entries']('index', root)), [('source.py', b'staged', '100644')])
            self.assertEqual(list(audit['entries']('history', root)), [('source.py', b'committed', '100644')])
