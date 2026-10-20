#!/usr/bin/env python3
"""Portable Markdown recipe validation and source packaging. No host installation."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'ChatGPT': 'chatgpt', 'T3 Code': 't3', 'Codex CLI': 'codex',
          'Claude Code': 'claude', 'OpenCode': 'opencode',
          'Development tools': 'development'}
STARTUP = {**{k: v for k, v in LABELS.items() if v != 'development'},
           'Terminal': 'terminal', 'Home only': 'none'}
DEFAULT = {'schema': 1, 'tools': list(LABELS.values()), 'startup': 'chatgpt'}


def validate(value):
    if not isinstance(value, dict) or set(value) != {'schema', 'tools', 'startup'}:
        raise ValueError('The recipe must contain only schema, tools and startup.')
    if type(value['schema']) is not int or value['schema'] != 1:
        raise ValueError('Unsupported recipe version.')
    tools = value['tools']
    if not isinstance(tools, list) or any(not isinstance(n, str) or n not in LABELS.values() for n in tools):
        raise ValueError('Choose only tools listed in BUILD-MY-ISO.md.')
    if len(tools) != len(set(tools)):
        raise ValueError('A tool is listed more than once.')
    startup = value['startup']
    if not isinstance(startup, str) or startup not in STARTUP.values():
        raise ValueError('Choose a listed Open at login option.')
    if startup not in {'terminal', 'none'} and startup not in tools:
        raise ValueError('The tool chosen to open at login must also be checked.')
    if 't3' in tools and not {'codex', 'claude', 'opencode'} & set(tools):
        raise ValueError('Check at least one provider for T3 Code: Codex CLI, Claude Code or OpenCode.')
    return {'schema': 1, 'tools': [n for n in LABELS.values() if n in tools], 'startup': startup}


def read(path):
    if path.stat().st_size > 65536:
        raise ValueError('Recipe is too large. Use the short project template.')
    text = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() == '.json':
        return validate(json.loads(text))
    sections = re.findall(r'<!-- codeswarm-tools:start -->(.*?)<!-- codeswarm-tools:end -->', text, re.S)
    if len(sections) != 1:
        raise ValueError('Use the tool checklist in BUILD-MY-ISO.md.')
    choices = re.findall(r'^- \[([ xX])\] (.+?)\s*$', sections[0], re.M)
    if len(choices) != len(LABELS) or {label for _, label in choices} != set(LABELS):
        raise ValueError('Keep each checklist label once; change only the checkbox marks.')
    startups = re.findall(r'^Open at login: (.+?)\s*$', text, re.M)
    if len(startups) != 1 or startups[0] not in STARTUP:
        raise ValueError('Set one Open at login line to a listed option.')
    return validate({'schema': 1, 'tools': [LABELS[label] for mark, label in choices if mark.lower() == 'x'],
                     'startup': STARTUP[startups[0]]})


def load(source):
    path = source / 'config/workflow.json'
    return read(path) if path.exists() else validate(DEFAULT)


def source_paths(root=ROOT):
    result = []
    for name in (root / 'builder/source-files.txt').read_text().splitlines():
        if not name or name.startswith('#'):
            continue
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Unsafe source manifest path.')
        path = root / rel
        if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
            raise ValueError('Source inputs must be regular files without symlink ancestors.')
        result.append((path, name))
    return result


def bundle(destination, selection, root=ROOT):
    selection = validate(selection)
    paths = source_paths(root)
    if any(n in {'config/workflow.json', 'source-sha256.json'} for _, n in paths):
        raise ValueError('Generated recipe and source hashes must not be in the source allowlist.')
    data = {name: path.read_bytes() for path, name in paths}
    data['config/workflow.json'] = (json.dumps(selection, indent=2) + '\n').encode()
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in data.items()}
    data['source-sha256.json'] = (json.dumps(hashes, indent=2) + '\n').encode()
    # Exclusive creation; never overwrite a user's existing archive.
    with destination.open('xb') as stream, tarfile.open(fileobj=stream, mode='w') as tar:
        for name, content in data.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(content))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'bundle', 'check-tool'])
    parser.add_argument('tool', nargs='?', choices=list(LABELS.values()))
    parser.add_argument('--recipe', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'check-tool':
        if args.tool is None:
            parser.error('check-tool requires a tool')
        raise SystemExit(0 if args.tool in load(ROOT)['tools'] else 1)
    if args.recipe is None:
        parser.error('--recipe is required')
    selection = read(args.recipe)
    if args.action == 'check':
        print(json.dumps(selection, indent=2))
    else:
        if args.output is None:
            parser.error('bundle requires --output pointing to a new archive')
        bundle(args.output, selection)
        print('Prepared local build source: ' + str(args.output))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit('Recipe stopped: ' + str(error))
