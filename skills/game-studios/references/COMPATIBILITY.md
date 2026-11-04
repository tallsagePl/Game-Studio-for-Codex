# v0.2 runtime implementation and validation status

The remaining executable source is now bundled and connected through a Codex
transport, rather than replaced with approximate reimplementations. All 434
upstream .claude files plus 135 seed/spec files are available via explicit
runtime-init. This changes implementation coverage; it does not establish parity.

- Settings/rigor/legacy precedence: retained YAML resolver and config-set helper.
- Checks: all 15 original handlers routed through preserved event declarations;
  native patches and reads normalized, original deny patterns translated.
- Session recovery/audit: original session/compact/stop helpers and checkpoints.
- Roles/memory: 49 project-scoped native profiles and project memory paths.
- Original helper commands and behavioral specs: packaged for explicit use.
- Updates/status: explicit wrapper commands; updates require allow-network.
- Notifications: PermissionRequest maps to original Notification; Windows helper
  retained, textual fallback elsewhere. This is a platform adaptation.

Read RUNTIME.md for prerequisites, initialization and helper argument delimiters.
Native delivery/trust, engine behavior and the full original spec suite remain
validation work. Unknown transcript parsing is replaced by explicit artifact
contracts. Ambiguous native patch previews refuse the operation. Model choices
remain the user's Codex selection. No automatic Codex-owned status bar is claimed.

The v0.1 catalog/fixture results below do not prove the new runtime path. The
prior gap assessment is preserved in docs/COMPATIBILITY-v0.1.md for provenance.
TESTING.md records new actual results separately; TEST-PLAN.md defines remaining
host and engine checks. Full behavioral parity remains unestablished.

