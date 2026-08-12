#!/usr/bin/env sh
# Create the isolated worktree for one task.
#
# This exists as a script rather than as a command in SKILL.md because the command was
# in SKILL.md, correctly, and was never once run correctly. Across an 18-task run, six
# agents attempted it, none included `-b`, five ran it from the wrong directory, and all
# six failed. A shell command in a document gets retyped from understanding; `-b` does
# not survive that, and without `-b` git tries to check out a branch that is already
# checked out in the primary worktree and refuses. The failure is unconditional.
#
# Usage:
#   create-worktree.sh <project-path> <task-id> <worktree-dir> <base-branch>
#
# Prints the created worktree path on stdout. Any failure exits non-zero with a
# diagnostic on stderr: that is a task failure to report, not a situation to work around.

set -eu

if [ $# -ne 4 ]; then
    echo "usage: $0 <project-path> <task-id> <worktree-dir> <base-branch>" >&2
    exit 2
fi

project_path=$1
task_id=$2
worktree_dir=$3
base_branch=$4
branch="worktree-${task_id}"
target="${worktree_dir}/${task_id}"

[ -d "$project_path" ] || { echo "project path does not exist: $project_path" >&2; exit 1; }
cd "$project_path"

# Never operate on a repository other than the one we were pointed at. An agent that has
# drifted upward -- or been handed a path inside someone else's checkout -- must fail here
# rather than initialise or mutate a repository nobody asked about.
toplevel=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "not a git repository: $project_path" >&2
    echo "refusing to run 'git init' -- /execute never creates repositories." >&2
    exit 1
}
# Compare physical paths so a symlinked or differently-cased argument still matches.
if [ "$(cd "$toplevel" && pwd -P)" != "$(pwd -P)" ]; then
    echo "refusing: $project_path is inside a different repository ($toplevel)." >&2
    echo "The target must be the repository root, not a subdirectory of one." >&2
    exit 1
fi

# Only refresh when a remote is actually configured; a repository with no remote is a
# supported configuration and must not fail here (F1).
if git remote get-url origin >/dev/null 2>&1; then
    git fetch origin "$base_branch" || true
fi

git rev-parse --verify --quiet "$base_branch" >/dev/null || {
    echo "base branch does not exist: $base_branch" >&2
    exit 1
}

if git show-ref --verify --quiet "refs/heads/${branch}"; then
    echo "branch ${branch} already exists -- this task has run before." >&2
    echo "Retries reuse the existing worktree via --worktree-path; they do not re-create it." >&2
    exit 1
fi

mkdir -p "$worktree_dir"

# -b is the whole point: create a NEW branch for this task and check that out. Without it
# git checks out <base-branch> itself, which the primary worktree already holds, and
# refuses with "'<branch>' is already used by worktree at ...".
git worktree add -b "$branch" "$target" "$base_branch" >&2

printf '%s\n' "$target"
