"""Mutants for the two mechanisms added after the first 5d round -- item 6's significance
screen and item 34's criterion-priority spread.

A second round rather than an amended first one, deliberately. The first round's result is a
measurement of seventeen mutants against the code as it stood; editing that file and re-running
would have replaced the record rather than extended it, and the two are not the same evidence.

The reach mutant is the one worth having. It does not disable the screen -- it makes it count
`index.md` and `what-next.md`, which name every feature by construction, so every feature clears
the threshold and the report goes from a shortlist to a list of everything. A check asserting only
that a candidate was reported would pass it.
"""

MUTANTS = [
    ("the cross-cutting threshold is raised out of reach, so the screen never fires",
     "skills/breakdown/scripts/check-references.py",
     "CROSS_CUTTING_AT = 3",
     "CROSS_CUTTING_AT = 99",
     "an unflagged feature that looks significant is a candidate"),

    ("reach counts index.md and what-next.md, which name every feature by construction",
     "skills/breakdown/scripts/check-references.py",
     '                        and os.path.basename(other) not in ("index.md", "what-next.md")\n',
     "",
     "an unflagged feature that looks significant is a candidate"),

    ("a feature that already declares the flag is screened again",
     "skills/breakdown/scripts/check-references.py",
     "            if SIGNIFICANT.search(text):\n                continue",
     "            if SIGNIFICANT.search(text) and False:\n                continue",
     "an unflagged feature that looks significant is a candidate"),

    ("a candidate starts failing the run under --strict, turning a heuristic into a gate",
     "skills/breakdown/scripts/check-references.py",
     "    if errors:\n        return 1\n    return 1 if (args.strict and warnings) else 0",
     "    if errors:\n        return 1\n    return 1 if (args.strict and (warnings or candidates)) else 0",
     "an unflagged feature that looks significant is a candidate"),

    ("the criterion-priority spread stops being reported",
     "skills/breakdown/scripts/check-definition.py",
     '          f"{len(edges)} one-way edges to triage; criterion priority: {spread}")',
     '          f"{len(edges)} one-way edges to triage")',
     "each mechanical test of the well-defined bar fires"),

    ("the spread is computed once and never updated, so it stops tracking the file",
     "skills/breakdown/scripts/check-definition.py",
     '            tally[c.get("priority") or "unset"] += 1',
     '            tally["P0"] += 1',
     "each mechanical test of the well-defined bar fires"),
]
