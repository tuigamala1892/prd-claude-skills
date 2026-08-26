#!/usr/bin/env python3
"""Read `<repo-structure>` and refuse `multi-repo` before anything is generated (item 53, P36).

The assumption is already there and already enforced: `create-worktree.sh` will not accept a
subdirectory, and `/execute` tracks one `project_path`. But it fires during **batch execution**,
several phases after the layout was knowable. A project split repo-per-service currently gets a
layer plan, a manifest and a full task set before anything objects -- and then fails with a
message about worktrees that does not name the actual cause.

Refusing in Phase 1 converts a confusing late failure into an accurate early one.

THE VALUES

  single      one repository, one component. The default when absent, and what the
              toolchain has always assumed
  monorepo    one repository, several components. Supported; this is what makes
              `<meta><cwd>` (item 54) systematically producible rather than hand-authored
  multi-repo  several repositories. REFUSED here, with the reason

WHY MULTI-REPO IS REFUSED, AND WHY THAT IS NOT A GIT LIMITATION

A repo-per-service layout would create a worktree per repository, which is ordinary. What is
missing is the **data model**, not the mechanism:

  - a *target* model with dependencies, so a contract lands in one repository before its
    consumer in another
  - an explicit account of the window in which a change spanning three repositories has merged
    into one of them and not the others

That window is a property repo-per-service **chose** -- it is why those teams version contracts
-- so supporting it means modelling the window, not removing it. That is a scope decision, and it
is deliberately not taken. The refusal says what would be needed rather than implying the layout
is wrong.

USAGE

    check-repo-structure.py <input-file> [--quiet]

  <input-file>  a PRD index.md or a CRD document

  exit 0  `single` or `monorepo`. The value is printed as `repo_structure=<value>`
  exit 1  REFUSED -- `multi-repo`, or a value that is not one of the three
  exit 2  the file does not exist
"""

import argparse
import os
import re
import sys

VALUES = ("single", "monorepo", "multi-repo")
ELEMENT = re.compile(r"<repo-structure>\s*([a-z-]+)\s*</repo-structure>", re.I)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input_file")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    path = os.path.abspath(args.input_file)
    if not os.path.isfile(path):
        print(f"no such file: {path}", file=sys.stderr)
        return 2

    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    m = ELEMENT.search(text)
    # Absent is `single`, deliberately. Every PRD written before this element existed means one
    # repository, and defaulting to a refusal would break all of them to guard against a layout
    # none of them use.
    value = (m.group(1).lower() if m else "single")

    if value not in VALUES:
        print(f"REFUSED: <repo-structure> is {value!r}, which is not one of "
              f"{', '.join(VALUES)}.", file=sys.stderr)
        return 1

    if value == "multi-repo":
        print("REFUSED: <repo-structure>multi-repo</repo-structure> is out of scope, and this "
              "is the right phase to say so.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Not a git limitation: a worktree per repository is ordinary. What is missing is "
              "the data model.", file=sys.stderr)
        print("  - a target model with dependencies, so a contract lands in one repository "
              "before its consumer in another", file=sys.stderr)
        print("  - an account of the window where a change spanning three repositories has "
              "merged into one and not the others", file=sys.stderr)
        print("", file=sys.stderr)
        print("That window is a property repo-per-service chose -- it is why those teams "
              "version contracts -- so supporting it means modelling the window, not removing "
              "it. Nothing was generated.", file=sys.stderr)
        return 1

    if not args.quiet:
        source = "declared" if m else "defaulted (no <repo-structure> element)"
        print(f"repo_structure={value}  [{source}]")
        if value == "monorepo":
            print("Tasks may declare <meta><cwd>; verification runs from there (item 54).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
