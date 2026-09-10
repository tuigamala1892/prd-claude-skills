"""Item 41's three re-entry defects, each mutant restoring the behaviour that was there before.

These four are the fixes for what a real corpus met on its second pass and the suite never did,
because every migration check ran one step, once, on a fresh copy. The step and the FIRST run
were the only things under test, and both of those are the easy half: the corpus that matters is
one somebody interrupted.

Each mutant puts back the exact line that was wrong. If one of them survives, the check that
replaced it has stopped doing the work it was written to do.
"""

MIGRATE = "schema/scripts/migrate.py"

MUTANTS = [
    # 1. The re-entry fix itself. R9 and R10 have preconditions that go false the moment their
    #    mechanical half lands, so without the PARTIAL_OF fork a second pass called a correctly
    #    PARTIAL file FAILED and exited 1.
    ("a rule left PARTIAL by an earlier pass is called unplaceable again",
     MIGRATE,
     """                if rid in PARTIAL_OF and PARTIAL_OF[rid](text):
                    partial = True
                    outstanding.append(rid)""",
     """                if False:
                    partial = True
                    outstanding.append(rid)""",
     "a partly migrated tree is safe to re-enter"),

    # 2. R4/R5 keyed on `pattern` again. R10's postcondition REQUIRES the criteria it creates to
    #    lack a pattern, so the old key made a schema-5 CRD read back as schema-2 and collected
    #    `derived-from` on criteria a person had authored.
    ("R4/R5 key on `pattern`, which R10 legitimately leaves absent",
     MIGRATE,
     '''    ("R4", "schema-3", "feature",
     lambda t: bool(_criteria_lacking(t, "priority")),''',
     '''    ("R4", "schema-3", "feature",
     lambda t: bool(_criteria_lacking(t, "pattern")),''',
     "an authored criterion never gains a migration's provenance"),

    ("R5 keys on `pattern`, so a migrated CRD oscillates between versions",
     MIGRATE,
     '''    ("R5", "schema-3", "crd",
     lambda t: bool(_criteria_lacking(t, "priority")),''',
     '''    ("R5", "schema-3", "crd",
     lambda t: bool(_criteria_lacking(t, "pattern")),''',
     "a partly migrated tree is safe to re-enter"),

    # 3. Line endings. Nothing fails a postcondition when this regresses -- values and tag counts
    #    both survive the flip -- so the only thing that catches it is a check that looks.
    ("every file is rewritten to LF, whatever it arrived as",
     MIGRATE,
     r'''    return text.replace("\r\n", "\n"), ("\r\n" if crlf > text.count("\n") - crlf else "\n")''',
     r'''    return text.replace("\r\n", "\n"), "\n"''',
     "a migration keeps the line endings it found"),

    # 4. The decode. This is the only regression in the file that loses content outright, and it
    #    exits 0 while doing it.
    ("undecodable bytes become U+FFFD and are written back",
     MIGRATE,
     '    text = raw.decode("utf-8")',
     '    text = raw.decode("utf-8", "replace")',
     "a file the migration cannot decode is escalated"),
]
