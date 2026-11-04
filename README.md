# Game Studio for Codex

**Turn Codex into your indie game studio.** Bring in a designer, gameplay programmer, balance analyst, or QA lead when the task calls for one. Start with **49 specialist roles and 74 workflows** for Unity, Godot, and Unreal, from your first mechanic to release review.

An independent MIT-licensed adaptation of [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios), originally built for Claude Code. Source history and attribution are preserved. Not affiliated with or endorsed by Donchitos, OpenAI or Anthropic.

> **Experimental port, v0.2.0. Full behavioral parity is not established.** The complete role/workflow library is available as instructions; the pinned execution/configuration/hook engine is now available through explicit runtime initialization, with platform adaptations that still need integration validation. See [COMPATIBILITY.md](COMPATIBILITY.md). Catalog tests are not 74 successful end-to-end game tasks.

## Included

- 49 selectable roles for design, Unity/Godot/Unreal, programming, art, audio, narrative, economy, QA and production.
- 74 workflows from concept through implementation, balance analysis, testing and release review.
- 14 rule documents, templates and all 379 upstream reference files, with SHA256 provenance.
- A self-contained Codex skill and portable tools for preparing prompts, observing a project and checking promised artifacts.
- Optional native Codex hooks for context, limited metadata records and bounded command/path guards. These are not the full original hook suite.

The model develops the game using actual Codex tools. The reference-mode utility does not call models, build a game or launch agents. Explicit initialized-runtime helpers can invoke the existing engine/test commands for the selected project. No Claude Code, API keys, network services or third-party Python packages are required for the portable tools.

If this helps you ship your game, give the repo a star so other solo developers can find it.

## Install

Requirements: Python 3.11+ and Codex with skill support. From the repository root:

```sh
python skills/game-studios/scripts/studio.py verify
python skills/game-studios/scripts/studio.py install
```

Default destination: `~/.agents/skills/game-studios`. Existing installations are never overwritten. For a staging copy, add `--dest /path/to/staging/game-studios`. Start a new Codex chat in your **game project**, then ask:

> Use $game-studios to review the construction economy. Find the real rules and data first. Do not edit files yet.

Or ask it to implement a concrete agreed mechanic with the smallest useful team and appropriate validation. It respects the game's existing instructions and engine. Names like `balance-check` select procedures; they are not separately registered native slash commands. Delegation requires an available Codex subagent mechanism.

## Tools

```sh
python skills/game-studios/scripts/studio.py list workflows
python skills/game-studios/scripts/studio.py list roles
python skills/game-studios/scripts/studio.py doctor --project /path/to/game
python skills/game-studios/scripts/studio.py prompt balance-check --role economy-designer --project /path/to/game --task "Read-only economy review"
python skills/game-studios/scripts/studio.py artifact --project /path/to/game --path docs/review.md
```

Quote paths with spaces on Windows. Tools use UTF-8. `doctor` returns observations, not proof of a configured or tested game. Missing inputs remain missing, not passing.

## Optional hooks

The Codex plugin manifest is `.codex-plugin/plugin.json`; hook definitions are in `hooks/hooks.json`. Plugin-capable installations require support, review and trust of the hook definition. Plain skill installation does **not** enable hooks or change Codex settings. Live host loading/trust is unverified in this release.

The guard catches tested destructive-command forms, secret paths and out-of-root patches. It is heuristic, not a shell parser or sandbox. Actual runtime permissions remain authoritative. Event records contain names/timestamps only in `.codex/studio-state/`; exclude that directory from game source control. No prompts, tool arguments or transcripts are retained.

## Validation

```sh
python -m unittest discover -s tests-codex -v
python skills/game-studios/scripts/studio.py verify
```

All 74 prompt routes, 49 role handoffs, provenance, installation and fixture-based handler behavior are checked. CI is configured for Windows/Linux and Python 3.11/3.13; configured jobs are not evidence that remote CI passed. [TESTING.md](TESTING.md) records actual checks and limits.

## Upstream and changes

Baseline: `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418`, framework 1.2.0. Original `.claude/` source and [upstream README](docs/UPSTREAM-README.md) remain for comparison, not as active Codex configuration. In the installable library, `SKILL.md` filenames become `WORKFLOW.md` so only one skill is discoverable. Reference contents are byte-identical and mapped in `references/provenance.json`.

This fork adds Codex translation, portable tools, native handler subsets and adaptation tests. Original workflow/template design belongs to upstream contributors. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).

## По-русски

Перенос процедур игровой студии из Claude Code в Codex: роли, игровые процессы, шаблоны и инструменты проверки. Работает с выбранным проектом и действующими правилами команды. Claude Code не нужен; все роли одновременно не запускаются.

Это экспериментальная версия. Библиотека перенесена полностью, но не все механизмы оригинала реализованы и проверены. Наличие 74 инструкций не доказывает работу всех процессов; конкретные отличия перечислены в COMPATIBILITY.md.

## Retained runtime mode (v0.2)

The remaining source mechanisms are packaged: complete settings resolver, helper scripts, original 15 hook handlers, checkpoint recovery, agent memory and behavioral specs. Read [RUNTIME.md](RUNTIME.md) before initialization. The runtime needs Bash (Git Bash on Windows) and Python; reference-only tools remain Python-only. runtime-init exports 49 native Codex role profiles and refuses existing .claude data. It does not select models or trust hooks automatically. Automatic update checks are disabled; explicit update checks require --allow-network. Version 0.1 fixture results do not validate this new engine path. See [TEST-PLAN.md](TEST-PLAN.md) for remaining integration checks.


