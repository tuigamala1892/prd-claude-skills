"""The CRD path's sign-off: /crd --resume classifies, and sign-off.py does the edit.

A CRD has no <review>, so the PRD path's trigger is absent. The script has three refusals, each
protecting something a sign-off must not touch, and one implementation shared with
check-definition.py. The mutants remove the refusals one at a time, fork the implementation,
and loosen the command's step.
"""

SO = "schema/scripts/sign-off.py"
CRD = "commands/crd.md"
CHECK = ("a migrated CRD is signed off in /crd --resume by the same code as a PRD feature "
         "-- by running it")

MUTANTS = [
    # --- the script's refusals ---------------------------------------------------------------------
    ("a complete CRD is signed off, rewriting a record of the past",
     SO,
     "    if state and state.group(2) in PAST:",
     "    if False:",
     CHECK),

    ("a PRD feature gains a second sign-off route beside its review",
     SO,
     '    if re.search(r"^\\s*<feature>", text, re.M):',
     "    if False:",
     CHECK),

    ("an unmigrated CRD is signed off",
     SO,
     '    if "<requirements>" in text:',
     "    if False:",
     CHECK),

    ("the sign-off removes derived-from from nothing",
     SO,
     '        without = re.sub(r\'\\s+derived-from="[^"]*"\', "", attrs)',
     "        without = attrs",
     CHECK),

    # --- one implementation ------------------------------------------------------------------------
    ("check-definition.py grows its own copy of the sign-off",
     "skills/breakdown/scripts/check-definition.py",
     "def record_review(path, by):",
     "def sign_off(text):\n    return text, 0, []\n\n\ndef record_review(path, by):",
     CHECK),

    # --- the command's step --------------------------------------------------------------------------
    ("the CRD step classifies but never signs off",
     CRD,
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/sign-off.py {project_path}/docs/crd/{slug}.md",
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py {project_path}/docs/crd/{slug}.md --check",
     CHECK),

    ("a complete CRD is offered for sign-off",
     CRD,
     "**A `complete` or `abandoned` CRD is not offered.**",
     "**A `complete` or `abandoned` CRD is offered like any other.**",
     CHECK),

    ("the document priority is derived from the criteria",
     CRD,
     "Never take the highest criterion priority.",
     "Take the highest criterion priority if the person is unsure.",
     CHECK),

    ("accepting a pattern on a CRD removes derived-from by hand",
     CRD,
     "| accepts the sentence and the pattern | the `pattern` |\n| corrects the pattern | their `pattern` |\n| rewrites the sentence | their sentence, and the `pattern` they give it |\n| defers it | nothing. The criterion stays unclassified |\n\n**Leave `derived-from` in place, on every row.** It is how the person checks each sentence against\nthe requirement",
     "| accepts the sentence and the pattern | the `pattern`, and remove `derived-from` |\n| corrects the pattern | their `pattern` |\n| rewrites the sentence | their sentence, and the `pattern` they give it |\n| defers it | nothing. The criterion stays unclassified |\n\n**Leave `derived-from` in place, on every row.** It is how the person checks each sentence against\nthe requirement",
     CHECK),

    ("the agent refuses a CRD in sign-off mode",
     "agents/prd-criteria-author.md",
     "**This is the one mode that also takes a CRD.**",
     "**This mode takes a PRD feature only.**",
     CHECK),
]
