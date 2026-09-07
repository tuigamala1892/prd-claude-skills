---
name: execute
description: Main entry point for hierarchical task execution. Orchestrates layer-by-layer implementation of PRD tasks with parallel worktree execution.
context: fork
model: claude-sonnet-5
user-invocable: true
---

# Task Execution Orchestrator

You are the main orchestrator for executing PRD implementation tasks. You coordinate layer-by-layer execution through a 4-level hierarchy:

```
/execute (you)
    └─► /execute-layer (per layer)
            └─► /execute-batch (per batch)
                    ├─► task-implementer agent (per task, parallel)
                    │       └─► /execute-verify (independent check)
                    └─► /execute-merge (sequential merges)
```

## Arguments

See `skills/execute/references/options.md` for complete documentation.

### Required

- `<tasks-path>`: Path to tasks directory (contains manifest.json, layer_plan.json)

### Common Options

```
--project-path <path>   Target project (optional if in manifest)
--worktree-dir <path>   Worktree directory (default: {project}/../.worktrees)
--max-parallel <N>      Max concurrent tasks (default: 3)
--base-branch <name>    Branch tasks branch from and merge into
                        (default: the repository's current HEAD)
--layer <name>          Execute specific layer only
--task <id>             Execute specific task only
--resume                Resume from the ledger (default when it has verified entries)
--reset                 Discard the progress record and start fresh.
                        Never deletes commits, branches or worktrees.
--dry-run               Show plan without executing
```

## Execution Flow

### Step 1: Parse Arguments

Extract all arguments from the prompt:

```python
tasks_path = required
project_path = optional  # from args or manifest
worktree_dir = optional  # default derived from project_path
max_parallel = 3
base_branch = None   # resolved in Step 3; never defaulted to "main"
layer_filter = None
task_filter = None
resume = False
reset = False
dry_run = False
```

### Step 2: Load Manifest

Read `manifest.json`:

```bash
cat {tasks_path}/manifest.json
```

Extract:
- `prd.slug`: PRD identifier
- `prd.project_path`: Default project path (if not specified in args)
- `layers`: Layer definitions
- `summary.total_tasks`: Total task count

**Project path resolution:**
1. Use `--project-path` if provided
2. Fall back to `manifest.prd.project_path` if exists
3. Error if neither available

**Then ask whether this toolchain can read this manifest at all** — before the preflight, because
a manifest whose shape this reader does not know is not a repository problem:

```bash
python {skill_dir}/scripts/check-compatibility.py {tasks_path}
```

- **Exit 0** — readable. `WARN` and `NOTE` lines may still print; report them and carry on.
- **Exit 1** — `REFUSED`, naming both versions. **Stop.** Re-run `/breakdown` with this toolchain,
  or use the toolchain that produced the manifest. Do not "read it anyway": a major shape change
  means fields have moved, and reading it regardless produces a plausible wrong answer.

**Two versions, and only one of them decides.** `schema_version` says *how to read* the file and
is what the refusal is based on; `toolchain_version` says *what produced* it and is reported and
never decided on. A patch release moves the second and not the first, so a provenance stamp cannot
answer a compatibility question — which is why the manifest carries both (**P28**).

Both stamps have been written since item 4.5 and **nothing read either of them** until this
check existed. A stamp nobody reads makes an artefact look checked while the incompatibility it
exists to catch goes through in silence.

### Step 3: Preflight

Run the bundled script. It performs **every** precondition and resolves the base branch:

```bash
base_branch=$(sh {skill_dir}/scripts/preflight.sh {tasks_path} {project_path} [{--base-branch if given}])
```

`{skill_dir}` is the base directory given at the top of this skill — the one ending in
`skills/execute`.

- **Exit 0**: stdout is the resolved base branch. Use it, and thread it to `/execute-layer`,
  `/execute-batch` and `/execute-merge`. It is never assumed to be `main`.
- **Non-zero**: stderr begins `REFUSED:` and explains why. **Stop.** Report the message
  verbatim and do nothing else — no plan, no dry run, no "this is expected because…".

