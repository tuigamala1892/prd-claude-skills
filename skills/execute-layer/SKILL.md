---
name: execute-layer
description: Handles one layer of task execution. Groups ready tasks into batches, spawns batch agents, and processes merge queue after each batch.
context: fork
model: claude-sonnet-5
---

# Layer Execution Agent

You manage the execution of a single layer. You build the ready queue, group tasks into batches, spawn batch agents, and coordinate merges.

## Input Arguments

Parse these from the prompt:

| Argument | Required | Description |
|----------|----------|-------------|
| `--tasks-path <path>` | Yes | Path to tasks directory |
| `--layer <name>` | Yes | Layer to execute (e.g., "1-foundation") |
| `--project-path <path>` | Yes | Main project directory |
| `--worktree-dir <path>` | Yes | Directory for worktrees |
| `--prd-slug <slug>` | Yes | PRD/CRD slug. Names the ledger merges are recorded in |
| `--max-parallel <N>` | No | Max concurrent tasks (default: 3) |
| `--base-branch <name>` | No | Branch to base worktrees on and merge into (default: repository HEAD) |

## Execution Flow

### Step 1: Load Layer Plan

Read `layer_plan.json` to get dependency graph:

```bash
cat {tasks_path}/layer_plan.json
```

Extract:
- `dependency_graph`: Map of task_id → list of dependency task_ids
- `layers`: List of layer definitions with task lists

### Step 2: Load What Cannot Be Derived

Read `execute-state.json`:

```bash
cat {tasks_path}/execute-state.json
```

Take **two fields, and only two**:

- `failed`: task IDs that failed and have not since merged
- `abandoned`: task IDs that hit the retry limit

Those are the only things in that file not derived from somewhere more trustworthy — which is
why `write-state.py` carries exactly those two forward and rebuilds everything else.

**Do not take `completed` from here.** Completion comes from `ledger-status.sh`, re-verified
against git, in Step 3. This file has over-reported completion in four consecutive runs, and
over-reporting is the dangerous direction: it starts a task before the dependency it builds on
has landed. `tasks` and `merge_queue` are records of what already happened; nothing in this
skill decides anything from them.

### Step 3: Build Ready Queue

Find tasks that are ready to execute:

```python
def build_ready_queue(layer, dependency_graph, state):
    ready = []

    # `verified` comes from ledger-status.sh -- tasks whose commit exists right now.
    # Do NOT read completion out of execute-state.json: it has been wrong in four
    # consecutive runs, and the dangerous direction is over-reporting, which would let a
    # task start before the dependency it builds on had actually landed.
    verified = set(ledger_status()["verified_tasks"])

    for task in layer["tasks"]:
        task_id = task["id"]

        # Skip work that git says is already done
        if task_id in verified:
            continue

        # Skip abandoned
        if task_id in state["abandoned"]:
            continue

        # Check dependencies -- satisfied only by a commit that exists
        deps = dependency_graph.get(task_id, [])
        all_deps_complete = all(d in verified for d in deps)

        if all_deps_complete:
            ready.append(task_id)

    return ready
```

### Step 4: Nothing to Mark

There is no step here, deliberately.

A layer is `in_progress` when `merged < total` and `completed` when they are equal, and
`write-state.py` computes both from the manifest and the ledger every time it runs. Writing
`"status": "in_progress"` by hand would assert something already derived — and it would be
**erased**, not merged, because the script rebuilds the whole file rather than patching it.

`current_layer` no longer exists. A position marker can only be maintained by hand, and the
layer being executed is an argument this skill was invoked with.

### Step 5: Execute Batches Loop

While there are ready tasks:

#### 5a. Build Batch

Group ready tasks up to `max_parallel`:

```python
batch = ready_queue[:max_parallel]
```

Assign batch number — a counter local to this layer, held for the duration of the loop and
passed to `/execute-batch` as an argument. It is not state and nothing persists it:

```python
batch_number += 1
```

#### 5b. Spawn Batch Agent

Invoke `/execute-batch` skill:

```
/execute-batch --tasks-path {tasks_path} --task-ids {comma_separated_ids} --project-path {project_path} --worktree-dir {worktree_dir} --batch-number {batch_number} --layer {layer} --base-branch {base_branch}
```

Wait for batch completion.

#### 5c. Handle Batch Result

Parse batch result:

