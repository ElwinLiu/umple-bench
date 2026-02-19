#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_FILE="$ROOT_DIR/scripts/state_machine_graph.py"
MODE="sync"

usage() {
  cat << 'USAGE'
Usage:
  scripts/sync_state_machine_graph.sh         # copy canonical helper into task tests/
  scripts/sync_state_machine_graph.sh --check # verify task copies match canonical helper
USAGE
}

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "Missing canonical helper: $SOURCE_FILE" >&2
  exit 1
fi

if [[ $# -gt 1 ]]; then
  usage
  exit 1
fi

if [[ $# -eq 1 ]]; then
  case "$1" in
    --check)
      MODE="check"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 1
      ;;
  esac
fi

count=0
outdated=0

while IFS= read -r verifier_file; do
  [[ -n "$verifier_file" ]] || continue

  if ! rg -q "state_machine_graph" "$verifier_file"; then
    continue
  fi

  target_file="$(dirname "$verifier_file")/state_machine_graph.py"
  rel_target="${target_file#$ROOT_DIR/}"
  count=$((count + 1))

  if [[ "$MODE" == "sync" ]]; then
    cp "$SOURCE_FILE" "$target_file"
    echo "SYNCED: $rel_target"
  else
    if [[ ! -f "$target_file" ]] || ! cmp -s "$SOURCE_FILE" "$target_file"; then
      echo "OUTDATED: $rel_target"
      outdated=$((outdated + 1))
    fi
  fi
done < <(rg --files "$ROOT_DIR/tasks" -g "**/tests/test_state_machine.py")

if [[ $count -eq 0 ]]; then
  echo "No verifier files importing state_machine_graph were found." >&2
  exit 1
fi

if [[ "$MODE" == "check" ]]; then
  if [[ $outdated -eq 0 ]]; then
    echo "All $count state_machine_graph.py copies are up to date."
  else
    echo "$outdated of $count state_machine_graph.py copies are out of date." >&2
    exit 1
  fi
else
  echo "Synced $count state_machine_graph.py copies."
fi
