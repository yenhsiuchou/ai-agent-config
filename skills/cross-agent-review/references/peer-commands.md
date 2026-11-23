# Peer Commands

Render the prompt to `<run-dir>/prompt-<step>.md` with
`scripts/render_prompt.py` (see `SKILL.md`), then pass it on stdin.
`<workdir>` is the review working directory from `target.md` (the repository
or the run's detached worktree). Reviews can take tens of minutes; run the
command in the background when the harness supports it, otherwise use a long
timeout.

## Claude Code orchestrator → Codex peer

```bash
python3 <cross-agent-review-dir>/scripts/run_codex.py \
  --prompt <run-dir>/prompt-<step>.md --output <run-dir>/<output>.md \
  --log <run-dir>/<output>.log -- \
  -C <workdir> -s read-only --add-dir <run-dir> [-c model_reasoning_effort=<level>]
```

- The script runs `codex exec <arguments> -o <output> -` with the prompt on
  stdin. `-o` saves Codex's final message, which is the deliverable.
- **Stall watchdog.** `codex exec` writes the log after each command and model
  response. When the log does not grow for 8 minutes, the script kills the
  call with its child processes and starts it again once. A normal gap is
  under 2 minutes; one stalled request has taken 20. Exit status 124 means
  every attempt stalled: report it as a peer failure.
- `-s read-only` lets Codex read files and run read-only commands such as
  `git diff`; it cannot edit the tree.
- `-c model_reasoning_effort=<level>` overrides the effort in
  `~/.codex/config.toml` for one call, when the calling skill asks for it.
- Codex loads the shared skills from `~/.codex/skills` and the repository's
  `.agents/skills`.

## Codex orchestrator → Claude Code peer

```bash
cd <workdir> && claude -p --permission-mode dontAsk \
  --allowedTools "Read Grep Glob Skill Agent Bash(git diff:*) Bash(git log:*) Bash(git show:*) Bash(git rev-parse:*) Bash(git merge-base:*) Bash(gh pr view:*) Bash(gh pr diff:*)" \
  --add-dir <run-dir> --output-format text \
  < <run-dir>/prompt-<step>.md > <run-dir>/<output>.md 2> <run-dir>/<output>.log
```

- `dontAsk` denies every tool outside `--allowedTools`, so the peer stays
  read-only without prompting.
- `--add-dir` lets the peer read the run directory.
- `claude -p` refuses to start inside a Claude Code session (`CLAUDECODE` is
  set). When it is set, the orchestrator is Claude and the peer is Codex.

## Failure checks

After each call, check the exit status and that the output file is non-empty.
On failure, read the `.log` file and report it. Common causes are a missing
CLI, expired login (`codex login` or `claude` login), and sandbox denials.