```json
{
  "batch_number": 1,
  "verified": ["L1-001", "L1-002"],
  "failed": ["L1-003"],
  "abandoned": [],
  "should_stop": false
}
```

**If `should_stop: true`:**
- Do NOT build another batch
- **Still run 5d.** Verified tasks have commits, and the ledger only learns about them when
  the merge happens. Skipping the merge queue on the way out loses work that succeeded, and
  the resume then redoes it.
- Report to the orchestrator immediately, passing `stop_reason_kind` and `stop_reason`
  through **unchanged**

`stop_reason_kind` distinguishes two outcomes that must not be summarised into one:

| Kind | What happened | What the operator must do |
|------|---------------|---------------------------|
| `abandoned` | A task failed 5 times | Read the errors; fix something |
| `usage_limit` | The subscription window closed mid-run | Nothing, until it resets |

Do not paraphrase a `usage_limit` stop into "task failed". Nothing failed — the run ran out of
allowance, and the only correct next action is to resume later.

#### 5d. Merge What the Batch Verified

The merge set is **5c's `verified` array**, in the order the batch returned it. That array is
the only thing that knows what this batch just proved:

```python
for task_id in batch_result["verified"]:
    invoke_merge(task_id)
```

**Do not look for the merge set in `execute-state.json`.** Its `merge_queue` is a record of
merges that have already happened — `write-state.py` derives it from the ledger, and every entry
in it is `"merged"` by construction. There is no `"ready"` entry to find, so a loop looking for
one merges nothing at all. See §Merge Queue State below, which says the same thing from the
other direction.

Call `/execute-merge` for each one:

```
/execute-merge --task-id {task_id} --project-path {project_path} --worktree-path {worktree_path} --task-file {task_file} --tasks-path {tasks_path} --prd-slug {prd_slug} --base-branch {base_branch} --attempts {attempts}
```

**IMPORTANT**: Merge tasks **sequentially**, one `/execute-merge` at a time, in the order above.
Parallel merges conflict.

#### 5e. Re-evaluate Ready Queue

After batch completes and merges finish:
- Some tasks may now have all dependencies satisfied
- Rebuild ready queue with fresh state
- Continue loop if tasks remain

### Step 6: Nothing to Close

When there are no more ready tasks, the layer is over and there is nothing to write.

`/execute-merge` runs `write-state.py` after every merge, so the last merge of the layer already
left `execute-state.json` current: `merged == total` for this layer, and its status therefore
reads `completed` without anyone saying so. If the layer ends with tasks unmerged, the file
correctly says `in_progress` — and writing `completed` over it, which is what this step used to
do, would be the assertion that made four runs disagree with git.

Report the outcome in Step 7 instead. A report is a claim about a run; the state file is a
derivation from the repository, and only one of the two may be authored.

### Step 7: Report Layer Result

Output structured result for orchestrator:

```json
{
  "layer": "1-foundation",
  "status": "completed",
  "tasks_total": 6,
  "tasks_completed": 6,
  "tasks_failed": 0,
  "tasks_abandoned": 0,
  "batches_executed": 3,
  "should_stop": false
}
```

**If a task was abandoned:**

```json
{
  "layer": "2-backend",
  "status": "stopped",
  "tasks_total": 9,
  "tasks_completed": 5,
  "tasks_failed": 0,
  "tasks_abandoned": 1,
  "abandoned_task": "L2-006",
  "batches_executed": 2,
  "should_stop": true,
  "stop_reason_kind": "abandoned",
  "stop_reason": "Task L2-006 abandoned after 5 attempts"
}
```

**If the run met a usage limit:**

```json
{
  "layer": "2-backend",
  "status": "stopped",
  "tasks_total": 9,
  "tasks_completed": 5,
  "tasks_failed": 0,
  "tasks_abandoned": 0,
  "stopped_task": "L2-006",
  "batches_executed": 2,
  "should_stop": true,
  "stop_reason_kind": "usage_limit",
  "stop_reason": "limit\nmatched: Claude AI usage limit\nreset: resets at 17:30 UTC"
}
```

Note `tasks_abandoned: 0` — nothing was abandoned, and `tasks_completed: 5` still counts the
tasks that merged before the stop.

## Batch Construction Algorithm

### Basic Batching

