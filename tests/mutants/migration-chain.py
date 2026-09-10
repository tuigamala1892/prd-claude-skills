"""The chain: the steps composed, which is the only shape a real corpus ever meets them in.

Every other migration mutant breaks a step. These break the COMPOSITION -- the thing that is
invisible to a suite of single steps, because each of those starts from an authored fixture and
stops after one move.

The three mutants take the check's three assertions one at a time. That is deliberate: the
check makes a strong claim (chain equals stepwise, byte for byte) and a scoped one (both land on
the fixture, modulo what the script may not write) and a guard on the scope itself (the scoped
comparison must still be looking at something). A mutant that trips all three tells you the
check fires; three that trip one each tell you which parts of it work.
"""

MIGRATE = "schema/scripts/migrate.py"
SCHEMAS = "tests/fixture/prd/SCHEMAS.json"

MUTANTS = [
    # 1. Composition: a chain takes only its LAST step, skipping everything between. Stepwise
    #    still walks them all, so the two legs end up holding different documents -- which is
    #    exactly what a corpus written against an old schema would silently get.
    ("a multi-version chain takes only its final step",
     MIGRATE,
     "    return [(v, rules_for(kind, v)) for v in VERSIONS[lo + 1:hi + 1]]",
     "    return [(v, rules_for(kind, v)) for v in VERSIONS[hi:hi + 1]]",
     "the whole chain composes"),

    # 2. Landing: R11/R12 resolve a document status toward the STRONGER claim. Both legs agree
    #    with each other -- so assertion one is satisfied and only the fixture comparison can
    #    see it. This is the mutant that proves the golden half is doing work rather than
    #    riding on the byte-for-byte half.
    ("a document status is resolved to `complete` rather than the weaker claim",
     MIGRATE,
     '    return DOC_STATUS.sub("<status>in-progress</status>", text, count=1)',
     '    return DOC_STATUS.sub("<status>complete</status>", text, count=1)',
     "the whole chain composes"),

    # 3. The scope guard. Widening judgement_elements until it covers the corpus makes the
    #    fixture comparison pass by having nothing left to compare -- a green light over an
    #    empty room, and the failure mode this repository keeps finding in its own checks.
    ("judgement_elements grows until the golden comparison compares nothing",
     SCHEMAS,
     '"judgement_elements": ["review", "notes", "data-model", "acceptance-criteria"]',
     '"judgement_elements": ["review", "notes", "data-model", "acceptance-criteria", "meta", '
     '"description", "feature", "features", "index", "what-next", "name", "slug", "summary"]',
     "the whole chain composes"),
]
