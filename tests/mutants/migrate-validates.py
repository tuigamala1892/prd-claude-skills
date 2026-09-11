"""/migrate validating what it produced, and checks.md held from both directions.

The validator was not run on the migrate path at all. The advice that followed -- `run
check-artefacts.py afterwards` -- was itself the evidence: a step somebody has to remember is one
this plan has repeatedly shown gets forgotten, which is why item 11 shipped a producer beside its
element rather than a note asking for one.

The registry mutants are the point of this file. checks.md was enforced in ONE direction: the
suite walked the repository and failed when a file ran an owning script without appearing in its
`Invoked by` column. Nothing walked the column and asked whether the caller it names still does
the thing, so a row could outlive the call it describes and go on claiming an assertion reaches a
skill that had stopped making it. A registry checked one way drifts the other, and the direction
nobody walks is the direction it drifts.

WHAT IS NOT MUTATED HERE, AND WHY

Phase 4 tells the reader to report the two exit codes separately -- `the migration did not finish`
and `the artefacts are not valid` are different problems with different fixes. That guidance has
no mutant, because it has no check, because it is tone. The same conclusion was reached twice
already in this suite by writing prose checks that passed while doing nothing. What IS held is
the structural half: the phase must INVOKE both scripts, which is the part that stops existing
when somebody deletes a step.
"""

SKILL = "skills/migrate/SKILL.md"
CHECKS = "schema/checks.md"

MUTANTS = [
    # The call itself. Note the row stays and the PROSE still names the script, so the registry's
    # mention-based check is satisfied throughout -- two sites mention it, one runs it, and only
    # a check keyed on the invocation can tell the difference.
    ("Phase 4 stops running the validator but goes on naming it",
     SKILL,
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/check-artefacts.py {path}\n",
     "",
     "Phase 4 RUNS the validator"),

    # Validating something other than what was migrated: the step is present, the result is about
    # a different tree, and every mention-based assertion still holds.
    ("Phase 4 validates a path other than the one it migrated",
     SKILL,
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/check-artefacts.py {path}",
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/check-artefacts.py .",
     "Phase 4 RUNS the validator"),

    # Registry, reality -> table. The suite already had this direction; it is here so the pair is
    # exercised together rather than each on its own.
    ("the registry forgets that /migrate validates",
     CHECKS,
     "`commands/prd.md` · `skills/breakdown/SKILL.md` · `skills/migrate/SKILL.md`",
     "`commands/prd.md` · `skills/breakdown/SKILL.md`",
     "every file that runs an owning script is listed as its caller"),

    # Registry, table -> reality, branch one: the named caller does not exist.
    ("a row names a caller that is not in the repository",
     CHECKS,
     "`commands/prd.md` · `skills/breakdown/SKILL.md` · `skills/migrate/SKILL.md`",
     "`commands/prd.md` · `skills/breakdown/SKILL.md` · `skills/migrate/SKILL-gone.md`",
     "every caller a row names actually runs its owner"),

    # Branch two: it exists and has nothing to do with the assertion. This is the drift that
    # actually happens -- a row edited to name the wrong file rather than a deleted one.
    ("a row names a caller that exists and never runs the script",
     CHECKS,
     "`commands/prd.md` · `skills/breakdown/SKILL.md` · `skills/migrate/SKILL.md`",
     "`commands/prd.md` · `skills/breakdown/SKILL.md` · `skills/execute/SKILL.md`",
     "every caller a row names actually runs its owner"),
]
