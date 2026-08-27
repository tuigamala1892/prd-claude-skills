#!/usr/bin/env python3
"""Migrate PRD, CRD and PROJECT.md artefacts between schema versions (plan item 41).

The rules this executes are specified in ../migration.md, which is the authority. This file is
its consumer, not a second statement of it: every rule below cites the identifier the guide
gives it (R1, R2, R3), and a rule that exists here and not there is a bug in this file.

WHAT MAKES THIS SAFE TO RE-ENTER

The marker of "already migrated" is the SHAPE, never a stamp. A feature file carrying
<definition> is migrated; one carrying <status> is not. So re-running is safe by construction,
a partly migrated tree is safe to re-enter, and there is no side-car that can disagree with the
content. The cost is a constraint the guide states: a transformation whose completion is not
visible in the shape has to be made total until it is.

WHAT IT REFUSES TO DO

A file matching no precondition is REPORTED, never transformed. That is the whole escalation
path, and it is why exit 2 exists separately from exit 1: nothing was written for those files,
so the tree is exactly as it was found.

USAGE

    migrate.py <path> --to schema-2 [--dry-run] [--quiet]
    migrate.py <path> --to schema-2 --check      # assert postconditions, write nothing
    migrate.py <path> --detect                   # report each file's schema, write nothing

EXIT CODES

  0  every file is in the target schema and every postcondition holds
  1  a postcondition failed; that file was RESTORED and the failure is named
  2  escalation -- one or more files matched no precondition. Nothing written for those
  3  usage error
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.dirname(HERE)

# ---------------------------------------------------------------- artefact kinds

# Which artefact a file is, decided by ROOT ELEMENT rather than by filename. R1 must not touch
# index.md or what-next.md -- their <status> is the document-level tag, which was never renamed
# and whose reader is what makes `/prd --resume` work. Deciding by filename would have been one
# convention away from breaking it.
ROOTS = (
    ("feature", re.compile(r"<\s*feature\s*>")),
    ("crd", re.compile(r"<\s*crd\s*>")),
    ("prd", re.compile(r"<\s*prd\s*>")),
    ("what-next", re.compile(r"<\s*what-next\s*>")),
    ("project-context", re.compile(r"<\s*project-context\b")),
)

META = re.compile(r"<meta>(.*?)</meta>", re.S)
FEATURE_ENTRY = re.compile(r"<feature\s+id=\"[^\"]+\"[^>]*>")


def kind_of(text):
    for name, pat in ROOTS:
        if pat.search(text):
            return name
    return None


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# ------------------------------------------------------------------------ rules
#
# Each rule is (id, artefact kind, old-shape test, transform, postcondition).
#
# `applies` tests the OLD shape -- the precondition. `done` tests the NEW one, and is what makes
# a second run a no-op rather than a second transformation. Together they are the file's own
# record of where it is, which is why nothing needs stamping.


def _meta_swap(text, old, new):
    """Rename <old> to <new>, inside <meta> only, preserving content byte for byte."""
    m = META.search(text)
    if not m:
        return text
    inner = m.group(1)
    swapped = re.sub(r"<%s>(.*?)</%s>" % (old, old), r"<%s>\1</%s>" % (new, new), inner, flags=re.S)
    return text[:m.start(1)] + swapped + text[m.end(1):]


def _meta_has(text, tag):
    m = META.search(text)
    return bool(m and re.search(r"<%s>" % tag, m.group(1)))


def _entries_with(text, attr):
    return [e for e in FEATURE_ENTRY.findall(text) if re.search(r"\b%s=" % attr, e)]


RULES = [
    ("R1", "feature",
     lambda t: _meta_has(t, "status"),
     lambda t: _meta_swap(t, "status", "definition"),
     lambda t: _meta_has(t, "definition") and not _meta_has(t, "status")),

    ("R2", "crd",
     lambda t: _meta_has(t, "status"),
     lambda t: _meta_swap(t, "status", "workflow"),
     lambda t: _meta_has(t, "workflow") and not _meta_has(t, "status")),

    ("R3", "project-context",
     lambda t: bool(_entries_with(t, "status")),
     lambda t: FEATURE_ENTRY.sub(lambda m: re.sub(r"\bstatus=", "built=", m.group(0)), t),
     lambda t: not _entries_with(t, "status")
               and len(_entries_with(t, "built")) == len(FEATURE_ENTRY.findall(t))),
]

# Artefacts the target schema does not change. Named rather than defaulted: "no rule matched"
# and "no rule was needed" are different answers, and only the first is an escalation.
UNCHANGED = {
    "schema-2": {"prd", "what-next"},
}

TARGETS = {"schema-2"}


# ----------------------------------------------------------------- invariants

VALUE = re.compile(r">\s*([^<>\s][^<>]*?)\s*<|=\"([^\"]*)\"")


def values(text):
    """Every element body and attribute value, as a sorted list.

    The rename invariant is that this is IDENTICAL before and after. A rename that alters a
    value is not a rename, and asserting only the tag names would not have noticed.
    """
    out = []
    for body, attr in VALUE.findall(text):
        out.append(body or attr)
    return sorted(v for v in out if v.strip())


def tag_counts(text):
    return len(re.findall(r"<[A-Za-z][\w-]*", text))


# --------------------------------------------------------------------- driving

def artefacts(path):
    if os.path.isfile(path):
        yield path
        return
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                yield os.path.join(dirpath, name)


def plan_for(text, target):
    """(kind, rule or None, verdict). Verdict is one of: MIGRATE, ALREADY, UNCHANGED, ESCALATE."""
    kind = kind_of(text)
    if kind is None:
        return None, None, "ESCALATE"
    if kind in UNCHANGED.get(target, ()):
        return kind, None, "UNCHANGED"
    for rid, rkind, applies, _t, done in RULES:
        if rkind != kind:
            continue
        if applies(text):
            return kind, rid, "MIGRATE"
        if done(text):
            return kind, rid, "ALREADY"
    return kind, None, "ESCALATE"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("--to", dest="target")
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"usage: no such path: {args.path}", file=sys.stderr)
        return 3
    if not args.detect:
        if not args.target:
            print("usage: --to <schema> is required unless --detect", file=sys.stderr)
            return 3
        if args.target not in TARGETS:
            print(f"usage: no migration to {args.target}. Known: {sorted(TARGETS)}",
                  file=sys.stderr)
            return 3

    escalations, failures, migrated, already = [], [], 0, 0
    rules_by_id = {r[0]: r for r in RULES}

    for path in artefacts(args.path):
        text = read(path)
        rel = os.path.relpath(path, args.path if os.path.isdir(args.path) else
                              os.path.dirname(path) or ".")

        if args.detect:
            kind = kind_of(text)
            if kind is None:
                escalations.append(f"{rel}: no artefact root element -- cannot select a migration")
                continue
            governed = [r for r in RULES if r[1] == kind]
            if not governed:
                state = "any"            # no rule touches this artefact; every schema fits
            elif any(r[4](text) for r in governed):
                state = "schema-2"
            elif any(r[2](text) for r in governed):
                state = "schema-1"
            else:
                # A governed artefact in neither shape cannot have a migration SELECTED for it,
                # which is exactly the case item 41 says to stop on rather than guess at.
                state = "UNKNOWN"
                escalations.append(
                    f"{rel}: a <{kind}> in neither the old shape nor the new one -- "
                    f"no migration can be selected")
            if not args.quiet:
                print(f"  {state:<10} {kind:<16} {rel}")
            continue

        kind, rid, verdict = plan_for(text, args.target)

        if verdict == "ESCALATE":
            why = ("no artefact root element" if kind is None
                   else f"a <{kind}> matching no precondition for {args.target}")
            escalations.append(f"{rel}: {why} -- STOPPED, nothing written")
            continue

        if verdict in ("ALREADY", "UNCHANGED"):
            already += 1
            if not args.quiet:
                print(f"  {verdict:<10} {rel}")
            continue

        _rid, _kind, _applies, transform, done = rules_by_id[rid]
        new = transform(text)

        # Postconditions, all three, before anything is kept. The value invariant is the one
        # that matters: it is what distinguishes a rename from an edit.
        problems = []
        if not done(new):
            problems.append(f"{rid}'s postcondition does not hold after transforming")
        if values(new) != values(text):
            problems.append("values changed; a rename that alters a value is not a rename")
        if tag_counts(new) != tag_counts(text):
            problems.append(f"element count moved from {tag_counts(text)} to {tag_counts(new)}")

        if problems:
            failures.append(f"{rel}: " + "; ".join(problems) + " -- RESTORED")
            continue

        if not args.check and not args.dry_run:
            write(path, new)
        migrated += 1
        if not args.quiet:
            verb = "WOULD" if (args.dry_run or args.check) else "MIGRATED"
            print(f"  {verb:<10} {rel}  [{rid}]")

    if args.detect:
        for line in escalations:
            print(f"  ESCALATE   {line}", file=sys.stderr)
        return 2 if escalations else 0

    # --check asks a different question from a run: not "can this be migrated" but "is it
    # migrated". A file the run WOULD have transformed is a file that is not there yet.
    if args.check and migrated:
        print(f"\nCHECK FAILED: {migrated} file(s) are not yet in {args.target}",
              file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"\n{migrated} migrated, {already} already in {args.target}, "
              f"{len(escalations)} escalated, {len(failures)} failed")

    for line in failures:
        print(f"  FAILED     {line}", file=sys.stderr)
    for line in escalations:
        print(f"  ESCALATE   {line}", file=sys.stderr)

    if failures:
        return 1
    if escalations:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
