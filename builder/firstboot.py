#!/usr/bin/python3 -I
"""Installed-only, bounded enrollment. Never clone or reset a node identity."""
import fcntl
import json
import os
from pathlib import Path
import subprocess

def eligible(root):
    return (root/'var/lib/code-swarm/admin-provisioned').is_file() and not (
        (root/'run/live/medium').exists() or
        'boot=live' in (root/'proc/cmdline').read_text().split())

def run(args, timeout=15):
    return subprocess.run(args, timeout=timeout, stdin=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode

def secure_key(folder, key):
    return not (folder.is_symlink() or key.is_symlink() or folder.stat().st_uid or key.stat().st_uid or
                folder.stat().st_mode & 0o077 or key.stat().st_mode & 0o077)

def main(root=Path('/')):
    if os.geteuid() != 0 or not eligible(root):
        return 1
    folder = root/'etc/code-swarm-enrollment'
    key = folder/'authkey'
    state = root/'var/lib/code-swarm/enrollment-status'
    if not key.is_file():
        return 0
    # Refuse inherited state, insecure files, repeated/ambiguous attempts.
    if not secure_key(folder, key):
        return 1
    if state.exists() or (root/'var/lib/tailscale/tailscaled.state').exists():
        key.unlink()
        return 1
    # Persist the claim before enabling daemon: failure/power loss requires owner review.
    with state.open('x') as f:
        f.write('attempting\n'); f.flush(); os.fsync(f.fileno())
    directory = os.open(state.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    outcome = 'failed-owner-review-required'
    try:
        if run(['systemctl', 'enable', '--now', 'tailscaled'], 30):
            return 1
        # File reference only: key never appears in process argv or environment.
        # Tailscale performs bounded connection retries within this one attempt.
        run(['tailscale', 'up', '--auth-key=file:'+str(key), '--timeout=240s'], 260)
        result = subprocess.run(['tailscale', 'status', '--json'], timeout=10,
                                capture_output=True, stdin=subprocess.DEVNULL)
        status = json.loads(result.stdout)
        if status.get('BackendState') == 'Running':
            outcome = 'connected'
        elif status.get('BackendState') == 'NeedsMachineAuth':
            outcome = 'pending-device-approval'
    except (subprocess.SubprocessError, ValueError, OSError):
        pass
    finally:
        key.unlink(missing_ok=True)
        state.write_text(outcome+'\n')
        state.chmod(0o600)
    return 0 if outcome == 'connected' else 1

if __name__ == '__main__':
    # Root-only systemd service is serialized even against an explicit owner retry.
    if os.geteuid() != 0:
        raise SystemExit(1)
    with open('/run/code-swarm-firstboot.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raise SystemExit(main())
