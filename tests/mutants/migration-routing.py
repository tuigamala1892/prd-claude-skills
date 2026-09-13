"""Findings 5 and 6 -- where a refusal is routed, which decides what the operator is told.

Both of these were exit codes that carried the wrong advice rather than wrong behaviour, and
that is the failure mode worth mutants: the script did stop, the file was left alone, and the
only thing wrong was which of three meanings the stop had. Nothing in a postcondition can see
that, and the person reading the output acts on it.

The two directions are mutated separately on purpose. Relaxing an escalation and tightening one
are opposite mistakes with the same shape, and a fix for either that quietly makes the other
worse is exactly what this file exists to catch.
"""

MIGRATE = "schema/scripts/migrate.py"
SKILL = "skills/migrate/SKILL.md"

MUTANTS = [
    # --- Finding 6 -------------------------------------------------------------------------
    ("a README is escalated again, halting a corpus that documents itself",
     MIGRATE,
     '            skipped.append(f"{rel}: no artefact root element -- not an artefact; left alone")',
     '            escalations.append(f"{rel}: no artefact root element -- cannot select a migration")',
     "a file that is not an artefact at all does not halt the migration"),

    ("files that are not artefacts are swallowed instead of listed",
     MIGRATE,
     '    for line in skipped:\n        print(f"  SKIPPED    {line}")\n    for line in short:',
     '    for line in []:\n        print(f"  SKIPPED    {line}")\n    for line in short:',
     "a file that is not an artefact at all does not halt the migration"),

    # The opposite direction: the fix must not have relaxed the case exit 2 exists for.
    ("an artefact in no recognised schema is skipped rather than escalated",
     MIGRATE,
     '            escalations.append(\n                f"{rel}: a <{kind}> in no recognised schema '
     '-- no migration can be selected")\n            continue',
     '            skipped.append(\n                f"{rel}: a <{kind}> in no recognised schema '
     '-- no migration can be selected")\n            continue',
     "a file the migration cannot place stops it, and is named"),

    # --- Finding 5 -------------------------------------------------------------------------
    ("a missing rationale is called a defect in the rule again",
     MIGRATE,
     '                escalations.append(\n                    f"{rel}: " + "; ".join(broken)\n'
     '                    + " -- NOT WRITTEN. A person supplies this; the migration cannot")',
     '                failures.append(f"{rel}: " + "; ".join(broken) + " -- NOT WRITTEN")',
     "an artefact missing what only a person can write is escalated"),

    # The dual read is what decided WHICH check saw the gap, so it is the routing's real hinge.
    ("the old spelling stops being read, so the gap surfaces as a rule defect",
     MIGRATE,
     '    d = re.search(r"<(definition|status)>\\s*([a-z-]+)\\s*</\\1>", m.group(1))',
     '    d = re.search(r"<(definition)>\\s*([a-z-]+)\\s*</\\1>", m.group(1))',
     "an artefact missing what only a person can write is escalated"),

    # Two earlier versions of this mutant survived, and both were right to. The first replaced a
    # single SENTENCE of the skill's guidance, leaving a paragraph that contradicted itself --
    # nothing can detect that. The second removed the paragraph outright, and the check that
    # should have caught it passed anyway: the paragraph that merely NAMES the case quotes the
    # script's line `A person supplies this`, which satisfied every shape worth writing.
    #
    # That conclusion is recorded rather than worked around. The tone of prose guidance is not
    # mechanically checkable, and a check that appears to hold it is worse than none. What is
    # checkable is the prohibition itself, sitting in the agent's list of prohibitions -- which
    # is where `do not invent a rationale` now lives, and what this mutant removes.
    ("the agent stops being told not to invent the rationale it is missing",
     "agents/schema-migrator.md",
     "- writing a missing `<rationale>` or `<superseded-by>` pointer for R7 or R8\n",
     "",
     "an artefact missing what only a person can write is escalated"),
]
