"""Mutants for items 49 and 50 -- the scope/confidence cross-check, and parity as a table.

The three `check-scope.py` mutants are the ones that matter. Two of them break the check by
making it MORE talkative, which is the failure mode a naive test cannot see: a cross-check that
fires on every adjacent band still "works", it is just ignored within a week. The quiet case is
as much the subject as the loud one, so it is mutated like one.

The parity mutants attack the table's three ways of going stale: a probe that stops resolving, an
asymmetry that loses its reason, and a verdict that stops matching its own evidence.
"""

MUTANTS = [
    # ------------------------------------------------------------------ item 49
    ("the cross-check fires on adjacent bands, so nobody reads it",
     "skills/breakdown/scripts/check-scope.py",
     "    return abs(BANDS.index(predicted) - BANDS.index(observed)) > 1",
     "    return predicted != observed",
     "the analysis predicts size and certainty"),

    ("a disagreement becomes an exit code, so the check can block on a model's guess",
     "skills/breakdown/scripts/check-scope.py",
     "        for line in reports:\n            print(f\"  DISAGREES  {line}\")",
     "        for line in reports:\n            print(f\"  DISAGREES  {line}\")\n"
     "        if reports:\n            return 1",
     "the analysis predicts size and certainty"),

    ("tasks that cannot be attributed are passed over in silence",
     "skills/breakdown/scripts/check-scope.py",
     "    if signals and unattributed:",
     "    if False:",
     "the analysis predicts size and certainty"),

    ("the analyser stops emitting the two signals the reader was built for",
     "skills/breakdown-analyze-prd/SKILL.md",
     '  "feature_signals": [',
     '  "feature_omens": [',
     "the analysis predicts size and certainty"),

    ("/breakdown stops running the cross-check",
     "skills/breakdown/SKILL.md",
     "   python {skill_dir}/scripts/check-scope.py {tasks_dir}",
     "   # the operator can eyeball the task count against the analysis",
     "the analysis predicts size and certainty"),

    # ------------------------------------------------------------------ item 50
    ("a parity probe stops resolving, because the capability moved and the table did not",
     "schema/parity.md",
     "| Uncertainty recorded as gaps | `schema/prd-format.md :: <gaps>` |",
     "| Uncertainty recorded as gaps | `schema/prd-format.md :: <deferred-items>` |",
     "parity between the paths is a table with probes"),

    ("an asymmetry loses the reason that is the whole point of recording it",
     "schema/parity.md",
     "| crd-only | yes | A greenfield PRD has nothing to have an impact on. The counterpart is "
     "`architecture-format.md`, which is a *design*, not an assessment |",
     "| crd-only | yes | n/a |",
     "parity between the paths is a table with probes"),

    ("a prd-only verdict keeps its verdict while the CRD quietly grows the capability",
     "schema/parity.md",
     "| Deferral beyond a single document | `schema/prd-format.md :: what-next.md` | — |",
     "| Deferral beyond a single document | `schema/prd-format.md :: what-next.md` | "
     "`skills/crd/references/crd-format.md :: <gaps>` |",
     "parity between the paths is a table with probes"),
]
