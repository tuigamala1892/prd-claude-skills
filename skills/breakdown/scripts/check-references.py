#!/usr/bin/env python3
"""Validate the references that leave the PRD (plan item 39, finding P24).

A PRD cites artefacts the toolchain cannot see: architecture decision records, an
open-questions register, and -- from the other direction -- decision records that name the
features they drive. Measured against the sample corpus: 19 distinct decision records over 136
mentions, 22 distinct questions over 44, none of them validated. A feature whose scope was
settled by a record that no longer exists is broken down without it, and nothing says so.

WHAT IS CHECKED

  ADR-NNN citations   resolve to a record in the decision directory
                      a citation of a *superseded* record is reported with its successor
  OQ-NNN citations    resolve to an entry in the open-questions register
                      a citation of a *resolved* question is reported with what resolved it
  **Drives:** links   in each decision record, resolve to a file that exists

WHAT IS NOT CHECKED, AND WHY

Principle citations (10 mentions in the corpus). A principle has no home until item 28 gives
`architecture.md` its `<principles>` section, so there is nothing to resolve a citation against.
Validating them against a file that does not exist yet would be the failure this plan is about.
That is 180 of the corpus's 190 references covered here and 10 deferred, deliberately.

The register itself is never written. It is human-maintained and outlives any one PRD; this
script reports and never repairs (plan item 39).

USAGE

    check-references.py <prd-dir> [--adr-dir DIR] [--questions FILE] [--strict] [--quiet]

  <prd-dir>      directory holding index.md, what-next.md and features/
  --adr-dir      decision records. Default: discovered, see DISCOVERY below
  --questions    the open-questions register, a single markdown file
  --strict       exit non-zero on warnings too, not just on dangling references
  --quiet        print the summary line only

DISCOVERY

`--adr-dir` and `--questions` default to the corpus project's layout, tried in order and
relative to <prd-dir>: ../../architecture/decisions, ../../../architecture/decisions,
../../docs/architecture/decisions. The register is looked for as open-questions.md beside the
decision directory and one level above it. A citation with nowhere to resolve *against* is an
error naming the flag to pass -- silently passing because the directory was not found is how a
validator becomes decorative.

EXIT CODES

  0  no dangling references (warnings may have been reported)
  1  at least one dangling reference, or a citation with no register to check against
  2  usage error
"""

import argparse
import os
import re
import sys

ADR_CITATION = re.compile(r"\bADR-(\d{1,4})\b")
OQ_CITATION = re.compile(r"\bOQ-(\d{1,4})\b")
# `**Status:** Superseded by ADR-014` -- item 36's convention, already regular in the corpus.
STATUS_FIELD = re.compile(r"^\s*\*\*Status:\*\*\s*(.+?)\s*$", re.M)
DRIVES_FIELD = re.compile(r"^\s*\*\*Drives:\*\*\s*(.+?)\s*$", re.M)
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# An id in a filename: `ADR-007-title.md`, `007-title.md`, `adr007.md`.
FILENAME_ID = re.compile(r"^(?:adr[-_]?)?(\d{1,4})\b", re.I)
RESOLVED_HEADING = re.compile(r"^#{1,6}\s*(.*\bOQ-(\d{1,4})\b.*)$", re.M)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def markdown_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                yield os.path.join(dirpath, name)


def discover_adr_dir(prd_dir):
    for rel in ("../../architecture/decisions",
                "../../../architecture/decisions",
                "../../docs/architecture/decisions"):
        cand = os.path.normpath(os.path.join(prd_dir, rel))
        if os.path.isdir(cand):
            return cand
    return None


def discover_questions(prd_dir, adr_dir):
    roots = [prd_dir, os.path.join(prd_dir, "..", "..")]
    if adr_dir:
        roots = [adr_dir, os.path.join(adr_dir, ".."), os.path.join(adr_dir, "..", "..")] + roots
    for root in roots:
        cand = os.path.normpath(os.path.join(root, "open-questions.md"))
        if os.path.isfile(cand):
            return cand
    return None


