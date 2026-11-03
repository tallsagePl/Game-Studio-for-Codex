# Updating Game Studio for Codex

Keep a copy of your current installed skill and any local customizations before
changing versions. Run the new checkout's tests and provenance check first.
Compare the existing and new SKILL.md, runtime helper and compatibility record.

The installer intentionally refuses an existing destination. Move the previous
installation to a backup location outside the active skills directory, then
install the reviewed new copy. Do not keep two discoverable copies of the same
skill under ~/.agents/skills. Start a new Codex session after replacement.

Plugin-hook updates require reviewing/trusting the new definition in the actual
host; a new skill copy alone does not enable or update trusted hooks.

The preserved Claude-specific migration guide is docs/UPSTREAM-UPGRADING.md.
Its commands are not Codex upgrade instructions.
