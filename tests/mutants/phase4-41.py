"""Item 41 -- the migration, its golden comparison, and its escalation path.

Two of these checks RUN the script, which is the only way the claim is worth anything: a
migration verified by reading it is a migration nobody has watched work. The third is about the
guide having a consumer, which is item 23's rule applied to item 41's own output.

The escalation mutants are the ones worth having. `stop and report this file, never transform it
anyway` is easy to write and easy to erode -- and the erosion looks like helpfulness.
"""

MIGRATE = "schema/scripts/migrate.py"
GUIDE = "schema/migration.md"

MUTANTS = [
    ("the rename drops a value instead of preserving it",
     MIGRATE,
     r'swapped = re.sub(r"<%s>(.*?)</%s>" % (old, old), r"<%s>\1</%s>" % (new, new), inner, flags=re.S)',
     r'swapped = re.sub(r"<%s>(.*?)</%s>" % (old, old), r"<%s>tbd</%s>" % (new, new), inner, flags=re.S)',
     "the migration turns the old fixture into the new one"),

    ("R1 starts matching index.md too, which breaks --resume",
     MIGRATE,
     '    ("R1", "feature",',
     '    ("R1", "prd",',
     "the migration turns the old fixture into the new one"),

    ("the transformation escapes <meta> and renames the whole file",
     MIGRATE,
     "    m = META.search(text)\n    if not m:\n        return text\n    inner = m.group(1)",
     "    m = META.search(text)\n    if not m:\n        return text\n    inner = text",
     "the migration turns the old fixture into the new one"),

    ("a second run transforms again instead of reporting ALREADY",
     MIGRATE,
     '        if done(text):\n            return kind, rid, "ALREADY"',
     '        if False:\n            return kind, rid, "ALREADY"',
     "the migration turns the old fixture into the new one"),

    ("--check stops distinguishing 'ran' from 'finished'",
     MIGRATE,
     "    if args.check and migrated:",
     "    if False:",
     "the migration turns the old fixture into the new one"),

    ("an unplaceable file is transformed anyway instead of stopping",
     MIGRATE,
     '    return kind, None, "ESCALATE"\n\n\ndef main():',
     '    return kind, RULES[0][0], "MIGRATE"\n\n\ndef main():',
     "a file the migration cannot place stops it, and is named"),

    ("escalation stops being distinguishable from success",
     MIGRATE,
     "    if escalations:\n        return 2\n    return 0",
     "    return 0",
     "a file the migration cannot place stops it, and is named"),

    ("the escalated files are counted but not named",
     MIGRATE,
     '    for line in escalations:\n        print(f"  ESCALATE   {line}", file=sys.stderr)\n\n    if failures:',
     '    for line in escalations:\n        print("  ESCALATE   (a file)", file=sys.stderr)\n\n    if failures:',
     "a file the migration cannot place stops it, and is named"),

    ("one unplaceable file gives up on the whole tree",
     MIGRATE,
     '        if verdict == "ESCALATE":',
     '        if verdict == "ESCALATE" or escalations:',
     "a file the migration cannot place stops it, and is named"),

    ("the guide stops naming the agent that performs its judgements",
     GUIDE,
     "[`schema-migrator`](../agents/schema-migrator.md)",
     "an agent",
     "the migration guide has an executor"),

    ("the executor stops citing the guide, so it follows what it remembers",
     "agents/schema-migrator.md",
     "Your specification is [`schema/migration.md`](../schema/migration.md).",
     "Your specification is what follows.",
     "the migration guide has an executor"),

    ("the skill loses the instruction to stop on an unplaceable file",
     "skills/migrate/SKILL.md",
     "| 2 | one or more files matched no precondition | **stop.** Report each by name |",
     "| 2 | one or more files matched no precondition | carry on with the rest |",
     "the migration guide has an executor"),
]
