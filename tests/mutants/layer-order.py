"""Mutants for item 74 -- a declared layer order is obeyed, not improved on.

The two fixtures came from the SAME declared graph and differ only in the behaviour under test,
so both directions have a real control: `inverted/` obeyed the order, `inverted-halted/` did not.
A checker that refuses everything passes any test fed only the second; one that refuses nothing
passes any test fed only the first.

The last mutant is the one this round exists for. `check-layer-order.py`'s refusal prints the
declared sequence and the emitted one, and the first version of the regression check asserted
that the word "declared" appeared in stderr -- which the refusal's own opening sentence already
satisfied. Two sites, so deleting the line changed nothing and the mutant passed. It now asserts
a layer that was DROPPED, which can only have come from the declared line.
"""

MUTANTS = [
    ("the subsequence test never fails, so a resequenced plan reads as obedient",
     "skills/breakdown/scripts/check-layer-order.py",
     "        if not any(d == e for d in it):\n            return False, e",
     "        if False:\n            return False, e",
     "declared layer order is obeyed"),

    ("the subsequence test always fails, so dropping an empty layer becomes a violation",
     "skills/breakdown/scripts/check-layer-order.py",
     "    it = iter(declared)",
     "    it = iter([])",
     "declared layer order is obeyed"),

    ("a project that declared no graph is judged against one anyway",
     "skills/breakdown/scripts/check-layer-order.py",
     "    if arch is None or not declared_order(arch):",
     "    if False:",
     "declared layer order is obeyed"),

    ("the refusal stops printing the declared sequence",
     "skills/breakdown/scripts/check-layer-order.py",
     "    print(f\"  declared  {' -> '.join(declared)}\", file=sys.stderr)",
     "    pass",
     "declared layer order is obeyed"),

    ("equality replaces subsequence, so item 31's dropped layers become violations",
     "skills/breakdown/scripts/check-layer-order.py",
     "    ok, offender = is_subsequence(emitted, declared)",
     "    ok, offender = (emitted == declared), (emitted[0] if emitted else None)",
     "declared layer order is obeyed"),

    # The fixture rather than the script: a positive control that stops being positive is a
    # check with nothing left to detect, and it would pass in silence.
    #
    # THE SUBSTITUTION MATTERS, and the first attempt at this mutant got it wrong. Renaming the
    # layer to `1-foundation` left the fixture ILLEGAL by a different route -- that name is in no
    # declared graph, so the check went on refusing and the mutant could not be caught. It read
    # as a survivor and was a badly built mutant. `1-integration` IS declared, so the emitted
    # list becomes 0-setup, 1-integration, 3-backend -- a legal subsequence of 0,1,2,3,4 -- and
    # the positive control genuinely stops being positive.
    ("the positive control is repaired, so nothing is out of sequence any more",
     "tests/fixture/layering/inverted-halted/layer_plan.json",
     '"id": "4-foundation"',
     '"id": "1-integration"',
     "declared layer order is obeyed"),
]
