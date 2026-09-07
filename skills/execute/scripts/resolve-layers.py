#!/usr/bin/env python3
"""Which layers this run executes, and in which order. Derived, never recited.

**`/execute` iterated a hardcoded list of five names** — `0-setup`, `1-foundation`, `2-backend`,
`3-frontend`, `4-integration` — while its Critical Rules said *"Never skip layers: Execute in
order (0→1→2→3→4)"*. Item 31 made the layer set derived from what the document puts work in,
item 61 removed the instruction forbidding that derivation, item 62 made the task schema admit any
layer id, and item 28 let a project declare its own `<layers>` graph instantiated per service.
**The producer derives and the consumer still recited** (**P44**).

The failure is silent and total rather than partial: a project whose layers are named anything
else gets a run that iterates five names, finds no tasks under any of them, skips every layer, and
reports a completed run of **zero tasks**. Nothing fails, because nothing runs.

`/breakdown` Phase 4 already says the true rule — *"Process exactly the layers `layer_plan.json`
contains — never a list written here"*. This is that rule for the other end of the pipeline, as a
script rather than a sentence, because a list in prose is exactly what went stale.

TWO SOURCES, AND THEY ANSWER DIFFERENT QUESTIONS

  layer_plan.json    ORDER. What /breakdown intended, in dependency order
  manifest.json      EXISTENCE. What was actually generated, derived from the files on disk

So the answer is the planned order, filtered to the layers that have tasks, followed by any layer
that has tasks and no plan entry — reported, and executed anyway, because the task files are the
deliverable and refusing to run work that exists helps nobody. A planned layer with no tasks is
also reported: it is usually item 31 dropping a tier correctly, and occasionally generation
failing silently, and only an operator can tell those apart.

Usage:
    resolve-layers.py <tasks-path> [--layer NAME] [--json]

Exit codes:
    0  resolved. stdout is the ordered layer list (one per line, or --json)
    1  REFUSED -- no layer has any task, or --layer names one that does not exist here
    2  could not read layer_plan.json or manifest.json
"""

import argparse
import io
import json
import os
import sys


def load(path, what):
    try:
        with io.open(path, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"no {what} in {os.path.dirname(path)} -- run /breakdown first"
    except ValueError as e:
        return None, f"{what} is not readable JSON: {e}"


def planned_layers(plan):
    """The layer ids `/breakdown` recorded, in the order it recorded them.

    `id` is the directory name -- `0-setup`, or `2-service-billing` for a declared graph
    instantiated per service (item 28). Anything without one is skipped rather than guessed at:
    a layer this cannot name is a layer nothing can execute.
    """
    out = []
    for entry in plan.get("layers") or []:
        lid = (entry.get("id") or "").strip()
        if lid and lid not in out:
            out.append(lid)
    return out


def layers_with_tasks(manifest):
    counts = {}
    for entry in manifest.get("task_inventory") or []:
        layer = (entry.get("layer") or "").strip()
        if layer:
            counts[layer] = counts.get(layer, 0) + 1
    if not counts:
        # A manifest written before item 32's inventory, or one with no tasks: fall back to the
        # summary, which has carried the same counts since the beginning.
        counts = dict((manifest.get("summary") or {}).get("tasks_per_layer") or {})
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tasks_path")
    ap.add_argument("--layer", default=None, help="run one layer; refused if the plan has no such layer")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    plan, err = load(os.path.join(args.tasks_path, "layer_plan.json"), "layer_plan.json")
    if err:
        print(f"cannot resolve layers: {err}", file=sys.stderr)
        return 2
    manifest, err = load(os.path.join(args.tasks_path, "manifest.json"), "manifest.json")
    if err:
        print(f"cannot resolve layers: {err}", file=sys.stderr)
        return 2

    planned = planned_layers(plan)
    counts = layers_with_tasks(manifest)

    ordered = [lid for lid in planned if counts.get(lid)]
    unplanned = sorted(lid for lid in counts if lid not in planned)
    ordered += unplanned
    empty = [lid for lid in planned if not counts.get(lid)]

    result = {
        "layers": ordered,
        "tasks_per_layer": {lid: counts.get(lid, 0) for lid in ordered},
        "planned_without_tasks": empty,
        "tasks_without_plan": unplanned,
        "total_tasks": sum(counts.values()),
    }

    # Refuse BEFORE printing anything on stdout. A caller that reads the list and the exit code
    # in that order gets a layer set from a run that was refused, which is the shape of every
    # "it printed something so it must have worked" failure this toolchain has had.
    if not ordered:
        print(f"REFUSED: no layer in {args.tasks_path} has any task. A run with nothing to "
              f"execute must not report a completed run of zero -- that is P44, and it is what "
              f"a hardcoded layer list produces against a project that named its layers "
              f"anything else.", file=sys.stderr)
        return 1

    if args.layer is not None and args.layer not in ordered:
        print(f"REFUSED: --layer {args.layer} is not a layer of this run. It has: "
              f"{', '.join(ordered)}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for lid in ordered:
            print(lid)

    for lid in unplanned:
        print(f"NOTE: {counts[lid]} task(s) in `{lid}`, which layer_plan.json does not declare. "
              f"Running it anyway -- the task files are the deliverable -- but the plan and the "
              f"files disagree, which is a /breakdown defect worth reporting.", file=sys.stderr)
    for lid in empty:
        print(f"NOTE: `{lid}` is planned and has no tasks. Usually item 31 dropping a tier "
              f"correctly; occasionally generation failing quietly.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
