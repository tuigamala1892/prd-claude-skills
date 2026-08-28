#!/usr/bin/env python3
"""Does every element the schema defines have somebody who reads it? (plan item 23)

**This is the check that would have caught this plan's own nine.** An audit of the plan against
this rule on 2026-08-25 found nine failures, two of them contradictions between items rather than
omissions -- in a document whose closing argument is that every producer needs a reader. That is
the strongest available evidence that the rule needs a script rather than a principle.

WHY A TEST SUITE COULD NOT ALREADY SEE THIS

P2 and P4 were both invisible to a suite that reads the files, because **the failure is an absent
consumer rather than a wrong string.** `<acceptance-criteria>` was well-formed XML throughout and
had no reader for the whole life of the toolchain; `<notes>` had none anywhere. Nothing about
either document was malformed. A check that a producer has a reader is the general form of this
whole plan.

THE READER IS MEASURED, NOT DECLARED

The obvious design is a registry: one row per element naming its reader. It would be 128 rows,
hand-maintained, and wrong within a month -- and a declared reader is a claim, which is the thing
this script exists to stop. So the reader is **found by looking**, in two tiers:

  script       a .py or .sh names the element     -- it is consumed by a program
  instruction  a skill, command or agent names it -- it is consumed by a model reading that file

Both are real consumption; this repository's own audit used the second. What is NOT a reader is
the schema document that DEFINES the element -- otherwise every element reads itself and the
check is a function that returns True.

WHAT IS DECLARED IS THE EXCEPTION

An element with no reader must appear in [`readers.md`](../readers.md) with a verdict and a
reason. Three verdicts:

  unread by design       prose a human reads; structure would be cost with no consumer
  externally maintained  produced and consumed outside the toolchain (the open-questions register)
  open                   a producer with no consumer, and nobody has decided what to do

**`open` is a legitimate verdict and is not a failure**, the same way `parity.md`'s is. An
element nobody has examined is a fact about this project; the defect this file exists to prevent
is one nobody has *written down*. The suite lists the open rows rather than refusing them.

THE REVERSE DIRECTION IS A REPORT, AND THE REASON IS MEASURED

The plan asks for the same test in reverse: every element a component *reads* must have a named
producer. Run naively that is 32 candidates of which 29 are false: `<prd-dir>`, `<tasks-path>`,
`<project-path>` and their kin are **usage-string placeholders**, and an element name and a CLI
placeholder are the same token. They are filtered by asking whether the same file declares an
argument of that name -- which removes the noise and leaves a report rather than a refusal,
because a filter tuned against one corpus is not a rule.

USAGE

    check-readers.py [--repo DIR] [--strict] [--quiet] [--json]

  --strict   exit non-zero on the open rows too

EXIT CODES

  0  every defined element has a reader or a declared exception
  1  an element has neither, or `readers.md` names an element the schema does not define
  2  usage error
"""

import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))

# The documents that DEFINE elements. They are excluded from the reader search by construction:
# a definition is not a consumption, and counting it as one makes every element self-satisfying.
SCHEMA_DOCS = [
    "schema/core.md",
    "schema/prd-format.md",
    "schema/decision-record.md",
    "skills/crd/references/crd-format.md",
    "skills/crd/references/project-format.md",
    "skills/breakdown/references/architecture-format.md",
    "skills/breakdown/references/task-format-spec.md",
]

READERS_DOC = "schema/readers.md"
VERDICTS = {"unread by design", "externally maintained", "open"}

