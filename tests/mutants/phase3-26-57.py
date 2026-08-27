MUTANTS = [
    # ---------------------------------------------------------------- item 26
    ("the greenfield row is deleted, so PROJECT.md is never created",
     "skills/execute/SKILL.md",
     "| No `PROJECT.md`, run came from a **PRD** | **create** it — from `architecture.md` when "
     "there is one, plus the task exports |\n",
     "",
     "greenfield ends with an architecture record"),

    ("the greenfield row skips instead of creating",
     "skills/execute/SKILL.md",
     "| No `PROJECT.md`, run came from a **PRD** | **create** it",
     "| No `PROJECT.md`, run came from a **PRD** | skip it",
     "greenfield ends with an architecture record"),

    ("the update path is lost while adding the create path",
     "skills/execute/SKILL.md",
     "| `PROJECT.md` exists | **update** it, exactly as before |",
     "| `PROJECT.md` exists | leave it alone |",
     "greenfield ends with an architecture record"),

    ("seeding starts copying the prescriptive half into the descriptive file",
     "agents/project-context-finalizer.md",
     "**Do not copy `<rules>` or `<principles>`.**",
     "**Copy `<rules>` and `<principles>` across too.**",
     "greenfield ends with an architecture record"),

    ("architecture.md's empty registries win over what was actually built",
     "agents/project-context-finalizer.md",
     "**the export wins**",
     "**the seeded entry wins**",
     "greenfield ends with an architecture record"),

    ("the finalizer forgets that a created file must satisfy the guard",
     "agents/project-context-finalizer.md",
     "**A created file must satisfy `check-project-md.py`**: `<meta>`, `<features>`, and "
     "**at least one\nregistry**.",
     "**A created file should be complete.**",
     "greenfield ends with an architecture record"),

    # ---------------------------------------------------------------- item 57
    ("affected-contracts loses every kind but api and schema",
     "skills/crd/references/crd-format.md",
     '    <contract kind="event"   ref="OrderPlaced@v2">New optional field; consumers '
     'unaffected</contract>\n'
     '    <contract kind="command" ref="deploy --dry-run">New flag</contract>\n',
     "",
     "impact analysis reports contracts"),

    ("a contract loses its kind",
     "skills/crd/references/crd-format.md",
     '<contract kind="api"     ref="PUT /api/settings">',
     '<contract ref="PUT /api/settings">',
     "impact analysis reports contracts"),

    ("the producer stops emitting contracts",
     "skills/crd-impact-analysis/SKILL.md",
     "  <affected-contracts>",
     "  <affected-apis-only>",
     "impact analysis reports contracts"),

    ("the analyzer agent stops emitting contracts",
     "agents/crd-impact-analyzer.md",
     "  <affected-contracts>",
     "  <affected-apis-only>",
     "impact analysis reports contracts"),

    ("affected-apis is deleted rather than deprecated, breaking every existing CRD",
     "skills/crd/references/crd-format.md",
     "| `affected-apis` | No | **Deprecated.** Accepted on read; equivalent to "
     "`affected-contracts` with `kind=\"api\"` |\n",
     "",
     "impact analysis reports contracts"),

    ("a missing registry produces an empty impact instead of a refusal",
     "skills/crd-impact-analysis/SKILL.md",
     "do not report an empty impact as though you had looked and found nothing.",
     "report what you can find.",
     "impact analysis reports contracts"),

    ("the layer derivation goes back to reading the deprecated elements",
     "skills/breakdown/SKILL.md",
     'CRD `<contract kind="schema">` |',
     'CRD `<affected-schemas>` |',
     "impact analysis reports contracts"),
]
