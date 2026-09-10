"""The correction to finding 6: whether an absent root element is expected here.

Finding 6 stopped a README halting the migration, and in doing so it answered a second question
nobody had asked it -- whether a `what-next.md` holding `# What Next` is an artefact. It is, and
a /prd run that went off-script produces exactly that file. The suite could not have caught it:
every what-next.md in every fixture is well-formed, so the fixtures agree with the reader. A
corpus found it.

These mutants hold both directions, because the fix is a boundary and a boundary can be pushed
either way. Losing the escalation puts the original defect back. Losing the skip puts finding 6's
defect back. One mutant each, and a third on the `features/` half, which is the part with no
fixed filename and therefore the part most likely to be dropped as an afterthought.
"""

MIGRATE = "schema/scripts/migrate.py"

MUTANTS = [
    # 1. The whole correction: everything rootless is prose again.
    ("a file the toolchain writes is skipped again when it has no root",
     MIGRATE,
     "            if toolchain_owns(path):",
     "            if False:",
     "a file the toolchain itself writes is missed when it has no root"),

    # 2. The named half. Dropping what-next.md from the set is the single edit that reproduces
    #    the reported defect exactly, with everything else still working.
    ("what-next.md stops being a name the toolchain owns",
     MIGRATE,
     'OWNED_NAMES = {"index.md", "what-next.md", "project.md"}',
     'OWNED_NAMES = {"index.md", "project.md"}',
     "a file the toolchain itself writes is missed when it has no root"),

    # 3. The directory half, which has no fixed filename behind it and is the easiest to lose.
    ("a prose file under features/ goes back to being nobody's artefact",
     MIGRATE,
     'OWNED_DIRS = {"features"}',
     'OWNED_DIRS = set()',
     "a file the toolchain itself writes is missed when it has no root"),

    # 4. The other direction. If every rootless file escalates, finding 6 is undone and one
    #    README halts the corpus again -- so the boundary is held from both sides.
    ("every rootless file escalates, so a README halts the corpus again",
     MIGRATE,
     "    return name in OWNED_NAMES or parent in OWNED_DIRS",
     "    return True",
     "a file that is not an artefact at all does not halt the migration"),
]
