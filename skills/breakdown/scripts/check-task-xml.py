#!/usr/bin/env python3
"""Does every task file parse? (item 80, finding P64)

The sixth crossing generated an `L4-001` carrying `<contract kind="schema" ref="Link">`
unescaped in prose. It was not well-formed XML, and **three readers hid it in turn**:

    build-manifest.py        `2 task(s)`, exit 0
    check-coverage.py        `1 of 2 task(s) attributed; criterion 7 named by no task`
    breakdown-review-tasks   PASSED -- "all required sections present"

None of those numbers points at a broken file. The coverage line points at ATTRIBUTION, which
is the thing an operator would then go and investigate, and the reviewer's verdict says the
file is fine. The cause was three levels away from every symptom.

WHY IT WAS NOBODY'S JOB, WHICH IS THE ACTUAL FINDING

`build-manifest.py` parsed these files with `ElementTree` and caught the failure behind a bare
`except Exception` whose comment read *"a malformed task file is item 4.x's problem, not this
script's"*. **The deferral was deliberate and the owner it deferred to was never assigned.**
`check-coverage.py` then imported `edges_of` from that script -- correctly, because the rules
for reading a task live in one place -- and inherited the silence: a file that cannot be parsed
has no `<source-feature>` edges, and no edges reads as *not attributed to anything*.

So this script exists to be that owner, and `checks.md` is where the next reader finds it
instead of deferring to a fourth place.

THE IDIOM WAS ALREADY HERE

`check-architecture.py`, `check-rules.py` and `check-project-md.py` all catch `ET.ParseError`
by name and report it with its position. `build-manifest.py` is the one that departed, and it
now names this script rather than growing a second copy of the assertion.

WHAT IT DOES NOT DO

It asserts that a task file is well-formed XML and nothing else. Whether the required sections
are present is `review-criteria.md`'s; whether the content obeys the project's rules is
`check-rules.py`'s; whether every criterion has a task is `check-coverage.py`'s. One script,
one job, one exit code -- and a parse failure has to be settled before any of those three can
mean anything, which is why it runs first.

USAGE

    check-task-xml.py <tasks-dir> [--quiet] [--json]

EXIT CODES

  0  every *.xml under <tasks-dir> parses
  1  at least one does not, named with its position
  2  usage error, or no task files found
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET


def task_files(tasks_dir):
    """Every *.xml under the tree, in a stable order."""
    found = []
    for dirpath, _dirs, names in os.walk(tasks_dir):
        for name in sorted(names):
            if name.lower().endswith(".xml"):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def parse_failures(paths, root):
    """(relative path, message) for each file that does not parse. Position included.

    `not well-formed` with no position is a file to re-read from the top, so the line and
    column ElementTree already knows are carried through rather than summarised away.
    """
    bad = []
    for path in paths:
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            ET.parse(path)
        except ET.ParseError as e:
            bad.append((rel, str(e)))
        except OSError as e:
            bad.append((rel, f"could not be read: {e.strerror}"))
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tasks_dir", metavar="tasks-dir")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    tasks_dir = os.path.abspath(args.tasks_dir)
    if not os.path.isdir(tasks_dir):
        print(f"REFUSED  not a directory: {args.tasks_dir}", file=sys.stderr)
        return 2

    paths = task_files(tasks_dir)
    if not paths:
        # Not exit 1: `no tasks` is a different finding from `a task is broken`, and reporting
        # the second for the first is the confusion this whole item is about.
        print(f"REFUSED  no task files (*.xml) under {args.tasks_dir}", file=sys.stderr)
        return 2

    bad = parse_failures(paths, tasks_dir)

    if args.json:
        print(json.dumps({"checked": len(paths),
                          "unparseable": [{"file": f, "error": m} for f, m in bad]}, indent=2))
    else:
        if not args.quiet:
            for rel, msg in bad:
                print(f"  MALFORMED  {rel}: {msg}", file=sys.stderr)
        print(f"{len(paths)} task file(s) checked: {len(bad)} that do not parse")

    if bad and not args.quiet:
        print("\nA task file that is not well-formed XML reaches its implementer as text, and "
              "every\nreader above this one reports a DIFFERENT symptom: the manifest omits it, "
              "coverage\ncalls it unattributed, and the reviewer passes it. Fix the file; the "
              "usual cause is\nan unescaped `<` in prose -- write `&lt;` or fence it.",
              file=sys.stderr)

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
