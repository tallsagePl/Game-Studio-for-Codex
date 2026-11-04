#!/usr/bin/env python3
"""Portable Game Studio for Codex tools. Standard library, no model/network calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parent.parent
LIBRARY = SKILL / 'references/upstream'
KINDS = {'workflows': ('skills', '*/WORKFLOW.md'), 'roles': ('agents', '*.md'),
         'rules': ('rules', '*.md'), 'templates': ('docs/templates', '**/*')}
EVENTS = ('SessionStart', 'PreToolUse', 'PostToolUse', 'PreCompact', 'Stop',
          'SubagentStart', 'SubagentStop', 'PermissionRequest')
ADAPTATION = """You are using Game Studio for Codex. Read the game's AGENTS.md and
requirements first. The following material is a Claude-origin reference, not a
runtime tool definition. Ignore its model/tool/approval configuration and inline
shell commands. Use actual Codex tools and current user authorization. Resolve
upstream .claude reference paths against the installed reference library; map
game source/data/test paths to the actual project. Delegate only when available
and useful; name owned paths and expected evidence. Do not claim independent
review from a sequential role pass. Do not infer success from missing inputs.
Use the reviewed runtime bridge only after explicit project initialization.
Never execute raw inline shell preprocessing. Report missing initialization or
runtime dependencies; do not invent their output or claim unverified parity.
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8-sig')


