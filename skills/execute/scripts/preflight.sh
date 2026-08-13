#!/usr/bin/env sh
# Every precondition /execute has, as one program whose exit status is the decision.
#
# These checks used to be prose in SKILL.md. Finding F15 is what happened next: pointed at a
# path containing docs/prd/ -- the exact case the prose refused -- /execute produced a full
# execution plan, and reasoned past the missing repository too:
#
#   "The project path is not yet a git repository - which is expected since this is a
#    greenfield project where L0-002 initializes git."
#
# A capable model treats prose as context to be weighed. It cannot weigh an exit code.
#
# This script also *resolves* the base branch and prints it, so running it is the cheapest
# way to get on with the job rather than a hoop to jump through. A guard nobody benefits from
# running is a guard that eventually stops being run.
#
# Usage:
#   preflight.sh <tasks-path> <project-path> [base-branch]
#
# On success: prints the resolved base branch on stdout, exits 0.
# On failure: prints REFUSED: <reason> on stderr, exits 1. There is nothing to interpret.

set -eu

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "usage: $0 <tasks-path> <project-path> [base-branch]" >&2
    exit 2
fi

tasks_path=$1
project_path=$2
base_branch=${3:-}

refuse() {
    echo "REFUSED: $1" >&2
    exit 1
}

# ---------------------------------------------------------------- inputs exist
[ -d "$tasks_path" ] || refuse "tasks path does not exist: $tasks_path"
[ -f "$tasks_path/manifest.json" ] || \
    refuse "no manifest.json in $tasks_path -- run /breakdown first"
[ -f "$tasks_path/layer_plan.json" ] || \
    refuse "no layer_plan.json in $tasks_path -- run /breakdown first"
[ -d "$project_path" ] || refuse "project path does not exist: $project_path"

# Resolve both to physical paths before comparing them; a relative argument or a symlink
# would otherwise slip past the containment checks below.
tasks_abs=$(cd "$tasks_path" && pwd -P)
project_abs=$(cd "$project_path" && pwd -P)

# ------------------------------------------------- never valid targets, whatever was typed
# /execute creates branches, merges and removes worktrees inside the target. A mistyped
# argument therefore does real damage, so rule these out before anything else runs.
[ -d "$project_abs/docs/prd" ] && \
    refuse "$project_abs contains docs/prd/ -- this is a documentation tree, not a target project"
[ -f "$project_abs/.claude-plugin/plugin.json" ] && \
    refuse "$project_abs is a Claude Code plugin -- this is the toolchain, not a target project"

case "$project_abs" in
    "$tasks_abs"|"$tasks_abs"/*)
        refuse "$project_abs is inside the tasks directory" ;;
esac
case "$tasks_abs" in
    "$project_abs"/*)
        # Not fatal on its own, but worth naming: the tasks tree would be committed as part
        # of the product unless it is ignored.
        echo "NOTE: tasks directory is inside the target project; it will show up in git status" >&2 ;;
esac

# ------------------------------------------------------------------ a real git repository
# /execute never creates one. Layer 0 used to claim it would, which contradicted this check
# and is finding F2.
toplevel=$(git -C "$project_abs" rev-parse --show-toplevel 2>/dev/null) || \
    refuse "$project_abs is not a git repository. /execute does not create repositories -- initialise it yourself, then re-run"

toplevel_abs=$(cd "$toplevel" && pwd -P)
[ "$toplevel_abs" = "$project_abs" ] || \
    refuse "$project_abs is inside a different repository ($toplevel_abs). The target must be the repository root"

# ------------------------------------------------------------------------- the base branch
# Never assumed to be `main` (F1). Everything downstream branches from and merges into this.
if [ -n "$base_branch" ]; then
    git -C "$project_abs" rev-parse --verify --quiet "$base_branch" >/dev/null || \
        refuse "base branch does not exist in $project_abs: $base_branch"
else
    base_branch=$(git -C "$project_abs" symbolic-ref --short HEAD 2>/dev/null) || \
        refuse "HEAD is detached in $project_abs, so there is no branch to merge into. Pass --base-branch explicitly"
fi

printf '%s\n' "$base_branch"
