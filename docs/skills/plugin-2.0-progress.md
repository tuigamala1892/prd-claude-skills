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
| **39** — validate references leaving the PRD | **Landed** 2026-08-25, *narrowed* | `e112ec8` |
| **54** — a working directory for verification | **Landed** 2026-08-25 | `fce02c9` |
| **55** — the ledger states what it verified | **Landed** 2026-08-25 | `2b12720` |
| **42** — rename with a checkable postcondition | Not started | — |
| **21** — runtime test for P1, and the authoring baseline | Not started | — |
| **9** — `/prd`'s prose guards become scripts | Not started | — |

Item 60 is new; it was found while doing 23a and is specified in the plan alongside P38.

**Suite:** 39 checks at branch point → **40** (23a) → **42** (39) → **43** (54) → **45** (55).

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

---

## 39 — 180 references that left the PRD and were never followed

**Commit:** `e112ec8` · **Addresses:** P24 · **Files:**
`skills/breakdown/scripts/check-references.py` (new), `skills/breakdown/SKILL.md`,
`commands/prd.md`, `tests/test_toolchain.py`

### What was built

`check-references.py <prd-dir> [--adr-dir DIR] [--questions FILE] [--strict] [--quiet]`.

| Reference | Resolves against | Dangling → | Stale → |
|---|---|---|---|
| `ADR-NNN` | the decision directory | exit 1 | reported with its successor |
| `OQ-NNN` | the open-questions register | exit 1 | reported with what resolved it |
| `**Drives:**` links | the feature the record names | exit 1 | — |

**Superseded and resolved do not refuse.** Both artefacts still exist; a feature citing one is a
judgement call, not a defect. `--strict` promotes them for a caller that wants it.

**Nothing is ever written.** The register is human-maintained and outlives any one PRD — item
39's own decision, restated in the script so the next reader does not "fix" it.

### Deviation from the plan: narrowed, and the number is stated

Item 39 says *"every `ADR-NNN`, `OQ-NNN` and principle citation resolves."* **Principle citations
are not checked** — 10 of the corpus's 190 references. A principle has nowhere to live until item
28 gives `architecture.md` its `<principles>` section (item 37 routes them there explicitly), so
there is no target to resolve against. Validating against a file that does not exist yet is the
defect this plan is about.

So: **180 of 190 covered, 10 deferred to Phase 3.** Written into the script's docstring under
*WHAT IS NOT CHECKED, AND WHY* rather than left as a silent gap — a validator quietly skipping a
class of input is worse than one that says it skips it.

### The other deviation: it was wired in, which item 39 does not mention

A script nothing invokes is the producer-without-a-reader this whole plan exists to describe, so
shipping one would have been self-refuting. Two callers, and they are deliberately asymmetric —
§4.3's rule that consumer-side validation refuses and producer-side is early warning:

- **`/breakdown` Phase 1, step 9** — runs it before Phase 2 reads the PRD, and **stops** on exit 1.
- **`/prd` Phase 6** — reports and offers to fix, while the author who knows the answer is still
  in the conversation.

`/prd` invokes it as `${CLAUDE_PLUGIN_ROOT}/skills/.../check-references.py {prd_dir}`, passing the
path **as an argument**: OQ1's probe established that the variable is expanded where the command
is written and is *not* exported to the spawned shell. A check asserts that exact string, because
the failure mode is silent — a script that cannot find its own path just does not run.

### Verification

Two checks, both `finding="P24"`, and the first is **the suite's first that runs a script rather
than reading one**. That is safe in a way running a skill is not: this one reads a directory and
returns an exit code, and creates nothing. It is also necessary — *"the script mentions ADR"* is a
property every useless validator also has.

It builds a temp tree with three planted dangling references (a missing record, a missing
question, a `**Drives:**` link to a deleted feature), one superseded record, one resolved
question, and asserts: exit 1; each dangling reference named as written with a file and line; the
supersession and resolution reported but not refusing; then repairs the three and asserts exit 0
on the same tree; then asserts that citations with **no register found at all** are an error
naming the flag to pass, rather than a quiet pass.

**Mutation-tested.** A build of the script returning 0 instead of 1 on errors makes the check fail
with *"a PRD with three dangling references exited 0"*. The check has been watched failing for the
reason it exists.

### A defect in my own first output, worth recording

The first run reported `ADR-7` for a citation written `ADR-007` — leading zeros were being
stripped for matching and then reused for display, sending a reader looking for a string that is
not in the file. Fixed by keeping the as-written form beside the match key; there is now an
assertion for it.

---

## 54 — verification ran from the repository root and nowhere else

**Commit:** `fce02c9` · **Addresses:** P36 (monorepo half) · **Files:**
`skills/breakdown/references/task-format-spec.md`, `skills/execute-verify/SKILL.md`,
`agents/task-implementer.md`, `skills/breakdown-generate-tasks/SKILL.md`,
`tests/test_toolchain.py`

### What was built

