"""Build the brownfield fixture the CRD half of the toolchain has never had.

§5.1 gave the greenfield path a fixture, and every finding fixed in this project came from
running against it. `/crd`, `/crd-context`, `/crd-investigate`, `/crd-impact-analysis` and
`/crd-context-update` have had only static checks -- so has `project-context-finalizer`,
wired in by item 4.10 and never executed. This is the missing half.

    python tests/fixture/setup_crd_fixture.py            # build
    python tests/fixture/setup_crd_fixture.py --clean    # rebuild from scratch
    python tests/fixture/setup_crd_fixture.py --verify   # is the target still intact?

What it makes, outside this repository:

    <workdir>/
      app/                  an existing FastAPI app: 17 files, 5 commits, NO remote,
                            8 passing tests, and no PROJECT.md
      change-request.md     prose from a stakeholder; turning it into a CRD is /crd's job

`/crd` and `/crd-context` both write *inside* `app/` -- `docs/crd/{slug}.md` and
`PROJECT.md` respectively -- so the workspace holds only the input.

The differences from §5.1 are the whole point. Greenfield starts from an empty repository;
brownfield starts from code that already works, has history, and has a test asserting the
behaviour a careless change would break.
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from crd_app_files import COMMITS, FILES  # noqa: E402

BASELINE = "crd-fixture-baseline.json"


def rmtree(path):
    """Windows marks objects under .git read-only, so a plain rmtree fails there."""
    def clear_readonly(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    if not os.path.exists(path):
        return
    try:
        shutil.rmtree(path, onexc=clear_readonly)
    except TypeError:
        shutil.rmtree(path, onerror=clear_readonly)
    assert not os.path.exists(path), f"failed to remove {path}"


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-crd-fixture")


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise SystemExit(f"{' '.join(args)} failed in {cwd}:\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def guard(workdir):
    """Never build inside this repository. /execute creates branches and removes worktrees
    in its target, and a CRD run also rewrites PROJECT.md in place."""
    target = os.path.abspath(workdir)
    repo = os.path.abspath(REPO)
    if os.path.normcase(target) == os.path.normcase(repo) or \
            os.path.normcase(target).startswith(os.path.normcase(repo) + os.sep):
        raise SystemExit(
            f"refusing to build the fixture inside the repository.\n"
            f"  repo    : {repo}\n"
            f"  workdir : {target}\n"
            "Pick a --workdir outside this tree, or omit it for the system temp dir.")


def build(workdir):
    guard(workdir)
    if os.path.exists(workdir):
        raise SystemExit(f"{workdir} already exists -- pass --clean to rebuild")
    os.makedirs(workdir)

    src = os.path.join(HERE, "crd", "change-request.md")
    shutil.copy2(src, os.path.join(workdir, "change-request.md"))
    # No docs/crd here: `/crd` writes to {project_path}/docs/crd/{slug}.md, inside the
    # target repository. An empty one at the workspace root was this fixture's first bug --
    # it looked like /crd had written to the wrong place when it had written to the right
    # one.

    app = os.path.join(workdir, "app")
    os.makedirs(app)
    run(["git", "init", "-b", "main"], cwd=app)
    run(["git", "config", "user.name", "Fixture"], cwd=app)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=app)

    # Lay the files down across several commits. A brownfield repository has history, and
    # /crd-investigate may reasonably read it; a single "Initial commit" would not be
    # brownfield at all.
    for n, message in enumerate(COMMITS):
        wrote = 0
        for rel, content, commit_n in FILES:
            if commit_n != n:
                continue
            path = os.path.join(app, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            wrote += 1
        assert wrote, f"commit {n} ({message}) would be empty"
        run(["git", "add", "-A"], cwd=app)
        run(["git", "commit", "-q", "-m", message], cwd=app)

    root_commit = run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=app)
    baseline = {
        "workdir": workdir,
        "app": app,
        "root_commit": root_commit,
        "head_at_setup": run(["git", "rev-parse", "HEAD"], cwd=app),
        "commits": int(run(["git", "rev-list", "--count", "HEAD"], cwd=app)),
        "files": len(FILES),
        "remotes_at_setup": run(["git", "remote"], cwd=app, check=False).split(),
        "change_request": os.path.join(workdir, "change-request.md"),
    }
    with open(os.path.join(workdir, BASELINE), "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)

    print(f"\nCRD fixture built at {workdir}\n")
    print(f"  target project : app/  ({baseline['commits']} commits, "
          f"{len(FILES)} files, NO remote)")
    print(f"  PROJECT.md     : absent -- producing it is /crd-context's job")
    print(f"  change request : change-request.md (prose, deliberately unstructured)")
    print(f"\nNext:")
    print(f"  /crd-context {app}")
    print(f"  /crd {os.path.join(workdir, 'change-request.md')} --project-path {app}\n")
    return baseline


def check_tests(app):
    """A brownfield fixture whose baseline is already broken cannot tell you whether a
    change request broke it. Only reports -- pytest may not be installed here."""
    py = sys.executable
    p = subprocess.run([py, "-m", "pytest", "-q"], cwd=app, capture_output=True, text=True)
    tail = (p.stdout or p.stderr or "").strip().splitlines()
    return p.returncode, (tail[-1] if tail else "(no output)")


def verify(workdir):
    """Is the target repository still the one we built? Mirrors §5.1's F2 guard."""
    path = os.path.join(workdir, BASELINE)
    if not os.path.isfile(path):
        raise SystemExit(f"no {BASELINE} in {workdir} -- build the fixture first")
    b = json.load(open(path, encoding="utf-8"))
    app = b["app"]
    fails, notes = [], []

    if not os.path.isdir(os.path.join(app, ".git")):
        fails.append(f"{app}/.git no longer exists -- something deleted it")
    else:
        ok = subprocess.run(["git", "cat-file", "-e", b["root_commit"]],
                            cwd=app, capture_output=True).returncode == 0
        if not ok:
            fails.append(f"root commit {b['root_commit'][:12]} is gone -- repo reinitialised")
        else:
            notes.append(f"root commit {b['root_commit'][:12]} intact")

        n = int(run(["git", "rev-list", "--count", "HEAD"], cwd=app, check=False) or 0)
        notes.append(f"{n} commit(s) on HEAD (was {b['commits']} at setup)")
        if n < b["commits"]:
            fails.append(f"history shrank: {n} commits, was {b['commits']}")

        remotes = run(["git", "remote"], cwd=app, check=False).split()
        if remotes != b["remotes_at_setup"]:
            notes.append(f"remotes changed: {b['remotes_at_setup']} -> {remotes}")

    pm = os.path.join(app, "PROJECT.md")
    notes.append(f"PROJECT.md {'present' if os.path.isfile(pm) else 'absent (not yet built)'}")

    for line in notes:
        print(f"  {line}")
    if fails:
        print("\nFAILED:")
        for f in fails:
            print(f"  {f}")
        return 1
    print("\nfixture intact")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--workdir", default=default_workdir())
    ap.add_argument("--clean", action="store_true", help="remove an existing fixture first")
    ap.add_argument("--verify", action="store_true", help="check the target is still intact")
    args = ap.parse_args()

    guard(args.workdir)
    if args.verify:
        return verify(args.workdir)
    if args.clean:
        rmtree(args.workdir)

    b = build(args.workdir)
    rc, summary = check_tests(b["app"])
    print(f"  baseline tests : {summary}")
    if rc != 0:
        print("\n  WARNING: the fixture's own tests do not pass. Fix that before running a\n"
              "  CRD against it -- otherwise a failure afterwards proves nothing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
