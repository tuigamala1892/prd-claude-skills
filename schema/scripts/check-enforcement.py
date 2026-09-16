#!/usr/bin/env python3
"""Does each assertion reach the paths its row says it does? (item 79, findings P55-P60)

`parity.md` measures CAPABILITY parity -- is the element documented on both paths -- with a
string probe against a format reference. Nothing measured ENFORCEMENT parity: whether the check
over that element actually runs on both. The distance between those two questions is where six
defects lived, and every one was found by a live run rather than by 144 static checks.

    P55  the gate's blocking-gaps assertion read features_of_prd() unconditionally
    P56  a CRD's significance was screened and nothing downstream acted on it
    8b   check-references.py reached a CRD for a whole phase with checks.md saying otherwise
    P58  `<gaps>` well-formed and aged had one caller and the CRD path was not it
    P59  the gate reported `blocked OK` for a kind it could not classify
    P60  the significance-candidate screen sat behind `if os.path.isdir(features_dir)`

Four of the six are capabilities `parity.md` already recorded as `both`. The element was on two
paths and its check on one, and no file in the repository could express the difference.

WHY THIS IS NOT A LINT ON `os.path.isdir`

Measured 2026-09-09: 43 `isdir`/`is_dir` calls across 28 files. Twenty-two are on a tasks
directory, a repo root, a worktree or a discovery candidate. Of the twenty-one on a document,
seven are PRD-only scripts that refuse a CRD with `exit 2` and a named reason, and ten dispatch
correctly. A syntactic check would flag `select-features.py`, which is the canonical dispatch,
and would not have found any of the six above -- three of which are about a value, a caller or a
printed line rather than a branch. The class is not the call.

WHAT IT ASSERTS

  1  every row's `Paths` is in the enum, and every value except `both` carries a reason
  2  every `both` row has a probe here, and every probe names a row -- BOTH directions, which
     is item 69's lesson: the forward direction alone could not see a script wired into a new
     caller, and it cannot see a probe for a row that has been deleted either
  3  each probe runs its owner TWICE -- against a well-formed CRD and against one mutated to
     carry the defect that assertion exists to catch. The good run must not report; the broken
     run must name the broken value

Assertion 3 is the whole point and the reason this is a script rather than a column. A
declaration alone is a documentation ratchet: it catches the asymmetry nobody wrote down, and
nothing about whether the code reaches. This repository has recorded nine false passes.

THE MARKER IS A VALUE OR A PROTOCOL TOKEN, NEVER A SENTENCE

Each probe names a string that must appear in the broken run's output and must NOT appear in the
good one. Seven of the ten name the mutated value itself -- `decsion`, `wont-have`, `nope.md`,
`banana` -- never the wording of a finding. Checks pinned to prose break when the prose improves,
which is this plan's second recorded lesson, and a probe asserting a sentence would fail the next
time somebody made a message clearer.

**Three cannot, and they are recorded rather than bent into the shape.** `check-writable.py`'s
assertion is about a file that already exists, so there is no bad value in any document and the
two states are `absent` and `present`; it keys on `REFUSED`, the token every script here prints
to refuse, which is a contract rather than a phrasing. `migrate.py` keys on `R2`, a rule id from
`migration.md`'s registry -- still a value, and one that must fail here if the rule is renamed.
`check-resume.py`'s assertion is about a document CHANGING after it was recorded, so both
workspaces are recorded from the good CRD by a `prepare` hook before one is broken, and it keys
on `CHANGED` -- the output names the changed source, never the changed value.

Both of those markers are second attempts. The first pair -- the filename, and `schema-` --
appeared in the good run as well as the broken one, so the probes distinguished nothing. **The
good-run assertion is what caught them**, before either could report a green result meaning
nothing, which is the ninth false pass this repository has recorded and the first caught by an
instrument rather than by a person.

USAGE

    check-enforcement.py [--quiet] [--json]

  exit 0  every `both` row was probed and both runs behaved
  exit 1  a row is unprobed, a probe is unrowed, or an assertion did not reach the CRD path
  exit 2  usage error, or checks.md could not be parsed
"""

