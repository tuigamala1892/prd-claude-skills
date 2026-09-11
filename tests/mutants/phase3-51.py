MUTANTS = [
    ("the Design phase is removed entirely",
     "commands/prd.md",
     "### Phase 4: Design (Architecture)",
     "### Phase 4: Scope Review",
     "architecture.md has a producer"),

    ("Design moves after Dependencies, inverting the causality",
     "commands/prd.md",
     "### Phase 4: Design (Architecture)",
     "### Phase 10: Design (Architecture)",
     "architecture.md has a producer"),

    ("the Design phase stops validating what it wrote",
     "commands/prd.md",
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-architecture.py "
     "{project_root}",
     "# review the file by eye",
     "architecture.md has a producer"),

    ("the script is invoked by a bare relative path",
     "commands/prd.md",
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-architecture.py "
     "{project_root}",
     "python skills/breakdown/scripts/check-architecture.py {project_root}",
     "architecture.md has a producer"),

    ("taking the default now writes a stub rule file",
     "commands/prd.md",
     "**Write no `architecture.md`.**",
     "**Write a minimal `architecture.md`.**",
     "architecture.md has a producer"),

    ('declining the phase is no longer recorded',
     'commands/prd.md',
     '**But record that the phase ran**, in `what-next.md` — the `<step kind= status=>` shape defined',
     '**Move on.**',
     'architecture.md has a producer'),

    ("the blank-page interview returns for a repo that describes itself",
     "commands/prd.md",
     "the question becomes **follow / extend / override**",
     "ask the architecture questions",
     "architecture.md has a producer"),

    ("the producer stops citing the schema it writes against",
     "commands/prd.md",
     "[`architecture-format.md`](../skills/breakdown/references/architecture-format.md)",
     "the architecture format",
     "architecture.md has a producer"),

    ("a reader stops reading the file the producer now writes",
     "skills/breakdown-analyze-prd/SKILL.md",
     "## `architecture.md`, when the caller hands you one",
     "## Project rules, when the caller hands you some",
     "architecture.md has a producer"),

    ("the phase sequence acquires a duplicate number",
     "commands/prd.md",
     "### Phase 5: Dependencies",
     "### Phase 4: Dependencies",
     "architecture.md has a producer"),
]
