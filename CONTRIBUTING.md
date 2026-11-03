# Contributing to Game Studio for Codex

This is an independent Codex adaptation, not the original Claude Code project.
Focus changes on portable tools, runtime translation, documented parity gaps,
reproducible tests and accurate compatibility claims.

- Keep the single skill at skills/game-studios/SKILL.md. Do not reintroduce nested
  SKILL.md files into its reference tree.
- Preserve pinned upstream reference bytes and the MIT notice. Deliberate
  baseline updates must update provenance and show the upstream diff.
- Python tools use the standard library and support Python 3.11+.
- Keep hooks optional and reviewable. Do not add silent network calls, model
  invocations, secret reads or automatic global configuration changes.
- Respect the user's project instructions, engine and existing authorization.
  Do not import mandatory Claude approval rituals into ordinary authorized work.
- Include a regression test for a concrete defect; distinguish fixture coverage
  from a real host, engine or model-driven validation.

Run from the repository root:

```sh
python -m unittest discover -s tests-codex -v
python skills/game-studios/scripts/studio.py verify
```

Update COMPATIBILITY.md and its installable copy at
skills/game-studios/references/COMPATIBILITY.md when behavior changes. Do not
claim parity from a catalog count. New live hook integrations need a real host
loading/trust check and documented supported transports.

Do not contribute private games, generated session records, credentials or
personal machine paths. Report security defects according to SECURITY.md.
Preserved upstream contribution guide: docs/UPSTREAM-CONTRIBUTING.md.