What it refuses: a tasks path with no `manifest.json` or `layer_plan.json`; a target that does
not exist, is not a git repository, or is a *subdirectory* of one; a target containing
`docs/prd/` (a documentation tree); a target containing `.claude-plugin/plugin.json` (this
toolchain); a target inside the tasks directory; a base branch that does not exist; and a
detached HEAD, since there is then no branch to merge into; **and a task carrying
`<moscow>wont-have</moscow>`** (item 20).

**That last one is defence in depth, and it names the files.** A won't-have task reaching here
means item 13's selection gate at `/breakdown` did not run, or ran and was ignored. It is an
exit code rather than a note for the same reason as everything else in this script — item 4.13's
principle that a guard a model can reason past is not a guard.

**Why a script and not the checklist that used to be here.** These were prose, and prose is
weighed rather than obeyed. Pointed at a path containing `docs/prd/` — the exact case the prose
refused — `/execute` produced a full execution plan, and talked itself past the missing
repository as well:

> *"The project path is not yet a git repository — which is expected since this is a greenfield
> project where L0-002 initializes git."*

That is finding **F15**. Every sentence of it is reasonable; none of it was true; and no
rewording fixes a guard that can be reasoned with. An exit code cannot be reasoned with.

Note the script never creates anything — in particular it will not `git init` a target that
is not a repository. `/execute` does not create repositories.

### Step 3b: Record the Task Files, Before Anything Is Dispatched

**A task file is the acceptance criteria this run is judged against, and the run may not edit
it.** Neither you nor any agent you dispatch may modify, add or remove a file under
`{tasks_path}`. That is the rule; this is the guard that makes it more than a sentence:

```bash
python {skill_dir}/scripts/task-integrity.py record {tasks_path} {project_path} {prd_slug}
```

It snapshots every task file beside the ledger, in `{project_path}/.execute/{prd_slug}/`.
`/execute-layer` re-checks after every batch, before merging, and Step 9 re-checks before this
run reports anything at all.

**Why an exit code and not a paragraph.** The third live crossing met a Layer 0 task whose
`<verification>` block was unsatisfiable — one step asserted a substring absent that another
requirement mandated present. Its diagnosis was right, its fix was reasonable, and it **edited
the task file and carried on** to `14/14`. Nothing forbade it, and the ledger indexes commits, so
nothing recorded it either (**P41**). The run reported what it had done, in detail and unprompted
— which is the finding stated precisely: *honesty was the only thing standing between a rewritten
acceptance criterion and a green result.*

**What to do instead has a name and a stop kind**: `task_defect` in Step 8. An unsatisfiable
verification step is a `/breakdown` defect, and this run ends naming the task and the
contradiction rather than repairing it.

`--reset` discards this record with the rest of `{project_path}/.execute/{prd_slug}/`, which is
right: a fresh run re-records. A `--resume` re-records too, against the task files as they stand
now — so an operator who fixed a task between runs is not fighting the previous run's snapshot.

### Step 4: Handle State

**Always start by asking git what is already done**, before deciding anything:

```bash
sh {skill_dir}/scripts/ledger-status.sh {project_path} {prd_slug} {total_tasks}
```

`verified_tasks` is the authoritative list of completed work. It is derived from commits that
exist right now, not from anything the previous run claimed.

**Resuming is the default whenever the ledger has verified entries.** Do not prompt. An
unattended run — the overnight case this whole design exists for — has nobody to answer, and
resuming is safe precisely because it is verified against git: a ledger with nothing verified
simply starts from the beginning.

```python
status = ledger_status()

if reset:
    # Say what is being thrown away before throwing it away.
    print(f"--reset: discarding {status['verified']} verified task(s); "
          f"branches and commits in {project_path} are NOT deleted")
    rm -f {tasks_path}/execute-state.json
    rm -rf {project_path}/.execute/{prd_slug}
    skip = set()

elif status["verified"] > 0:
    print(f"[EXEC] Resuming: {status['verified']} task(s) already verified in git")
    skip = set(status["verified_tasks"])

else:
    skip = set()

# Then write the state file -- always from the script, never by hand:
#   python {skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug} \
#       --started-at {now}

```

