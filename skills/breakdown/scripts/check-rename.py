#!/usr/bin/env python3
"""Do the index, the feature directory and every reference between them agree? (items 6, 42)

`rename-feature.py` asserts its three postconditions about the slug it just moved. This asks the
same question about the whole PRD, at any moment: **no reference anywhere resolves to a slug that
has no file, and no file sits outside the index without saying why.** The two are not the same
check -- one is about an operation, this one is about a state -- and the state is the one that
decays, because a PRD is edited by hand for weeks after the last rename.

THREE CAUSES, ONE TEST, AND WHY THEY ARE NOT TOLD APART BY COUNTING

An unindexed feature file is a rename residue, real drift, or a legitimately retired feature. Only
the third has a marker: `<definition>superseded</definition>`, which section 4.2 removes from the
index deliberately. So a `superseded` file may be unindexed and anything else unindexed is a
defect. Do not try to separate the other two by counting how many references each has -- P9
records why that fails: the count is a property of the corpus, not of the defect.

WHAT IS CHECKED

  index -> disk       every <feature file="..."> resolves to a file that exists
  disk -> index       every features/*.md is indexed, or declares `superseded`
  identity            a feature file's <slug> matches its own filename
  references          file=, ref=, <depends-on slug=>, <superseded-by slug=> and markdown links
                      all resolve to a feature file that exists
  residue             no feature file carries <priority> -- item 1 moved it to the index entry,
                      and a copy left behind is a second answer with nothing keeping it in step

WHAT IS REPORTED AND NOT REFUSED

A `superseded` pointer that **nothing references any more** has reached the exit condition its own
convention states, and nobody has ever evaluated it. It is a housekeeping fact rather than a
defect, so it prints and exits 0.

WHAT THIS DOES NOT OWN

The pairing rules between a `<definition>` and the element that justifies it -- `excluded` with no
`<rationale>`, `superseded` with no successor, `superseded` still in the index -- belong to
`check-status.py`, which reads the label. A rule stated in two programs is a rule that will be
changed in one of them.

Bare prose mentions of a slug are not references. They do not resolve, and a script that treated
them as broken would fail on every sentence that names a feature.

USAGE

    check-rename.py <prd-dir> [--quiet] [--json]

EXIT CODES

  0  the index, the directory and the references agree
  1  at least one dangling reference, orphan, identity mismatch or residue
  2  usage error, or the PRD could not be read
"""

import argparse
import importlib.util
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "select_features", os.path.join(_HERE, "select-features.py"))
_sel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sel)

SLUG_EL = re.compile(r"<slug>\s*([a-z0-9-]+)\s*</slug>")
META = re.compile(r"<meta>(.*?)</meta>", re.S)
PRIORITY_EL = re.compile(r"<priority>\s*([a-z-]+)\s*</priority>")

# Every shape a reference to a feature takes. Each yields (kind, target) where the target is
# either a path relative to the PRD directory or a bare slug.
PATH_REFS = [
    ("file=", re.compile(r'\bfile="([^"]+\.md)"')),
    ("ref=", re.compile(r'\bref="([^"]+\.md)"')),
    ("link ", re.compile(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)")),
]
SLUG_REFS = [
    ("depends-on", re.compile(r'<depends-on\b[^>]*\bslug="([^"]*)"')),
    ("superseded-by", re.compile(r'<superseded-by\b[^>]*\bslug="([^"]*)"')),
]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def documents(prd_dir):
    """Every file a reference can be written in, as (relative path, text)."""
    out = []
    for extra in ("index.md", "what-next.md"):
        p = os.path.join(prd_dir, extra)
        if os.path.isfile(p):
            out.append((extra, read(p)))
    fdir = os.path.join(prd_dir, "features")
    if os.path.isdir(fdir):
        for name in sorted(os.listdir(fdir)):
            if name.endswith(".md"):
                out.append((f"features/{name}", read(os.path.join(fdir, name))))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir", metavar="prd-dir")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    prd_dir = args.prd_dir
    if not os.path.isdir(prd_dir):
        print(f"REFUSED  not a directory: {prd_dir}", file=sys.stderr)
        return 2
    if not os.path.isfile(os.path.join(prd_dir, "index.md")):
        print(f"REFUSED  no index.md in {prd_dir}", file=sys.stderr)
        return 2

    rows, err = _sel.features_of_prd(prd_dir)
    if err:
        print(f"REFUSED  {err}", file=sys.stderr)
        return 2

    docs = documents(prd_dir)
    on_disk = {rel.split("/")[1][:-3]: rel for rel, _ in docs if rel.startswith("features/")}
    indexed = {r["slug"]: r for r in rows}

    errors, reports = [], []

    # ---- identity, orphans and residue. A dangling index entry is NOT reported here: the
    # reference loop below reads `file=` like every other reference, and reporting it twice
    # would make one defect look like two.
    for slug, rel in sorted(on_disk.items()):
        text = read(os.path.join(prd_dir, rel.replace("/", os.sep)))
        declared = SLUG_EL.search(text)
        if declared and declared.group(1) != slug:
            errors.append(f"{rel}: <slug>{declared.group(1)}</slug> does not match its filename "
                          f"-- one of the two is a rename that stopped half way")

        # ---- disk -> index
        if slug not in indexed and _sel.definition_of(text) != "superseded":
            errors.append(f"{rel}: is not in index.md and is not `superseded` -- a rename "
                          f"residue or real drift, and either way nothing will break it down")

        # ---- residue: <priority> in a feature file (item 1)
        meta = META.search(text)
        if meta and PRIORITY_EL.search(meta.group(1)):
            errors.append(f"{rel}: <meta> still carries <priority> -- it lives on the index "
                          f"entry now, and a copy here is a second answer with nothing keeping "
                          f"it in step")

    # ---- references. One loop over every shape, so a new reference form is one row above
    # rather than a second traversal.
    referenced = set()
    for rel, text in docs:
        base = os.path.dirname(os.path.join(prd_dir, rel.replace("/", os.sep)))
        for kind, rx in PATH_REFS:
            for target in rx.findall(text):
                if re.match(r"^[a-z]+://", target):
                    continue
                resolved = os.path.normpath(os.path.join(base, target.replace("/", os.sep)))
                if not os.path.isfile(resolved):
                    errors.append(f"{rel}: {kind}{target} resolves to nothing")
                    continue
                slug = os.path.splitext(os.path.basename(resolved))[0]
                if slug in on_disk and os.path.samefile(
                        resolved, os.path.join(prd_dir, on_disk[slug].replace("/", os.sep))):
                    referenced.add(slug)
        for kind, rx in SLUG_REFS:
            for slug in rx.findall(text):
                if slug in on_disk:
                    referenced.add(slug)
                else:
                    errors.append(f"{rel}: <{kind} slug=\"{slug}\"> names a feature with no file")

    # ---- the exit condition nobody evaluates
    for slug, rel in sorted(on_disk.items()):
        text = read(os.path.join(prd_dir, rel.replace("/", os.sep)))
        if _sel.definition_of(text) == "superseded" and slug not in referenced:
            reports.append(f"{rel}: `superseded` and nothing references it any more -- the "
                           f"pointer has reached the exit condition its convention states")

    if args.json:
        print(json.dumps({"features": len(on_disk), "errors": errors, "reports": reports},
                         indent=2))
    elif not args.quiet:
        for line in errors:
            print(f"  DANGLING  {line}")
        for line in reports:
            print(f"  RETIRED   {line}")

    print(f"{len(indexed)} indexed, {len(on_disk)} on disk: {len(errors)} unresolved, "
          f"{len(reports)} pointers reached their exit condition")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
