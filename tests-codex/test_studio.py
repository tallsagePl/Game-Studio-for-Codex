import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/game-studios/scripts/studio.py'
spec = importlib.util.spec_from_file_location('studio', SCRIPT)
studio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(studio)


class StudioTests(unittest.TestCase):
    def setUp(self):
        # No real project, credential, game build or model endpoint is touched.
        self.temporary = tempfile.TemporaryDirectory(prefix='codex-studio-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_provenance_matches_original_and_installed_library(self):
        result = studio.verify()
        self.assertEqual(result['hashes_verified'], 379)
        self.assertEqual(result['behavioral_parity'], 'not-established')
        manifest = json.loads(studio.read_text(studio.SKILL / 'references/provenance.json'))
        for entry in manifest['files']:
            with self.subTest(source=entry['source_path']):
                self.assertEqual(hashlib.sha256((ROOT / entry['source_path']).read_bytes()).hexdigest(), entry['sha256'])

    def test_all_74_workflows_compile_without_preprocessing(self):
        for entry in studio.catalog('workflows'):
            with self.subTest(workflow=entry['name']):
                result = studio.compile_prompt(entry['name'], self.root, 'Read-only fixture task', [])
                self.assertIn('## Workflow reference: ' + entry['name'], result)
                self.assertIn('Read-only fixture task', result)
                self.assertNotIn('\n!`', result)
                self.assertNotIn('\nallowed-tools:', result)
                self.assertIn('not a\nruntime tool definition', result)

    def test_all_49_roles_compile_without_model_override(self):
        for entry in studio.catalog('roles'):
            with self.subTest(role=entry['name']):
                result = studio.compile_prompt('scope-check', self.root, 'Fixture', [entry['name']])
                self.assertIn('## Role reference: ' + entry['name'], result)
                self.assertNotIn('\nmodel: opus', result)
                self.assertNotIn('\nmodel: sonnet', result)

    def test_unknown_workflow_and_traversal_names_fail(self):
        for name in ('missing-workflow', '../agents/producer', '/etc/passwd'):
            with self.assertRaises(ValueError):
                studio.lookup('workflows', name)

    def test_unity_marker_and_existing_team_detected(self):
        (self.root / 'ProjectSettings').mkdir()
        (self.root / 'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.3.27f2')
        (self.root / 'docs/team').mkdir(parents=True)
        (self.root / 'docs/team/WORKFLOW.md').write_text('Existing authority')
        result = studio.doctor(self.root)
        self.assertEqual(result['engine_markers'], ['unity'])
        self.assertTrue(result['documents']['docs/team/WORKFLOW.md'])

    def test_godot_and_unreal_markers_detected(self):
        (self.root / 'project.godot').write_text('config_version=5')
        (self.root / 'sample.uproject').write_text('{}')
        self.assertEqual(studio.doctor(self.root)['engine_markers'], ['godot', 'unreal'])

    def test_empty_project_is_not_claimed_configured(self):
        result = studio.doctor(self.root)
        self.assertEqual(result['engine_markers'], [])
        self.assertEqual(result['assessment'], 'observations-only')

    def test_artifact_presence_and_missing_are_distinguished(self):
        (self.root / 'artifact.md').write_text('fixture')
        self.assertTrue(studio.check_artifact(self.root, 'artifact.md')['exists'])
        self.assertFalse(studio.check_artifact(self.root, 'absent.md')['exists'])
        with self.assertRaises(ValueError):
            studio.check_artifact(self.root, '../outside.md')

    def pre_tool(self, name, args):
        return studio.hook({'hook_event_name':'PreToolUse','tool_name':name,'tool_input':args,'cwd':str(self.root)})

    def test_destructive_commands_block_and_read_only_commands_pass(self):
        for command in ('git push --force origin main', 'git push -uf origin main',
                        'git reset --hard HEAD', 'git clean -df', 'rm -rf folder',
                        'Remove-Item folder -Recurse'):
            with self.subTest(command=command):
                result = self.pre_tool('Bash', {'command': command})
                self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.pre_tool('Bash', {'command': 'git status --short'}), {})
        self.assertEqual(self.pre_tool('Bash', {'cmd': 'git log -3'}), {})

    def test_patch_move_and_secret_paths_block(self):
        for command in ('*** Update File: ../outside.txt\n',
                        '*** Add File: .env\n',
                        '*** Update File: good.txt\n*** Move to: ../outside.txt\n'):
            with self.subTest(patch=command):
                self.assertEqual(self.pre_tool('apply_patch', {'command':command})['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.pre_tool('apply_patch', {'command':'*** Add File: Assets/Good.cs\n'}), {})

    def test_patch_transport_forms_are_guarded(self):
        patch = '*** Update File: ../outside.txt\n'
        for args in (patch, {'command':patch}, {'input':patch}, {'patch':patch}):
            with self.subTest(args=args):
                self.assertEqual(self.pre_tool('apply_patch', args)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_structured_secret_read_and_env_command_block(self):
        self.assertIn('hookSpecificOutput', self.pre_tool('Read', {'file_path':'.env.local'}))
        self.assertIn('hookSpecificOutput', self.pre_tool('Bash', {'command':'cat .env'}))

    def test_every_native_event_returns_valid_output(self):
        for event in studio.EVENTS:
            with self.subTest(event=event):
                result = studio.hook({'hook_event_name':event,'cwd':str(self.root),'session_id':'fixture/../../secret'})
                self.assertIsInstance(result, dict)
                json.dumps(result)
        logs = list((self.root / '.codex/studio-state').glob('*.jsonl'))
        self.assertEqual(len(logs), 1)
        lines = [json.loads(line) for line in logs[0].read_text().splitlines()]
        self.assertEqual({line['event'] for line in lines}, {'PostToolUse','PreCompact','Stop','SubagentStart'})

    def test_hooks_do_not_retain_prompt_or_tool_arguments(self):
        studio.hook({'hook_event_name':'PostToolUse','cwd':str(self.root),'session_id':'fixture',
                     'tool_input':{'content':'dummy-private-data'},'prompt':'dummy-private-data'})
        data = next((self.root / '.codex/studio-state').glob('*.jsonl')).read_text()
        self.assertNotIn('dummy-private-data', data)

    def test_unknown_event_fails(self):
        with self.assertRaises(ValueError):
            studio.hook({'hook_event_name':'Notification','cwd':str(self.root)})

    def test_state_symlink_is_rejected_when_available(self):
        outside = self.root / 'outside'; outside.mkdir()
        try:
            (self.root / '.codex').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not allow symlink creation')
        with self.assertRaises(ValueError):
            studio.hook({'hook_event_name':'Stop','cwd':str(self.root)})
        self.assertEqual(list(outside.iterdir()), [])

    def test_install_is_self_contained_and_never_overwrites(self):
        destination = self.root / 'skills/game-studios'
        self.assertFalse(studio.install(destination)['hooks_enabled'])
        self.assertEqual(len(list(destination.rglob('SKILL.md'))), 1)
        self.assertTrue((destination / 'scripts/studio.py').is_file())
        self.assertTrue((destination / 'references/COMPATIBILITY.md').is_file())
        with self.assertRaises(ValueError):
            studio.install(destination)
        result = subprocess.run([sys.executable,str(destination / 'scripts/studio.py'),'verify'],
                                capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_cli_prompt_works_with_unicode_and_spaces(self):
        project = self.root / 'Игра с пробелами'; project.mkdir()
        result = subprocess.run([sys.executable,str(SCRIPT),'prompt','balance-check','--project',str(project),
                                 '--role','economy-designer','--task','Проверь экономику без правок'],
                                capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Проверь экономику без правок', result.stdout)

    def test_cli_bad_hook_payload_fails(self):
        for raw in ('bad json', '[]', '{"hook_event_name":"Notification"}'):
            result = subprocess.run([sys.executable,str(SCRIPT),'hook'],input=raw,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode, 2)

    def test_plugin_manifest_references_real_resources(self):
        plugin = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        self.assertTrue((ROOT / plugin['skills']).is_dir())
        hooks = json.loads((ROOT / plugin['hooks']).read_text())['hooks']
        self.assertEqual(set(hooks), set(studio.EVENTS))
        import re
        matcher = hooks['PreToolUse'][0]['matcher']
        for name in ('Bash', 'exec_command', 'PowerShell', 'apply_patch', 'Read', 'Edit', 'Write'):
            self.assertIsNotNone(re.search(matcher, name), name)
        for groups in hooks.values():
            for group in groups:
                for item in group['hooks']:
                    for key in ('command', 'command_windows'):
                        self.assertIn('${PLUGIN_ROOT}/skills/game-studios/scripts/studio.py', item[key])


if __name__ == '__main__':
    unittest.main()
