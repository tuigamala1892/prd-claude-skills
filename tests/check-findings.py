#!/usr/bin/env python3
"""Does every finding the plan names have a status? (item 85, finding P68)

`readers.md` distinguishes an element with no reader from one with a recorded reason it has none.
`checks.md` distinguishes an assertion with an owner from an ownerless row kept deliberately.
`parity.md` distinguishes a settled asymmetry from an `open` one. **Findings had no such file**,
and they are the thing the whole plan is organised around.

Measured before this existed: P9 was explicitly RETRACTED, P13 was measured and CLOSED -- and both
were simply absent from every index, so nothing could tell a decision from an omission. Worse,
**P58-P68 had no definition anywhere**: eleven findings that existed only as `finding=` tags in
the regression suite and words in commit messages.

WHY THIS LIVES IN tests/ AND HAS NO checks.md ROW

`checks.md` is *"every assertion the toolchain makes about an artefact"*. This asserts nothing
about a PRD, a CRD or a task -- it audits the project's own record-keeping. Putting it in that
table would widen the table's meaning to cover project documentation, which is how a registry
stops being about one thing. `mutate.py` and `probe-p1.py` live here on the same basis.

WHAT IT ASSERTS

  1  every id CITED as a finding across the plan, the ledger and the suite has a row -- so a
     finding named in a commit message and nowhere else fails here
  2  every row's `Status` is in the enum, and every row names something under `Settled by`
  3  a row naming a regression check names one that EXISTS in tests/test_toolchain.py
  4  a row naming an item names one the plan defines
  5  `P0` is not a finding, and is not mistaken for one -- it is a criterion priority level

Assertion 3 is the one that decays without help: a check renamed in the suite leaves a row here
pointing at nothing, and the row still reads as settled.

USAGE

    check-findings.py [--quiet] [--json]

EXIT CODES

  0  every cited finding has a row, and every row resolves
  1  at least one does not
  2  usage error, or a file could not be read
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

PLAN = os.path.join(REPO, "docs", "skills", "plugin-2.0-plan.md")
LEDGER = os.path.join(REPO, "docs", "skills", "plugin-2.0-progress.md")
SUITE = os.path.join(REPO, "tests", "test_toolchain.py")
REGISTRY = os.path.join(REPO, "docs", "skills", "plugin-2.0-findings.md")

STATUSES = {"closed", "retracted", "open", "superseded"}

# `P0|P1|P2` is core section 4's criterion priority vocabulary and collides with the finding id
# space. A bare `\bP2\b` finds both, so the levels are excluded by the shapes they appear in
# rather than by hoping they do not occur.
LEVEL_CONTEXT = re.compile(r"P0\|P1\|P2|priority=\"P[012]\"|`P[012]`")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def rows(text):
    """The registry's table, as dicts. Raises rather than returning an empty list."""
    section = text.split("## The table", 1)
    if len(section) != 2:
        raise ValueError("plugin-2.0-findings.md has no table section")
    out = []
    for line in section[1].splitlines():
        if not line.startswith("|") or set(line) <= set("| -"):
            continue
        # Split on UNESCAPED pipes. `P0\|P1\|P2` is a legitimate cell value here, and splitting
        # on every pipe turns a four-column row into six and reads as a malformed table.
        cells = [c.strip().replace("\\|", "|")
                 for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) != 4 or cells[0] == "Finding":
            if cells and cells[0] == "Finding":
                continue
            raise ValueError(f"malformed row ({len(cells)} cells): {line[:70]}")
        out.append({"id": cells[0].strip("*"), "claim": cells[1],
                    "status": cells[2], "settled": cells[3]})
    if not out:
        raise ValueError("the findings table parsed to no rows")
    return out


def cited_ids(plan, ledger, suite):
    """Every id used AS A FINDING, with the priority levels screened out."""
    found = set()
    for text in (plan, ledger):
        for line in text.splitlines():
            stripped = LEVEL_CONTEXT.sub("", line)
            found.update(re.findall(r"\bP(\d{1,2})\b", stripped))
    found.update(re.findall(r'finding="P(\d{1,2})"', suite))
    # P0 is a priority level and never a finding. Screened by name because a line can mention it
    # outside the shapes above -- and being wrong about this inflates the population silently.
    return {f"P{n}" for n in found if n != "0"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        plan, ledger, suite = read(PLAN), read(LEDGER), read(SUITE)
        table = rows(read(REGISTRY))
    except (OSError, ValueError) as e:
        print(f"REFUSED  {e}", file=sys.stderr)
        return 2

    check_names = set(re.findall(r'@check\(\s*"([^"]+)"', suite))
    item_numbers = set(re.findall(r"^\*\*(\d{1,2})[a-z]?\.", plan, re.M))

    problems = []
    have = {r["id"] for r in table}

    for pid in sorted(cited_ids(plan, ledger, suite) - have, key=lambda x: int(x[1:])):
        problems.append(f"{pid} is cited as a finding and has no row. A finding whose claim "
                        f"lives only in a commit message is one nobody can look up")

    for r in table:
        where = r["id"]
        if r["status"] not in STATUSES:
            problems.append(f"{where}: status is {r['status']!r}, not one of "
                            f"{'|'.join(sorted(STATUSES))}")
        if len(r["settled"]) < 10:
            problems.append(f"{where}: `Settled by` is empty. Every status needs one, including "
                            f"`open` -- an open row with no reason is the thing this file "
                            f"exists to prevent")
        if not r["claim"]:
            problems.append(f"{where}: no claim. The row says what became of a finding without "
                            f"saying what the finding was")

        # A row pointing at a check that no longer exists still reads as settled.
        for quoted in re.findall(r"``\s*(.+?)\s*``|`([^`]+)`", r["settled"]):
            name = (quoted[0] or quoted[1]).strip()
            if name in check_names or "." in name or "/" in name or " " not in name:
                continue
            if name not in check_names:
                problems.append(f"{where}: names a regression check that does not exist -- "
                                f"{name!r}. Renamed in the suite, and the row still reads as "
                                f"guarded")

        for item in re.findall(r"\bitems? (\d{1,2})\b", r["settled"]):
            if item not in item_numbers:
                problems.append(f"{where}: settled by item {item}, which the plan does not "
                                f"define")

    counts = {s: sum(1 for r in table if r["status"] == s) for s in sorted(STATUSES)}

    if args.json:
        print(json.dumps({"rows": len(table), "cited": len(cited_ids(plan, ledger, suite)),
                          "by_status": {k: v for k, v in counts.items() if v},
                          "findings": problems}, indent=2))
    else:
        if not args.quiet:
            for line in problems:
                print(f"  UNRECORDED  {line}")
        summary = ", ".join(f"{n} {s}" for s, n in counts.items() if n)
        print(f"{len(table)} finding(s) recorded: {summary}; {len(problems)} problem(s)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
