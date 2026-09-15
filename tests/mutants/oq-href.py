"""Mutants for the open-questions pointer -- `check-references.py` never read the href.

prd-format.md permits `<open-questions href=>` and says OQ-NNN citations are validated either
way. The script only guessed at paths, and the template's own example was not one of them. The
three ways back to that are: the pointer is not read, the pointer loses to a guess, and a broken
pointer is quietly swapped for whatever the guess finds.
"""

CHECK = "an open-questions href in what-next.md names the register"

MUTANTS = [
    ("the href is never read, so the register is only ever guessed at",
     "skills/breakdown/scripts/check-references.py",
     "    href = None if args.questions else questions_href(prd_dir)\n",
     "    href = None\n",
     CHECK),

    ("discovery outranks the document, so the href only counts where no guess succeeds",
     "skills/breakdown/scripts/check-references.py",
     "    elif href:\n        q_path = href[1]\n    else:\n"
     "        q_path = discover_questions(prd_dir, adr_dir)",
     "    else:\n        q_path = discover_questions(prd_dir, adr_dir) or (href and href[1])",
     CHECK),

    ("a broken href falls back to a register it never named",
     "skills/breakdown/scripts/check-references.py",
     "    elif href:\n        q_path = href[1]\n",
     "    elif href and href[1] and os.path.isfile(href[1]):\n        q_path = href[1]\n",
     CHECK),
]
