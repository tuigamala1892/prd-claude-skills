"""Mutants for item 67 -- a snapshot that replaces another says what changed between them.

P45 is a guard that measured the right thing at the wrong boundary: `record` runs on every
invocation, so a run that stopped, had its task edited, and resumed snapshotted the edit as its
new baseline and reported UNCHANGED for the rest of the run. Nothing was wrong with the
comparison; it was simply never made at the moment that mattered.

So these break the moment rather than the comparison: the re-record stops comparing, compares and
says nothing, says something and records nothing, or records everything under one kind so a
legitimate edit between runs and an illegitimate one during a dispatch stop being distinguishable.

The last one is the defect this round already caught once, in the fix itself: a diff file named
by the clock collides with another edit in the same second, and the second overwrites the first.
"""

MUTANTS = [
    ("the re-record stops comparing, which is P45 exactly",
     "skills/execute/scripts/task-integrity.py",
     "    changed, removed, added, recorded = differences(args.tasks_path, snap)\n    between = []",
     "    changed, removed, added, recorded = None, None, None, None\n    between = []",
     "a snapshot that replaces another says what changed between them"),

    ("it compares and records nothing, so the evidence dies with the old snapshot",
     "skills/execute/scripts/task-integrity.py",
     "    if recorded is not None and (changed or removed or added):",
     "    if False:",
     "a snapshot that replaces another says what changed between them"),

    ("the report names the files and shows no diff",
     "skills/execute/scripts/task-integrity.py",
     "        for diff in diffs:\n            print(diff, end=\"\", file=sys.stderr)",
     "        pass",
     "a snapshot that replaces another says what changed between them"),

    ("an edit between runs is recorded as a mid-dispatch edit, and the two stop being different",
     "skills/execute/scripts/task-integrity.py",
     '        between, diffs, edits = write_edits(args, snap, recorded, changed, removed, added,\n'
     '                                            "edited-between-runs")',
     '        between, diffs, edits = write_edits(args, snap, recorded, changed, removed, added,\n'
     '                                            "modified")',
     "a snapshot that replaces another says what changed between them"),

    ("the count leaves the RECORDED line, so stdout reads as a clean record",
     "skills/execute/scripts/task-integrity.py",
     '          + (f" ({len(between)} changed since the last run)" if between else ""))',
     "          )",
     "a snapshot that replaces another says what changed between them"),

    ("a re-record after an edit between runs becomes a stop, and a fixable task has nowhere to go",
     "skills/execute/scripts/task-integrity.py",
     "    print(f\"RECORDED {len(entries)} task file(s) from {args.tasks_path}\"",
     "    return 1 or print(f\"RECORDED {len(entries)} task file(s) from {args.tasks_path}\"",
     "a snapshot that replaces another says what changed between them"),

    ("the diff file is named by the clock again, so two edits in one second erase one another",
     "skills/execute/scripts/task-integrity.py",
     '        name = f"{task_id_of(rel)}-{after_sha[:12]}.diff"',
     '        name = f"{task_id_of(rel)}-{at.replace(chr(58), chr(45))}.diff"',
     "a snapshot that replaces another says what changed between them"),

    ("a mid-dispatch edit stops being a stop, which is item 63 undone",
     "skills/execute/scripts/task-integrity.py",
     '          "diff above, and fix the task with /breakdown -- not from inside the run.",\n'
     "          file=sys.stderr)\n    return 1",
     '          "diff above, and fix the task with /breakdown -- not from inside the run.",\n'
     "          file=sys.stderr)\n    return 0",
     "a snapshot that replaces another says what changed between them"),

    ("/execute stops being told that a re-record reports anything",
     "skills/execute/SKILL.md",
     "**And a re-record says what it replaced (item 67).**",
     "**A re-record takes a fresh snapshot.**",
     "a snapshot that replaces another says what changed between them"),
]
