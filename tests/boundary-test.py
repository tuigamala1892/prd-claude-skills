#!/usr/bin/env python3
"""The runtime test across the `/breakdown` -> `/execute` boundary (plan item 59, A8/R13).

Items 13-17, 19, 20 and 30-32 all specify behaviour at that boundary, and **no run had ever
crossed it with an input this plan's schema describes**. For a document whose central
methodological complaint is that static agreement is not evidence, that ratio was the wrong way
round.

TWO MODES, AND THE SPLIT IS THE POINT -- the same split `probe-p1.py` makes, for the same reason

    boundary-test.py --grade <prd-dir> <tasks-dir>    offline. Assert against a task set.
    boundary-test.py --run                            live. Build a workspace, run /breakdown,
                                                      then grade what it produced.

The grader is a separate mode so it can be exercised without spending a live run. **A grader
that has only ever run behind the expensive path is a grader nobody has checked** -- and the
regression suite drives `--grade` against a synthesised task set on every run, which is what
keeps these five assertions honest between live measurements.

FIVE ASSERTIONS, IN THE PLAN'S ORDER

  1  criteria arrive VERBATIM, with their ids            item 17 -- the one that would have
                                                         failed for the whole life of the
                                                         toolchain
  2  <source-feature> resolves both ways                 items 16, 30
  3  the coverage report names a REAL shortfall          item 30
  4  both tiers are reported                             item 19
  5  a won't-have task is refused at preflight           item 20

ASSERTION 3 IS THE ONE WORTH INSISTING ON

A coverage check reporting *"4 features have no task"* passes a test that a check reporting the
WRONG four would also pass. So this removes one named feature's tasks and asserts the report names
**that feature, by slug, and no other**. Naming the shortfall is what makes item 30 falsifiable;
a test that does not force it cannot detect a check that counts correctly and attributes wrongly.

USAGE

    boundary-test.py --grade <prd-dir> <tasks-dir> [--project <path>] [--quiet]
    boundary-test.py --run [--keep]

  exit 0  every assertion held
  exit 1  at least one failed, each named
  exit 2  nothing to grade -- the run did not happen. NOT a pass.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPTS = os.path.join(REPO, "skills", "breakdown", "scripts")
EXEC_SCRIPTS = os.path.join(REPO, "skills", "execute", "scripts")

CRITERION = re.compile(r"<criterion\b([^>]*)>(.*?)</criterion>", re.S)
FEATURE_ENTRY = re.compile(r'<feature\s+priority="([^"]+)"\s+file="([^"]+)"')


def norm(text):
    """Whitespace-normalised body. Indentation legitimately differs between a feature file and
    a task; the WORDS are what item 17 requires to be unchanged."""
    return " ".join((text or "").split())


def criteria_in(text):
    out = {}
    for attrs, body in CRITERION.findall(text):
        cid = re.search(r'id="([^"]*)"', attrs)
        if cid:
            out[cid.group(1)] = norm(body)
    return out


def criteria_by_feature(text):
    """A task's carried criteria, grouped by the feature each came from (item 65).

    `<acceptance-criteria>` may wrap its criteria in `<from-feature slug="...">` blocks, and must
    when the task descends from more than one feature: criterion ids are per feature, so `1` from
    `save-link` and `1` from `tag-links` are different requirements with the same name. Criteria
    outside any wrapper are returned under None -- unambiguous for a single-feature task, and a
    failure for a task that spans several.
    """
    m = re.search(r"<acceptance-criteria>(.*?)</acceptance-criteria>", text, re.S)
    if not m:
        return {}
    body = m.group(1)
    groups, rest = {}, body
    for slug, inner in re.findall(r'<from-feature\s+slug="([^"]+)"\s*>(.*?)</from-feature>',
                                  body, re.S):
        groups[slug] = criteria_in(inner)
        rest = rest.replace(inner, "")
    loose = criteria_in(rest)
    if loose:
        groups[None] = loose
    return groups


def edges_in(text):
    """Every feature a task descends from, in either shape (item 65).

    New: `<source-feature slug="save-link" moscow="must-have" satisfies-criteria="1,4"
    requirement-level="P0"/>`, repeatable. Old: one `<source-feature>slug</source-feature>` with
    sibling `<moscow>`, `<satisfies-criteria>` and `<requirement-level>` elements, which still
    fill in an attribute the new form omits.

    P43 is why this repeats: three live runs met a task covering more than one feature and
    invented three different workarounds, the worst of them silent.
    """
    m = re.search(r"<meta>(.*?)</meta>", text, re.S)
    if not m:
        return []
    meta = m.group(1)
    sib = {tag: meta_of(text, tag)
           for tag in ("moscow", "satisfies-criteria", "requirement-level")}
    edges = []
    for attrs, body in re.findall(r"<source-feature\b([^>]*?)(?:/>|>(.*?)</source-feature>)",
                                  meta, re.S):
        def attr(name):
            a = re.search(r'\b%s="([^"]*)"' % name, attrs)
            return norm(a.group(1)) if a else None
        slug = attr("slug") or norm(body)
        if not slug:
            continue
        cites = attr("satisfies-criteria") or sib.get("satisfies-criteria") or ""
        edges.append({"slug": slug,
                      "moscow": attr("moscow") or sib.get("moscow"),
                      "level": attr("requirement-level") or sib.get("requirement-level"),
                      "cites": [x.strip() for x in cites.split(",") if x.strip()]})
    return edges


def task_files(tasks_dir):
    for dirpath, dirnames, filenames in os.walk(tasks_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(".xml"):
                yield os.path.join(dirpath, name)


def meta_of(text, tag):
    m = re.search(r"<meta>(.*?)</meta>", text, re.S)
    if not m:
        return None
    el = re.search(r"<%s>\s*(.*?)\s*</%s>" % (tag, tag), m.group(1), re.S)
    return norm(el.group(1)) if el else None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# --------------------------------------------------------------------------------- assertions

def grade(prd_dir, tasks_dir, project=None, quiet=False):
    failures, notes, qualified = [], [], []

    features = {}
    index = os.path.join(prd_dir, "index.md")
    if not os.path.isfile(index):
        print(f"nothing to grade: no index.md in {prd_dir}", file=sys.stderr)
        return 2
    with open(index, encoding="utf-8") as f:
        for tier, rel in FEATURE_ENTRY.findall(f.read()):
            slug = os.path.splitext(os.path.basename(rel))[0]
            path = os.path.join(prd_dir, rel.replace("/", os.sep))
            text = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
            features[slug] = {"tier": tier, "criteria": criteria_in(text)}

    tasks = []
    for path in task_files(tasks_dir):
        text = open(path, encoding="utf-8").read()
        edges = edges_in(text)
        tasks.append({
            "path": path,
            "id": meta_of(text, "id") or os.path.basename(path),
            "edges": edges,
            "slugs": [e["slug"] for e in edges],
            "groups": criteria_by_feature(text),
            "criteria": criteria_in(text),
        })
    if not tasks:
        print(f"nothing to grade: no task files under {tasks_dir}", file=sys.stderr)
        return 2

    attributed = [t for t in tasks if t["edges"]]
    if not attributed:
        print(f"nothing to grade: none of {len(tasks)} task(s) carries a <source-feature>. "
              f"Item 16 did not reach this run, so assertions 1-4 have no subject",
              file=sys.stderr)
        return 2

    # ---- 1. Criteria arrive verbatim, with their ids. P2's fix, and the assertion that would
    #         have failed for the whole life of the toolchain.
    for t in attributed:
        # Which carried criteria belong to which feature. A single-feature task may leave them
        # ungrouped -- there is nothing to confuse them with -- and a task spanning features must
        # group them, because ids repeat across features and `1` alone names two requirements.
        loose = t["groups"].get(None) or (t["criteria"] if not t["groups"] else {})
        if len(t["edges"]) > 1 and loose:
            failures.append(
                f"1: {t['id']} descends from {len(t['edges'])} features and carries "
                f"{len(loose)} criterion/criteria outside any <from-feature>. Ids repeat across "
                f"features, so an ungrouped id names two requirements at once")

        for edge in t["edges"]:
            source = features.get(edge["slug"])
            if not source:
                continue  # assertion 2's problem, not this one
            carried = t["groups"].get(edge["slug"])
            if carried is None:
                carried = loose if len(t["edges"]) == 1 else {}
            for cid, body in carried.items():
                want = source["criteria"].get(cid)
                if want is None:
                    # `feature#3` is a notation no schema defines, and the first live run
                    # invented it for 37 criteria because <source-feature> was single-valued and
                    # a task carrying a neighbour's criterion had no way to say whose it was.
                    # Item 65 gave it one, so this is now a FAILURE rather than a finding: the
                    # gap it worked around is closed, and <from-feature> is the supported answer.
                    if "#" in cid:
                        qualified.append(f"{t['id']}: {cid}")
                        continue
                    failures.append(f"1: {t['id']} carries a criterion {cid} that "
                                    f"{edge['slug']} does not have")
                elif want != body:
                    failures.append(
                        f"1: {t['id']} REWORDED {edge['slug']} criterion {cid}.\n"
                        f"      PRD:  {want}\n"
                        f"      task: {body}")
            for cid in edge["cites"]:
                if cid not in carried and not any(c.endswith("#" + cid) for c in carried):
                    failures.append(
                        f"1: {t['id']} cites {edge['slug']} criterion {cid} in "
                        f"<source-feature satisfies-criteria=> but does not carry it in "
                        f"<context>")
    notes.append(f"1: {sum(len(t['criteria']) for t in attributed)} criterion copy/copies "
                 f"checked against the PRD, verbatim")
    if qualified:
        failures.append(f"1: {len(qualified)} carried criterion id(s) are QUALIFIED "
                        f"(`feature#id`), a notation the schema does not define: "
                        f"{', '.join(qualified[:5])}. Item 65 made <source-feature> repeatable "
                        f"and gave <acceptance-criteria> its <from-feature> grouping, so a task "
                        f"carrying a neighbour's criterion can now say whose it is. This used to "
                        f"be a finding because the schema could not express it; it can")

    # ---- 2. <source-feature> resolves BOTH ways.
    named = {slug for t in attributed for slug in t["slugs"]}
    for slug in sorted(named - set(features)):
        failures.append(f"2: a task names <source-feature slug=\"{slug}\">, which the "
                        f"PRD does not contain")
    buildable = {s for s, f in features.items() if f["tier"] != "wont-have"}
    for slug in sorted(buildable - named):
        failures.append(f"2: {slug} is in scope and no task names it")
    notes.append(f"2: {len(named)} feature(s) named by {len(attributed)} attributed task(s)")

    # ---- 3. The coverage report names a REAL shortfall, by slug.
    victim = sorted(named & buildable)[0] if (named & buildable) else None
    # Removing one feature's tasks can uncover ANOTHER feature, when a task walks both -- which
    # is the ordinary case since item 65 and was unrepresentable before it. So the expectation is
    # computed rather than assumed to be `[victim]`: what should be reported is every feature
    # whose last task went with it.
    survivors = {}
    for t in attributed:
        if victim in t["slugs"]:
            continue
        for slug in t["slugs"]:
            survivors[slug] = survivors.get(slug, 0) + 1
    expected_uncovered = sorted(s for s in (named & buildable) if not survivors.get(s))
    if victim is None:
        failures.append("3: no in-scope feature has tasks, so the shortfall probe cannot run")
    else:
        tmp = tempfile.mkdtemp(prefix="boundary-3-")
        try:
            work = os.path.join(tmp, "tasks")
            shutil.copytree(tasks_dir, work)
            removed = 0
            for path in list(task_files(work)):
                if victim in [e["slug"] for e in
                              edges_in(open(path, encoding="utf-8").read())]:
                    os.remove(path)
                    removed += 1
            p = run([sys.executable, os.path.join(SCRIPTS, "build-manifest.py"), work])
            if p.returncode != 0:
                failures.append(f"3: could not rebuild the manifest after removing {victim}")
            else:
                p = run([sys.executable, os.path.join(SCRIPTS, "check-coverage.py"),
                         prd_dir, work, "--json"])
                try:
                    out = json.loads(p.stdout)
                except ValueError:
                    out = {}
                got = sorted(f["slug"] for f in out.get("uncovered_features") or [])
                if got != expected_uncovered:
                    failures.append(
                        f"3: removed {removed} task(s) naming `{victim}` and the coverage report "
                        f"named {got or 'nothing'}, not {expected_uncovered}. A check that counts "
                        f"correctly and attributes wrongly passes any test that only counts")
                elif p.returncode != 1:
                    failures.append(f"3: a real shortfall exited {p.returncode}, not 1")
                else:
                    notes.append(f"3: removing `{victim}`'s {removed} task(s) was reported as "
                                 f"{expected_uncovered} and nothing else")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ---- 4. Both tiers reported. Not "a tier exists on the task" -- item 19 is about the
    #         OUTPUT, and <requirement-level> has no other reader at all.
    # Per EDGE since item 65: both tiers belong to the edge, because a task that is must-have
    # for one feature and could-have for another has two answers and the manifest takes the
    # strongest. A task whose second edge carries neither would report a tier it did not earn.
    missing_tier = sorted({f"{t['id']}/{e['slug']}" for t in attributed for e in t["edges"]
                           if not e["moscow"] or not e["level"]})
    if missing_tier:
        failures.append(f"4: {len(missing_tier)} attributed edge(s) carry no moscow or "
                        f"requirement-level: {', '.join(missing_tier[:5])}")
    if project:
        state_path = os.path.join(tasks_dir, "execute-state.json")
        if not os.path.isfile(state_path):
            p = run([sys.executable, os.path.join(EXEC_SCRIPTS, "write-state.py"),
                     tasks_dir, project, "probe"])
            if p.returncode != 0:
                failures.append(f"4: write-state.py failed: {p.stderr.strip()}")
        if os.path.isfile(state_path):
            state = json.load(open(state_path, encoding="utf-8"))
            by_tier = (state.get("tiers") or {}).get("by_tier") or {}
            if not by_tier:
                failures.append("4: execute-state.json reports no tiers, so the two-level "
                                "filter is invisible in the output")
            elif not any("/" in k for k in by_tier):
                failures.append(f"4: the tier report groups by one level, not two: {by_tier}")
            else:
                notes.append(f"4: reported as {by_tier}")
    else:
        notes.append("4: tier REPORT not checked -- pass --project to reach write-state.py")

    # ---- 5. A won't-have task is REFUSED at preflight, not merely absent.
    if project:
        tmp = tempfile.mkdtemp(prefix="boundary-5-")
        try:
            work = os.path.join(tmp, "tasks")
            shutil.copytree(tasks_dir, work)
            open(os.path.join(work, "layer_plan.json"), "w", encoding="utf-8",
                 newline="\n").write('{"layers": []}\n')
            run([sys.executable, os.path.join(SCRIPTS, "build-manifest.py"), work])
            flight = os.path.join(EXEC_SCRIPTS, "preflight.sh")
            clean = run(["sh", flight, work, project])
            if clean.returncode != 0:
                failures.append(f"5: preflight refused a clean tree, so its refusal below "
                                f"proves nothing: {clean.stderr.strip()}")
            else:
                layer = os.path.join(work, "1-foundation")
                os.makedirs(layer, exist_ok=True)
                with open(os.path.join(layer, "L1-999-wont.xml"), "w", encoding="utf-8",
                          newline="\n") as f:
                    # The per-edge shape item 65 writes. The element form is still refused
                    # -- preflight matches both -- but what /breakdown produces now is this, and
                    # a probe that only exercises the retired shape stops proving anything the
                    # day the last old task file is regenerated.
                    f.write("<task>\n  <meta>\n    <id>L1-999</id>\n    <name>W</name>\n"
                            "    <layer>1-foundation</layer>\n    <priority>1</priority>\n"
                            '    <source-feature slug="rejected" moscow="wont-have" '
                            'satisfies-criteria="1" requirement-level="P0"/>\n'
                            "  </meta>\n</task>\n")
                p = run(["sh", flight, work, project])
                if p.returncode == 0:
                    failures.append('5: a task carrying moscow="wont-have" passed preflight. '
                                    "Item 20 is defence in depth and it did not fire")
                elif "L1-999" not in p.stderr:
                    failures.append(f"5: preflight refused without naming the task:\n"
                                    f"{p.stderr}")
                else:
                    notes.append("5: preflight refused the won't-have task and named it")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        notes.append("5: preflight refusal not checked -- pass --project")

    if not quiet:
        for n in notes:
            print(f"  ok   {n}")
        for f in failures:
            print(f"  FAIL {f}", file=sys.stderr)
        print(f"\n{len(notes)} assertion group(s) held, {len(failures)} failure(s)")
    return 1 if failures else 0


# --------------------------------------------------------------------------------- live mode

def live(keep=False):
    """Run /breakdown over the current fixture, then grade what it produced.

    The version is read from SCHEMAS.json rather than named: nothing in this repository
    hardcodes a fixture schema version, and a runtime test pinned to `schema-2` would have been
    testing a corpus three migrations old.
    """
    reg = json.load(open(os.path.join(HERE, "fixture", "prd", "SCHEMAS.json"), encoding="utf-8"))
    prd = os.path.join(HERE, "fixture", "prd", reg["current"], "link-shelf")

    root = tempfile.mkdtemp(prefix="boundary-run-")
    project = os.path.join(root, "app")
    os.makedirs(project)
    for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"]):
        run(["git"] + args, cwd=project)
    # The PRD and the tasks live OUTSIDE the project, and that is not cosmetic: preflight.sh
    # refuses a target containing docs/prd/ (F15), so a workspace that nests them makes item
    # 20's refusal unprovable -- the first run with this layout reported "preflight refused a
    # clean tree, so its refusal below proves nothing", which is the grader catching the
    # HARNESS rather than the toolchain.
    workspace_prd = os.path.join(root, "docs", "prd", "link-shelf")
    shutil.copytree(prd, workspace_prd)
    tasks = os.path.join(root, "docs", "tasks", "link-shelf")

    prompt = (f"/breakdown {workspace_prd}/index.md "
              f"--project-path {project} --output-dir {tasks}")
    # bypassPermissions, not acceptEdits. The first live attempt used acceptEdits and the run
    # was refused at every gate: `/breakdown` is script-gated at Phases 1, 2, 2a and 5, and
    # acceptEdits permits file edits without permitting the interpreter to run a bundled script.
    #
    # The agent under test then did the RIGHT thing, which is the finding worth keeping: it
    # declined to hand-simulate the blocked validators, citing F15 and P16 -- "a run that fakes
    # them produces output nobody has actually checked". The skill's own argument for why guards
    # are programs reached the agent reading it. A run graded on simulated gates would have been
    # worse than no run.
    cmd = ["claude", "-p", prompt,
           "--plugin-dir", REPO, "--add-dir", REPO, "--add-dir", root,
           "--permission-mode", "bypassPermissions"]
    print(f"workspace: {root}")
    print("  " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=project, text=True)
    if p.returncode != 0:
        print(f"the /breakdown run exited {p.returncode}; nothing to grade", file=sys.stderr)
        return 2
    try:
        return grade(workspace_prd, tasks, project=project)
    finally:
        if not keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print(f"kept: {root}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--grade", nargs=2, metavar=("PRD-DIR", "TASKS-DIR"))
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--project")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.run:
        return live(keep=args.keep)
    if args.grade:
        return grade(args.grade[0], args.grade[1], project=args.project, quiet=args.quiet)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
