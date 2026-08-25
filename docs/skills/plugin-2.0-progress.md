# Plugin 2.0 — Implementation Ledger

**Companion to** [`plugin-2.0-plan.md`](plugin-2.0-plan.md), which stays a specification. This
file is the record of what has actually landed against it.

**Branch:** `phase-1-live-defects`
**Started:** 2026-08-25

---

## Why this is a separate file

The plan specifies 59 items and states, in its own closing argument, that a producer should have
a reader and an artefact should have one concern. Recording build status inside it would mix the
specification with the build log, duplicate that log across 59 items, and make the spec's diffs
unreadable. So the plan keeps its status line and a pointer, and the detail lives here.

This is the same split `/execute` already makes: the ledger is the record, and everything
countable is derived from it rather than asserted beside it.

**What belongs here:** what landed, under which commit, how it was verified, and **where the
implementation departed from what the plan specified** — that last one is the reason this file is
worth keeping. A plan written before the code is read is a plan that will be wrong somewhere, and
the places it was wrong are what the next phase needs to know.

---

## Phase 1 — Fix what is broken today. No schema change.

Plan order: `23a` · `39` · `54` · `55` · `42` · `21` · `9`

| Item | Status | Commit |
|---|---|---|
| **23a** — `schema_version` mismatch | **Landed** 2026-08-25 | `78b8104` |
| **60** — `execute-layer` hand-maintains a derived file | Not started | — |
| **39** — validate references leaving the PRD | Not started | — |
| **54** — a working directory for verification | Not started | — |
| **55** — the ledger states what it verified | Not started | — |
| **42** — rename with a checkable postcondition | Not started | — |
| **21** — runtime test for P1, and the authoring baseline | Not started | — |
| **9** — `/prd`'s prose guards become scripts | Not started | — |

Item 60 is new; it was found while doing 23a and is specified in the plan alongside P38.

**Suite:** 39 checks passing at branch point → **40** after 23a.

---

## 23a — `state-schema.md` documented a file nothing has written since 2.0

**Commit:** `78b8104` · **Addresses:** P28 · **Files:**
`skills/execute/references/state-schema.md`, `tests/test_toolchain.py`

### What the plan specified

> *"`execute-state.json`'s documented `schema_version` must equal what `write-state.py` writes —
> today they are `2.0` and `3.0`."*

### What was actually wrong

The version string was the visible half, and fixing only it would have produced a document whose
number agreed with the producer while everything under the number still described a different
file. The reference documented, as current:

- root fields `options`, `current_layer`, `current_batch`, `worktree_dir`, `worktrees`,
  `context_update` — none of which the script writes
- per-task `commits[]`, `errors[]`, `retry_feedback[]`, `worktree_path`, `branch`
- a task status enum of eight values where the script writes four, including `completed` where
  the script writes `merged`
- `metrics.elapsed_seconds` and `metrics.total_retries`, both removed
- an `init_state` / `save_state` pair showing the file being assembled and written **by hand**,
  which is the one thing F21 exists to forbid

### Direction of the fix, and why it was not in doubt

`write-state.py` is the producer, and `skills/execute/SKILL.md` §State Initialization already
describes the 3.0 behaviour correctly. Two of the three documents agreed; the reference was the
outlier. The reference was rewritten.

### How the new content was produced

`write-state.py` was run against a throwaway three-task fixture — one task merged with a real
commit, one failed, one pending — and **its output was pasted into the reference** rather than
transcribed from reading the script. A hand-copied schema is how the previous one drifted.

### Deviation from the plan

**Larger than specified, deliberately.** The plan called this a version-string mismatch; it was a
whole-document rewrite (458 → 260 lines). The narrow fix would have satisfied the plan's wording
and left the defect in place.

One section was added that the plan did not ask for: **What 2.0 Carried and 3.0 Does Not**, a
table of the removed fields and why each went. A reader holding a 2.0 file otherwise has no way to
tell a renamed field from a deleted one.

### Verification

New check, `state-schema.md documents the file write-state.py actually writes`, `finding="P28"`,
at `tests/test_toolchain.py`. It compares the two mechanically rather than by reading, because
reading is what missed this across three schema revisions:

- the writer's `state = {...}` literal is parsed out of the script with `ast`
- the reference's example is parsed with `json`
- the **root key sets must match**, in both directions
- every version the reference states — in the prose *and* in the example — must equal the
  writer's

**Confirmed against the pre-fix file**, where it fails naming all eight disagreeing fields:

```
written, undocumented: ['derived_from', 'missing_commits']
documented, never written: ['worktree_dir', 'current_layer', 'current_batch',
                            'options', 'worktrees', 'context_update']
```

A check that has never been seen to fail is not a check. This one has.

### Found while doing it, not fixed here

`skills/execute-layer/SKILL.md` still instructs hand-writing `current_layer`, `current_batch` and
per-layer counters into the state file, and iterates `merge_queue` for a `"ready"` status that
3.0 never emits. Written up as **P38 / item 60** in the plan.
