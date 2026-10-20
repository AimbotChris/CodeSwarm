"""Core OS workflows, shared by any builder that runs configure.py."""
from pathlib import Path
import runpy
import json
import textwrap
import re

def configure(source, root):
    selection = runpy.run_path(str(source / 'builder/recipe.py'))['load'](source)
    runpy.run_path(str(source / 'scripts/toolchain.py'))['stage'](source, root)


    def write_workflow(path, text, mode=0o644):
        target = root / 'config/includes.chroot' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        first, separator, rest = text.partition('\n')
        target.write_text(first + separator + textwrap.dedent(rest))
        target.chmod(mode)


    write_workflow('usr/local/bin/code-swarm-workflow', (source / 'product/code-swarm-workflow').read_text(), 0o755)
    write_workflow('usr/share/code-swarm/WORKFLOWS.md', (source / 'docs/WORKFLOWS.md').read_text())
    for name in ['LICENSE', 'THIRD-PARTY.md']:
        write_workflow('usr/share/doc/code-swarm/' + name, (source / name).read_text())
    write_workflow('etc/code-swarm/workflow.json', json.dumps(selection, indent=2) + '\n')
    write_workflow('etc/skel/.config/code-swarm/workflow.json', json.dumps({'startup': selection['startup']}) + '\n')
    write_workflow('etc/systemd/user/code-swarm-t3.service', '''[Unit]
    Description=T3 Code multi-provider workspace
    StartLimitIntervalSec=300
    StartLimitBurst=4
    [Service]
    ExecStart=/usr/bin/t3code --ozone-platform=x11
    Restart=on-failure
    RestartSec=15
    TimeoutStopSec=60
    KillMode=control-group
    ''')
    write_workflow('usr/share/applications/code-swarm-workflows.desktop', '''[Desktop Entry]
    Type=Application
    Name=Code Swarm Workflows
    Comment=Open coding tools, sign in, and choose your startup workflow
    Exec=/usr/local/bin/code-swarm-workflow
    Terminal=false
    Categories=Development;
    ''')
    # General coding prerequisites also support users adding their preferred harness.
    packages = root / 'config/package-lists/desktop.list.chroot'
    lines = packages.read_text().splitlines()
    if 'chatgpt' not in selection['tools']:
        lines = [line for line in lines if line != 'chatgpt']
        for relative in ['etc/systemd/user/codex-desktop.service', 'usr/local/libexec/codex-session-start']:
            (root / 'config/includes.chroot' / relative).unlink(missing_ok=True)
    if 't3' not in selection['tools']:
        (root / 'config/includes.chroot/etc/systemd/user/code-swarm-t3.service').unlink(missing_ok=True)
    base = ['git', 'openssh-client', 'ripgrep', 'unzip']
    if 'development' in selection['tools']:
        base += ['build-essential', 'nodejs', 'npm']
    for package in base:
        if package not in lines:
            lines.append(package)
    packages.write_text('\n'.join(lines) + '\n')
    menu = root / 'config/includes.chroot/etc/xdg/openbox/menu.xml'
    text = menu.read_text().replace('<item label="Start ChatGPT">',
        '<item label="Choose workflow"><action name="Execute"><command>code-swarm-workflow</command></action></item>\n<item label="Start ChatGPT">')
    if 'chatgpt' not in selection['tools']:
        text = re.sub(r'<item label="(?:Start ChatGPT|Stop ChatGPT|Reset crash limit and start)">.*?</item>', '', text, flags=re.S)
        for relative in ['etc/xdg/mimeapps.list', 'etc/skel/.config/mimeapps.list']:
            path = root / 'config/includes.chroot' / relative
            if path.exists():
                path.write_text(path.read_text().replace('x-scheme-handler/codex=chatgpt.desktop\n', ''))
    menu.write_text(text)
    # The legacy Openbox session should use the same per-user preference too.
    autostart = root / 'config/includes.chroot/etc/xdg/openbox/autostart'
    autostart.write_text(autostart.read_text().replace('systemctl --user start codex-desktop.service', 'code-swarm-workflow autostart'))
    session = root / 'config/includes.chroot/usr/share/xsessions/code-swarm.desktop'
    session.write_text(session.read_text().replace('Codex worker with visible recovery controls', 'Coding workspace with a choice of agent workflows'))

    hook = root / 'config/hooks/live/0895-workflow-tools.hook.chroot'
    hook.write_text('''#!/bin/sh
    set -eu
    test -x /usr/bin/git
    mkdir -p /usr/share/code-swarm
    # Fail the build on missing runtimes; no provider login or API calls.
    # Keep all first-run state outside /root and the installed owner's skeleton.
    temporary=$(mktemp -d)
    trap 'rm -rf "$temporary"' EXIT HUP INT TERM
    export HOME="$temporary"
    export XDG_CONFIG_HOME="$temporary/config"
    export XDG_CACHE_HOME="$temporary/cache"
    export XDG_DATA_HOME="$temporary/data"
    export XDG_STATE_HOME="$temporary/state"
    {
     git --version
    } > /usr/share/code-swarm/toolchain-versions.txt
    ''')
    smoke = []
    for name in ['codex', 'claude', 'opencode']:
        if name in selection['tools']:
            smoke.append('timeout 30 ' + name + ' --version')
    if 't3' in selection['tools']:
        smoke += ['test -x /usr/bin/t3code', "dpkg-query -W -f='${Package} ${Version}\\n' t3code"]
    if 'chatgpt' in selection['tools']:
        smoke += ['test -x /usr/bin/chatgpt', "dpkg-query -W -f='${Package} ${Version}\\n' chatgpt"]
    first, separator, rest = hook.read_text().partition('\n')
    hook.write_text((first + separator + textwrap.dedent(rest)).replace(' git --version\n', ' git --version\n' + ''.join(' ' + line + '\n' for line in smoke)))
    hook.chmod(0o755)


if __name__ == '__main__':
    configure(Path('/work'), Path('/work/build'))
