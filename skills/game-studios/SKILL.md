---
name: game-studios
description: Apply Game Studio for Codex roles and workflows to game design, engine development, balance, production, QA and release tasks in a confirmed game project.
---

# Game Studio for Codex

An independent Codex adaptation of Donchitos/Claude-Code-Game-Studios. Use the whole workflow library selectively; do not launch every role. This is an experimental port, not a guarantee of Claude runtime equivalence.

## Establish the project

Use the user's current project root. Read its AGENTS.md and existing concept, progress and team instructions. Do not assume the toolkit checkout is the game. Existing project requirements and current user decisions override template defaults. Preserve the chosen engine, source layout, save contracts and test commands. No hardcoded developer paths, game names or model choices are required.

The portable helper is `scripts/studio.py` relative to this skill. Python 3.11+ is sufficient; no API keys, third-party packages or Claude installation are needed. Helpers return observations or prepare prompts. They never call a model or execute a generated plan themselves.

## Select and run a procedure

1. Identify the smallest useful workflow. `python <skill>/scripts/studio.py list workflows` lists all 74; `list roles` lists all 49 role profiles. All upstream entrypoints are stored as WORKFLOW.md to prevent recursive skill discovery.
2. Read `references/upstream/skills/<workflow>/WORKFLOW.md` and necessary references only. Start/help/project-stage-detect suit orientation; brainstorm/quick-design/design-system suit mechanics; dev-story/vertical-slice suit implementation; balance-check suits economy; ux-design/ux-review suit UI; qa-plan/smoke-check/story-done suit verification. Team-* workflows define coordinated role tasks.
3. Read the matching role under `references/upstream/agents/`. A helper can prepare both: `python <skill>/scripts/studio.py prompt balance-check --role economy-designer --project <root> --task "Review construction economy without edits"`.
4. Interpret the resulting procedure using Codex tools. For delegated work, pass the chosen role, concrete task, owned paths and expected evidence to the available subagent mechanism. Respect live concurrency limits and one writer per file. If unavailable, label sequential role passes; never call them independent reviews.
5. Perform authorized work, proportionate validation and real result review. Missing data means NOT ASSESSED, not success. Human fun, accessibility in use and market demand require appropriate human evidence. Visible game changes need actual runtime inspection or an explicit unverified limitation.

## Runtime translation

Claude `model`, `allowed-tools`, `context`, `memory` and `maxTurns` frontmatter is reference metadata, not Codex configuration. Keep the user's selected Codex model. Read/Glob/Grep map to available file tools; Write/Edit to authorized edits; AskUserQuestion to available questions; Task/Agent/TeamCreate to actual Codex delegation. Native Claude slash commands are not registered by this single-skill package: use `$game-studios` and natural-language workflow names.

Do not execute upstream inline `!` shell expansions. The helper removes them from compiled prompts. Upstream .claude paths refer to reference resources, not a directory to create automatically in a game. Resolve SKILL.md references to WORKFLOW.md, document/template paths to `references/upstream`, and game paths to the actual project. Locate real data, code and tests before applying Godot-style src/assets defaults to Unity or Unreal.

Do not invent results for omitted upstream scripts or configuration. `doctor --project <root>` observes known engine markers and project documents; it does not implement every project.yaml resolver. Original helpers remain available only in the fork checkout's .claude directory and are not executed by the portable package.

## Rules, checks and session continuity

Read relevant path-scoped guidance in `references/upstream/rules/` before editing corresponding gameplay, UI, networking, data or engine files. Templates are in `references/upstream/docs/templates/`. Prefer existing task/backlog formats over parallel production bureaucracy.

Small clear tasks can proceed directly. Significant behavior benefits from fresh review and affected tests. Before committing or delivering, check actual diff, requirements, test/build results and retained evidence. No agent can claim independent acceptance of its own implementation.

The optional Codex plugin supplies native session context, bounded local event records, a limited destructive-command/secret-path guard, patch-path checks and subagent lifecycle reminders. Hooks require runtime support and user trust; installing this skill alone does not enable them. They are guardrails, not a sandbox, and are not equivalent to all 15 upstream hooks. Read references/COMPATIBILITY.md before claiming feature parity. In skill-only mode, perform the relevant checks explicitly.

Use `artifact --project <root> --path <relative-path>` to verify a promised file exists without reading its content. Use `verify` for catalog/provenance integrity. Preserve user authorization; do not add approval rituals copied from upstream prose for already authorized ordinary edits. Concept changes, release decisions and publication follow actual user instructions.

## Provenance and limits

Upstream: https://github.com/Donchitos/Claude-Code-Game-Studios at commit 05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418. The MIT notice is retained in references/upstream/LICENSE. Original reference bytes are preserved; only SKILL.md filenames become WORKFLOW.md. references/provenance.json records the mapping and hashes.

All workflows and roles are available as adapted instructions; catalog completeness is not proof that every workflow has produced a correct game result. Never turn a structural check into a full behavioral parity claim.
