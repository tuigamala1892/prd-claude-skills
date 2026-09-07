"""Mutants for item 66 -- /execute takes its layer set from the plan, not from its own prose.

The defect these guard is silent and total rather than partial: a hardcoded tier list against a
project that named its layers anything else finds nothing under any name, skips every layer, and
reports a COMPLETED RUN OF ZERO TASKS. So the round breaks the resolution in every direction it
could plausibly be broken -- order lost, unplanned layers dropped, the empty run reported as a
success, an unknown `--layer` iterated to nothing -- and then breaks the two halves of the prose.

The last pair is the one worth reading. Item 61's first attempt removed a rescinded instruction
and QUOTED it in the replacement as a historical note, and the check written for it failed
immediately and correctly: a model reads a quoted rule with the same weight as a stated one. The
same trap is available here in the form of a quoted list, so it is a mutant.
"""

MUTANTS = [
    # ------------------------------------------------------------------ the resolution
    ("the layers come back sorted rather than in the order the plan records them",
     "skills/execute/scripts/resolve-layers.py",
     "    ordered = [lid for lid in planned if counts.get(lid)]",
     "    ordered = sorted(lid for lid in counts if counts.get(lid))",
     "the layer set is the plan's, not a list in /execute's prose"),

    ("the plan is ignored, so dependency order becomes alphabetical order",
     "skills/execute/scripts/resolve-layers.py",
     "    planned = planned_layers(plan)",
     "    planned = []",
     "the layer set is the plan's, not a list in /execute's prose"),

    ("a layer with tasks and no plan entry is dropped, and its work never runs",
     "skills/execute/scripts/resolve-layers.py",
     "    ordered += unplanned",
     "    ordered += []",
     "the layer set is the plan's, not a list in /execute's prose"),

    ("a run with nothing to execute becomes a success",
     "skills/execute/scripts/resolve-layers.py",
     '              f"anything else.", file=sys.stderr)\n        return 1',
     '              f"anything else.", file=sys.stderr)\n        return 0',
     "the layer set is the plan's, not a list in /execute's prose"),

    ("--layer names anything it likes and the run iterates to a silent zero",
     "skills/execute/scripts/resolve-layers.py",
     "    if args.layer is not None and args.layer not in ordered:",
     "    if False:",
     "the layer set is the plan's, not a list in /execute's prose"),

    ("a planned layer with no tasks stops being reported",
     "skills/execute/scripts/resolve-layers.py",
     '    for lid in empty:\n        print(f"NOTE: `{lid}` is planned and has no tasks.',
     '    for lid in []:\n        print(f"NOTE: `{lid}` is planned and has no tasks.',
     "the layer set is the plan's, not a list in /execute's prose"),

    ("the plan/files disagreement is resolved silently instead of reported",
     "skills/execute/scripts/resolve-layers.py",
     '    for lid in unplanned:\n        print(f"NOTE: {counts[lid]} task(s) in `{lid}`',
     '    for lid in []:\n        print(f"NOTE: {counts[lid]} task(s) in `{lid}`',
     "the layer set is the plan's, not a list in /execute's prose"),

    # ------------------------------------------------------------------ the wiring and the prose
    ("/execute stops asking and reads the plan file itself",
     "skills/execute/SKILL.md",
     "python {skill_dir}/scripts/resolve-layers.py {tasks_path} [--layer {layer_filter}]",
     "cat {tasks_path}/layer_plan.json",
     "/execute asks for its layers and recites none"),

    ("the tier list comes back, as the loop it used to be",
     "skills/execute/SKILL.md",
     "layers = resolve_layers()      # the script's stdout, in order",
     'layers = ["0-setup", "1-foundation", "2-backend", "3-frontend", "4-integration"]',
     "/execute asks for its layers and recites none"),

    ("the tier list comes back as a historical note, which reads the same to a model",
     "skills/execute/SKILL.md",
     "This step used to iterate a hardcoded list of\nthe five shipped tier names",
     'This step used to iterate a hardcoded\n`["0-setup", "1-foundation", "2-backend", "3-frontend", "4-integration"]`',
     "/execute asks for its layers and recites none"),

    ("the Critical Rule asserting a fixed sequence comes back",
     "skills/execute/SKILL.md",
     "1. **Execute the layers the plan declares**, in the order it declares them, and skip only\n"
     "   what git says is already done. There is no fixed set and no fixed count: item 31 derives the\n"
     "   set from the document, item 28 lets a project name its own. `resolve-layers.py` answers this,\n"
     "   and a list of tier names written here is how P44 happened",
     "1. **Never skip layers**: Execute in order (0→1→2→3→4)",
     "/execute asks for its layers and recites none"),

    ("the rule keeps its ban and loses the true half, so the check forbids a sentence nobody writes",
     "skills/execute/SKILL.md",
     "1. **Execute the layers the plan declares**, in the order it declares them, and skip only",
     "1. **Execute layers**: run them, and skip only",
     "/execute asks for its layers and recites none"),
]
