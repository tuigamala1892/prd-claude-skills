"""Second mutation round: the two reader checks that were decorative, plus their neighbours.

Every mutant here is one the PREVIOUS version of the check survived, or a new link in the
wiring chain that replaced it.
"""
MUTANTS = [
    # --- the two that got through last time, in their original form ------------------
    ("plan-layers: the declared-graph row deleted (survived round 1)",
     "skills/breakdown-plan-layers/SKILL.md",
     "| `architecture.json` with a non-empty `layer_blocks` | **that graph**, exactly as declared |",
     "| a declared graph | that graph, exactly as declared |",
     "the declared layer graph reaches plan-layers"),

    ("execute-batch: the branch removed, phrase left in a code block (survived round 1)",
     "skills/execute-batch/SKILL.md",
     "| has no `<test-requirements>` | omitted, and the line below substituted |",
     "| the project switched it off | omitted, and the line below substituted |",
     "`<testing default>` reaches execution as data"),

    # --- each link of the new wiring chain --------------------------------------------
    ("Phase 1 stops writing architecture.json",
     "skills/breakdown/SKILL.md",
     "python {skill_dir}/scripts/check-architecture.py {target_dir} --json > "
     "{tasks_dir}/architecture.json",
     "cat {target_dir}/architecture.md > {tasks_dir}/architecture.json",
     "the declared layer graph reaches plan-layers"),

    ("Phase 3 stops passing architecture.json to plan-layers",
     "skills/breakdown/SKILL.md",
     "**and, when it exists,\n`{tasks_dir}/architecture.json`**",
     "**and nothing else**",
     "the declared layer graph reaches plan-layers"),

    ("plan-layers stops naming the field that carries the graph",
     "skills/breakdown-plan-layers/SKILL.md",
     '"layer_blocks": [',
     '"the_graph": [',
     "the declared layer graph reaches plan-layers"),

    ("plan-layers stops reading the edges",
     "skills/breakdown-plan-layers/SKILL.md",
     '{"id": "1", "name": "contracts",   "depends_on": []},',
     '{"id": "1", "name": "contracts"},',
     "the declared layer graph reaches plan-layers"),

    ("the five tiers stop being labelled a default",
     "skills/breakdown-plan-layers/SKILL.md",
     "## Layer Definitions (the default graph)",
     "## Layer Definitions",
     "the declared layer graph reaches plan-layers"),

    ("the DAG-not-a-chain warning is dropped",
     "skills/breakdown-plan-layers/SKILL.md",
     "the result is a DAG, not a chain",
     "the result is an ordering",
     "the declared layer graph reaches plan-layers"),

    # --- the testing chain -------------------------------------------------------------
    ("execute-batch gains an architecture argument it was never given",
     "skills/execute-batch/SKILL.md",
     "| `--layer <name>` | Yes | Layer name (for status reporting) |",
     "| `--layer <name>` | Yes | Layer name (for status reporting) |\n"
     "| `--architecture <path>` | No | Path to architecture.md |",
     "`<testing default>` reaches execution as data"),

    ("execute-batch stops branching on the task's own section",
     "skills/execute-batch/SKILL.md",
     "| has no `<test-requirements>` | omitted, and the line below substituted |",
     "| a project that switched TDD off | omitted, and the line below substituted |",
     "`<testing default>` reaches execution as data"),

    ("review-criteria.md goes back to requiring tests unconditionally",
     "skills/breakdown/references/review-criteria.md",
     '  - **`test-requirements` is required unless the project declares '
     '`<testing default="none">`** in `architecture.md`. Read the declaration before failing a',
     '  - `test-requirements` is always required. Read the section before failing a',
     "`<testing default>` reaches execution as data"),

    ("task-format-spec.md goes back to an unconditional required section",
     "skills/breakdown/references/task-format-spec.md",
     "> **`<testing default=>` decides whether this section is required, and three components "
     "must\n> agree.**",
     "> **This section is always required.**",
     "`<testing default>` reaches execution as data"),

    ("tdd-workflow.md acquires the mandate, making a fourth enforcement site",
     "skills/execute-batch/references/tdd-workflow.md",
     "# TDD Workflow for Task Implementation",
     "# TDD Workflow\n\nTDD is mandatory.",
     "`<testing default>` reaches execution as data"),
]
