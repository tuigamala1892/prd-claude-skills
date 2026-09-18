#!/usr/bin/env python3
"""Record that an artefact was written, on the day it was written.

WHY THIS IS ITS OWN SCRIPT

Because two artefacts carry the date under two names -- `index.md`'s <updated> and
`what-next.md`'s <last-updated>, with PROJECT.md using the latter -- and one rule maintains both.
A second implementation of "date an artefact" is how three definitions of <criterion> came to
exist and disagree; `build-what-next.py` imports this rather than keeping a copy, the way it
already imports `select-features.py` rather than carrying a second gap parser.

THE TRIGGER IS THE MUTATION, NOT THE SESSION

This is the correction that produced the script. The first version of the date lived in
`build-what-next.py` alone and `/prd` was told to run it "at the end of every writing session" --
which assumes a session is one sitting that ends the day it began. A PRD is neither. It is
resumed across days, and gaps are opened and closed *during* a session, so there is no single
moment called the end to hang a date on. Each write is its own event and dates its own file:

  a gap opened or closed, or a <definition> changed  ->  build-what-next.py derives, and
                                                         dates what-next.md because it wrote it
  a feature spec written, or an index entry changed  ->  this script, on index.md
  prose edited and nothing derived                   ->  build-what-next.py --touch

WHICH IS WHY THE TWO DATES ARE NOT ONE FACT STORED TWICE

They answer different questions and move at different moments. Closing a gap changes
`what-next.md` and not the index; adding a feature changes both; changing a feature's priority
changes the index alone, because [core section 4] puts priority on the index entry and nowhere
else. A single shared date would be wrong for whichever file did not change.

ALREADY TODAY IS NOT A WRITE

A run that would set the date to the value it already holds writes nothing and says so. The point
is a diff that means something: a PRD touched four times on Thursday should show one changed file,
not four identical rewrites, and a caller that can run this after every edit has to be cheap
enough to run after every edit.

USAGE

    touch-artefact.py <path>...              # date each artefact, if the date would change
    touch-artefact.py <path>... --date DATE  # a specific YYYY-MM-DD, for a caller with its own
                                             # notion of today (and for the suite)

EXIT CODES

  0  every path was dated, or already carried today's date
  1  a path carries no <meta> to place the date in -- migrate it first
  2  usage error -- no such file, or a --date that is not a date
"""

import argparse
import datetime
import os
import re
import sys

# Which element each artefact spells it with. The name is the artefact's, not this script's
# choice: `index.md` has said <updated> since schema-1 and renaming it would be a migration for
# a word. Keyed by ROOT ELEMENT rather than filename, because a filename is a convention and a
# root element is the artefact -- the same rule `migrate.py` uses to decide what a file is.
BY_ROOT = {
    "prd": "updated",                 # index.md
    "what-next": "last-updated",
    "project": "last-updated",        # PROJECT.md
}
# Falls back to the filename when the root is unrecognised, so a fragment under test still works.
BY_NAME = {"index.md": "updated", "what-next.md": "last-updated",
           "project.md": "last-updated"}

ROOT = re.compile(r"<([a-z][a-z0-9-]*)>")
META_CLOSE = re.compile(r"( *)</meta>")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def element_for(path, text):
    """The date element this artefact uses: by root element, then by filename."""
    m = ROOT.search(text)
    if m and m.group(1) in BY_ROOT:
        return BY_ROOT[m.group(1)]
    return BY_NAME.get(os.path.basename(path).lower())


def touch(text, element, today):
    """Set <element> to `today`, returning the new text.

    Returns None when there is nowhere to put it -- no <meta> -- rather than appending it
    somewhere a reader does not look. A date outside <meta> is a date nothing reads, which is
    the state this whole line of work started from.

    THERE IS NO `ALREADY TODAY` BRANCH HERE, ON PURPOSE

    It had one, and a mutation round proved it dead: rewriting `<updated>2026-04-02</updated>`
    to itself is byte-identical, so the branch and the substitution produced the same string and
    no single edit to either could change the outcome. Two sites satisfying one rule is a rule
    with no check over it. The comparison in main() is the one site, and it is the honest place
    for it -- whether anything changed is a question about the FILE, not about this substitution.

    A date written with stray whitespace is therefore normalised rather than preserved, which is
    a write, correctly: the file did change.
    """
    current = re.compile(r"<%s>\s*([^<]*)</%s>" % (element, element))
    m = current.search(text)
    if m:
        return text[:m.start()] + f"<{element}>{today}</{element}>" + text[m.end():]
    anchor = META_CLOSE.search(text)
    if not anchor:
        return None
    line = f"{anchor.group(1)}  <{element}>{today}</{element}>\n"
    return text[:anchor.start()] + line + text[anchor.start():]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--date", help="YYYY-MM-DD; defaults to today")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    today = args.date or datetime.date.today().isoformat()
    if not ISO_DATE.match(today):
        print(f"REFUSED: --date {today!r} is not YYYY-MM-DD", file=sys.stderr)
        return 2

    rc = 0
    for path in args.paths:
        if not os.path.isfile(path):
            print(f"REFUSED: no such artefact: {path}", file=sys.stderr)
            return 2
        text = read(path)
        element = element_for(path, text)
        if not element:
            print(f"REFUSED: {os.path.basename(path)} is not an artefact that carries a date. "
                  f"The three that do are index.md, what-next.md and PROJECT.md",
                  file=sys.stderr)
            return 2
        updated = touch(text, element, today)
        if updated is None:
            print(f"  NO META  {path}: nowhere to put <{element}>. Migrate the file first -- "
                  f"see schema/migration.md", file=sys.stderr)
            rc = 1
            continue
        if updated == text:
            if not args.quiet:
                print(f"  already  {os.path.basename(path)} <{element}> is {today}")
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        if not args.quiet:
            print(f"  dated    {os.path.basename(path)} <{element}> {today}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
