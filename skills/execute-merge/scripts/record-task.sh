#!/usr/bin/env sh
# Record one completed task in the ledger, after its commit exists.
#
# The ledger is an index into git, not a substitute for it. Two rules make it trustworthy,
# and both are enforced here rather than described:
#
#   1. Record a SHA, never an adjective. "completed" cannot be checked; a SHA can.
#   2. Append AFTER the commit exists. A crash between the two under-reports progress,
#      which is recoverable. The reverse over-reports, which is how execute-state.json
#      came to claim 23 of 18 tasks done in a run that actually completed 18.
#
# Usage:
#   record-task.sh <project-path> <slug> <task-id> <commit-sha> [attempts]
#
# Exits non-zero if the commit does not exist. That is the whole point: a task cannot be
# recorded as done by asserting it.

set -eu

if [ $# -lt 4 ] || [ $# -gt 5 ]; then
    echo "usage: $0 <project-path> <slug> <task-id> <commit-sha> [attempts]" >&2
    exit 2
fi

project_path=$1
slug=$2
task_id=$3
commit=$4
attempts=${5:-1}

[ -d "$project_path" ] || { echo "project path does not exist: $project_path" >&2; exit 1; }
cd "$project_path"

toplevel=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "not a git repository: $project_path" >&2; exit 1; }
if [ "$(cd "$toplevel" && pwd -P)" != "$(pwd -P)" ]; then
    echo "refusing: $project_path is inside a different repository ($toplevel)." >&2
    exit 1
fi

# The commit must exist, and must be a commit. Verify before writing anything.
if ! git cat-file -e "${commit}^{commit}" 2>/dev/null; then
    echo "refusing to record ${task_id}: commit ${commit} does not exist in $project_path" >&2
    echo "A task is done when a commit exists, not when something says it is." >&2
    exit 1
fi
full=$(git rev-parse "${commit}^{commit}")

# The ledger lives with the commits it indexes, so the two share a fate: reset or re-clone
# the repository and the ledger goes too, rather than surviving to describe work that is no
# longer there. The self-ignoring .gitignore keeps it out of `git status` without touching a
# tracked file.
base=.execute
mkdir -p "$base/$slug"
[ -f "$base/.gitignore" ] || printf '*\n' > "$base/.gitignore"

printf '{"task_id":"%s","commit":"%s","at":"%s","attempts":%s,"verified":true}\n' \
    "$task_id" "$full" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$attempts" \
    >> "$base/$slug/ledger.jsonl"

echo "recorded ${task_id} -> ${full}" >&2
printf '%s\n' "$full"
