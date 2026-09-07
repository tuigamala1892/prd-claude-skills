"""Mutants for item 63 -- a task file is not editable by the run it judges.

Three checks, and they are guarded three different ways, so the mutants are too.

The first check RUNS the script, so its mutants break the script: the stop stops being a stop,
the diff stops being a diff, the record stops being written, and -- the one worth keeping -- the
record is written into `ledger.jsonl` instead of beside it, where `ledger-status.sh` would read an
entry with no commit as a task whose commit had vanished. A guard against a false green that
manufactures a false red is not an improvement.

The second and third guard wiring and prose. The wiring mutants include one that is not a
deletion: `/execute-layer` re-*records* instead of verifying, which is the plausible wrong version
of this feature -- it blesses the edit and reports success.
"""

MUTANTS = [
    # ------------------------------------------------------------------ the script
    ("an edited task file stops being a stop",
     "skills/execute/scripts/task-integrity.py",
     "          file=sys.stderr)\n    return 1",
     "          file=sys.stderr)\n    return 0",
     "a task file edited mid-run is a stop with a diff"),

    ("nothing recorded reports as nothing changed",
     "skills/execute/scripts/task-integrity.py",
     '        print("Run `task-integrity.py record` before dispatching any task.", file=sys.stderr)\n        return 2',
     '        print("Run `task-integrity.py record` before dispatching any task.", file=sys.stderr)\n        return 0',
     "a task file edited mid-run is a stop with a diff"),

    ("the diff becomes a summary of itself",
     "skills/execute/scripts/task-integrity.py",
     '        print(diff, end="")',
     '        print(f"{rel} was modified")',
     "a task file edited mid-run is a stop with a diff"),

    ("the edit is reported and never recorded",
     "skills/execute/scripts/task-integrity.py",
     '    with io.open(edits, "a", encoding="utf-8", newline="\\n") as f:\n'
     "        for line in lines:\n"
     '            f.write(json.dumps(line) + "\\n")',
     "    pass",
     "a task file edited mid-run is a stop with a diff"),

    ("the edit record goes into the ledger, where an entry with no commit reads as a lost task",
     "skills/execute/scripts/task-integrity.py",
     '    edits = os.path.join(run_dir(args.project_path, args.slug), "task-edits.jsonl")',
     '    edits = os.path.join(run_dir(args.project_path, args.slug), "ledger.jsonl")',
     "a task file edited mid-run is a stop with a diff"),

    ("a task file that appeared mid-run stops counting as an edit",
     "skills/execute/scripts/task-integrity.py",
     "    for rel in sorted(present - set(recorded)):\n        added.append(rel)",
     "    pass",
     "a task file edited mid-run is a stop with a diff"),

    # ------------------------------------------------------------------ the wiring
    ("/execute stops taking the snapshot, so there is nothing to compare against",
     "skills/execute/SKILL.md",
     "python {skill_dir}/scripts/task-integrity.py record {tasks_path} {project_path} {prd_slug}",
     "ls {tasks_path}",
     "the guard runs before dispatch and again before anything merges"),

    ("/execute stops re-checking before it reports",
     "skills/execute/SKILL.md",
     "python {skill_dir}/scripts/task-integrity.py verify {tasks_path} {project_path} {prd_slug}\n```\n\n- **Exit 0**",
     "python {skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug}\n```\n\n- **Exit 0**",
     "the guard runs before dispatch and again before anything merges"),

    ("the layer re-RECORDS instead of verifying, blessing the edit and reporting success",
     "skills/execute-layer/SKILL.md",
     "python {skill_dir}/../execute/scripts/task-integrity.py verify {tasks_path} {project_path} {prd_slug}",
     "python {skill_dir}/../execute/scripts/task-integrity.py record {tasks_path} {project_path} {prd_slug}",
     "the guard runs before dispatch and again before anything merges"),

    ("an edited task file is folded back into `abandoned`, and the operator debugs the code",
     "skills/execute/SKILL.md",
     '#### `stop_reason_kind: "task_edited"` — a task file changed after dispatch',
     "#### A task file changed after dispatch",
     "the guard runs before dispatch and again before anything merges"),

    # The pair below breaks the OTHER half of the two assertions that survived round 1. A check
    # that only forbids a bad state passes on a file that has lost the good state too, so each
    # of those rules is now broken twice: once by removing the report, once by removing the row
    # and the step that make the check non-vacuous.
    ("the stop-kind table stops naming the run's own edits",
     "skills/execute/SKILL.md",
     "| `task_edited` | a task file changed after dispatch | **this run's** |\n",
     "",
     "the guard runs before dispatch and again before anything merges"),

    ("the batch's step for a blocked result stops being a step",
     "skills/execute-batch/SKILL.md",
     "### Step 7b: A `blocked` Result Is Not a Failure and Never a Retry",
     "**A note on blocked results.**",
     "an unsatisfiable task is reported, and reporting it has somewhere to go"),

    # ------------------------------------------------------------------ the escalation path
    ("the implementer may edit the task file again",
     "agents/task-implementer.md",
     "## The Task File Is Read-Only\n\n**You may not modify the task file. Not one character, and not for any reason.**",
     "## The Task File\n\n**Read it before you start, and re-read it before you commit.**",
     "an unsatisfiable task is reported, and reporting it has somewhere to go"),

    ("`blocked` loses the half that says what the step contradicts",
     "agents/task-implementer.md",
     '    "contradicts": "requirement 4 — \\"the README must carry a TODO section listing deferred work\\"",\n',
     "",
     "an unsatisfiable task is reported, and reporting it has somewhere to go"),

    ("the blocked result becomes an ordinary failure, worth five retries of an impossible task",
     "agents/task-implementer.md",
     '  "status": "blocked",',
     '  "status": "failed",',
     "an unsatisfiable task is reported, and reporting it has somewhere to go"),

    ("the batch may retry a task no implementation can satisfy",
     "skills/execute-batch/SKILL.md",
     "**Do not run the classifier on it, do not queue a retry, and do not increment the attempt.**",
     "Treat it like any other failure of the implementation.",
     "an unsatisfiable task is reported, and reporting it has somewhere to go"),

    ("the verifier loses its vocabulary for a step no implementation can pass",
     "skills/execute-verify/SKILL.md",
     '  "kind": "task-defect",',
     '  "kind": "verification",',
     "an unsatisfiable task is reported, and reporting it has somewhere to go"),
]