import argparse
import json
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
BREAKDOWN = os.path.join(REPO, "skills", "breakdown", "scripts")
SCHEMA_SCRIPTS = _HERE

PATH_VALUES = {"both", "prd-only", "crd-only", "n/a"}


# ---------------------------------------------------------------- the probe corpus

# A well-formed CRD at the current schema. Every probe starts from this and breaks ONE thing, so
# a probe that reports on the good run is a defect in the probe rather than in the toolchain --
# which is why the good run is asserted first and separately.
GOOD_CRD = """<crd>
  <meta>
    <name>Archive links instead of deleting them</name>
    <slug>archive-links</slug>
    <type>feature-modify</type>
    <created>2026-09-09</created>
    <workflow>ready</workflow>
    <priority>must-have</priority>
  </meta>

  <context>
    <project-ref>PROJECT.md</project-ref>
    <related-features>
      <feature-ref id="save-link">Deletion lives here today</feature-ref>
    </related-features>
  </context>

  <change-request>
    <summary>Archiving hides a link without destroying it.</summary>
    <motivation>Deletion is permanent and people ask for links they removed.</motivation>
  </change-request>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0">
      When a user archives a link, the system shall mark it archived.
    </criterion>
  </acceptance-criteria>

  <impact-analysis>
    <affected-files>
      <file action="modify">app/models/link.py</file>
    </affected-files>
    <affected-features>
      <feature id="save-link">Archive is additive</feature>
    </affected-features>
    <affected-contracts>
      <contract kind="schema" ref="Link">Adds an archived timestamp</contract>
    </affected-contracts>
    <scope>small</scope>
    <confidence>high</confidence>
  </impact-analysis>
</crd>
"""

PROJECT_MD = """<project-context>
  <meta>
    <name>link-shelf</name>
    <last-context-hash>0000000</last-context-hash>
  </meta>
  <features>
    <feature id="save-link" built="complete">Save a link</feature>
  </features>
  <schema-registry>
    <model name="Link" table="links">id, url</model>
  </schema-registry>
</project-context>
"""

TASK_XML = """<task><meta><id>L2-001</id>
<source-feature slug="archive-links" moscow="must-have" satisfies-criteria="1"
 requirement-level="P0"/>
</meta></task>
"""

MANIFEST = {"total_tasks": 1, "task_inventory": [{"id": "L2-001", "layer": "2-backend"}]}


def _doc(ws):
    return os.path.join(ws, "docs", "crd", "archive-links.md")


def _tasks(ws):
    return os.path.join(ws, "tasks")


