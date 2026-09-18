"""Mutants for the two dates a PRD declares: who writes them, when, and who reads them.

The ways back are the ways it got here. The producer stops firing, so the date freezes at birth --
that is the original defect, and it is mutant 1. Or the producer fires too often, which turns
`--check` into a write and makes the date record when the check last ran. Or the trigger drifts
back to the end of a session, which assumes a session is one sitting that ends the day it began.
Or idempotence goes, and `run it after every edit` stops being an instruction anybody follows. Or
one artefact grows the other's element name. Or the reader goes back to computing its own answer
from mtime, which is what left both elements unread while a column about their exact subject sat
two lines away. Or a second implementation of dating an artefact appears, which is how three
definitions of <criterion> came to disagree.
"""

DATE = "what-next.md's <last-updated> is written whenever the file is rewritten, and read"
OWNER = "one script dates every artefact that carries a date, and today's date is not a write"

BUILDER = "schema/scripts/build-what-next.py"
TOUCHER = "schema/scripts/touch-artefact.py"
CHECKER = "schema/scripts/check-artefacts.py"
LISTER = "skills/breakdown/scripts/list-prds.py"
FORMAT = "schema/prd-format.md"
COMMAND = "commands/prd.md"

MUTANTS = [
    # ---- what-next.md's date: the producer, the no-op, the reader, the shape ----------------
    ("the producer stops firing, so the date freezes at birth -- the original defect",
     BUILDER,
     "        f.write(touch(stamp(text)))",
     "        f.write(stamp(text))",
     DATE),

    ("the date is rewritten even when there is nothing to derive, so a no-op becomes a write",
     BUILDER,
     "    if existing and existing.group(0) == wanted and stamped == text:\n",
     "    if False:\n",
     DATE),

    ("the reader goes back to computing the age from mtime, and both dates are unread again",
     LISTER,
     '            "declared": max([d for d in (declared_date_of(what_next),\n',
     '            "declared": max([d for d in (None,\n',
     DATE),

    ("the reader stops reading index.md, so a PRD worked on there reads as untouched",
     LISTER,
     "                                         declared_date_of(index, INDEX_UPDATED)) if d],\n",
     "                                         None) if d],\n",
     DATE),

    ("what-next.md's date shape is unchecked, so one nothing can parse passes",
     CHECKER,
     '        problems.append(f"<last-updated> is {updated!r}, not YYYY-MM-DD. A date nothing '
     'can "',
     '        pass  # ("<last-updated> is not a date. A date nothing can "',
     DATE),

    ("a what-next.md carrying no date at all is accepted",
     CHECKER,
     '        if at_least(version, "schema-4"):\n            problems.append("<meta> has no '
     '<last-updated>;',
     '        if False:\n            problems.append("<meta> has no <last-updated>;',
     DATE),

    ("--touch stops dating a file whose block is already current",
     BUILDER,
     "        if args.touch:\n",
     "        if False:\n",
     DATE),

    ("--touch is accepted alongside --check, so a run that says write and do not write picks one",
     BUILDER,
     "    if args.touch and args.check:\n",
     "    if False:\n",
     DATE),

    ("the flag is renamed in the script while the command still writes --touch",
     BUILDER,
     '    ap.add_argument("--touch", action="store_true",\n',
     '    ap.add_argument("--date", action="store_true",\n',
     DATE),

    # The TABLE row, not the bash line below it. Deleting the bash line is not a way back: the
    # table still routes the trigger, so the instruction survives and the mutant was measuring
    # nothing. Two sites legitimately state this, so the catchable edit is to the routing.
    ("the table stops pairing a prose-only edit with --touch, so nothing dates that session",
     COMMAND,
     "| edited `<next-steps>`, `<risks>` or `<session-notes>` and derived nothing | "
     "`build-what-next.py {prd_dir} --touch` |",
     "| edited `<next-steps>`, `<risks>` or `<session-notes>` and derived nothing | nothing |",
     DATE),

    ("the table stops pairing an index-entry write with the script that dates index.md",
     COMMAND,
     "| wrote a feature spec, or changed an index entry — including its `priority` | "
     "`touch-artefact.py {prd_dir}/index.md` |",
     "| wrote a feature spec, or changed an index entry — including its `priority` | nothing |",
     # DATE, not OWNER: the whole trigger table is asserted in one place, and that place is the
     # check that owns the command's invocations. Declaring OWNER here reported MISSED against a
     # mutant the suite had in fact caught.
     DATE),

    ("prd-format.md drops the case --touch exists for",
     FORMAT,
     "**`--touch` is for\nthat case**",
     "The date is close enough either way",
     DATE),

    ("prd-format.md stops naming the producer, so the element goes back to having none",
     FORMAT,
     "**`<last-updated>` is written by `build-what-next.py`, every time it rewrites the file**",
     "**`<last-updated>` records when the PRD was last worked on**",
     DATE),

    ("prd-format.md drops the reason the declared date beats mtime",
     FORMAT,
     "which **does not survive a clone**",
     "which is usually close enough",
     DATE),

    # ---- the owning script: one implementation, idempotent, per-artefact element ------------
    # The one site. It had two -- an `already today` branch in touch() as well -- and the
    # substitution was byte-identical to the branch, so neither edit could change the outcome.
    ("today's date becomes a write, so running it after every edit means four identical diffs",
     TOUCHER,
     "        if updated == text:\n",
     "        if False:\n",
     OWNER),

    ("index.md is dated with what-next.md's element name, so one artefact declares two dates",
     TOUCHER,
     '    "prd": "updated",                 # index.md\n',
     '    "prd": "last-updated",            # index.md\n',
     OWNER),

    ("an artefact with no <meta> is reported as dated, having been left alone",
     TOUCHER,
     "    if not anchor:\n        return None\n",
     "    if not anchor:\n        return text\n",
     OWNER),

    ("a file that carries no date is dated anyway, inventing a producer nobody asked for",
     TOUCHER,
     "        if not element:\n",
     "        if False:\n",
     OWNER),

    ("--date takes anything, so the producer writes what the checker refuses",
     TOUCHER,
     "    if not ISO_DATE.match(today):\n",
     "    if False:\n",
     OWNER),

    ("build-what-next.py keeps its own copy of dating an artefact",
     BUILDER,
     '    return _touch.touch(text, "last-updated", today) or text\n',
     '    pat = re.compile(r"<last-updated>[^<]*</last-updated>")\n'
     '    return pat.sub(f"<last-updated>{today}</last-updated>", text)\n',
     OWNER),

    ("index.md's date shape is unchecked, so one nothing can parse passes",
     CHECKER,
     '        problems.append(f"<updated> is {updated!r}, not YYYY-MM-DD. A date nothing can '
     'parse is "',
     '        pass  # ("<updated> is not a date. A date nothing can parse is "',
     OWNER),

    ("an index.md carrying no date at all is accepted",
     CHECKER,
     '        problems.append("<meta> has no <updated>; `list-prds.py` reports when a PRD was '
     'last "',
     '        pass  # ("<meta> has no <updated>; `list-prds.py` reports when a PRD was last "',
     OWNER),

    ("commands/prd.md goes back to dating at the end of a session",
     COMMAND,
     "**Neither date is a session boundary.**",
     "**Date both files at the end of the session.**",
     OWNER),

    ("the gap-closure step stops rebuilding the block, so it is stale until some later phase",
     COMMAND,
     "**Then rebuild the derived block, here rather than at the end of the session:**",
     "The block is rebuilt in Phase 9.",
     OWNER),
]
