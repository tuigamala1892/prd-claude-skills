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

WHERE THE VALUE COMES FROM, AND WHY THERE ARE TWO PLACES (item 28)

Repository layout is a property of the **codebase**, not of a document about it, so
`architecture.md` owns it: item 28 puts `<repo-structure>` inside `<rules>`, beside the layer
graph and the test policy. The input document's own copy is the fallback, for the many PRDs
written before that file existed and for projects that never write one.

Resolution order, and it is a choice rather than a synchronisation (plan section 4.1):

  1. `{project-root}/architecture.md` -- authoritative when it declares the element
  2. the input document
  3. `single`

**A disagreement is reported, not refused.** A PRD saying `single` while `architecture.md` says
`monorepo` is what happens the first time a project writes the newer file, and refusing would
break a valid repository to punish a stale sentence. The project file wins and both values are
named, so the stale one is visible and can be deleted. What is never acceptable is preferring one
silently, which is the drift the ownership rule exists to prevent.

USAGE

    check-repo-structure.py <input-file> [--project-root DIR] [--quiet]

  <input-file>     a PRD index.md or a CRD document
  --project-root   where architecture.md lives. Default: the input file's directory,
                   walked up to the repository root

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


def find_architecture(start, explicit=None):
    """architecture.md at the project root. Walk up from the input, stopping at the repo root."""
    import os as _os
    if explicit:
        candidate = _os.path.join(_os.path.abspath(explicit), "architecture.md")
        return candidate if _os.path.isfile(candidate) else None
    cur = _os.path.abspath(start)
    if _os.path.isfile(cur):
        cur = _os.path.dirname(cur)
    for _ in range(6):
        candidate = _os.path.join(cur, "architecture.md")
        if _os.path.isfile(candidate):
            return candidate
        if _os.path.isdir(_os.path.join(cur, ".git")):
            break
        parent = _os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input_file")
    ap.add_argument("--project-root")
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
    doc_value = (m.group(1).lower() if m else None)

    arch_path = find_architecture(path, args.project_root)
    arch_value, disagree = None, None
    if arch_path:
        am = ELEMENT.search(open(arch_path, encoding="utf-8", errors="replace").read())
        if am:
            arch_value = am.group(1).lower()

    if arch_value and doc_value and arch_value != doc_value:
        disagree = (arch_value, doc_value)

    if arch_value:
        value, source = arch_value, "architecture.md"
    elif doc_value:
        value, source = doc_value, "the input document"
    else:
        value, source = "single", "defaulted (no <repo-structure> anywhere)"

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
        print(f"repo_structure={value}  [{source}]")
        if disagree:
            print(f"  DISAGREE: architecture.md says {disagree[0]!r} and the input document "
                  f"says {disagree[1]!r}.")
            print(f"  The project file wins -- layout is a property of the codebase, not of a "
                  f"document about it. Delete the stale one rather than keeping both in step.")
        if value == "monorepo":
            print("Tasks may declare <meta><cwd>; verification runs from there (item 54).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
