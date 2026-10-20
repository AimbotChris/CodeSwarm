"""Personal build selections never execute user-supplied commands."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
r = runpy.run_path(str(ROOT / 'builder/recipe.py'))


class RecipeTests(unittest.TestCase):
    def test_template_and_json_agree(self):
        selection = r['read'](ROOT / 'BUILD-MY-ISO.md')
        self.assertEqual(selection, {'schema': 1, 'tools': ['chatgpt', 't3', 'codex', 'development'], 'startup': 'chatgpt'})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'recipe.json'
            path.write_text(json.dumps(selection))
            self.assertEqual(r['read'](path), selection)

    def test_dependency_startup_and_untrusted_fields_are_rejected(self):
        cases = [dict(schema=1, tools=['t3'], startup='t3'),
                 dict(schema=1, tools=['claude'], startup='chatgpt'),
                 dict(schema=1, tools=['claude', 'claude'], startup='claude'),
                 dict(schema=1, tools=['arbitrary; command'], startup='none'),
                 dict(schema=1, tools=[], startup='none', command='echo unwanted'),
                 dict(schema=True, tools=[], startup='none'),
                 dict(schema=1, tools=[], startup=[])]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                r['validate'](case)
        self.assertEqual(r['validate'](dict(schema=1, tools=[], startup='none'))['tools'], [])

    def test_bad_or_duplicate_markdown_options_are_rejected(self):
        text = (ROOT / 'BUILD-MY-ISO.md').read_text()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'recipe.md'
            for bad in [text.replace('- [ ] Claude Code', '- [x] unknown tool'),
                        text + '\nOpen at login: Terminal\n',
                        text.replace('- [ ] Claude Code', '- [ ] OpenCode'),
                        text.replace('- [x] ChatGPT', '- [ ] ChatGPT')]:
                path.write_text(bad)
                with self.assertRaises(ValueError):
                    r['read'](path)

    def test_portable_bundle_contains_only_allowlisted_bytes_and_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'builder').mkdir()
            (root / 'builder/source-files.txt').write_text('app.py\n')
            (root / 'app.py').write_text('print("synthetic")\n')
            (root / 'private-auth.json').write_text('synthetic excluded content')
            selection = dict(schema=1, tools=['opencode'], startup='opencode')
            destination = root / 'source.tar'
            r['bundle'](destination, selection, root)
            with tarfile.open(destination) as tar:
                self.assertEqual(set(tar.getnames()), {'app.py', 'config/workflow.json', 'source-sha256.json'})
                self.assertEqual(json.load(tar.extractfile('config/workflow.json')), selection)
                hashes = json.load(tar.extractfile('source-sha256.json'))
                for name, expected in hashes.items():
                    self.assertEqual(hashlib.sha256(tar.extractfile(name).read()).hexdigest(), expected)
                self.assertTrue(all(m.uid == 0 and m.gid == 0 for m in tar.getmembers()))
            with self.assertRaises(FileExistsError):
                r['bundle'](destination, selection, root)
            (root / 'builder/source-files.txt').write_text('../private-auth.json\n')
            with self.assertRaises(ValueError):
                r['bundle'](root / 'unsafe.tar', selection, root)