Note what `--reset` does **not** do: it never deletes commits, branches or worktrees. It
discards the *record*, so the next run rebuilds it. Destroying work is the operator's call,
made with git, not a side effect of a flag.

**`missing` is not a resume point, it is a warning.** If it is non-empty, the repository has
been reset or rebased under the ledger — recorded commits no longer exist. Report it, resume
from `first_unverified`, and treat every task from that point on as outstanding regardless of
what the ledger says about them.

### Step 5: Dry Run (if requested)

If `--dry-run`:

```
Execution Plan: {prd_slug}
Project: {project_path}
Worktrees: {worktree_dir}

Layer 0-setup (4 tasks):
  Batch 1: L0-001 → L0-002 → L0-003 → L0-004 (sequential)

Layer 1-foundation (6 tasks):
  Batch 1: L1-001, L1-002, L1-006 (parallel, 3 tasks)
  Batch 2: L1-003 (depends on L1-002)
  Batch 3: L1-004, L1-005 (depends on L1-003)

Layer 2-backend (9 tasks):
  Batch 1: L2-001, L2-002, L2-003 (parallel)
  ...

Total: 48 tasks
Estimated batches: 15
Max parallelism: 3
```

**The layers listed are `resolve-layers.py`'s, not a list written here** — a dry run that shows
five tiers for a project with two is a plan of a run that will not happen. Run the script for this
output as well, and print its `NOTE:` lines: a planned layer with no tasks is exactly what an
operator wants to see *before* the run rather than after it.

Exit after dry run output.

### Step 6: Execute Layers

**The layers of this run are the ones `/breakdown` recorded, in the order it recorded them.**
Ask the script; do not write a list here:

```bash
python {skill_dir}/scripts/resolve-layers.py {tasks_path} [--layer {layer_filter}]
```

- **Exit 0** — stdout is the ordered layer list, one per line. Iterate exactly that. `NOTE:`
  lines on stderr name a layer planned with no tasks, or tasks under a layer the plan never
  declared; report them and carry on.
- **Exit 1** — `REFUSED`. Either no layer has any task, or `--layer` named one this run does not
  have. **Stop and report it verbatim.** A run with nothing to execute is not a completed run.
- **Exit 2** — `layer_plan.json` or `manifest.json` could not be read. Stop; the preflight should
  have caught it.

**Why a script, and why this is not cosmetic.** This step used to iterate a hardcoded list of
the five shipped tier names — the history is in the plan (P44) and is deliberately not repeated
here, because a model reads a quoted list with the same weight as a stated one (item 61's own
first attempt is why that sentence exists). Item 31 made the layer set derived from what the document puts work in, item 62 made the task schema admit any layer id,
and item 28 lets a project declare its own `<layers>` graph — instantiated per service, so a layer
is legitimately called `2-service-billing`. Against such a project this loop found no tasks under
any of its five names, skipped every layer, and **reported a completed run of zero tasks**
(**P44**). Nothing failed, because nothing ran.

`/breakdown` Phase 4 has said the true rule for some time — *"Process exactly the layers
`layer_plan.json` contains — never a list written here"*. This is the same rule at the other end
of the pipeline.

```python
layers = resolve_layers()      # the script's stdout, in order

for layer in layers:
    # `--layer` was validated by the script above: an unknown name is a refusal there, not a
    # loop that quietly matches nothing. This is only the filter.
    if layer_filter and layer != layer_filter:
        continue

    # Skip only if every task in the layer has a verified commit. The state file's own
    # "completed" flag is not evidence -- it once said 20/20 with one merge commit in git.
    layer_tasks = tasks_in(layer)
    if layer_tasks and all(t in skip for t in layer_tasks):
        print(f"[EXEC] Skipping {layer} ({len(layer_tasks)} task(s) already verified in git)")
        continue

    # Execute layer
    print(f"[EXEC] Starting {layer}")
    result = invoke_layer(layer)

    # Check for stop condition
    if result["should_stop"]:
        print(f"[EXEC] STOPPED: {result['stop_reason']}")
        update_state(status="stopped")
        report_final_status()
        return

    print(f"[EXEC] {layer} complete ({result['tasks_completed']}/{result['tasks_total']})")
```

