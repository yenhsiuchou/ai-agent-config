#!/usr/bin/env bash
set -euo pipefail

repository_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backup_dir="$HOME/.agent-config-backups/$(date +%Y%m%d-%H%M%S)"

link_path() {
  local source_path="$1"
  local destination_path="$2"
  local backup_path

  if [[ -L "$destination_path" ]] && [[ "$(readlink "$destination_path")" == "$source_path" ]]; then
    return
  fi

  if [[ -e "$destination_path" || -L "$destination_path" ]]; then
    backup_path="$backup_dir${destination_path#$HOME}"
    mkdir -p "$(dirname "$backup_path")"
    mv "$destination_path" "$backup_path"
  fi

  mkdir -p "$(dirname "$destination_path")"
  ln -s "$source_path" "$destination_path"
}

link_path "$repository_dir/AGENTS.md" "$HOME/.codex/AGENTS.md"
link_path "$repository_dir/AGENTS.md" "$HOME/.claude/CLAUDE.md"

for skill_dir in "$repository_dir"/skills/*; do
  skill_name="$(basename "$skill_dir")"
  link_path "$skill_dir" "$HOME/.codex/skills/$skill_name"
  link_path "$skill_dir" "$HOME/.claude/skills/$skill_name"
done

echo "Installed shared agent configuration from $repository_dir"