def index_records(adr_dir):
    """id -> {path, status, superseded_by, drives}. Ids come from the filename, then a heading."""
    records = {}
    for path in markdown_files(adr_dir):
        text = read(path)
        m = FILENAME_ID.match(os.path.basename(path))
        rid = m.group(1) if m else None
        if rid is None:
            head = ADR_CITATION.search(text[:400])
            rid = head.group(1) if head else None
        if rid is None:
            continue
        status_m = STATUS_FIELD.search(text)
        status = status_m.group(1) if status_m else ""
        successor = None
        if "supersed" in status.lower():
            after = ADR_CITATION.search(status)
            successor = after.group(0) if after else None
        drives = []
        for line in DRIVES_FIELD.findall(text):
            drives += [target for _, target in MD_LINK.findall(line)]
        key = rid.lstrip("0") or "0"
        records[key] = {"path": path, "status": status,
                        "superseded_by": successor, "drives": drives}
    return records


def index_questions(path):
    """id -> resolution text, or None when the entry is still open."""
    text = read(path)
    questions = {}
    for heading, qid in RESOLVED_HEADING.findall(text):
        key = qid.lstrip("0") or "0"
        # Item 36's convention: a resolved question is annotated in place, in its heading.
        resolved = re.search(r"\bresolved\b(.*)$", heading, re.I)
        questions[key] = resolved.group(0).strip() if resolved else None
    for qid in OQ_CITATION.findall(text):
        questions.setdefault(qid.lstrip("0") or "0", None)
    return questions


def cite(text, pattern):
    """(key, as-written, line) per citation. The key matches; the as-written form is reported.

    ADR-007 and ADR-7 are the same record and a report that renames one to the other sends a
    reader looking for a string that is not in the file.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in pattern.finditer(line):
            out.append((m.group(1).lstrip("0") or "0", m.group(0), i))
    return out


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir")
    ap.add_argument("--adr-dir")
    ap.add_argument("--questions")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    prd_dir = os.path.abspath(args.prd_dir)
    if not os.path.isdir(prd_dir):
        print(f"REFUSED: no such PRD directory: {prd_dir}", file=sys.stderr)
        return 2

    adr_dir = os.path.abspath(args.adr_dir) if args.adr_dir else discover_adr_dir(prd_dir)
    q_path = os.path.abspath(args.questions) if args.questions else discover_questions(
        prd_dir, adr_dir)

    records = index_records(adr_dir) if adr_dir and os.path.isdir(adr_dir) else None
    questions = index_questions(q_path) if q_path and os.path.isfile(q_path) else None

    errors, warnings, counted = [], [], 0

    for path in markdown_files(prd_dir):
        rel = os.path.relpath(path, prd_dir)
        text = read(path)

        for rid, written, line in cite(text, ADR_CITATION):
            counted += 1
            if records is None:
                errors.append(f"{rel}:{line}: cites {written} and no decision directory was "
                              f"found -- pass --adr-dir")
            elif rid not in records:
                errors.append(f"{rel}:{line}: {written} does not exist in "
                              f"{os.path.relpath(adr_dir, prd_dir)}")
            elif records[rid]["superseded_by"]:
                warnings.append(f"{rel}:{line}: {written} is superseded by "
                                f"{records[rid]['superseded_by']}")
            elif "supersed" in records[rid]["status"].lower():
                warnings.append(f"{rel}:{line}: {written} is superseded and names no successor")

        for qid, written, line in cite(text, OQ_CITATION):
            counted += 1
            if questions is None:
                errors.append(f"{rel}:{line}: cites {written} and no open-questions register was "
                              f"found -- pass --questions")
            elif qid not in questions:
                errors.append(f"{rel}:{line}: {written} is not in "
                              f"{os.path.basename(q_path)}")
            elif questions[qid]:
                warnings.append(f"{rel}:{line}: {written} is already {questions[qid]}")

    # The other direction: a record naming a feature that is not there any more.
    if records:
        for rid in sorted(records, key=lambda k: int(k)):
            rec = records[rid]
            for target in rec["drives"]:
                counted += 1
                if re.match(r"^[a-z]+://|^#", target):
                    continue
                resolved = os.path.normpath(
                    os.path.join(os.path.dirname(rec["path"]), target.split("#")[0]))
                if not os.path.exists(resolved):
                    errors.append(f"{os.path.basename(rec['path'])}: **Drives:** "
                                  f"{target} does not exist")

    if not args.quiet:
        for line in errors:
            print(f"  DANGLING  {line}")
        for line in warnings:
            print(f"  STALE     {line}")

    where = os.path.relpath(adr_dir, prd_dir) if adr_dir else "not found"
    print(f"{counted} references checked against {where}: "
          f"{len(errors)} dangling, {len(warnings)} stale")

    if errors:
        return 1
    return 1 if (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
