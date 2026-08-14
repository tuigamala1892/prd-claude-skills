#!/usr/bin/env python3
"""Write execute-state.json, deriving every countable field from git and the ledger.

This file has been wrong in every run that produced it, and wrong differently each time:

  run 6   tasks_completed 23 against tasks_total 18; completed[] held 19 entries;
          elapsed_seconds 4000 for a run of 10476
  run 7   status "completed" alongside tasks_remaining 2
  run 8   status "completed" alongside tasks_completed 4 of 18, while git held 18 merges --
          and a second copy of the file written into the TARGET repository, each copy
          holding a different half of the schema

Four wrong shapes, four sets of prose instructions telling the model how to keep it right.
Meanwhile the manifest, the worktree, the ledger and the preflight became scripts and have
been correct in every run since. So this is a script.

Nothing here is incremented and nothing is asserted. Task completion comes from the ledger,
re-verified against git; counts come from len(). The only fields carried over are the ones
that genuinely cannot be derived -- when a task was abandoned, and why -- and even those
come from the previous file rather than from a running total.

Usage:
    write-state.py <tasks-path> <project-path> <slug> [--started-at ISO8601]
                   [--abandoned ID,ID] [--failed ID,ID]

Writes <tasks-path>/execute-state.json and prints a one-line summary. Refuses to write
anywhere inside <project-path>.
"""

import json
import os
import subprocess
import sys
import time


def git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_ledger(project_path, slug):
    """Ledger entries whose commit still exists, in order, stopping at the first gap.

    Stopping is deliberate: a later verified SHA is not evidence that an earlier missing one
    was ever done, so counting past a gap would over-report exactly as before.
    """
    path = os.path.join(project_path, ".execute", slug, "ledger.jsonl")
    verified, missing, gap = [], [], False
    if not os.path.isfile(path):
        return verified, missing
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        sha = e.get("commit") or ""
        ok = bool(sha) and subprocess.run(
            ["git", "cat-file", "-e", sha + "^{commit}"],
            cwd=project_path, capture_output=True).returncode == 0
        if ok and not gap:
            verified.append(e)
        else:
            gap = True
            missing.append(e)
    return verified, missing


def main():
    argv = sys.argv[1:]
    opts = {}
    for key in ("--started-at", "--abandoned", "--failed"):
        if key in argv:
            i = argv.index(key)
            if i + 1 < len(argv):
                opts[key] = argv[i + 1]
                argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 3:
        print(__doc__.strip().split("Usage:")[-1], file=sys.stderr)
        return 2

    tasks_path = os.path.abspath(args[0])
    project_path = os.path.abspath(args[1])
    slug = args[2]

    if not os.path.isdir(tasks_path):
        print(f"tasks path does not exist: {tasks_path}", file=sys.stderr)
        return 1

    state_path = os.path.join(tasks_path, "execute-state.json")

    # F21 was a *second* copy of this file at the target's root, alongside the correct one in
    # the tasks directory. The first version of this guard refused whenever the tasks path sat
    # anywhere inside the project -- which also refuses the legitimate brownfield layout, where
    # `/crd` and `/breakdown` write `docs/crd/` and `docs/tasks/` *into* the project on purpose,
    # so a change request travels with the code it changes. That broke the CRD path entirely
    # (F22). Refuse the actual mistake instead: writing to the project root.
    if os.path.normcase(os.path.abspath(state_path)) == os.path.normcase(
            os.path.join(os.path.abspath(project_path), "execute-state.json")):
        print(f"REFUSED: that would write execute-state.json to the project root "
              f"({project_path}). It belongs in the tasks directory.", file=sys.stderr)
        return 1
    prev = {}
    if os.path.isfile(state_path):
        try:
            prev = json.load(open(state_path, encoding="utf-8"))
        except Exception:
            pass

    manifest = {}
    mpath = os.path.join(tasks_path, "manifest.json")
    if os.path.isfile(mpath):
        try:
            manifest = json.load(open(mpath, encoding="utf-8"))
        except Exception:
            pass
    inventory = manifest.get("task_inventory") or []
    total = manifest.get("summary", {}).get("total_tasks", len(inventory))

    verified, missing = read_ledger(project_path, slug)
    done = {e["task_id"]: e for e in verified if e.get("task_id")}

    def id_list(key):
        raw = opts.get(key)
        if raw is not None:
            return [x for x in (s.strip() for s in raw.split(",")) if x]
        return list(prev.get(key.lstrip("-"), []) or [])

    abandoned = [t for t in id_list("--abandoned") if t not in done]
    failed = [t for t in id_list("--failed") if t not in done and t not in abandoned]

    tasks, layers = {}, {}
    for entry in inventory:
        tid, layer = entry.get("id"), entry.get("layer", "unknown")
        if not tid:
            continue
        if tid in done:
            status = "merged"
        elif tid in abandoned:
            status = "abandoned"
        elif tid in failed:
            status = "failed"
        else:
            status = "pending"
        rec = {"status": status, "layer": layer, "name": entry.get("name", "")}
        if tid in done:
            rec["commit"] = done[tid].get("commit")
            rec["merged_at"] = done[tid].get("at")
            rec["attempts"] = done[tid].get("attempts", 1)
        tasks[tid] = rec
        lay = layers.setdefault(layer, {"total": 0, "merged": 0})
        lay["total"] += 1
        if status == "merged":
            lay["merged"] += 1
    for lay in layers.values():
        lay["status"] = "completed" if lay["merged"] == lay["total"] else "in_progress"

    # `completed` only when every task the manifest knows about has a commit that exists.
    complete = bool(total) and len(done) == total and not missing and not abandoned
    state = {
        "schema_version": "3.0",
        "prd_slug": slug,
        "project_path": project_path,
        "tasks_path": tasks_path,
        "started_at": opts.get("--started-at") or prev.get("started_at") or now(),
        "updated_at": now(),
        "completed_at": now() if complete else None,
        "status": "completed" if complete else "in_progress",
        "derived_from": "ledger + git; no field in this file is maintained by hand",
        "tasks": tasks,
        "layers": layers,
        "completed": sorted(done),
        "failed": failed,
        "abandoned": abandoned,
        "merge_queue": [{"task_id": t, "status": "merged", "commit": done[t].get("commit"),
                         "merged_at": done[t].get("at")} for t in sorted(done)],
        "missing_commits": [e.get("task_id") for e in missing],
        "metrics": {
            "tasks_total": total,
            "tasks_completed": len(done),
            "tasks_failed": len(failed),
            "tasks_abandoned": len(abandoned),
            "tasks_remaining": max(0, (total or 0) - len(done)),
            "total_attempts": sum(int(e.get("attempts", 1) or 1) for e in verified),
        },
    }

    with open(state_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")

    stray = os.path.join(project_path, "execute-state.json")
    if os.path.isfile(stray):
        print(f"WARNING: a stray {stray} exists inside the target project. It is not written "
              f"by this script; delete it.", file=sys.stderr)

    print(f"execute-state.json: {state['status']}, {len(done)}/{total} verified"
          + (f", {len(missing)} commit(s) missing" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
