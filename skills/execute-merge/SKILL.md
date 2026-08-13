---
name: execute-merge
description: Merges completed task worktree to the base branch. Handles sequential merge queue to prevent conflicts.
context: fork
model: claude-sonnet-4-6
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
| `--base-branch <name>` | No | Branch to merge into. Defaults to the repository's current HEAD — never assume `main` |

## Execution Flow

### Step 0: Resolve the Base Branch

Do this before any command that references `{base_branch}`. If `--base-branch` was not
supplied, take it from the repository rather than assuming `main`:

```bash
base_branch=$(git -C {project_path} symbolic-ref --short HEAD)
```

### Step 1: Parse Task XML

Read task file for commit message context:

```bash
cat {task_file}
```

Extract:
- `<meta><id>`: Task ID
- `<meta><name>`: Task name
- `<meta><layer>`: Layer name
- `<requirements>`: For commit message summary

### Step 2: Verify Worktree State

Check worktree is ready for merge:

```bash
cd {worktree_path}

# Check we're on the right branch
git branch --show-current
# Expected: worktree-{task_id}

# Check for uncommitted changes
git status --porcelain
# Expected: empty (all changes committed)

# Get commit count
git rev-list --count {base_branch}..HEAD
# Expected: >= 1
```

### Step 3: Ensure Changes Committed

If there are uncommitted changes (shouldn't happen normally):

```bash
cd {worktree_path}
git add .
git commit -m "$(cat <<'EOF'
[{task_id}] Uncommitted changes before merge

Auto-committed by merge agent.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Step 4: Switch to Main Project

```bash
cd {project_path}

# Refuse to merge into anything other than the repository we were pointed at. A previous
# run, having failed to create a worktree, walked up to the workspace root, ran `git init`
# there and merged into *that* -- producing a stray repository holding the docs tree and a
# gitlink to the real project. Assert the target before mutating it.
test "$(git rev-parse --show-toplevel)" = "$(pwd -P)" || {
  echo "REFUSED: $(pwd -P) is not a repository root; refusing to merge" && exit 1
}

# Ensure we're on the base branch
git checkout {base_branch}

# Pull latest ONLY if a remote is configured. A repository with no remote is a
# supported configuration, and an unconditional fetch fails the merge queue.
if git remote get-url origin >/dev/null 2>&1; then
  git fetch origin {base_branch} || true
  git merge origin/{base_branch} --ff-only 2>/dev/null || true
fi
```

### Step 5: Merge Worktree Branch

Use `--no-ff` to preserve merge history:

```bash
cd {project_path}

git merge --no-ff worktree-{task_id} -m "$(cat <<'EOF'
Merge worktree-{task_id}: {task_name}

Layer: {layer}
Task: {task_id}
Commits: {commit_count}

Implements:
- {requirement_1_summary}
- {requirement_2_summary}

Verification: Passed
EOF
)"
```

### Step 6: Handle Merge Result

**If merge succeeds:**
- Capture merge commit hash
- Proceed to cleanup

**If merge fails (conflict):**
- This should NOT happen with sequential merging
- Abort merge: `git merge --abort`
- Report conflict details
- Keep worktree for debugging

### Step 7: Cleanup Worktree

After successful merge:

```bash
cd {project_path}

# Remove worktree
git worktree remove {worktree_path}

