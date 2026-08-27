#!/bin/sh
# Refuse `git checkout -- <path>` on a file with uncommitted work (item 54's rule, as a guard).
#
# The ledger has said since item 54 that mutation-testing an uncommitted file must not be undone
# with `git checkout -- <file>`: it reverts to HEAD and discards the real edits along with the
# mutation. That rule was written down, read, and then broken anyway on 2026-08-27, losing two
# regression checks (recovered from a scratchpad patch script, which was luck rather than
# design).
#
# A rule that has been violated by the person who wrote it is a prose guard, and P16 is the
# whole plan's finding about those. So: an exit code.
#
#   sh tests/dirty-guard.sh <path>...
#
#   exit 0  every path is clean, or does not exist -- checkout is safe
#   exit 1  at least one path has uncommitted changes. Copy it aside first
set -e
dirty=""
for p in "$@"; do
    if [ -e "$p" ] && ! git diff --quiet -- "$p" 2>/dev/null; then
        dirty="$dirty $p"
    fi
done
if [ -n "$dirty" ]; then
    echo "REFUSED: uncommitted work would be discarded by a checkout:" >&2
    for p in $dirty; do
        echo "  $p  ($(git diff --numstat -- "$p" | awk '{print $1"+ "$2"-"}'))" >&2
    done
    echo "" >&2
    echo "Copy the file aside and copy it back, as the mutation harness does. A checkout" >&2
    echo "reverts to HEAD and takes the real edits with the mutation -- item 54." >&2
    exit 1
fi
echo "clean: $* -- checkout is safe"
