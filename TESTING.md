# Validation record — 2026-11-03

Platform: Windows, Python 3.13.1. No paid model calls, Claude, game engine or
upstream-controlled executable scripts were run by the adaptation tests.

```sh
python -m unittest discover -s tests-codex -v
python skills/game-studios/scripts/studio.py verify
```

Result after review fixes: 20 unittest cases, 19 passed and one skipped because this host
does not allow the directory-symlink fixture. It is unverified locally, not a
pass. Parameterized loops prepared all 74 workflows and 49 role handoffs.
Provenance checked 379 reference files against the preserved originals. The
install test ran the installed helper in a disposable project directory.

Fixtures cover engine detection, absent artifacts, path traversal, tested
destructive commands, secret paths, seven handler events, limited metadata
retention, malformed payloads and Unicode paths.

CI is configured for Windows/Linux and Python 3.11/3.13. Remote results must be
checked after publication; configuration is not execution evidence.

No full parity claim: original hook behaviors, all configuration effects, live
plugin loading/trust and game-development outcomes are not covered.
See COMPATIBILITY.md for the concrete gaps.


Fresh-checkout verification: a separate local clone with core.autocrlf=true
passed verify and the same 20 cases (19 passed, one symlink skip).
Independent review identified and rechecked transport, packaging, attribution
and line-ending corrections. Full parity remains unestablished.


## v0.2 retained runtime — 2026-11-04

Windows / Python 3.13.1. The 36-case full suite passed 33 cases and skipped
three (two symlink fixtures unsupported on this host, and the opt-in retained
Bash roundtrip). The 16-case runtime subset then ran with
CODEX_STUDIO_RUNTIME_TESTS=1: 15 passed, one symlink skip. That second run verified
actual upstream rigor resolution and checkpoint write/read using Git Bash.
Across the two runs, 34 distinct cases passed; two symlink cases remain skipped.
The verification command matched 379 original references and 569 runtime/seed
payload files. Fixture tests exercised all 49 generated native role definitions,
patch normalization, permission checks, native event responses and contracts.

Live plugin trust, real Codex event delivery and the complete original
behavioral suite remain unverified. No marketplace/public push or game-project
runtime activation was performed by these checks.

Final integrated run after choosing the reviewed project-local workflow body: 
36 cases, 34 passed, 2 symlink cases skipped, including the real Bash roundtrip.

