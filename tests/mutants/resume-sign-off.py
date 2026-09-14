"""Sign-off: the step that ends `derived-from`, performed by a person in /prd --resume.

Core section 2 had said since item 41 that `derived-from` lasts "until sign-off", and nothing
performed one. After a live migration, every criterion in a corpus had no pattern and no step to
reach it. The exception this adds is narrow on purpose: the challenger may propose a pattern for a
sentence a MIGRATION wrote, and still not for one a person wrote.

Sign-off has two steps. A person classifies, and `derived-from` stays for the reviewer. Recording
the review then removes it from exactly the classified criteria. Most of these mutants move the
removal to the wrong moment or apply it to the wrong criteria.
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
    ("accepting a pattern removes derived-from before the reviewer has used it",
     PRD,
     "| accepts the sentence and the pattern | the `pattern` |",
     "| accepts the sentence and the pattern | the `pattern`, and remove `derived-from` |",
     CHECK),

    ("the resume step stops saying the review is the sign-off",
     PRD,
     "**Recording it is the sign-off.**",
     "**Recording it is the final step.**",
     CHECK),

    # --- the sign-off itself, in the review writer ------------------------------------------------
    ("recording a review signs nothing off",
     "skills/breakdown/scripts/check-definition.py",
     '    stripped, signed, _unclassified = _so.sign_off(REVIEW.sub("", text))',
     '    stripped, signed, _unclassified = REVIEW.sub("", text), 0, []',
     CHECK),

    ("the sign-off touches criteria nobody classified",
     "schema/scripts/sign-off.py",
     "            return m.group(0)\n        without = ",
     "            pass\n        without = ",
     CHECK),

    ("the review hashes the file before signing it off, so it is born STALE",
     "skills/breakdown/scripts/check-definition.py",
     '        by, time.strftime("%Y-%m-%d"), content_sha(stripped))',
     '        by, time.strftime("%Y-%m-%d"), content_sha(REVIEW.sub("", text)))',
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

    # --- R6's story: owed by `defined` only, in both halves of the rule -------------------------
    ("R6's postcondition asks every feature for a story again",
     "schema/scripts/migrate.py",
     '               and (not _is_defined(t) or "<user-story>" in t)),',
     '               and "<user-story>" in t),',
     "R6 owes a user story to `defined` features only -- by running it"),

    ("R6 stops asking a defined feature for its story",
     "schema/scripts/migrate.py",
     '               and (not _is_defined(t) or "<user-story>" in t)),',
     '               and True),',
     "R6 owes a user story to `defined` features only -- by running it"),

    # --- the procedure: a sign-off --check would never accept ----------------------------------
    ("R4's postcondition demands derived-from, so a signed-off file is never finished",
     "schema/scripts/migrate.py",
     '     lambda t: not _criteria_lacking(t, "pattern") and not _criteria_lacking(t, "priority")),\n\n    ("R5"',
     '     lambda t: not _criteria_lacking(t, "pattern") and not _criteria_lacking(t, "priority")\n'
     '               and not _criteria_lacking(t, "derived-from")),\n\n    ("R5"',
     CHECK),
]
