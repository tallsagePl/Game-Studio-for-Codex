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

