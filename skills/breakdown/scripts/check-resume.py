#!/usr/bin/env python3
"""A resumed /breakdown resumes from the documents it was given, or refuses (finding P73).

`/breakdown` resumes by existence. Phase 2 says *"if analysis.json exists, skip this phase"*,
Phase 3 the same of `layer_plan.json`, and Phase 4 of each layer's `.done`. None of the three
asked what the file was built FROM. The gap-closure live run edited a CRD between two
`/breakdown` runs and reported that the second would have skipped its analysis -- dropping the
two criteria the edit added, and handing every later phase an analysis of a document that no
longer exists. Nothing downstream could tell: the task set would look complete, and coverage is
measured against the manifest those same stale phases wrote.

WHAT IT DOES

Step 8 of Phase 1 runs this once, before anything reads the document.

  nothing to resume        no analysis.json, no layer_plan.json and no layer `.done` in the
                           tasks directory. The sources are RECORDED in `sources.json`, and every
                           phase runs. Recording again here is correct, not wasteful: a run that
                           stopped in Phase 1 wrote nothing any later run will skip
  resume, unchanged        every recorded source hashes as it did. Exit 0; the skips are sound
  resume, changed          REFUSED, naming each source CHANGED, ADDED or REMOVED
  resume, unrecorded       REFUSED. The artefacts predate this script, and nothing can say what
                           they were built from -- which is the question, so it is not guessed

It never deletes. The artefacts may be a task set somebody has already reviewed, and a script
that regenerates it on noticing a changed comma would destroy that work without asking. The
refusal names the directory to move aside.

WHAT A SOURCE IS

What the skipped phases read, and no more:

  PRD    index.md and every features/**/*.md -- what the analysis passes read. `what-next.md`
         is not one: it is DERIVED from the others and restamped, so hashing it would refuse a
         resume over a file no phase reads
  CRD    the file
  CRD    PROJECT.md under --project-path -- Phase 2 takes the tech stack from it
  both   architecture.md under --project-path, when present -- Phase 3 plans layers from it

Hashed as bytes. A source is labelled by its role (`document/...`, `project/...`) rather than
by its absolute path, so a checkout that moves is not a changed document.

USAGE

    check-resume.py <prd-dir|crd-file> <tasks-dir> [--project-path PATH]

EXIT CODES

  0  nothing to resume (sources recorded), or every source unchanged since they were
  1  REFUSED: the artefacts were built from different sources, or from unrecorded ones
  2  usage error
"""

import argparse
import datetime
import glob
import hashlib
import json
import os
import sys

RECORD = "sources.json"
# What a later phase skips because it exists. Everything else in the directory is rewritten by
# the phase that produces it, so its age cannot mislead a resume.
SKIPPED_BECAUSE_PRESENT = ("analysis.json", "layer_plan.json")


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sources(document, project_path):
    """label -> absolute path, for every file a skipped phase would have read."""
    out = {}
    if os.path.isdir(document):
        index = os.path.join(document, "index.md")
        if os.path.isfile(index):
            out["document/index.md"] = index
        for p in sorted(glob.glob(os.path.join(document, "features", "**", "*.md"),
                                  recursive=True)):
            rel = os.path.relpath(p, document).replace(os.sep, "/")
            out[f"document/{rel}"] = p
    else:
        out[f"document/{os.path.basename(document)}"] = document
    if project_path:
        if os.path.isfile(document):
            candidate = os.path.join(project_path, "PROJECT.md")
            if os.path.isfile(candidate):
                out["project/PROJECT.md"] = candidate
        candidate = os.path.join(project_path, "architecture.md")
        if os.path.isfile(candidate):
            out["project/architecture.md"] = candidate
    return out


def resumable(tasks_dir):
    """The artefacts a later phase would skip for, by name."""
    found = [n for n in SKIPPED_BECAUSE_PRESENT if os.path.isfile(os.path.join(tasks_dir, n))]
    found += sorted(os.path.relpath(p, tasks_dir).replace(os.sep, "/")
                    for p in glob.glob(os.path.join(tasks_dir, "*", ".done")))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("document", metavar="prd-dir|crd-file")
    ap.add_argument("tasks_dir")
    ap.add_argument("--project-path")
    args = ap.parse_args()

    document = os.path.abspath(args.document)
    tasks_dir = os.path.abspath(args.tasks_dir)
    project = os.path.abspath(args.project_path) if args.project_path else None
    if not os.path.exists(document):
        print(f"REFUSED: no such PRD directory or CRD file: {document}", file=sys.stderr)
        return 2
    if not os.path.isdir(tasks_dir):
        print(f"REFUSED: no such tasks directory: {tasks_dir}", file=sys.stderr)
        return 2

    now = {label: digest(path) for label, path in sources(document, project).items()}
    record = os.path.join(tasks_dir, RECORD)
    present = resumable(tasks_dir)

    if not present:
        with open(record, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"recorded": datetime.date.today().isoformat(), "sources": now}, f,
                      indent=2, sort_keys=True)
            f.write("\n")
        print(f"nothing to resume: recorded {len(now)} source(s) in {RECORD}")
        return 0

    if not os.path.isfile(record):
        print(f"REFUSED: {tasks_dir} holds {', '.join(present)} and no {RECORD}, so nothing "
              f"can say which documents they were built from. A later phase would skip "
              f"because they exist. Move the directory aside and run again.", file=sys.stderr)
        return 1

    try:
        with open(record, encoding="utf-8") as f:
            then = json.load(f)["sources"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"REFUSED: {record} could not be read ({e}), so nothing can say which documents "
              f"{', '.join(present)} were built from. Move the directory aside and run again.",
              file=sys.stderr)
        return 1

    drift = [f"  CHANGED  {k}" for k in sorted(now.keys() & then.keys()) if now[k] != then[k]]
    drift += [f"  ADDED    {k}" for k in sorted(now.keys() - then.keys())]
    drift += [f"  REMOVED  {k}" for k in sorted(then.keys() - now.keys())]
    if drift:
        print(f"REFUSED: {tasks_dir} was built from different sources, and resuming would skip "
              f"the phases that read them ({', '.join(present)}):", file=sys.stderr)
        for line in drift:
            print(line, file=sys.stderr)
        print(f"Move {tasks_dir} aside and run again; every phase then reads the documents as "
              f"they are now.", file=sys.stderr)
        return 1

    print(f"resuming: {len(now)} source(s) unchanged since they were recorded -- "
          f"{', '.join(present)} may be skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
