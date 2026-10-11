#!/usr/bin/python3
"""Finalize sources inside the installed target, never on the build host."""
from pathlib import Path
import re
base=Path('/etc/apt')
# Keep vendor stanzas and keys unchanged. Disable media-only sources and replace
# only this image's three Debian suites with explicit signed codename sources.
for p in [base/'sources.list',*sorted((base/'sources.list.d').glob('*.list'))]:
 if not p.exists():continue
 lines=[]
 for line in p.read_text().splitlines():
  active=line.lstrip().startswith(('deb ','deb-src '))
  media=active and 'cdrom:' in line
  debian=active and re.search(r'https?://(?:deb\.debian\.org/debian/?|security\.debian\.org(?:/debian-security)?/?)\s+trixie(?:-updates|-security)?\s',line)
  lines.append('# Code Swarm OS replaced: '+line if media or debian else line)
 p.write_text('\n'.join(lines)+'\n')
for p in sorted((base/'sources.list.d').glob('*.sources')):
 if p.name=='code-swarm-debian.sources':continue
 blocks=[];changed=False
 for block in p.read_text().strip().split('\n\n'):
  uris=re.search(r'^URIs:\s*(.*)$',block,re.M)
  suites=re.search(r'^Suites:\s*(.*)$',block,re.M)
  media=uris and 'cdrom:' in uris.group(1)
  debian=uris and suites and all(re.match(r'https?://(?:deb\.debian\.org|security\.debian\.org)/',u) for u in uris.group(1).split()) and set(suites.group(1).split()) <= {'trixie','trixie-updates','trixie-security'}
  if media or debian:
   changed=True
   block=re.sub(r'^Enabled:.*\n?', '',block,flags=re.M)+'\nEnabled: no'
  blocks.append(block)
 new='\n\n'.join(blocks)+'\n'
 # Do not rewrite unrelated vendor files, even their formatting.
 if changed and new!=p.read_text():p.write_text(new)
(base/'sources.list.d/code-swarm-debian.sources').write_text('''Types: deb
URIs: https://deb.debian.org/debian
Suites: trixie trixie-updates
Components: main contrib non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://security.debian.org/debian-security
Suites: trixie-security
Components: main contrib non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
''')
