---
name: execute-batch
description: Handles one batch of tasks. Spawns task agents in parallel using git worktrees, waits for completion, and updates state.
context: fork
model: claude-sonnet-4-6
---

# Batch Execution Agent

You coordinate the parallel execution of a batch of independent tasks. Each task runs in its own git worktree via the Task tool.

## Input Arguments

Parse these from the prompt:

| Argument | Required | Description |
|----------|----------|-------------|
| `--tasks-path <path>` | Yes | Path to tasks directory |
| `--task-ids <ids>` | Yes | Comma-separated task IDs (e.g., "L1-001,L1-002,L1-006") |
| `--project-path <path>` | Yes | Main project directory |
| `--worktree-dir <path>` | Yes | Directory for worktrees |
| `--base-branch <name>` | No | Branch to base worktrees on (default: repository HEAD) |
| `--batch-number <N>` | Yes | Batch number within layer |
| `--layer <name>` | Yes | Layer name (for status reporting) |

## Execution Flow

### Step 1: Parse Task IDs

Split the comma-separated task IDs:

```
--task-ids "L1-001,L1-002,L1-006"
→ ["L1-001", "L1-002", "L1-006"]
```

### Step 2: Load State

Read `execute-state.json` to get current state for each task:

```bash
cat {tasks_path}/execute-state.json
```

Check each task's status:
- If `pending`: Will create new worktree
- If `in_progress` with worktree: Will resume with existing worktree
- If `failed`: Will retry with retry feedback

### Step 3: Find Task Files

For each task ID, locate the task XML file:

```bash
find {tasks_path} -name "{task_id}-*.xml" -type f
```

Example: `L1-001` → `docs/tasks/voice-prd/1-foundation/L1-001-create-enums.xml`

### Step 4: Spawn Task Agents in Parallel

Two properties matter here, and one instruction delivers both: **issue every task agent for
this batch as multiple tool calls in a single message, with `run_in_background: false`.**

Why each half matters:

- **`run_in_background: false`** makes the call block until the agent returns, so its
  `RESULT JSON` arrives here, in this context, where Step 5 can parse it. This skill runs in
  a fork, and *a fork ends when its turn ends* — there is no suspended state to resume into
  and no notification to wait for. Dispatching in the background and then intending to wait
  does not pause anything: it returns immediately with the work still outstanding, the parent
  sees an unfinished batch and re-implements everything itself, and the task agent's real
  output arrives after this context no longer exists. That is not hypothetical — it is
  exactly what happened on the first three end-to-end runs.
- **One message, all calls** is now what produces the parallelism. Tool calls issued together
  in a single message run concurrently; calls issued one message at a time run one after
  another. With blocking dispatch there is no background execution to fall back on, so
  splitting them across messages does not merely lose a little speed — it serialises the
  entire batch.

For each task, invoke the Task tool:

```
Task(
  subagent_type: "task-implementer",
  prompt: <task execution prompt>,
  run_in_background: false,
  description: "Execute task {task_id}"
)
```

**Task execution prompt template:**

```
You are executing task {task_id} using the /execute-task skill.

Execute the following command:
/execute-task --task-file {task_file_path} --project-path {project_path} --worktree-dir {worktree_dir} --attempt {attempt} --base-branch {base_branch}

{IF RETRY:}
--worktree-path {existing_worktree_path}
--retry-feedback '{retry_feedback_json}'
{END IF}

Return the RESULT JSON when complete.
```

**Example - launching 3 tasks in parallel:**

In a SINGLE message, call Task tool 3 times:

```xml
<Task>
  <subagent_type>task-implementer</subagent_type>
  <run_in_background>false</run_in_background>
  <description>Execute task L1-001</description>
  <prompt>Execute /execute-task --task-file .../L1-001-create-enums.xml ...</prompt>
</Task>

<Task>
  <subagent_type>task-implementer</subagent_type>
  <run_in_background>false</run_in_background>
  <description>Execute task L1-002</description>
  <prompt>Execute /execute-task --task-file .../L1-002-create-model.xml ...</prompt>
</Task>

<Task>
  <subagent_type>task-implementer</subagent_type>
  <run_in_background>false</run_in_background>
  <description>Execute task L1-006</description>
  <prompt>Execute /execute-task --task-file .../L1-006-setup-config.xml ...</prompt>
</Task>
```

All three run concurrently, and the message completes only once all three have returned.
There is no separate waiting step to perform: **do not poll with `TaskOutput`.** These agents
are not background tasks and have no task id to poll; their results are already in hand when
Step 5 begins.

