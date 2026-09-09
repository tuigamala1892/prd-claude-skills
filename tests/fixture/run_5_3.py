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
import re
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
           "--plugin-dir", REPO, "--add-dir", REPO, "--add-dir", cwd]
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


def script(name, *args):
    """Run one of the toolchain's own validators and return (exit code, combined output).

    Every criterion below is asserted by RUNNING the script that owns the assertion, never by
    reading the run's own summary of itself. A step that grades its own homework is what the
    third crossing's `14/14` turned out to be until `ledger-status.sh` derived the number from
    git instead.
    """
    for d in (os.path.join(REPO, "skills", "breakdown", "scripts"),
              os.path.join(REPO, "schema", "scripts"),
              os.path.join(REPO, "skills", "execute", "scripts")):
        path = os.path.join(d, name)
        if os.path.isfile(path):
            p = subprocess.run([sys.executable, path, *args], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            return p.returncode, p.stdout + p.stderr
    raise SystemExit(f"no such script: {name}")


def crd_prompt(request, app):
    """/crd is an INTERVIEW, and one non-interactive turn is not one.

    The sixth crossing's first attempt ran the bare invocation and got back four clarifying
    questions and no document -- which is `/crd` behaving correctly, not failing. It asks what
    only a person can answer: whether archive and restore are dedicated endpoints, whether
    `include archived` is one shared parameter or one per endpoint, and what tier the change
    is. It then stops rather than inventing them, which is the rule it is built on.

    So the stakeholder's answers are supplied up front, exactly as a hand-driven session
    supplied them by typing.

    THE LINE THIS MUST NOT CROSS is item 21 run 2's finding: a fixture that explains the
    experiment to its subject produces a clean result that measures nothing. Everything below
    is a product decision a person owns. Nothing here says what SHAPE to write, which elements
    to fill, what to do about anything it is not told, or that an undecided question belongs
    in `<gaps>` -- if the run invents an answer instead of recording a gap, that is a finding,
    and this prompt has to leave room for it to be one.
    """
    return (
        f"/{P}:crd {request} --project-path {app}\n\n"
        "This is a non-interactive session, so here are the stakeholder's answers to the "
        "questions this interview normally asks, given up front:\n"
        "- Archive and restore are dedicated endpoints, not a flag on an update.\n"
        "- Seeing what is archived is a parameter on the existing list endpoint, not a "
        "separate view.\n"
        "- One shared parameter includes archived items across list, search and tag "
        "filtering.\n"
        "- This is must-have.\n"
        "- Hard delete stays exactly as it is, and stays available.\n"
        "Anything not covered above has not been decided.")


def build_steps(ws):
    app = os.path.join(ws, "app")
    tasks = os.path.join(app, "docs", "tasks", SLUG)
    worktrees = os.path.join(ws, ".worktrees")
    crd_dir = os.path.join(app, "docs", "crd")

    def find_crd():
        """Whatever /crd actually wrote. The slug is ITS decision, derived from the prose.

        Assuming SLUG here would turn `it chose a different name` into `it wrote nothing`,
        which is a different finding and the wrong one.
        """
        if not os.path.isdir(crd_dir):
            return os.path.join(crd_dir, f"{SLUG}.md")
        found = sorted(f for f in os.listdir(crd_dir) if f.endswith(".md"))
        return os.path.join(crd_dir, found[0] if found else f"{SLUG}.md")

    crd = find_crd()
    project_md = os.path.join(app, "PROJECT.md")
    request = os.path.join(ws, "change-request.md")

    def s1(r):
        """Step 1: /crd-context builds PROJECT.md from a codebase that has none."""
        if not os.path.isfile(project_md):
            return False, "no PROJECT.md was written"
        code, out = script("check-project-md.py", app, "--status")
        if code == 1:
            return False, "PROJECT.md is unusable:\n" + out[-300:]
        acode, aout = script("check-artefacts.py", project_md)
        if acode != 0:
            return False, "PROJECT.md is not the shape its schema describes:\n" + aout[-300:]
        stale = "stale=yes" in out
        feats = len(re.findall(r"<feature\b[^>]*\bid=", open(project_md, encoding="utf-8",
                                                             errors="replace").read()))
        # It must have written PROJECT.md and nothing else. A context step that also edits the
        # application has done more than it was asked to, and nothing downstream would say so.
        dirty = [ln[3:] for ln in git(["status", "--porcelain"], app).splitlines()
                 if "PROJECT.md" not in ln]
        if dirty:
            return False, f"the context step also changed {dirty}"
        return True, (f"PROJECT.md valid, {feats} feature(s), "
                      f"{'stale=yes' if stale else 'stale=no'}, nothing else touched")

    def s2(r):
        """Step 2: /crd turns stakeholder prose into a CRD.

        This is where item 79's `commands/crd.md` invocation of `check-status.py` first runs
        against a document a model wrote rather than one a fixture supplied.
        """
        crd = find_crd()
        if not os.path.isfile(crd):
            return False, f"no CRD at {os.path.relpath(crd, ws)}"
        text = open(crd, encoding="utf-8", errors="replace").read()

        acode, aout = script("check-artefacts.py", crd)
        if acode != 0:
            return False, "the CRD is not the shape schema-6 describes:\n" + aout[-300:]

        # P58's assertion, on this path, against a real document for the first time.
        scode, sout = script("check-status.py", crd)
        if scode != 0:
            return False, "its <gaps> do not survive the check /crd now runs:\n" + sout[-300:]

        rcode, rout = script("check-references.py", crd, "--project-path", app)
        if rcode != 0:
            return False, "its references do not resolve:\n" + rout[-400:]

        fcode, fout = script("select-features.py", crd)
        if fcode != 0:
            return False, "the selector refuses it:\n" + fout[-300:]

        crit = re.findall(r'<criterion\b[^>]*\bpattern="([a-z-]+)"[^>]*\bpriority="(P[012])"',
                          text)
        if not crit:
            return False, "no <criterion> carries both `pattern` and `priority` (items 33, 46)"
        gaps = re.findall(r'<gap\b[^>]*\bkind="([a-z]+)"', text)
        sig = re.search(r'architecturally-significant[^>]*because="([a-z-]+)"', text)
        ages = len([ln for ln in sout.splitlines() if "AGE" in ln])
        return True, (f"{len(crit)} EARS criteria, {len(gaps)} gap(s) ({ages} aged by the new "
                      f"check), significance {sig.group(1) if sig else 'not declared'}")

    def s3(r):
        """Step 3: /breakdown turns the CRD into tasks.

        This is where P62's `{document}` first reaches a live run. Handed the CRD's DIRECTORY
        instead of the file, `check-coverage.py` exits 2 with `no index.md` and
        `check-references.py` reports `0 references checked` -- so the run's own text is checked
        for that signature as well as the artefacts being checked for correctness.
        """
        crd = find_crd()
        manifest = os.path.join(tasks, "manifest.json")
        if not os.path.isfile(manifest):
            return False, f"no manifest at {os.path.relpath(manifest, ws)}"
        n = len([f for _r, _d, fs in os.walk(tasks) for f in fs if f.endswith(".xml")])
        if not n:
            return False, "a manifest with no task files"

        if "no index.md" in r["text"]:
            return False, ("the run was handed the CRD's DIRECTORY, not the file -- P62's "
                           "failure, live")

        ccode, cout = script("check-coverage.py", crd, tasks)
        if ccode != 0:
            return False, "the tasks do not cover the CRD:\n" + cout[-400:]

        gcode, gout = script("check-gate.py", crd, tasks, "--project-path", app)
        if "COULD NOT CHECK" in gout:
            return False, "the gate could not make an assertion:\n" + gout[-400:]

        layers = sorted({d for d in os.listdir(tasks)
                         if os.path.isdir(os.path.join(tasks, d))})
        if "0-setup" in layers:
            return False, "a brownfield run produced 0-setup, which scaffolds nothing"
        findings = [ln for ln in gout.splitlines() if ln.strip().startswith(("1 ", "2 ", "3 "))]
        return True, (f"{n} task(s) in {layers}, coverage OK, gate: "
                      + "; ".join(f.strip() for f in findings))

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
        dict(id=1, name="crd-context", desc="/crd-context builds PROJECT.md from the codebase",
             cwd=ws, timeout=1800, check=s1,
             prompt=f"/{P}:crd-context {app}"),
        dict(id=2, name="crd", desc="/crd turns the stakeholder prose into a CRD",
             cwd=ws, timeout=1800, check=s2, prompt=crd_prompt(request, app)),
        dict(id=3, name="breakdown", desc="/breakdown turns the CRD into tasks",
             cwd=ws, timeout=3600, check=s3,
             prompt=lambda: f"/{P}:breakdown {find_crd()} --project-path {app}"),
        dict(id=4, name="execute", desc="/execute the CRD tasks into the brownfield app",
             cwd=ws, timeout=5400, check=s4,
             prompt=f"/{P}:execute {tasks} --project-path {app} "
                    f"--worktree-dir {worktrees} --max-parallel 2"),
    ]



