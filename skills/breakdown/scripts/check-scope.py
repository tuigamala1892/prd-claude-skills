#!/usr/bin/env python3
"""Compare what the analysis PREDICTED against what generation PRODUCED (plan item 49).

`<scope>` and `<confidence>` were required fields on the CRD path with no consumer anywhere in
the toolchain -- which is why items 29 and 31 were written as if from nothing. This is their
reader, and it is the same reader on both paths.

WHY A CROSS-CHECK AND NOT A ROUTING INPUT

A size estimate from a model is soft. That is tolerable precisely BECAUSE it selects nothing: no
layer set, no batch size, no filter. Item 31 demoted `<scope>` from routing for exactly this
reason. What a soft prediction is good for is disagreeing with an observation -- "impact analysis
called this small; generation produced 14 tasks" means one of the two is wrong, and both answers
are worth having.

GROSS DISAGREEMENT ONLY

Bands are counted in FILES (core §5) and the observation is counted in TASKS, and a task creates
at most three files, so the two units do not line up. Comparing numbers would produce a check
that fires constantly and is therefore ignored -- the fate of every alarm nobody can silence. So
the comparison is band against band, and only NON-ADJACENT bands disagree:

    small  vs medium   quiet      the units do not line up; this is noise
    medium vs large    quiet
    small  vs large    REPORTED   one of the two is wrong

CONFIDENCE IS REPORTED, NEVER COMPARED

`<confidence>` grades the analysis, not the output, so there is nothing to hold it against. It is
listed so an operator can see where the analyser was guessing before deciding whether to trust a
data model it inferred. Item 38's gate reads the same field.

WHAT THIS DOES NOT DO

Exit 0 even when it reports. A prediction losing an argument with an observation is information,
not a failure -- and a check that can block on a model's size estimate is a check that will be
disabled the first time it is wrong. Exit 1 is reserved for a file it cannot read.

USAGE

    check-scope.py <tasks-dir> [--quiet]

  exit 0  the comparison ran; disagreements, if any, are on stdout
  exit 1  analysis.json or manifest.json is missing or does not parse
  exit 2  usage error
"""

import argparse
import json
import os
import sys

# Core §5's bands, in files. Ordered, because "non-adjacent" is a statement about the order.
BANDS = ["small", "medium", "large"]
BAND_OF_COUNT = [(3, "small"), (8, "medium")]  # above the last boundary is "large"

CONFIDENCE = ["low", "medium", "high"]


def band_of(count):
    for ceiling, name in BAND_OF_COUNT:
        if count <= ceiling:
            return name
    return "large"


def disagrees(predicted, observed):
    """True only for non-adjacent bands. Unknown values never disagree -- they are absent data,
    and reporting absent data as a conflict is how a check earns its reputation for crying wolf.
    """
    if predicted not in BANDS or observed not in BANDS:
        return False
    return abs(BANDS.index(predicted) - BANDS.index(observed)) > 1


def load(path, what):
    if not os.path.isfile(path):
        print(f"cannot compare: no {what} at {path}", file=sys.stderr)
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError) as e:
        print(f"cannot compare: {what} does not parse ({e})", file=sys.stderr)
        return None


import importlib.util  # noqa: E402

# One answer to `what does this task descend from`, loaded from the file that writes it. Item 65
# made attribution a list, and a cross-check that reads only the singular key counts an
# integration task once, under whichever feature it happened to name first.
_bm_spec = importlib.util.spec_from_file_location(
    "build_manifest", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "build-manifest.py"))
build_manifest = importlib.util.module_from_spec(_bm_spec)
_bm_spec.loader.exec_module(build_manifest)