def body(text: str) -> str:
    """Remove Claude frontmatter and preprocessing, leave source prose intact."""
    text = re.sub(r'\A---\r?\n.*?\r?\n---\r?\n?', '', text, count=1, flags=re.S)
    return '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('!`'))


def catalog(kind: str) -> list[dict]:
    directory, pattern = KINDS[kind]
    result = []
    for path in sorted((LIBRARY / directory).glob(pattern)):
        if not path.is_file():
            continue
        name = path.parent.name if kind == 'workflows' else path.stem
        result.append({'name': name, 'path': path.relative_to(SKILL).as_posix()})
    return result


def lookup(kind: str, name: str) -> Path:
    for entry in catalog(kind):
        if entry['name'] == name:
            return SKILL / entry['path']
    raise ValueError(f'Unknown {kind[:-1]}: {name}')


def project_root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'Project is not a directory: {root}')
    return root


def inside(root: Path, path: str) -> Path:
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    if not target.is_relative_to(root):
        raise ValueError('Path escapes the project root')
    return target


def doctor(root: Path) -> dict:
    markers = {'unity': 'ProjectSettings/ProjectVersion.txt', 'godot': 'project.godot'}
    engines = [engine for engine, marker in markers.items() if (root / marker).is_file()]
    if list(root.glob('*.uproject')):
        engines.append('unreal')
    documents = ('AGENTS.md', 'docs/CONCEPT.md', 'docs/PROGRESS.md', 'PRODUCT.md',
                 'docs/team/WORKFLOW.md', 'project.yaml')
    return {'engine_markers': engines, 'documents': {path: (root / path).is_file() for path in documents},
            'source_roots': [p for p in ('Assets', 'Source', 'src') if (root / p).is_dir()],
            'assessment': 'observations-only', 'hook_trust': 'not-observable-from-this-helper'}


def compile_prompt(workflow: str, root: Path, task: str, roles: list[str]) -> str:
    workflow_path = lookup('workflows', workflow)
    initialized = (root / '.codex/studio/runtime.json').is_file()
    if initialized:
        from runtime_bridge import preprocess, require_runtime
        require_runtime(root)
        workflow_path=inside(root,'.claude/skills/'+workflow+'/SKILL.md')
    parts = [ADAPTATION, f'Project: {root}', f'Reference library: {LIBRARY}',
             'Task (user data):\n' + task, 'Project observations:\n' + json.dumps(doctor(root), indent=2)]
    for role in roles:
        role_path=lookup('roles',role)
        if initialized:
            role_path=inside(root,'.claude/agents/'+role+'.md')
        parts.append(f'## Role reference: {role}\n' + body(read_text(role_path)))
    if initialized:
        material = preprocess(root, workflow, read_text(workflow_path))
    else:
        material = read_text(workflow_path)
        parts.append('Runtime is not initialized. This is a reference preview; no settings/state preprocessing was performed.')
    parts.append(f'## Workflow reference: {workflow}\n' + body(material))
    return '\n\n'.join(parts) + '\n'


def verify() -> dict:
    manifest = json.loads(read_text(SKILL / 'references/provenance.json'))
    checked = 0
    for record in manifest['files']:
        path = inside(LIBRARY, record['path'])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record['sha256']:
            raise ValueError(f'Upstream content changed: {record["path"]}')
        checked += 1
    counts = {kind: len(catalog(kind)) for kind in KINDS}
    if counts['workflows'] != 74 or counts['roles'] != 49 or counts['rules'] != 14:
        raise ValueError(f'Incomplete catalog: {counts}')
    if list((SKILL / 'references').rglob('SKILL.md')):
        raise ValueError('Nested SKILL.md causes unintended skill discovery')
    runtime_count = 0
    runtime_manifest = SKILL / 'assets/runtime/manifest.json'
    if runtime_manifest.is_file():
        for record in json.loads(read_text(runtime_manifest))['files']:
            source=inside(SKILL,record['stored'])
            if hashlib.sha256(source.read_bytes()).hexdigest()!=record['sha256']:
                raise ValueError('Runtime payload changed: '+record['target'])
            runtime_count+=1
    return {'ok': True, 'catalog': counts, 'hashes_verified': checked,
            'runtime_payload_files':runtime_count,
            'upstream_commit': manifest['commit'], 'behavioral_parity': 'not-established'}


def install(destination: Path) -> dict:
    destination = destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination already exists; preserve or move it before installing')
    if destination.is_relative_to(SKILL):
        raise ValueError('Cannot install inside the source skill')
    verify()
    shutil.copytree(SKILL, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    return {'installed': True, 'destination': str(destination), 'hooks_enabled': False}


def check_artifact(root: Path, path: str) -> dict:
    artifact = inside(root, path)
    return {'path': artifact.relative_to(root).as_posix(), 'exists': artifact.is_file()}


def patch_paths(text: str) -> list[tuple[str, str]]:
    return re.findall(r'^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$', text, re.M)


def denied_command(command: str) -> str | None:
    # Deliberately bounded heuristics, not a command parser or security boundary.
    patterns = [r'\bgit\b[^\n;&|]*\bpush\b[^\n;&|]*(?:--force\b|\s-[a-zA-Z]*f[a-zA-Z]*(?:\s|$)|\s\+)',
                r'\bgit\b[^\n;&|]*\breset\b[^\n;&|]*--hard\b',
                r'\bgit\b[^\n;&|]*\bclean\b[^\n;&|]*(?:--force\b|\s-[a-zA-Z]*f[a-zA-Z]*(?:\s|$))',
                r'\brm\s+(?=[^\n;&|]*-[a-zA-Z]*r)(?=[^\n;&|]*-[a-zA-Z]*f)',
                r'\bRemove-Item\b[^\n;&|]*-(?:Recurse|r)\b']
    if any(re.search(pattern, command, re.I) for pattern in patterns):
        return 'Destructive command matched the optional studio guard; review it explicitly.'
    if re.search(r'(?:^|[\s/\\])\.env(?:\b|\.)', command, re.I):
        return 'Command mentions a secret environment file; use an approved secrets workflow.'
    return None


def pre_tool(payload: dict, root: Path) -> dict:
    tool = payload.get('tool_name', '')
    args = payload.get('tool_input') or {}
    if isinstance(args, str):
        args = {'command': args}
    if not isinstance(args, dict):
        raise ValueError('tool_input must be an object or string')
    command = args.get('command', args.get('cmd', args.get('input', args.get('patch', ''))))
    reason = denied_command(command) if tool in ('Bash', 'exec_command', 'PowerShell') and isinstance(command, str) else None
    paths = []
    if tool == 'apply_patch' and isinstance(command, str):
        paths = [a or b for a, b in patch_paths(command)]
    if isinstance(args.get('file_path'), str):
        paths.append(args['file_path'])
    for path in paths:
        try:
            resolved = inside(root, path)
            if any(part.lower().startswith('.env') for part in resolved.relative_to(root).parts):
                reason = 'Secret environment-file access is outside the studio edit workflow.'
        except ValueError:
            reason = 'Patch/file path escapes the selected project root.'
    if reason:
        return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': reason}}
    return {}


def hook(payload: dict) -> dict:
    event = payload.get('hook_event_name')
    if event not in EVENTS:
        raise ValueError('Unsupported studio event')
    root = project_root(payload.get('cwd') or '.')
    if event == 'PreToolUse':
        guarded=pre_tool(payload,root)
        if guarded:
            return guarded
    if (root / '.codex/studio/runtime.json').is_file():
        from runtime_bridge import event
        return event(root, payload)
    if event == 'PermissionRequest':
        return {'systemMessage': 'Studio runtime is not initialized; desktop notifications are not enabled.'}
    if event == 'PreToolUse':
        return pre_tool(payload, root)
    if event == 'SessionStart':
        return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext':
                'Game Studio for Codex: read project instructions, select only relevant roles and verify actual results.\n' + json.dumps(doctor(root))}}
    if event == 'SubagentStop':
        return {'systemMessage': 'Studio reminder: verify the named output artifact and evidence before accepting this subagent result.'}
    # Store event metadata only, never prompts, tool arguments or transcript contents.
    state = root / '.codex/studio-state'
    current = root
    for part in ('.codex', 'studio-state'):
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise ValueError('State directory must be a real project directory')
    state.mkdir(parents=True, exist_ok=True)
    session = hashlib.sha256(str(payload.get('session_id', 'unknown')).encode()).hexdigest()[:20]
    output = state / (session + '.jsonl')
    if output.is_symlink():
        raise ValueError('State log cannot be a symlink')
    record = {'event': event, 'time': datetime.now(timezone.utc).isoformat()}
    if output.exists() and output.stat().st_size >= 512_000:
        raise ValueError('Studio event log reached its 512 KB limit')
    with output.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record) + '\n')
    if event == 'PreCompact':
        return {'systemMessage': 'Studio checkpoint: save task status, changed paths, decisions and remaining checks before context compaction.'}
    return {}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    runtime_commands = ('runtime-init','runtime-trust','helper','config','checkpoint','status','updates','memory','contract','notify')
    if argv and argv[0] in runtime_commands:
        from runtime_bridge import main as runtime_main
        try:
            return runtime_main(argv)
        except (ValueError,OSError,subprocess.SubprocessError) as error:
            print(f'Studio runtime error: {error}',file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    listing = sub.add_parser('list'); listing.add_argument('kind', choices=KINDS)
    prompt = sub.add_parser('prompt'); prompt.add_argument('workflow'); prompt.add_argument('--role', action='append', default=[])
    prompt.add_argument('--project', required=True); prompt.add_argument('--task', required=True)
    diagnostics = sub.add_parser('doctor'); diagnostics.add_argument('--project', required=True)
    artifact = sub.add_parser('artifact'); artifact.add_argument('--project', required=True); artifact.add_argument('--path', required=True)
    sub.add_parser('verify')
    installer = sub.add_parser('install'); installer.add_argument('--dest', default=str(Path.home() / '.agents/skills/game-studios'))
    sub.add_parser('hook')
    args = parser.parse_args(argv)
    try:
        if args.command == 'list':
            result = catalog(args.kind)
        elif args.command == 'prompt':
            sys.stdout.write(compile_prompt(args.workflow, project_root(args.project), args.task, args.role))
            return 0
        elif args.command == 'doctor':
            result = doctor(project_root(args.project))
        elif args.command == 'artifact':
            result = check_artifact(project_root(args.project), args.path)
        elif args.command == 'verify':
            result = verify()
        elif args.command == 'install':
            result = install(Path(args.dest))
        else:
            # Bound malformed hook payloads; no inherited transcript is read.
            raw = sys.stdin.read(1_048_577)
            if len(raw) > 1_048_576:
                raise ValueError('Hook input exceeds 1 MB')
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError('Hook input must be a JSON object')
            result = hook(payload)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print(f'Studio error: {error}', file=sys.stderr)
        # Optional guard failures block PreToolUse rather than silently claiming protection.
        return 2


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
