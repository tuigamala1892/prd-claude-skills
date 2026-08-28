"""Mutants for item 64 -- the generator is told where its verification commands run.

Two checks, and they guard two different kinds of thing.

The first is half prose and half MEASUREMENT: the brief's facts are parsed, then a worktree is
built by `create-worktree.sh` and git is asked whether they are still true. So this round breaks
it from both ends -- the brief stops saying a fact, the brief says a false one, and (the last
mutant) the *script* changes the branch name so the brief is left describing a toolchain that no
longer behaves that way. That last one is the reason the measured half exists at all.

The second guards prose in two files at once, and prose is the weakest thing to guard. Each rule
is therefore broken where it is written and where it is judged: removing it from the generator
must fail, and removing it from `review-criteria.md` must fail too. A rule stated in two places
needs two mutants or it has one check and a decoy.
"""

MUTANTS = [
    # ------------------------------------------------ the facts, in the generator's brief
    ("the section stating the execution context disappears",
     "skills/breakdown-generate-tasks/SKILL.md",
     "## Where your verification commands will run",
     "## Notes on the environment",
     "the generator is told where its verification commands will run"),

    ("`.git` goes back to being a directory, which is P42's concrete instance",
     "skills/breakdown-generate-tasks/SKILL.md",
     ".git      a FILE, the gitlink pointing back at the primary repository; never a directory",
     ".git      the repository's git directory, as in any checkout",
     "the generator is told where its verification commands will run"),

    ("the branch fact is dropped, so a step may compare against the base branch",
     "skills/breakdown-generate-tasks/SKILL.md",
     "branch    `worktree-{task-id}`, created with -b by create-worktree.sh; never the base branch\n",
     "",
     "the generator is told where its verification commands will run"),

    ("siblings become visible -- a fact the brief may state and the run will not honour",
     "skills/breakdown-generate-tasks/SKILL.md",
     "siblings  the other tasks of this layer run at the same time in worktrees of their own and are\n          NOT visible here; only layers already merged into the base branch are",
     "siblings  the other tasks of this layer are merged in before your steps run",
     "the generator is told where its verification commands will run"),

    # ------------------------------------------------ the preference, in both files
    ("the generator stops preferring the artefact to the environment",
     "skills/breakdown-generate-tasks/SKILL.md",
     "### Assert the artefact, not the environment",
     "### Some examples",
     "an environment-shaped verification step is a review question"),

    ("the preference is left with one worked example instead of a class",
     "skills/breakdown-generate-tasks/SKILL.md",
     "| `test -f src/store.py` | `test \"$(git branch --show-current)\" = main` | the file is what the task promised; the branch name is decided three skills away and is never `main` here |\n",
     "",
     "an environment-shaped verification step is a review question"),

    ("the one assertion a live run actually wrote is generalised out of the table",
     "skills/breakdown-generate-tasks/SKILL.md",
     "| `python -c \"import link_shelf\"` | `test -d .git` |",
     "| `python -c \"import link_shelf\"` | `git status --porcelain` |",
     "an environment-shaped verification step is a review question"),

    # Both of these delete the WHOLE bullet, continuation lines included. Cutting only the first
    # line leaves the indented remainder in place -- still saying `worktree` and `.git` -- and the
    # check reads the bullet, not the line, so a one-line cut would survive.
    ("review no longer asks whether a step holds inside a worktree",
     "skills/breakdown/references/review-criteria.md",
     "- [ ] **Every step holds inside a git worktree.** That is where `/execute` runs them: cwd is the\n"
     "      worktree root, `.git` is a *file* rather than a directory, the branch is\n"
     "      `worktree-{task-id}` and never the base branch, and the other tasks of this layer are not\n"
     "      merged in. A step asserting any of those otherwise fails a task that is correct — which is\n"
     "      **P42**, found by a live run on `Path('.git').is_dir()`.\n",
     "- [ ] Steps do not repeat one another\n",
     "an environment-shaped verification step is a review question"),

    ("review no longer prefers the artefact, so only the listed examples are catchable",
     "skills/breakdown/references/review-criteria.md",
     "- [ ] **Each step asserts the task's own artefact where one would do.** `import link_shelf` is a\n"
     "      claim about this task's output; `test -d .git` is a claim about somebody else's execution\n"
     "      model. Flag the second wherever the first is available, and where the task genuinely\n"
     "      depends on an environment property, the step must name what provides it.\n",
     "- [ ] Each step is worth its runtime\n",
     "an environment-shaped verification step is a review question"),

    ("the environment-shaped patterns lose the one a live run produced",
     "skills/breakdown/references/review-criteria.md",
     "\"test -d .git\"                          → test -f the file this task creates\n",
     "",
     "an environment-shaped verification step is a review question"),

    # ------------------------------------------------ and the measured half, from the other end
    #
    # EXPECTED ORPHAN: this one also fails `the merge is executed by one script, not described`,
    # and that is a true positive rather than a rename. `merge-task.sh:53` recomputes
    # `branch="worktree-${task_id}"` for itself, so the prefix is stated independently in two
    # scripts and documented in a third place by the generator's brief. Do not read the harness
    # warning as a stale check name.
    ("create-worktree.sh renames the branch, leaving the brief describing a toolchain that has moved",
     "skills/execute-batch/scripts/create-worktree.sh",
     'branch="worktree-${task_id}"',
     'branch="task-${task_id}"',
     "the generator is told where its verification commands will run"),
]
