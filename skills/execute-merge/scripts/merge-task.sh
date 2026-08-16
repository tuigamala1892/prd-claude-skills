#!/usr/bin/env sh
# Merge one task's worktree into the base branch, record it, and clean up -- as one program.
#
# This is the structural half of item 4.12: git operations in one place with one owner. It was
# the last git sequence in the toolchain still *described* rather than executed -- twelve
# commands spread across ten prose steps in execute-merge/SKILL.md, carried out by a forked
# skill. Every other critical git operation here became a script because the prose version
# demonstrably failed:
#
#   worktree creation  six agents retyped it, none kept `-b`, all six failed       (F18)
#   the toplevel guard a run walked up, ran `git init`, and merged into that       (F19)
#   the ledger         a status field said 23 of 18 tasks were done                (F16)
#
# There is no reason to expect the merge to be the exception, and one specific reason to
# expect it not to be: it is the step that decides whether a task counts as complete.
#
# Usage:
#   merge-task.sh <project-path> <slug> <task-id> <worktree-path> <task-file> [base-branch] [attempts]
#
# On success: prints the merge commit SHA on stdout, exits 0. The task is merged AND recorded.
#
# Exit codes, because the caller must treat these differently:
#   0  merged, recorded, cleaned up
#   1  refused before touching anything -- preconditions failed, nothing was merged
#   2  bad usage
#   3  merge conflict. The merge was aborted and the worktree PRESERVED. Not a task failure
#      to retry blindly: sequential merging is supposed to make this impossible, so a
#      conflict means an assumption broke and a human should look.
#
# ORDER: MERGE, RECORD, THEN CLEAN UP
#
# Not the order the prose had, and the difference matters. Recording immediately after the
# merge commit exists means a crash in between *under*-reports progress, which a resume
# recovers from. Cleaning up first would put a failure mode -- a worktree that will not
# remove -- between the commit and the record of it, so a completed, merged task could end up
# unrecorded and then redone. Cleanup is tidying; it cannot be allowed to decide whether work
# counts.

set -eu

if [ $# -lt 5 ] || [ $# -gt 7 ]; then
    echo "usage: $0 <project-path> <slug> <task-id> <worktree-path> <task-file> [base-branch] [attempts]" >&2
    exit 2
fi

project_path=$1
slug=$2
task_id=$3
worktree_path=$4
task_file=$5
base_branch=${6:-}
attempts=${7:-1}
branch="worktree-${task_id}"

here=$(cd "$(dirname "$0")" && pwd -P)

refuse() {
    echo "REFUSED: $1" >&2
    exit 1
}

# ------------------------------------------------------------------ the target repository
[ -d "$project_path" ] || refuse "project path does not exist: $project_path"
cd "$project_path"

toplevel=$(git rev-parse --show-toplevel 2>/dev/null) \
    || refuse "not a git repository: $project_path (/execute never creates one)"
[ "$(cd "$toplevel" && pwd -P)" = "$(pwd -P)" ] \
    || refuse "$project_path is inside a different repository ($toplevel); the target must be the repository root"

# ------------------------------------------------------------------------ the base branch
# Never assumed to be `main` (F1).
if [ -z "$base_branch" ]; then
    base_branch=$(git symbolic-ref --short HEAD 2>/dev/null) \
        || refuse "HEAD is detached in $project_path and no base branch was given"
fi
git rev-parse --verify --quiet "$base_branch" >/dev/null \
    || refuse "base branch does not exist: $base_branch"

# Tracked changes only. Untracked files are none of our business -- the tasks directory
# legitimately sits inside the target in some layouts -- but a dirty index would be clobbered
# by the checkout below, and that is someone's unsaved work.
if ! git diff --quiet || ! git diff --cached --quiet; then
    refuse "$project_path has uncommitted tracked changes; refusing to check out $base_branch over them"
fi

# ------------------------------------------------------------------------ the worktree
[ -d "$worktree_path" ] || refuse "worktree does not exist: $worktree_path"
git show-ref --verify --quiet "refs/heads/${branch}" \
    || refuse "branch ${branch} does not exist -- nothing to merge for ${task_id}"

wt_branch=$(git -C "$worktree_path" branch --show-current 2>/dev/null || echo '')
[ "$wt_branch" = "$branch" ] \
    || refuse "worktree $worktree_path is on '${wt_branch:-<detached>}', expected '$branch'"

if ! git -C "$worktree_path" diff --quiet || ! git -C "$worktree_path" diff --cached --quiet; then
    refuse "worktree $worktree_path has uncommitted changes; the task agent must commit its own work"
fi

ahead=$(git rev-list --count "${base_branch}..${branch}")
[ "$ahead" -ge 1 ] \
    || refuse "${branch} has no commits beyond ${base_branch}; there is nothing to merge for ${task_id}"

# -------------------------------------------------------------------- the merge itself
task_name=$(sed -n 's:.*<name>\(.*\)</name>.*:\1:p' "$task_file" 2>/dev/null | head -1)
layer=$(sed -n 's:.*<layer>\(.*\)</layer>.*:\1:p' "$task_file" 2>/dev/null | head -1)
[ -n "$task_name" ] || task_name=$task_id

git checkout --quiet "$base_branch"

# Only when a remote is actually configured. A repository with no remote is supported, and an
# unconditional fetch used to fail the whole merge queue (F1).
if git remote get-url origin >/dev/null 2>&1; then
    git fetch origin "$base_branch" >/dev/null 2>&1 || true
    git merge "origin/${base_branch}" --ff-only >/dev/null 2>&1 || true
fi

msg="Merge ${branch}: ${task_name}

Task: ${task_id}${layer:+
Layer: ${layer}}
Commits: ${ahead}

Verification: passed"

if ! git merge --no-ff "$branch" -m "$msg" >&2; then
    git merge --abort 2>/dev/null || true
    echo "CONFLICT: merging ${branch} into ${base_branch} conflicted; merge aborted" >&2
    echo "Worktree PRESERVED at ${worktree_path} for inspection." >&2
    echo "Sequential merging is meant to prevent this, so an assumption has broken." >&2
    exit 3
fi

merge_sha=$(git rev-parse HEAD)

# ------------------------------------------------------------------------ record it now
# Before cleanup, and by the one script that owns the ledger -- which verifies the SHA exists
# rather than taking this script's word for it.
sh "$here/record-task.sh" "$project_path" "$slug" "$task_id" "$merge_sha" "$attempts" >/dev/null

# ------------------------------------------------------------------------ then tidy up
# Past this point the task is merged and recorded. Nothing below may change that, so failures
# here are warnings: a worktree left behind is untidy, whereas a completed task reported as
# outstanding gets redone.
cleanup_warned=0
if ! git worktree remove "$worktree_path" 2>/dev/null; then
    if ! git worktree remove --force "$worktree_path" 2>/dev/null; then
        echo "WARNING: could not remove worktree $worktree_path (task is merged and recorded)" >&2
        cleanup_warned=1
    fi
fi
if ! git branch -d "$branch" >/dev/null 2>&1; then
    if ! git branch -D "$branch" >/dev/null 2>&1; then
        echo "WARNING: could not delete branch $branch (task is merged and recorded)" >&2
        cleanup_warned=1
    fi
fi
[ "$cleanup_warned" -eq 0 ] || echo "NOTE: merge succeeded; only cleanup was incomplete." >&2

echo "[MERGE] ${task_id} -> ${base_branch} (${merge_sha})" >&2
printf '%s\n' "$merge_sha"
