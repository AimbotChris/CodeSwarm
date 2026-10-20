"""Workflow preferences and image integration, without accounts or system changes."""
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
workflow = runpy.run_path(str(ROOT / 'product/code-swarm-workflow'))
toolchain = runpy.run_path(str(ROOT / 'scripts/toolchain.py'))
configure = runpy.run_path(str(ROOT / 'scripts/configure-workflows.py'))['configure']


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.config)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_personal_choice_persists_and_invalid_values_fall_back(self):
        self.assertEqual(workflow['get_default'](), 'chatgpt')
        for name in workflow['TOOLS']:
            workflow['set_default'](name)
            self.assertEqual(workflow['get_default'](), name)
        path = workflow['preference_path']()
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        for content in ['bad json', 'null', '{"startup": "shell command"}', '{"startup": []}']:
            path.write_text(content)
            self.assertEqual(workflow['get_default'](), 'chatgpt')
        with self.assertRaises(ValueError):
            workflow['set_default']('unlisted')

    def test_launches_use_provider_auth_without_shell_or_privilege(self):
        for name, expected in [('codex', ['codex', 'login']), ('claude', ['claude', 'auth', 'login']),
                               ('opencode', ['opencode', 'auth', 'login'])]:
            self.assertEqual(workflow['command'](name, True), ['xterm', '-hold', '-e', *expected])
        with patch.object(workflow['subprocess'], 'Popen') as popen:
            workflow['launch']('none')
            popen.assert_not_called()
            workflow['launch']('t3')
            popen.assert_called_once_with(['systemctl', '--user', 'start', 'code-swarm-t3.service'])


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source'
        self.build = Path(self.temp.name) / 'build'
        for name in ['vendor', 'config', 'scripts', 'product', 'docs', 'builder']:
            (self.source / name).mkdir(parents=True)
        (self.source / 'builder/recipe.py').write_text((ROOT / 'builder/recipe.py').read_text())
        self.items = []
        for name, member in [('codex', 'bin/codex'), ('claude', 'package/claude'), ('opencode', 'opencode')]:
            path = self.source / 'vendor' / (name + '.tar.gz')
            with tarfile.open(path, 'w:gz') as tar:
                data = b'#!/bin/sh\necho synthetic\n'
                entry = tarfile.TarInfo(member)
                entry.size = len(data)
                entry.mode = 0o755
                tar.addfile(entry, io.BytesIO(data))
                if name == 'codex':
                    entry = tarfile.TarInfo('bin/codex-code-mode-host')
                    entry.size = len(data)
                    entry.mode = 0o755
                    tar.addfile(entry, io.BytesIO(data))
            self.items.append(dict(name=name, file=path.name, kind='tar', sha256=toolchain['digest'](path)))
        deb = self.source / 'vendor/t3.deb'
        deb.write_bytes(b'synthetic package')
        self.items.append(dict(name='t3-code', file=deb.name, kind='deb', sha256=toolchain['digest'](deb)))
        notice = self.source / 'vendor/upstream-license.txt'
        notice.write_text('Synthetic upstream license fixture')
        self.items.append(dict(name='upstream-license', file=notice.name, kind='notice', sha256=toolchain['digest'](notice)))
        self.manifest = self.source / 'config/toolchain.json'
        self.manifest.write_text(json.dumps({'architecture': 'amd64', 'inputs': self.items}))

    def test_changed_artifact_stops_before_staging(self):
        (self.source / 'vendor' / self.items[-1]['file']).write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'checksum'):
            toolchain['stage'](self.source, self.build)
        self.assertFalse(self.build.exists())

    def test_unsafe_archive_never_extracts(self):
        for member, kind in [('../escaped', tarfile.REGTYPE), ('/absolute', tarfile.REGTYPE),
                             ('symlink', tarfile.SYMTYPE), ('device', tarfile.CHRTYPE)]:
            archive = self.source / 'bad.tar'
            with tarfile.open(archive, 'w') as tar:
                safe = tarfile.TarInfo('first-safe-file')
                tar.addfile(safe)
                entry = tarfile.TarInfo(member)
                entry.type = kind
                entry.linkname = '/etc/passwd' if kind == tarfile.SYMTYPE else ''
                tar.addfile(entry)
            dest = self.build / 'unsafe'
            with self.assertRaises(RuntimeError):
                toolchain['extract'](archive, dest)
            self.assertFalse(dest.exists())

    def prepare_recipe(self, selection=None):
        (self.source / 'scripts/toolchain.py').write_text((ROOT / 'scripts/toolchain.py').read_text())
        (self.source / 'product/code-swarm-workflow').write_text((ROOT / 'product/code-swarm-workflow').read_text())
        (self.source / 'docs/WORKFLOWS.md').write_text('Workflow guide')
        (self.source / 'LICENSE').write_text('Synthetic license fixture')
        (self.source / 'THIRD-PARTY.md').write_text('Synthetic notice fixture')
        config = self.build / 'config'
        packages = config / 'package-lists/desktop.list.chroot'
        packages.parent.mkdir(parents=True)
        packages.write_text('git\nchatgpt\n')
        includes = config / 'includes.chroot'
        for name, text in [('etc/xdg/openbox/menu.xml', '<item label="Start ChatGPT">'),
                           ('etc/xdg/openbox/autostart', 'systemctl --user start codex-desktop.service\n'),
                           ('usr/share/xsessions/code-swarm.desktop', 'Codex worker with visible recovery controls')]:
            path = includes / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        (config / 'hooks/live').mkdir(parents=True)
        if selection is not None:
            (self.source / 'config/workflow.json').write_text(json.dumps(selection))
        configure(self.source, self.build)
        return config, includes, packages

    def test_recipe_installs_tools_and_preserves_other_configuration(self):
        config, includes, packages = self.prepare_recipe()
        self.assertEqual(packages.read_text().splitlines().count('git'), 1)
        self.assertIn('openssh-client', packages.read_text())
        self.assertIn('chatgpt', packages.read_text())
        self.assertIn('code-swarm-workflow autostart', (includes / 'etc/xdg/openbox/autostart').read_text())
        for name in ['codex', 'claude', 'opencode']:
            link = includes / 'usr/local/bin' / name
            self.assertTrue(link.is_symlink())
            self.assertTrue((includes / str(link.readlink()).lstrip('/')).is_file())
        self.assertTrue((includes / 'opt/code-swarm/tools/codex/bin/codex-code-mode-host').exists())
        self.assertTrue((config / 'packages.chroot/t3.deb').exists())
        self.assertEqual((includes / 'usr/share/doc/code-swarm/vendor/upstream-license.txt').read_text(),
                         'Synthetic upstream license fixture')
        self.assertEqual(json.loads((includes / 'usr/share/code-swarm/toolchain.json').read_text())['inputs'], self.items)
        service = (includes / 'etc/systemd/user/code-swarm-t3.service').read_text()
        self.assertIn('ExecStart=/usr/bin/t3code', service)
        self.assertNotIn('User=root', service)
        self.assertIn('claude --version', (config / 'hooks/live/0895-workflow-tools.hook.chroot').read_text())

    def test_personal_recipe_excludes_unselected_tools_and_changes_startup(self):
        choice = {'schema': 1, 'tools': ['claude'], 'startup': 'claude'}
        config, includes, packages = self.prepare_recipe(choice)
        self.assertNotIn('chatgpt', packages.read_text().splitlines())
        self.assertNotIn('nodejs', packages.read_text().splitlines())
        self.assertTrue((includes / 'usr/local/bin/claude').is_symlink())
        self.assertFalse((includes / 'usr/local/bin/codex').exists())
        self.assertFalse((config / 'packages.chroot/t3.deb').exists())
        self.assertFalse((includes / 'etc/systemd/user/code-swarm-t3.service').exists())
        smoke = (config / 'hooks/live/0895-workflow-tools.hook.chroot').read_text()
        self.assertIn('claude --version', smoke)
        self.assertNotIn('codex --version', smoke)
        self.assertNotIn(' t3code', smoke)
        self.assertEqual(json.loads((includes / 'etc/code-swarm/workflow.json').read_text()), choice)
        self.assertEqual(json.loads((includes / 'etc/skel/.config/code-swarm/workflow.json').read_text()), {'startup': 'claude'})


if __name__ == '__main__':
    unittest.main()
