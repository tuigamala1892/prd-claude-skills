#!/usr/bin/env python3
"""Refuse to overwrite an artefact that already exists (plan items 9 and 48, finding P16).

`/prd` Phase 8 has carried this guard as prose since the beginning:

    test -e docs/prd/[project-slug]/index.md && echo EXISTS
    If anything is already there, **stop and ask** ...

That is an instruction to a model, and this repository has converted five other prose guards
into programs for the same reason each time: the documented guard was ignored. A PRD is an hour
of someone's thinking, and a slug collision should never be the reason it disappears.

TWO SITUATIONS END UP HERE AND ONLY ONE IS SAFE

  resuming a PRD loaded in Initialization    writing back is the point       --resume, exit 0
  a new PRD that collides with a slug        the second destroys the first   exit 1, REFUSED

The script cannot tell those apart -- only the caller knows which one it is in -- so it refuses
by default and requires `--resume` to be stated. A guard whose safe path is the default is a
guard that gets taken by accident.

TWO ARTEFACTS, ONE GUARD

Item 48 found the identical hole on the CRD path: `/crd` was documented as stateless and wrote
`docs/crd/{slug}.md` with no pre-write check at all. It had simply not been caught by it yet.

So this takes a PRD DIRECTORY or a single FILE rather than growing a second script. That is
deliberate and it is this repository's most repeated lesson arriving again -- `keep_awake` was
written inside one caller and its own docstring recorded the identical failure it was written
for; item 60 was a rule added without removing what it contradicted. A fix belongs at the level
of the problem, and the problem here is "an artefact representing a long conversation is about
to be replaced", which was never PRD-specific.

USAGE

    check-writable.py <prd-dir|file> [--resume] [--quiet]

  exit 0  nothing would be lost: the target is empty, absent, or --resume was given
  exit 1  REFUSED, listing every file that would be replaced, with its size and age
  exit 2  usage error
"""

import argparse
import os
import sys
import time

# The three things `/prd` Phase 8 writes.
WRITES = ("index.md", "what-next.md", os.path.join("features", "*.md"))


def existing(target):
    """Every file the caller would replace, in the order a person would want to read them.

    A single file is its own answer: `/crd` writes one document, so there is no set to walk.
    A directory is a PRD, and the three things `/prd` Phase 8 writes are named rather than
    globbed -- a directory holding unrelated files is not a PRD about to be lost.
    """
    if os.path.isfile(target):
        return [target]
    if not os.path.isdir(target):
        return []
    prd_dir = target
    found = []
    for name in ("index.md", "what-next.md"):
        path = os.path.join(prd_dir, name)
        if os.path.isfile(path):
            found.append(path)
    features = os.path.join(prd_dir, "features")
    if os.path.isdir(features):
        for name in sorted(os.listdir(features)):
            if name.lower().endswith(".md"):
                found.append(os.path.join(features, name))
    return found


def describe(path, root):
    stat = os.stat(path)
    age_days = (time.time() - stat.st_mtime) / 86400
    when = f"{age_days:.0f}d ago" if age_days >= 1 else "today"
    return f"{os.path.relpath(path, root):<40} {stat.st_size:>7} bytes  {when}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", metavar="prd-dir|file",
                    help="a PRD directory (/prd) or a single artefact file (/crd)")
    ap.add_argument("--resume", action="store_true",
                    help="the caller has confirmed this is the artefact loaded at start-up")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    target = os.path.abspath(args.target)
    found = existing(target)
    name = os.path.basename(target)

    if not found:
        if not args.quiet:
            print(f"clear to write: {target} holds nothing that would be lost")
        return 0

    if args.resume:
        if not args.quiet:
            print(f"resuming {name}: {len(found)} file(s) will be written back")
        return 0

    root = os.path.dirname(target) or "."
    what = "a document" if os.path.isfile(target) else "a PRD"
    print(f"REFUSED: {name} already holds {what}. "
          f"{len(found)} file(s) would be replaced:", file=sys.stderr)
    for path in found:
        print(f"  {describe(path, root)}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Two projects with similar names produce the same slug, and the second silently "
          "destroys the first.", file=sys.stderr)
    print("Say what is about to be replaced, then either take a different slug or re-run "
          "with --resume once the user has confirmed this is the artefact they meant.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
