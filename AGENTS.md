# Game Studio for Codex

This is the toolkit repository, an independent fork of Donchitos/Claude-Code-Game-Studios. Read skills/game-studios/SKILL.md when using the toolkit. The .claude directory preserves upstream source and is not Codex runtime configuration. Do not execute its scripts or inline preprocessing implicitly.

For toolkit changes, keep the pinned upstream library byte-identical and update provenance deliberately. Run `python -m unittest discover -s tests-codex -v` and `python skills/game-studios/scripts/studio.py verify`. Do not confuse catalog/prompt coverage with full behavioral parity. Keep COMPATIBILITY.md honest about unsupported or untested behavior.

Use a focused independent review for substantive changes when delegation is available. Reviewers must inspect evidence and must not modify the files they review. Do not publish personal game data, absolute developer paths, credentials, session state or model transcripts. Preserve upstream MIT attribution and history.
