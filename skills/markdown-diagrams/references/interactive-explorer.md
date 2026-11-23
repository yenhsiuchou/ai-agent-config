# Interactive Explorer

An explorer lets the learner change one choice and watch the outcome, such as
a loop order, a cut choice, or a packet flow. It is embedded inline in the
chapter Markdown and rendered by Markdown Preview Enhanced in the notes
workspace.

## Parts

- **Block:** a `<div data-<name>-explorer aria-label="...">` in the chapter.
  Its content is a static fallback (SVG or PNG) for previews without scripts.
- **Runtime:** one shared script that mounts each block in a Shadow DOM, keeps
  state per block, re-mounts after Markdown Preview Enhanced replaces the
  block (MutationObserver), and does not bind twice when reloaded.
- **Loader:** a small versioned loader in `assets/`, registered in the notes
  workspace's `.crossnote/head.html` with `data-version` set to a hash of the
  runtime. Update the version whenever the runtime changes.

## Content

- Tabs for fixed cases, controls for the choice, and a panel that shows the
  computed result next to the rule's verdict.
- A short "How To Read" section.
- The explorer simulates the rule from the source and says so.

## Verification

Check it in headless Chromium: every case, every control, and a narrow width.
Record the check in the course notes.
