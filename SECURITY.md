# Security policy — Game Studio for Codex

This policy covers this independent Codex adaptation. Do not send fork-specific
reports to the upstream Claude Code Game Studios maintainers.

When private vulnerability reporting is enabled on this repository, use its
Security → Report a vulnerability action. If unavailable, request a private
reporting channel in a sanitized issue without exploit details or secrets.
No response-time or resolution SLA is promised for this experimental project.

Relevant issues include unintended data reads/writes, unsafe hook behavior,
undisclosed network access, or packaging that changes instructions without
review. Supply the commit, platform, minimum fixture and observed effect.
Use dummy data, not credentials, real user information or private game content.

The optional command guard is heuristic and not a sandbox. Codex permissions
remain authoritative. Review hook definitions before trusting them. The portable
tools make no network/model calls and do not execute the original shell scripts.

For vulnerabilities in Codex itself, use OpenAI's official reporting process;
for Claude Code itself, use Anthropic's. General behavior of an underlying model
is not proven to be a vulnerability in this toolkit.

Preserved upstream policy: docs/UPSTREAM-SECURITY.md.
