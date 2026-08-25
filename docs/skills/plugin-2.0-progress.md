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
| **60** — `execute-layer` hand-maintains a derived file | **Landed** 2026-08-25 | `e00c3ae` |
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

### Found while doing it

`skills/execute-layer/SKILL.md` reads and writes the 2.0 shape of the file 23a had just
documented. Written up as **P38 / item 60** and fixed next; see below.

---

## 60 — `execute-layer` maintained a file that is rebuilt from git each time

**Commit:** `e00c3ae` · **Addresses:** P38 · **Files:** `skills/execute-layer/SKILL.md`,
`tests/test_toolchain.py`

### Why this exists at all

It is not in the plan's original 59. It was found by doing 23a — writing down what
`write-state.py` actually emits made it obvious that a consumer was reading a different
document — and was added to the plan as P38 / item 60 afterwards, in Phase 1 beside 23a.

### The live half

**5d could not merge anything.** It iterated `merge_queue` looking for `status == "ready"`, and
`write-state.py` derives that list from the ledger *after* each merge, so every entry is
`"merged"` by construction. A loop looking for `"ready"` matches nothing, ever. The merge set is
5c's `verified` array, which is the only thing that knows what the batch just proved.

**Step 2 took `completed` from the state file** — the one field Step 3 forbids taking from there,
four lines later, because over-reporting completion starts a task before its dependency landed.

### The quieter half

Steps 4, 5a and 6 wrote `current_layer`, `current_batch` and per-layer counters. Those fields do
not exist in 3.0, and a hand-written field is **erased rather than merged**, because the script
rebuilds the document instead of patching it. No corruption — but instructions that teach a model
the file is hand-maintained, which is how it became hand-maintained four times.

### What made it survive

Two things, both worth carrying forward:

1. **The skill already stated the correct rule**, at line 349: *"There is no queue to maintain in
   a file… writing one by hand would make that untrue."* It was added without removing the four
   blocks it contradicts, so the document said both. Same shape as the nine the plan found in
   itself — the fix written, the thing it replaced left in place.
2. **F21 had a check for exactly this and it did not fire.** The mutation pattern was an allowlist
   of seven field names, and `state["current_batch"]` was not among them. Now widened to any key:
   the finding is that the whole file is derived, which is true of fields nobody has invented yet.

### Deviation from the plan

None — the item was written to match what was done, since it was found during implementation
rather than specified before it. Recorded here so the plan is not read as having predicted it.

### Verification

`python tests/test_toolchain.py` — 40 checks, 0 failed.

The widened F21 was **run against the unfixed file** and fails there, naming the line:

```
FAIL  execute-state.json is written by a script, never by hand   [F21]
      mutate execute-state.json by hand; call write-state.py instead:
      skills/execute-layer/SKILL.md:124: state["current_batch"] = batch_number
```

*A first attempt at this proof was worthless and is recorded because it is the failure mode this
whole phase is about:* the `git stash` that was supposed to restore the unfixed file used the
wrong flag order, did nothing, and the suite reported **pass** — against the already-fixed file.
A green result whose mechanism has not been shown is not a result.
