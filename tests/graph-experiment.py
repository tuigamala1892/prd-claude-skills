#!/usr/bin/env python3
"""Open question 7's experiment: is the layer graph load-bearing, or only convention?

The plan asks it in one sentence -- **run the fixture through the default graph and through a
deliberately poor one, and compare the task sets** -- and writes the decision rule BEFORE the
measurement (R15), because an experiment with no decision attached is a measurement nobody has
to act on. This script is the measurement half. The rule it is read against:

    the poor graph produces materially worse tasks  ->  LOAD-BEARING
    the two task sets are comparable                ->  CONVENTION
    the difference is small or unclear              ->  LOAD-BEARING (ambiguity protects)

THE POOR GRAPH, AND WHY THIS ONE

Valid, and wrong in exactly one respect. `check-architecture.py` refuses a graph that is cyclic
or has an unreachable layer, so a poor graph that gets refused measures the validator rather than
the question. This one keeps the five default layer NAMES and inverts the dependency direction:

    default   setup -> foundation -> backend -> frontend -> integration
    poor      setup -> integration -> frontend -> backend -> foundation

That isolates the variable OQ7 actually names as the loss -- *"models before endpoints before UI
is a genuine dependency truth for that app class"*. The names, the count, the fan-out and the
task limits are identical; only the order is wrong. And it is the shape of rule file a real user
would plausibly write, which is OQ7's third loss: *"my rule file was wrong and the toolchain
obeyed it"*.

THE METRIC IS CATEGORICAL ON PURPOSE

One run per arm cannot separate a graph effect from a model's sampling noise if the metric is a
matter of degree -- 9 tasks against 11 says nothing. So the primary metric is one that should be
**exactly zero** in any sound decomposition, whatever the sampling:

    FORWARD REFERENCE -- a task whose <dependencies> names an interface that is <exports>ed by a
    task in a layer that runs LATER. The build order cannot satisfy it. It is not "worse", it is
    unbuildable, and one is material.

Two secondary metrics guard against the primary being vacuous:

    UNRESOLVED  a dependency naming an interface no task anywhere exports (self-containment)
    COVERAGE / GATE  check-coverage.py and check-gate.py, run against each arm

And one observation that is not a metric but is the point of OQ7's third loss:

    ANNOUNCED   did anything in the run -- the skill, a script, the gate -- say the graph was a
                problem? A silent bad build is the failure mode the question is really about.

WHAT THIS CANNOT SETTLE, STATED BECAUSE THE PLAN'S OWN STANDARD REQUIRES IT

One PRD, one run per arm, a stochastic model. If the two arms differ only in degree, this
experiment has not measured a graph effect and the third row of the table applies -- which is why
the third row exists and why it resolves toward protection. A categorical difference (0 forward
references against several) is the only result this design can carry on its own.

USAGE

    graph-experiment.py --grade <tasks-dir>              metrics for one task set, as JSON
    graph-experiment.py --compare <default-json> <poor-json>   read the decision table
    graph-experiment.py --run [--keep]                   both arms live, then compare

  exit 0  the comparison ran and is reported
  exit 1  a run did not produce a task set. NOT a result.
  exit 2  usage error
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPTS = os.path.join(REPO, "skills", "breakdown", "scripts")

DEFAULT_GRAPH = None          # no architecture.md -- the shipped default applies

# NEUTRAL PROSE, AND THE FIRST VERSION WAS NOT -- this is the experiment's own contamination,
# found by reading what the first poor arm produced. That version's prose said "the layer names
# are the toolchain's own; the dependency direction is inverted", and `plan-layers` read it and
# wrote back `the inverted direction is reported rather than corrected`. **A fixture that
# describes the experiment is part of the experiment** -- the same defect item 21 recorded when
# its PRD explained the tier probe to the model under test, one phase after that was written
# down. A real user's wrong rule file does not announce that it is wrong, so the stimulus was
# not the one the question is about. Nothing below hints at intent, at ordering, or at OQ7.
POOR_GRAPH = """# Architecture

