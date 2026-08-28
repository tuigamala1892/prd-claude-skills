#!/usr/bin/env python3
"""Can this toolchain read this manifest? (plan item 24, finding P28)

`build-manifest.py` has stamped every manifest with two versions since item 4.5, and **nothing
has ever read either of them.** A stamp nobody reads is provenance theatre: it makes an artefact
look checked while the incompatibility it exists to catch goes through silently.

TWO VERSIONS, AND ONLY ONE OF THEM ANSWERS THIS QUESTION

  toolchain_version   WHAT PRODUCED this file. Provenance. A patch release moves it
  schema_version      HOW TO READ this file. Compatibility. A patch release does NOT move it

A provenance stamp cannot answer a compatibility question, which is why there are two. `2.0.1`
producing a manifest `2.0.0` could read is ordinary; a manifest whose *shape* this reader has
never seen is not. So the decision reads `schema_version` and the report names
`toolchain_version`, and the two are never conflated.

WHY THE ACCEPTED VERSION IS DECLARED HERE AND NOT IMPORTED

The obvious implementation imports `MANIFEST_SCHEMA_VERSION` from `build-manifest.py`. That
implementation can never detect anything: producer and reader would be equal by construction,
every comparison would pass, and the check would be a function that returns True. The producer's
version and the reader's accepted range are different facts about different programs, and this
file is the reader's half. When `/execute` learns to read a new manifest shape, this constant
moves -- deliberately, in the same commit, by somebody who checked.

THE RULE, AND WHY IT IS ASYMMETRIC

  major differs            REFUSE. The shape is not one this reader knows, in either direction
  minor is higher          WARN. Written by a newer toolchain; the extra fields are ignored
  minor is equal or lower  silent
  absent                   WARN. A manifest from before the stamp existed

Additive minors are the whole reason `/breakdown` could add item 16's traceability fields without
breaking a reader written against 1.0. Majors are not additive, which is what makes them majors.

USAGE

    check-compatibility.py <tasks-dir> [--strict] [--quiet] [--json]

  --strict   exit non-zero on warnings too, not only on a refusal

EXIT CODES

  0  this toolchain can read this manifest (warnings may have been reported)
  1  known-incompatible -- REFUSED, with both versions named
  2  usage error, or the manifest could not be read
"""

import argparse
import json
import os
import re
import sys

# The manifest shapes THIS reader understands. See the docstring: importing the producer's
# constant would make the comparison vacuous.
READER_SCHEMA = "1.2"

VERSION = re.compile(r"^(\d+)\.(\d+)")


def parts(version):
    """(major, minor) from a dotted version, or None when it is not one."""
    m = VERSION.match(str(version or "").strip())
    return (int(m.group(1)), int(m.group(2))) if m else None


def plugin_version():
    """The running plugin's declared version -- what would produce a manifest right now."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    pj = os.path.join(root, ".claude-plugin", "plugin.json")
    try:
        return json.load(open(pj, encoding="utf-8")).get("version")
    except Exception:
        return None


def judge(schema_version):
    """(refusals, warnings) for one manifest's declared schema version."""
    refuse, warn = [], []
    reader = parts(READER_SCHEMA)

    if schema_version is None:
        warn.append(f"the manifest declares no schema_version, so it was written before the "
                    f"stamp existed. Reading it as {READER_SCHEMA} and hoping is the only "
                    f"option; rebuild it with build-manifest.py to remove the doubt")
        return refuse, warn

    got = parts(schema_version)
    if got is None:
        refuse.append(f"schema_version is {schema_version!r}, which is not a version. A reader "
                      f"cannot decide compatibility against a string it cannot parse")
        return refuse, warn

    if got[0] != reader[0]:
        direction = "a newer" if got[0] > reader[0] else "an older"
        refuse.append(f"manifest schema_version {schema_version} is {direction} MAJOR than "
                      f"this toolchain reads ({READER_SCHEMA}). Majors are not additive -- "
                      f"fields have moved or changed meaning, and reading it anyway would "
                      f"produce a plausible wrong answer")
    elif got[1] > reader[1]:
        warn.append(f"manifest schema_version {schema_version} is newer than this toolchain "
                    f"reads ({READER_SCHEMA}). Minors are additive, so this runs -- but the "
                    f"fields added since {READER_SCHEMA} are ignored, and one of them may be "
                    f"the one you care about")
    return refuse, warn


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tasks_dir", metavar="tasks-dir")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = os.path.join(args.tasks_dir, "manifest.json")
    if not os.path.isfile(path):
        print(f"REFUSED  no manifest.json in {args.tasks_dir}", file=sys.stderr)
        return 2
    try:
        manifest = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"REFUSED  manifest.json does not parse: {e}", file=sys.stderr)
        return 2

    schema_version = manifest.get("schema_version")
    produced_by = manifest.get("toolchain_version")
    running = plugin_version()

    refuse, warn = judge(schema_version)

    # Provenance. REPORTED and never decided on: a manifest produced by 2.0.0 and read by 2.0.1
    # is the ordinary case, and refusing it would make every patch release a migration.
    notes = []
    if produced_by is None:
        notes.append("the manifest records no toolchain_version, so what produced it is unknown")
    elif running and produced_by != running:
        notes.append(f"produced by toolchain {produced_by}; this one is {running}. That is "
                     f"provenance, not incompatibility -- schema_version is what decided above")
    elif running:
        notes.append(f"produced by toolchain {running}, which is this one")

    if args.json:
        print(json.dumps({"schema_version": schema_version, "reads": READER_SCHEMA,
                          "toolchain_version": produced_by, "running": running,
                          "refusals": refuse, "warnings": warn, "notes": notes}, indent=2))
    elif not args.quiet:
        for line in refuse:
            print(f"  REFUSED   {line}")
        for line in warn:
            print(f"  WARN      {line}")
        for line in notes:
            print(f"  NOTE      {line}")

    print(f"manifest schema_version {schema_version or 'absent'} against reader "
          f"{READER_SCHEMA}: {len(refuse)} refusals, {len(warn)} warnings")

    if refuse:
        return 1
    return 1 if (args.strict and warn) else 0


if __name__ == "__main__":
    sys.exit(main())
