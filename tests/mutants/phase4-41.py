"""Item 41 -- the migration, its golden comparison, and its escalation path.

Two of these checks RUN the script, which is the only way the claim is worth anything: a
migration verified by reading it is a migration nobody has watched work. The third is about the
guide having a consumer, which is item 23's rule applied to item 41's own output.

The escalation mutants are the ones worth having. `stop and report this file, never transform it
anyway` is easy to write and easy to erode -- and the erosion looks like helpfulness.

EVERY ANCHOR IN THIS FILE WAS ONCE STALE

Nine of these twelve reported ANCHOR NOT FOUND: they were written against a shape `migrate.py`
had before the rules became six-tuples carrying their target version, and they had been inert
ever since -- through every round anybody ran. A mutation harness reports an unapplied mutant as
MISSED, which reads exactly like a check that failed to catch a real defect, so the number was
wrong in the direction that looks like rigour. `MISSED` has two meanings and only one of them is
about the check.

That is the argument for re-running this file whenever `migrate.py` changes shape, rather than
only when its behaviour does. An anchor is a dependency on someone else's source text, and it is
the only kind this repository keeps that nothing else validates.
"""

MIGRATE = "schema/scripts/migrate.py"
GUIDE = "schema/migration.md"

MUTANTS = [
    ("the rename drops a value instead of preserving it",
     MIGRATE,
     r'''    inner = re.sub(r"<%s>(.*?)</%s>" % (old, old), r"<%s>\1</%s>" % (new, new),
                   m.group(1), flags=re.S)''',
     r'''    inner = re.sub(r"<%s>(.*?)</%s>" % (old, old), r"<%s>tbd</%s>" % (new, new),
                   m.group(1), flags=re.S)''',
     "the migration turns the old fixture into the new one"),

    ("R1 starts matching index.md too, which breaks --resume",
     MIGRATE,
     '    ("R1", "schema-2", "feature",',
     '    ("R1", "schema-2", "prd",',
     "the migration turns the old fixture into the new one"),

    # This one used to read `the transformation escapes <meta> and renames the whole file`, and
    # that mutant is NOT DETECTABLE by this corpus: no feature file in any fixture carries a
    # second <status> outside <meta>, so a rename that escaped the element would have nothing
    # extra to rename and the golden comparison would pass. Recorded rather than quietly
    # reformulated, because `we could not exercise this` and `this is safe` are different
    # statements. What is exercised instead is the other half of the same line -- the splice that
    # puts the rewritten <meta> back -- where losing the element's own tags is a structural loss
    # the comparison does see.
    ("the splice drops the <meta> tags it edited inside",
     MIGRATE,
     # `_meta_drop` ends on the identical line, so the anchor carries the line above it.
     "                   m.group(1), flags=re.S)\n"
     "    return text[:m.start(1)] + inner + text[m.end(1):]",
     "                   m.group(1), flags=re.S)\n"
     "    return text[:m.start()] + inner + text[m.end():]",
     "the migration turns the old fixture into the new one"),

    ("a second run transforms again instead of reporting ALREADY",
     MIGRATE,
     "        if VERSIONS.index(current) >= VERSIONS.index(args.target):",
     "        if False:",
     "the migration turns the old fixture into the new one"),

    ("--check stops distinguishing 'ran' from 'finished'",
     MIGRATE,
     "    if args.check and (migrated or partial):",
     "    if False and (migrated or partial):",
     "the migration turns the old fixture into the new one"),

    ("an unplaceable file is given the oldest schema instead of stopping",
     MIGRATE,
     "        else:\n            return None\n    return reached",
     "        else:\n            return VERSIONS[0]\n    return reached",
     "a file the migration cannot place stops it, and is named"),

    ("escalation stops being distinguishable from success",
     MIGRATE,
     "    if escalations:\n        return 2\n    if partial:\n        return 0\n    return 0",
     "    if partial:\n        return 0\n    return 0",
     "a file the migration cannot place stops it, and is named"),

    ("the escalated files are counted but not named",
     MIGRATE,
     '    for line in escalations:\n        print(f"  ESCALATE   {line}", file=sys.stderr)\n\n    if failures:',
     '    for line in escalations:\n        print("  ESCALATE   (a file)", file=sys.stderr)\n\n    if failures:',
     "a file the migration cannot place stops it, and is named"),

    ("one unplaceable file gives up on the whole tree",
     MIGRATE,
     '            escalations.append(\n                f"{rel}: a <{kind}> in no recognised schema '
     '-- no migration can be selected")\n            continue',
     '            escalations.append(\n                f"{rel}: a <{kind}> in no recognised schema '
     '-- no migration can be selected")\n            break',
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

    # The old form of this mutant replaced only the ACTION half of the row -- `stop` became
    # `carry on with the rest` -- and the check greps for the phrase `no precondition`, which
    # that edit leaves in place. So it would have survived even had its anchor matched: a mutant
    # that models the erosion without touching what the check reads is a mutant that cannot fail.
    # This one removes the phrase, which is what the check actually asserts is there.
    ("the skill loses the instruction to stop on an unplaceable file",
     "skills/migrate/SKILL.md",
     "| 2 | one or more files matched no precondition, or could not be decoded as UTF-8 | "
     "**stop.** Report each by name |",
     "| 2 | some files were skipped | carry on with the rest |",
     "the migration guide has an executor"),
]
