"""`--detect` counting its own listing, so Phase 1 quotes a number instead of estimating one.

The skill asks for five totals and nothing produced them. An agent told to state a number it was
never given counted a sixty-six line listing by eye and reported sixty features where there were
sixty-five -- with every other fact in its report correct, which is what makes an invented number
hard to see rather than obvious.

The mutants come in two kinds, and the second kind is the point. Removing the totals puts the
original defect back. The others leave a totals line in place and make it WRONG -- which is the
same defect one layer down, and the layer where nobody thinks to look, because a printed number
reads as a counted one.
"""

MIGRATE = "schema/scripts/migrate.py"

MUTANTS = [
    ("--detect stops printing totals, so Phase 1 counts by eye again",
     MIGRATE,
     '            total = sum(found.values())',
     '            total = None\n        if False:',
     "--detect counts its own listing"),

    # Wrong, not absent. A summary that disagrees with the listing beneath it is the invented
    # number with a producer's authority behind it.
    ("the total is counted from the wrong thing and drifts from the listing",
     MIGRATE,
     "            total = sum(found.values())",
     "            total = sum(found.values()) - len(skipped)",
     "--detect counts its own listing"),

    ("the escalated count is reported as zero however many there were",
     MIGRATE,
     "                  f\"{len(escalations)} escalated, \"",
     "                  f\"0 escalated, \"",
     "--detect counts its own listing"),

    # The per-schema breakdown is what `M already current` is read from, so losing one version
    # from it is losing the number Phase 1 leads with.
    ("the breakdown drops every version but the first",
     MIGRATE,
     'print("    " + "     ".join(f"{v}  {found[v]}"\n                                            for v in VERSIONS if v in found))',
     'print("    " + "     ".join(f"{v}  {found[v]}"\n                                            for v in VERSIONS[:1] if v in found))',
     "--detect counts its own listing"),

    # The path, which is what would have shown that the reported run scanned a wider tree than
    # the reader had in mind.
    ("the totals stop saying which tree was scanned",
     MIGRATE,
     'print(f"\\n{total} artefact{\'\' if total == 1 else \'s\'} under {args.path}, "',
     'print(f"\\n{total} artefact{\'\' if total == 1 else \'s\'} somewhere, "',
     "--detect counts its own listing"),
]
