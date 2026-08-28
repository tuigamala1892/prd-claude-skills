#!/usr/bin/env python3
"""Do the tasks match the document? (plan item 30, finding P20).

`build-manifest.py` already answers *do the files match the manifest*. This is the same question
asked one level up: **does the task set match the PRD it came from**. It is the general form of
item 23's closing observation -- a check that every producer has a reader -- arriving as a check
that every requirement has an implementer.

It needs item 16. Before `<source-feature>` and `<satisfies-criteria>` existed, attribution was a
string match on a task's name, and nothing here could be asked at all.

FOUR ASSERTIONS, AND A FIFTH THAT LIVES SOMEWHERE ELSE

  1  every in-scope feature has at least one task naming it
  2  every task's <source-feature> resolves to a feature that exists and was not skipped
  3  every in-scope criterion is named by some task, and every id named resolves
  5  no task descends from a wont-have, excluded or superseded feature

The fourth assertion in the plan -- every architecturally-significant feature is named by a
decision record's `**Drives:**` -- is NOT here. `check-references.py` already runs it, and a rule
stated in two programs is a rule that will be changed in one of them. This script names that
script instead.

WHY 3 IS THE ONE THAT DECAYS

Kiro's spec asks for criterion-level traceability and its own samples fail to keep it: the
workflow specifies `_Requirements: 1.2_` and the sample degrades to `_Requirements: 1_`.
Fine-grained traceability survives exactly as long as something verifies it, and this is that
something.

THE SHORTFALL IS REPORTED BY NAME, NEVER AS A COUNT

"4 must-have features have no task" passes a test that a check naming the WRONG four would also
pass. Naming them is what makes this falsifiable -- and it is the same idiom as item 15's
"5 must-have features are not defined enough to break down".

USAGE

    check-coverage.py <prd-dir|crd-file> <tasks-dir> [--priority T] [--requirement-level L]
                      [--json] [--quiet]

  exit 0  the task set covers the document
  exit 1  a shortfall, named
  exit 2  usage error, or an input could not be read
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The selection rules live in ONE place. Re-deriving "was this feature skipped" here would give
# the toolchain two answers to that question, and the interesting failures are exactly the ones
# where they disagree.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "select_features", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "select-features.py"))
select_features = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(select_features)

LEVELS = ["P0", "P1", "P2"]
CRITERION = re.compile(r"<criterion\b([^>]*)>", re.S)


def criteria_of(path):
    """(id, priority) for every criterion in a feature file. Absent priority is P1 -- core §4."""
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    out = []
    for attrs in CRITERION.findall(text):
        cid = re.search(r'id="([^"]*)"', attrs)
        level = re.search(r'priority="(P[012])"', attrs)
        if cid:
            out.append((cid.group(1), level.group(1) if level else "P1"))
    return out


def in_level(level, threshold):
    return LEVELS.index(level) <= LEVELS.index(threshold)


def load_manifest(tasks_dir):
    path = os.path.join(tasks_dir, "manifest.json")
    if not os.path.isfile(path):
        return None, f"no manifest.json in {tasks_dir}"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("task_inventory") or [], None
    except (ValueError, OSError) as e:
        return None, f"manifest.json does not parse ({e})"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", metavar="prd-dir|crd-file")
    ap.add_argument("tasks_dir")
    ap.add_argument("--priority", default="could-have", choices=select_features.SELECTABLE)
    ap.add_argument("--requirement-level", default="P2", choices=LEVELS)
    ap.add_argument("--include-tbd", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if os.path.isdir(args.source):
        rows, err = select_features.features_of_prd(args.source)
        feature_dir = args.source
    elif os.path.isfile(args.source):
        rows, err = select_features.features_of_crd(args.source)
        feature_dir = os.path.dirname(args.source)
    else:
        print(f"usage: no such path: {args.source}", file=sys.stderr)
        return 2
    if err:
        print(f"cannot check coverage: {err}", file=sys.stderr)
        return 2

    inventory, err = load_manifest(args.tasks_dir)
    if err:
        print(f"cannot check coverage: {err}", file=sys.stderr)
        return 2

    # Which features SHOULD have tasks, decided by the same code /breakdown selected with.
    in_scope, skipped = {}, {}
    for row in rows:
        reasons, _warn = select_features.judge(
            row["tier"], row["definition"], row["gaps"], args.priority, args.include_tbd)
        (skipped if reasons else in_scope)[row["slug"]] = dict(row, reasons=reasons)

    covered, cited, bad_source, forbidden = {}, {}, [], []
    for task in inventory:
        slug = task.get("source_feature")
        if not slug:
            continue  # Layer 0 legitimately has none; assertion 1 is what catches a real gap
        covered.setdefault(slug, []).append(task["id"])
        cited.setdefault(slug, set()).update(task.get("satisfies_criteria") or [])

        if slug in skipped:
            why = skipped[slug]["reasons"]
            # Item 13's runtime backstop. A task descending from a feature nobody intends to
            # build means the selection gate did not run, or ran and was ignored.
            if any("item 13" in r for r in why):
                forbidden.append((task["id"], slug, why[0]))
            else:
                bad_source.append((task["id"], slug, why[0]))
        elif slug not in in_scope:
            bad_source.append((task["id"], slug, "names a feature the document does not contain"))

    # ---- 1. an in-scope feature with no task at all, reported BY NAME and by tier.
    uncovered = [r for slug, r in sorted(in_scope.items()) if slug not in covered]

    # ---- 3. criteria, both directions.
    missing_criteria, unknown_criteria = [], []
    for slug, row in sorted(in_scope.items()):
        path = os.path.join(feature_dir, row["file"].replace("/", os.sep)) \
            if os.path.isdir(args.source) else args.source
        declared = criteria_of(path)
        known = {cid for cid, _ in declared}
        want = {cid for cid, level in declared if in_level(level, args.requirement_level)}
        got = cited.get(slug, set())
        for cid in sorted(want - got, key=lambda x: (len(x), x)):
            missing_criteria.append((slug, cid))
        for cid in sorted(got - known, key=lambda x: (len(x), x)):
            unknown_criteria.append((slug, cid))

    problems = bool(uncovered or bad_source or forbidden or missing_criteria or unknown_criteria)

    if args.json:
        print(json.dumps({
            "uncovered_features": [{"slug": r["slug"], "tier": r["tier"]} for r in uncovered],
            "unresolved_source_features": [{"task": t, "slug": s} for t, s, _ in bad_source],
            "forbidden_source_features": [{"task": t, "slug": s} for t, s, _ in forbidden],
            "uncovered_criteria": [{"feature": s, "id": c} for s, c in missing_criteria],
            "unknown_criteria": [{"feature": s, "id": c} for s, c in unknown_criteria],
            "attributed_tasks": sum(len(v) for v in covered.values()),
            "total_tasks": len(inventory),
        }, indent=2))
    elif not args.quiet:
        print(f"{sum(len(v) for v in covered.values())} of {len(inventory)} task(s) attributed; "
              f"{len(in_scope)} feature(s) in scope "
              f"[--priority {args.priority}, --requirement-level {args.requirement_level}]")
        if not problems:
            print("  every in-scope feature and criterion is covered")

    if uncovered:
        by_tier = {}
        for r in uncovered:
            by_tier.setdefault(r["tier"], []).append(r["slug"])
        for tier in ("must-have", "should-have", "could-have"):
            if tier in by_tier:
                print(f"\n{len(by_tier[tier])} {tier} feature(s) have no task: "
                      f"{', '.join(sorted(by_tier[tier]))}", file=sys.stderr)
    for task_id, slug, why in forbidden:
        print(f"  FORBIDDEN  {task_id} descends from `{slug}`, which {why}. The selection gate "
              f"did not run, or ran and was ignored", file=sys.stderr)
    for task_id, slug, why in bad_source:
        print(f"  UNRESOLVED {task_id}: <source-feature>{slug}</source-feature> -- {why}",
              file=sys.stderr)
    if missing_criteria:
        print(f"\n{len(missing_criteria)} criterion/criteria at or above "
              f"{args.requirement_level} are named by no task:", file=sys.stderr)
        for slug, cid in missing_criteria:
            print(f"  {slug} criterion {cid}", file=sys.stderr)
    for slug, cid in unknown_criteria:
        print(f"  UNKNOWN    a task cites {slug} criterion {cid}, which does not exist",
              file=sys.stderr)

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