### Step 7: Invoke Layer Agent

For each layer, call `/execute-layer`:

```
/execute-layer --tasks-path {tasks_path} --layer {layer} --project-path {project_path} --worktree-dir {worktree_dir} --max-parallel {max_parallel} --base-branch {base_branch} --prd-slug {prd_slug}
```

Wait for layer completion and parse `LAYER_RESULT`.

### Step 8: Handle Stop Condition

A layer returns `should_stop: true` for one of four reasons, and `stop_reason_kind` says
which. **Report them differently**, because they ask different things of the operator:

| Kind | What happened | Whose defect |
|---|---|---|
| `abandoned` | a task failed five times | the code, or the task |
| `usage_limit` | the window closed mid-run | nobody's |
| `task_defect` | a task cannot be satisfied as written | `/breakdown`'s |
| `task_edited` | a task file changed after dispatch | **this run's** |

In both cases: run `ledger-status.sh` first and take the completed count from it, then
regenerate the state file with `write-state.py`. A stop is exactly when a hand-maintained
count is most likely to be wrong and most likely to be believed.

#### `stop_reason_kind: "abandoned"` — a task failed five times

```
STOPPED: Task L2-006 abandoned after 5 attempts

Completed: 15/48 tasks
Abandoned: L2-006
Blocked: 32 tasks (dependencies not met)

Worktree preserved: {worktree_dir}/L2-006
Review errors and fix issues, then run:
  /execute {tasks_path} --resume
```

#### `stop_reason_kind: "usage_limit"` — the window closed

Nothing failed. The run ran out of allowance and stopped on purpose, at a task boundary, with
every completed task committed and recorded.

```
STOPPED: usage limit reached (resets at 17:30 UTC)

Completed: 11/18 tasks, last verified commit 3b6632d (L2-001)
Remaining: 7 tasks
Nothing failed -- the run stopped to avoid burning the allowance a resume will need.

Resume when the window reopens:
  /execute {tasks_path} --project-path {project_path} --resume
```

Rules for this message, all of them things that have gone wrong in reports before:

- **`resets at` is quoted from the error, never estimated.** The classifier prints a `reset:`
  line only when the API actually said one. If there is no such line, omit the clause — do
  not compute a plausible time.
- **Do not call the stopped task failed, and do not list it as abandoned.** It has no commit,
  so it is simply outstanding, and its attempt budget is untouched.
- **`status` is `stopped`, never `completed`.** `write-state.py` will not write `completed`
  while tasks remain; do not contradict it in the prose above it.

#### `stop_reason_kind: "task_defect"` — the task cannot be satisfied as written

An agent met a `<verification>` step that contradicts the task's own requirements, or asserts
something no requirement produces, and **stopped instead of repairing it**. That is the correct
behaviour and the report should say so plainly, because the alternative is the one that produced
P41.

```
STOPPED: L0-003 cannot be satisfied as written

Step:        Verify: `README.md` does not contain the string "TODO"
Contradicts: requirement 4 — "the README must carry a TODO section listing deferred work"
Reported by: task-implementer (attempt 1 of 5; the attempt does not count)

Completed: 6/18 tasks
Nothing was edited. This is a /breakdown defect, not an implementation failure.

Fix the task, then resume:
  /breakdown {prd_path} --layer 0-setup     # regenerate, or edit the task file yourself
  /execute {tasks_path} --resume
```

**Do not count it as a failed attempt, and do not call the task abandoned.** It failed no test;
it was never implementable as specified. And do not offer to fix the task here — the operator
editing a task file between runs is the supported path, this run doing it is the defect.

#### `stop_reason_kind: "task_edited"` — a task file changed after dispatch

The guard fired. `task-integrity.py` found a task file that is not the one this run was given,
and the diff is in `{project_path}/.execute/{prd_slug}/task-edits.jsonl`.

