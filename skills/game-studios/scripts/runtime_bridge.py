"""Codex transport for the pinned studio runtime. No implicit initialization."""
from __future__ import annotations
import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SKILL = Path(__file__).resolve().parent.parent
LOCK = '.codex/studio/runtime.json'


def confined(root, relative):
    root = Path(root).resolve(); path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path leaves its selected root')
    return path


def manifest():
    return json.loads((SKILL / 'assets/runtime/manifest.json').read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload(entry):
    path = confined(SKILL, entry['stored'])
    if digest(path) != entry['sha256']:
        raise ValueError('Bundled runtime changed: ' + entry['target'])
    return path.read_bytes()


def text_body(text):
    return re.sub(r'\A---\r?\n.*?\r?\n---\r?\n?', '', text, count=1, flags=re.S)


def initialize(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('Select an existing project directory')
    if (root / '.gitignore').is_symlink():
        raise ValueError('.gitignore must not be a symlink')
    # Refuse existing Claude data instead of merging or replacing it silently.
    if (root / '.claude').exists() or (root / '.claude').is_symlink():
        raise ValueError('Existing .claude directory: use a separate worktree or reviewed manual integration')
    entries = manifest()['files']
    prepared = [(entry, payload(entry)) for entry in entries]
    codex = root / '.codex'
    if codex.is_symlink():
        raise ValueError('.codex must not be a symlink')
    state = confined(root, '.codex/studio'); state.mkdir(parents=True, exist_ok=True)
    if (state / 'runtime.json').exists():
        raise ValueError('Runtime already initialized')
    role_paths = []
    for entry, content in prepared:
        target = confined(root, entry['target'])
        if target.is_symlink():
            raise ValueError('Seed target cannot be a symlink')
        if entry['target'].startswith('.claude/agents/') and entry['target'].endswith('.md'):
            name = Path(entry['target']).stem
            path = confined(root, '.codex/agents/game-studio-' + name + '.toml')
            if path.exists():
                raise ValueError('Native role already exists: ' + name)
            role_paths.append((name, path, content.decode('utf-8-sig')))
    # Install the complete .claude runtime atomically; seeds never overwrite game files.
    with tempfile.TemporaryDirectory(prefix='install-', dir=state) as scratch:
        tree = Path(scratch) / '.claude'; tree.mkdir()
        for entry, content in prepared:
            if entry['required']:
                path = tree / Path(entry['target']).relative_to('.claude')
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
        os.replace(tree, root / '.claude')
    for entry, content in prepared:
        if not entry['required']:
            path = confined(root, entry['target'])
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(content)
    for name, path, content in role_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        instructions = ('Follow current user authorization and project AGENTS.md. Use Codex tools, not Claude model/tool declarations. '
                        'Read the relevant Game Studio workflow. Keep one writer per file and verify actual results. '
                        f'Project memory: .claude/agent-memory/{name}/MEMORY.md. Read when relevant and retain only useful project facts.\n\n'
                        + text_body(content))
        with path.open('x', encoding='utf-8') as stream:
            stream.write('name = ' + json.dumps('game-studio-' + name) + '\n')
            stream.write('description = ' + json.dumps('Game Studio role: ' + name) + '\n')
            stream.write('developer_instructions = ' + json.dumps(instructions, ensure_ascii=False) + '\n')
    lock = {'baseline':manifest()['baseline'], 'files':{entry['target']:entry['sha256'] for entry in entries if entry['required']},
            'allow_network':False, 'native_roles':len(role_paths)}
    (state / 'runtime.json').write_text(json.dumps(lock, indent=2)+'\n', encoding='utf-8')
    ignore = root / '.gitignore'
    with ignore.open('a', encoding='utf-8') as stream:
        stream.write('\n# Game Studio local/session data\n.codex/studio/\n.claude/agent-memory/\nproduction/session-logs/\nproduction/session-state/\nproject.local.yaml\n')
    return {'initialized':True,'roles_exported':len(role_paths),'runtime_files':len(lock['files']),
            'hooks_trusted':False,'tests_run':False,'allow_network':False}


def load_lock(root):
    root = Path(root).resolve()
    path = confined(root, LOCK)
    if not path.is_file():
        raise ValueError('Runtime not initialized; run runtime-init explicitly')
    return json.loads(path.read_text(encoding='utf-8'))


def changed_runtime(root):
    lock = load_lock(root)
    return [name for name, expected in lock['files'].items()
            if not confined(root,name).is_file() or digest(confined(root,name)) != expected]


def require_runtime(root):
    changed = changed_runtime(root)
    if changed:
        raise ValueError('Runtime differs from reviewed baseline: ' + ', '.join(changed[:5]) + '; review and use runtime-trust --accept explicitly')


def bash_path():
    candidates = [os.environ.get('CODEX_STUDIO_BASH'),
                  'C:/Program Files/Git/bin/bash.exe' if os.name == 'nt' else shutil.which('bash')]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise ValueError('Bash is required for the retained runtime; set CODEX_STUDIO_BASH')


def execute(root, name, args=(), input_text='', timeout=20, allow_network=False):
    root = Path(root).resolve(); require_runtime(root)
    lock = load_lock(root)
    if name not in lock['files'] or not name.endswith('.sh'):
        raise ValueError('Not an allowlisted runtime shell script')
    for index, argument in enumerate(args):
        override = args[index+1] if argument=='--root' and index+1<len(args) else (argument[7:] if argument.startswith('--root=') else None)
        if argument=='--root' and override is None:
            raise ValueError('--root needs a value')
        if override is not None and Path(override).resolve()!=root:
            raise ValueError('Helper --root must equal the selected --project')
    environment = os.environ.copy()
    environment.update({'CLAUDE_PROJECT_DIR':root.as_posix(),'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'})
    if not allow_network:
        environment['CI'] = '1'  # Original update-check helper honors CI: no background requests.
    result = subprocess.run([bash_path(), confined(root,name).as_posix(), *args], cwd=root,
                            env=environment, input=input_text, text=True, encoding='utf-8', errors='replace',
                            capture_output=True, timeout=timeout)
    return result


def planned_files(root, patch, post=False):
    """Conservative preview of native apply_patch. Ambiguous hunks are refused."""
    lines = patch.splitlines(); result=[]; i=0
    while i < len(lines):
        match=re.match(r'^\*\*\* (Add|Update|Delete) File: (.+)$',lines[i])
        if not match:
            i+=1; continue
        operation,name=match.groups(); path=confined(root,name); i+=1; block=[]; moved=None
        while i < len(lines) and not re.match(r'^\*\*\* (?:Add|Update|Delete) File:|^\*\*\* End Patch',lines[i]):
            if lines[i].startswith('*** Move to: '):
                moved=lines[i][13:]; confined(root,moved)
            else:
                block.append(lines[i])
            i+=1
        if post:
            final_path=confined(root,moved) if moved else path
            content=final_path.read_text(encoding='utf-8-sig') if final_path.is_file() else ''
        elif operation == 'Add':
            content='\n'.join(line[1:] for line in block if line.startswith('+'))+'\n'
        elif operation == 'Delete':
            content=''
        else:
            if not path.is_file():
                raise ValueError('Patch update target is missing: '+name)
            original=path.read_text(encoding='utf-8-sig').splitlines(); cursor=0; output=[]; groups=[]; group=[]
            for line in block:
                if line.startswith('@@'):
                    if group: groups.append(group)
                    group=[]
                elif not line.startswith('*** End of File'):
                    group.append(line)
            if group: groups.append(group)
            for group in groups:
                old=[line[1:] for line in group if line.startswith((' ','-'))]
                new=[line[1:] for line in group if line.startswith((' ','+'))]
                if not old:
                    raise ValueError('Insertion without context cannot be safely previewed')
                positions=[n for n in range(cursor,len(original)-len(old)+1) if original[n:n+len(old)]==old]
                if len(positions)!=1:
                    raise ValueError('Patch context is absent or ambiguous; split the patch or supply unique context')
                n=positions[0]; output+=original[cursor:n]+new; cursor=n+len(old)
            content='\n'.join(output+original[cursor:])+'\n'
        result.append({'tool_name':'Write','tool_input':{'file_path':path.as_posix(),'content':content}})
        if moved:
            result.append({'tool_name':'Write','tool_input':{'file_path':confined(root,moved).as_posix(),'content':content}})
    if not result:
        raise ValueError('No native patch operations recognized; validation cannot be skipped')
    if len(result)>32:
        raise ValueError('Split patches larger than 32 file operations for bounded validation')
    return result


def normalize(root, payload):
    tool=payload.get('tool_name',''); args=payload.get('tool_input') or {}
    if isinstance(args,str): args={'command':args}
    if not isinstance(args,dict): raise ValueError('Tool arguments must be an object')
    command=args.get('command',args.get('cmd',args.get('input',args.get('patch',''))))
    if tool=='apply_patch':
        return [{**payload, **item} for item in planned_files(root,command,post=payload.get('hook_event_name')=='PostToolUse')]
    if tool in ('exec_command','PowerShell'):
        return [{**payload,'tool_name':'Bash','tool_input':{**args,'command':command}}]
    if tool=='Read' or tool.endswith('read_file'):
        path=args.get('file_path',args.get('path'))
        return [{**payload,'tool_name':'Read','tool_input':{**args,'file_path':confined(root,path).as_posix()}}] if path else []
    return [payload]


def extract_output(text):
    try:
        value=json.loads(text)
    except (ValueError,TypeError):
        return text.strip(),False
    if not isinstance(value,dict): return text.strip(),False
    specific=value.get('hookSpecificOutput') or {}
    message='\n'.join(str(x) for x in (value.get('systemMessage'),specific.get('additionalContext'),value.get('reason'),specific.get('permissionDecisionReason')) if x)
    return message, specific.get('permissionDecision')=='deny' or value.get('decision')=='block'


def permission_denial(settings, operation):
    tool=operation.get('tool_name',''); arguments=operation.get('tool_input') or {}
    command=arguments.get('command','')
    path=arguments.get('file_path','').replace('\\','/')
    for declaration in settings.get('permissions',{}).get('deny',[]):
        match=re.fullmatch(r'([^()]+)\((.*)\)',declaration)
        if not match: continue
        kind,pattern=match.groups()
        if kind=='PowerShell' and tool=='Bash':
            value=command
        elif kind!=tool:
            continue
        else:
            value=command if kind=='Bash' else path
        patterns=[pattern,pattern.removeprefix('**/')]
        if any(fnmatch.fnmatchcase(value.lower(),p.lower()) for p in patterns):
            return 'Preserved studio permission denied this operation: '+declaration
    return None


def expand_braces(pattern):
    match=re.search(r'\{([^{}]+)\}',pattern)
    if not match: return [pattern]
    return [p for choice in match[1].split(',') for p in expand_braces(pattern[:match.start()]+choice+pattern[match.end():])]


def matching_rules(root, paths):
    result=[]
    for file in sorted((Path(root)/'.claude/rules').glob('*.md')):
        text=file.read_text(encoding='utf-8-sig')
        front=re.match(r'---\s*\n(.*?)\n---',text,re.S)
        patterns=re.findall(r'^\s*-\s*["\'](.+?)["\']\s*$',front[1],re.M) if front else []
        def optional_globstars(pattern):
            if '**/' not in pattern: return [pattern]
            prefix,suffix=pattern.split('**/',1)
            return [prefix+middle+tail for middle in ('**/','') for tail in optional_globstars(suffix)]
        patterns=[variant for pattern in patterns for expanded in expand_braces(pattern) for variant in optional_globstars(expanded)]
        if not patterns or any(fnmatch.fnmatchcase(path,p) for p in patterns for path in paths):
            result.append(text_body(text))
    return '\n\n'.join(result)


def contract(root, agent_id, path=None):
    state=confined(root,'.codex/studio/contracts'); state.mkdir(parents=True,exist_ok=True)
    file=state/(hashlib.sha256(agent_id.encode()).hexdigest()+'.json')
    if path is not None:
        target=confined(root,path)
        file.write_text(json.dumps({'path':target.relative_to(root).as_posix()}),encoding='utf-8')
    return json.loads(file.read_text()) if file.is_file() else None


def event(root,payload):
    root=Path(root).resolve(); require_runtime(root)
    name=payload['hook_event_name']; original=json.loads((root/'.claude/settings.json').read_text(encoding='utf-8-sig'))
    native_name=name
    if name=='PermissionRequest':
        name='Notification'; payload={**payload,'notification_type':'permission_prompt','message':'Codex requests permission: '+str(payload.get('tool_name','tool'))}
    operations=normalize(root,payload) if name in ('PreToolUse','PostToolUse') else [payload]
    messages=[]; denied=False
    for operation in operations:
        if name=='PreToolUse':
            reason=permission_denial(original,operation)
            if reason:
                messages.append(reason); denied=True; continue
        if name=='SubagentStop':
            # Never parse or copy the host's unstable full transcript format.
            known=contract(root,str(operation.get('agent_id','unknown')))
            operation={key:value for key,value in operation.items() if key!='agent_transcript_path'}
            if known:
                synthetic=confined(root,'.codex/studio/contracts/'+hashlib.sha256(str(operation.get('agent_id','unknown')).encode()).hexdigest()+'.jsonl')
                synthetic.write_text(json.dumps({'type':'user','message':{'role':'user','content':'Write your full output to `'+known['path']+'`'}})+'\n',encoding='utf-8')
                operation['agent_transcript_path']=synthetic.as_posix()
            else:
                messages.append('Return-artifact contract not registered; artifact acceptance must be checked by the coordinator.')
        for group in original.get('hooks',{}).get(name,[]):
            matcher=group.get('matcher','')
            value=operation.get('tool_name','') if name in ('PreToolUse','PostToolUse') else operation.get('notification_type','')
            if matcher and not re.fullmatch(matcher,value): continue
            for handler in group['hooks']:
                match=re.search(r'/\.claude/(hooks/[^"\s]+\.sh)',handler['command'])
                if not match: raise ValueError('Unsupported upstream handler declaration')
                result=execute(root,'.claude/'+match[1],input_text=json.dumps(operation,ensure_ascii=False),timeout=handler.get('timeout',15)+2)
                message,blocked=extract_output(result.stdout)
                if message: messages.append(message)
                if result.stderr.strip(): messages.append(result.stderr.strip())
                if result.returncode not in (0,2): raise ValueError('Runtime hook failed: '+match[1]+'\n'+result.stderr)
                denied=denied or result.returncode==2 or blocked
        if name=='PreToolUse' and operation.get('tool_name') in ('Write','Edit'):
            path=operation['tool_input'].get('file_path')
            if path: messages.append(matching_rules(root,[confined(root,path).relative_to(root).as_posix()]))
        if name=='SubagentStart':
            role=str(operation.get('agent_type','')).removeprefix('game-studio-')
            if re.fullmatch(r'[a-z0-9-]+',role):
                memory=confined(root,'.claude/agent-memory/'+role+'/MEMORY.md')
                if memory.is_file(): messages.append(memory.read_text(encoding='utf-8')[:16000])
    text='\n\n'.join(m for m in messages if m).strip()
    if name=='Stop':
        notification=execute(root,'.claude/hooks/notify.sh',input_text=json.dumps({'notification_type':'idle_prompt','message':'Game Studio for Codex has finished this turn.'}),timeout=10)
        notification_text,_=extract_output(notification.stdout)
        if notification_text: text+='\n'+notification_text
    if native_name=='PreToolUse':
        specific={'hookEventName':native_name}
        if denied: specific.update(permissionDecision='deny',permissionDecisionReason=text or 'Studio validation refused the tool call')
        elif text: specific['additionalContext']=text
        return {'hookSpecificOutput':specific}
    if denied and native_name=='PostToolUse': return {'decision':'block','reason':text or 'Written output failed studio validation'}
    if native_name in ('SessionStart','SubagentStart'):
        return {'hookSpecificOutput':{'hookEventName':native_name,'additionalContext':text}}
    return {'systemMessage':text} if text else {}


def preprocess(root,workflow,text):
    def replace(match):
        command=match[1]
        if 'yaml-helper.sh' in command:
            keys=re.search(r'--keys\s+([^`\s]+)',command)
            args=['resolve_config']+(['--keys',keys[1]] if keys else [])
            result=execute(root,'.claude/hooks/yaml-helper.sh',args)
        elif 'story-status.sh' in command:
            result=execute(root,'.claude/scripts/story-status.sh')
        elif command=='git log --oneline -30 2>/dev/null || true':
            result=subprocess.run(['git','log','--oneline','-30'],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
        elif command=='git tag --list --sort=-v:refname 2>/dev/null | head -5':
            result=subprocess.run(['git','tag','--list','--sort=-v:refname'],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
            result.stdout='\n'.join(result.stdout.splitlines()[:5])
        elif command.startswith('ls production/sprints/'):
            directory=Path(root)/'production/sprints'
            return '\n'.join(p.name for p in sorted(directory.iterdir())) if directory.is_dir() else '(no production/sprints/ directory yet)'
        else:
            raise ValueError('Unmapped workflow preprocessing: '+command)
        if result.returncode: raise ValueError('Preprocessing failed: '+result.stderr)
        return result.stdout.strip()
    require_runtime(root)
    return re.sub(r'^!`([^`]+)`\s*$',replace,text,flags=re.M)


def main(argv):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('runtime-init','runtime-trust','helper','config','checkpoint','status','updates','memory','contract','notify'))
    parser.add_argument('--project',required=True); parser.add_argument('--accept',action='store_true')
    parser.add_argument('--allow-network',action='store_true'); parser.add_argument('--agent-id'); parser.add_argument('--path')
    parser.add_argument('--role'); parser.add_argument('--text'); parser.add_argument('--model',default='Unknown')
    parser.add_argument('--context-used',type=float)
    separator=argv.index('--') if '--' in argv else len(argv)
    args=parser.parse_args(argv[:separator]); args.arguments=argv[separator+1:] if separator<len(argv) else []
    root=Path(args.project).resolve()
    if args.action=='runtime-init': print(json.dumps(initialize(root),indent=2)); return 0
    if args.action=='runtime-trust':
        changes=changed_runtime(root)
        if args.accept:
            lock=load_lock(root)
            for name in changes: lock['files'][name]=digest(confined(root,name))
            confined(root,LOCK).write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'changed':changes,'accepted':args.accept},indent=2)); return 0
    require_runtime(root)
    if args.action=='contract':
        if not args.agent_id or not args.path: raise ValueError('contract requires --agent-id and --path')
        print(json.dumps(contract(root,args.agent_id,args.path))); return 0
    if args.action=='memory':
        if not args.role or not re.fullmatch(r'[a-z0-9-]+',args.role): raise ValueError('Select a valid role')
        path=confined(root,'.claude/agent-memory/'+args.role+'/MEMORY.md')
        if args.text is not None:
            if len(args.text)>16000: raise ValueError('Keep role memory under 16000 characters')
            path.parent.mkdir(parents=True,exist_ok=True); path.write_text(args.text,encoding='utf-8')
        print(path.read_text(encoding='utf-8') if path.is_file() else ''); return 0
    if args.action=='config': name='.claude/hooks/yaml-helper.sh'; arguments=['resolve_config']+args.arguments
    elif args.action=='checkpoint': name='.claude/scripts/session-state.sh'; arguments=args.arguments or ['show']
    elif args.action=='status': name='.claude/statusline.sh'; arguments=[]
    elif args.action=='updates':
        if not args.allow_network: raise ValueError('Update checking requires explicit --allow-network')
        name='.claude/hooks/update-check.sh'; arguments=args.arguments or ['refresh']
    elif args.action=='notify': name='.claude/hooks/notify.sh'; arguments=[]
    else:
        if not args.arguments: raise ValueError('helper requires its allowlisted name and arguments')
        name='.claude/scripts/'+args.arguments[0]+'.sh'; arguments=args.arguments[1:]
    stdin=json.dumps({'model':{'display_name':args.model},'workspace':{'project_dir':root.as_posix()},'context_window':{'used_percentage':args.context_used}}) if args.action=='status' else (json.dumps({'message':args.text or 'Game Studio for Codex needs attention','notification_type':'idle_prompt'}) if args.action=='notify' else (sys.stdin.read() if args.action=='checkpoint' and arguments[0]!='show' else ''))
    result=execute(root,name,arguments,input_text=stdin,timeout=60,allow_network=args.allow_network)
    sys.stdout.write(result.stdout); sys.stderr.write(result.stderr); return result.returncode
