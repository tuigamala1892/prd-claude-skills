# Plugin 2.0 — Implementation Ledger

**Companion to** [`plugin-2.0-plan.md`](plugin-2.0-plan.md), which stays a specification. This
file is the record of what has actually landed against it.

**Branches:** `phase-1-live-defects` (merged 2026-08-26), `phase-2-make-it-testable`
(merged 2026-08-26), then `phase-3-architecture-artefact`
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
| **42** — rename with a checkable postcondition | **Landed** 2026-08-25 | `083c70e` |
| **21** — runtime test for P1, and the authoring baseline | **Landed** 2026-08-26, *result is UNDECIDABLE by design* | `14545f9` |
| **9** — `/prd`'s prose guards become scripts | **Landed** 2026-08-26, *Phase 1 share* | `6c7825b` |

Item 60 is new; it was found while doing 23a and is specified in the plan alongside P38.

**Phase 1 is complete.** Eight items, 39 → 49 regression checks, every item verified by running
something rather than reading it. What the phase cost in surprises is in each entry below; the
three that generalise are collected in *What Phase 1 taught* at the end of this file.

**Suite:** 39 checks at branch point → **40** (23a) → **42** (39) → **43** (54) → **45** (55) → **46** (42) → **48** (21) → **49** (9).

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

---

## 42 — a rename that finishes, or a PRD exactly as it was found

**Commit:** `083c70e` · **Addresses:** P27 · **Files:**
`skills/breakdown/scripts/rename-feature.py` (new), `commands/prd.md`, `tests/test_toolchain.py`

**This was the phase's designated rehearsal** — the plan calls it *"the cheapest possible rehearsal
of item 41's postcondition machinery, on 8 files rather than 64… if the pattern is awkward here it
will be far worse there."* It was awkward here, in a specific and useful way. See *What the
rehearsal found*.

### What was built

`rename-feature.py <prd-dir> <old> <new> [--dry-run]`, wired to `/prd --rename`. It rewrites the
reference shapes, then **asserts** the three postconditions rather than assuming them: nothing
resolves to the old slug, no file exists under it, the new slug appears in exactly one index entry
and one feature file.

### Two corrections to the item, both found by running it

**The item lists five sites; there are six.** `what-next.md` carries
`ref="features/{slug}.md"` and was not in the list. Found by running the operation against the
§5.1 fixture — not by re-reading the item, which had been read several times.

**One of the five was not a reference.** *"The index entry's content"* is prose: `<name>` and
`<summary>` may mention the old slug in a sentence. Prose mentions are now **reported with file
and line and never rewritten** — a script that edits English is a worse failure than a stale
sentence. Same refuses/reports split item 39 draws.

Both corrections are in the plan.

### What the rehearsal found — the reason this item exists

The first working version asserted the postconditions **after** renaming the file and rewriting
four others. A failure therefore produced *a half-done rename plus an accurate message*, which is
worse than not starting: the operator is told it did not finish and has to work out how far it
got.

Now it snapshots every file it will touch, restores them all when a postcondition fails, and
**asserts the restore** — because an unverified undo is the same class of claim as the unverified
rename this script exists to replace. If the rollback is itself incomplete it says
`ROLLBACK INCOMPLETE` and names what to check, rather than claiming nothing happened.

**Carry this into item 41.** Its partial-completion contract is *per-file atomic*, which is this
property at 64 files instead of 8. Learning it on a rename cost one afternoon; learning it on the
EARS migration would have cost a corpus.

### Verification

The check copies the §5.1 fixture, adds the two inbound link shapes the corpus has and the fixture
does not, plus a prose mention, and then asserts the three postconditions **from the outside** —
walking the tree itself rather than trusting the script's report of itself. It also asserts
`what-next.md` was carried, and that the prose sentence was left alone.

Then the rollback: a second copy with two files claiming one slug, hashed before and after, and
**every byte must match**. Three mutants fail the check — rollback removed, a reference shape
removed, and a version that rewrites prose.

