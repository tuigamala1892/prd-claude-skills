"""Mutants for item 86 -- `PROJECT.md` fits the prompt it is about to be sent in (P69).

Nine mutants against one check. Six break the SCRIPT, two break a CALLER or the registry row,
and one is the negative control that the other eight cannot supply.

Three are worth naming in advance, because each leaves the check's most obvious assertion true:

  - **the refusal stops naming the size.** It still exits 1, still refuses, still prints a
    sentence about being too large. What it stops doing is telling an author *by how much* --
    which is the difference between a file to split and a budget to raise. The assertion runs
    under `--quiet` for exactly this: the informational report carries the same number, so a
    check that read the default output would stay green while the refusal said nothing.
  - **a second 3.6.** The two size scripts still agree, because the copied value is the same
    value. Only the AST assertion can see it, and the day it stops being the same value is the
    day it matters. This is the drift `schema/core.md` exists to prevent, in one line.
  - **a caller that mentions instead of invoking.** `checks.md`'s forward check asserts the
    named caller CONTAINS the script's name, and item 69's asserts that no UNLISTED file runs
    it. This mutant satisfies both -- the file still names it, and it is still listed -- and the
    guard is simply not wired into one of the four reads.

AND ONE THAT EXISTS TO PROVE A CHECK IS NOT HOLLOW

`refuse everything` is the negative control. Every other mutant here makes the script accept
something it should refuse; without one that makes it refuse something it should accept, a
checker that exited 1 unconditionally would satisfy all seven.
"""

SCRIPT = "skills/breakdown/scripts/check-project-size.py"
CHECK = "PROJECT.md fits the prompt"

MUTANTS = [
    # ------------------------------------------------------------ the script
    ("the refusal exits 0, so the guard reports and nothing acts on it",
     SCRIPT,
     "        return 1\n",
     "        return 0\n",
     CHECK),

    ("the boundary is inclusive, so a file exactly at the budget is refused",
     SCRIPT,
     "    if total > budget:",
     "    if total >= budget:",
     CHECK),

    ("the refusal stops naming the size, so `too big` carries no number",
     SCRIPT,
     'REFUSED: PROJECT.md is {total:,} estimated tokens against a {budget:,}-token ',
     'REFUSED: PROJECT.md does not fit the {budget:,}-token ',
     CHECK),

    ("the divisor is copied rather than imported, and the copy is free to drift",
     SCRIPT,
     "           else sib.DEFAULT_CHARS_PER_TOKEN)",
     "           else 3.6)",
     CHECK),

    ("the budget is copied rather than imported, and its owner stops owning it",
     SCRIPT,
     "else sib.DEFAULT_BUDGET",
     "else 60000",
     CHECK),

    ("a project with no PROJECT.md reports a measurement, so absent reads as fits",
     SCRIPT,
     'print(f"no PROJECT.md at {path} -- nothing to measure")',
     'print(f"no PROJECT.md at {path} -- 0 estimated tokens")',
     CHECK),

    # ------------------------------------------------------------ the control
    ("it refuses everything, which satisfies every assertion about refusing",
     SCRIPT,
     "    if total > budget:",
     "    if total > -1:",
     CHECK),

    # ------------------------------------------------------------ the wiring
    ("a listed caller mentions the script instead of running it",
     "commands/crd.md",
     "     python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-project-size.py "
     "{project_path}",
     "     # the budget is the one check-project-size.py applies",
     CHECK),

    ("the row claims the assertion runs on the PRD path, where the file does not exist",
     "schema/checks.md",
     "`skills/breakdown/SKILL.md` | crd-only | A PRD has `check-prd-size.py`;",
     "`skills/breakdown/SKILL.md` | prd-only | A PRD has `check-prd-size.py`;",
     CHECK),
]
