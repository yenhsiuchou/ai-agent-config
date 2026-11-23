# AI Agent Config

Shared, tool-neutral preferences and reusable skills for coding agents.

## Contents

- `AGENTS.md`: global working preferences.
- `skills/`: reusable workflows with the Agent Skills `SKILL.md` format.
- `hooks/`: Claude Code hook scripts: the confirmation before posting a
  GitHub PR review or comment, and the `[<PR number>]` prefix on the title of
  a session that reviews a PR.
- `claude/settings-hooks.json`: the hook entries that use those scripts.
- `install.sh`: links this repository into Codex and Claude Code.
- `scripts/check-public-content.py` and `githooks/`: the pre-commit and
  pre-push checks that keep private and employer content out of this public
  repository.

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

## Public Content Check

This repository is public. `install.sh` points this clone's `core.hooksPath`
at `githooks/`, so every commit and push runs
`scripts/check-public-content.py`. It rejects:

- absolute home paths, credential formats, PR numbers, and long commit hashes;
- email addresses, in content or as author or committer, other than the ones
  the local config allows;
- each `deny <regex>` in `~/.agent-config-local/public-content.txt`.

The deny list stays outside the repository because the words in it are
private. The check fails when that file is missing. To audit what is already
published, run:

```sh
python3 scripts/check-public-content.py --tree      # files at HEAD
python3 scripts/check-public-content.py --history   # every version in all refs
```

Project-specific review context, which skills read when it exists, lives in
`~/.agent-config-local/review-context/<repository directory name>/`.

## Update

Edit this repository, commit the change, and pull it on each machine. The
links make the updated preferences and skills available the next time either
agent starts a session.