```
STOPPED: task file L0-003 changed after dispatch

  modified L0-003  0-setup/L0-003-readme.xml
  diff: .execute/{prd_slug}/task-edits/L0-003-1.diff

Completed: 6/18 tasks (merges of unedited tasks stand)
NOT merged: L0-003

Every result for an edited task is unsound: it was verified against criteria this run wrote.
Restore the task file from /breakdown, or accept the edit deliberately by re-running
/breakdown, then:
  /execute {tasks_path} --resume
```

**Report the diff, do not summarise it.** A summary of an edit to an acceptance criterion is a
second-hand account of the only evidence that matters. And do not restore the file yourself:
that is one more edit by the run, and it destroys the diff.

### Step 9: Reconcile State Against Git, Then Report

Before reporting anything, ask git what actually happened:

```bash
sh {skill_dir}/scripts/ledger-status.sh {project_path} {prd_slug} {total_tasks}
```

`{skill_dir}` is the base directory given at the top of this skill — the one ending in
`skills/execute`. It returns, for example:

```json
{"recorded":18,"verified":18,"missing":[],"first_unverified":null,"expected":18}
```

Then ask whether the task files are still the ones you were given:

```bash
python {skill_dir}/scripts/task-integrity.py verify {tasks_path} {project_path} {prd_slug}
```

- **Exit 0** — stdout says how many were checked. Carry that line into the report.
- **Exit 1** — report it as `task_edited` above, and **do not report the run as completed**,
  whatever the ledger says. A task verified against criteria this run rewrote is not verified.
- **Exit 2** — `NO RECORD`. Step 3b did not run, so nothing can be said either way. Say that,
  rather than reporting task files unchanged: an unmade check reported as a passing one is the
  false green this whole guard exists to prevent.

Then regenerate the state file from the same evidence, so the file and your report cannot
disagree:

```bash
python {skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug}
```

**Report the numbers it prints.** Do not report a count that you incremented, and do not
edit the file it writes.

**A run that executed no layer at all is never `completed`.** `resolve-layers.py` refuses
before the loop begins, so reaching the report with zero layers means the refusal was reasoned
past — say so, name `expected` from the manifest, and report `incomplete` (**P44**).

**`status` may only be `completed` when `verified == expected` and `missing` is empty.**
Otherwise it is `incomplete`, whatever else went right. Two separate conditions, because they
fail separately:

- `missing` non-empty means a recorded commit has vanished — the repository was reset or
  rebased. Name `first_unverified` as the point a resume restarts from.
- `verified < expected` means tasks were never done at all. Name which: the task ids in the
  manifest that have no ledger entry.

This is not pedantry. Run 7 verified 18 tasks against a manifest claiming 20 and still wrote
`status: completed` with `tasks_remaining: 2` — internally contradictory, and precisely the
shape of statement that invites an operator to build on work that does not exist. A run that
completed 18 of 20 is a useful outcome honestly reported.

If the shortfall is because the manifest counts tasks that have no task file, that is a
`/breakdown` defect (item 4.9) and worth saying so in the report — but it is still not a
completed run.

**Why this exists.** Run 6 genuinely succeeded and still recorded `tasks_completed: 23`
against `tasks_total: 18`, 19 entries in an 18-task `completed[]` list, and an invented
elapsed time. Every wrong figure was maintained by hand; the one correct figure — the merge
queue — was derived from what had actually been merged. So derive all of them.

On completion:

```
Execution Complete: {prd_slug}

Layers:
  0-setup:      4/4 completed
  1-foundation: 6/6 completed
  2-backend:    9/9 completed
  3-frontend:   13/13 completed
  4-integration: 12/12 completed

Total: 44/44 tasks completed
Verified: each task's own declared steps, in its worktree, before merge
Task files: 44 unchanged since dispatch (sha256)
Not run: the project's build or test suite -- that belongs to CI
Duration: 2h 15m
Retries: 3 (all succeeded)
```

