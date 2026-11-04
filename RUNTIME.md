# Retained runtime and Codex transport — v0.2

The remaining executable mechanisms are packaged from the pinned upstream Git
objects, not rewritten as approximate Python copies. The runtime manifest maps
569 files (434 required .claude files plus project/spec seeds) to their original
hashes. Only project initialization reconstructs the Claude-shaped file layout;
that layout is a compatibility ABI for the retained helpers, not a Claude model.

## Initialize explicitly

```sh
python skills/game-studios/scripts/studio.py runtime-init --project /path/to/game
```

This creates .claude runtime files, project-scoped .codex/agents profiles for all
49 roles and a local runtime lock. Existing game seed files are not overwritten.
Existing .claude data is refused: use a separate worktree or review a manual
integration. No existing global Codex settings are changed, no models are
selected, and plugin hooks are not automatically trusted. Initialization writes
upstream CLAUDE.md only if absent; Codex instructions remain authoritative.

Keep a game backup/worktree before trying the runtime for the first time.
On Windows the retained engine needs Git Bash and Python; jq is recommended,
with the original documented fallbacks. Set CODEX_STUDIO_BASH if Bash lives at
a nonstandard path. The reference-only utilities still need only Python.

## Settings and helpers

The delimiter `--` is required before retained helper arguments. Wrapper options
go before it, so helper flags cannot be swallowed by the wrapper.

```sh
python skills/game-studios/scripts/studio.py config --project /path/to/game -- --keys workflow,review_mode,qa.level
python skills/game-studios/scripts/studio.py helper --project /path/to/game -- config-set modes.rigor full --dry-run
python skills/game-studios/scripts/studio.py helper --project /path/to/game -- config-set modes.rigor full
python skills/game-studios/scripts/studio.py helper --project /path/to/game -- project-state
python skills/game-studios/scripts/studio.py checkpoint --project /path/to/game -- show
python skills/game-studios/scripts/studio.py status --project /path/to/game --model actual-session-model
```

`checkpoint --project ROOT -- checkpoint` reads checkpoint text on stdin.
Settings use the original resolver: local/base/legacy values, rigor expansion,
system overrides, enum validation and effects-map semantics remain in the pinned
engine. Named helpers expose the remaining source scripts without shell eval.
Foreign --root overrides are refused. Tools that build/test a game remain real
side effects and should be invoked only when authorized for that task.

## Session, memory and return contracts

Native session/compact/stop events invoke the corresponding retained hooks.
The original active checkpoint and session logs are available at
production/session-state and production/session-logs. The coordinator must write
useful checkpoints; the runtime does not invent a summary of unseen work.

```sh
python skills/game-studios/scripts/studio.py memory --project ROOT --role economy-designer
python skills/game-studios/scripts/studio.py memory --project ROOT --role economy-designer --text "Reviewed project facts"
python skills/game-studios/scripts/studio.py contract --project ROOT --agent-id ACTUAL_ID --path docs/review.md
```

Register actual spawned agent IDs and promised artifact paths. The bridge turns
that contract into a minimal local transcript for the original artifact guard.
It does not parse/copy the full, unstable Codex transcript. Without a registered
contract it explicitly reports that artifact acceptance needs coordinator review.
Native role profiles inherit the user's model and include project memory paths.

## Automatic checks

After runtime initialization and plugin trust, the bridge routes native events
to the original handlers: session loading/gaps, commit/push checks, registry and
write/read guards, asset/skill checks, compact/stop and agent lifecycle. Native
apply_patch operations are previewed conservatively before writes and inspected
from disk after writes. Ambiguous preview contexts are refused, not silently
validated. Applicable original path rules are added as native tool context.

PermissionRequest and Stop supply permission/idle notification triggers; explicit native Notification
events do not exist in this integration. The original Windows notification helper
is retained; other platforms may only show its textual notification. Status is
available explicitly, not installed as a Codex-owned UI status bar.

Network update checking is off during automatic events through the original
helper's CI guard. To request it explicitly:

```sh
python skills/game-studios/scripts/studio.py updates --project ROOT --allow-network -- refresh
```

Pinned script modifications are refused until reviewed. `runtime-trust --project
ROOT` lists changed runtime files; `--accept` rebaselines them after deliberate
review. This is needed after authorized customization/skill improvement. Never
rebaseline unknown changes merely to silence a warning.

## Validation status

Implementation coverage is not proof of parity. Source/specs and test cases are
prepared; real host event delivery, Bash/platform behavior, path-rule semantics,
agent contracts and engine workflows need the planned integration checks.
See TEST-PLAN.md and TESTING.md for actual execution evidence.

