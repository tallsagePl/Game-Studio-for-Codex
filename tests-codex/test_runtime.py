"""Runtime tests. Live retained Bash execution requires explicit opt-in."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/game-studios/scripts/runtime_bridge.py'
spec=importlib.util.spec_from_file_location('runtime_bridge',SCRIPT)
runtime=importlib.util.module_from_spec(spec); spec.loader.exec_module(runtime)
sys.modules['runtime_bridge']=runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='studio-runtime-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def init(self):
        return runtime.initialize(self.root)

    def test_complete_payload_and_native_profiles(self):
        result=self.init()
        self.assertEqual(result['runtime_files'],434)
        self.assertEqual(result['roles_exported'],49)
        self.assertFalse(runtime.changed_runtime(self.root))
        self.assertEqual(len(list((self.root/'.claude/skills').glob('*/SKILL.md'))),74)
        for file in (self.root/'.codex/agents').glob('*.toml'):
            profile=tomllib.loads(file.read_text(encoding='utf-8'))
            self.assertIn('developer_instructions',profile)
            self.assertNotIn('model',profile)

    def test_existing_game_seeds_never_overwritten(self):
        (self.root/'project.yaml').write_text('existing: true\n')
        self.init()
        self.assertEqual((self.root/'project.yaml').read_text(),'existing: true\n')
        with self.assertRaises(ValueError): self.init()

    def test_existing_claude_configuration_refused(self):
        (self.root/'.claude').mkdir()
        with self.assertRaises(ValueError): self.init()
        self.assertFalse((self.root/'.codex').exists())

    def test_gitignore_symlink_refused_when_supported(self):
        outside=self.root/'outside'; outside.write_text('unchanged')
        try: (self.root/'.gitignore').symlink_to(outside)
        except OSError: self.skipTest('Host does not permit symlink fixture')
        with self.assertRaises(ValueError): self.init()
        self.assertEqual(outside.read_text(),'unchanged')

    def test_modified_runtime_requires_explicit_review(self):
        self.init()
        file=self.root/'.claude/hooks/validate-commit.sh'
        file.write_text('unreviewed fixture')
        self.assertIn('.claude/hooks/validate-commit.sh',runtime.changed_runtime(self.root))
        with self.assertRaises(ValueError): runtime.require_runtime(self.root)

    def test_patch_context_preview_and_post_write(self):
        file=self.root/'example.txt'; file.write_text('one\ntwo\nthree\n')
        patch_text='*** Begin Patch\n*** Update File: example.txt\n@@\n one\n-two\n+changed\n three\n*** End Patch\n'
        self.assertEqual(runtime.planned_files(self.root,patch_text)[0]['tool_input']['content'],'one\nchanged\nthree\n')
        file.write_text('one\nchanged\nthree\n')
        self.assertEqual(runtime.planned_files(self.root,patch_text,post=True)[0]['tool_input']['content'],file.read_text())

    def test_ambiguous_or_escaping_patch_refused(self):
        (self.root/'example.txt').write_text('same\nsame\n')
        with self.assertRaises(ValueError): runtime.planned_files(self.root,'*** Update File: example.txt\n@@\n-same\n+new\n')
        with self.assertRaises(ValueError): runtime.planned_files(self.root,'*** Add File: ../outside\n+bad\n')

    def test_rule_braces_match_engine_paths(self):
        self.init()
        guidance=runtime.matching_rules(self.root,['Assets/Game/UI/Panel.cs'])
        self.assertIn('UI must NEVER own',guidance)

    def test_contract_never_needs_full_host_transcript(self):
        self.init()
        runtime.contract(self.root,'agent/../id','docs/expected.md')
        self.assertEqual(runtime.contract(self.root,'agent/../id')['path'],'docs/expected.md')
        with self.assertRaises(ValueError): runtime.contract(self.root,'agent','../outside')

    def test_pretool_native_denial_preserved(self):
        self.init()
        failed=subprocess.CompletedProcess([],2,stdout='',stderr='fixture commit gate failed')
        with patch.object(runtime,'execute',return_value=failed):
            result=runtime.event(self.root,{'hook_event_name':'PreToolUse','tool_name':'exec_command','tool_input':{'cmd':'git commit -m fixture'}})
        self.assertEqual(result['hookSpecificOutput']['permissionDecision'],'deny')

    def test_foreign_root_override_refused_before_execution(self):
        self.init()
        with self.assertRaises(ValueError):
            runtime.execute(self.root,'.claude/scripts/session-state.sh',['checkpoint','--root',str(self.root.parent)])

    def test_preserved_permissions_translated(self):
        self.init()
        result=runtime.event(self.root,{'hook_event_name':'PreToolUse','tool_name':'exec_command','tool_input':{'cmd':'git reset --hard HEAD'}})
        self.assertEqual(result['hookSpecificOutput']['permissionDecision'],'deny')

    def test_session_output_is_valid_native_context(self):
        self.init()
        passed=subprocess.CompletedProcess([],0,stdout='fixture recovery context',stderr='')
        with patch.object(runtime,'execute',return_value=passed):
            result=runtime.event(self.root,{'hook_event_name':'SessionStart','source':'compact'})
        self.assertIn('fixture recovery context',result['hookSpecificOutput']['additionalContext'])

    def test_preprocessing_is_allowlisted_not_shell_evaluation(self):
        self.init()
        passed=subprocess.CompletedProcess([],0,stdout='workflow: full\n',stderr='')
        with patch.object(runtime,'execute',return_value=passed):
            output=runtime.preprocess(self.root,'help','!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys workflow`')
        self.assertEqual(output,'workflow: full')
        with self.assertRaises(ValueError): runtime.preprocess(self.root,'help','!`unmapped-command --fixture`')

    def test_runtime_init_cli_argument_order(self):
        helper=ROOT/'skills/game-studios/scripts/studio.py'
        result=subprocess.run([sys.executable,str(helper),'runtime-init','--project',str(self.root)],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['initialized'])

    @unittest.skipUnless(os.environ.get('CODEX_STUDIO_RUNTIME_TESTS')=='1','Retained Bash integration is opt-in')
    def test_real_configuration_and_checkpoint_roundtrip(self):
        self.init()
        result=runtime.execute(self.root,'.claude/scripts/config-set.sh',['modes.rigor','full'])
        self.assertEqual(result.returncode,0,result.stderr)
        result=runtime.execute(self.root,'.claude/hooks/yaml-helper.sh',['resolve_config','--keys','workflow,review_mode,qa.level'])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('full',result.stdout)
        result=runtime.execute(self.root,'.claude/scripts/session-state.sh',['checkpoint'],input_text='- Task: fixture roundtrip\n')
        self.assertEqual(result.returncode,0,result.stderr)
        result=runtime.execute(self.root,'.claude/scripts/session-state.sh',['show'])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('fixture roundtrip',result.stdout)


if __name__=='__main__': unittest.main()