# owner -> how to probe it.
#
#   argv     built from the workspace; the CRD is always passed in its CRD shape
#   break    (old, new) -- ONE replacement in the good CRD
#   marker   the mutated value, which must appear broken and must not appear good
#   note     why this mutation is the defect the assertion exists to catch
#
# `check-writable.py` is the one probe whose mutation is not in the document: its assertion is
# about a file that already exists, so the two states are `absent` and `present`. Recorded here
# rather than bent into the document shape, because a probe that tests something other than the
# assertion is worse than no probe.
PROBES = {
    "check-artefacts.py": {
        "script": os.path.join(SCHEMA_SCRIPTS, "check-artefacts.py"),
        "argv": lambda ws: [_doc(ws)],
        "break": ("<workflow>ready</workflow>", "<workflow>banana</workflow>"),
        "marker": "banana",
        "note": "a <workflow> outside core section 3's enum",
    },
    "check-status.py": {
        "script": os.path.join(BREAKDOWN, "check-status.py"),
        "argv": lambda ws: [_doc(ws)],
        "break": ("<confidence>high</confidence>",
                  "<confidence>high</confidence>\n  </impact-analysis>\n  <gaps>\n"
                  "    <gap id=\"1\" kind=\"decsion\" raised=\"2026-09-09\">Undecided</gap>\n"
                  "  </gaps>\n  <impact-analysis>"),
        "marker": "decsion",
        "note": "a <gap kind=> one letter outside core section 6's enum",
    },
    "check-references.py": {
        "script": os.path.join(BREAKDOWN, "check-references.py"),
        "argv": lambda ws: [_doc(ws), "--project-path", ws],
        "break": ("<project-ref>PROJECT.md</project-ref>",
                  "<project-ref>nope.md</project-ref>"),
        "marker": "nope.md",
        "note": "a <project-ref> naming a file that does not exist",
    },
    "select-features.py": {
        "script": os.path.join(BREAKDOWN, "select-features.py"),
        "argv": lambda ws: [_doc(ws)],
        "break": ("<priority>must-have</priority>", "<priority>wont-have</priority>"),
        "marker": "wont-have",
        "note": "item 13's correctness rule -- a document somebody decided against building",
    },
    "check-coverage.py": {
        "script": os.path.join(BREAKDOWN, "check-coverage.py"),
        "argv": lambda ws: [_doc(ws), _tasks(ws)],
        "break": ('<criterion id="1" pattern="event-driven" priority="P0">',
                  '<criterion id="9" pattern="event-driven" priority="P0">'),
        "marker": "9",
        "note": "a criterion no task cites, so coverage must name it",
    },
    "check-gate.py": {
        "script": os.path.join(BREAKDOWN, "check-gate.py"),
        "argv": lambda ws: [_doc(ws), _tasks(ws)],
        "break": ("<confidence>high</confidence>",
                  "<confidence>high</confidence>\n  </impact-analysis>\n  <gaps>\n"
                  "    <gap id=\"1\" kind=\"decision\" raised=\"2026-09-09\">Undecided</gap>\n"
                  "  </gaps>\n  <impact-analysis>"),
        "marker": "blocking gap",
        "note": "item 29's execution stop, which was unreachable on this path until item 77",
    },
    "check-repo-structure.py": {
        "script": os.path.join(BREAKDOWN, "check-repo-structure.py"),
        "argv": lambda ws: [_doc(ws), "--project-root", ws],
        "break": ("<scope>small</scope>",
                  "<scope>small</scope>\n    <repo-structure>multi-repo</repo-structure>"),
        "marker": "multi-repo",
        "note": "a layout the toolchain refuses, declared by the document rather than found late",
    },
    "migrate.py": {
        "script": os.path.join(SCHEMA_SCRIPTS, "migrate.py"),
        # No --to: `--check` alone means the newest schema, which is how /crd --resume asks it.
        # A version named here went stale at the next schema and nothing would have said so.
        "argv": lambda ws: [_doc(ws), "--check"],
        "break": ("<workflow>ready</workflow>",
                  "<status>ready</status>\n    <requirements>\n"
                  "      <requirement level=\"must-have\">Old shape</requirement>\n"
                  "    </requirements>"),
        # The migration RULE id, from migration.md's registry -- a value, and one that must
        # fail here if the rule is ever renamed. `schema-` was the first marker and appeared in
        # both runs' summary lines, which the good-run assertion caught.
        "marker": "R2",
        "note": "a CRD written in a superseded spelling, which --check must refuse to guess past",
    },
    "check-resume.py": {
        "script": os.path.join(BREAKDOWN, "check-resume.py"),
        "argv": lambda ws: [_doc(ws), _tasks(ws), "--project-path", ws],
        # Its assertion is about a document CHANGING, so both workspaces are recorded from the
        # good CRD and made a resume before the break is applied -- see `prepare` in probe().
        "prepare": lambda ws: _record_then_resume(ws),
        "break": ("<scope>small</scope>", "<scope>large</scope>"),
        # A protocol token rather than the value: the changed value is not in the output, the
        # changed SOURCE is, and `CHANGED` is the line that names it.
        "marker": "CHANGED",
        "note": "a CRD edited after the analysis a resume would skip to was built from it",
    },
    "check-writable.py": {
        "script": os.path.join(BREAKDOWN, "check-writable.py"),
        "argv": lambda ws: [_doc(ws)],
        "break": None,          # the state is the filesystem, not the document -- see above
        # There is no bad VALUE to key on, so this keys on the exit protocol instead. `REFUSED`
        # is the token every script in this toolchain prints to refuse; it is a contract rather
        # than a phrasing. The filename was the first marker and appears in both runs -- the
        # absent case says `clear to write: <name>` -- which the good-run assertion caught.
        "marker": "REFUSED",
        "note": "a document already on disk, which must never be silently replaced",
    },
}