TEMPLATE = re.compile(r"```(?:xml|markdown)\n(.*?)```", re.S)
ELEMENT = re.compile(r"<([a-z][a-z0-9-]*)[\s>/]")
# argparse names, however they are spelled: a positional, a flag, or a metavar. A tag that is
# also an argument of the same script is an argument, not an element.
ARG_NAME = re.compile(r'(?:add_argument\(\s*["\']-{0,2}|metavar=["\'])([a-z][a-z0-9_-]*)')


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def defined_elements(repo):
    """element -> the schema documents that define it, from their template blocks."""
    out = {}
    for rel in SCHEMA_DOCS:
        path = os.path.join(repo, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            continue
        for block in TEMPLATE.findall(read(path)):
            for tag in ELEMENT.findall(block):
                out.setdefault(tag, set()).add(rel)
    return out


def candidate_readers(repo):
    """(scripts, instructions) -- every file that could consume an element, schema docs aside."""
    scripts, instructions = [], []
    for dirpath, dirnames, names in os.walk(repo):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
        for n in sorted(names):
            rel = os.path.relpath(os.path.join(dirpath, n), repo).replace(os.sep, "/")
            if rel in SCHEMA_DOCS or rel == READERS_DOC:
                continue
            # The plan and the ledger discuss every element by name; counting them would make
            # "somebody wrote about it" indistinguishable from "somebody reads it". The suite is
            # excluded for the same reason -- a test naming an element is not a consumer of it.
            if rel.startswith("docs/") or rel.startswith("tests/"):
                continue
            if n.endswith((".py", ".sh")):
                scripts.append(rel)
            elif n.endswith(".md") and rel.split("/")[0] in (
                    "skills", "commands", "agents", "schema"):
                instructions.append(rel)
    return scripts, instructions


def reader_index(repo, files):
    return {rel: read(os.path.join(repo, rel.replace("/", os.sep))) for rel in files}


def names_it(text, tag):
    """Whether this file names the element AS an element rather than in passing.

    `<tag`, `</tag>` or the bare name in backticks or quotes. A word in a sentence is not
    enough: `status` and `context` are ordinary English, and matching them as prose would give
    every element in the schema a reader by accident.
    """
    return re.search(r"<%s[\s>/]|</%s>|[`\"']<?%s>?[`\"']" % ((re.escape(tag),) * 3),
                     text) is not None


def body_of(text):
    """A script with its leading usage block removed.

    The reverse direction reads element names out of code, and a usage string is exactly where
    they are NOT elements: `check-coverage.py <prd-dir> <tasks-dir>` names two arguments in the
    same notation an artefact uses for two elements. Dropping the module docstring and the
    leading comment block removes most of the candidates measured on this corpus, which is the
    difference between a report and a noise generator.
    """
    return re.sub(r'\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'', "", text, flags=re.S)


def parse_readers_doc(repo):
    """element -> (verdict, why) from readers.md's table, or None when the file is missing."""
    path = os.path.join(repo, READERS_DOC.replace("/", os.sep))
    if not os.path.isfile(path):
        return None
    rows = {}
    section = read(path).split("## The exceptions", 1)
    if len(section) != 2:
        return rows
    for line in section[1].split("\n---\n", 1)[0].splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in ("element", ""):
            continue
        # Emphasis is formatting, not content: a verdict written `**open**` to make it visible
        # in the table is the same verdict. A check that reads markdown literally is a check
        # that breaks when somebody bolds a cell.
        verdict = re.sub(r"[*`_]", "", cells[1]).strip().lower()
        rows[re.sub(r"[*`_]", "", cells[0]).strip("<>/ ")] = (verdict, cells[2])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    defined = defined_elements(repo)
    if not defined:
        print(f"REFUSED  no schema templates found under {repo}", file=sys.stderr)
        return 2

    declared = parse_readers_doc(repo)
    if declared is None:
        print(f"REFUSED  {READERS_DOC} does not exist. Every element with no reader has to be "
              f"declared somewhere, and the declaration is what stops `nobody reads this` being "
              f"discovered one artefact at a time", file=sys.stderr)
        return 2

    scripts, instructions = candidate_readers(repo)
    stext, itext = reader_index(repo, scripts), reader_index(repo, instructions)

    unread, by_script, by_instruction = [], {}, {}
    for tag in sorted(defined):
        s = [f for f in scripts if names_it(stext[f], tag)]
        i = [f for f in instructions if names_it(itext[f], tag)]
        if s:
            by_script[tag] = s
        elif i:
            by_instruction[tag] = i
        else:
            unread.append(tag)

    problems, opens, notes = [], [], []
    for tag in unread:
        row = declared.get(tag)
        if row is None:
            problems.append(f"<{tag}> is defined in {', '.join(sorted(defined[tag]))} and "
                            f"NOTHING reads it. Give it a reader, or record it in "
                            f"{READERS_DOC} with a verdict and a reason")
            continue
        verdict, why = row
        if verdict not in VERDICTS:
            problems.append(f"<{tag}>: verdict {verdict!r} is not one of "
                            f"{' | '.join(sorted(VERDICTS))}")
        elif verdict == "open":
            opens.append(f"<{tag}>: {why}")

    for tag in sorted(declared):
        if tag not in defined:
            problems.append(f"{READERS_DOC} declares <{tag}>, which no schema document defines. "
                            f"An exception list that outlives its elements is a list nobody "
                            f"has read")
        elif tag not in unread:
            notes.append(f"<{tag}> is declared an exception and something names it "
                         f"({(by_script.get(tag) or by_instruction.get(tag))[0]}). Naming an "
                         f"element to VALIDATE it is not reading its content, so this is "
                         f"reported rather than refused")

    # ---- the reverse direction, as a report. See the docstring for why it is not binding.
    orphan_reads = {}
    # Python only. A shell script parses no XML -- every `<x>` in one is a usage placeholder or
    # a redirect, so including them measures the notation rather than the reading.
    for rel in [f for f in scripts if f.endswith(".py")]:
        text = body_of(stext[rel])
        args_declared = set(ARG_NAME.findall(stext[rel]))
        for tag in set(ELEMENT.findall(text)):
            # No element in this schema is two characters. `<br>` and a loop variable in a
            # comment are not producers with no consumer.
            if len(tag) < 3 or tag in defined or tag.replace("-", "_") in args_declared:
                continue
            orphan_reads.setdefault(tag, []).append(rel)

    if args.json:
        print(json.dumps({"defined": len(defined), "by_script": len(by_script),
                          "by_instruction": len(by_instruction), "unread": unread,
                          "problems": problems, "open": opens, "notes": notes,
                          "orphan_reads": orphan_reads}, indent=2))
    elif not args.quiet:
        for line in problems:
            print(f"  NO READER  {line}")
        for line in opens:
            print(f"  OPEN       {line}")
        for line in notes:
            print(f"  NOTE       {line}")
        for tag, files in sorted(orphan_reads.items()):
            print(f"  READ-ONLY  <{tag}> is read by {', '.join(files)} and no schema document "
                  f"defines it")

    print(f"{len(defined)} elements defined: {len(by_script)} read by a script, "
          f"{len(by_instruction)} by an instruction, {len(unread)} unread "
          f"({len(opens)} open), {len(problems)} undeclared")

    if problems:
        return 1
    return 1 if (args.strict and opens) else 0


if __name__ == "__main__":
    sys.exit(main())
