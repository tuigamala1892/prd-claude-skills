#!/usr/bin/env sh
# Derive progress from git, rather than from a counter someone maintained by hand.
#
# Run 6 succeeded and still reported tasks_completed 23 against tasks_total 18, 19 entries
# in a completed[] list of 18 tasks, and elapsed_seconds 4000 for a run of 10476. Every
# wrong number was one a model incremented; every right one -- the merge queue -- was
# derived. So derive.
#
# Usage:
#   ledger-status.sh <project-path> <slug> [expected-total]
#
# Prints a JSON object on stdout:
#   {"recorded":18,"verified":18,"verified_tasks":["L0-001",...],"missing":[],
#    "first_unverified":null,"expected":18}
#
# `verified_tasks` is what a resume skips. It lists only tasks confirmed done *before* the
# first gap, so a resume never skips a task on the strength of a record it could not check.
#
# `verified` counts ledger entries whose commit is actually reachable now. An entry whose
# SHA has vanished -- the repository was reset, rebased, or the entry was written
# optimistically -- is reported in `missing`, and `first_unverified` is where a resume must
# restart. Scanning stops being trustworthy at the first gap: a later verified SHA is not
# evidence that an earlier missing one was ever done.

set -eu

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "usage: $0 <project-path> <slug> [expected-total]" >&2
    exit 2
fi

project_path=$1
slug=$2
expected=${3:-null}

[ -d "$project_path" ] || { echo "project path does not exist: $project_path" >&2; exit 1; }
cd "$project_path"
git rev-parse --show-toplevel >/dev/null 2>&1 || {
    echo "not a git repository: $project_path" >&2; exit 1; }

ledger=".execute/$slug/ledger.jsonl"
if [ ! -f "$ledger" ]; then
    printf '{"recorded":0,"verified":0,"verified_tasks":[],"missing":[],"first_unverified":null,"expected":%s}\n' "$expected"
    exit 0
fi

recorded=0
verified=0
missing=""
vtasks=""
first_unverified=""
gap=0

while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || continue
    recorded=$((recorded + 1))
    task=$(printf '%s' "$line" | sed -n 's/.*"task_id":"\([^"]*\)".*/\1/p')
    sha=$(printf '%s' "$line" | sed -n 's/.*"commit":"\([^"]*\)".*/\1/p')
    if [ -n "$sha" ] && git cat-file -e "${sha}^{commit}" 2>/dev/null; then
        # Only count as verified while no earlier entry has gone missing. A resume must not
        # skip a task on the strength of a record it could not check.
        if [ "$gap" -eq 0 ]; then
            verified=$((verified + 1))
            [ -n "$vtasks" ] && vtasks="$vtasks,"
            vtasks="$vtasks\"$task\""
        fi
    else
        gap=1
        [ -n "$missing" ] && missing="$missing,"
        missing="$missing\"$task\""
        [ -z "$first_unverified" ] && first_unverified="$task"
    fi
done < "$ledger"

if [ -z "$first_unverified" ]; then
    fu=null
else
    fu="\"$first_unverified\""
fi

printf '{"recorded":%s,"verified":%s,"verified_tasks":[%s],"missing":[%s],"first_unverified":%s,"expected":%s}\n' \
    "$recorded" "$verified" "$vtasks" "$missing" "$fu" "$expected"