def checkout_guard(phase):
    """Item 78: a live run must not write into the toolchain checkout (P57).

    Every harness here verifies the TARGET and none looked at the plugin, which is how a run
    left `skills/execute/preflight_err.txt` behind unnoticed. `--snapshot` before, `--check`
    after; residue is named and never deleted, because it is evidence.
    """
    import subprocess as _sp, sys as _sys, os as _os
    script = _os.path.join(REPO, "tests", "checkout-clean.py")
    p = _sp.run([_sys.executable, script, f"--{phase}"], capture_output=True, text=True,
                encoding="utf-8", errors="replace")
    if phase == "check" and p.returncode == 1:
        print(p.stderr.rstrip(), file=_sys.stderr)
    return p.returncode

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
    checkout_guard("snapshot")   # item 78: the plugin must be unchanged by this run

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
        shown = s["prompt"]() if callable(s["prompt"]) else s["prompt"]
        print(f"  $ {shown}\n", flush=True)
        prompt = s["prompt"]() if callable(s["prompt"]) else s["prompt"]
        r = claude(prompt, s["cwd"], os.path.join(results, f"step-{s['id']}"),
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
    dirty = checkout_guard("check")   # item 78: did the run write into the plugin?
    return 0 if all(o[2] == "PASS" for o in outcomes) and dirty == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