`<meta><cwd>`, optional, relative to the worktree root. **Absent, everything runs at the root
exactly as before** — no existing task changes behaviour. Present, `execute-verify` and the
implementer run commands from there, and the task writes `pytest tests/test_invoices.py` rather
than `cd packages/billing && pytest tests/test_invoices.py`.

### Three things the plan did not specify, and why each was needed

**A guard.** The item says "relative to the worktree root" as a comment in an XML sample.
Enforced by prose, that is P16's failure mode exactly. An absolute path, a drive letter or any
`..` is now refused — including `packages/../packages/billing`, which *would* resolve back
inside. Conservative on purpose: nothing is lost by making an author write the path they meant,
and a verification that passes outside the worktree has proved something about files no merge
will carry.

**A producer.** The item names two readers and no writer, so the element would have shipped
read-only — the exact defect this plan exists to describe. `breakdown-generate-tasks` emits it
when the source names a component, and is explicitly told **not** to infer it from
`<files-to-create>`: two files sharing a parent directory is not evidence that the parent is where
the test runner lives, and a wrong `<cwd>` fails verification in a way that looks like broken
code. Item 53's `<repo-structure>monorepo</repo-structure>` is what will make it systematic.

**`cwd` in the verification result.** A passing run now says where it ran. A step that fails in
the wrong directory looks exactly like a step that fails in the right one.

### Verification

The check **extracts the guard from `execute-verify/SKILL.md` and runs it under `sh`** against
seven inputs, so what is tested is the text that shipped rather than a copy of it. `sh` is already
a hard dependency of the toolchain — `preflight.sh`, `create-worktree.sh` and `merge-task.sh` are
how `/execute` works — so a box without it cannot run the pipeline either.

It also asserts the element has a producer *and* readers, in both directions. That is item 23's
rule applied at the moment of writing rather than in an audit afterwards.

### The check's first version was wrong, and it passed

Removing the escape branch from the guard **did not fail the test**. The escaping case was
`../../etc`, which does not exist under a temp worktree, so `cd` failed on its own and the
fallback refusal — *"does not exist"* — satisfied an assertion that only looked for `REFUSED`.
The test could not tell a guard from a coincidence.

Fixed by placing a real `outside/` directory beside the worktree and pointing the escaping case at
it, and by asserting the **specific** refusal reason rather than the word `REFUSED`. Both mutants
now fail, and the escape one reports `LANDED:/tmp/.../outside` — the escape it was supposed to
prevent, printed.

*This is the second false pass in this phase from the same cause: a green result whose mechanism
had not been shown. The first was a `git stash` that silently did nothing (item 60).*

### A process note worth keeping

Mutation-testing an **uncommitted** file must not be undone with `git checkout -- <file>`. Doing
that here reverted `execute-verify/SKILL.md` to HEAD and discarded the item's real edits along
with the mutation; they had to be rewritten. Copy the file aside and copy it back.

---

## 55 — the ledger recorded *that* a task was verified, not *what* was verified

**Commit:** `2b12720` · **Addresses:** P37 · **Files:**
`skills/execute-merge/scripts/record-task.sh`, `skills/execute-merge/SKILL.md`,
`skills/execute/SKILL.md`, `tests/test_toolchain.py`

### What changed

`"verified":true` → `"verified":"task-steps"`. One string.

What `execute-verify` actually runs is the task's own `<verification>` block, in its worktree, by
a separate agent on a different model — real verification, and more than the field does. The
boolean invited the wider reading, and in any project with a build pipeline a task that merges
green and breaks CI was indistinguishable from one that did not.

### Not a schema break, and checked rather than assumed

Nothing read the old field. `ledger-status.sh` computes its own `verified` **count** from git
reachability — a different quantity that happens to share the word — and `write-state.py` reads
`task_id`, `commit`, `at` and `attempts`. Grepped for readers before changing the value, because
a field with no reader and a field with a reader you did not find look identical from the writer.

### The half that reaches a person

The report is where the implication actually lands, so the completion block now carries:

```
Total: 44/44 tasks completed
Verified: each task's own declared steps, in its worktree, before merge
Not run: the project's build or test suite -- that belongs to CI
```

with a note that both added lines are load-bearing and must not be trimmed as boilerplate.
Running the project's pipeline stays out of scope — `/execute` has no business owning it. **Not
implying it ran is a different question**, and this is the answer to that one.

### Verification

The check **runs `record-task.sh`** against a real commit in a temp repository and reads the bytes
it appended, rather than grepping the script. It also asserts the rule the new field leans on: a
commit that does not exist is still refused, and nothing is appended. A *named* verification of a
merge that never happened would be worse than the boolean it replaced.

**Three mutants fail it**, and the third is the one that matters:

| Mutant | Caught by |
|---|---|
| `"verified":true` | the static assertion |
| report lines removed | the second check |
| `"verified":"everything"` | **the runtime assertion** — it passes the static one |

That third mutant is why the behavioural half is worth its cost: it proves the runtime assertion
is doing work rather than sitting dead behind the grep that precedes it.

### Deviation from the plan

None of substance. The item specified the field and the wording; the report lines and the
refuses-a-missing-commit assertion are the same idea carried to where it is read.
