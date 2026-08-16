"""Run the §5.3 brownfield sequence against the CRD fixture.

    python tests/fixture/run_5_3.py --list
    python tests/fixture/run_5_3.py --only 4          # just /execute
    python tests/fixture/run_5_3.py                   # all four steps

§5.3 was originally driven by hand, one `claude -p` at a time, with the results read out of
the fixture afterwards. That worked once and is not repeatable: the prompts lived in a
terminal history, and the pass criteria lived in someone's head. This is the same thing as a
program, so a re-run after a fix means one command and the criteria are checked rather than
recalled.

IT IS STATEFUL, AND THAT MATTERS

Each step consumes the previous step's output from the same fixture, exactly as a real
brownfield workflow would. Step 4 in particular *cannot* be re-run against a tree where it has
already succeeded -- the ledger is verified against git, so every task is skipped and the run
correctly does nothing. `--reset-to <ref>` puts the app back to a step's starting state first.

`--permission-mode bypassPermissions` is required for step 4. `acceptEdits` permits file
writes but not `Bash`, and `/execute` needs git; the first §5.2 test 9 failed for exactly that
reason and the failure was misattributed to the toolchain (F14, withdrawn).
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SLUG = "archive-links"
P = json.load(open(os.path.join(REPO, ".claude-plugin", "plugin.json"),
                   encoding="utf-8"))["name"]


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-crd-fixture")


def git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout.strip()


PERMISSION_MODE = "bypassPermissions"


def claude(prompt, cwd, results_dir, name, timeout):
    """One `claude -p` run, with its transcript and result JSON captured."""
    os.makedirs(results_dir, exist_ok=True)
    sid = str(uuid.uuid5(NS, f"5.3/{name}/{time.strftime('%Y%m%d-%H%M%S')}"))
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--session-id", sid,
           "--model", "sonnet", "--permission-mode", PERMISSION_MODE,
           "--plugin-dir", REPO]
    started = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        out, err, rc = p.stdout, p.stderr, p.returncode
        timed_out = False
    except subprocess.TimeoutExpired as e:
        raw = e.stdout or ""
        out = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        err, rc = f"TIMEOUT after {timeout}s", -1
        timed_out = True
    elapsed = round(time.time() - started, 1)

    text, cost = out, None
    try:
        data = json.loads(out)
        text = data.get("result", out)
        cost = data.get("total_cost_usd")
    except Exception:
        data = {"raw": out}

    with open(os.path.join(results_dir, "stdout.json"), "w", encoding="utf-8") as f:
        f.write(out or "")
    with open(os.path.join(results_dir, "stderr.txt"), "w", encoding="utf-8") as f:
        f.write(err or "")
    with open(os.path.join(results_dir, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt)
    with open(os.path.join(results_dir, "session-id.txt"), "w", encoding="utf-8") as f:
        f.write(sid)

    return {"text": text or "", "rc": rc, "elapsed": elapsed, "cost": cost,
            "timed_out": timed_out, "sid": sid}


def build_steps(ws):
    app = os.path.join(ws, "app")
    tasks = os.path.join(app, "docs", "tasks", SLUG)
    worktrees = os.path.join(ws, ".worktrees")

    def ledger_status(expected):
        script = os.path.join(REPO, "skills", "execute", "scripts", "ledger-status.sh")
        p = subprocess.run(["sh", script, app, SLUG, str(expected)],
                           capture_output=True, text=True)
        try:
            return json.loads(p.stdout)
        except Exception:
            return {}

    def s4(r):
        """Step 4: /execute the generated tasks into the brownfield app."""
        n_tasks = len([f for _r, _d, fs in os.walk(tasks) for f in fs
                       if f.endswith(".xml")])
        if not n_tasks:
            return False, "no task files -- run step 3 first"

        st = ledger_status(n_tasks)
        verified = st.get("verified_tasks", [])
        merges = len(git(["log", "--merges", "--oneline"], app).splitlines())

        if st.get("missing"):
            return False, f"ledger names commits that do not exist: {st['missing']}"
        if len(verified) < n_tasks:
            return False, (f"{len(verified)} of {n_tasks} tasks verified in the ledger; "
                           f"{merges} merge commit(s)")
        if merges < n_tasks:
            return False, (f"ledger says {len(verified)} but git holds only {merges} merge "
                           f"commit(s) -- one per task is the criterion")

        # The trap. The change request asked for archiving *alongside* delete; a change that
        # removed hard delete did more than it was asked to.
        t = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=app,
                           capture_output=True, text=True)
        if "test_delete_is_permanent" not in subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=app,
                capture_output=True, text=True).stdout:
            return False, "test_delete_is_permanent is gone -- the trap was sprung"
        if " failed" in t.stdout:
            return False, "the application's own tests fail:\n" + t.stdout[-400:]

        passed = ""
        for line in t.stdout.splitlines():
            if "passed" in line:
                passed = line.strip()

        # F23/F24: the finalizer's output must parse, and must carry a real hash.
        chk = subprocess.run(
            [sys.executable, os.path.join(REPO, "skills", "execute", "scripts",
                                          "check-project-md.py"), app, "--status"],
            capture_output=True, text=True)
        proj = os.path.join(app, "PROJECT.md")
        hash_line = ""
        if os.path.isfile(proj):
            for line in open(proj, encoding="utf-8", errors="replace"):
                if "last-context-hash" in line:
                    hash_line = line.strip()
                    break
        if "current-HEAD" in hash_line or "{" in hash_line:
            return False, f"F24 is back: last-context-hash is a placeholder -- {hash_line}"
        if chk.returncode == 1:
            return False, ("PROJECT.md is unusable after the finalizer ran:\n"
                           + (chk.stdout + chk.stderr)[-400:])

        stale = "stale=yes" in chk.stdout
        note = ("; context reads STALE immediately after being written (F24's off-by-one)"
                if stale else "; context reads current")
        return True, (f"{len(verified)}/{n_tasks} verified, {merges} merge commit(s), "
                      f"{passed}, trap held{note}")

    return [
        dict(id=4, name="execute", desc="/execute the CRD tasks into the brownfield app",
             cwd=ws, timeout=5400, check=s4,
             prompt=f"/{P}:execute {tasks} --project-path {app} "
                    f"--worktree-dir {worktrees} --max-parallel 2"),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workdir", default=default_workdir())
    ap.add_argument("--only", help="comma-separated step ids")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--permission-mode", default="bypassPermissions")
    ap.add_argument("--reset-to", metavar="REF",
                    help="git reset --hard the app to REF and clear the ledger first")
    args = ap.parse_args()

    globals()["PERMISSION_MODE"] = args.permission_mode
    ws = os.path.abspath(args.workdir)
    app = os.path.join(ws, "app")
    steps = build_steps(ws)

    if args.list:
        for s in steps:
            print(f"  {s['id']}  {s['desc']}")
        return 0

    if not os.path.isdir(app):
        print(f"no fixture at {app} -- run setup_crd_fixture.py first", file=sys.stderr)
        return 2

    if args.reset_to:
        print(f"resetting {app} to {args.reset_to} and clearing the ledger")
        subprocess.run(["git", "-C", app, "reset", "--hard", "-q", args.reset_to])
        subprocess.run(["git", "-C", app, "clean", "-fdq", "-e", ".execute"])
        import shutil
        shutil.rmtree(os.path.join(app, ".execute"), ignore_errors=True)

    want = {int(x) for x in args.only.split(",")} if args.only else None
    results = os.path.join(ws, "results-5.3")

    outcomes = []
    for s in steps:
        if want and s["id"] not in want:
            continue
        print(f"\n{'=' * 78}\n  STEP {s['id']}: {s['desc']}\n{'=' * 78}")
        print(f"  $ {s['prompt']}\n", flush=True)
        r = claude(s["prompt"], s["cwd"], os.path.join(results, f"step-{s['id']}"),
                   s["name"], s["timeout"])
        ok, why = s["check"](r)
        status = "PASS" if ok else ("TIMEOUT" if r["timed_out"] else "FAIL")
        cost = f", ${r['cost']:.2f}" if r.get("cost") else ""
        print(f"\n  -> {status}  ({r['elapsed']}s{cost})  {why}")
        outcomes.append((s["id"], s["desc"], status, why))

    print(f"\n{'=' * 78}\n  §5.3 SUMMARY\n{'=' * 78}")
    for i, desc, status, why in outcomes:
        print(f"  {status:<8} {i}. {desc}")
        print(f"           {why}")
    print(f"\n  results: {results}")
    return 0 if all(o[2] == "PASS" for o in outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
