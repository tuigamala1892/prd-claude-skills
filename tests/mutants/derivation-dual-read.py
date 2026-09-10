"""Core section 3's accepted-on-read rule, in the reader that DERIVES from it.

`build-what-next.py` matched only the new spelling and defaulted a miss to `tbd`, so a corpus
written before item 45 derived as entirely unfinished -- a plausible answer, written into the
file as derived truth, in a run that exited 0. A reader that failed loudly would have been a
nuisance; this one was a liar.

The sweep that followed found the other four readers of a renamed element already correct, so
this is one reader rather than a pattern. `check-artefacts.py` is the model: it reads both and
says which it found.

The third mutant is the one worth having. Making a regex accept two spellings shifts every
capture group along by one, and the caller reading the old index gets the TAG NAME instead of
the value -- so the counts come back keyed on `definition` rather than `defined`. That is not a
crash and not an empty result; it is a different wrong answer reached from the correct fix, and
it is the mistake this change was one line away from shipping.
"""

BUILDER = "schema/scripts/build-what-next.py"

MUTANTS = [
    ("the derivation reads only the new spelling again",
     BUILDER,
     r'DEFINITION = re.compile(r"<(definition|status)>\s*([a-z-]+)\s*</\1>")',
     r'DEFINITION = re.compile(r"<(definition)>\s*([a-z-]+)\s*</\1>")',
     "the derivation reads a feature written before the rename"),

    # The default is half the defect: without it the miss would be visible instead of plausible.
    ("an unreadable definition silently becomes `tbd`",
     BUILDER,
     '        definition = definition.group(2) if definition else "tbd"',
     '        definition = "tbd"',
     "the derivation reads a feature written before the rename"),

    # The group index, which is the trap the fix itself sets.
    ("the caller keeps reading group 1, which is now the tag name",
     BUILDER,
     "        definition = definition.group(2) if definition else \"tbd\"",
     "        definition = definition.group(1) if definition else \"tbd\"",
     "the derivation reads a feature written before the rename"),
]