### Note on where the script lives

`skills/breakdown/scripts/` now holds two PRD-artefact tools (`check-references.py`,
`rename-feature.py`), one of which `/prd` calls and `/breakdown` does not. That is slightly wrong
and deliberately not fixed mid-phase: item 22's `check-artefacts.py` is where these consolidate,
and inventing a directory now would mean moving them twice.

---

## 21 — the runtime probe, and what it actually established

**Commits:** `5a4c1b4`, `2630cb1`, `65c8a63`, `14545f9` · **Addresses:** P1 · **Files:**
`tests/fixture/prd/staff-service/` (new), `tests/probe-p1.py` (new), `tests/test_toolchain.py`

### The result

Run 3, on the decontaminated fixture: **17 tasks across four layers** before a 45-minute
timeout. No task is named or aimed at the rejected feature. Thirteen mention it in their
requirements and **every one is a negative instruction** — *"Do NOT add a telemetry table … Quokka
telemetry is wont-have and is excluded from this release."*

The decision artefacts show the path it took:

| Artefact | What it did with the won't-have |
|---|---|
| `analysis.json` | Carried it **in full** — description, both criteria — and derived a `TelemetryOptOut` model and a `/telemetry` endpoint from it, each tagged `wont-have` |
| `layer_plan.json` | Dropped it, under `"excluded"` and `"features_excluded"` — **keys that exist in no schema in this repository** |

**So `/breakdown` did not build the rejected feature, and nothing filtered it either.** The model
read `priority="wont-have"`, decided on its own, and invented JSON keys to record the decision.
P1's *mechanism* claim stands exactly as written — no consumer reads priority — while P1's
predicted *consequence* did not occur, because a model declined work the toolchain would have
allowed. That is a quieter failure mode than the one P1 predicts, and it is item 13's real case:
make the exclusion **enforced** rather than hoped for.

### The instrument was wrong three times, each differently

This is the part worth carrying forward.

| Attempt | Reported | Why it was wrong |
|---|---|---|
| Whole-file match | **13 of 17 derive from the won't-have** | Counted `assert 'telemetry' not in s`. It could not tell *builds X* from *proves X absent*, and failed in the confident direction |
| Name + objective | **0 attributions, every tier** | Generation renames to domain language — the export task is `GET /export`, not `walrus`. The feature's own words do not survive into the task |
| Either, for several iterations | nothing matched at all | A heredoc collapsed `\b` into a literal `0x08` byte, silently disabling both word-boundary anchors. I was debugging the layer above the defect |

**What that establishes is worth more than the original question.** String-match attribution
**cannot decide P1 on today's task format** — both failure directions were observed on a single
real run. That is **item 16 measured**: until a task carries `<source-feature>`, this question has
no runtime answer. The grader therefore exits `3 UNDECIDABLE` with its evidence rather than
emitting a number nobody should trust.

### Three probe defects the runs exposed, in order

1. **No `--add-dir`** (run 1). The workspace comes from `mkdtemp()`, so it can never be
   pre-authorised; every read and `mkdir` was refused. **The agent under test diagnosed this
   itself**, named the argv line, and declined to hand back a result it could not vouch for.
2. **A timeout discarded the run** (run 2). It killed a 25-minute `/breakdown` that had already
   written nine tasks, a layer plan and an analysis, and threw all of it away with the transcript.
3. **Root discovery keyed off `manifest.json`** (run 3), which `/breakdown` writes in its last
   phase — so it reported "no task XML anywhere" against a workspace holding 17 tasks. A
   truncated run is precisely the run it has to survive.

### The fixture explained the experiment to the subject

Run 2 came back clean and was worthless. `analysis.json` wrote back my own commentary:

```
"feature_naming": "Deliberately obscure animal names (zebra, walrus, narwhal, quokka)
 chosen to prevent accidental coincidental matching."
"wont_have_handling": "... must not appear in generated tasks. It is fully specified to
 ensure /breakdown cannot skip it for being incomplete."
```

