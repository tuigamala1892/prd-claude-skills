"""Sign-off: the step that ends `derived-from`, performed by a person in /prd --resume.

Core section 2 had said since item 41 that `derived-from` lasts "until sign-off", and nothing
performed one. After a live migration, every criterion in a corpus had no pattern and no step to
reach it. The exception this adds is narrow on purpose: the challenger may propose a pattern for a
sentence a MIGRATION wrote, and still not for one a person wrote. Most of these mutants widen that
exception or loosen the pairing of `pattern` with the removal of `derived-from`.
"""

AGENT = "agents/prd-criteria-author.md"
PRD = "commands/prd.md"
CHECK = ("a migrated criterion is signed off by a person in /prd --resume, and the sign-off "
         "reaches --check -- by running it")

MUTANTS = [
    # --- the agent -----------------------------------------------------------------------------
    ("the challenger may propose a pattern for an authored criterion",
     AGENT,
     "You may **not** propose one for a\ncriterion a person wrote.",
     "You may also propose one for a\ncriterion a person wrote.",
     CHECK),

    ("sign-off mode may rewrite the sentences it reads",
     AGENT,
     "**Do not rewrite a sentence.** If one is unsound, say what is wrong; the person rewrites it.",
     "**Rewrite a sentence** if one is unsound, and say what you changed.",
     CHECK),

    ("the challenger loses its sign-off mode",
     AGENT,
     "| `sign-off` | What pattern is each migrated sentence",
     "| `migrated` | What pattern is each migrated sentence",
     CHECK),

    # --- the resume step -------------------------------------------------------------------------
    ("accepting a pattern leaves derived-from in place",
     PRD,
     "| accepts the sentence and the pattern | the `pattern`, and **remove `derived-from` in the same edit** |",
     "| accepts the sentence and the pattern | the `pattern` |",
     CHECK),

    ("deferring a criterion removes its derived-from anyway",
     PRD,
     "| defers it | nothing. The criterion keeps `derived-from` and stays unsigned |",
     "| defers it | remove `derived-from`, and leave the pattern for later |",
     CHECK),

    ("sign-off is offered across the whole PRD at once",
     PRD,
     "**Then offer it, one feature at a time, and let the person choose which.**",
     "**Then offer it across every PRD feature in one pass.**",
     CHECK),

    ("the sign-off dispatch runs in the background",
     PRD,
     "  run_in_background: false,\n  description: \"Sign off migrated criteria for {slug}\"",
     "  description: \"Sign off migrated criteria for {slug}\"",
     CHECK),

    # --- the procedure: a sign-off --check would never accept ----------------------------------
    ("R4's postcondition demands derived-from, so a signed-off file is never finished",
     "schema/scripts/migrate.py",
     '     lambda t: not _criteria_lacking(t, "pattern") and not _criteria_lacking(t, "priority")),\n\n    ("R5"',
     '     lambda t: not _criteria_lacking(t, "pattern") and not _criteria_lacking(t, "priority")\n'
     '               and not _criteria_lacking(t, "derived-from")),\n\n    ("R5"',
     CHECK),
]
