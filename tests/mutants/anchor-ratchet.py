"""The anchor ratchet, held from both sides.

`MISSED` has two meanings: the check ran and caught nothing, or the mutant was never applied
because its anchor no longer resolves. Only the first is about the check, and `mutate.py`'s
output cannot tell them apart. Nothing validated anchors, and anchors are the one dependency on
somebody else's source text that this repository keeps.

The mutants here are unusual in that they break a MUTANT FILE rather than a source file. That is
deliberate and it is the only way to exercise this: the thing under test is the suite's own
grip on its tooling, so the tooling is what gets broken.

Both directions are exercised because a ratchet with one is a ceiling nobody lowers. Growing must
fail so the regression is caught -- it has happened three times now, once to the person who had
just written the docstring warning about it. Shrinking must fail too, so a repair brings the
ceiling down with it rather than leaving slack for the next change to spend silently.
"""

TARGET = "tests/mutants/phase4-41.py"
SUITE = "tests/test_toolchain.py"

MUTANTS = [
    # Grow: one more anchor stops resolving. This is exactly what happened three times in the
    # session that wrote this file, and what every green round failed to mention.
    ("an anchor in another mutant file stops resolving",
     TARGET,
     '    ("R1", "schema-2", "feature",',
     '    ("R1", "schema-2", "feature", "this no longer appears in migrate.py",',
     "every mutant anchor resolves"),

    # Shrink without lowering: the ceiling keeps slack the repair should have removed. Modelled
    # by raising the ceiling, which is the edit somebody actually makes when they want a red
    # suite to go green.
    #
    # THE NUMBER MATTERS, AND AN EARLIER ONE SURVIVED.
    #
    # This mutant's own anchor is the line it mutates, so applying it stops that anchor
    # resolving and adds exactly one to the count being tested. With a ceiling of 22 the
    # arithmetic cancelled perfectly -- stale 21 became 22, the ceiling became 22, and both
    # branches went quiet. The mutant perturbed the very quantity it was measuring, and 21 + 1
    # == 22 by coincidence rather than by design.
    #
    # Any ceiling the count cannot reach breaks the coincidence. At a ceiling of 0 the count
    # rises to 1 when this mutant lands, and 1 >= 9 is false, so the shrink branch fires.
    # Recorded rather than silently renumbered, because a mutant that cannot fail looks exactly
    # like a check that works.
    ("the ceiling is raised instead of the anchor being fixed",
     SUITE,
     "STALE_ANCHOR_CEILING = 0",
     "STALE_ANCHOR_CEILING = 9",
     "every mutant anchor resolves"),
]
