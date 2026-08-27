MUTANTS = [
    ("integration goes back to being unconditional",
     "skills/breakdown/SKILL.md",
     "| `4-integration` | **more than one other tier is present**, or a requirement is "
     "explicitly cross-cutting | the count above |",
     "| `4-integration` | always, for wiring changes together | none |",
     "the layer set is derived from content"),

    ("the frontend derivation row is deleted",
     "skills/breakdown/SKILL.md",
     "| `3-frontend` | there are components, screens or routes | analysis "
     "`frontend_components`; CRD frontend paths in `<affected-files>` |\n",
     "",
     "the layer set is derived from content"),

    ("Phase 4 restores the unconditional five-layer list",
     "skills/breakdown/SKILL.md",
     "**Process exactly the layers `layer_plan.json` contains — never a list written here.**",
     "Determine layers to process based on input type:\n"
     "- **PRD Greenfield**: `[0-setup, 1-foundation, 2-backend, 3-frontend, 4-integration]`\n",
     "the layer set is derived from content"),

    ("Phase 4 stops taking its set from the plan",
     "skills/breakdown/SKILL.md",
     "**Process exactly the layers `layer_plan.json` contains",
     "**Process exactly the layers the analysis implies",
     "the layer set is derived from content"),

    ("the degenerate case is removed",
     "skills/breakdown/SKILL.md",
     "**When the derivation yields one layer holding one task, there is no plan to make. Run "
     "the\ntask.**",
     "Always build a layer plan.",
     "the layer set is derived from content"),

    ("dropped layers stop carrying a reason",
     "skills/breakdown-plan-layers/SKILL.md",
     '{"id": "3-frontend", "reason": "no components, screens or routes in this document"},\n'
     '    {"id": "4-integration", "reason": "only one other tier present -- nothing to wire"}',
     '"3-frontend",\n    "4-integration"',
     "the layer set is derived from content"),

    ("the plan can no longer express the degenerate case",
     "skills/breakdown-plan-layers/SKILL.md",
     '  "degenerate": false,\n',
     '',
     "the layer set is derived from content"),

    ("layers_dropped is documented but always empty",
     "skills/breakdown-plan-layers/SKILL.md",
     '  "layers_dropped": [\n'
     '    {"id": "3-frontend", "reason": "no components, screens or routes in this document"},\n'
     '    {"id": "4-integration", "reason": "only one other tier present -- nothing to wire"}\n'
     '  ],',
     '  "layers_dropped": [],',
     "the layer set is derived from content"),

    ("skip-layering and skip-batching are collapsed into one decision",
     "skills/breakdown/SKILL.md",
     "**Two decisions, and they are not the same one.** *Skip layering* when the work spans one "
     "tier.\n*Skip batching* when a layer holds few enough tasks.",
     "**One decision:** small changes skip the machinery.",
     "the layer set is derived from content"),
]
