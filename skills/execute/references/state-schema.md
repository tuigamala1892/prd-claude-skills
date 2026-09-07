# Execute State Schema

## Overview

The execution state is stored in `execute-state.json` in the tasks directory. It is a **report**,
not a record: every field is derived from the ledger and git each time it is written, and nothing
in it is authoritative. The ledger is the record; this file is the readable summary of it.

## File Location

```
{tasks-path}/execute-state.json
```

Example: `docs/tasks/link-shelf/execute-state.json`

`write-state.py` refuses to write `execute-state.json` at the project root — that was run 8's
second copy, holding a different half of the schema from the correct one.

## Schema Version

Current version: `3.0`

`schema_version` records **how to read the file**. It moves when the shape below changes, which is
not the same event as a plugin release; see `plugin.json` for the toolchain version.

## The Only Writer

```bash
python {skill_dir}/scripts/write-state.py {tasks_path} {project_path} {prd_slug} \
    --started-at {run_start_iso8601} [--abandoned ID,ID] [--failed ID,ID]
```

Run once at the start, after each merge (`/execute-merge` does this), and once at the end.

**No field in this file may be written or edited by hand**, and there is no `init_state`. Four runs
produced four different wrong shapes when it was assembled from prose instructions: 23 of 18
complete; 19 entries for 18 tasks; `completed` alongside 2 remaining; `completed` alongside 4 of 18
while git held 18 merges. The script cannot count to 4 when git says 18.

A hand-written field is also **erased**, not merged: the script rebuilds the whole document from
the manifest and the ledger on every run. Only two things are carried forward from the previous
file, because they genuinely cannot be derived — which tasks were abandoned, and which failed.

## Complete Schema

Real output from `write-state.py`, for a three-task run with one task merged and one failed:

```json
{
  "schema_version": "3.0",
  "prd_slug": "link-shelf",
  "project_path": "/home/user/projects/link-shelf",
  "tasks_path": "/home/user/projects/docs/tasks/link-shelf",
  "started_at": "2026-08-25T09:00:00Z",
  "updated_at": "2026-08-25T09:14:02Z",
  "completed_at": null,
  "status": "in_progress",
  "derived_from": "ledger + git; no field in this file is maintained by hand",

  "tasks": {
    "L1-001": {
      "status": "merged",
      "layer": "1-foundation",
      "name": "Create enums and constants",
      "commit": "3dde7196e91c08c2d9ed32708436028980494daa",
      "merged_at": "2026-08-25T09:12:00Z",
      "attempts": 1
    },
    "L2-001": {
      "status": "failed",
      "layer": "2-backend",
      "name": "Create project CRUD API",
      "source_feature": "save-link",
      "moscow": "must-have",
      "requirement_level": "P0"
    },
    "L2-002": {
      "status": "pending",
      "layer": "2-backend",
      "name": "Create link CRUD API",
      "source_features": [
        {"slug": "list-links", "moscow": "should-have",
         "satisfies_criteria": ["2"], "requirement_level": "P1"},
        {"slug": "tag-links", "moscow": "could-have",
         "satisfies_criteria": ["1", "3"], "requirement_level": "P2"}
      ],
      "moscow": "should-have",
      "requirement_level": "P1"
    }
  },

  "layers": {
    "1-foundation": {"total": 1, "merged": 1, "status": "completed"},
    "2-backend": {"total": 2, "merged": 0, "status": "in_progress"}
  },

  "tiers": {
    "by_tier": {"must-have/P0": 1, "should-have/P1": 1},
    "unattributed": 1
  },

  "completed": ["L1-001"],
  "failed": ["L2-001"],
  "abandoned": [],

  "merge_queue": [
    {
      "task_id": "L1-001",
      "status": "merged",
      "commit": "3dde7196e91c08c2d9ed32708436028980494daa",
      "merged_at": "2026-08-25T09:12:00Z"
    }
  ],

  "missing_commits": [],

  "metrics": {
    "tasks_total": 3,
    "tasks_completed": 1,
    "tasks_failed": 1,
    "tasks_abandoned": 0,
    "tasks_remaining": 2,
    "total_attempts": 1
  }
}
```


