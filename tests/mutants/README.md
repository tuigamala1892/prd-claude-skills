# Mutant specifications

One file per item or item group, each defining `MUTANTS` for `tests/mutate.py`:

```bash
python tests/mutate.py tests/mutants/phase3-56.py
```

**These are kept, not thrown away.** A mutant spec records *what somebody could plausibly break*
about an item, which is the part of a regression check that is otherwise invisible: the check
says what must be true, and the mutants say what going wrong looks like. Re-running an old spec
after a refactor is the cheapest way to find out whether the checks still work or merely still
pass.

## Writing one

```python
MUTANTS = [
    ("a short label for the report",     # what this mutant does
     "skills/breakdown/SKILL.md",        # repo-relative path
     "the exact text to find",           # must match exactly, once
     "what to replace it with",
     "substring of the check name that MUST fail"),
]
```

**Aim mutants at plausible tidying, not obvious vandalism.** The two most valuable in Phase 3
were both changes a careful person might make on purpose: copying `<rules>` into `PROJECT.md`
(looks like completeness, destroys the prescriptive/descriptive split) and deleting
`<affected-apis>` (looks tidy, breaks every CRD already written).

**Never write the mutant file with a shell heredoc.** `\b` in a regex becomes a literal `0x08`
byte and the file looks correct in `grep`; that cost a day in item 21 and recurred three times in
Phase 3. Write it with an editor or a Python script.

## Phase 3

| Spec | Item | Result |
|---|---|---|
| `phase3-25-28-37.py` | the artefact, its guard, its readers | 13/13 |
| `phase3-51.py` | the Design phase in `/prd` | 10/10 |
| `phase3-31.py` | the derived layer set | 9/9 |
| `phase3-56.py` | the `<banned>` / `<task-limits>` enforcers | 13/13 |
| `phase3-26-57.py` | greenfield seed, contracts | 13/13 |

Each figure is the round that passed; the rounds before it are in
`docs/skills/plugin-2.0-progress.md`, and they are the interesting ones — **five of the first ten
checks caught nothing while the suite was green.**
