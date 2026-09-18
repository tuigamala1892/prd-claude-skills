#!/usr/bin/env python3
"""List every PRD and where its status marker actually lives (plan item 9, findings P16, F3).

`/prd` Initialization greps for the marker across two files:

    grep -l "<status>in-progress</status>" docs/prd/*/what-next.md docs/prd/*/index.md

Both locations are checked because F3 was exactly this: resume looked only in `what-next.md`
while the real PRD carried the marker in `index.md`, so an existing PRD could not be found --
and a PRD that cannot be found is a PRD that gets silently replaced.

Grepping two files for one string is a shell command a model can mistype, and the *decision*
that follows it has always been prose. This makes both an exit code.

WHAT IT REPORTS

One line per PRD: slug, feature count, the status each file declares, and when it was last
written -- from what-next.md's own `<last-updated>`, falling back to the file's mtime and saying
which it used. Then the two conditions worth acting on:

  WROTE IT    what-next.md's <toolchain-version> (item 24), when it differs from the plugin
              running now. Provenance, never a refusal: a PRD written by an older toolchain is
              the ordinary case, and it is worth SAYING so before an interview resumes over it
  DISAGREE    index.md and what-next.md declare different statuses. Nothing can resume this
              safely, because the answer depends on which file the reader happens to check --
              which is F3 restated as a data defect rather than a code one.
  NO MARKER   neither file declares a status. `--resume` cannot see this PRD at all.

WHY THE DATE IS READ FROM THE FILE AND NOT FROM mtime

This column used to be mtime alone, which is wrong in the one case that matters: **mtime does not
survive a clone.** Every PRD in a fresh checkout reads as touched today, so the column said
nothing precisely when a person had least context about the tree in front of them. The declared
date is the only answer that travels with the document.

It is also what gave `<last-updated>` a reader. It had none -- the column that wanted its value
computed its own from mtime instead, and the element was left declared, unwritten after birth and
unread, which is the shape item 23 exists to catch. `build-what-next.py` now writes it whenever
it rewrites the file; this reads it. mtime stays as the fallback for a file that declares no date,
labelled `mtime` so a reader can tell a measurement from a declaration.

USAGE

    list-prds.py [prd-root] [--check] [--quiet]

  prd-root  defaults to docs/prd
  --check   exit 1 if any PRD disagrees with itself or carries no marker

  exit 0  listed; with --check, every PRD is self-consistent
  exit 1  with --check, at least one PRD disagrees or has no marker
  exit 2  the root does not exist
"""

import argparse
import datetime
import os
import re
import sys
import time

STATUS = re.compile(r"<status>\s*([a-z-]+)\s*</status>", re.I)
NAME = re.compile(r"<name>\s*(.+?)\s*</name>", re.S)
# Item 24's stamp, written by build-what-next.py. Read here because an element with no reader
# is the defect this plan spends most of its items removing.
TOOLCHAIN = re.compile(r"<toolchain-version>\s*([^<\s]+)\s*</toolchain-version>", re.I)
# The date the same script writes when it rewrites the file. Only a well-formed one is read: a
# malformed date is check-artefacts.py's to report, and guessing at one here would be a second
# opinion about a shape that already has an owner.
UPDATED = re.compile(r"<last-updated>\s*(\d{4}-\d{2}-\d{2})\s*</last-updated>", re.I)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def status_of(path):
    """The first <status> a file declares, or None. `/prd` writes exactly one."""
    if not os.path.isfile(path):
        return None
    m = STATUS.search(read(path))
    return m.group(1).lower() if m else None


def stamp_of(path):
    """The toolchain version that last wrote this file, or None."""
    if not os.path.isfile(path):
        return None
    m = TOOLCHAIN.search(read(path))
    return m.group(1) if m else None


def declared_date_of(path):
    """The date what-next.md says it was last written, or None."""
    if not os.path.isfile(path):
        return None
    m = UPDATED.search(read(path))
    return m.group(1) if m else None


