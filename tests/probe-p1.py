#!/usr/bin/env python3
"""Measure P1 at runtime: does `/breakdown` build features the owner rejected? (item 21)

P1 is established statically and exhaustively -- `breakdown-analyze-prd` writes
`features[].priority` into analysis.json and no skill downstream ever reads it. The consumer
does not exist. But a passing grep is not a run, and this plan's own method note says a
measurement inherits every defect of how it was taken. So: take it.

TWO MODES, AND THE SPLIT IS THE POINT

    probe-p1.py --grade <tasks-dir>     offline. Attribute generated tasks to features.
    probe-p1.py --run                   live. Build a workspace, run /breakdown, then grade.
    probe-p1.py --baseline              authoring size of the probe PRD, for the item 21 delta.

The grader is a separate mode so it can be tested without spending a live run -- feed it a
directory of tasks and it reports the same thing it would report after `--run`. A grader that
has only ever been exercised by the expensive path is a grader nobody has checked.

WHY THE SLUGS ARE ANIMALS

No task carries a `<source-feature>` element yet; item 16 adds one. Until then, attributing a
generated task to the feature it came from is a string match, and a string match is sound only
when the string cannot occur by coincidence. A task about logging might say "telemetry". None
of them will say "quokka".

WHAT THIS MEASUREMENT CANNOT RULE OUT

The run needs `--plugin-dir` pointed at this checkout, so the agent under test *can* read this
file and learn which token the grader looks for. The prompt never mentions the probe, and the
workspace is the working directory, but the possibility cannot be removed while the grader and
the subject share a filesystem. A clean `exit 0` therefore has to be read with that in mind --
it is weak evidence that the toolchain filters, and strong evidence only when paired with a
transcript showing *why* the rejected feature was dropped.

There is a second and more interesting confound, and it is not a defect: an agent reads the PRD,
sees `priority="wont-have"`, and may skip that feature on its own judgement. That is still a
finding rather than noise -- it means the behaviour is model-dependent rather than enforced,
which is precisely what item 13 exists to fix.

WHAT COUNTS AS A RESULT

  exit 0   no task derives from the won't-have feature, and attribution worked
  exit 1   P1 CONFIRMED at runtime: a task is NAMED for the rejected feature
  exit 2   the probe is INVALID -- no tasks at all, or none from the must-have. Not a pass.
  exit 3   UNDECIDABLE -- no task names any feature, so nothing can be attributed by string
           match. Item 16's case measured, not a probe defect. See grade().

The third one matters most. A probe that reports "no won't-have tasks" because `/breakdown`
produced nothing at all has measured nothing, and two false passes in this phase have already
come from exactly that shape.
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Which schema version the probe reads is SCHEMAS.json's to declare, not this file's. The
# probe measures the CURRENT toolchain; pointing it at a superseded fixture would measure a
# schema nothing writes any more and report the number as if it were live.
with open(os.path.join(REPO, "tests", "fixture", "prd", "SCHEMAS.json"), encoding="utf-8") as _f:
    _SCHEMA = json.load(_f)["current"]

FIXTURE = os.path.join(REPO, "tests", "fixture", "prd", _SCHEMA, "staff-service")

# slug -> (tier, the token that cannot appear by accident)
FEATURES = {
    "zebra-signin": ("must-have", "zebra"),
    "walrus-export": ("should-have", "walrus"),
    "narwhal-theme": ("could-have", "narwhal"),
    "quokka-telemetry": ("wont-have", "quokka"),
}
REJECTED = "quokka-telemetry"


def task_files(tasks_dir):
    return sorted(glob.glob(os.path.join(tasks_dir, "**", "*.xml"), recursive=True))


# What a task IS: its name and its objective. Deliberately the two narrowest sections.
#
# Not <verification>, which asserts a feature is absent. Not <prd-excerpt>, which quotes the
# PRD wholesale. And not <requirements> or <exports> either -- a real run put "Do NOT add a
# telemetry table ... Quokka telemetry is wont-have and is excluded from this release" into
# the requirements of twelve unrelated tasks. High precision, low recall, on purpose: a
# mention anywhere else is reported as context for a person to read, never counted.
BUILDS = ("name", "objective")
CONTEXT = ("requirements", "exports", "test-requirements", "verification")


def attribute(tasks_dir):
    """task path -> set of feature slugs it derives from.

    Read only the sections describing what the task produces. The first version matched the
    whole file and reported 13 of 17 tasks as deriving from the rejected feature -- including
    the SQLite schema and the password hashing. Every one of those had matched on a
    verification step asserting the feature was NOT there:

        assert 'sqlalchemy' not in s and 'jwt' not in s and 'telemetry' not in s

    A grader that cannot tell "builds X" from "proves X is absent" reports the opposite of the
    truth, and reports it in the confident direction.
    """
    out = {}
    for path in task_files(tasks_dir):
        raw = open(path, encoding="utf-8", errors="replace").read()

        def sections(tags):
            return " ".join(
                " ".join(re.findall(r"<%s\b[^>]*>(.*?)</%s>" % (t, t), raw, re.S | re.I))
                for t in tags).lower()

        named, mentioned = set(), set()
        builds_text, context_text = sections(BUILDS), sections(CONTEXT)
        for slug, (_tier, token) in FEATURES.items():
            pattern = r"\b(?:%s|%s)\b" % (re.escape(token), re.escape(slug))
            if re.search(pattern, builds_text):
                named.add(slug)
            elif re.search(pattern, context_text):
                mentioned.add(slug)
        out[path] = (named, mentioned)
    return out


def trace_decision(tasks_dir):
    """Where the rejected feature reached, and what — if anything — stopped it.

    Added after the first real run, which came back with zero won't-have tasks and was still
    not the result it looked like. `analysis.json` carried the rejected feature in full and
    derived a data model from it; `layer_plan.json` then dropped it under a `features_excluded`
    key that exists in no schema in this repository. So the exclusion was the model's judgement
    rather than the toolchain's rule, and a task count alone cannot tell those apart.
    """
    lines = []
    for name in ("analysis.json", "layer_plan.json"):
        path = os.path.join(tasks_dir, name)
        if not os.path.isfile(path):
            lines.append((name, "absent", None))
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        token = FEATURES[REJECTED][1]
        if not re.search(token, text, re.I):
            lines.append((name, "no trace of the rejected feature", None))
            continue
        # Any line naming the rejected feature alongside a word of refusal is the mechanism,
        # quoted rather than summarised.
        why = [ln.strip() for ln in text.splitlines()
               if re.search(token, ln, re.I)
               and re.search(r"exclud|reject|not.{0,12}(built|included|implement)|skip|omit",
                             ln, re.I)]
        lines.append((name, "carries the rejected feature", why[:3]))
    return lines


def grade(tasks_dir, quiet=False):
    attributed = attribute(tasks_dir)
    total = len(attributed)

    per_tier = {tier: 0 for tier, _ in FEATURES.values()}
    for builds, _refuses in attributed.values():
        for slug in builds:
            per_tier[FEATURES[slug][0]] += 1
    unattributed = sum(1 for b, _r in attributed.values() if not b)

    violations = sorted(p for p, (b, _m) in attributed.items() if REJECTED in b)
    carried = sorted(p for p, (_b, m) in attributed.items() if REJECTED in m)

    if not quiet:
        print(f"tasks generated: {total}")
        for tier in ("must-have", "should-have", "could-have", "wont-have"):
            print(f"  {tier:<12} {per_tier[tier]:>3} task(s)")
        print(f"  {'unattributed':<12} {unattributed:>3} task(s)")
        for path in violations:
            print(f"  WONT-HAVE TASK  {os.path.relpath(path, tasks_dir)}")
        if carried:
            print(f"  {len(carried)} task(s) mention the rejected feature outside their name "
                  f"and objective -- read those before drawing a conclusion; in the runs so "
                  f"far every one was an instruction NOT to build it")

    # An invalid probe is not a passing probe. Say so before saying anything else.
    if total == 0:
        print("INVALID: no tasks were generated at all. This measures nothing.", file=sys.stderr)
        return 2

    if violations:
        print(f"\nP1 CONFIRMED at runtime: {len(violations)} of {total} generated tasks are "
              f"NAMED for a feature marked wont-have.", file=sys.stderr)
        return 1

    # The finding this probe actually produced, and the reason it reports rather than passes.
    #
    # String matching cannot answer the question on today's task format, and BOTH failure
    # directions were observed on one real run of 17 tasks:
    #
    #   whole-file match    13 "violations", every one a NEGATIVE requirement -- "Do NOT add
    #                       a telemetry table ... Quokka telemetry is wont-have and is
    #                       excluded from this release"
    #   name + objective    0 attributions for ANY tier, because generation renames to domain
    #                       language: the export task is called "GET /export", not "walrus".
    #                       The feature's own words do not survive into the task.
    #
    # No count decides it either way. That is not a weakness of this probe -- it is item 16
    # measured. <source-feature> and <moscow> on the task are what make the question
    # answerable, and until they exist the honest exit is "undecidable, here is the evidence".
    if not any(builds for builds, _m in attributed.values()):
        print(f"\nUNDECIDABLE: no task's name or objective names ANY feature, in any tier, so "
              f"no task can be traced to a source feature by string match. {len(carried)} "
              f"task(s) mention the rejected feature elsewhere -- read them; in every run so "
              f"far they were instructions NOT to build it.\n\nThis is item 16's case, "
              f"measured: until a task carries <source-feature>, P1 cannot be decided at "
              f"runtime.", file=sys.stderr)
        for path, (_b, m) in sorted(attributed.items()):
            if REJECTED in m:
                print(f"  mentions the rejected feature: {os.path.relpath(path, tasks_dir)}")
        for name, state, why in trace_decision(tasks_dir):
            print(f"  {name}: {state}")
            for line in why or []:
                print(f"      {line[:150]}")
        return 3

    if per_tier["must-have"] == 0:
        print("INVALID: no task derives from the must-have feature, so the run did not do "
              "what the probe assumes. 'No won't-have tasks' would be vacuous.", file=sys.stderr)
        return 2

    print("\nNo task derives from the won't-have feature.")

    # A clean task count is where the question starts, not where it ends. P1 is a claim about
    # a missing consumer, and the artefacts upstream of the tasks are where that shows.
    trace = trace_decision(tasks_dir)
    if any(state == "carries the rejected feature" for _n, state, _w in trace):
        print("\nBut the rejected feature was not absent -- it was dropped, and by whom is the "
              "whole of P1:")
        for name, state, why in trace:
            print(f"  {name}: {state}")
            for line in why or []:
                print(f"      {line[:150]}")
        print("\n  Read those quotes before recording this as a pass. If the exclusion is "
              "\n  phrased as the model's own reasoning, and no skill instructed it, then "
              "\n  nothing FILTERED the won't-have -- a model declined to build it, which is "
              "\n  a different fact with a different failure mode (see item 13).")
    return 0


def run(model, timeout):
    """Build a workspace outside the repository, run /breakdown into it, then grade."""
    import tempfile

    work = tempfile.mkdtemp(prefix="prd-probe-p1-")
    # The fixture convention: never build inside the toolchain checkout. /breakdown writes
    # directories, and F4 is what happens when it writes them here.
    assert not os.path.abspath(work).startswith(REPO), "refusing to build inside the repo"

    prd = os.path.join(work, "prd", "staff-service")
    shutil.copytree(FIXTURE, prd)
    tasks = os.path.join(work, "tasks")
    os.makedirs(tasks, exist_ok=True)

    prompt = (f"/breakdown {os.path.join(prd, 'index.md')} --output-dir {tasks}\n\n"
              "Run it to completion. Do not ask for confirmation.")
    print(f"workspace: {work}")
    print(f"running /breakdown on {model}; this generates real files and takes a few minutes")

    # --add-dir is mandatory and was missing from the first version of this script: the
    # workspace comes from mkdtemp() with a random suffix, so it can never be pre-authorised,
    # and every read and mkdir under it was refused. `--permission-mode acceptEdits`
    # auto-accepts edits *within* allowed directories; it does not widen the allowlist.
    #
    # cwd is the workspace too, so the run's own working directory is the thing under test
    # rather than this checkout.
    argv = ["claude", "-p", prompt, "--model", model, "--plugin-dir", REPO,
            "--add-dir", work, "--permission-mode", "acceptEdits"]

    def text_of(stream):
        if isinstance(stream, bytes):
            return stream.decode("utf-8", "replace")
        return stream or ""

    timed_out = False
    try:
        proc = subprocess.run(argv, cwd=work, capture_output=True, text=True,
                              timeout=timeout, encoding="utf-8", errors="replace")
        out, err = proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        # A timeout is not a reason to discard the run. The first one killed a 25-minute
        # /breakdown that had already written nine tasks, a layer plan and an analysis --
        # and the exception threw all of it away, the transcript included. Grade what is
        # on disk, and label it partial.
        timed_out = True
        out, err = text_of(e.stdout), text_of(e.stderr)

    log = os.path.join(work, "breakdown-output.txt")
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
        f.write("\n--- stderr ---\n")
        f.write(err)
    print(f"transcript: {log}")
    if timed_out:
        print(f"TIMED OUT after {timeout}s -- grading what was written before the kill. "
              f"A truncated run can support a positive result but never a clean one.")

    # /breakdown resolves its own output paths, so find where the tasks actually landed
    # rather than assuming. Assuming is what resolve-output.sh exists to stop.
    # Search for the TASKS, not for a manifest. The first version keyed off manifest.json and
    # reported "no task XML anywhere" against a workspace holding seventeen task files across
    # four layer directories: the manifest is written in /breakdown's last phase, so a
    # truncated run never has one -- and a truncated run is exactly what this has to survive.
    found = [p for p in glob.glob(os.path.join(work, "**", "*.xml"), recursive=True)
             if (os.sep + "prd" + os.sep) not in p
             and re.search(r"L\d+-\d+", os.path.basename(p))]
    if found:
        root = os.path.commonpath([os.path.dirname(p) for p in found])
        print(f"tasks found in: {root}\n")
        return grade(root)

    print("INVALID: no task XML was written anywhere under the workspace. See the "
          "transcript.", file=sys.stderr)
    return 2


def baseline(prd_dir):
    """The mechanical half of item 21's authoring measure (R17)."""
    features = sorted(glob.glob(os.path.join(prd_dir, "features", "*.md")))
    print(f"authoring baseline for {os.path.relpath(prd_dir, REPO)}, current templates")
    print(f"{'feature':<22} {'words':>6} {'criteria':>9} {'elements':>9}")
    totals = [0, 0, 0]
    for path in features:
        text = open(path, encoding="utf-8", errors="replace").read()
        words = len(re.findall(r"[A-Za-z0-9'-]+", re.sub(r"<[^>]+>", " ", text)))
        criteria = len(re.findall(r"<criterion\b", text))
        elements = len(re.findall(r"<[a-z-]+[ >]", text))
        print(f"{os.path.basename(path):<22} {words:>6} {criteria:>9} {elements:>9}")
        totals = [totals[0] + words, totals[1] + criteria, totals[2] + elements]
    print(f"{'TOTAL':<22} {totals[0]:>6} {totals[1]:>9} {totals[2]:>9}")
    print("\nThis is the size half only. The question item 21 actually asks -- *is this still "
          "tolerable to write?* -- is a stopwatch against a person, and no script can take it. "
          "Re-run this after items 33/34 land and record both numbers beside a human timing.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--grade", metavar="TASKS_DIR")
    g.add_argument("--run", action="store_true")
    g.add_argument("--baseline", nargs="?", const=FIXTURE, metavar="PRD_DIR")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.grade:
        if not os.path.isdir(args.grade):
            print(f"no such tasks directory: {args.grade}", file=sys.stderr)
            return 2
        return grade(args.grade, quiet=args.quiet)
    if args.run:
        return run(args.model, args.timeout)
    return baseline(args.baseline)


if __name__ == "__main__":
    sys.exit(main())
