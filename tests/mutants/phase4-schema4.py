"""Items 1, 2, 5, 27, 29 and 35 -- the rest of the feature template, as one schema version.

Four new checks plus the two migration ones, which now have a second mixed step to exercise.

The mutants that matter here are the ones that look like tidying. Restoring `<priority>` to the
feature file looks like completeness; giving `reference` an ordering constraint looks like
consistency; banning `TBD` outright looks like rigour. Each of the three destroys something the
plan spent an item establishing.
"""

CORE = "schema/core.md"
PRD_FMT = "schema/prd-format.md"
MIGRATE = "schema/scripts/migrate.py"
ANALYZE = "skills/breakdown-analyze-prd/SKILL.md"
PLAN = "skills/breakdown-plan-layers/SKILL.md"

MUTANTS = [
    # ---- item 29: gaps ---------------------------------------------------------------------
    ("a gap kind that warns starts stopping the run instead",
     CORE,
     "| `ownership` | no | **warn** — the boundary may move under the task |",
     "| `ownership` | no | yes |",
     "uncertainty has a channel that survives the handoff"),

    ("the specification gap stops barring `defined`",
     CORE,
     "| `specification` | **yes** — it bars `defined` outright | yes |",
     "| `specification` | no | yes |",
     "uncertainty has a channel that survives the handoff"),

    ("the placeholder ban goes back to banning marked uncertainty too",
     "skills/breakdown/references/review-criteria.md",
     '- [ ] No **unmarked** placeholder text: "TODO", "TBD", "...", "[fill in]", "etc."',
     '- [ ] No placeholder text: "TODO", "TBD", "...", "[fill in]", "etc."',
     "uncertainty has a channel that survives the handoff"),

    ("the reviewer's copy of the ban loses the qualification",
     "skills/breakdown-review-tasks/SKILL.md",
     '- No **unmarked** placeholder text: "TODO", "TBD", "...", "[fill in]", "etc."',
     '- No placeholder text: "TODO", "TBD", "...", "[fill in]", "etc."',
     "uncertainty has a channel that survives the handoff"),

    ("the analyser starts answering gaps instead of carrying them",
     ANALYZE,
     "### `gaps` are carried, never resolved",
     "### `gaps` are reviewed and settled here",
     "uncertainty has a channel that survives the handoff"),

    ("task files stop carrying the gaps that reach them",
     "skills/breakdown/references/task-format-spec.md",
     "<gaps>\n  <gap id=\"3\" kind=\"decision\" raised=\"2026-08-18\">",
     "<!-- gaps are left in the PRD -->\n  <!-- gap id=\"3\" kind=\"decision\" raised=\"2026-08-18\">",
     "uncertainty has a channel that survives the handoff"),

    # ---- item 27: dependencies -------------------------------------------------------------
    ("`reference` acquires an ordering constraint",
     PLAN,
     "| `reference` | **none.** It says the two are related, not that one waits |",
     "| `reference` | the depended-on feature comes first |",
     "feature dependencies are declared edges"),

    ("plan-layers defers to the interview's recorded sequence again",
     PLAN,
     "**You own the ordering, and you are the only component that does.**",
     "**Follow the sequence in `what-next.md` where one exists.**",
     "feature dependencies are declared edges"),

    # The anchor spans a line wrap, which the first version of this mutant did not and so was
    # reported ANCHOR NOT FOUND -- a mutant that never applied, which the harness distinguishes
    # from one that applied and was missed. They are different defects and it names both.
    ("the analyser re-derives edges from markdown links",
     ANALYZE,
     "**A markdown link between features is not an\nedge**",
     "A markdown link between features is also an\nedge",
     "feature dependencies are declared edges"),

    # ---- items 1, 5, 35 --------------------------------------------------------------------
    ("`<priority>` comes back to the feature file",
     PRD_FMT,
     "    <!-- priority is NOT here. It lives on the index entry -- core §4 -->",
     "    <priority>must-have|should-have|could-have</priority>",
     "the feature template carries intent, significance"),

    ("the definition enum loses the values that keep a rejected feature in the record",
     PRD_FMT,
     "    <definition>tbd|in-progress|defined|excluded|superseded</definition>",
     "    <definition>tbd|in-progress|defined</definition>",
     "the feature template carries intent, significance"),

    ("the user story is dropped from the template",
     PRD_FMT,
     "  <user-story>\n  As a {{actor}}, I want {{capability}}, so that {{benefit}}.\n  </user-story>",
     "  <!-- intent goes in the description -->",
     "the feature template carries intent, significance"),

    ("a phase attribute reappears on a criterion",
     PRD_FMT,
     '    <criterion id="1" pattern="event-driven" priority="P0">',
     '    <criterion id="1" pattern="event-driven" priority="P0" phase="1">',
     "the feature template carries intent, significance"),

    # The conclusion survives and the reason goes -- which is how an argued section decays in
    # practice, and is why the check asserts the reason rather than the heading.
    ("the <phases> argument keeps its conclusion and loses its reason",
     PRD_FMT,
     "A phase would have forced an author to *demote* something\nimportant in order to say it was stuck.",
     "A phase would have been worse.",
     "the feature template carries intent, significance"),

    ("the significance flag loses its only reader",
     "skills/breakdown/scripts/check-references.py",
     'SIGNIFICANT = re.compile(r"<architecturally-significant\\b([^>]*)>")',
     'SIGNIFICANT = re.compile(r"<never-matches-anything\\b([^>]*)>")',
     "the feature template carries intent, significance"),

    # ---- item 2 ----------------------------------------------------------------------------
    ("<considerations> stops being marked unread by design",
     PRD_FMT,
     "**`<considerations>` is unread by design, and the template says so.**",
     "**`<considerations>` holds the rest.**",
     "`<considerations>` is unread by design"),

    ("the analyser goes back to inferring over a declared data model",
     ANALYZE,
     "**When a feature declares one, copy it. Do not infer alongside it.**",
     "Infer the data model from the feature text.",
     "`<considerations>` is unread by design"),

    ("the migration drops note prose instead of carrying it to the catch-all",
     MIGRATE,
     "        parts.append(block(\"considerations\", lines))",
     "        parts.append(block(\"considerations\", lines[:1]))",
     "a migration it may not finish does the half it can"),

    ("the migration writes a user story it was forbidden to invent",
     MIGRATE,
     "     lambda t: _split_notes(_meta_drop(t, \"priority\")),",
     "     lambda t: _split_notes(_meta_drop(t, \"priority\")).replace("
     "\"<description>\", \"<user-story>As a user...</user-story>\\n  <description>\"),",
     "a migration it may not finish does the half it can"),

    ("the duplicated priority survives the migration",
     MIGRATE,
     '     lambda t: _split_notes(_meta_drop(t, "priority")),',
     '     lambda t: _split_notes(t),',
     "a migration it may not finish does the half it can"),
]