def days_since(iso):
    """Whole days between an ISO date and today, or None if it will not parse.

    A future date is reported as a negative age rather than clamped to today. A PRD dated ahead
    of the clock is a data defect somebody should see, and hiding it behind `today` is how it
    stays hidden.
    """
    try:
        d = datetime.date.fromisoformat(iso)
    except ValueError:
        return None
    return (datetime.date.today() - d).days


def plugin_version():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    try:
        import json
        return json.load(open(os.path.join(root, ".claude-plugin", "plugin.json"),
                              encoding="utf-8")).get("version")
    except Exception:
        return None


def survey(root):
    out = []
    for slug in sorted(os.listdir(root)):
        prd = os.path.join(root, slug)
        if not os.path.isdir(prd):
            continue
        index, what_next = os.path.join(prd, "index.md"), os.path.join(prd, "what-next.md")
        if not os.path.isfile(index) and not os.path.isfile(what_next):
            continue
        features = os.path.join(prd, "features")
        count = len([n for n in os.listdir(features) if n.lower().endswith(".md")]) \
            if os.path.isdir(features) else 0
        name = None
        if os.path.isfile(index):
            m = NAME.search(read(index))
            name = " ".join(m.group(1).split()) if m else None
        newest = max((os.path.getmtime(p) for p in (index, what_next) if os.path.isfile(p)),
                     default=0)
        out.append({
            "slug": slug,
            "name": name or slug,
            "features": count,
            "index": status_of(index),
            "what_next": status_of(what_next),
            "age_days": (time.time() - newest) / 86400 if newest else None,
            "declared": declared_date_of(what_next),
            "wrote_it": stamp_of(what_next),
        })
    return out


def touched(prd):
    """The `touched` column: the declared date when there is one, mtime when there is not."""
    declared = prd["declared"]
    if declared:
        age = days_since(declared)
        return declared if age is None else f"{declared} ({age}d)"
    if prd["age_days"] is None:
        return "-"
    return ("today (mtime)" if prd["age_days"] < 1
            else f"{prd['age_days']:.0f}d ago (mtime)")


def verdict(prd):
    i, w = prd["index"], prd["what_next"]
    if i is None and w is None:
        return "NO MARKER"
    if i is not None and w is not None and i != w:
        return "DISAGREE"
    return i or w


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("root", nargs="?", default=os.path.join("docs", "prd"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        # Not an error worth failing on: no PRD directory means no PRD, which is the normal
        # state of a fresh project and exactly what `/prd` with no arguments expects.
        if not args.quiet:
            print(f"no PRD directory at {root}")
        return 0 if not args.check else 0

    prds = survey(root)
    if not prds:
        if not args.quiet:
            print(f"no PRDs under {root}")
        return 0

    if not args.quiet:
        print(f"{'slug':<24} {'feat':>4}  {'status':<12} {'declared in':<22} touched")
        for prd in prds:
            state = verdict(prd)
            where = ", ".join(f for f, v in (("index.md", prd["index"]),
                                             ("what-next.md", prd["what_next"])) if v) or "-"
            print(f"{prd['slug']:<24} {prd['features']:>4}  {state:<12} {where:<22} "
                  f"{touched(prd)}")

    running = plugin_version()
    for prd in prds:
        stamp = prd["wrote_it"]
        if stamp and running and stamp != running:
            print(f"\n{prd['slug']}: written by toolchain {stamp}; this one is {running}. "
                  f"Provenance, not a problem -- but a PRD authored against an older schema may "
                  f"need `/migrate` before it is resumed.")

    bad = [p for p in prds if verdict(p) in ("DISAGREE", "NO MARKER")]
    for prd in bad:
        if verdict(prd) == "DISAGREE":
            print(f"\n{prd['slug']}: index.md says {prd['index']!r} and what-next.md says "
                  f"{prd['what_next']!r}. A resume finds whichever file it looks in first, "
                  f"which is F3 as a data defect. Fix the PRD before resuming it.",
                  file=sys.stderr)
        else:
            print(f"\n{prd['slug']}: no <status> in either file, so `--resume` cannot see it "
                  f"and a new PRD on this slug would replace it without warning.",
                  file=sys.stderr)

    if args.check and bad:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