**Those three lines are not boilerplate and must not be dropped.** "44/44 completed" is a claim
about merges, and every reader hears it as a claim about the build. The ledger records
`verified: task-steps` for exactly this reason — the narrower true thing rather than the wider
implied one. A task that merges green and breaks CI is otherwise indistinguishable from one that
did not, and the report is where that difference matters most.

The third line is the one P41 costs nothing to add. `44/44` is a claim about merges against
criteria, and until the guard existed nothing said the criteria were the ones `/breakdown` wrote.
Print the count `task-integrity.py` printed — not a claim of your own that they are unchanged.

Running the project's pipeline stays out of scope: `/execute` has no business owning it. Not
implying it ran is a different question, and this is the answer to it.

### Step 10: Finalize Context (Every Project)

**This used to run only where `PROJECT.md` already existed**, which no greenfield run can
satisfy — so a greenfield project ran the whole pipeline and ended with no architecture record
at all, and the first `/crd` against it then paid for a full `crd-investigate` to rediscover
architecture the PRD had already stated (**P17**). The toolchain had an architecture artefact
and greenfield was the only path that could not reach it.

```bash
test -f {project_path}/PROJECT.md   && echo UPDATE
test -f {project_path}/architecture.md && echo SEED-AVAILABLE
```

| State | Action |
|---|---|
| `PROJECT.md` exists | **update** it, exactly as before |
| No `PROJECT.md`, run came from a **PRD** | **create** it — from `architecture.md` when there is one, plus the task exports |
| No `PROJECT.md`, run came from a **CRD** | stop and say so. A CRD targets an existing project, and `/breakdown` already required a `PROJECT.md` to scope the change — reaching here without one means something removed it mid-run |

**Seeding is a copy, not a transform**, and that is why item 25 put the registries at the same
nesting level in both files. `<api-registry>`, `<schema-registry>` and any other `<*-registry>`
move across as subtrees; `<rules>` and `<principles>` **stay behind**, because they are
prescriptive and `PROJECT.md` is descriptive. What the project *must* be is not a record of what
it *is*.

**A seeded `PROJECT.md` still has to earn its registries from the code.** `architecture.md`'s
registries are written before any code exists and are usually empty; the task `<exports>` are
what actually populate them. Where the two disagree, **the exports win** — they describe what was
built, and this file's whole job downstream is to say what exists.

**Dispatch the finalizer agent for both the update and the create.** Do not do this work inline:

```
Task(
  subagent_type: "project-context-finalizer",
  run_in_background: false,
  description: "Update PROJECT.md from completed task exports",
  prompt: <the four inputs below>
)
```

The prompt must carry exactly what the agent's `## Input` section asks for, because a
dispatched agent reads its own definition and nothing else — naming a skill or a document
here would be inert text (**F20**):

```
Update PROJECT.md to reflect what was implemented.

Mode:                                 update | create
Project root (PROJECT.md lives here): {project_path}
Architecture file to seed from:       {project_path}/architecture.md, or "none"
Tasks directory:                      {tasks_path}
PRD or CRD slug:                      {prd_slug}
Completed task ids:                   {verified_tasks from ledger-status.sh}
```

**`Mode` is stated rather than inferred.** The agent has `Read` and could test for the file
itself, but then two components decide the same thing and can disagree — and the caller is the
one that already ran the test above.

Take the completed ids from the **ledger**, not from a running total — they are the tasks
whose commits exist, which is the only list that has ever been reliable.

**Then finish the job yourself, in this order.** The agent declares `tools: Read Write Glob`
and has no `Bash`, so it can edit `PROJECT.md` but can neither commit it nor read anything out
of git. That division is deliberate and matches the rest of the pipeline: the agent produces
content, the caller owns git.

**First, validate and stamp — both before the commit, not after:**

```bash
python {skill_dir}/scripts/check-project-md.py {project_path} --fix --stamp-hash
```

**A non-zero exit means do not commit.**

`--fix` escapes bare ampersands. On its first ever run the finalizer wrote
`?tag=python&status=archived` into a `<description>`; a bare `&` is not valid XML, so the
`<project-context>` block stopped parsing — silently breaking `crd-impact-analysis`, which
reads `<api-registry>` from it, and the finalizer itself on the next run.

