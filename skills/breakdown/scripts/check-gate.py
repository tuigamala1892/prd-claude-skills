#!/usr/bin/env python3
"""The gate between `/breakdown` and `/execute` (plan item 38, finding P25).

**Placed at that boundary and nowhere else.** Not inside `/execute`, which is the unattended
overnight case P19 correctly refuses to block. `/breakdown` and `/execute` are already separate
invocations, so an approval between them costs nothing at 2am -- and item 30's coverage check
already runs exactly there, which makes this a report-and-confirm over work that is happening
anyway rather than a new phase.

THREE ASSERTIONS, EACH REPORTED BY NAME

  1  every in-scope feature has at least one task                        item 30
  2  every architecturally-significant feature is named by a record's
     **Drives:**, or the absence is reported                             items 35, 36
  3  no gap that BLOCKS EXECUTION is left in a feature that was built    item 29

THIS SCRIPT DECIDES NOTHING THAT ANOTHER SCRIPT ALREADY DECIDES

Assertions 1 and 2 are `check-coverage.py`'s and `check-references.py`'s, and they are RUN here
rather than reimplemented. A gate that re-derived coverage would be a second answer to *"is this
feature covered"*, and the interesting failures are exactly the ones where two answers disagree.
What the gate adds is the third assertion, the aggregation, and the stop.

Assertion 3 is here because nothing else asks it. `select-features.py` refuses a feature carrying
a `specification` gap at SELECTION time; this asks the question after generation, over the
features that actually produced tasks -- which is a different set whenever `--include-tbd` or a
`--priority` threshold was passed, and a different question from *should we have started*.

  specification | dependency | decision   BLOCK execution     -- reported, and they stop the gate
  ownership | evidence                    WARN                -- reported, and they do not

WHAT THE SWITCH CONTROLS, AND WHAT IT DOES NOT

`architecture.md`'s `<design-track enabled=>` decides whether the gate STOPS, never whether it
CHECKS. With `enabled="false"` it prints the report and returns 0 even when something is wrong;
with it enabled, a finding exits 1 and `/breakdown` must ask before `/execute` may run. **The
report is the valuable half** -- the confirmation only matters if somebody is there, and the three
assertions are worth running either way.

`--require-confirmation` forces the stopping behaviour without an `architecture.md`, for a caller
that has already decided somebody is present.

USAGE

    check-gate.py <prd-dir|crd-file> <tasks-dir> [--project-path DIR]
                  [--priority TIER] [--requirement-level LEVEL]
                  [--require-confirmation] [--quiet] [--json]

EXIT CODES

  0  nothing to confirm, or the design track is off so the report is advisory
  1  the design track is on and there is something to confirm
  2  usage error, or an input could not be read
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "select_features", os.path.join(_HERE, "select-features.py"))
_sel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sel)

# Core 6. Three kinds stop an overnight run; two are worth saying and not worth stopping for.
BLOCKING_GAPS = {"specification", "dependency", "decision"}

SOURCE_FEATURE = re.compile(r"<source-feature>\s*([a-z0-9-]+)\s*</source-feature>")


def run(script, *args):
    """Run one of the owning checks and return (exit code, combined output)."""
    p = subprocess.run([sys.executable, os.path.join(_HERE, script), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def design_track(project_path):
    """`<design-track>` from architecture.md, via the script that owns parsing it.

    Absent file, absent element and a project that never opted in all mean the same thing --
    off -- and that is the shipped behaviour rather than a fallback.
    """
    if not project_path:
        return {"enabled": False, "adr_dir": None, "source": "no --project-path given"}
    p = subprocess.run([sys.executable, os.path.join(_HERE, "check-architecture.py"),
                        project_path, "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        # A present-and-broken architecture.md is check-architecture's refusal to report, not
        # this script's to swallow. Say so and treat the track as off.
        return {"enabled": False, "adr_dir": None,
                "source": "architecture.md could not be read -- see check-architecture.py"}
    try:
        parsed = json.loads(p.stdout)
    except Exception:
        return {"enabled": False, "adr_dir": None, "source": "architecture.md declares nothing"}
    track = parsed.get("design_track") or {}
    return {"enabled": bool(track.get("enabled")), "adr_dir": track.get("adr_dir"),
            "source": parsed.get("path") or "architecture.md"}


def built_features(tasks_dir):
    """Every feature slug some task descends from -- the set the gate asks about."""
    slugs = set()
    for dirpath, _dirs, names in os.walk(tasks_dir):
        for name in sorted(names):
            if not name.lower().endswith(".xml"):
                continue
            with open(os.path.join(dirpath, name), encoding="utf-8", errors="replace") as f:
                slugs.update(SOURCE_FEATURE.findall(f.read()))
    return slugs


def blocking_gaps(prd_dir, built):
    """Assertion 3: a gap that blocks execution, in a feature that produced tasks."""
    findings = []
    rows, err = _sel.features_of_prd(prd_dir)
    if err:
        return findings, err
    for row in rows:
        if row["slug"] not in built:
            continue
        for kind in sorted(set(row["gaps"]) & BLOCKING_GAPS):
            findings.append(f"{row['slug']}: carries a <gap kind=\"{kind}\"> and has tasks. "
                            f"An undecided question built anyway is an invented one")
    return findings, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("document", metavar="prd-dir|crd-file")
    ap.add_argument("tasks_dir", metavar="tasks-dir")
    ap.add_argument("--project-path", default=None)
    ap.add_argument("--priority", default=None)
    ap.add_argument("--requirement-level", default=None)
    ap.add_argument("--require-confirmation", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.tasks_dir):
        print(f"REFUSED  not a directory: {args.tasks_dir}", file=sys.stderr)
        return 2
    if not os.path.exists(args.document):
        print(f"REFUSED  no such document: {args.document}", file=sys.stderr)
        return 2

    track = design_track(args.project_path)

    # ---- 1. coverage, run by the script that owns it
    cov_args = [args.document, args.tasks_dir]
    if args.priority:
        cov_args += ["--priority", args.priority]
    if args.requirement_level:
        cov_args += ["--requirement-level", args.requirement_level]
    cov_code, cov_out = run("check-coverage.py", *cov_args)

    # ---- 2. significance, likewise. Reports and never refuses (item 35), so its exit code is
    #         not the signal -- the STALE lines are.
    ref_args = [args.document]
    if track["adr_dir"] and args.project_path:
        ref_args += ["--adr-dir", os.path.normpath(
            os.path.join(args.project_path, track["adr_dir"]))]
    ref_code, ref_out = (0, "") if os.path.isfile(args.document) else run(
        "check-references.py", *ref_args)
    undriven = [ln.strip() for ln in ref_out.splitlines()
                if "STALE" in ln and "architecturally significant" in ln]

    built = built_features(args.tasks_dir) if os.path.isdir(args.document) else set()

    # Scoped to what was BUILT, and that is the gate's decision rather than a re-reading of
    # check-references's. Its assertion is about the PRD; this one is about whether THIS task
    # set may proceed, and a significant feature nobody built cannot block a run of the ones
    # that were. The unscoped list is still in that script's own output.
    if built:
        undriven = [ln for ln in undriven if any(f"{slug}.md" in ln for slug in built)]

    # ---- 3. the gaps that block execution, in features that produced tasks
    gaps, gap_err = [], None
    if os.path.isdir(args.document):
        gaps, gap_err = blocking_gaps(args.document, built)

    findings = []
    if cov_code != 0:
        findings.append(("coverage", cov_out))
    for line in undriven:
        findings.append(("significance", line))
    for line in gaps:
        findings.append(("blocked", line))
    if gap_err:
        findings.append(("blocked", f"could not read the document: {gap_err}"))

    if args.json:
        print(json.dumps({"design_track": track, "coverage_exit": cov_code,
                          "findings": [{"assertion": a, "detail": d} for a, d in findings]},
                         indent=2))
    elif not args.quiet:
        print(f"GATE  {args.tasks_dir}")
        print(f"  design track: {'ON -- confirmation required' if track['enabled'] else 'off'} "
              f"({track['source']})")
        print(f"  1 coverage      {'OK' if cov_code == 0 else 'SHORTFALL'}")
        for line in cov_out.splitlines():
            if line.strip():
                print(f"      {line.strip()}")
        print(f"  2 significance  {'OK' if not undriven else str(len(undriven)) + ' undriven'}")
        for line in undriven:
            print(f"      {line}")
        print(f"  3 blocked       {'OK' if not gaps else str(len(gaps)) + ' blocking gap(s)'}")
        for line in gaps:
            print(f"      {line}")

    stop = track["enabled"] or args.require_confirmation
    if not findings:
        print("gate: nothing to confirm")
        return 0
    print(f"gate: {len(findings)} finding(s)"
          + ("; confirmation required before /execute" if stop
             else "; design track off, so this is a report"))
    return 1 if stop else 0


if __name__ == "__main__":
    sys.exit(main())
