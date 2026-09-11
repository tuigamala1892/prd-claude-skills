"""Items 33 and 34 -- EARS criteria, criterion priority, and the first mixed migration step.

Four checks: the criterion schema itself, the two-vocabulary rule, and the two migration checks
that had to be split when schema-2 -> schema-3 turned out not to be fully mechanical.

The PARTIAL mutants are the ones worth having. A script that stops at the judgement boundary and
one that crosses it both look like they worked -- the first leaves 550 criteria un-stamped, the
second invents the attribute the whole taxonomy depends on.
"""

CORE = "schema/core.md"
MIGRATE = "schema/scripts/migrate.py"
PRD_FMT = "schema/prd-format.md"
CRD_FMT = "skills/crd/references/crd-format.md"

MUTANTS = [
    ("a template criterion goes back to Given/When/Then",
     PRD_FMT,
     '    <criterion id="1" pattern="event-driven" priority="P0">\n'
     "      When {{trigger}}, the system shall {{response}}.",
     '    <criterion id="1">\n'
     "      <given>{{context}}</given><when>{{action}}</when><then>{{outcome}}</then>",
     "a criterion is one EARS sentence"),

    ("a criterion loses the word `shall`, becoming a scenario again",
     CRD_FMT,
     "When the user toggles the dark mode switch on, the system shall apply the dark theme\n"
     "    immediately.",
     "When the user toggles the dark mode switch on, the dark theme is applied.",
     "a criterion is one EARS sentence"),

    ("a criterion is assigned a pattern outside the taxonomy",
     PRD_FMT,
     '<criterion id="2" pattern="unwanted-behaviour" priority="P1">',
     '<criterion id="2" pattern="error-case" priority="P1">',
     "a criterion is one EARS sentence"),

    ("criterion priority is written in MoSCoW after all",
     CRD_FMT,
     '<criterion id="3" pattern="optional-feature" priority="P1">',
     '<criterion id="3" pattern="optional-feature" priority="should-have">',
     "a criterion is one EARS sentence"),

    ("the generator stops distinguishing the failure patterns from the happy path",
     "skills/breakdown-generate-tasks/SKILL.md",
     "| `unwanted-behaviour` | the error path — the thing that must NOT happen, does not |",
     "| (removed) | — |",
     "a criterion is one EARS sentence"),

    ('the two priority levels collapse into one vocabulary',
     'schema/core.md',
     '| Requirement | `priority=` on each `<criterion>`, both paths | `P0` · `P1` · `P2` | which criteria within them are built |',
     '| Requirement | `priority=` on each `<criterion>`, both paths | `must-have` · `should-have` · `could-have` | which criteria within them are built |',
     'the two priority levels stay in two vocabularies'),

    ("the filter stops saying which of the two runs first",
     "skills/breakdown/SKILL.md",
     "**Applied second, always.**",
     "**They compose.**",
     "the two priority levels stay in two vocabularies"),

    ("the filter stops reporting what it excluded",
     "skills/breakdown/SKILL.md",
     "**Report what the filter excluded, by feature.**",
     "**Get on with it.**",
     "the two priority levels stay in two vocabularies"),

    ("the migration invents the pattern it is forbidden to assign",
     MIGRATE,
     '        if not re.search(r\'\\bpriority=\', attrs):\n            add += \' priority="P1"\'',
     '        if not re.search(r\'\\bpattern=\', attrs):\n            add += \' pattern="event-driven"\'\n'
     '        if not re.search(r\'\\bpriority=\', attrs):\n            add += \' priority="P1"\'',
     "a migration it may not finish does the half it can"),

    ("priority is left to the documented default instead of written in",
     MIGRATE,
     "        if not re.search(r'\\bpriority=', attrs):\n            add += ' priority=\"P1\"'",
     "        if False:\n            add += ' priority=\"P1\"'",
     "a migration it may not finish does the half it can"),

    ("derived-from is dropped, so the rewrite cannot be reviewed",
     MIGRATE,
     "        if cid and not re.search(r'\\bderived-from=', attrs):",
     "        if False:",
     "a migration it may not finish does the half it can"),

    ("PARTIAL stops being reported, so a half-done tree reads as done",
     MIGRATE,
     '    return text, report, problems, ("PARTIAL" if partial else "MIGRATED")',
     '    return text, report, problems, "MIGRATED"',
     "a migration it may not finish does the half it can"),

    ("--check accepts a PARTIAL tree",
     MIGRATE,
     "    if args.check and (migrated or partial):",
     "    if args.check and migrated:",
     "a migration it may not finish does the half it can"),

    ("the mechanical step wanders outside the criteria",
     MIGRATE,
     '    return CRITERION.sub(one, text)',
     '    return CRITERION.sub(one, text).replace("<description>", "<desc>")',
     "a migration it may not finish does the half it can"),

    ("the golden comparison is pointed at a step that carries judgements",
     "tests/fixture/prd/SCHEMAS.json",
     '"migration_from_previous": "mechanical"',
     '"migration_from_previous": "mixed"',
     "the migration turns the old fixture into the new one"),
]