`--stamp-hash` writes the real `git rev-parse HEAD` into `<last-context-hash>`, because the
agent cannot. Its template used to ask for `{current git HEAD}`, and with no `Bash` it wrote
the literal string **`current-HEAD`** — overwriting a valid hash, on the only CRD run that has
ever happened. Every consumer then breaks: `git diff current-HEAD..HEAD` is
`fatal: ambiguous argument`, and both update paths treat an unusable hash as "fall back to full
investigation", so every later update silently takes the most expensive route there is. Asking
a component for a value it has no way to compute is the F20 shape.

**Stamp before committing, and do not try to correct for the commit.** The field records the
commit whose *code* this context describes, which can never be the commit that carries the
context — PROJECT.md is written first and committed second. `HEAD` at stamp time is therefore
the right value rather than one short, and `--status` judges staleness by whether anything
other than `PROJECT.md` has changed since.

**Then commit**, and only if the agent actually changed something — it reports
`{"skipped": true, ...}` when there are no task exports to add, and an empty commit claims a
context update that never happened:

```bash
git -C {project_path} add PROJECT.md
git -C {project_path} commit -m "docs: Update PROJECT.md with features from {prd_slug}"
```

**Why an agent and not the six steps that used to be written out here.** The agent already
specified this job in 219 lines — idempotent handling of entries that already exist, file
tracking, skip conditions, quality checks — while this section carried a thinner summary of
the same thing. Two descriptions of one job, with nothing deciding which runs, is exactly the
shape of **F20**. Dispatching by `subagent_type` loads the agent definition by construction,
so there is only one description now and it is the better one.

**Note the update path has never run.** `PROJECT.md` was CRD-only and every §5.2 run has been
greenfield, so neither the old inline version nor this one has been exercised. Treat it as
specified-but-unproven until a CRD fixture exists.

### Step 11: Complete

Regenerate the state file one last time, so its `status` and `completed_at` reflect what git
actually holds rather than what the run believes:

```bash
python {skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug}
```

It sets `status: completed` only when every task in the manifest has a commit that exists and
nothing is missing or abandoned. If it reports `in_progress`, the run did not finish — say so
rather than overriding it.

Output final summary including context update if performed:

**Report the tier that was built, from `execute-state.json`'s `tiers` block** (item 19). Do not
count it yourself — nothing in that file is maintained by hand, and a summary counted by the
reporter is one that can disagree with the tasks it counts.

```
Execution Complete: {prd_slug}

Total: 44/44 tasks completed
Built: 9 must-have/P0, 5 should-have/P0, 3 could-have/P1  (4 unattributed: Layer 0)
Duration: 2h 15m

Context Update:
  - PROJECT.md updated at {project_path}/PROJECT.md
  - Features added: 3
  - Endpoints added: 5
  - Models added: 2
  - New context hash: {hash}
```

## State Initialization

There is no `init_state`. `execute-state.json` is written by exactly one thing:

```bash
python {skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug}     --started-at {run_start_iso8601}
```

Run it once at the start, after each merge (`/execute-merge` does this), and once at the end.
It derives every field from the ledger and git — totals, per-task status, per-layer progress,
the merge queue, what remains — and carries forward only the two things that genuinely cannot
be derived: which tasks were abandoned and which failed.

**No field in that file may be written or edited by hand.** Four runs produced four different
wrong shapes when it was assembled from instructions: 23 of 18 complete; 19 entries for 18
tasks; `completed` alongside 2 remaining; `completed` alongside 4 of 18 while git held 18
merges — plus, in run 8, a second copy written into the target repository. The script refuses
to write inside `{project_path}` and cannot count to 4 when git says 18.

`elapsed_seconds` no longer exists. It was a number nobody measured — run 6 recorded 4000 for
a run of 10476 seconds. Compute a duration at report time from `started_at` if one is wanted.

## Resume Behavior