## `source_features`, `moscow`, `requirement_level` and `tiers` (items 19 and 65)

Item 16 puts four traceability elements on a task; `build-manifest.py` carries them into the
manifest; this file records them per task and **derives `tiers` from them**.

**`source_features` is a list, because a task may descend from more than one feature** (item 65).
`source_feature` — singular — is still written when there is exactly one, and is **absent** when
there are several rather than naming whichever came first: a reader that knows only the singular
key then sees an unattributed task instead of a misattributed one, which is the difference P43
was about.

**`moscow` and `requirement_level` are the STRONGEST across the edges.** A task is built or not
built as a unit, so `tiers` counts it once, at the strongest obligation it carries. The per-edge
values stay in the list for a reader that needs to know which feature asked for what.

**They are omitted when absent, never written as `null`.** A Layer 0 task legitimately carries
no tier — it descends from the tech stack rather than from a feature — so *"has no tier"* and
*"tier not recorded"* have to stay distinguishable, and `tiers.unattributed` counts the
difference rather than hiding it.

**`requirement_level` would otherwise have no reader at all.** Item 16 puts it on the task and
item 30 checks criteria against the *threshold* rather than against the element, so nothing else
looks at it. Reporting it is both the cheapest reader and the useful one: *"built 14 tasks:
9 must-have/P0, 5 should-have/P0"* is a sentence an operator can act on, and it is the only place
the two-level filter — `--priority` and `--requirement-level` — becomes visible in the **output**
rather than only in the invocation.

**`tiers` is derived, like every other field here.** Nothing in this file is maintained by hand,
and a summary counted by whoever writes the report is a summary that disagrees with the tasks it
counts.

## Field Descriptions

### Root Fields

| Field | Type | Derived from |
|-------|------|--------------|
| `schema_version` | string | Constant `"3.0"` |
| `prd_slug` | string | Argument |
| `project_path` | string | Argument, absolute |
| `tasks_path` | string | Argument, absolute |
| `started_at` | ISO8601 | `--started-at`, else the previous file, else now |
| `updated_at` | ISO8601 | Now |
| `completed_at` | ISO8601 \| null | Now when `status` is `completed`, else null |
| `status` | enum | `completed` \| `in_progress` — see below |
| `derived_from` | string | Constant; states the provenance rule in the file itself |
| `tasks` | object | Manifest inventory × ledger |
| `layers` | object | Grouped from the same |
| `completed` | array | Sorted task ids with a verified commit |
| `failed` | array | `--failed`, minus anything since merged |
| `abandoned` | array | `--abandoned`, minus anything since merged |
| `merge_queue` | array | One entry per verified merge |
| `missing_commits` | array | Ledger entries whose commit is **not** in git |
| `metrics` | object | `len()` of the above; nothing is incremented |

### Overall Status

Two values, and only two:

- `in_progress` — anything short of complete
- `completed` — every task the manifest knows about has a commit that exists, with no missing
  commits and nothing abandoned

There is no `initializing` and no `stopped` value in this file. A stop is a fact about the run, not
about the state; `/execute` reports it and `write-state.py` will not write `completed` for a run
that stopped early.

### Task Fields

| Field | Type | Present |
|-------|------|---------|
| `status` | enum | Always |
| `layer` | string | Always — from the manifest entry |
| `name` | string | Always — from the manifest entry |
| `commit` | string | Merged tasks only |
| `merged_at` | ISO8601 | Merged tasks only |
| `attempts` | number | Merged tasks only — from the ledger entry |

**Task status:**

- `merged` — a ledger entry whose commit exists in git. The only status that means done.
- `failed` — named in `--failed` and not since merged
- `abandoned` — named in `--abandoned` and not since merged
- `pending` — everything else

