#!/usr/bin/env python3
"""No task may depend on something a LATER layer exports (plan item 73, finding P51).

Open question 7 asked whether the layer graph is load-bearing or only convention, and the
experiment answered LOAD-BEARING. The arm that settled it produced 14 tasks in which backend
endpoints imported `Link`, `get_db` and `db_session` from a layer the declared graph runs
*after* them -- 16 edges that cannot be satisfied in the order they will be executed. Every
existing check passed: `check-coverage.py` exit 0, `check-gate.py` exit 0.

WHY THIS IS NOT THE MITIGATION THE PLAN ORIGINALLY SPECIFIED

Item 73's parent text asks `/breakdown` to *report when a supplied graph decomposes materially
differently from the shipped default*. That needs a baseline, a second decomposition to compare
against, and a threshold for "materially". The experiment showed something cheaper and stronger:
**the defect is visible inside a single task set.** A task naming an interface that a later task
exports is unbuildable on its own terms, with no default to compare against and no judgement
about degree. So this checks that instead, and the departure is recorded in the ledger.

WHY AN EXIT CODE AND NOT AN INSTRUCTION

Two runs of the *same* inverted graph behaved differently: one obeyed it and emitted the 16
edges silently, the other noticed and refused. **The protection was a model judgement, and it
fired in one run of two.** That is item 4.13 -- a guard a model can reason past is not a guard --
arriving at open question 7.

WHAT COUNTS, AND WHAT DELIBERATELY DOES NOT

  counts        a dependency whose interface name is EXPORTED by another task in this set,
                where that task's layer runs later in the planned order
  does NOT      a dependency naming something no task exports. Those are external libraries --
                `python`, `sqlite3`, `pydantic`, `fastapi.testclient.TestClient` -- declared as
                interfaces, and treating them as unmet contracts made a first version of this
                metric report 9 violations against a task set that was completely sound

ORDER COMES FROM THE PLAN, NOT FROM THE LAYER NUMBER

`layer_plan.json` lists the layers it emitted, in the order `/execute` will run them, and
`resolve-layers.py` reads that same list. A layer id is not a rank: a project may declare
`<layers>` whose ids ascend while its dependencies do not, which is exactly the fixture that
produced this finding.

USAGE

    check-layering.py <tasks-dir> [--json] [--quiet]

EXIT CODES

  0  no task depends on a later layer
  1  at least one does; each is named with the task, the interface and both layers
  2  the task set could not be read
"""

import argparse
import json
import os
import re
import sys

INTERFACE = re.compile(r'<interface\s+name="([^"]+)"')


def layer_order(tasks_dir):
    """The order /execute will run, from layer_plan.json; directory order as a fallback.

    The fallback matters: a task set generated before item 73, or one whose plan was removed,
    still has directories, and refusing to check it would make this guard skippable by deletion.
    """
    plan = os.path.join(tasks_dir, "layer_plan.json")
    if os.path.isfile(plan):
        try:
            layers = json.load(open(plan, encoding="utf-8")).get("layers") or []
            ids = [l.get("id") for l in layers if l.get("id")]
            if ids:
                return ids, "layer_plan.json"
        except (ValueError, OSError):
            pass
    dirs = sorted(d for d in os.listdir(tasks_dir)
                  if os.path.isdir(os.path.join(tasks_dir, d)) and re.match(r"\d+-", d))
    return dirs, "directory order (no layer_plan.json)"


def collect(tasks_dir, order):
    """Every task, with the rank of the layer it sits in."""
    rank = {name: i for i, name in enumerate(order)}
    tasks = []
    for layer_dir in sorted(os.listdir(tasks_dir)):
        full = os.path.join(tasks_dir, layer_dir)
        if not os.path.isdir(full) or layer_dir not in rank:
            continue
        for fn in sorted(os.listdir(full)):
            if not fn.endswith(".xml"):
                continue
            text = open(os.path.join(full, fn), encoding="utf-8", errors="replace").read()
            tid = re.search(r"<id>\s*([^<]+?)\s*</id>", text)
            deps = re.search(r"<dependencies>(.*?)</dependencies>", text, re.S)
            exps = re.search(r"<exports>(.*?)</exports>", text, re.S)
            tasks.append({
                "id": tid.group(1) if tid else fn,
                "layer": layer_dir,
                "rank": rank[layer_dir],
                "deps": INTERFACE.findall(deps.group(1)) if deps else [],
                "exports": INTERFACE.findall(exps.group(1)) if exps else [],
            })
    return tasks


def violations(tasks):
    exporters = {}
    for t in tasks:
        for e in t["exports"]:
            exporters.setdefault(e, t)
    out = []
    for t in tasks:
        for d in t["deps"]:
            src = exporters.get(d)
            if src and src["rank"] > t["rank"]:
                out.append({"task": t["id"], "layer": t["layer"], "needs": d,
                            "exported_by": src["id"], "exported_in": src["layer"]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tasks_dir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.tasks_dir):
        print(f"REFUSED: {args.tasks_dir} is not a directory", file=sys.stderr)
        return 2
    try:
        order, source = layer_order(args.tasks_dir)
        tasks = collect(args.tasks_dir, order)
    except OSError as e:
        print(f"REFUSED: could not read the task set: {e}", file=sys.stderr)
        return 2
    if not tasks:
        print(f"REFUSED: no task XML under {args.tasks_dir}", file=sys.stderr)
        return 2

    bad = violations(tasks)
    if args.json:
        # The object and nothing else: group 8b found a --json flag printing a human summary
        # after the object, so `| jq` failed on trailing data and nothing had ever parsed it.
        print(json.dumps({"order": order, "order_source": source, "tasks": len(tasks),
                          "violations": bad}, indent=2))
        return 1 if bad else 0

    if not args.quiet:
        print(f"layering: {len(tasks)} task(s), order {' -> '.join(order)} [{source}]")
    if not bad:
        if not args.quiet:
            print("layering: OK -- no task depends on a layer that runs after it")
        return 0

    print(f"REFUSED: {len(bad)} dependenc(ies) point at a layer that runs LATER. The build order "
          f"cannot satisfy them.", file=sys.stderr)
    for v in bad:
        print(f"  {v['task']} ({v['layer']}) needs {v['needs']!r}, exported by "
              f"{v['exported_by']} in {v['exported_in']}", file=sys.stderr)
    print("\nEither the declared <layers> graph orders these the wrong way round, or generation "
          "put a task in the wrong layer. Both are fixable; neither is fixable by this script, "
          "because choosing between them is a judgement about the project.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
