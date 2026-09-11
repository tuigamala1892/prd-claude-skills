"""`mutate.py`'s own third guard, on the path where it stopped being one.

The restore runs in a `finally` and verifies itself by hash. What it could not survive was the
copy ITSELF failing -- an exception raised inside that `finally` ends the run before the
verification, before the remaining files are put back, and before the report that would name
what is broken.

It fired once, on a run whose mutation was a ceiling constant the suite reads. The check left
weakened went on passing, so the tree held a green suite and an unrestored file, and the only
evidence was `MM` in `git status`. That is the exact false green this harness exists to prevent,
arriving through the harness.

These mutants are unusual in breaking the harness rather than the toolchain. That is the only
way to hold it: the thing under test is the machinery the other mutants are run by.
"""

MUTATE = "tests/mutate.py"

MUTANTS = [
    # The regression itself: narrow the except so an OSError escapes again, exactly as it did.
    # Kept syntactically valid on purpose -- a mutant that breaks the parse would be caught by
    # the import blowing up, which says nothing about whether the guard works.
    ("a failed restore raises out of the finally instead of reporting",
     MUTATE,
     "        except OSError as e:",
     "        except ZeroDivisionError as e:",
     "a failed restore is reported, not raised"),

    # The hash half of the guard: a restore that produced the wrong bytes is waved through.
    ("a restore is trusted rather than verified by hash",
     MUTATE,
     "        return None if sha(path) == before else \"restored, but the bytes differ from before\"",
     "        return None",
     "a failed restore is reported, not raised"),

    # And the caller: a run that cannot put a file back must stop, not mutate on top of it.
    ("the run carries on after a file it could not restore",
     MUTATE,
     "            if aborted:",
     "            if False:",
     "a failed restore is reported, not raised"),
]
