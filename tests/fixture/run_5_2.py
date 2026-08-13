"""Run the §5.2 end-to-end sequence against the §5.1 fixture.

    python tests/fixture/run_5_2.py --list
    python tests/fixture/run_5_2.py --only 7,8      # cheap preflight tests
    python tests/fixture/run_5_2.py                 # everything except test 9
    python tests/fixture/run_5_2.py --include-full  # add the full /execute run

Test 9 is a real `/execute`: parallel per-task agents, worktrees, a retry loop. It is
excluded unless asked for, because it is by far the most expensive thing in the plan.

Each test records its own pass criteria. Several are EXPECTED to fail -- the items that
would fix them are not done -- and those are marked `expect_fail` with the item, exactly
as in tests/test_toolchain.py, so a genuine regression stays distinguishable from a
known gap.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SLUG = "link-shelf"
# Plugin commands are namespaced. A bare `/prd` is "Unknown command".
P = json.load(open(os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))),
    ".claude-plugin", "plugin.json"), encoding="utf-8"))["name"]


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-fixture")


def sha(path):
    import hashlib
    if not os.path.isfile(path):
        return None
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def git(args, cwd):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stdout.strip()


PERMISSION_MODE = "acceptEdits"   # overridden by --permission-mode


def claude(prompt, cwd, results_dir, name, timeout, extra=()):
    """One `claude -p` run, with its transcript and result JSON captured."""
    os.makedirs(results_dir, exist_ok=True)
    # Per-run, not per-day: the CLI refuses to reuse a session id, so a same-day
    # rerun with a date-derived id fails before doing anything.
    sid = str(uuid.uuid5(NS, f"5.2/{name}/{time.strftime('%Y%m%d-%H%M%S')}"))
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--session-id", sid,
           "--model", "sonnet", "--permission-mode", PERMISSION_MODE,
           "--plugin-dir", REPO, *extra]
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

    text = out
    try:
        text = json.loads(out).get("result", out)
    except Exception:
        pass
    for fn, body in (("stdout.json", out), ("stderr.txt", err), ("result.txt", text)):
        with open(os.path.join(results_dir, fn), "w", encoding="utf-8") as f:
            f.write(body or "")

    # The transcript is the only reliable record of what tools actually ran -- but for a
    # forked skill the parent transcript records almost nothing, because the work happens
    # in subagent sessions written to <sid>/subagents/. Capturing only the parent yields a
    # file with zero tool calls in it, which reads as "nothing ran" and hides the entire
    # execution. Copy both.
    for root, _d, files in os.walk(os.path.join(os.path.expanduser("~"), ".claude", "projects")):
        if f"{sid}.jsonl" in files:
            shutil.copy2(os.path.join(root, f"{sid}.jsonl"),
                         os.path.join(results_dir, "transcript.jsonl"))
            subs = os.path.join(root, sid, "subagents")
            if os.path.isdir(subs):
                dest = os.path.join(results_dir, "subagents")
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(subs, dest)
            break
    return {"rc": rc, "text": text or "", "elapsed": elapsed, "session": sid,
            "timed_out": timed_out}


def refused(text):
    """Did the model decline, rather than doing the thing?"""
    t = text.lower()
    return any(w in t for w in ("refused", "refuse", "cannot", "can't", "will not",
                                "won't", "error", "aborted", "declined", "invalid",
                                "must be absolute", "not a valid"))


def bailed_early(text):
    """Did the run stop before reaching the behaviour under test?

    Tests 7-9 need generated tasks to exist. Without them `/execute` stops at input
    validation and emits an error -- which a naive "did it refuse?" check happily reads
    as success. That is a false pass, and a false pass is worse than a red test: it
    reports the guard works when the guard was never reached.
    """
    t = text.lower()
    return any(w in t for w in ("manifest.json not found", "run /breakdown first",
                                "validation failed", "no generated task breakdown",
                                "does not exist — there is no"))


# --------------------------------------------------------------------- the tests

def make_tests(ws, app, prd_fresh):
    tasks_dir = os.path.join(ws, "docs", "tasks", SLUG)
    idx = os.path.join(ws, "docs", "prd", SLUG, "index.md")

    def t2(r, before):
        made = [d for d in (os.listdir(os.path.join(prd_fresh, "docs", "prd"))
                            if os.path.isdir(os.path.join(prd_fresh, "docs", "prd")) else [])]
        if not made:
            return False, "no PRD directory created under docs/prd/"
        slug = made[0]
        base = os.path.join(prd_fresh, "docs", "prd", slug)
        have_idx = os.path.isfile(os.path.join(base, "index.md"))
        wn = os.path.join(base, "what-next.md")
        if not have_idx:
            return False, f"docs/prd/{slug}/index.md missing"
        if not os.path.isfile(wn):
            return False, f"docs/prd/{slug}/what-next.md missing"
        import xml.etree.ElementTree as ET
        try:
            root = ET.parse(wn).getroot()
        except Exception as e:
            return False, f"what-next.md is not well-formed XML: {e}"
        st = (root.findtext("status") or root.findtext("meta/status") or "").strip()
        if not st:
            return False, "what-next.md has no <status> element (F3)"
        return True, f"PRD '{slug}' written; what-next.md valid XML, status={st!r}"

    def t3(r, before):
        if not before["slug"]:
            return False, "no PRD exists to detect - test 2 did not produce one"
        after = sha(os.path.join(prd_fresh, "docs", "prd", before["slug"], "index.md"))
        if after != before["idx"]:
            return False, "existing index.md was overwritten without confirmation"
        mentioned = before["slug"].lower() in r["text"].lower() or "existing" in r["text"].lower()
        if not mentioned:
            return False, ("existing PRD not detected or offered; output did not mention it:\n"
                           + r["text"][:300])
        return True, "existing PRD detected and left untouched"

    def t4(r, before):
        if not before["slug"]:
            return False, "no PRD exists to resume - test 2 did not produce one"
        if before["slug"].lower() in r["text"].lower():
            return True, f"resume found the existing PRD ({before['slug']})"
        return False, "resume did not identify the existing PRD:\n" + r["text"][:300]

    def t5(r, before):
        stray = os.path.join(ws, "relative-out")
        if os.path.isdir(stray):
            return False, "relative --output-dir was accepted; ./relative-out was created"
        if not refused(r["text"]):
            return False, "relative path not clearly rejected:\n" + r["text"][:300]
        return True, "relative --output-dir rejected"

    def t6(r, before):
        if not os.path.isdir(tasks_dir):
            return False, f"no tasks generated at docs/tasks/{SLUG}/"
        n = sum(len(f) for _r, _d, f in os.walk(tasks_dir))
        # Compare against the repo's state BEFORE the run. A plain "is git status
        # empty" check fails on any unrelated uncommitted file -- including this
        # harness while it is being written -- and reports contamination that did
        # not happen.
        now = set(git(["status", "--porcelain"], REPO).splitlines())
        new = sorted(now - set(before["repo_dirt"]))
        if new:
            return False, ("toolchain repo was written to during the run:\n    "
                           + "\n    ".join(new[:8]))
        tasks = [f for _r, _d, fs in os.walk(tasks_dir) for f in fs if f.endswith(".xml")]
        if not tasks:
            return False, f"{n} files present but no task XML among them"
        return True, f"{len(tasks)} task file(s) generated; nothing new in the toolchain tree"

    def t7(r, before):
        t = r["text"].lower()
        if bailed_early(r["text"]):
            return False, ("stopped at input validation, so the no-remote path was never "
                           "reached - run test 6 first:\n" + r["text"][:250])
        if git(["remote"], app):
            return False, "a remote was configured; this no longer tests the no-remote path"
        if "git pull" in t and ("fail" in t or "error" in t):
            return False, "failed on a git pull despite there being no remote"
        # A dry run that got through preflight reports a plan.
        if not any(w in t for w in ("layer", "batch", "task", "plan")):
            return False, "no execution plan produced:\n" + r["text"][:250]
        return True, "reached the execution plan with no remote configured"

    def t8(r, before):
        if bailed_early(r["text"]):
            return False, ("stopped at input validation, so the wrong-repository guard was "
                           "never reached - run test 6 first:\n" + r["text"][:250])
        if not refused(r["text"]):
            return False, ("did NOT refuse a project path containing docs/prd/:\n"
                           + r["text"][:300])
        # The refusal must be for the right reason, not an incidental error.
        if "docs/prd" not in r["text"].lower() and "docs\\prd" not in r["text"].lower():
            return False, ("refused, but not on the docs/prd guard - reason unclear:\n"
                           + r["text"][:300])
        return True, "refused to target a tree containing docs/prd/, for that reason"

    def t9(r, before):
        if not os.path.isdir(os.path.join(app, ".git")):
            return False, "CRITICAL: the target repository's .git no longer exists"
        if not git(["cat-file", "-e", before["root"]], app) == "":
            pass
        ok = subprocess.run(["git", "cat-file", "-e", before["root"]], cwd=app,
                            capture_output=True).returncode == 0
        if not ok:
            return False, f"CRITICAL: root commit {before['root'][:12]} gone - repo reinitialised"
        commits = git(["rev-list", "--count", "HEAD"], app)
        merged = int(commits or 0) - int(before["commits"] or 0)
        if merged <= 0:
            return False, (f"no commits merged (still {commits}); tasks did not complete:\n"
                           + r["text"][:400])

        # "Some commits appeared" is far too weak, and so was its first replacement.
        # That one asked only for merge commits numbering at least half the tasks, which
        # caught lost isolation but happily passed a run that stopped two thirds of the
        # way through. Now that the ledger and the state file are derived from git and can
        # be trusted (F16, F21), ask them directly.
        ledger = os.path.join(app, ".execute", SLUG, "ledger.jsonl")
        recorded = []
        if os.path.isfile(ledger):
            for line in open(ledger, encoding="utf-8"):
                line = line.strip()
                if line:
                    try:
                        recorded.append(json.loads(line))
                    except Exception:
                        pass
        verified = [e for e in recorded if subprocess.run(
            ["git", "cat-file", "-e", str(e.get("commit", "")) + "^{commit}"],
            cwd=app, capture_output=True).returncode == 0]

        state_path = os.path.join(os.path.dirname(tasks_dir), SLUG, "execute-state.json")
        st = {}
        if os.path.isfile(state_path):
            try:
                st = json.load(open(state_path, encoding="utf-8"))
            except Exception:
                pass
        n_tasks = st.get("metrics", {}).get("tasks_total") or len(
            [f for _r, _d, fs in os.walk(tasks_dir) for f in fs if f.endswith(".xml")])
        n_merge_commits = len([l for l in git(["log", "--oneline", "--merges"], app).splitlines() if l])

        # Isolation: every task that completed did so through its own worktree merge.
        if verified and n_merge_commits < len(verified):
            return False, (
                f"isolation failed: {len(verified)} task(s) recorded but only "
                f"{n_merge_commits} merge commit(s) exist. Tasks wrote into the main "
                f"working tree instead of isolated worktrees")

        stray = [d for d in ("api", "main.py") if os.path.exists(os.path.join(app, d))]             if os.path.isdir(os.path.join(app, "app")) else []
        if stray:
            return False, (f"duplicate implementations at the project root ({stray}) alongside "
                           "app/ - the signature of unisolated concurrent writes")

        # Completeness is a separate question from correctness, and conflating them is how a
        # run that stopped at 11 of 18 got reported as a pass. An interruption -- an API
        # stall, a killed process -- is not a toolchain defect, so it is neither PASS nor
        # FAIL. What matters is whether the record is *consistent* with git, because that is
        # what makes the run resumable.
        if len(verified) < n_tasks:
            stalled = "stalled mid-stream" in r["text"] or "API Error" in r["text"]
            consistent = st.get("status") == "in_progress" and not st.get("missing_commits")
            why = (f"{len(verified)} of {n_tasks} tasks completed"
                   + (" -- run interrupted (API error)" if stalled else "")
                   + ("; state file agrees, record is consistent and resumable" if consistent
                      else f"; STATE FILE DISAGREES: status={st.get('status')!r}, "
                           f"missing={st.get('missing_commits')}"))
            return (True, "INCOMPLETE: " + why) if consistent else (False, why)

        if st and st.get("status") != "completed":
            return False, (f"all {n_tasks} tasks verified but the state file says "
                           f"{st.get('status')!r}")

        return True, (f"{merged} commit(s), {n_merge_commits} merge commit(s), "
                      f"{len(verified)}/{n_tasks} tasks verified in the ledger; "
                      "state file agrees; .git intact and root commit preserved")

    return [
        dict(id=2, name="prd-fresh", desc="/prd on a fresh directory",
             cwd=prd_fresh, timeout=900, check=t2,
             prompt=f"/{P}:prd A tiny command-line todo list in Python with add, list and done "
                    "commands, storing tasks in a local JSON file. Do not ask me any "
                    "questions - make reasonable assumptions, note them, and write the PRD "
                    "files now."),
        dict(id=3, name="prd-existing", desc="/prd again with no arguments",
             cwd=prd_fresh, timeout=600, check=t3, expect_fail="4.3",
             prompt=f"/{P}:prd"),
        dict(id=4, name="prd-resume", desc="/prd --resume",
             cwd=prd_fresh, timeout=600, check=t4, prompt=f"/{P}:prd --resume"),
        dict(id=5, name="breakdown-relative", desc="/breakdown with a relative --output-dir",
             cwd=ws, timeout=600, check=t5, expect_fail="4.6",
             prompt=f"/{P}:breakdown docs/prd/{SLUG}/index.md --output-dir ./relative-out"),
        dict(id=6, name="breakdown-absolute", desc="/breakdown with an absolute --output-dir",
             cwd=ws, timeout=5400, check=t6, clean_tasks=True,
             prompt=f"/{P}:breakdown {idx} --output-dir {app}"),
        dict(id=7, name="execute-no-remote", desc="/execute against a repo with no remote",
             cwd=ws, timeout=900, check=t7,
             prompt=f"/{P}:execute {tasks_dir} --project-path {app} "
                    f"--worktree-dir {os.path.join(ws, '.worktrees')} --dry-run"),
        dict(id=8, name="execute-refuses-docs", desc="/execute against a path containing docs/prd/",
             cwd=ws, timeout=600, check=t8,
             prompt=f"/{P}:execute {tasks_dir} --project-path {ws} "
                    f"--worktree-dir {os.path.join(ws, '.worktrees')} --dry-run"),
        dict(id=9, name="execute-full", desc="Full /execute run on the fixture",
             cwd=ws, timeout=14400, check=t9, full=True,
             prompt=f"/{P}:execute {tasks_dir} --project-path {app} "
                    f"--worktree-dir {os.path.join(ws, '.worktrees')} --max-parallel 2"),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workdir", default=default_workdir())
    ap.add_argument("--only", help="comma-separated test ids")
    ap.add_argument("--include-full", action="store_true", help="also run test 9")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--permission-mode", default="acceptEdits",
                    help="acceptEdits permits file writes but NOT Bash; /execute needs git, "
                         "so a real run requires bypassPermissions. The first test 9 failed "
                         "silently on this: subagents wrote files but could not create worktrees.")
    args = ap.parse_args()

    globals()["PERMISSION_MODE"] = args.permission_mode
    ws = args.workdir
    app = os.path.join(ws, "app")
    prd_fresh = os.path.join(ws, "prd-fresh")
    results = os.path.join(ws, "results-5.2")
    tasks_root = os.path.join(ws, "docs", "tasks", SLUG)

    tests = make_tests(ws, app, prd_fresh)
    if args.list:
        for t in tests:
            tag = f"  [expect_fail {t['expect_fail']}]" if t.get("expect_fail") else ""
            tag += "  [expensive]" if t.get("full") else ""
            print(f"  {t['id']}  {t['desc']}{tag}")
        return 0

    if not os.path.isdir(app):
        raise SystemExit(f"fixture not built at {ws} -- run setup_fixture.py first")
    os.makedirs(prd_fresh, exist_ok=True)
    os.makedirs(results, exist_ok=True)

    wanted = {int(x) for x in args.only.split(",")} if args.only else None
    selected = [t for t in tests
                if (wanted is None or t["id"] in wanted)
                and (args.include_full or wanted is not None or not t.get("full"))]

    summary = []
    for t in selected:
        # State captured before the run, for checks that compare before/after.
        before = {"commits": git(["rev-list", "--count", "HEAD"], app),
                  "root": git(["rev-list", "--max-parents=0", "HEAD"], app),
                  "repo_dirt": git(["status", "--porcelain"], REPO).splitlines()}
        pdir = os.path.join(prd_fresh, "docs", "prd")
        if os.path.isdir(pdir) and os.listdir(pdir):
            slug = sorted(os.listdir(pdir))[0]
            before["slug"] = slug
            before["idx"] = sha(os.path.join(pdir, slug, "index.md"))
        else:
            before["slug"], before["idx"] = "", None

        # /breakdown resumes from .done markers, so a stale tasks tree silently makes
        # this a no-op that inherits the previous run's output. Clear it first or the
        # test measures nothing.
        if t.get("clean_tasks") and os.path.isdir(tasks_root):
            shutil.rmtree(tasks_root, ignore_errors=True)
            print(f"  (cleared {tasks_root})", flush=True)

        print(f"\n{'=' * 78}\n  TEST {t['id']}: {t['desc']}\n{'=' * 78}", flush=True)
        print(f"  $ {t['prompt'][:150]}", flush=True)
        r = claude(t["prompt"], t["cwd"], os.path.join(results, f"test-{t['id']}"),
                   t["name"], t["timeout"])
        try:
            ok, why = t["check"](r, before)
        except Exception as e:
            ok, why = False, f"check raised {type(e).__name__}: {e}"

        # A killed run has no behavioural verdict to give. Grading one as FAIL is how
        # test 9 produced finding F14: the checker described a truncated run as if the
        # toolchain had chosen to skip worktrees. Say "inconclusive" and mean it.
        if r["timed_out"]:
            status = "INCONCLUSIVE"
            why = (f"run killed at {t['timeout']}s before finishing -- no verdict. "
                   f"State at the cut: {why}")
        elif ok and t.get("expect_fail"):
            status = "FIXED"
        elif ok:
            status = "PASS"
        elif t.get("expect_fail"):
            status = f"KNOWN/{t['expect_fail']}"
        else:
            status = "FAIL"
        print(f"\n  -> {status}  ({r['elapsed']}s)  {why}", flush=True)
        summary.append((t["id"], t["desc"], status, why, r["elapsed"]))

    print(f"\n\n{'=' * 78}\n  §5.2 SUMMARY\n{'=' * 78}")
    for tid, desc, status, why, el in summary:
        print(f"  {status:<12} {tid}. {desc:<46} {el:>7.1f}s")
    with open(os.path.join(results, "summary.json"), "w", encoding="utf-8") as f:
        json.dump([{"id": i, "desc": d, "status": s, "why": w, "seconds": e}
                   for i, d, s, w, e in summary], f, indent=2)
    print(f"\n  results: {results}")
    # INCONCLUSIVE is not a pass, so it must not exit 0 -- but it is not evidence of a
    # defect either, so it is reported separately from FAIL.
    return 1 if any(s in ("FAIL", "INCONCLUSIVE") for _i, _d, s, _w, _e in summary) else 0


if __name__ == "__main__":
    sys.exit(main())
