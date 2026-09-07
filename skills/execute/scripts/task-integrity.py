#!/usr/bin/env python3
"""Snapshot the task files before dispatch, and prove afterwards that nobody edited them.

**A run may not modify the acceptance criteria it is judged against.** The third live crossing
met a Layer 0 task whose `<verification>` block was unsatisfiable -- one step asserted a
substring absent that another requirement mandated present. The run diagnosed it correctly,
edited the task file, and carried on to a green `14/14`. Nothing forbade it, and nothing
recorded it: the ledger indexes commits, and a task edit leaves no trace at all (**P41**).

That result is weaker than it reads, by item 59's own standard -- *a runtime test whose crossing
is made to pass by adjusting the test has measured nothing*. The run reported what it had done,
in detail and unprompted, so the failure is not dishonesty: it is that **honesty was the only
thing standing between a rewritten acceptance criterion and a green result.**

This is that guard, as an exit code rather than a paragraph, for item 4.13's reason -- a guard a
model can reason past is not a guard, and this run reasoned past one that did not exist.

Usage:
    task-integrity.py record <tasks-path> <project-path> <slug>
    task-integrity.py verify <tasks-path> <project-path> <slug>

`record` snapshots every task file. `verify` re-hashes them and reports the difference.

Exit codes, because the caller must treat these differently:
    0  unchanged -- every recorded task file is byte-identical, and the count is on stdout
    1  EDITED -- at least one task file changed, was removed, or appeared. The diff is on
       stdout, and an entry naming it is appended to the run's record. This is a stop.
    2  refused, or nothing recorded to compare against. Not the same claim as `unchanged`,
       and never reported as one.

Where things live, and why there: `{project}/.execute/{slug}/`, beside `ledger.jsonl` and under
the same self-ignoring `.gitignore`. The record of what a run did to its own inputs shares a fate
with the commits it produced -- reset the repository and both go, rather than one surviving to
describe the other. Edits go to `task-edits.jsonl` and NOT to the ledger, because
`ledger-status.sh` reads every line there as a task with a commit and an entry without one would
read as a task whose commit had vanished.
"""

import argparse
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time

TASK_ID = re.compile(r"^(L\d+-\d+)")


def die(msg, code=2):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(code)


