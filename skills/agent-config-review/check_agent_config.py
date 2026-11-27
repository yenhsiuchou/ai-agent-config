#!/usr/bin/env python3
"""Report the mechanical inconsistencies among agent rules, memory, skills, and hooks.

The sources come from `~/.agent-config-local/agent-config-review.json`:

    {
      "editable": {"<kind>": ["<path or glob>", ...], ...},
      "read_only": {"<kind>": ["<path or glob>", ...], ...}
    }

Kinds that the checks read: `memory` (memory directories), `skills` (skill
roots holding `<name>/SKILL.md`), `hooks` (hook script directories),
`hook_settings` (JSON files with a `hooks` key), and `rules` (rule files or
directories of `.md` files). A kind under `read_only` is read for reference and
never reported as something to fix.

Each finding prints as one JSON line with `check`, `path`, `detail`, and
`editable`. `--only PATH...` keeps the findings whose path is under one of the
given paths. The exit status is 0; the caller decides what to fix.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from pathlib import Path

CONFIG = Path("~/.agent-config-local/agent-config-review.json").expanduser()
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
INDEX_LINK = re.compile(r"^- \[[^\]]*\]\(([^)]+\.md)\)", re.M)
WIKI_LINK = re.compile(r"\[\[([a-z0-9][a-z0-9-]*)\]\]")
HOOK_SCRIPT = re.compile(r"((?:~|\$HOME|\$\{HOME\}|" + re.escape(str(Path.home())) + r")/\.claude/hooks/[\w.-]+)")
SKILL_REFERENCE = re.compile(r"`/?([a-z0-9][a-z0-9:-]*[a-z0-9])`\s+skill|skill\s+`/?([a-z0-9][a-z0-9:-]*[a-z0-9])`")
PLUGIN_SKILLS = "~/.claude/plugins/**/skills/*/SKILL.md"


def expand(patterns: list[str]) -> list[Path]:
    paths = []
    for pattern in patterns:
        matches = glob.glob(str(Path(pattern).expanduser()))
        paths += [Path(m) for m in sorted(matches)]
    return paths


def read(path: Path, editable: bool, report: "Report") -> str | None:
    try:
        return path.read_text(errors="replace")
    except OSError as error:
        report.add("file-unreadable", path, str(error), editable)
        return None


def frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


class Report:
    def __init__(self) -> None:
        self.findings: list[dict] = []

    def add(self, check: str, path: Path, detail: str, editable: bool) -> None:
        self.findings.append({"check": check, "path": str(path), "detail": detail, "editable": editable})


def check_memory(directory: Path, editable: bool, report: Report) -> None:
    files = {p.name: p for p in directory.glob("*.md") if p.name != "MEMORY.md"}
    names = {}
    texts = {name: read(path, editable, report) for name, path in files.items()}
    for name, path in files.items():
        if texts[name] is None:
            continue
        fields = frontmatter(texts[name])
        if not fields.get("name") or not fields.get("description"):
            report.add("memory-frontmatter", path, "missing name or description", editable)
        names[fields.get("name") or path.stem] = path
    index_path = directory / "MEMORY.md"
    if not files and not index_path.exists():
        return
    index = (read(index_path, editable, report) or "") if index_path.exists() else ""
    listed = set(INDEX_LINK.findall(index))
    for target in sorted(listed - set(files)):
        report.add("memory-index-dangling", index_path, f"index lists {target}, which does not exist", editable)
    for name in sorted(set(files) - listed):
        report.add("memory-index-missing", files[name], "file has no line in MEMORY.md", editable)
    for name, path in files.items():
        for target in WIKI_LINK.findall(texts[name] or ""):
            if target not in names:
                report.add("memory-link-unresolved", path, f"[[{target}]] names no memory; a rename or delete may have left it", editable)


def skill_names(roots: list[Path]) -> set[str]:
    names = set()
    for root in roots:
        names |= {p.parent.name for p in root.glob("*/SKILL.md")}
    return names


def check_skills(roots: list[Path], editable: bool, report: Report) -> None:
    for root in roots:
        for path in root.glob("*/SKILL.md"):
            text = read(path, editable, report)
            if text is None:
                continue
            fields = frontmatter(text)
            if fields.get("name") != path.parent.name:
                report.add("skill-name", path, f"name {fields.get('name')!r} differs from directory {path.parent.name!r}", editable)
            if not fields.get("description"):
                report.add("skill-description", path, "missing description", editable)


def check_skill_references(texts: list[tuple[Path, bool]], known: set[str], report: Report) -> None:
    for path, editable in texts:
        for match in SKILL_REFERENCE.finditer(read(path, editable, report) or ""):
            name = (match.group(1) or match.group(2)).split(":")[-1]
            if name not in known:
                report.add("skill-reference-unknown", path, f"names skill `{name}`, which no skill root has", editable)


def check_hooks(script_dirs: list[Path], settings_files: list[tuple[Path, bool]], editable_dirs: set[Path], report: Report) -> None:
    script_names = {s.name for d in script_dirs if d.is_dir() for s in d.iterdir()}
    registered = set()
    for path, editable in settings_files:
        try:
            hooks = json.loads(path.read_text()).get("hooks", {})
        except (OSError, json.JSONDecodeError) as error:
            report.add("hook-settings-unreadable", path, str(error), editable)
            continue
        if not isinstance(hooks, dict):
            report.add("hook-settings-unreadable", path, "hooks is not an object", editable)
            continue
        for event, entries in hooks.items():
            for entry in entries if isinstance(entries, list) else []:
                for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                    command = hook.get("command", "") if isinstance(hook, dict) else ""
                    for script in HOOK_SCRIPT.findall(command):
                        name = Path(script).name
                        registered.add(name)
                        if Path(os.path.expandvars(script)).expanduser().exists():
                            continue
                        if name in script_names:
                            report.add("hook-script-not-installed", path, f"{event} runs {script}; the script is in a hook directory but not installed", editable)
                        else:
                            report.add("hook-script-missing", path, f"{event} runs {script}, which does not exist", editable)
    for directory in script_dirs:
        if not directory.is_dir():
            report.add("hook-directory-missing", directory, "hooks source is not a directory", directory in editable_dirs)
            continue
        for script in directory.iterdir():
            if script.is_file() and script.name not in registered and not script.name.startswith("."):
                report.add("hook-script-unregistered", script, "no hook settings entry runs this script", directory in editable_dirs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=[])
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    report = Report()

    def sources(kind: str) -> list[tuple[Path, bool]]:
        found = []
        for group, editable in (("editable", True), ("read_only", False)):
            found += [(p, editable) for p in expand(config.get(group, {}).get(kind, []))]
        return found

    for directory, editable in sources("memory"):
        check_memory(directory, editable, report)
    skill_roots = sources("skills")
    for root, editable in skill_roots:
        check_skills([root], editable, report)
    known = skill_names([root for root, _ in skill_roots])
    known |= {Path(p).parent.name for p in glob.glob(str(Path(PLUGIN_SKILLS).expanduser()), recursive=True)}
    texts = []
    for kind in ("rules", "memory"):
        for path, editable in sources(kind):
            texts += [(p, editable) for p in ([path] if path.is_file() else sorted(path.glob("*.md")))]
    texts += [(p, editable) for root, editable in skill_roots for p in sorted(root.glob("*/SKILL.md"))]
    check_skill_references(texts, known, report)
    hook_dirs = sources("hooks")
    check_hooks([d for d, _ in hook_dirs], sources("hook_settings"), {d for d, e in hook_dirs if e}, report)

    only = [Path(p).expanduser().resolve() for p in args.only]
    for finding in report.findings:
        path = Path(finding["path"]).resolve()
        if only and not any(path == o or o in path.parents for o in only):
            continue
        print(json.dumps(finding, ensure_ascii=False))


if __name__ == "__main__":
    main()
