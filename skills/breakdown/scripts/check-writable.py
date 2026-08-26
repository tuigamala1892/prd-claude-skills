#!/usr/bin/env python3
"""Refuse to overwrite a PRD that already exists (plan item 9, finding P16).

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

USAGE

    check-writable.py <prd-dir> [--resume] [--quiet]

  exit 0  nothing would be lost: the directory is empty, absent, or --resume was given
  exit 1  REFUSED, listing every file that would be replaced, with its size and age
  exit 2  usage error
"""

import argparse
import os
import sys
import time

# The three things `/prd` Phase 8 writes.
WRITES = ("index.md", "what-next.md", os.path.join("features", "*.md"))


def existing(prd_dir):
    """Every file Phase 8 would replace, in the order a person would want to read them."""
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
    ap.add_argument("prd_dir")
    ap.add_argument("--resume", action="store_true",
                    help="the caller has confirmed this is the PRD loaded in Initialization")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    prd_dir = os.path.abspath(args.prd_dir)
    found = existing(prd_dir) if os.path.isdir(prd_dir) else []

    if not found:
        if not args.quiet:
            print(f"clear to write: {prd_dir} holds no PRD files")
        return 0

    if args.resume:
        if not args.quiet:
            print(f"resuming {os.path.basename(prd_dir)}: {len(found)} file(s) will be "
                  f"written back")
        return 0

    root = os.path.dirname(prd_dir) or "."
    print(f"REFUSED: {os.path.basename(prd_dir)} already holds a PRD. "
          f"{len(found)} file(s) would be replaced:", file=sys.stderr)
    for path in found:
        print(f"  {describe(path, root)}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Two projects with similar names produce the same slug, and the second silently "
          "destroys the first.", file=sys.stderr)
    print("Say what is about to be replaced, then either take a different slug or re-run "
          "with --resume once the user has confirmed this is the PRD they meant.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
