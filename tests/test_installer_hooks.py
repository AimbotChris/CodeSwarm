"""Exercise the shipped installer command with isolated injected hook failures."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'd-i preseed/late_command string '
CONFIG = ROOT / 'config/installer-only/code-swarm.cfg'

class InstallerHookTests(unittest.TestCase):
    def run_chain(self, first_status, second_status=0):
        lines = CONFIG.read_text().splitlines()
        commands = [line[len(PREFIX):] for line in lines if line.startswith(PREFIX)]
        self.assertEqual(len(commands), 1)
        with tempfile.TemporaryDirectory(prefix='r6-installer-hooks-') as temp:
            directory = Path(temp)
            (directory / 'code-swarm-hostname.sh').write_text(
                'echo first >> "$HOOK_LOG"\nexit ' + str(first_status) + '\n')
            (directory / 'code-swarm-admin.sh').write_text(
                'echo second >> "$HOOK_LOG"\n'
                + ('touch "$SUCCESS_MARKER"\n' if second_status == 0 else '')
                + 'exit ' + str(second_status) + '\n')
            env = dict(os.environ, HOOK_LOG=str(directory / 'calls'),
                       SUCCESS_MARKER=str(directory / 'success'))
            # Only relocate the ISO-mounted hooks; retain the release shell syntax.
            command = commands[0].replace('/cdrom/', temp + '/')
            result = subprocess.run(['/bin/sh', '-c', command], env=env,
                                    capture_output=True, text=True)
            return result.returncode, (directory / 'calls').read_text().splitlines(), (directory / 'success').exists()

    def test_first_hook_failure_is_nonzero_and_admin_never_runs(self):
        self.assertEqual(self.run_chain(47), (47, ['first'], False))

    def test_admin_failure_is_nonzero_without_success_marker(self):
        self.assertEqual(self.run_chain(0, 48), (48, ['first', 'second'], False))

    def test_success_runs_both_hooks_and_creates_marker(self):
        self.assertEqual(self.run_chain(0), (0, ['first', 'second'], True))

if __name__ == '__main__':
    unittest.main()