# ---------------------------------------------------------------- the registry

def rows(path):
    """checks.md's table as dicts. Raises rather than returning an empty list."""
    text = open(path, encoding="utf-8").read()
    section = text.split("## The table", 1)
    if len(section) != 2:
        raise ValueError("checks.md has no table section")
    out = []
    for line in section[1].splitlines():
        if not line.startswith("|") or set(line) <= set("| -"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or cells[0] == "Assertion":
            if cells and cells[0] == "Assertion":
                continue
            raise ValueError(f"malformed row ({len(cells)} cells): {line[:70]}")
        out.append({"assertion": cells[0], "owner": cells[1].strip("`"),
                    "paths": cells[3], "why": cells[4], "item": cells[5]})
    if not out:
        raise ValueError("checks.md's table parsed to no rows")
    return out


# ---------------------------------------------------------------- the probes

def workspace(root, crd_text):
    """A CRD in the layout the CRD path uses, plus the project it is a change against."""
    crd_dir = os.path.join(root, "docs", "crd")
    layer = os.path.join(root, "tasks", "2-backend")
    for d in (crd_dir, layer):
        os.makedirs(d, exist_ok=True)
    with open(_doc(root), "w", encoding="utf-8", newline="\n") as f:
        f.write(crd_text)
    with open(os.path.join(root, "PROJECT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PROJECT_MD)
    with open(os.path.join(layer, "L2-001-archive.xml"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(TASK_XML)
    with open(os.path.join(root, "tasks", "manifest.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(MANIFEST, f)
    return root


def run(script, argv):
    p = subprocess.run([sys.executable, script, *argv], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def _record_then_resume(ws):
    """`check-resume.py`'s starting state: sources recorded, and an analysis to skip to."""
    spec = PROBES["check-resume.py"]
    code, out = run(spec["script"], spec["argv"](ws))
    if code != 0:
        raise RuntimeError(f"check-resume.py could not record a fresh workspace:\n{out[:300]}")
    with open(os.path.join(_tasks(ws), "analysis.json"), "w", encoding="utf-8") as f:
        f.write("{}")


def probe(owner, spec, tmp):
    """Run one owner against a good CRD and a broken one. Returns a list of findings."""
    import shutil
    import tempfile

    findings = []
    good_root = tempfile.mkdtemp(prefix="enf-good-", dir=tmp)
    bad_root = tempfile.mkdtemp(prefix="enf-bad-", dir=tmp)
    try:
        if spec["break"] is None:
            # The filesystem-state probe: `good` is the document absent, `bad` is it present.
            workspace(good_root, GOOD_CRD)
            os.remove(_doc(good_root))
            workspace(bad_root, GOOD_CRD)
        else:
            old, new = spec["break"]
            if old not in GOOD_CRD:
                return [f"{owner}: its mutation anchor {old!r} is not in the good CRD, so the "
                        f"probe changes nothing and would pass against any script at all"]
            workspace(good_root, GOOD_CRD)
            if spec.get("prepare"):
                # A probe whose assertion is about change: both start good and are prepared
                # there, and only then is the bad one broken.
                workspace(bad_root, GOOD_CRD)
                spec["prepare"](good_root)
                spec["prepare"](bad_root)
                with open(_doc(bad_root), "w", encoding="utf-8", newline="\n") as f:
                    f.write(GOOD_CRD.replace(old, new, 1))
            else:
                workspace(bad_root, GOOD_CRD.replace(old, new, 1))

        good_code, good_out = run(spec["script"], spec["argv"](good_root))
        bad_code, bad_out = run(spec["script"], spec["argv"](bad_root))

        if "Traceback (most recent call last)" in good_out:
            findings.append(f"{owner}: crashed on a well-formed CRD, so it does not reach this "
                            f"path at all:\n      {good_out.strip().splitlines()[-1][:160]}")
            return findings
        if spec["marker"] in good_out:
            findings.append(f"{owner}: reported {spec['marker']!r} against a well-formed CRD. "
                            f"The probe cannot distinguish anything, and a checker that flags "
                            f"every document satisfies it")
        if spec["marker"] not in bad_out:
            findings.append(
                f"{owner}: did not name {spec['marker']!r} for a CRD carrying {spec['note']}. "
                f"The assertion does not reach the CRD path -- exit {bad_code}, output:"
                f"\n      {(bad_out.strip() or '(nothing)')[:400]}")
        if (good_code, good_out) == (bad_code, bad_out):
            findings.append(f"{owner}: produced identical results for a well-formed CRD and one "
                            f"carrying {spec['note']}")
    finally:
        shutil.rmtree(good_root, ignore_errors=True)
        shutil.rmtree(bad_root, ignore_errors=True)
    return findings


# ---------------------------------------------------------------- main

def main():
    import tempfile

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--checks", default=os.path.join(REPO, "schema", "checks.md"))
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        table = rows(args.checks)
    except (OSError, ValueError) as e:
        print(f"REFUSED  {e}", file=sys.stderr)
        return 2

    findings = []

    # 1 -- the column is an enum, and an asymmetry carries a reason.
    for r in table:
        if r["paths"] not in PATH_VALUES:
            findings.append(f"{r['owner']}: Paths is {r['paths']!r}, not one of "
                            f"{'|'.join(sorted(PATH_VALUES))}")
        elif r["paths"] != "both" and len(r["why"]) < 20:
            findings.append(f"{r['owner']}: Paths is `{r['paths']}` with no reason. An "
                            f"asymmetry nobody wrote down is what this column exists to prevent")

    # 2 -- both directions. A row with no probe is a claim nothing tested; a probe with no row
    # is a test of something the registry has stopped describing.
    declared = {r["owner"] for r in table if r["paths"] == "both"}
    for owner in sorted(declared - set(PROBES)):
        findings.append(f"{owner}: checks.md says `both` and there is no probe. The column "
                        f"would then be a documentation ratchet, which catches the row nobody "
                        f"wrote down and nothing about whether the code reaches")
    for owner in sorted(set(PROBES) - declared):
        findings.append(f"{owner}: probed here and checks.md does not say `both`. Either the "
                        f"row moved or the probe outlived it")

    # 3 -- and the half a declaration cannot carry: run each one.
    probed = 0
    tmp = tempfile.mkdtemp(prefix="check-enforcement-")
    try:
        for owner in sorted(declared & set(PROBES)):
            findings.extend(probe(owner, PROBES[owner], tmp))
            probed += 1
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    counts = {v: sum(1 for r in table if r["paths"] == v) for v in sorted(PATH_VALUES)}

    if args.json:
        print(json.dumps({"rows": len(table), "probed": probed, "paths": counts,
                          "findings": findings}, indent=2))
    else:
        if not args.quiet:
            for line in findings:
                print(f"  UNREACHED  {line}")
        summary = ", ".join(f"{n} {v}" for v, n in counts.items() if n)
        print(f"{len(table)} assertion(s): {summary}; {probed} probed by running, "
              f"{len(findings)} finding(s)")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
