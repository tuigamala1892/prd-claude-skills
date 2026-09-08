"""Mutants for item 73 -- no task may depend on an interface a later layer exports.

The check has two controls and both must be live. A checker that refuses everything passes any
test fed only the bad arm; a checker that refuses nothing passes any test fed only the good one.
So the mutants break it in BOTH directions: one stops it seeing the 16 real violations, one makes
it invent violations in a task set that is sound.

That second one is not hypothetical. The first version of this metric counted a dependency on
`python`, `pip` or `sqlite3` -- external libraries declared as interfaces -- as an unmet
contract, and reported nine findings against the default arm. The mutant reproduces it exactly.
"""

MUTANTS = [
    ("the rank comparison never fires, so the inverted arm reads as sound",
     "skills/breakdown/scripts/check-layering.py",
     '            if src and src["rank"] > t["rank"]:',
     '            if src and False:',
     "no task depends on a layer that runs after"),

    ("an external library counts as an unmet contract, which is the nine-false-positives defect",
     "skills/breakdown/scripts/check-layering.py",
     '            if src and src["rank"] > t["rank"]:',
     '            if src is None or src["rank"] > t["rank"]:\n                src = src or t',
     "no task depends on a layer that runs after"),

    ("order is taken from directory names, so a layer id is treated as a rank",
     "skills/breakdown/scripts/check-layering.py",
     '            if ids:\n                return ids, "layer_plan.json"',
     '            if False:\n                return ids, "layer_plan.json"',
     "no task depends on a layer that runs after"),

    ("the refusal stops naming the interface, so a count replaces a finding",
     "skills/breakdown/scripts/check-layering.py",
     '        print(f"  {v[\'task\']} ({v[\'layer\']}) needs {v[\'needs\']!r}, exported by "',
     '        print(f"  {v[\'task\']} ({v[\'layer\']}) needs something, exported by "',
     "no task depends on a layer that runs after"),

    ("--json prints the human summary too, so the object cannot be parsed",
     "skills/breakdown/scripts/check-layering.py",
     '        return 1 if bad else 0\n\n    if not args.quiet:',
     '        print("layering: done")\n        return 1 if bad else 0\n\n    if not args.quiet:',
     "no task depends on a layer that runs after"),

    # The fixture is the check's subject, and a positive control that drifts to zero is a check
    # with nothing to detect. This breaks the FIXTURE rather than the script.
    ("the positive control loses the layer that made it positive",
     "tests/fixture/layering/inverted/layer_plan.json",
     '"id": "4-foundation"',
     '"id": "0-foundation"',
     "no task depends on a layer that runs after"),
]
