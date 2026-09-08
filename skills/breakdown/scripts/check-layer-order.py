#!/usr/bin/env python3
"""The emitted layer order is the declared graph's (plan item 74, finding P52).

`breakdown-plan-layers` may decide *which* layers exist — that is item 31, and a tier with no
work in it is not a tier. It may **not** decide what order they run in when the project has
declared one. Its own Dependency Ordering section says so:

    A `data` or `runtime` edge that would order a later layer before an earlier one is a
    contradiction, not an ordering. REPORT IT AND PLACE THE TASKS BY LAYER; a feature edge cannot
    override the layer graph, because the layer graph is the project's declared rule and the edge
    is one author's note.

Two obligations. Against an inverted graph a live run discharged the first and not the second: it
wrote an `ordering_conflicts` entry at `severity: critical` naming both layers *and* emitted them
resequenced into the buildable order. The operator is then told the declared rule is in force
while a different one is — P16's shape, with a correct diagnosis attached to it.

THE RULE: SUBSEQUENCE, NOT EQUALITY

Layers with no work are dropped (item 31), so the emitted list is shorter than the declared one.
What must hold is that it is a **subsequence**: every emitted layer appears in the declared graph,
and their relative order is unchanged. `0-setup, 3-backend, 4-foundation` is a legal reading of
`0,1,2,3,4`; `0-setup, 4-foundation, 3-backend` is not, whatever its merits.

WHY THIS IS NOT `check-layering.py`, WHICH LOOKS ADJACENT

They are orthogonal, and the fixtures show it. `inverted/` **obeys** the declared order and
carries 16 unbuildable dependencies — this script passes it and `check-layering.py` refuses it.
`inverted-halted/` **violates** the declared order, and `check-layering.py` cannot judge it at all:
that run emitted no task files, so it exits 2 for want of a subject. The defect P52 describes
happens in `layer_plan.json`, before a single task exists, which is precisely why a check reading
task dependencies cannot be the one that catches it. One script, one job.

WHAT IT DOES NOT DO

No `architecture.json` means no declared graph, and the shipped default carries no promise about
order beyond its own definition — so there is nothing to check and the script says so and exits 0.
It also does not judge whether the declared graph is *good*: `check-layering.py` answers that from
the consequences, and this one answers only whether the project's rule was obeyed.

USAGE

    check-layer-order.py <tasks-dir> [--json] [--quiet]

EXIT CODES

  0  the emitted order is a subsequence of the declared one, or no graph was declared
  1  it is not; declared and emitted are both printed, in order
  2  the artefacts could not be read
"""

import argparse
import json
import os
import sys


def load(path, label):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (ValueError, OSError) as e:
        print(f"REFUSED: {label} could not be read: {e}", file=sys.stderr)
        raise SystemExit(2)


def declared_order(arch):
    """Every declared layer, in order, as `{id}-{name}` -- the directory convention.

    A block with a non-null `applies_to` is instantiated per matching directory, so its layer
    ids repeat across units. Those are flattened here in declaration order: what is being checked
    is relative sequence, and a unit's layers keep theirs within the flattened list.
    """
    out = []
    for block in arch.get("layer_blocks") or []:
        for layer in block.get("layers") or []:
            out.append(f"{layer['id']}-{layer['name']}")
    return out


def is_subsequence(emitted, declared):
    """Returns (ok, first offending emitted layer or None)."""
    it = iter(declared)
    for e in emitted:
        if not any(d == e for d in it):
            return False, e
    return True, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tasks_dir")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.tasks_dir):
        print(f"REFUSED: {args.tasks_dir} is not a directory", file=sys.stderr)
        return 2

    arch = load(os.path.join(args.tasks_dir, "architecture.json"), "architecture.json")
    plan = load(os.path.join(args.tasks_dir, "layer_plan.json"), "layer_plan.json")
    if plan is None:
        print(f"REFUSED: no layer_plan.json under {args.tasks_dir}", file=sys.stderr)
        return 2

    emitted = [l["id"] for l in (plan.get("layers") or []) if l.get("id")]
    if not emitted:
        print(f"REFUSED: layer_plan.json emits no layers", file=sys.stderr)
        return 2

    if arch is None or not declared_order(arch):
        if args.json:
            print(json.dumps({"declared": [], "emitted": emitted, "checked": False}, indent=2))
        elif not args.quiet:
            print("layer order: no architecture.json, so no declared graph to obey")
        return 0

    declared = declared_order(arch)
    ok, offender = is_subsequence(emitted, declared)

    if args.json:
        print(json.dumps({"declared": declared, "emitted": emitted,
                          "checked": True, "ok": ok, "offender": offender}, indent=2))
        return 0 if ok else 1

    if ok:
        if not args.quiet:
            print(f"layer order: OK -- {' -> '.join(emitted)} follows the declared graph")
        return 0

    print("REFUSED: the emitted layer order is not the declared one.", file=sys.stderr)
    print(f"  declared  {' -> '.join(declared)}", file=sys.stderr)
    print(f"  emitted   {' -> '.join(emitted)}", file=sys.stderr)
    print(f"  first out of sequence: {offender}", file=sys.stderr)
    print("\nDropping a layer with no work in it is allowed and expected (item 31); RESEQUENCING "
          "is not. If the declared graph cannot be built in its own order, that is a conflict to "
          "report and for a person to fix in architecture.md -- placing the tasks in a different "
          "order tells the operator their declared rule is in force while a different one is.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