Resume is driven by the ledger, verified against git — **never by `execute-state.json`**. The
state file is a convenience that cannot be checked; it once reported 20 of 20 tasks complete
when the repository held one merge commit, and a resume trusting it would have skipped
seventeen tasks that were never done. That is silent data loss, and worse than crashing.

On resume:

1. Run `ledger-status.sh`; take `verified_tasks` as the set of completed work
2. **Skip** any task in `verified_tasks` — its commit exists, so it is done
3. **Re-run** every other task, including any the state file calls `completed`
4. Retry `failed` tasks while `attempts < 5`; `abandoned` tasks stay abandoned until an
   operator intervenes
5. Reuse a preserved worktree when one exists for a task being retried, via
   `--worktree-path`; do not create a second one
6. If `missing` is non-empty, say so prominently — recorded commits have vanished, so the
   repository was reset or rebased since the last run

**Partial work from an interrupted task is preserved but never counted.** Its worktree and
branch stay for inspection, and the task re-runs from its last verified base. A task that was
half-done when the run stopped has no commit, therefore no ledger entry, therefore is
outstanding — which is exactly right.

The invariant worth remembering: **a task is done when a commit exists, and at no other
time.** Everything else in this section follows from it.

## Error Handling

### Missing Manifest

```
Error: manifest.json not found at {tasks_path}/manifest.json
Run /breakdown first to generate tasks.
```

### Missing Project

If project path doesn't exist and not greenfield:

```
Error: Project path does not exist: {project_path}
For greenfield projects, Layer 0 will create it.
```

### Git Not Initialized

`/execute` never creates a repository — not at `{project_path}`, and emphatically not
anywhere above it. Stop and report, so the operator can decide:

```
Error: Git repository not initialized at {project_path}
/execute does not create repositories. Initialise it yourself, then re-run.
```

### Resume With Nothing To Resume

Not an error. `--resume` against an empty or absent ledger simply runs from the beginning,
because that is what the evidence says is outstanding:

```
[EXEC] --resume: no verified tasks in the ledger; starting from the beginning
```

A missing `execute-state.json` is likewise not fatal — the ledger is the record that matters,
and it lives in `{project_path}/.execute/{prd_slug}/`.

## Output Format

### Minimal Mode (default)

```
[EXEC] Starting layer 0-setup (4 tasks)
[EXEC] Layer 0-setup complete (4/4)
[EXEC] Starting layer 1-foundation (6 tasks)
[EXEC] Layer 1-foundation complete (6/6)
...
[EXEC] All layers complete (44/44 tasks)
```

### Verbose Mode

```
[EXEC] Execution Plan:
  PRD: voice-prd-generator
  Project: /home/user/projects/voice-prd
  Worktrees: /home/user/projects/.worktrees
  Max parallel: 3

[EXEC] Starting layer 0-setup (4 tasks)
  [LAYER 0-setup] Batch 1/1: L0-001, L0-002, L0-003, L0-004
    [L0-001] Creating worktree...
    [L0-001] Implementing...
    [L0-001] Verified (3/3 steps)
    ...
  [LAYER 0-setup] Merged: L0-001, L0-002, L0-003, L0-004
[EXEC] Layer 0-setup complete (4/4)
...
```

## Context Isolation

This skill runs in `context: fork`:
- Fresh context for each execution
- No context bleed from previous runs
- Spawns child skills which also fork
- State file is the persistence mechanism

## Critical Rules

1. **Execute the layers the plan declares**, in the order it declares them, and skip only
   what git says is already done. There is no fixed set and no fixed count: item 31 derives the
   set from the document, item 28 lets a project name its own. `resolve-layers.py` answers this,
   and a list of tier names written here is how P44 happened
2. **Respect dependencies**: Only execute tasks with satisfied deps
3. **Stop on abandon**: If task hits 5 failures, STOP immediately
4. **Preserve worktrees**: Never delete worktrees on failure
5. **Sequential merges**: Merge one task at a time to avoid conflicts
6. **Update state**: Write state after every significant event
7. **Never edit a task file**: not you, not any agent you dispatch. An unsatisfiable task is
   reported, never repaired — see Step 3b and Step 8's `task_defect`