```python
def build_batches(ready_tasks, max_parallel):
    batches = []
    remaining = list(ready_tasks)

    while remaining:
        batch = remaining[:max_parallel]
        remaining = remaining[max_parallel:]
        batches.append(batch)

    return batches
```

### Example

Ready queue: `[L1-001, L1-002, L1-006, L1-003, L1-004, L1-005]`
Max parallel: 3

Batch 1: `[L1-001, L1-002, L1-006]`
Batch 2: `[L1-003, L1-004, L1-005]`

### Dynamic Re-evaluation

After Batch 1 completes:
- L1-001, L1-002, L1-006 now complete
- L1-003 depends on L1-002 → now ready
- L1-004 depends on L1-003 → still blocked
- L1-005 depends on L1-003 → still blocked

New ready queue: `[L1-003]` (only 1 task ready now)

Batch 2 executes with just L1-003.

After Batch 2:
- L1-003 complete
- L1-004 now ready
- L1-005 now ready

Batch 3: `[L1-004, L1-005]`

## Merge Queue Processing

### Sequential Merge Order

Tasks complete in parallel but merge sequentially:

```
Execution Order (parallel):
  L1-001 completes at t=10s
  L1-006 completes at t=15s
  L1-002 completes at t=20s

Merge Order (sequential by priority):
  1. L1-001 (priority 1) → merge at t=21s
  2. L1-002 (priority 2) → merge at t=22s
  3. L1-006 (priority 3) → merge at t=23s
```

### Merge Queue State

```json
{
  "merge_queue": [
    {"task_id": "L1-001", "status": "merged", "commit": "3dde719", "merged_at": "2026-08-25T09:12:00Z"},
    {"task_id": "L1-002", "status": "merged", "commit": "8a1f0c4", "merged_at": "2026-08-25T09:13:00Z"}
  ]
}
```

Every entry is a merge that happened, with the commit that proves it. There is no `priority`
field and no `pending`, `ready` or `merging` entry — a queue of intentions is exactly the kind of
assertion that was wrong in four runs out of four. L1-006 is absent from the example because it
has not merged yet, and nothing records an intention to merge it.

### Merge Order

Tasks are merged in the order they finish verifying, and you hold that order yourself for the
duration of the batch — pass it to `/execute-merge` one task at a time. There is no queue to
maintain in a file.

`execute-state.json` does contain a `merge_queue`, but it is **derived** from the ledger by
`write-state.py` after the fact, as a record of what was merged and when. Do not append to it;
an entry there means a merge commit exists, and writing one by hand would make that untrue.

## Error Handling

### Batch Agent Failure

If batch agent crashes or times out:
- Mark all tasks in batch as failed
- Add to retry queue for next batch
- Continue with remaining batches

### Merge Failure

If merge fails (shouldn't happen with sequential merges):
- Keep worktree for debugging
- Mark task as failed
- Report to orchestrator

### State Corruption

If state file is corrupted:
- Attempt to reconstruct from worktrees and git log
- If not possible, report error and stop

## Output Format

### Status Line (Minimal Mode)

```
[LAYER 1-foundation] Started (6 tasks)
[LAYER 1-foundation] Batch 1/3: L1-001 ✓, L1-002 ✓, L1-006 ✓
[LAYER 1-foundation] Merged: L1-001, L1-002, L1-006
[LAYER 1-foundation] Batch 2/3: L1-003 ✓
[LAYER 1-foundation] Merged: L1-003
[LAYER 1-foundation] Batch 3/3: L1-004 ✓, L1-005 ✓
[LAYER 1-foundation] Merged: L1-004, L1-005
[LAYER 1-foundation] Complete (6/6 tasks)
```

### Final Result

End with:

```
LAYER_RESULT:
{json object}
```

The orchestrator parses this to decide next layer or stop.

## Dependency Graph Format

From `layer_plan.json`:

```json
{
  "dependency_graph": {
    "L0-001": [],
    "L0-002": ["L0-001"],
    "L0-003": ["L0-002"],
    "L0-004": ["L0-003"],
    "L1-001": ["L0-004"],
    "L1-002": ["L1-001"],
    "L1-003": ["L1-002"],
    "L1-004": ["L1-003"],
    "L1-005": ["L1-003"],
    "L1-006": ["L0-004"]
  }
}
```

Reading: `L1-003` depends on `L1-002`. L1-003 cannot start until L1-002 is complete.
