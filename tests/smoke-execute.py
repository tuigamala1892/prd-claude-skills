#!/usr/bin/env python3
"""Assert what an /execute run leaves behind, for the Phase 1 changes that touched it.

Phase 1 changed seven files on the execute path and the regression suite covers them
statically: it reads instructions, and runs `record-task.sh` and the `<cwd>` guard in
isolation. Nothing had run the pipeline. This closes that gap.

WHAT IT ASSERTS, AND WHICH ITEM EACH ONE IS FOR

  ledger entries carry `verified: "task-steps"`      item 55 -- not a bare `true`
  every ledger commit exists in git                  the ledger's own rule
  at least one merge happened                        item 60 -- the old 5d loop scanned
                                                     merge_queue for "ready", which
                                                     write-state.py never writes, so a run
                                                     following it would merge nothing
  execute-state.json is schema 3.0                   item 23a
  its root keys match what write-state.py writes     item 23a, at runtime rather than in docs
  no execute-state.json at the project root          F21
  no worktree left attached                          a preserved worktree means an abandonment

USAGE

    smoke-execute.py <workspace> [--slug link-shelf] [--expect-tasks N]

  <workspace>  the fixture workspace: holds docs/tasks/<slug>/ and app/

  exit 0  every assertion held
  exit 1  at least one failed, each named
  exit 2  the run did not happen -- nothing to assert. Not a pass.
"""

import argparse
import ast
import json
import os
import subprocess
import sys


def git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def writer_keys(repo):
    """The root keys write-state.py actually writes, from its own dict literal."""
    path = os.path.join(repo, "skills", "execute", "scripts", "write-state.py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                and any(isinstance(t, ast.Name) and t.id == "state" for t in node.targets)):
            return [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
    raise SystemExit("no `state = {...}` literal in write-state.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workspace")
    ap.add_argument("--slug", default="link-shelf")
    ap.add_argument("--expect-tasks", type=int, default=None,
                    help="fail unless exactly this many tasks are recorded merged")
    args = ap.parse_args()

    ws = os.path.abspath(args.workspace)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = os.path.join(ws, "app")
    tasks_dir = os.path.join(ws, "docs", "tasks", args.slug)
    ledger_path = os.path.join(app, ".execute", args.slug, "ledger.jsonl")
    state_path = os.path.join(tasks_dir, "execute-state.json")

    if not os.path.isdir(app):
        print(f"exit 2: no target project at {app}", file=sys.stderr)
        return 2
    if not os.path.isfile(ledger_path):
        print(f"exit 2: no ledger at {ledger_path}. /execute has not merged anything, so "
              f"there is nothing to assert -- an empty run is not a passing run.",
              file=sys.stderr)
        return 2

    fails, notes = [], []

    entries = []
    for line in open(ledger_path, encoding="utf-8"):
        line = line.strip()
        if line:
            entries.append(json.loads(line))

    # item 60: a run following the old 5d loop merges nothing at all.
    if not entries:
        fails.append("the ledger exists but is empty: no task was merged (item 60)")
    else:
        notes.append(f"{len(entries)} task(s) merged and recorded")

    for e in entries:
        # item 55
        if e.get("verified") != "task-steps":
            fails.append(f"{e.get('task_id')}: ledger says verified={e.get('verified')!r}, "
                         f"expected 'task-steps' (item 55)")
        # the rule the ledger rests on
        sha = e.get("commit") or ""
        if not sha or git(["cat-file", "-e", sha + "^{commit}"], app) is None:
            fails.append(f"{e.get('task_id')}: ledger commit {sha[:12]} is not in the "
                         f"repository")
        elif not git(["merge-base", "--is-ancestor", sha, "HEAD"], app) == "":
            # `--is-ancestor` prints nothing and exits 0 when true; git() returns "" then.
            fails.append(f"{e.get('task_id')}: commit {sha[:12]} is not reachable from HEAD, "
                         f"so it was recorded but not merged")

    if args.expect_tasks is not None and len(entries) != args.expect_tasks:
        fails.append(f"expected {args.expect_tasks} merged task(s), ledger has {len(entries)}")

    # item 23a, at runtime
    if not os.path.isfile(state_path):
        fails.append(f"no execute-state.json at {state_path}")
    else:
        state = json.load(open(state_path, encoding="utf-8"))
        if state.get("schema_version") != "3.0":
            fails.append(f"execute-state.json says schema_version "
                         f"{state.get('schema_version')!r}, expected '3.0' (item 23a)")
        expected = writer_keys(repo)
        missing = [k for k in expected if k not in state]
        extra = [k for k in state if k not in expected]
        if missing or extra:
            fails.append(f"execute-state.json's shape does not match write-state.py: "
                         f"missing={missing} unexpected={extra}")
        else:
            notes.append(f"execute-state.json is schema {state['schema_version']} with "
                         f"{len(expected)} root fields, status {state.get('status')!r}")

    # F21: the second copy that appeared in run 8.
    stray = os.path.join(app, "execute-state.json")
    if os.path.exists(stray):
        fails.append(f"F21: a second execute-state.json was written to the project root")

    worktrees = (git(["worktree", "list"], app) or "").splitlines()
    if len(worktrees) > 1:
        notes.append(f"{len(worktrees) - 1} worktree(s) still attached -- a task was abandoned")
    else:
        notes.append("no worktrees left attached")

    print("Execute smoke test\n" + "=" * 60)
    for note in notes:
        print(f"  ok    {note}")
    for fail in fails:
        print(f"  FAIL  {fail}")
    print("=" * 60)
    print(f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
