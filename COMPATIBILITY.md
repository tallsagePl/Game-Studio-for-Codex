# Compatibility and parity

Version 0.1.0 preserves the complete role/workflow reference library.
**Full behavioral parity with Claude Code is not established.**

## Available and checked

- All 49 role profiles can be prepared as handoff instructions; Claude model
  declarations are not applied to Codex.
- All 74 workflows can be prepared without executing Claude inline shell
  preprocessing. This is prompt coverage, not end-to-end behavioral validation.
- All 379 reference files and 14 rule documents have matching provenance hashes.
  The templates directory contains 71 files, including supporting guidance.
- Self-contained skill installation has one discoverable entrypoint and refuses
  to overwrite existing files. It does not mutate global Codex configuration.
- Engine markers, project documents and source roots are observed; no engine is
  invented for an empty directory. Unicode paths and artifact checks are tested.

## Adapted runtime behavior

Read/Glob/Grep/Write/Edit use available Codex tools; questions use available
question mechanisms and existing user authorization. Task/Agent/TeamCreate use
actual Codex subagents when available. Profiles are not permanently registered
agents; sequential role passes are not independent reviews. Workflow names are
natural-language selectors, not 74 native slash commands. Applicable rules must
be read by the coordinator; identical automatic path activation is not provided.
Codex permissions remain authoritative; Claude allow/deny patterns are not copied.

## Original hook-by-hook status

- `session-start.sh`: partial — project observations; original recovery and full
  settings resolution differ.
- `detect-gaps.sh`: not ported; requires explicit workflow review.
- `validate-commit.sh`: not ported; destructive-command guards do not validate
  original commit registries or evidence contracts.
- `validate-push.sh`: partial — tested force-push patterns blocked; full original
  project preflight not ported.
- `validate-registry.sh`: not ported.
- `validate-write.sh`: partial — secret/out-of-root paths guarded; original
  prototype, design and localization semantics differ.
- `validate-read.sh`: not ported.
- `validate-assets.sh`: not ported; PostToolUse metadata is not asset validation.
- `validate-skill-change.sh`: not ported as a hook; explicit verify/tests exist.
- `notify.sh`: not ported; Notification is not supported by this handler.
- `pre-compact.sh`: partial — checkpoint reminder/event, not recovery synthesis.
- `session-stop.sh`: partial — metadata, not the original session log.
- `log-agent.sh`: partial — metadata only, not a prompt audit trail.
- `log-agent-stop.sh`: partial — reminder, not full original lifecycle logging.
- `validate-agent-artifact.sh`: partial — reminder and explicit artifact command;
  automatic transcript contract parsing is not provided.

Original status line, automatic update checking, per-agent memory, complete YAML
settings precedence/rigor effects, helper runtime and upstream behavioral-spec
execution are not implemented in the portable package. They remain preserved
in .claude/ for comparison; preservation does not make them Codex features.

## Native hook verification

The optional plugin defines seven current Codex event types. Handler behavior is
tested with JSON fixtures. Live plugin loading/trust and every tool transport
are not validated here. Host support and trusted definitions are prerequisites.
Guards are heuristic, not a command parser or sandbox.

Full parity requires implementing these gaps, comparing original behavioral
specs on both runtimes, verifying live events and testing representative tasks
in each engine. Catalog checks do not satisfy those requirements.

Sources: [Codex hooks](https://learn.chatgpt.com/docs/hooks),
[plugin packaging](https://developers.openai.com/plugins/build/plugins),
[skills](https://learn.chatgpt.com/docs/build-skills),
[upstream](https://github.com/Donchitos/Claude-Code-Game-Studios).
