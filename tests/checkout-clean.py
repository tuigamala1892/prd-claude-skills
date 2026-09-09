#!/usr/bin/env python3
"""The toolchain checkout is unchanged by a live run (plan item 78, finding P57).

A run's deliverables belong to its target. **Nothing belongs in the plugin**, which is shared by
every project that loads it, so a file left there outlives the run and belongs to no project.

WHY THIS EXISTS RATHER THAN A RULE IN A SKILL

Step 4 of the fifth crossing wrote `skills/execute/preflight_err.txt` and `resolve_err.txt` into
the checkout. **No instruction asked for it**: no SKILL.md in the execute tree contains a `2>`
redirect and none names `_err.txt`. The model invented a stderr capture, wrote it to a *relative*
path, and the path resolved inside the plugin.

`/execute` now says where scratch goes. That is prose, and P16 is this plan's finding about prose
-- so this is the exit code beside it. The rule and the evidence are different jobs (item 4.13).

WHAT IT IS NOT

**It does not clean up.** The files are evidence of what a run did, and a harness that tidied them
away would hand the next person the same surprise with no trace. It names them and fails.

**It is not a test of the target.** Every live harness already verifies the target project; none
of them looked at the checkout, which is how this went unnoticed. `dirty-guard.sh` guards
`git checkout --` during a mutation round -- a different moment entirely.

USAGE

    checkout-clean.py                 # compare against a snapshot taken earlier, or just report
    checkout-clean.py --snapshot      # record the checkout's state before a run
    checkout-clean.py --check         # fail if the run changed anything the snapshot did not have

  exit 0  the checkout is as the snapshot left it
  exit 1  a run wrote into the toolchain; every path is named
  exit 2  no snapshot to compare against, or git could not be read
"""

import argparse
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(REPO, ".git", "checkout-clean.json")


def porcelain():
    """Every path git considers changed or untracked, as a set. `.git/` is excluded by git."""
    p = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(f"REFUSED: git status failed: {p.stderr.strip()[:200]}", file=sys.stderr)
        raise SystemExit(2)
    out = set()
    for line in p.stdout.splitlines():
        if len(line) > 3:
            out.add(line[3:].strip().strip('"'))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--snapshot", action="store_true", help="record the state before a run")
    g.add_argument("--check", action="store_true", help="fail if a run added anything")
    args = ap.parse_args()

    now = porcelain()

    if args.snapshot:
        os.makedirs(os.path.dirname(SNAP), exist_ok=True)
        with open(SNAP, "w", encoding="utf-8", newline="\n") as f:
            json.dump(sorted(now), f, indent=2)
        print(f"checkout snapshot: {len(now)} pre-existing change(s) recorded")
        return 0

    if not args.check:
        for path in sorted(now):
            print(f"  {path}")
        print(f"{len(now)} changed or untracked path(s) in the checkout")
        return 0

    if not os.path.isfile(SNAP):
        print("REFUSED: no snapshot to compare against. Run --snapshot before the run, or this "
              "check cannot tell a run's residue from work already in progress.", file=sys.stderr)
        return 2

    before = set(json.load(open(SNAP, encoding="utf-8")))
    added = sorted(now - before)
    if not added:
        print("checkout clean: the run added nothing to the toolchain")
        return 0

    print(f"REFUSED: a run wrote {len(added)} path(s) into the toolchain checkout:",
          file=sys.stderr)
    for path in added:
        print(f"  {path}", file=sys.stderr)
    print("\nA run's output belongs to its target. The plugin is shared by every project that "
          "loads it, so a file left here outlives this run and belongs to no project -- which is "
          "F4, and item 78 is why this check exists. `/execute` names the directory scratch may "
          "use; a relative redirect is the defect, because a skill may not assume its cwd.\n"
          "These are NOT deleted: they are evidence of what the run did.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