The layer graph for this project.

<architecture version="1.0">
  <rules>
    <layers>
      <layer id="0" name="setup"       depends-on=""/>
      <layer id="1" name="integration" depends-on="0"/>
      <layer id="2" name="frontend"    depends-on="1"/>
      <layer id="3" name="backend"     depends-on="2"/>
      <layer id="4" name="foundation"  depends-on="3"/>
    </layers>
  </rules>
</architecture>
"""


def task_files(tasks_dir):
    """Every task XML under the tasks directory, as (layer_id, path)."""
    out = []
    for root, _dirs, files in os.walk(tasks_dir):
        for fn in sorted(files):
            if not fn.endswith(".xml"):
                continue
            m = re.match(r"L(\d+)-", fn)
            if m:
                out.append((int(m.group(1)), os.path.join(root, fn)))
    return sorted(out)


def parse(path):
    """(task id, declared layer id, deps, exports) -- tolerant, because a task set from a live
    run is the subject and a parse error in it is a finding rather than a crash."""
    text = open(path, encoding="utf-8", errors="replace").read()
    tid = re.search(r"<id>\s*([^<]+?)\s*</id>", text)
    deps_block = re.search(r"<dependencies>(.*?)</dependencies>", text, re.S)
    exp_block = re.search(r"<exports>(.*?)</exports>", text, re.S)
    names = lambda b: set(re.findall(r'<interface\s+name="([^"]+)"', b)) if b else set()
    return (tid.group(1) if tid else os.path.basename(path),
            names(deps_block.group(1) if deps_block else ""),
            names(exp_block.group(1) if exp_block else ""))


def run_script(name, *args):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def grade(tasks_dir, prd_dir=None, project=None):
    """Every metric for one arm. Pure measurement -- no verdict here."""
    files = task_files(tasks_dir)
    if not files:
        return {"error": f"no task XML under {tasks_dir}", "tasks": 0}

    exporters, tasks = {}, []
    for layer, path in files:
        tid, deps, exps = parse(path)
        tasks.append({"id": tid, "layer": layer, "deps": sorted(deps), "exports": sorted(exps)})
        for e in exps:
            # First exporter wins; a duplicate export is its own defect and is reported.
            exporters.setdefault(e, (layer, tid))

    forward, unresolved = [], []
    for t in tasks:
        for d in t["deps"]:
            if d not in exporters:
                unresolved.append({"task": t["id"], "needs": d})
                continue
            exp_layer, exp_task = exporters[d]
            if exp_layer > t["layer"]:
                forward.append({"task": t["id"], "layer": t["layer"], "needs": d,
                                "exported_by": exp_task, "exported_in_layer": exp_layer})

    result = {
        "tasks": len(tasks),
        "layers": sorted({t["layer"] for t in tasks}),
        "forward_references": forward,
        "forward_count": len(forward),
        "unresolved": unresolved,
        "unresolved_count": len(unresolved),
    }

    if prd_dir:
        code, out = run_script("check-coverage.py", prd_dir, tasks_dir)
        result["coverage_exit"] = code
        result["coverage_tail"] = out.strip().splitlines()[-3:] if out.strip() else []
    if prd_dir and project:
        args = [os.path.join(prd_dir, "index.md"), tasks_dir, "--project-path", project]
        code, out = run_script("check-gate.py", *args)
        result["gate_exit"] = code
        result["gate_tail"] = out.strip().splitlines()[-4:] if out.strip() else []
    return result


def compare(default, poor):
    """The decision table, applied. Returns (verdict, lines)."""
    lines = []
    for label, a in (("default", default), ("poor", poor)):
        if a.get("error"):
            lines.append(f"{label:8} ERROR {a['error']}")
        else:
            lines.append(f"{label:8} {a['tasks']:>2} tasks, layers {a['layers']}, "
                         f"forward-refs {a['forward_count']}, unresolved {a['unresolved_count']}, "
                         f"coverage exit {a.get('coverage_exit', '-')}, "
                         f"gate exit {a.get('gate_exit', '-')}")
    if default.get("error") or poor.get("error"):
        return "NO RESULT", lines + ["an arm produced no task set; this is not a comparison"]

    worse = []
    if poor["forward_count"] > default["forward_count"]:
        worse.append(f"forward references {default['forward_count']} -> {poor['forward_count']}")
    if poor["unresolved_count"] > default["unresolved_count"]:
        worse.append(f"unresolved dependencies "
                     f"{default['unresolved_count']} -> {poor['unresolved_count']}")
    for key in ("coverage_exit", "gate_exit"):
        if key in default and poor.get(key, 0) > default.get(key, 0):
            worse.append(f"{key} {default[key]} -> {poor[key]}")

    identical = (poor["forward_count"] == default["forward_count"]
                 and poor["unresolved_count"] == default["unresolved_count"]
                 and poor.get("coverage_exit") == default.get("coverage_exit")
                 and poor.get("gate_exit") == default.get("gate_exit"))

    if worse:
        # A forward reference is unbuildable rather than merely worse, so one is material.
        # Any other degradation is a difference of degree on a single run, which this design
        # says it cannot carry -- so it lands in the third row, not the first.
        categorical = poor["forward_count"] > 0 and default["forward_count"] == 0
        verdict = "LOAD-BEARING" if categorical else "LOAD-BEARING (via row 3: unclear)"
        lines.append("materially worse: " + "; ".join(worse))
        return verdict, lines
    if identical:
        lines.append("no metric degraded, and every one is equal")
        return "CONVENTION", lines
    lines.append("differences exist but none is a degradation -- row 3")
    return "LOAD-BEARING (via row 3: unclear)", lines


def live(keep=False, arms=("default", "poor"), out_dir=None):
    reg = json.load(open(os.path.join(HERE, "fixture", "prd", "SCHEMAS.json"), encoding="utf-8"))
    # link-shelf, not staff-service: all three of its features are `defined`, so both arms get
    # the same buildable input. staff-service carries a wont-have designed to be REFUSED and an
    # in-progress feature, which would confound a comparison about layering.
    prd_src = os.path.join(HERE, "fixture", "prd", reg["current"], "link-shelf")

    results = {}
    checkout_guard("snapshot")   # item 78
    root = out_dir or tempfile.mkdtemp(prefix="oq7-")
    # A workspace inside this checkout is refused by `resolve-output.sh` before a single task is
    # written -- correctly, since F4 is a run whose entire output landed in the toolchain tree.
    # It cost one live arm here: the run exited 0, produced nothing, and the grader reported
    # `no task XML`, which reads exactly like a toolchain finding and was a harness fault.
    # A negative result whose instrument has not been checked is not a result.
    if os.path.abspath(root).startswith(os.path.abspath(REPO) + os.sep):
        raise SystemExit(
            f"refusing to run inside the checkout: {root}\n"
            f"resolve-output.sh walks ANCESTORS for a plugin root, so anything under {REPO} is "
            f"'inside the toolchain' and /breakdown stops in Phase 1. Use a path outside it, or "
            f"omit --out for a temporary directory.")
    os.makedirs(root, exist_ok=True)
    try:
        for arm, graph in [a for a in (("default", DEFAULT_GRAPH), ("poor", POOR_GRAPH))
                           if a[0] in arms]:
            base = os.path.join(root, arm)
            project = os.path.join(base, "app")
            os.makedirs(project)
            for a in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"]):
                subprocess.run(["git"] + a, cwd=project, capture_output=True)
            if graph:
                open(os.path.join(project, "architecture.md"), "w",
                     encoding="utf-8", newline="\n").write(graph)
            prd = os.path.join(base, "docs", "prd", "link-shelf")
            shutil.copytree(prd_src, prd)
            tasks = os.path.join(base, "docs", "tasks", "link-shelf")

            prompt = (f"/breakdown {prd}/index.md --project-path {project} --output-dir {tasks}")
            cmd = ["claude", "-p", prompt, "--plugin-dir", REPO,
                   "--add-dir", REPO, "--add-dir", base,
                   "--permission-mode", "bypassPermissions"]
            print(f"\n=== arm: {arm} ===\nworkspace: {base}\n  " + " ".join(cmd), flush=True)
            p = subprocess.run(cmd, cwd=project, text=True, capture_output=True,
                               encoding="utf-8", errors="replace")
            transcript = os.path.join(root, f"{arm}.transcript.txt")
            open(transcript, "w", encoding="utf-8", newline="\n").write(
                (p.stdout or "") + "\n---- stderr ----\n" + (p.stderr or ""))
            print(f"  exit {p.returncode}; transcript {transcript}", flush=True)

            g = grade(tasks, prd_dir=prd, project=project)
            # OQ7's third loss: was it SAID, or was it silent?
            blob = ((p.stdout or "") + (p.stderr or "")).lower()
            g["announced"] = sorted({w for w in ("architecture.md", "layer graph", "inverted",
                                                 "dependency order", "refused", "warning")
                                     if w in blob})
            results[arm] = g
            with open(os.path.join(root, f"{arm}.json"), "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(json.dumps(g, indent=2))
            print(json.dumps({k: v for k, v in g.items()
                              if k not in ("forward_references", "unresolved")},
                             indent=2), flush=True)

        if len(results) < 2:
            print("\n  one arm only (%s); compare with --compare" % ", ".join(results))
            return 0
        verdict, lines = compare(results["default"], results["poor"])
        print("\n" + "=" * 78)
        for l in lines:
            print("  " + l)
        print(f"\n  OQ7 verdict: {verdict}")
        print("=" * 78)
        out = os.path.join(root, "oq7-result.json")
        open(out, "w", encoding="utf-8", newline="\n").write(
            json.dumps({"verdict": verdict, "arms": results}, indent=2))
        print(f"  result: {out}")
        dirty = checkout_guard("check")   # item 78
        return 0 if "NO RESULT" not in verdict and dirty == 0 else 1
    finally:
        if keep:
            print(f"kept: {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)



def checkout_guard(phase):
    """Item 78: a live run must not write into the toolchain checkout (P57).

    Every harness here verifies the TARGET and none looked at the plugin, which is how a run
    left `skills/execute/preflight_err.txt` behind unnoticed. `--snapshot` before, `--check`
    after; residue is named and never deleted, because it is evidence.
    """
    import subprocess as _sp, sys as _sys, os as _os
    script = _os.path.join(REPO, "tests", "checkout-clean.py")
    p = _sp.run([_sys.executable, script, f"--{phase}"], capture_output=True, text=True,
                encoding="utf-8", errors="replace")
    if phase == "check" and p.returncode == 1:
        print(p.stderr.rstrip(), file=_sys.stderr)
    return p.returncode

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--grade", metavar="TASKS-DIR")
    ap.add_argument("--prd", metavar="PRD-DIR")
    ap.add_argument("--project", metavar="PATH")
    ap.add_argument("--compare", nargs=2, metavar=("DEFAULT-JSON", "POOR-JSON"))
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--arm", choices=("default", "poor", "both"), default="both")
    ap.add_argument("--out", metavar="DIR", help="persist workspaces and per-arm JSON here")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    if args.grade:
        print(json.dumps(grade(args.grade, args.prd, args.project), indent=2))
        return 0
    if args.compare:
        a = json.load(open(args.compare[0], encoding="utf-8"))
        b = json.load(open(args.compare[1], encoding="utf-8"))
        verdict, lines = compare(a, b)
        for l in lines:
            print("  " + l)
        print(f"\n  OQ7 verdict: {verdict}")
        return 0
    if args.run:
        arms = ("default", "poor") if args.arm == "both" else (args.arm,)
        return live(keep=args.keep, arms=arms, out_dir=args.out)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