def sha256(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def task_files(tasks_path):
    """Every task XML under the tasks path, as paths relative to it, sorted.

    Dot-directories are skipped: the snapshot itself must never become something the next
    snapshot records.
    """
    found = []
    for root, dirs, files in os.walk(tasks_path):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(files):
            if name.endswith(".xml"):
                rel = os.path.relpath(os.path.join(root, name), tasks_path)
                found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def task_id_of(rel):
    m = TASK_ID.match(os.path.basename(rel))
    return m.group(1) if m else rel


def run_dir(project_path, slug):
    return os.path.join(project_path, ".execute", slug)


def snapshot_dir(project_path, slug):
    return os.path.join(run_dir(project_path, slug), "task-snapshot")


def preconditions(tasks_path, project_path):
    if not os.path.isdir(tasks_path):
        die(f"tasks path does not exist: {tasks_path}")
    if not os.path.isdir(project_path):
        die(f"project path does not exist: {project_path}")


def ignore_file(project_path):
    """The same self-ignoring .gitignore record-task.sh writes, for the same reason."""
    base = os.path.join(project_path, ".execute")
    os.makedirs(base, exist_ok=True)
    marker = os.path.join(base, ".gitignore")
    if not os.path.exists(marker):
        with io.open(marker, "w", encoding="utf-8", newline="\n") as f:
            f.write("*\n")


def differences(tasks_path, snap):
    """(changed, removed, added, recorded) between a snapshot and the task files as they are.

    Shared by `record` and `verify` because the question is the same question -- what is
    different from the last snapshot -- asked at two moments. It was in `verify` alone until
    item 67, which is why a re-record could replace a snapshot without anyone knowing what it
    had replaced (**P45**).
    """
    hashes = os.path.join(snap, "hashes.json")
    if not os.path.isfile(hashes):
        return None, None, None, None
    recorded = json.load(io.open(hashes, encoding="utf-8"))["files"]
    present = set(task_files(tasks_path))
    changed, removed = [], []
    for rel, meta in sorted(recorded.items()):
        live = os.path.join(tasks_path, rel)
        if not os.path.isfile(live):
            removed.append(rel)
        elif sha256(live) != meta["sha256"]:
            changed.append(rel)
    added = sorted(present - set(recorded))
    return changed, removed, added, recorded


def write_edits(args, snap, recorded, changed, removed, added, kind):
    """Append one record per difference, with a diff for every modified file.

    `kind` is the only thing that distinguishes an edit made DURING a run from one made between
    two of them -- deliberately. Both are the same act on the same file, and the second is
    legitimate while the first is not; what neither may be is invisible.
    """
    run = run_dir(args.project_path, args.slug)
    os.makedirs(os.path.join(run, "task-edits"), exist_ok=True)
    at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines, diffs = [], []

    for rel in changed:
        before = io.open(os.path.join(snap, rel), encoding="utf-8",
                         errors="replace").read().splitlines(keepends=True)
        after = io.open(os.path.join(args.tasks_path, rel), encoding="utf-8",
                        errors="replace").read().splitlines(keepends=True)
        diff = "".join(difflib.unified_diff(
            before, after,
            fromfile=f"a/{rel} ({'as dispatched' if kind == 'modified' else 'previous run'})",
            tofile=f"b/{rel} (now)"))
        # Named by the CONTENT it records, not by the clock. A timestamp at second resolution
        # collided the first time this ran -- two edits to one task inside the same second, and
        # the second diff overwrote the first, which is P45's erasure one directory down. A
        # content hash also makes re-recording the same edit idempotent rather than duplicated.
        after_sha = sha256(os.path.join(args.tasks_path, rel))
        name = f"{task_id_of(rel)}-{after_sha[:12]}.diff"
        with io.open(os.path.join(run, "task-edits", name), "w", encoding="utf-8",
                     newline="\n") as f:
            f.write(diff)
        diffs.append(diff)
        lines.append({"task_id": task_id_of(rel), "path": rel, "kind": kind, "at": at,
                      "sha_before": recorded[rel]["sha256"], "sha_after": after_sha,
                      "diff": f"task-edits/{name}"})

    for rel in removed:
        lines.append({"task_id": task_id_of(rel), "path": rel,
                      "kind": "removed" if kind == "modified" else "removed-between-runs",
                      "at": at, "sha_before": recorded[rel]["sha256"], "sha_after": None,
                      "diff": None})
    for rel in added:
        lines.append({"task_id": task_id_of(rel), "path": rel,
                      "kind": "added" if kind == "modified" else "added-between-runs",
                      "at": at, "sha_before": None,
                      "sha_after": sha256(os.path.join(args.tasks_path, rel)), "diff": None})

    edits = os.path.join(run, "task-edits.jsonl")
    with io.open(edits, "a", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
    return lines, diffs, edits


def cmd_record(args):
    preconditions(args.tasks_path, args.project_path)
    files = task_files(args.tasks_path)
    if not files:
        die(f"no task files (*.xml) under {args.tasks_path}")

    ignore_file(args.project_path)
    snap = snapshot_dir(args.project_path, args.slug)

    # ITEM 67. Compare BEFORE replacing. A resume re-records -- an operator may fix a task
    # between runs, and forbidding that leaves an unsatisfiable task with nowhere to go -- but
    # until this, re-recording replaced the evidence with the thing it was evidence about. The
    # fourth live crossing stopped on a task, the task was edited, the resume snapshotted the
    # edited file, and `verify` reported UNCHANGED for the rest of the run (**P45**).
    #
    # So the edit is recorded and the run is not stopped. The distinction between `the operator`
    # and `the run` is not visible on disk and this does not pretend to draw it: both leave the
    # same trace, which is the honest version of the same protection.
    changed, removed, added, recorded = differences(args.tasks_path, snap)
    between = []
    if recorded is not None and (changed or removed or added):
        between, diffs, edits = write_edits(args, snap, recorded, changed, removed, added,
                                            "edited-between-runs")
        print(f"CHANGED SINCE LAST RUN: {len(between)} task file(s) differ from the previous "
              f"snapshot:", file=sys.stderr)
        for line in between:
            print(f"  {line['kind']:<20} {line['task_id']}  {line['path']}", file=sys.stderr)
        for diff in diffs:
            print(diff, end="", file=sys.stderr)
        print(f"recorded in {edits}. This is allowed -- a task may be fixed between runs -- and "
              f"it is reported because a run that resumes into edited criteria should say so.",
              file=sys.stderr)

    if os.path.isdir(snap):
        shutil.rmtree(snap)
    os.makedirs(snap)

    entries = {}
    for rel in files:
        src = os.path.join(args.tasks_path, rel)
        dst = os.path.join(snap, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        entries[rel] = {"sha256": sha256(src), "bytes": os.path.getsize(src),
                        "task_id": task_id_of(rel)}

    with io.open(os.path.join(snap, "hashes.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "tasks_path": os.path.abspath(args.tasks_path),
                   "files": entries}, f, indent=2)
        f.write("\n")

    print(f"RECORDED {len(entries)} task file(s) from {args.tasks_path}"
          + (f" ({len(between)} changed since the last run)" if between else ""))
    return 0


def cmd_verify(args):
    preconditions(args.tasks_path, args.project_path)
    snap = snapshot_dir(args.project_path, args.slug)
    hashes = os.path.join(snap, "hashes.json")
    if not os.path.isfile(hashes):
        # Not `unchanged`. Nothing was recorded, so nothing can be said either way, and a run
        # that reports "task files unchanged" on this basis has asserted what it did not check.
        print(f"NO RECORD: nothing was recorded for {args.slug} at {snap}", file=sys.stderr)
        print("Run `task-integrity.py record` before dispatching any task.", file=sys.stderr)
        return 2

    changed, removed, added, recorded = differences(args.tasks_path, snap)

    if not (changed or removed or added):
        print(f"UNCHANGED {len(recorded)} task file(s) since dispatch (sha256)")
        return 0

    lines, diffs, edits = write_edits(args, snap, recorded, changed, removed, added, "modified")
    for diff in diffs:
        print(diff, end="")

    print(f"EDITED {len(lines)} task file(s) changed since dispatch:", file=sys.stderr)
    for line in lines:
        print(f"  {line['kind']:<8} {line['task_id']}  {line['path']}", file=sys.stderr)
    print(f"recorded in {edits}", file=sys.stderr)
    print("A task file is the acceptance criteria this run is judged against. Stop, report the "
          "diff above, and fix the task with /breakdown -- not from inside the run.",
          file=sys.stderr)
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    for mode in ("record", "verify"):
        p = sub.add_parser(mode)
        p.add_argument("tasks_path")
        p.add_argument("project_path")
        p.add_argument("slug")
    args = ap.parse_args()
    return cmd_record(args) if args.mode == "record" else cmd_verify(args)


if __name__ == "__main__":
    sys.exit(main())