# Delete the branch
git branch -d worktree-{task_id}
```

If removal fails:
```bash
git worktree remove --force {worktree_path}
git branch -D worktree-{task_id}
```

### Step 8: Record the Task in the Ledger

**Do this immediately after the merge commit exists, before updating any counters.** The
ledger is the record that can be checked; `execute-state.json` is a convenience that cannot.

```bash
sh {skill_dir}/scripts/record-task.sh {project_path} {prd_slug} {task_id} {merge_commit_sha} {attempts}
```

`{skill_dir}` is the base directory given at the top of this skill — the one ending in
`skills/execute-merge`. `{merge_commit_sha}` is the merge commit you just created:
`git rev-parse HEAD` in `{project_path}`.

The script refuses to record a SHA that does not exist, which is the entire point: a task
cannot be marked done by asserting it. **If it exits non-zero, the task is not done** — treat
that as a merge failure and do not report success.

Order matters. Appending after the commit means a crash between the two *under*-reports
progress, which a resume can recover from. Appending first over-reports, and over-reporting is
how `execute-state.json` came to claim 23 of 18 tasks complete in a run that did 18.

### Step 9: Refresh State

Step 8 already recorded the fact. This step only regenerates the human-readable view of it:

```bash
python {execute_skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug}
```

**Do not edit `execute-state.json` by hand — not one field.** The script derives every value
from the ledger and git, which is the only reason it is ever right. Left to prose, this file
has been wrong in four different ways across four runs: 23 of 18 complete, 19 entries for 18
tasks, `completed` alongside 2 remaining, and `completed` alongside 4 of 18 while git held 18
merges. A fifth set of careful instructions would produce a fifth shape of wrong.

The script also refuses to write inside `{project_path}` — in run 8 a second copy of this file
appeared in the target repository as untracked noise (**F21**).

### Step 10: Report Result

**Success:**

```json
{
  "task_id": "L1-001",
  "status": "merged",
  "merge_commit": "abc1234567890",
  "commits_merged": 2,
  "worktree_cleaned": true,
  "branch_deleted": true
}
```

**Conflict (should not happen):**

```json
{
  "task_id": "L1-001",
  "status": "conflict",
  "conflict_files": ["app/models/__init__.py"],
  "conflict_type": "both_modified",
  "worktree_preserved": true,
  "resolution_needed": true,
  "suggested_action": "Manually resolve conflict in worktree, then re-run merge"
}
```

## Merge Commit Format

```
Merge worktree-L1-001: Create enums and constants

Layer: 1-foundation
Task: L1-001
Commits: 2

Implements:
- ProjectStatus enum (draft, in_progress, complete)
- PersonaType enum (developer, designer, pm)

Verification: Passed
```

## Sequential Merge Guarantee

The layer agent ensures merges happen in priority order:

```
Merge Queue:
  Priority 1: L1-001 (status: ready)   ← Merge this first
  Priority 2: L1-002 (status: ready)   ← Wait
  Priority 3: L1-006 (status: pending) ← Still implementing
```

Each task waits for lower-priority tasks to merge before proceeding.

This ensures:
- No merge conflicts between parallel tasks
- Deterministic commit history
- Easy rollback of specific tasks

## Worktree Preservation

On merge failure:
- **Never delete worktree**
- Worktree contains all implementation work
- User can inspect and manually resolve
- Resume will re-attempt merge after manual fix

## Error Handling

### Branch Not Found

```bash
git merge worktree-{task_id}
# fatal: worktree-L1-001 - not something we can merge
```

Action: Check if branch exists, report error if not.

### Worktree Not Found

```bash
git worktree remove {worktree_path}
# fatal: '{worktree_path}' is not a working tree
```

Action: Already removed (maybe manual cleanup). Continue.

### Uncommitted Changes on the Base Branch

```bash
git checkout {base_branch}
# error: Your local changes would be overwritten
```

Action: Error - the base branch should always be clean. Report and stop.

### Merge Conflict

```bash
git merge --no-ff worktree-{task_id}
# CONFLICT (content): Merge conflict in app/models/__init__.py
# Automatic merge failed; fix conflicts and then commit.
```

Action:
1. Abort: `git merge --abort`
2. Report conflict details
3. Preserve worktree
4. Return conflict status

## Output Format

### Status Line

```
[MERGE] L1-001 → {base_branch} (abc1234)
```

### Final Result

```
MERGE_RESULT:
{json object}
```

## Git Commands Reference

| Command | Purpose |
|---------|---------|
| `git merge --no-ff branch` | Merge preserving history |
| `git merge --abort` | Cancel conflicting merge |
| `git worktree remove path` | Remove worktree |
| `git worktree remove --force path` | Force remove |
| `git branch -d branch` | Delete merged branch |
| `git branch -D branch` | Force delete branch |
| `git rev-parse HEAD` | Get current commit hash |
| `git rev-list --count {base_branch}..HEAD` | Count commits since the base branch |
