#!/usr/bin/env python3
"""Derive what-next.md's <authoring-gaps> block from the feature files (plan item 11).

WHY THIS EXISTS AT ALL

Item 11 specifies <authoring-gaps> as "DERIVED, never hand-maintained" and names item 6 as the
deriver -- an item a whole phase away. An element with no producer is the defect this plan spends
most of its items removing, and item 51 exists solely because one shipped that way. So the
producer lands with the schema, and item 6 becomes its caller rather than its author.

A PRD with twenty-one unfinished features has twenty-one entries to keep in step with twenty-one
files. That has never once happened by hand: the corpus this schema was measured against listed
ZERO tbd items while carrying twenty-one. Generating it is the only version that stays true.

WHAT IT AGGREGATES, AND WHAT IT REFUSES TO INVENT

  <summary>          one count per <definition> value across every feature file
  <gap .../>         a POINTER to a feature's own <gap>: slug, id, kind, raised. No body --
                     there is one place a gap is written and one place it is corrected
  <feature .../>     a feature short of `defined` that declares no <gaps> at all, so there is
                     nothing to point at and the shortfall has to be named directly

It never writes a gap that a feature file does not declare, and it never resolves one. The
derivation reports what the documents say; it does not have an opinion about them.

WHAT IT DOES NOT TOUCH

Everything else in what-next.md. <next-steps>, <risks>, <session-notes> and <open-questions> are
human-authored, and a generator that rewrote them would be the second producer for one artefact
that item 27 spent its whole argument refusing.

USAGE

    build-what-next.py <prd-dir>                 # rewrite <authoring-gaps> in place
    build-what-next.py <prd-dir> --check         # exit 1 if the block is stale. Writes nothing
    build-what-next.py <prd-dir> --stdout        # print the block, write nothing

EXIT CODES

  0  the block was written, or --check found it current
  1  --check found it stale, or missing where features exist
  2  usage error -- no such directory, or no what-next.md to write into
"""

import argparse
import json
import os
import re
import sys

FEATURE_SLUG = re.compile(r"<slug>\s*([a-z0-9-]+)\s*</slug>")
DEFINITION = re.compile(r"<definition>\s*([a-z-]+)\s*</definition>")
GAP = re.compile(r'<gap\b([^>]*)>')
BLOCK = re.compile(r"( *)<authoring-gaps>.*?</authoring-gaps>", re.S)
META_CLOSE = re.compile(r"( *)</meta>")
STAMP = re.compile(r"<toolchain-version>\s*[^<]*</toolchain-version>")

# The order counts appear in <summary>. Fixed rather than sorted, so a diff between two runs
# shows what changed rather than where a value happened to sort.
ORDER = ["defined", "in-progress", "tbd", "excluded", "superseded"]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def features(prd_dir):
    d = os.path.join(prd_dir, "features")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".md")]


def derive(prd_dir, indent="  "):
    counts = {k: 0 for k in ORDER}
    rows = []

    for path in features(prd_dir):
        text = read(path)
        slug = FEATURE_SLUG.search(text)
        slug = slug.group(1) if slug else os.path.basename(path)[:-3]
        definition = DEFINITION.search(text)
        definition = definition.group(1) if definition else "tbd"
        counts[definition] = counts.get(definition, 0) + 1

        gaps = GAP.findall(text)
        for attrs in gaps:
            a = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
            rows.append(f'{indent}  <gap slug="{slug}" id="{a.get("id", "")}" '
                        f'kind="{a.get("kind", "")}" raised="{a.get("raised", "")}"/>')

        # A feature short of `defined` with nothing to point at. `excluded` and `superseded`
        # are NOT shortfalls -- they are decisions, and listing them as authoring gaps would
        # put a resolved thing on a list of unresolved ones.
        if not gaps and definition in ("tbd", "in-progress"):
            why = "no criteria written" if "<criterion" not in text else "held short of defined"
            rows.append(f'{indent}  <feature slug="{slug}" definition="{definition}">{why}'
                        f'</feature>')

    summary = " ".join(f'{k}="{counts.get(k, 0)}"' for k in ORDER)
    body = [f"{indent}<authoring-gaps>", f"{indent}  <summary {summary}/>"]
    body += rows
    body.append(f"{indent}</authoring-gaps>")
    return "\n".join(body)


def plugin_version():
    """The running plugin's version, for item 24's stamp."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))          # scripts/schema/
    try:
        return json.load(open(os.path.join(root, ".claude-plugin", "plugin.json"),
                              encoding="utf-8")).get("version")
    except Exception:
        return None


def stamp(text):
    """Insert item 24's <toolchain-version> into <meta> when it is ABSENT. Never update it.

    The stamp records what WROTE this PRD, and rewriting it on every derivation would turn
    provenance into a version tracker: every plugin release would make every what-next.md look
    stale, and a file that is always stale is a check nobody runs. An older stamp is the ordinary
    case and is exactly what `list-prds.py` reports before a resume.
    """
    if STAMP.search(text):
        return text
    version = plugin_version()
    if not version:
        return text
    m = META_CLOSE.search(text)
    if not m:
        return text
    line = f"{m.group(1)}  <toolchain-version>{version}</toolchain-version>\n"
    return text[:m.start()] + line + text[m.start():]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    prd_dir = os.path.abspath(args.prd_dir)
    if not os.path.isdir(prd_dir):
        print(f"REFUSED: no such PRD directory: {prd_dir}", file=sys.stderr)
        return 2

    if args.stdout:
        print(derive(prd_dir))
        return 0

    target = os.path.join(prd_dir, "what-next.md")
    if not os.path.isfile(target):
        print(f"REFUSED: no what-next.md in {prd_dir}", file=sys.stderr)
        return 2

    text = read(target)
    existing = BLOCK.search(text)
    indent = existing.group(1) if existing else "  "
    wanted = derive(prd_dir, indent)

    stamped = stamp(text)
    if existing and existing.group(0) == wanted and stamped == text:
        print(f"authoring-gaps is current: {len(features(prd_dir))} feature(s)")
        return 0

    if args.check:
        # The stamp is never a staleness condition -- see stamp(). Only the derived block is.
        if existing and existing.group(0) == wanted:
            print(f"authoring-gaps is current: {len(features(prd_dir))} feature(s)")
            return 0
        where = "is stale" if existing else "is missing"
        print(f"STALE: what-next.md's <authoring-gaps> {where}. Run without --check to "
              f"rebuild it.", file=sys.stderr)
        return 1

    if existing:
        text = text[:existing.start()] + wanted + text[existing.end():]
    else:
        # Between </meta> and <next-steps>, or after </meta>. Never at the end: a derived block
        # that drifts to the bottom of the file stops being read with the summary it belongs to.
        anchor = text.find("</meta>")
        if anchor == -1:
            print("REFUSED: what-next.md has no <meta> to place <authoring-gaps> after. Migrate "
                  "the file first -- see schema/migration.md", file=sys.stderr)
            return 2
        cut = anchor + len("</meta>")
        text = text[:cut] + "\n\n" + wanted + text[cut:]

    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(stamp(text))
    print(f"authoring-gaps rebuilt from {len(features(prd_dir))} feature(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