The overview named the finding under test; the won't-have carried *"**This feature is rejected and
must not be built**"*. **A fixture that describes the experiment is part of the experiment.**

Rewritten as a plain PRD for a plain product, `tier-probe` renamed to `staff-service` so even the
slug stops signalling, and rejection declared by `<priority>wont-have</priority>` and nothing else.
The check had the assertion *backwards* — it used to **require** "must not be built" in the
won't-have. It now forbids that and five similar instructions, requires the won't-have to be no
thinner than the thinnest other feature, and scans every PRD file for words describing the
experiment.

### Deviation from the plan

**The authoring measure is half-delivered and says so.** `--baseline` reports size — 394 words, 8
criteria, 64 elements across four features — which is the instrument the after-measurement compares
against. *"Is this still tolerable to write?"* is a stopwatch against a person and no script can
take it. Recorded in the plan's item 21 rather than reported as done.

**And a datum for item 18:** a **four-feature** PRD did not finish `/breakdown` in 45 minutes. P5
says `analyze-prd` is handed 174k tokens of corpus; this is what the small end already costs.

---

## 9 — `/prd`'s two remaining prose guards become exit codes

**Commit:** `6c7825b` · **Addresses:** P16 (and F3's other half) · **Files:**
`skills/breakdown/scripts/check-writable.py` (new), `skills/breakdown/scripts/list-prds.py`
(new), `commands/prd.md`, `tests/test_toolchain.py`

### Scope

Item 9 names three guards: the Phase 8 pre-write check, the status marker, and item 6's checks.
**The first two are here; item 6 is a Phase 5 item** and its checks land with it.

### What replaced what

| Was | Is | Why it needed to be a program |
|---|---|---|
| `test -e docs/prd/{slug}/index.md && echo EXISTS`, then four paragraphs | `check-writable.py` | Lists every file at risk with size and age, and **refuses**. `--resume` is the only way past and must be stated — the script cannot tell a resume from a slug collision, only the caller can, and a guard whose safe path is the default is a guard taken by accident |
| `ls -d docs/prd/*/` and a two-file `grep -l` | `list-prds.py` | Reports **which file** declares each status — F3's other half, since resume once looked only in `what-next.md` while the PRD carried the marker in `index.md` |

`list-prds.py` names two conditions that previously had no name and no exit code:

- **`DISAGREE`** — `index.md` and `what-next.md` declare different statuses, so whether a resume
  finds the PRD depends on which file it reads first. F3 restated as a data defect.
- **`NO MARKER`** — neither declares one, so `--resume` cannot see the PRD and a new one on that
  slug would replace it without warning.

### The part worth keeping: the F3 check had to be rewritten, not extended

Four of its assertions were pinned to the exact prose this item deletes — the `ls -d`, the grep
covering both filenames, Phase 8's `test -e`, and its `**stop and ask**`. Removing the prose broke
the check that existed to protect the behaviour, **while the behaviour got stronger**.

That is P16 one level up: *a check written against a paragraph passes only while the paragraph is
there.* It now asserts the mechanism — that `list-prds.py` itself reads both marker locations, and
that Phase 8 runs the guard and calls its exit code binding. Those survive a rewording; the old
ones did not survive an improvement.

### Verification

Both scripts are **run** against a temp tree holding a live PRD with features, a fresh slug, a
self-contradicting PRD, a PRD with no marker, and one declaring its status in a single file (the
older layout, which must *not* be reported as a defect).

Four mutants fail the check: a guard returning 0, one that resumes unconditionally, a `--check`
that never fails, and restoring the old `test -e` prose to `/prd`.

### Deviation from the plan

None. Item 9's own note — pass the plugin path as an argument, never write a bare relative path —
was already settled by OQ1's probe and is followed: both invocations are
`${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/…` with the target passed as an argument.

---

## Phase 2 — Make the rest testable.

Plan order: `18` · `43` · `52` · `53`, on branch `phase-2-make-it-testable`.

| Item | Status | Commit |
|---|---|---|
| **/execute smoke test** — Phase 1's execute-path changes, exercised | **Done** 2026-08-26 | `b54135f` |
| **18** — per-feature analysis + size refusal | **Landed** 2026-08-26 | `8129cdb` |
| **43** — a fixture per schema version | **Landed** 2026-08-26, *scaffolding; schema-2 arrives with item 1* | `f512ece` |
| **52** — a context check at `/prd` initialization | **Landed** 2026-08-26 | `ae38b83` |
| **53** — declare `<repo-structure>`; refuse multi-repo early | **Landed** 2026-08-26 | `1a4184e` |

### What Phase 2 delivered, and what it deliberately did not

**Phase 2 is complete.** Four items plus the smoke test, 49 → 56 regression checks and one
`expect_fail` that names the next thing to build.

| Item | The refusal or scaffold it added |
|---|---|
| **18** | `check-prd-size.py` — per **prompt**, not per corpus, so a large PRD split into small prompts passes and a single oversized one does not |
| **43** | Versioned fixture directories + `SCHEMAS.json`, so Phase 4's schema items land by *adding* rather than by breaking the suite in the same commit |
| **52** | `check-project-context.py` — `/prd` reads `PROJECT.md` before asking what the stack should be |
| **53** | `check-repo-structure.py` — `multi-repo` refused in Phase 1, with what would be needed |

**Three of the four are refusals with a stated reason**, which is the shape Phase 1 converged on:
an exit code, a named cause, and text saying what to do instead. The fourth is scaffolding whose
whole purpose is to make a later item cheap.

### What item 43 does not include, and why that is the item's own answer

No `schema-2` fixture. Item 43's text says Phase 4's schema items each land **by adding** their
change to a schema-2 fixture beside schema-1 — so authoring it here would mean inventing the
target schema ahead of items 1, 33 and 34, which specify it.

What exists instead is the scaffolding plus a check marked `expect_fail="item 1"` that reports
KNOWN today and **FIXED** the moment a second schema is registered — verified by registering one
and watching it flip. The suite therefore refuses to let schema-2 arrive quietly.

**One thing is owed with it.** Rule 2 — a non-current fixture is frozen — is enforced today by a
`"frozen": false` flag and prose, not by content hashes. There is no frozen fixture yet to hash.
When schema-1 becomes frozen that check needs writing, or rule 2 is exactly the prose guard P16
is about. Recorded in `SCHEMAS.json` and here rather than left to be noticed.

### The correction Phase 2 forced on Phase 1's reasoning

I twice cited the 45-minute `/breakdown` run from item 21 as fresh evidence for item 18.
**Measuring the fixtures disproved it:**

```
link-shelf     4 prompts, whole corpus  2,195 tokens
staff-service  5 prompts, whole corpus  1,758 tokens
```

Those are ~2k tokens against a 200k window. Nothing there stresses context, so the slow and
truncated runs had a different cause — most plausibly the per-layer generate → review → retry
loop. **P5 is still real and still Blocking for the 174k corpus; the runtime evidence I offered
for it was not evidence.** Item 18 was built on the static argument, which holds.

### The lesson Phase 2 added to Phase 1's three

**Checks pinned to formatting break when the formatting changes.** Three prose assertions failed
this phase on presentation rather than content: a phrase split by a line wrap, and twice on
backticks inside the matched phrase. Worse, one of them forbade *documenting the history it
enforced* — it matched the words "full PRD content" anywhere, so it failed on the sentence
quoting the old instruction to explain the change.

Both are the same error as Phase 1's second lesson, one level down: **assert the meaning, not the
presentation.** There is now a `prose()` helper that collapses whitespace and strips markdown
emphasis, and item 18's check tests for imperative grammar rather than for a phrase.

### The smoke test, and what it took to run at all

Phase 1 changed seven files on the execute path and nothing had run the pipeline. It has now.

**Result: 0 failures.** `/breakdown` produced 13 tasks across four layers with a manifest carrying
`toolchain_version: 2.0.0`; `/execute --task L0-001` then implemented, verified and merged it. The
raw artefacts, read directly rather than through the checker:

```
ledger  {"task_id":"L0-001","commit":"0790495...","attempts":1,"verified":"task-steps"}

git     *   0790495 Merge worktree-L0-001: Create project skeleton and dependency config
        |\
        | * dca9a16 [L0-001] Create project skeleton and dependency config
        |/
        * 868090f Initial commit

state   schema 3.0, 17 root fields matching write-state.py's own dict literal
```

That confirms **item 55** (the ledger names what it verified), **item 60** (a merge happened at
all — the loop it replaced scanned `merge_queue` for `"ready"`, which `write-state.py` never
writes, so a run following it merges nothing), and **item 23a** at runtime rather than in docs.
**Item 54**'s `<cwd>` is absent from this task, so the default branch — worktree root, behaviour
unchanged — is the one exercised, which is the branch that matters for regression.

Afterwards: `git status` clean in the checkout, and `setup_fixture.py --verify` PASS with root
commit `868090f` intact.

### Three attempts, and two of them were about permissions rather than the toolchain

**1. `--plugin-dir` loads a plugin; it does not make the plugin readable.** `/breakdown` stopped in
Phase 1 because `resolve-output.sh`, `check-references.py` and `build-manifest.py` were outside the
session's allowed directories. The agent verified both *guard* scripts would have passed by hand,
refused to substitute for the one *generator* — *"hand-writing it would produce an artifact that
looks complete and is knowably not"* — and removed the directory it had created. Fixed in
`setup_fixture.py`'s printed sequence and in `CLAUDE.md`.

**2. A permission failure was reported as a missing repository.** `/execute` refused with *"the
target is not a git repository"* while `app/.git` existed and its root commit was intact. Every
`git` and `sh` call had been rejected under `acceptEdits`, so it fell back to `Glob`, which does
not match hidden directories, got nothing, and stated the repository was absent — then speculated
from a stale settings entry that something had deleted it.

*Stopping was right; the stated reason was not.* This is the phase's own lesson arriving from
outside: **a negative result whose instrument has not been checked is not a result.** The fixture's
`--verify` settles the question in two seconds and was not consulted.

**3. `bypassPermissions`, with the checkout committed first** so any stray edit would show in
`git status`, the target being a throwaway fixture with no remote and a recorded root commit, and
the prompt bounding the agent to the workspace. Both after-checks were run, not assumed.

---

## Phase 3 — The architecture artefact. One piece of work.

Plan order: `25` + `28` + `37` + `51` + `31` + `56` + `26` + `57`, on branch
`phase-3-architecture-artefact`. The plan insists these are one item because splitting them means
designing `architecture.md` four times.

| Item | Status | Commit |
|---|---|---|
| **25 + 28 + 37** — the artefact, its guard, its readers | **Landed** 2026-08-26 | `_` |
| **51** — a Design phase in `/prd`, the producer | **Landed** 2026-08-26 | `_` |
| **31** — derive the layer set from content, both paths | not started | |
| **56** — enforce `<banned>` and `<task-limits>` | not started | |
| **26** — seed PROJECT.md on greenfield | not started | |
| **57** — impact analysis reports contracts, not APIs | not started | |

---

## 25 + 28 + 37 — the file that makes the pipeline a parameter

**Addresses:** P11, P17, P18, P35, and review finding R8 · **Files:**
`skills/breakdown/references/architecture-format.md` (new),
`skills/breakdown/scripts/check-architecture.py` (new), `skills/breakdown/SKILL.md`,
`skills/breakdown-plan-layers/SKILL.md`, `skills/breakdown-analyze-prd/SKILL.md`,
`skills/breakdown-generate-tasks/SKILL.md`, `skills/breakdown/references/task-format-spec.md`,
`skills/breakdown/references/review-criteria.md`, `skills/breakdown/scripts/check-references.py`,
`skills/breakdown/scripts/check-repo-structure.py`, `skills/execute-batch/SKILL.md`,
`skills/execute/scripts/check-project-md.py`, `skills/crd/references/project-format.md`,
`tests/test_toolchain.py`

### Why the three are one commit

25 defines the artefact, 28 fills it, 37 says what belongs in which half. Landing 25 alone would
have shipped a file with a schema nothing fills; landing 28 without 37 would have blurred
`<rules>` and `<principles>`, which is the blur item 37 exists to prevent — something written as
a principle when it needed to be a constraint is weighed rather than obeyed, while the operator
believes it is in force.

### What was built

`architecture.md` at the project root, beside `PROJECT.md`, prescriptive where that file is
descriptive. `<rules>` is what the toolchain **obeys**; `<principles>` is what a reader is
**told**; registries are root children of neither, so item 26's seeding stays a subtree copy
rather than a transform.

`check-architecture.py` refuses twelve classes of broken rule file and exits 0 on an absent one.
**That asymmetry is the item**, and it is stated in the script rather than left implicit: a rule
file that is silently ignored is worse than none, because the rule is not in force and the
operator believes it is.

### Deviations from the plan

**Three, and the first two are defects the plan would have created.**

**1. `<repo-structure>` would have had two homes.** Item 28 puts it in `<rules>`; item 53 already
shipped reading it from the PRD document. That is P8's shape — one value stored twice — created
by the plan rather than found in the code. Resolved by §4.1's rule, which says choose rather than
synchronise: `architecture.md` owns it because layout is a property of the codebase, the document
is the fallback for the projects that have no rule file, and a **disagreement is reported, not
refused**. Refusing would break a valid repository the first time someone writes the newer file.

**2. `<testing default=>` is a four-reader change, not three.** The plan names `generate-tasks`,
`review-tasks` and `execute-batch`. But `task-format-spec.md` is what marks
`<test-requirements>` a *required section*, so a project declaring `default="none"` with only
three of the four changed still fails every task at batch review and never reaches execution.
P18 says this in its own prose — *"an opinion enforced in more places than it is documented is
harder to make overridable"* — and then the remediation item counted the places wrong.

**3. Item 39's deferred tenth is closed here.** `check-references.py` shipped in Phase 1 checking
180 of the corpus's 190 references and saying so, because a principle had nowhere to resolve
against. `<principles>` now exists, so `P-NNN` citations are checked and the exclusion is deleted
rather than left standing.

**The hyphen in `P-NNN` is load-bearing**, and this is the kind of thing that is obvious only
once written down: item 34's criterion priorities are `P0`, `P1` and `P2`. A citation pattern
without the hyphen reports a dangling principle on every prioritised criterion — 550 of them in
the corpus — which is a validator that has to be switched off to get any work done. There is an
assertion for it.

### R8, reproduced before it was fixed

`check-project-md.py` hard-required `api-registry` **and** `schema-registry`. That pair is REST
plus relational: the toolchain re-vendoring its own architecture one level below where item 28
frees it, so a CLI project seeded with only a `<command-registry>` failed a guard it should pass.

Confirmed by running the pre-fix script from `git show HEAD:` against a CLI fixture, where it
refuses naming both absent registries. It now requires **at least one**, which keeps the proxy
the two names stood for — *a consumer can read this* — without mandating a shape.

### The part worth carrying forward: two of my five checks were decorative

The suite went 56 → 61 and every check passed. Mutation found that **two of the five did no
work**:

| Mutant | Why it survived |
|---|---|
| plan-layers stops honouring the declared graph | the check asserted the file *mentions* `architecture.md`; the phrase appears five times, so deleting the branch left the word behind |
| execute-batch stops honouring `default="none"` | the check asserted the phrase `testing default="none"`, which survived inside a code block after the branch was removed |

Both are Phase 1's second lesson — *assert the mechanism, not the presentation* — arriving in
work written after that lesson was recorded. **A check that names a vocabulary word passes for as
long as the word is anywhere in the file.**

**And the fix was design, not a stronger regex.** Chasing the checks would have hardened a bad
design; both readers turned out to be wired wrongly:

- **`plan-layers` was being told to re-parse `architecture.md` by eye**, after
  `check-architecture.py` had already parsed and validated it. Two parsers of one document that
  can disagree. Now Phase 1 writes `check-architecture.py --json` to
  `{tasks_dir}/architecture.json` and Phase 3 hands that path down — a chain of named artefacts,
  each link separately assertable.
- **`execute-batch` was being told to read a file it is never given.** Its arguments are
  `--tasks-path`, `--task-ids`, `--project-path`, `--worktree-dir`, `--base-branch`,
  `--batch-number`, `--layer`, and nothing else. The declaration already reaches it in the
  artefact it is holding: a task generated under `default="none"` **has no
  `<test-requirements>` section**. Branch on that. This is S2 applied to policy — derived from
  the artefact in hand, never asserted beside it — and it removes a third source of truth
  instead of adding one.

The rewritten checks assert the wiring, and the check now forbids `execute-batch` from ever
gaining an `--architecture` argument.

### Verification

`python tests/test_toolchain.py` — **61 checks, 0 failed**, 1 known (item 43's `expect_fail`,
untouched).

Five new checks, three of which **run a script** rather than reading one:

| Check | What it runs |
|---|---|
| a rule file that cannot be obeyed stops the run | `check-architecture.py` against 12 broken projects, 1 valid, 1 absent — each asserted on its **named cause**, not on exit 1 |
| PROJECT.md requires a registry, not the REST pair | `check-project-md.py` against command-only, event-only, screen-only, the REST pair, and none |
| principle citations resolve | `check-references.py` against resolving, dangling, and no-register trees |
| the declared layer graph reaches plan-layers as validated data | the wiring chain, link by link |
| `<testing default>` reaches execution as data | where each of four components gets the answer from |

**Six mutation rounds, and the rounds are the entry.** The suite was green from the first
write; mutation found that **five of ten new checks did no work**, and then that the harness
itself was lying twice.

| Round | Result | What it exposed |
|---|---|---|
| 1 | 7/9 | two checks asserted a **token** — `architecture.md` appears five times in plan-layers, so deleting the branch left the word behind |
| 2 | 8/13 | five more of the same class. Substring presence cannot detect one occurrence being removed |
| 3 | **11/13, misreported as 6/13** | the layer check was made mechanical and *renamed*; the harness still matched the old name and reported MISSED for a check that fired |
| 4 | 12/13 | checks now assert **conditions**, not only consequences — a mutant had deleted *when* to use a declared graph while leaving *what to do* |
| 5 | **13/13, and hollow** | an unrelated variable-scope slip left one check red *before* mutating. An already-failing check "catches" every mutant trivially |
| 6 | **13/13, baseline stated green** | the real result |

### The two design changes mutation forced, neither knowable by reading

Chasing the checks would have hardened a bad design. Both readers were wired wrongly:

- **`plan-layers` was being told to re-parse `architecture.md` by eye**, after
  `check-architecture.py` had already parsed and validated it — two parsers of one document that
  can disagree. Phase 1 now writes `check-architecture.py --json` to
  `{tasks_dir}/architecture.json` and Phase 3 hands that path down. The check then became
  **mechanical**: it parses the JSON example documented in `plan-layers` and compares it
  key-for-key against live producer output. That is 23a's pattern — the comparison that caught a
  schema three revisions stale — reused rather than reinvented.
- **`execute-batch` was being told to read a file it is never given.** Its arguments are
  `--tasks-path`, `--task-ids`, `--project-path`, `--worktree-dir`, `--base-branch`,
  `--batch-number`, `--layer`, and nothing else. The declaration already reaches it in the
  artefact in its hand: a task generated under `default="none"` **has no `<test-requirements>`
  section**. Branch on that. S2 applied to policy — derived from the artefact, never asserted
  beside it — and it removes a third source of truth rather than adding one. The check now
  **forbids** `execute-batch` ever gaining an `--architecture` argument.

### What this adds to Phase 1's first lesson

Phase 1 recorded *a green result whose mechanism has not been shown is not a result*. Round 5 is
the companion, and it cost an hour to learn:

> **A red result whose baseline has not been shown is not a result either.**

A check that was already failing catches every mutant, and the report is indistinguishable from
a healthy one. The harness now **refuses to run unless the suite is green first**, and prints
the failing checks if it is not. It also warns when a check fails that no mutant expected —
which is what round 3 needed and did not have.

Both harnesses copy each file aside and restore from the copy, then **verify the restore by
hash**. `git checkout -- <file>` on an uncommitted file reverts it to HEAD and discards the work
along with the mutation; that cost an afternoon in item 54 and is now automated against.

### And a third instrument note, from the shell rather than the suite

Three patch scripts were lost to heredocs eating a backslash level: `\b` in a regex became a
literal `0x08` byte, which is the same defect that disabled item 21's word-boundary anchors and
sent me debugging the layer above it. Every patch in this item is a **file** run with `python
<path>`, never a `<<'PY'` heredoc. Quoting the heredoc is not sufficient.


## What Phase 1 taught

Three things recurred often enough to be worth stating once, at the top of Phase 2 rather than
buried in eight entries.

### 1. A green result whose mechanism has not been shown is not a result

**Five false passes in eight items**, each a different mechanism:

| Where | The false pass |
|---|---|
| 23a proof | `git stash` with the wrong flag order silently did nothing; the suite reported PASS against the already-fixed file |
| item 54 | Removing the guard's escape branch still passed — `cd` failed anyway on a path that did not exist, and the fallback refusal satisfied an assertion looking only for `REFUSED` |
| item 21 run 2 | A clean probe result produced by a fixture that had explained the experiment to the agent under test |
| item 21 grading | 13 of 17 tasks reported as deriving from the rejected feature; every one was a *negative* requirement |
| item 21 grading | Then 0 of 17 for every tier, because a stray `0x08` byte had disabled both word-boundary anchors |

Every one was caught by mutation: break the thing, watch the check fail, put it back. **That is
now the standard for this build** — no check is finished until it has been seen failing for the
reason it exists.

### 2. Checks pinned to prose break when the prose improves

Item 9 removed four paragraphs and broke the F3 check that protected them — *while the behaviour
those paragraphs described got stronger*. A check asserting a sentence passes only while the
sentence is there.

Assert the mechanism: that a script reads both files, that an exit code is treated as binding.
Item 23's rule — every element has a named reader — is the same idea, and item 58's table of
assertions is where this belongs permanently.

### 3. Half the items were larger than specified, and the plan was right to be vague

| Item | Specified | Actually |
|---|---|---|
| 23a | a version string | a whole reference document describing a schema three revisions old |
| 42 | five reference sites | six, and one of the five was prose rather than a reference |
| 54 | two readers honour `<cwd>` | plus a guard, a producer, and a field in the result |
| 21 | run `/breakdown`, assert the count | the count cannot be attributed at all until item 16 |

**None of these was knowable before opening the file**, which is the argument for the ledger
existing: the plan is a specification written before the code was read, and where it was wrong is
what Phase 2 needs. Item 41's per-file atomicity — learned on item 42's rename, at 8 files instead
of 64 — is the clearest example of the rehearsal paying for itself.
