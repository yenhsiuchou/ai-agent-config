# Work Hub invariants

Each rule names what breaks when a change violates it. The reviewer checks the
diff against every rule that the changed files touch.

## Server and state

1. **The server is a `ThreadingHTTPServer`.** Two requests, or a request and a
   background watcher thread, run at once. State that more than one thread
   reads and writes (a dict in memory, a JSON file under `data/`) changes only
   while holding that module's lock. A read-modify-write of a state file holds
   the lock across the read and the write. Breaks: lost updates, half-written
   JSON that the next start cannot parse.
2. **A new state file is written atomically**: write a temporary file in the
   same directory, then `os.replace`. Breaks: a crash or sleep mid-write leaves
   a truncated file. Older writers that use `write_text` directly are existing
   debt; flag them only when the diff touches them.
3. **The server binds `127.0.0.1` and checks the `Host` header** against its
   allow list; a POST also needs the `X-PR-Triage: 1` header, which a page on
   another site cannot send. A new endpoint goes through the same handler and
   the same checks; nothing listens on another interface. An endpoint that
   runs a command or opens a file takes only values from a fixed set or a path
   checked to be under an allowed root.
4. **A long call (`gh`, `claude -p`, `git`, a build) never runs on the request
   thread** unless the endpoint is documented as slow. It runs as a background
   job whose state the page polls, and the job survives a page reload.
5. **A missing or unreadable state file degrades, never crashes**: the page
   shows the error or an empty state.

## Python modules and the running server

6. **The running server keeps the old modules in memory.** A change to
   `server.py`, `projects.py`, `triage.py`, or any module the server imports
   needs a server restart before it is verified. Before restarting, check that
   `data/prepare_jobs.json` has no running job. After restarting, call the
   changed API with `curl localhost:8765/api/...` and check the response.
7. **The project-file parser and its readers change together.** A new key in
   a `*.project.yaml` file needs the parser (`projects.py`), the `check`
   command, and the page code that shows it in the same change. Breaks: the
   parser rejects the key as unknown, or the page silently ignores it.
8. **Each module runs both from the command line and from the server.** A
   change to a module's functions keeps its CLI subcommands working.

## Page (`index.html`)

9. **New UI follows the dashboard style**: a row of KPI tiles, then charts,
   cards, and chips; explanations go in a hover tooltip, not on the page. Reuse
   the `.tile` class and the `--s1..--s4` palette. UI text is English.
10. **The page builds DOM with the `el()` helper and `textContent`**, never
    `innerHTML`, so a value from the server or from GitHub (PR title, branch
    name, file name, session title) is never parsed as HTML. A new `innerHTML`,
    `outerHTML`, or `insertAdjacentHTML` with such a value is a bug.
11. **A button that starts something shows its running state** and cannot
    start a second copy by a double click.

## Paths and private content

12. **No new hard-coded personal path or employer name.** A path comes from an
    env var or the local config, with `~` expanded at use. New code does not
    add a repository name, colleague name, or real PR number to source,
    comments, or UI text.

## VS Code extension

13. **A change to `vscode-extension/extension.js` or `package.json` needs a
    rebuild and reinstall** (`build_vsix.py`, then `code --install-extension`)
    before it is verified. A new setting in `package.json` has a default that
    works when the setting is empty.
