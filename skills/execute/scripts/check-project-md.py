#!/usr/bin/env python3
"""Validate PROJECT.md's embedded <project-context> block, and optionally repair it.

`project-context-finalizer` rewrites this file after every CRD run, and on its first ever
execution it produced:

    ?tag=python&status=archived

A bare `&` is not valid XML. The block stopped parsing, which silently breaks every consumer:
`crd-impact-analysis` reads `<api-registry>` and `<schema-registry>` from it, and the finalizer
itself has to parse the file to update it next time. The run reported success.

This is the same defect the project opened with -- 94 bare ampersands escaped so the PRD
directory would parse -- reintroduced by a component whose whole job is writing XML. Telling
an agent to escape ampersands is a prose instruction; checking afterwards is not.

Usage:
    check-project-md.py <project-path>          # validate; exit 1 if malformed
    check-project-md.py <project-path> --fix    # escape bare ampersands, then validate

`--fix` only escapes `&` that does not already begin an entity. It does not attempt to repair
unbalanced tags or anything else structural -- if the block is broken in some other way, that
is a defect to look at rather than paper over.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

BLOCK = re.compile(r"<project-context.*?</project-context>", re.S)
BARE_AMP = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)")


def main():
    argv = [a for a in sys.argv[1:]]
    fix = "--fix" in argv
    argv = [a for a in argv if not a.startswith("--")]
    if len(argv) != 1:
        print("usage: check-project-md.py <project-path> [--fix]", file=sys.stderr)
        return 2

    path = os.path.join(os.path.abspath(argv[0]), "PROJECT.md")
    if not os.path.isfile(path):
        # Not an error: greenfield projects have no PROJECT.md and never will.
        print(f"no PROJECT.md at {path} -- nothing to validate")
        return 0

    text = open(path, encoding="utf-8").read()
    m = BLOCK.search(text)
    if not m:
        print(f"REFUSED: {path} has no <project-context> block. Every CRD skill reads that "
              f"block; without it the file is decoration.", file=sys.stderr)
        return 1

    block = m.group(0)
    bare = BARE_AMP.findall(block)

    if fix and bare:
        repaired = BARE_AMP.sub("&amp;", block)
        try:
            ET.fromstring(repaired)
        except ET.ParseError as e:
            print(f"REFUSED: escaping ampersands did not make it parse ({e}). Something else "
                  f"is wrong; look at it rather than repairing blindly.", file=sys.stderr)
            return 1
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text[:m.start()] + repaired + text[m.end():])
        print(f"escaped {len(bare)} bare ampersand(s) in {path}")
        block = repaired

    try:
        root = ET.fromstring(block)
    except ET.ParseError as e:
        print(f"REFUSED: <project-context> in {path} is not well-formed: {e}", file=sys.stderr)
        if bare:
            print(f"  {len(bare)} bare ampersand(s) found, e.g. {bare[0]!r} -- "
                  f"re-run with --fix", file=sys.stderr)
        return 1

    sections = [c.tag for c in root]
    missing = [s for s in ("meta", "features", "api-registry", "schema-registry")
               if s not in sections]
    if missing:
        print(f"REFUSED: {path} is missing {', '.join(missing)} -- consumers read these",
              file=sys.stderr)
        return 1

    print(f"PROJECT.md valid: " + ", ".join(
        f"{c.tag} {len(list(c))}" for c in root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
