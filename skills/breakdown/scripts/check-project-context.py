#!/usr/bin/env python3
"""Report what the repository already knows about itself, before `/prd` asks (item 52, P34).

`commands/prd.md` mentions `PROJECT.md` zero times. `/crd` opens by finding it, comparing
`last-context-hash` against `HEAD`, and updating before anything else. So a greenfield PRD
authored inside a repository that already has a codebase, a `PROJECT.md` and an established
architecture notices none of it, and proceeds to ask what the tech stack should be.

**Greenfield describes the document, not the repository it lands in.** A PRD for a new product
inside an existing monorepo is ordinary, which is why this is a check rather than a `--greenfield`
flag: a flag can be missed by omission, and the answer to "is this greenfield?" in Phase 2 does
not tell you whether the directory is empty.

WHAT IT LOOKS FOR

  PROJECT.md          the descriptive artefact `/crd` maintains -- what the codebase IS
  architecture.md     the prescriptive one (item 25) -- what it must be. Absent until Phase 3,
                      and reported as absent rather than treated as an error
  last-context-hash   compared against HEAD, so stale context is named as stale

EXIT CODES, AND NEITHER IS A FAILURE

  0  no project context found. `/prd` asks from scratch, as it always has
  3  context found -- details on stdout. `/prd` must offer follow / extend / override rather
     than asking from scratch, and must not silently contradict what is already there
  2  usage error

`3` is deliberately not `1`. Finding context is the good case: it is information the interview
should use, not a problem to report. A PRD is never refused for this -- refusing to let someone
write a PRD because their repository has a README would be absurd -- so the exit code carries a
branch, not a verdict.

USAGE

    check-project-context.py [project-root] [--quiet]
"""

import argparse
import os
import re
import subprocess
import sys

HASH_EL = re.compile(r"<last-context-hash>\s*(.*?)\s*</last-context-hash>", re.S)
NAME_EL = re.compile(r"<name>\s*(.*?)\s*</name>", re.S)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def head_of(root):
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"no such directory: {root}", file=sys.stderr)
        return 2

    project_md = os.path.join(root, "PROJECT.md")
    architecture_md = os.path.join(root, "architecture.md")
    found = []

    if os.path.isfile(project_md):
        text = read(project_md)
        m = NAME_EL.search(text)
        name = " ".join(m.group(1).split()) if m else "(unnamed)"
        stamped = HASH_EL.search(text)
        stamped = stamped.group(1) if stamped else None
        head = head_of(root)

        if stamped and head and stamped != head:
            state = f"STALE -- stamped {stamped[:12]}, HEAD is {head[:12]}"
        elif stamped and head:
            state = f"current as of {head[:12]}"
        elif not stamped:
            state = "carries no last-context-hash, so its freshness cannot be established"
        else:
            state = "present (not a git repository, so freshness cannot be compared)"
        found.append(("PROJECT.md", f"{name} -- {state}"))

    if os.path.isfile(architecture_md):
        found.append(("architecture.md", "present at the project root"))

    if not found:
        if not args.quiet:
            print(f"no PROJECT.md or architecture.md at {root}")
            print("Nothing to reconcile: ask about the stack and the architecture as usual.")
        return 0

    if not args.quiet:
        print(f"this repository already describes itself ({root}):")
        for name, detail in found:
            print(f"  {name:<16} {detail}")
        print()
        print("Do not ask about tech stack or architecture from scratch. Report what is here,")
        print("then offer: FOLLOW it, EXTEND it, or OVERRIDE it with a stated reason.")
        if any("STALE" in d for _n, d in found):
            print()
            print("PROJECT.md is stale. Say so: it describes an older commit, and a PRD written")
            print("against it may contradict code that already exists. `/crd` updates it.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