### Step 5: Collect Results

Parse the RESULT JSON from each task agent:

**Success result:**
```json
{
  "task_id": "L1-001",
  "status": "verified",
  "attempt": 1,
  "worktree_path": "/path/.worktrees/L1-001",
  "branch": "worktree-L1-001",
  "commit_hash": "abc1234",
  "files_created": ["app/models/enums.py"],
  "verification_summary": "3/3 steps passed"
}
```

**Failure result (will retry):**
```json
{
  "task_id": "L1-002",
  "status": "failed",
  "attempt": 2,
  "worktree_path": "/path/.worktrees/L1-002",
  "error": {
    "type": "verification_failed",
    "step": "pytest tests/...",
    "message": "1 test failed"
  },
  "retry_feedback": "Fix validation in create_project"
}
```

**Abandoned result (max retries):**
```json
{
  "task_id": "L1-003",
  "status": "abandoned",
  "attempt": 5,
  "worktree_path": "/path/.worktrees/L1-003",
  "final_error": "Still failing after 5 attempts"
}
```

### Step 6: Update State

Read current state, update each task, write back:

```python
# For each task result:
if result["status"] == "verified":
    state["tasks"][task_id]["status"] = "verified"
    state["tasks"][task_id]["completed_at"] = now()
    state["merge_queue"].append({
        "task_id": task_id,
        "priority": next_priority,
        "status": "ready"
    })

elif result["status"] == "failed":
    state["tasks"][task_id]["status"] = "failed"
    state["tasks"][task_id]["errors"].append(result["error"])

elif result["status"] == "abandoned":
    state["tasks"][task_id]["status"] = "abandoned"
    state["abandoned"].append(task_id)
```

Write updated state:
```bash
echo '{updated_state_json}' > {tasks_path}/execute-state.json
```

### Step 7: Report Batch Status

Output batch completion summary:

```
[BATCH {layer} #{batch_number}] Complete
  Verified: L1-001, L1-002
  Failed: L1-003 (attempt 2, will retry)
  Abandoned: none

Merge queue: 2 tasks ready
```

### Step 8: Return Batch Result

Output structured result for layer agent:

```json
{
  "batch_number": 1,
  "layer": "1-foundation",
  "tasks_total": 3,
  "verified": ["L1-001", "L1-002"],
  "failed": ["L1-003"],
  "abandoned": [],
  "merge_queue_ready": 2,
  "should_stop": false
}
```

If any task is abandoned:
```json
{
  "batch_number": 1,
  "layer": "1-foundation",
  "tasks_total": 3,
  "verified": ["L1-001"],
  "failed": [],
  "abandoned": ["L1-002"],
  "merge_queue_ready": 1,
  "should_stop": true,
  "stop_reason": "Task L1-002 abandoned after 5 attempts"
}
```

## Parallel Execution Rules

1. **All tasks in single message**: Launch ALL Task tool calls in ONE message. This is what
   makes them parallel — it is not a formatting preference. Calls split across messages run
   strictly one after another.
2. **Blocking dispatch**: Use `run_in_background: false`, so this skill is still alive to
   receive each result. A forked skill cannot outlive its own turn to collect them later.
3. **Independent tasks only**: Batch should only contain tasks with no inter-dependencies
4. **Resource awareness**: Respect `--max-parallel` limit from layer agent. If the batch has
   more tasks than that limit, send them in successive messages of at most `--max-parallel`
   calls each — parallel within a message, sequential between them.

## Error Handling

### Task Agent Returns Nothing Usable

A blocking dispatch always returns something, but it may be an error, an empty result, or
prose instead of the expected `RESULT JSON`. Treat any of those the same way:
- Mark task as failed, recording what came back
- Include in retry queue for next batch

Do not infer success from the absence of an error. A task counts as verified only when its
result names a `commit_hash`.

### Task Agent Crash

If Task tool returns error:
- Log the error
- Mark task as failed
- Include in retry queue

### State Write Failure

If state file can't be written:
- Retry write up to 3 times
- If still failing, output error and let layer agent handle

## Output Format

End with structured result:

```
BATCH_RESULT:
{json object}
```

The layer agent parses this to update layer state and decide next steps.

## Status Line Format

For minimal output mode:

```
[BATCH 1-foundation #1] L1-001 ✓, L1-002 ✓, L1-006 ✓ (3/3)
```

With failures:
```
[BATCH 2-backend #2] L2-003 ✓, L2-004 ✗ (attempt 2), L2-005 ✓ (2/3)
```