The in-flight values a hand-maintained file used to carry — `in_progress`, `verifying`, `verified`,
`merging` — are gone. A task that is being worked on is `pending` here, because this file is
written between steps and cannot observe a step in progress. Ask the batch, not the state file.

### Layer Fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | number | Tasks in this layer, from the manifest |
| `merged` | number | How many have a verified commit |
| `status` | enum | `completed` when `merged == total`, else `in_progress` |

### Merge Queue Entry

Every entry is a merge that **has happened** and is verifiable:

```json
{"task_id": "L1-001", "status": "merged", "commit": "3dde719...", "merged_at": "2026-08-25T09:12:00Z"}
```

It is a history, not a plan. There is no `pending`, `ready` or `merging` entry and no `priority`
field — a queue of intentions is exactly the kind of assertion that was wrong in four runs out of
four.

### Missing Commits

Ledger entries naming a commit that git cannot find. `read_ledger` stops counting at the first
such gap, deliberately: a later verified SHA is not evidence that an earlier missing one was ever
done. A non-empty `missing_commits` means the ledger and the repository disagree, and the
repository wins.

### Metrics

| Field | Description |
|-------|-------------|
| `tasks_total` | From the manifest summary |
| `tasks_completed` | `len(verified merges)` |
| `tasks_failed` | `len(failed)` |
| `tasks_abandoned` | `len(abandoned)` |
| `tasks_remaining` | `tasks_total - tasks_completed`, floored at 0 |
| `total_attempts` | Sum of ledger `attempts` |

`elapsed_seconds` and `total_retries` no longer exist. `elapsed_seconds` was a number nobody
measured — run 6 recorded 4000 for a run of 10476 seconds. Compute a duration at report time from
`started_at` if one is wanted.

## What 2.0 Carried and 3.0 Does Not

A file written by 2.0 is readable but not comparable; these fields were removed rather than
renamed, and each for the same reason.

| 2.0 field | Why it is gone |
|---|---|
| `options` | The run's arguments, not its state. `/execute` has them already. |
| `current_layer`, `current_batch` | Position markers only a hand-writer can maintain; the script rebuilds the file and cannot observe a run mid-step. |
| `worktree_dir`, `worktrees` | Worktrees are git's, and `git worktree list` is the truth. A cached copy went stale in every run. |
| Per-task `commits[]`, `errors[]`, `retry_feedback[]` | The ledger holds what happened; retry feedback belongs to the batch that acts on it. |
| Layer `started_at`, `completed_at`, `tasks_*` | Timestamps nothing derived and counts that disagreed with git. |
| `context_update` | The finalizer's own concern, and it reports its own result. |
| `metrics.elapsed_seconds`, `metrics.total_retries` | Numbers nobody measured. |

## Reading the File

```python
import json
from pathlib import Path

def load_state(tasks_path: str) -> dict | None:
    state_file = Path(tasks_path) / "execute-state.json"
    return json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else None
```

There is no `save_state` counterpart, by design. To change the file, change what it is derived
from — merge a task, or pass `--failed` / `--abandoned` — and run the script.

## Resume Behavior

Resume is driven by the ledger, verified against git — **never by this file**. It once reported 20
of 20 complete when the repository held one merge commit, and a resume trusting it would have
skipped seventeen tasks that were never done.

On resume, `/execute` re-reads the ledger, re-checks each commit with `git cat-file`, and rebuilds
this file. A missing `execute-state.json` is therefore not fatal — it is regenerated. See
`skills/execute/SKILL.md` § Resume Behavior for the full sequence.

## Concurrency

There is one writer and it writes the whole file in one pass, so there is no lock and no merge.
Batches run in parallel, but they append to the **ledger**; the state file is written between
batches, after each merge, by a single caller. If two writers ever appear, the fix is to remove
one, not to add a lock — a lock around a derived file only serialises the rewriting of something
that will be rewritten again anyway.
