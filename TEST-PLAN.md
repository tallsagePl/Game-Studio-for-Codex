# v0.2 test plan

1. Run Python unit/fixture suite, including initialization, 49 native TOML roles,
   existing-file protection, path confinement, patch preview/post-write behavior,
   settings transport, contracts and native hook output conversion.
2. In a disposable game fixture, opt into retained Bash integration using
   CODEX_STUDIO_RUNTIME_TESTS=1. Check rigor resolution and checkpoint roundtrip;
   compare retained hook/spec behavior rather than treating a mock as execution.
3. In a dedicated worktree, initialize runtime, review/trust plugin hooks and
   capture real events: startup/resume/compact, commit/push, file edits/reads,
   asset failures, agent start/stop/contracts, permission notification and stop.
4. Run original studio-tests behavioral specs with actual Codex tasks and retain
   real outcomes. Check missing inputs, independent reviews and engine-specific
   setup. Do not automatically claim that all 74 tasks pass.
5. Test the user's game separately: Unity EditMode, build/shader gates and bounded
   runtime scenarios. Preserve saves; keep source/test logs tied to actual HEAD.

Use normal sandboxed scratch fixtures for source/runtime comparisons. These
checks must not read credentials, publish code or run paid models implicitly.
The user originally requested preparation only, then explicitly authorized game
testing; record each actual run and any remaining unverified platform behavior.
