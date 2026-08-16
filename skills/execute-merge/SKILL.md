---
name: execute-merge
description: Merges completed task worktree to the base branch. Handles sequential merge queue to prevent conflicts.
context: fork
model: claude-sonnet-5
---

# Merge Agent

You merge a completed task's worktree branch into the base branch. Tasks complete in parallel but merge sequentially to avoid conflicts.

## Input Arguments

Parse these from the prompt:

| Argument | Required | Description |
|----------|----------|-------------|
| `--task-id <id>` | Yes | Task ID to merge (e.g., "L1-001") |
| `--project-path <path>` | Yes | Main project directory |
| `--worktree-path <path>` | Yes | Path to task's worktree |
| `--task-file <path>` | Yes | Task XML for commit context |
| `--tasks-path <path>` | Yes | Tasks directory for state update |
| `--prd-slug <slug>` | Yes | PRD/CRD slug. Names the ledger the merge is recorded in |
| `--attempts <n>` | No | Attempt number for this task (default 1); recorded in the ledger |
| `--base-branch <name>` | No | Branch to merge into. Defaults to the repository's current HEAD — never assume `main` |

## Execution Flow

### Step 1: Merge, Record and Clean Up

One script does the whole git sequence, and its exit status is the decision:

```bash
sh {skill_dir}/scripts/merge-task.sh {project_path} {prd_slug} {task_id} \
   {worktree_path} {task_file} {base_branch} {attempts}
```

`{skill_dir}` is the base directory given at the top of this skill — the one ending in
`skills/execute-merge`. It prints the merge commit SHA on stdout.

| Exit | Meaning | What you do |
|------|---------|-------------|
| 0 | Merged, recorded in the ledger, worktree and branch cleaned up | Go to Step 2 |
| 1 | **Refused before touching anything.** Nothing was merged | Report the `REFUSED:` line verbatim; the task is not merged |
| 3 | **Merge conflict.** Aborted; worktree preserved | Report it and stop — see below |

What it does, in this order: resolves the base branch from the repository rather than assuming
`main`; asserts the target is the repository root; asserts the base branch has no uncommitted
tracked changes; asserts the worktree is on `worktree-{task_id}`, is clean, and is at least one
commit ahead; merges `--no-ff` with a message built from the task XML; records the merge commit
via `record-task.sh`; and only then removes the worktree and deletes the branch.

**Why this is one program and not the ten steps that used to be here.** It was the last git
sequence in the toolchain still described rather than executed — and every other one became a
script because the described version demonstrably failed. Six agents retyped `git worktree add`
and none kept `-b` (F18); a run walked up out of the target, ran `git init` and merged into that
(F19); a status field claimed 23 of 18 tasks were done (F16). The merge is the step that decides
whether a task counts as complete, so it is the last place to leave to improvisation. This is
the structural half of item **4.12**: git operations in one place, with one owner.

**Order matters, and it is not the order the prose had.** The ledger entry is written
immediately after the merge commit exists, *before* cleanup. A crash in between then
under-reports progress, which a resume recovers from. Cleaning up first would put a failure
mode — a worktree that will not remove — between the commit and the record of it, so a merged
task could end up unrecorded and be done twice. Cleanup failures are warnings; they cannot
decide whether work counts.

**It refuses uncommitted changes rather than committing them.** The old Step 3 auto-committed
whatever it found in the worktree under a merge-agent byline. Committing work you did not write,
to get past a state you did not expect, is the improvisation that produced F19. The task agent
owns its commits; if it did not make one, that is a task failure to report.

### Step 2: Refresh State

The ledger already holds the fact. This only regenerates the human-readable view of it:

```bash
python {execute_skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug}
```

**Do not edit `execute-state.json` by hand — not one field.** The script derives every value
from the ledger and git, which is the only reason it is ever right. Left to prose, this file has
been wrong in four different ways across four runs: 23 of 18 complete, 19 entries for 18 tasks,
`completed` alongside 2 remaining, and `completed` alongside 4 of 18 while git held 18 merges. A
fifth set of careful instructions would produce a fifth shape of wrong.

The script also refuses to write inside `{project_path}` — in run 8 a second copy of this file
appeared in the target repository as untracked noise (**F21**).

### Step 3: Report Result

Report what the script printed. Do not restate a SHA you did not read from it.

**Success:**

```json
{
  "task_id": "L1-001",
  "status": "merged",
  "merge_commit": "abc1234567890",
  "worktree_cleaned": true,
  "branch_deleted": true
}
```

**Conflict (exit 3):**

```json
{
  "task_id": "L1-001",
  "status": "conflict",
  "worktree_preserved": true,
  "resolution_needed": true,
  "suggested_action": "Inspect the preserved worktree, resolve manually, then re-run"
}
```

A conflict is not a task failure to retry blindly. Sequential merging is supposed to make it
impossible, so a conflict means an assumption broke — report it and stop rather than looping.

## Merge Commit Format

Built by the script from the task XML, not composed here:

```
Merge worktree-L1-001: Create enums and constants

Task: L1-001
Layer: 1-foundation
Commits: 2

Verification: passed
```

The old format also carried an `Implements:` list summarising requirements. It is gone
deliberately: it was the one field a model had to write, and it is the one nobody reads. Every
line above is derived, so the message cannot disagree with the merge it describes.

## Sequential Merge Guarantee

`/execute-layer` merges tasks one at a time, in the order they finished verifying. It calls
this skill once per task and waits for each to return.

That ordering is the only thing preventing conflicts between parallel tasks, which is why a
conflict is treated as a broken assumption rather than a retryable failure.

## Worktree Preservation

On any refusal or conflict the worktree is preserved — it holds all the implementation work,
and a resume re-attempts the merge once a human has looked. The script never removes a worktree
whose task it did not successfully merge and record.

## Error Handling

Every case below is detected by `merge-task.sh` and reported through its exit status. None of
them needs a command run here — running one by hand is how the target repository got mutated
from the wrong directory in the first place (F19).

| Condition | Exit | The script's behaviour |
|-----------|------|------------------------|
| Target is not a repository, or not its root | 1 | Refuses. Never runs `git init` |
| Base branch missing, or HEAD detached with none given | 1 | Refuses |
| Uncommitted **tracked** changes on the base branch | 1 | Refuses rather than checking out over them. Untracked files are ignored — the tasks directory legitimately sits inside the target in some layouts |
| Worktree missing, on the wrong branch, or dirty | 1 | Refuses. The task agent owns its own commits |
| Branch has no commits beyond the base | 1 | Refuses — there is nothing to merge |
| Merge conflict | 3 | Aborts the merge, preserves the worktree, records nothing |
| Worktree or branch will not delete | 0 | Warns. The task **is** merged and recorded; cleanup does not decide whether work counts |

In every exit-1 case the repository is untouched and the ledger is unchanged, so the task is
simply outstanding.

## Output Format

### Status Line

```
[MERGE] L1-001 -> {base_branch} (abc1234)
```

### Final Result

```
MERGE_RESULT:
{json object}
```
