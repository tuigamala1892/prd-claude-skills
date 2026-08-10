"""Execute the Phase 0 probes via `claude -p` and capture ground truth.

Each run gets its own copy of the probe project. That isolation matters: the
control arm writes the same filename across several evals, so shared state would
let one run's output be mistaken for another's.

Ground truth for "which model ran" and "did it fork" comes from the session
transcript and the result JSON, not from the model's self-report -- models
misreport their own identity. --session-id is pinned so the transcript can be
located deterministically afterwards.
"""

import argparse
import json
import os
import shutil
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
PROJECTS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "projects")


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-probes")


def find_transcript(session_id, since):
    """Locate ~/.claude/projects/<slug>/<session-id>.jsonl written by this run."""
    if not os.path.isdir(PROJECTS_DIR):
        return None
    for root, _dirs, files in os.walk(PROJECTS_DIR):
        if f"{session_id}.jsonl" in files:
            p = os.path.join(root, f"{session_id}.jsonl")
            if os.path.getmtime(p) >= since - 5:
                return p
    return None


def one_run(run, proj_src, workspace, timeout, extra_flags, salt):
    rid = f"{run['eval_name']}/{run['configuration']}"
    rundir = os.path.join(workspace, run["eval_name"], run["configuration"])
    proj = os.path.join(rundir, "project")
    outputs = os.path.join(rundir, "outputs")
    if os.path.exists(rundir):
        shutil.rmtree(rundir)
    os.makedirs(outputs, exist_ok=True)
    shutil.copytree(proj_src, proj)

    # Salted so a rerun never collides with a previous run's pinned session id.
    session_id = str(uuid.uuid5(NS, rid + salt))
    cmd = ["claude", "-p", run["prompt"],
           "--output-format", "json",
           "--session-id", session_id,
           "--model", run["model"],
           "--permission-mode", "acceptEdits"] + extra_flags

    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=proj, capture_output=True, text=True,
                              timeout=timeout, encoding="utf-8", errors="replace")
        stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        raw = e.stdout or ""
        stdout = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        stderr, rc = f"TIMEOUT after {timeout}s", -1
    elapsed = time.time() - started

    for fn, text in (("stdout.txt", stdout), ("stderr.txt", stderr)):
        with open(os.path.join(rundir, fn), "w", encoding="utf-8") as f:
            f.write(text or "")

    result = None
    try:
        result = json.loads(stdout)
        with open(os.path.join(rundir, "raw.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass

    wd = os.path.join(proj, "workdir")
    produced = []
    if os.path.isdir(wd):
        for fn in sorted(os.listdir(wd)):
            src = os.path.join(wd, fn)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(outputs, fn))
                produced.append(fn)

    tpath = find_transcript(session_id, started)
    if tpath:
        shutil.copy2(tpath, os.path.join(rundir, "transcript.jsonl"))

    tokens = 0
    if isinstance(result, dict):
        usage = result.get("usage") or {}
        tokens = sum(v for k, v in usage.items() if isinstance(v, int) and "token" in k)

    with open(os.path.join(rundir, "timing.json"), "w", encoding="utf-8") as f:
        json.dump({"total_tokens": tokens, "duration_ms": int(elapsed * 1000),
                   "total_duration_seconds": round(elapsed, 1)}, f, indent=2)
    with open(os.path.join(rundir, "run.json"), "w", encoding="utf-8") as f:
        json.dump({**run, "session_id": session_id, "returncode": rc,
                   "transcript": os.path.basename(tpath) if tpath else None,
                   "produced_files": produced, "elapsed_seconds": round(elapsed, 1)},
                  f, indent=2)

    # The project copy is only needed for its workdir, which is already captured.
    shutil.rmtree(proj, ignore_errors=True)
    return {"id": rid, "rc": rc, "elapsed": round(elapsed, 1),
            "files": produced, "transcript": bool(tpath)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iteration", type=int, choices=(1, 2, 3), required=True)
    ap.add_argument("--workdir", default=default_workdir())
    ap.add_argument("--only", help="substring filter on eval_name/configuration")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--salt", default="",
                    help="vary derived session ids so a rerun does not collide")
    ap.add_argument("--flag", action="append", default=[],
                    help="extra flag passed through to claude")
    args = ap.parse_args()

    proj_src = os.path.join(args.workdir, "probe-project")
    runs_path = os.path.join(args.workdir, f"runs{args.iteration}.json")
    if not os.path.isdir(proj_src) or not os.path.isfile(runs_path):
        raise SystemExit(f"missing probe project or run plan in {args.workdir}\n"
                         f"run: python build_probes.py --iteration {args.iteration}")

    runs = json.load(open(runs_path, encoding="utf-8"))
    if args.only:
        runs = [r for r in runs if args.only in f"{r['eval_name']}/{r['configuration']}"]
    workspace = os.path.join(args.workdir, f"iteration-{args.iteration}")
    os.makedirs(workspace, exist_ok=True)
    print(f"running {len(runs)} probe(s), {args.workers} at a time -> {workspace}\n", flush=True)

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one_run, r, proj_src, workspace, args.timeout, args.flag, args.salt)
                for r in runs]
        for fut in as_completed(futs):
            res = fut.result()
            results.append(res)
            print(f"  [{'ok ' if res['rc'] == 0 else 'ERR'}] {res['id']:<42} "
                  f"{res['elapsed']:>6.1f}s  files={res['files']}  "
                  f"transcript={res['transcript']}", flush=True)

    print(f"\ndone: {sum(1 for r in results if r['rc'] == 0)}/{len(results)} exited 0")


if __name__ == "__main__":
    main()