def task_counts(manifest):
    """Tasks per source feature, and how many could not be attributed.

    The key is `task_inventory`, which is what `build-manifest.py` has always written. This read
    `manifest["tasks"]` when it shipped, and its test seeded that same invented key -- so the
    check validated the implementation against itself and attributed nothing on a real manifest.
    The test now builds the manifest by RUNNING build-manifest.py, which is the only version of
    this assertion that could have caught it.

    ATTRIBUTION IS ITEM 16's, AND IT LANDED IN GROUP 5d. This file shipped one group earlier,
    when a task carried no <source-feature> at all and the per-feature comparison had nothing to
    run on; item 65 then made an edge repeatable, which is why `edges_of()` is read below rather
    than a single slug. What survives from that period is the COUNT: a task that names no source
    feature is still reported rather than passed over, because a cross-check that quietly
    compares nothing is indistinguishable from one that found no disagreement, and this
    repository has shipped that mistake before. Today an unattributed task means a Layer 0 task,
    which legitimately has no source feature, or a generator that failed to attribute one --
    and only an operator can tell those apart.
    """
    per_feature, unattributed = {}, 0
    for task in manifest.get("task_inventory") or []:
        # A task counts once under EVERY feature it descends from (item 65). One task walking
        # three features and counted under one is what made run 3's `L4-002` look like a
        # `tag-links` task, so dropping `save-link` from scope would have silently taken the
        # only end-to-end assertion of it with them.
        edges = build_manifest.edges_of(task)
        if not edges:
            unattributed += 1
        for edge in edges:
            per_feature[edge["slug"]] = per_feature.get(edge["slug"], 0) + 1
    return per_feature, unattributed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tasks_dir")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    analysis = load(os.path.join(args.tasks_dir, "analysis.json"), "analysis.json")
    manifest = load(os.path.join(args.tasks_dir, "manifest.json"), "manifest.json")
    if analysis is None or manifest is None:
        return 1

    total = len(manifest.get("task_inventory") or [])
    per_feature, unattributed = task_counts(manifest)
    signals = analysis.get("feature_signals") or []

    reports, lines = [], []

    # ---- the CRD path: one document, so the total IS the observation. No attribution needed.
    declared = analysis.get("scope")
    if declared:
        observed = band_of(total)
        lines.append(f"scope: analysis said {declared}; generation produced {total} task(s) "
                     f"({observed})")
        if disagrees(declared, observed):
            reports.append(f"scope: the analysis called this {declared} and generation produced "
                           f"{total} task(s), which is {observed}. One of the two is wrong -- "
                           f"either the change was under-analysed or the generator ran away")

    # ---- the PRD path: one prediction per feature, compared where the tasks can be attributed.
    for row in signals:
        slug = row.get("feature")
        predicted = row.get("scope")
        if not slug or slug not in per_feature:
            continue
        observed = band_of(per_feature[slug])
        if disagrees(predicted, observed):
            reports.append(f"scope: {slug} was analysed as {predicted} and generated "
                           f"{per_feature[slug]} task(s), which is {observed}")

    if signals and unattributed:
        lines.append(f"scope: {unattributed} of {total} task(s) name no source feature, so they "
                     f"were not compared. Layer 0 tasks legitimately have none; anywhere else "
                     f"this is a task the generator did not attribute")

    # ---- confidence: reported, never compared.
    unsure = [r for r in signals if r.get("confidence") in ("low", "medium")]
    if unsure:
        lines.append("confidence: the analyser was not sure of " +
                     ", ".join(f"{r.get('feature')} ({r.get('confidence')})"
                               for r in sorted(unsure, key=lambda r: CONFIDENCE.index(
                                   r.get("confidence")))))
    declared_conf = analysis.get("confidence")
    if declared_conf in ("low", "medium"):
        lines.append(f"confidence: the impact analysis rated itself {declared_conf}")

    if not args.quiet:
        for line in lines:
            print(f"  {line}")
        for line in reports:
            print(f"  DISAGREES  {line}")
        if not lines and not reports:
            print("  nothing to compare: the analysis carried no scope or confidence")

    return 0


if __name__ == "__main__":
    sys.exit(main())
