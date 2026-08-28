"""Mutants for items 13, 14 and 15 -- the three filters `/breakdown` never had.

The three rules are not the same KIND of rule, and most of these mutants attack that distinction
rather than the filtering itself. A selector that filters correctly but lets item 13 be overridden
has turned a decision into a suggestion; one whose default has drifted silently changes what every
existing invocation builds; one that refuses on every gap kind halts an overnight run on an open
question rather than on an unknown.

The two `report` mutants matter as much as the rest. Item 15's whole content is that what it
skipped is NAMED -- a silently omitted must-have is worse than the unfiltered behaviour this
replaced -- so a selector that drops the right features and says nothing has failed the item.
"""

MUTANTS = [
    # ------------------------------------------------------------------ item 13
    ("item 13 becomes overridable, turning a decision into a suggestion",
     "skills/breakdown/scripts/select-features.py",
     '    if tier == "wont-have":',
     '    if tier == "wont-have" and not include_tbd:',
     "declines work it was told not to do"),

    ("a superseded feature comes back, so a merged feature is built twice",
     "skills/breakdown/scripts/select-features.py",
     '    if definition == "superseded":\n'
     '        out.append("item 13: `<definition>superseded</definition>` -- see `<superseded-by>`")',
     '    if definition == "superseded-nope":\n'
     '        out.append("item 13: `<definition>superseded</definition>` -- see `<superseded-by>`")',
     "declines work it was told not to do"),

    # ------------------------------------------------------------------ item 14
    ("the default threshold drifts, silently changing what every existing invocation builds",
     "skills/breakdown/scripts/select-features.py",
     '    ap.add_argument("--priority", default="could-have", choices=SELECTABLE,',
     '    ap.add_argument("--priority", default="must-have", choices=SELECTABLE,',
     "declines work it was told not to do"),

    ("the threshold is off by one, so it excludes the tier it was asked for",
     "skills/breakdown/scripts/select-features.py",
     "    if tier in SELECTABLE and TIERS.index(tier) > TIERS.index(threshold):",
     "    if tier in SELECTABLE and TIERS.index(tier) >= TIERS.index(threshold):",
     "declines work it was told not to do"),

    # ------------------------------------------------------------------ item 15
    ("every gap kind refuses, so an overnight run halts on an open question",
     "skills/breakdown/scripts/select-features.py",
     'REFUSING_GAPS = {"specification"}',
     'REFUSING_GAPS = {"specification", "dependency", "decision", "evidence", "ownership"}',
     "declines work it was told not to do"),

    ("--include-tbd reaches the gap block, so the author's `incomplete` is overridable",
     "skills/breakdown/scripts/select-features.py",
     "    refusing = sorted(set(gaps) & REFUSING_GAPS)",
     "    refusing = [] if include_tbd else sorted(set(gaps) & REFUSING_GAPS)",
     "declines work it was told not to do"),

    # ---------------------------------------------------------- the report is the item
    ("only the first reason is reported, so fixing one of two appears to change nothing",
     "skills/breakdown/scripts/select-features.py",
     "    return out, warn",
     "    return out[:1], warn",
     "declines work it was told not to do"),

    ("the undefined must-haves stop being called out, which is the sentence item 15 exists for",
     "skills/breakdown/scripts/select-features.py",
     "    if undefined_musts:",
     "    if undefined_musts and False:",
     "declines work it was told not to do"),

    ("an empty selection reports success, so `nothing to build` looks like `built everything`",
     "skills/breakdown/scripts/select-features.py",
     '        print(f"\\nnothing to build: all {len(rows)} feature(s) were skipped", '
     'file=sys.stderr)\n        return 1',
     '        print(f"\\nnothing to build: all {len(rows)} feature(s) were skipped", '
     'file=sys.stderr)\n        return 0',
     "declines work it was told not to do"),

    ("/breakdown stops running the selector and goes back to building everything",
     "skills/breakdown/SKILL.md",
     "python {skill_dir}/scripts/select-features.py {prd_dir} --priority {threshold}",
     "# analyse every feature the index names",
     "declines work it was told not to do"),
]
