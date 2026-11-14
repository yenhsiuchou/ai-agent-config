# AI Agent Config

Shared, tool-neutral preferences and reusable skills for coding agents.

## Contents

- `AGENTS.md`: global working preferences.
- `skills/`: reusable workflows with the Agent Skills `SKILL.md` format.
- `hooks/`: Claude Code hook scripts, such as the confirmation before posting
  a GitHub PR review or comment.
- `claude/settings-hooks.json`: the hook entries that use those scripts.
- `install.sh`: links this repository into Codex and Claude Code.

## Install

Run this command from the repository root:

```sh
./install.sh
```

The installer creates these links:

```text
~/.codex/AGENTS.md                         -> AGENTS.md
~/.claude/CLAUDE.md                        -> AGENTS.md
~/.codex/skills/<skill-name>               -> skills/<skill-name>
~/.claude/skills/<skill-name>              -> skills/<skill-name>
~/.claude/hooks/<hook-script>              -> hooks/<hook-script>
```

It also adds each entry in `claude/settings-hooks.json` to
`~/.claude/settings.json` when no entry with the same command is there, and
leaves the other settings unchanged. Machine-specific settings, such as
permissions, stay out of this repository.

It moves an existing target into `~/.agent-config-backups/<timestamp>/` before
replacing it. It never replaces Codex built-in skills.

## Update

Edit this repository, commit the change, and pull it on each machine. The
links make the updated preferences and skills available the next time either
agent starts a session.
