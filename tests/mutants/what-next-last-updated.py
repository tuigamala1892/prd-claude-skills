"""Mutants for what-next.md's `<last-updated>` having a producer, a reader and a shape.

The ways back are the ways it got here. The producer stops firing, so the date freezes at birth
again -- that is the original defect, and it is mutant 1. Or the producer fires too often, which
turns `--check` into a write and makes the date record when the check last ran. Or the reader goes
back to computing its own answer from mtime, which is what left the element unread while a column
about its exact subject sat two lines away. Or the shape check stops refusing a date nothing can
parse, which is the same as having no date. Or prd-format.md stops naming the producer, and the
next person to read the file finds an element nobody owns.
"""

CHECK = "what-next.md's <last-updated> is written whenever the file is rewritten, and read"
BUILDER = "schema/scripts/build-what-next.py"
CHECKER = "schema/scripts/check-artefacts.py"
LISTER = "skills/breakdown/scripts/list-prds.py"
FORMAT = "schema/prd-format.md"

MUTANTS = [
    ("the producer stops firing, so the date freezes at birth -- the original defect",
     BUILDER,
     "        f.write(touch(stamp(text)))",
     "        f.write(stamp(text))",
     CHECK),

    ("the date is rewritten even when there is nothing to derive, so a no-op becomes a write",
     BUILDER,
     "    if existing and existing.group(0) == wanted and stamped == text:\n",
     "    if False:\n",
     CHECK),

    ("touch() cannot find the element and appends a second one instead of updating it",
     BUILDER,
     "    if UPDATED.search(text):\n",
     "    if False:\n",
     CHECK),

    ("the reader goes back to computing the age from mtime, and the element is unread again",
     LISTER,
     '    declared = prd["declared"]\n',
     "    declared = None\n",
     CHECK),

    ("the shape check accepts anything, so a date nothing can parse passes",
     CHECKER,
     "    elif not ISO_DATE.match(updated):\n",
     "    elif False:\n",
     CHECK),

    ("a file carrying no date at all is accepted",
     CHECKER,
     '        if at_least(version, "schema-4"):\n            problems.append("<meta> has no '
     '<last-updated>;',
     '        if False:\n            problems.append("<meta> has no <last-updated>;',
     CHECK),

    ("--touch stops dating a file whose block is already current",
     BUILDER,
     "        if args.touch:\n",
     "        if False:\n",
     CHECK),

    ("--touch is accepted alongside --check, so a run that says write and do not write picks one",
     BUILDER,
     "    if args.touch and args.check:\n",
     "    if False:\n",
     CHECK),

    ("the flag is renamed in the script while the command still writes --touch",
     BUILDER,
     '    ap.add_argument("--touch", action="store_true",\n',
     '    ap.add_argument("--date", action="store_true",\n',
     CHECK),

    ("commands/prd.md stops running the builder for the session that derived nothing",
     "commands/prd.md",
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/build-what-next.py {prd_dir} --touch",
     "# the date is maintained by hand",
     CHECK),

    ("prd-format.md drops the case --touch exists for",
     FORMAT,
     "**`--touch` is for\nthat case**",
     "The date is close enough either way",
     CHECK),

    ("prd-format.md stops naming the producer, so the element goes back to having none",
     FORMAT,
     "**`<last-updated>` is written by `build-what-next.py`, every time it rewrites the file**",
     "**`<last-updated>` records when the PRD was last worked on**",
     CHECK),

    ("prd-format.md drops the reason the declared date beats mtime",
     FORMAT,
     "which **does not survive a clone**",
     "which is usually close enough",
     CHECK),
]
