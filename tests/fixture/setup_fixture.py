"""Materialise the §5.1 test fixture, and verify the invariants afterwards.

    python tests/fixture/setup_fixture.py            # build the workspace
    python tests/fixture/setup_fixture.py --verify   # check it survived a run
    python tests/fixture/setup_fixture.py --clean    # remove and rebuild

The workspace is created OUTSIDE this repository and the script refuses to build
inside it. Finding F4 is "generated output leaked into the toolchain tree", and a
fixture that runs `/execute` inside the toolchain would be the worst possible case
of it -- `/execute` creates branches, merges and removes worktrees.

The target project is created as a git repository with **no remote**, on purpose.
That is the configuration finding F1 said `/execute` could not survive, so the
fixture reproduces it rather than working around it.

`--verify` compares against a baseline recorded at setup. The point is to make F2
falsifiable: if anything deletes or reinitialises the target's `.git`, the recorded
root commit will be gone and the check fails loudly, instead of the damage being
noticed later.
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET


def rmtree(path):
    """Remove a tree containing a git repository, on Windows too.

    Git marks objects under .git read-only, so a plain rmtree fails there. Doing this
    with ignore_errors=True would be worse than useless: it reports success, leaves the
    tree in place, and the next build then refuses because the directory still exists.
    """
    def clear_readonly(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if not os.path.exists(path):
        return
    try:                                     # onexc replaced onerror in 3.12
        shutil.rmtree(path, onexc=clear_readonly)
    except TypeError:
        shutil.rmtree(path, onerror=clear_readonly)
    if os.path.exists(path):
        raise SystemExit(f"could not remove {path} -- is a process holding it open?")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PRD_SRC = os.path.join(HERE, "prd")
SLUG = "link-shelf"


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-fixture")


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(args)}\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def guard(workdir):
    target = os.path.abspath(workdir)
    repo = os.path.abspath(REPO)
    if os.path.normcase(target) == os.path.normcase(repo) or \
            os.path.normcase(target).startswith(os.path.normcase(repo) + os.sep):
        raise SystemExit(
            f"refusing to build the fixture inside the repository.\n"
            f"  repo    : {repo}\n"
            f"  workdir : {target}\n"
            "/execute creates branches, merges and removes worktrees in its target. "
            "Pick a --workdir outside this tree, or omit it for the system temp dir.")


def validate_prd():
    """Fail fast if the fixture PRD is malformed -- /breakdown parses it as XML."""
    problems = []
    index = os.path.join(PRD_SRC, SLUG, "index.md")
    root = ET.parse(index).getroot()
    if root.tag != "prd":
        problems.append(f"index.md root element is <{root.tag}>, expected <prd>")
    if (root.findtext("meta/slug") or "").strip() != SLUG:
        problems.append("meta/slug does not match the directory name")

    feats = root.findall("features/feature")
    if not 2 <= len(feats) <= 4:
        problems.append(f"{len(feats)} features -- §5.1 asks for two or three")
    for f in feats:
        rel = f.get("file")
        if not rel:
            problems.append(f"feature {f.findtext('name')!r} has no file attribute")
            continue
        path = os.path.join(PRD_SRC, SLUG, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            problems.append(f"feature file missing: {rel}")
            continue
        froot = ET.parse(path).getroot()
        if froot.tag != "feature":
            problems.append(f"{rel} root is <{froot.tag}>, expected <feature>")
        if not froot.findall("acceptance-criteria/criterion"):
            problems.append(f"{rel} has no acceptance criteria")

    wn = ET.parse(os.path.join(PRD_SRC, SLUG, "what-next.md")).getroot()
    if (wn.findtext("status") or "").strip() != "in-progress":
        problems.append("what-next.md has no <status>in-progress</status> "
                        "-- /prd --resume greps for exactly that (F3)")

    if problems:
        raise SystemExit("fixture PRD is invalid:\n  " + "\n  ".join(problems))
    return len(feats)


def build(workdir):
    guard(workdir)
    n_features = validate_prd()

    if os.path.exists(workdir):
        raise SystemExit(f"{workdir} already exists -- pass --clean to rebuild")
    os.makedirs(workdir)

    docs = os.path.join(workdir, "docs", "prd")
    os.makedirs(docs)
    shutil.copytree(os.path.join(PRD_SRC, SLUG), os.path.join(docs, SLUG))

    # The target project: an existing repository, because /execute's preflight
    # requires one, with NO remote, because that is what F1 could not survive.
    app = os.path.join(workdir, "app")
    os.makedirs(app)
    with open(os.path.join(app, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Link Shelf\n\nFixture target project. Created by setup_fixture.py.\n")
    run(["git", "init", "-b", "main"], cwd=app)
    run(["git", "config", "user.name", "Fixture"], cwd=app)
    run(["git", "config", "user.email", "fixture@example.invalid"], cwd=app)
    run(["git", "add", "-A"], cwd=app)
    run(["git", "commit", "-q", "-m", "Initial commit"], cwd=app)

    root_commit = run(["git", "rev-parse", "HEAD"], cwd=app)
    remotes = run(["git", "remote"], cwd=app, check=False)

    baseline = {
        "workdir": workdir, "app": app, "slug": SLUG,
        "root_commit": root_commit,
        "remotes_at_setup": remotes.split() if remotes else [],
        "prd_index": os.path.join(docs, SLUG, "index.md"),
        "features": n_features,
    }
    with open(os.path.join(workdir, "fixture-baseline.json"), "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)

    print(f"fixture built at {workdir}\n")
    print(f"  PRD           : docs/prd/{SLUG}/index.md  ({n_features} features)")
    print(f"  target project: app/  (git repo, branch main, NO remote)")
    print(f"  root commit   : {root_commit[:12]}  <- --verify checks this survives\n")
    print("Run the §5.2 sequence from inside the workspace:\n")
    print(f"  cd {workdir}")
    print(f"  claude --plugin-dir {REPO}\n")
    print(f"  /breakdown docs/prd/{SLUG}/index.md --output-dir {os.path.join(workdir, 'app')}")
    print(f"  /execute docs/tasks/{SLUG} --project-path {os.path.join(workdir, 'app')}\n")
    print("Then: python tests/fixture/setup_fixture.py --verify")


def verify(workdir):
    bpath = os.path.join(workdir, "fixture-baseline.json")
    if not os.path.isfile(bpath):
        raise SystemExit(f"no baseline at {bpath} -- build the fixture first")
    b = json.load(open(bpath, encoding="utf-8"))
    app = b["app"]
    fails, notes = [], []

    # F2: the target repository must still be the same repository.
    if not os.path.isdir(os.path.join(app, ".git")):
        fails.append("F2: {app}/.git no longer exists -- something deleted it".format(app=app))
    else:
        known = subprocess.run(["git", "cat-file", "-e", b["root_commit"]],
                               cwd=app, capture_output=True).returncode == 0
        if not known:
            fails.append(f"F2: root commit {b['root_commit'][:12]} is gone -- "
                         "the repository was reinitialised, not merely modified")
        else:
            notes.append(f"root commit {b['root_commit'][:12]} intact")

    # F1: the run must not have required a remote.
    remotes = run(["git", "remote"], cwd=app, check=False).split()
    if remotes and not b["remotes_at_setup"]:
        notes.append(f"a remote was added during the run: {remotes} "
                     "(not a failure, but the fixture is no longer testing the "
                     "no-remote path)")
    else:
        notes.append("still no remote configured -- the no-remote path was exercised")

    # Did anything actually happen?
    tasks = os.path.join(workdir, "docs", "tasks", b["slug"])
    if os.path.isdir(tasks):
        n = sum(len(fs) for _r, _d, fs in os.walk(tasks))
        notes.append(f"tasks generated: {n} files under docs/tasks/{b['slug']}/")
    else:
        notes.append("no tasks generated yet -- /breakdown has not been run")

    commits = run(["git", "rev-list", "--count", "HEAD"], cwd=app, check=False)
    notes.append(f"target repo now has {commits} commit(s)")
    wt = run(["git", "worktree", "list"], cwd=app, check=False).splitlines()
    if len(wt) > 1:
        notes.append(f"{len(wt) - 1} worktree(s) still attached -- expected 0 after a "
                     "clean run; a preserved worktree means a task was abandoned")

    print("Fixture verification\n" + "=" * 60)
    for n in notes:
        print(f"  note  {n}")
    for f in fails:
        print(f"  FAIL  {f}")
    print("=" * 60)
    print("PASS -- fixture invariants hold" if not fails else f"{len(fails)} FAILURE(S)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workdir", default=default_workdir())
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--clean", action="store_true", help="remove the workspace first")
    args = ap.parse_args()

    if args.verify:
        return verify(args.workdir)
    guard(args.workdir)
    if args.clean and os.path.exists(args.workdir):
        rmtree(args.workdir)
        print(f"removed {args.workdir}")
    build(args.workdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
