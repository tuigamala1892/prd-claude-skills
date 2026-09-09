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

**Phase 3 is complete.** Eight items in six commits, 56 → 66 regression checks, and the toolchain's
five vendored opinions are now a project's to change. Every item was verified by mutation against
a stated-green baseline; the rounds are where the real findings were, and they are collected in
*What six mutation rounds taught* below.

| Item | Status | Commit |
|---|---|---|
| **25 + 28 + 37** — the artefact, its guard, its readers | **Landed** 2026-08-26 | `3982022` |
| **51** — a Design phase in `/prd`, the producer | **Landed** 2026-08-26 | `3c6781f` |
| **31** — derive the layer set from content, both paths | **Landed** 2026-08-26 | `7d320b0` |
| **56** — enforce `<banned>` and `<task-limits>` | **Landed** 2026-08-26 | `7d320b0` |
| **26** — seed PROJECT.md on greenfield | **Landed** 2026-08-27 | `95ac1fc` |
| **57** — impact analysis reports contracts, not APIs | **Landed** 2026-08-27 | `95ac1fc` |

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


## 26 + 57 — closing the greenfield loop, and generalising what a contract is

**Addresses:** P17 (output half), P35, A3/D3 · **Files:** `skills/execute/SKILL.md`,
`agents/project-context-finalizer.md`, `skills/crd/references/crd-format.md`,
`skills/crd-impact-analysis/SKILL.md`, `agents/crd-impact-analyzer.md`,
`skills/breakdown/SKILL.md`, `tests/test_toolchain.py`

### 26: the gate was a condition greenfield could never satisfy

`test -f {project_path}/PROJECT.md` ran the finalizer only where the file already existed. No new
project can satisfy that, so greenfield ran the whole pipeline and ended with **no architecture
record at all** — and the first `/crd` against it then paid for a full `crd-investigate` to
rediscover architecture the PRD had already stated.

The gate now branches three ways: update where it exists, **create** where it does not and the
run came from a PRD, and refuse where it does not and the run came from a CRD (which means
something removed a file `/breakdown` had already required).

**Two decisions the plan left open, both settled by the prescriptive/descriptive split:**

- **Seeding copies the registries and leaves `<rules>` and `<principles>` behind.**
  `architecture.md` says what the project *must* be; `PROJECT.md` says what it *is*. Copying the
  rules across would collapse the one distinction that makes two files defensible — open
  question 2 is uneasy about having two at all, and this is the answer to it. This is also why
  item 25 put registries at the same nesting level in both: the seeding is a subtree **copy**,
  not a transform.
- **Where a seeded entry and a task export disagree, the export wins.** `architecture.md`'s
  registries are written before any code exists and are usually empty; the exports describe what
  was built, and this file's whole job downstream is to say what exists.

`Mode` is passed explicitly rather than inferred by the agent. It has `Read` and could test for
the file, but then two components decide the same thing and can disagree — and the caller has
already run the test.

### 57: opening the registry set without this would be the half that shows

`crd-impact-analysis` could now *read* an event or command registry (item 25) and had nowhere to
report the impact: it emitted `<affected-apis>` and `<affected-schemas>` and nothing else.

`<affected-contracts>` with a `kind` that **matches the registry the contract came from**, so the
enum extends when the registry set does rather than being a second list to keep in step — the
mistake item 25 had just corrected one level up.

**`<affected-apis>` is deprecated, not deleted.** This is the only Phase 3 item that changes a
*published* artefact shape, and every CRD already written uses the old element. It stays readable
and marked deprecated; item 41 rewrites them. Deleting it would have bought tidiness with every
existing CRD.

**Item 31 had to follow within hours of landing.** Its derivation keyed the backend tier off
`<affected-apis>`; with contracts generalised, an *event* contract change is what puts work in an
event-driven graph's `contracts` layer, which was unreachable from an impact analysis before.

### Verification

`python tests/test_toolchain.py` — **66 checks, 0 failed**, 1 known. Two new checks, **13/13
mutants** against a green baseline.

The two mutants worth naming are both *plausible tidying* rather than obvious breakage: copying
`<rules>` into `PROJECT.md` looks like completeness and destroys the prescriptive/descriptive
split; deleting `<affected-apis>` looks tidy and breaks every CRD already written.

---

---

## Phase 4 — The schema core and its migration.

Plan order: `44` → `45` → `41` → `33` · `34` · `29` · `27` · `35` · `1` · `2` · `4` · `5` · `11` ·
`12` · `36`, on branch `phase-4-schema-core`.

The order inside this phase is an argument, not a preference. **44 is first** because a shared
core defined *after* the elements it shares is a merge rather than an extraction. **45 next**,
because renaming three vocabularies is cheap before they have consumers. **41 third** — the
migration is written *before* the items that rewrite artefacts, not after, because none of them
can land until the transformation is specified and checkable.

**Phase 4 is complete.** Fifteen items in six commits, **66 → 86** regression checks, `known 0`,
and the artefact schema has moved through four versions with a migration that has been run over
every one of them. **Not pushed to `origin`.**

The phase's shape, in one line each:

| | What it established |
|---|---|
| **44** | one definition of every shared element, and templates out of the command files |
| **45** | three renames, and the word the fourth keeps |
| **41** | the migration, its three consumers, and the marker that turned out to be the shape |
| **33 + 34** | the criterion becomes a requirement, and the first judgement boundary |
| **29 · 27 · 35 · 1 · 2 · 5** | the rest of the feature template, as one schema version |
| **4 · 11 · 12 · 36** | conventions that refuse, a list that derives itself, a record with a reader |

**Four schema versions, four fixtures, three migration steps** — one fully mechanical and two
mixed. `SCHEMAS.json` declares which is which and what each mixed step's *judgement surface* is,
so the golden comparison asserts exactly what the script owns and nothing about what it is
forbidden to do.

| Item | Status | Commit |
|---|---|---|
| **44** — one schema core, cited by both paths | **Landed** 2026-08-27 | `9fc531c` |
| **45** — three status vocabularies, three names | **Landed** 2026-08-27 | `145282d` |
| **41** — the migration, and its golden comparison | **Landed** 2026-08-27 | `28b85b9` |
| **33 + 34** — EARS criteria, and criterion priority | **Landed** 2026-08-27 | `4f81d54` |
| **29 + 27 + 35 + 1 + 2 + 5** — the rest of the template | **Landed** 2026-08-27 | `15bb097` |
| **4 + 11 + 12 + 36** — conventions, derived list, dual read, record | **Landed** 2026-08-27 | `3410f62` |

---

## 44 — one definition, two paths, and three copies that had already drifted

**Addresses:** P30 · **Files:** `schema/core.md` (new), `schema/prd-format.md` (new),
`commands/prd.md`, `commands/crd.md`, `skills/crd/SKILL.md`,
`skills/crd/references/crd-format.md`, `skills/crd/references/project-format.md`,
`skills/breakdown/SKILL.md`, `skills/breakdown/references/task-format-spec.md`,
`tests/test_toolchain.py`, `tests/mutants/phase4-44.py` (new), `CLAUDE.md`

### What "extraction, not merge" meant in practice

The plan's ordering note is the whole design of this item and it is easy to read past. Item 44
lists elements that items 33, 34, 29, 45 and 49 will *change* — EARS criteria, `<gaps>`, renamed
status tags, `P0|P1|P2`. It is tempting to read that as *build the core out of the new shapes*,
which would mean writing the core after those items.

**The core is populated with today's shapes instead**, and each section that is scheduled to
change says so in a block quote naming the item that will change it. That is what makes the rest
of the phase an edit to one file rather than a reconciliation of two — which is the difference
between an extraction and a merge, and the reason the plan put this item first.

### The drift was real, and it was found rather than assumed

Three documents defined `<criterion>`: `commands/prd.md`'s feature template, `commands/crd.md`'s
Phase 6 template, and `crd-format.md`. A fourth, `skills/crd/SKILL.md`, carried its own copy of
the whole `<crd>` shape. They had already come apart:

| Divergence | Where |
|---|---|
| `<scope>` and `<confidence>` marked **required** | `crd-format.md` |
| ...and emitted by neither producer | `commands/crd.md`, `skills/crd/SKILL.md` |
| `<affected-contracts>` (item 57, Phase 3) | `crd-format.md` only — both producers predate it |
| `<step kind= status=>` written by `/prd` Phase 4 (item 51, Phase 3) | absent from the `what-next.md` template it writes into |

The last two are the useful ones: **both are Phase 3 items that updated the spec and left a
producer behind.** Item 51 wrote a producer for a `<step>` shape the template does not document,
and item 57 opened `<affected-contracts>` in the format reference while two templates went on
showing the deprecated pair. Neither was visible while the definitions lived in four places; both
were unavoidable the moment they had to be written down once.

### Deviations from the plan

- **A new top-level `schema/` directory**, holding `core.md` and `prd-format.md`. The plan says
  the core is "a single reference that each cites" without saying where it lives. Putting it in
  either path's `references/` would make the other path a guest in it, which is the asymmetry the
  item exists to remove.

- **The three existing format references stay where they are.** `crd-format.md`,
  `project-format.md` and `task-format-spec.md` each cite the core and none moved. Moving them
  would have been tidier and is not what item 44 asks for; the tidy rule that would justify it —
  *schema in `schema/`, operating guidance in `references/`* — does not actually hold, because
  `project-format.md` and `task-format-spec.md` each have two owning skills. Recorded so that a
  later consolidation is a decision rather than a discovery.

- **`/crd`'s templates were extracted too, which the item does not mention.** It names only
  `/prd`'s. But `commands/crd.md` and `skills/crd/SKILL.md` held the same defect in the same
  shape, and two of the four drifts above are theirs. Leaving them would have fixed the argument
  on one path and not the other.

- **`<step status=>` is a fifth tag spelled `status`**, and the core says so rather than claiming
  four. It is PRD-only, so it is defined in `prd-format.md`; but the count is stated in the core,
  because the core is where someone goes to get that count right.

### The finding item 45 inherits

The plan's item 45 renames three vocabularies. **There are four**, and the fourth is the one the
rename leaves alone:

| Tag | Records | Item 45 |
|---|---|---|
| `<status>` in `index.md` / `what-next.md` | how far the **interview** got | *unchanged* |
| `<status>` in a feature's `<meta>` | how completely it is **defined** | → `<definition>` |
| `<status>` in a CRD's `<meta>` | where it is in the **process** | → `<workflow>` |
| `status=` on `PROJECT.md`'s `<feature>` | how much exists **in code** | → `built=` |

This is not an omission in the plan so much as a consequence it did not state: the rename does
not leave one tag ambiguous, **it frees the word.** After item 45, `<status>` means exactly one
thing — and that thing is the only one of the four with a shipped reader today, `list-prds.py`.
Renaming it would break `--resume` for no gain.

### Verification

Two checks, both parsing rather than matching prose, and both watched failing.

**`the schema core is one definition that both paths cite -- and its citations resolve`.** Three
assertions: the version the core declares equals `SCHEMAS.json`'s `current`; every local link out
of the core resolves; and every row of the core's *"who cites this file"* table names a document
that really does link back — directly, or through the intermediary its own row names.

**`no artefact template lives in a command file`.** Parses every fenced `xml` block in the two
commands and the CRD skill and asserts none is rooted at `<prd>`, `<crd>`, `<feature>` or
`<what-next>`. A structural claim about what a block *is*, not a search for forbidden words — and
it also requires each command to link the file that defines what it writes, because a citation
removed is how the template comes back.

Suite 66 → **68** checks. Mutation: **6/6 caught** against a stated-green baseline
(`tests/mutants/phase4-44.py`).

### What the mutation round changed, which reading could not

**The second hop was decorative, and one mutant proved it.** The citation check originally
verified that `commands/prd.md` links `prd-format.md`, and stopped there. Mutant 4 broke the
*second* hop — `prd-format.md`'s own citation of the core — and the suite reported nothing. A
chain checked at its first link is not a chain that has been checked.

Then the fix was wrong in an instructive way. Asserting *"the intermediary links `core.md`
somewhere"* made the check green again — and unfalsifiable, because `prd-format.md` cites the
core in two places and `crd-format.md` in five. **No single edit could break it, which means no
single edit could ever have been caught by it.** It is the same failure the first version had,
one level down.

What holds is the region: the intermediary must cite the core **in its preamble**, before its
first section heading. One site, and the right one — a reader who reaches the templates without
being told the shared elements are defined elsewhere has already been misled.

> Phase 3's lesson was *scope to the region that owns the claim*. This adds the test for whether
> you have: **if no single edit can break the check, it is not checking.** Counting the sites
> that satisfy an assertion is quicker than a mutation round, and finds the same defect.

**And a modelling error the check caught in me.** The second-hop assertion first resolved the
intermediary by joining its basename to `schema/` — correct for `prd-format.md`, wrong for
`crd-format.md`, which lives under `skills/crd/references/`. The suite went red before the
mutation round could start. Resolving the hop from the *citing document's own link* is both
correct and the smaller assumption: only the citing file knows where its intermediary is.

---

## 45 — three renames, and the word one of them gets to keep

**Addresses:** P29 · **Files:** `schema/core.md`, `schema/prd-format.md`, `commands/prd.md`,
`commands/crd.md`, `skills/crd/SKILL.md`, `skills/crd/references/crd-format.md`,
`skills/crd/references/project-format.md`, `skills/crd-context-update/SKILL.md`,
`skills/breakdown/scripts/rename-feature.py`, `agents/crd-investigator.md`,
`agents/crd-context-updater.md`, `agents/crd-impact-analyzer.md`,
`agents/project-context-finalizer.md`, `tests/fixture/prd/schema-2/**` (new),
`tests/fixture/prd/SCHEMAS.json`, `tests/fixture/setup_fixture.py`, `tests/probe-p1.py`,
`tests/test_toolchain.py`, `tests/mutants/phase4-45.py` (new), `CLAUDE.md`

### What landed

`<status>` → `<definition>` on a PRD feature, `<status>` → `<workflow>` on a CRD's `<meta>`,
`status=` → `built=` on a `PROJECT.md` feature. Values unchanged in all three, so a diff against
the previous fixture shows the rename and nothing else — which is deliberate, because item 41's
golden comparison then has exactly one transformation to account for.

### The fourth vocabulary, and why it is not a gap in the plan

The plan's item 45 names three. **There are four tags spelled `status`**, and the fourth is the
document-level one in `index.md` and `what-next.md` that records how far the interview got.

The plan does not mention it, and the reason it does not need to is the interesting part: the
rename does not leave one tag ambiguous, **it frees the word.** Once its three namesakes have
names of their own, `<status>` means exactly one thing — and that one thing is the only member of
the set with a shipped reader (`list-prds.py`, which makes `--resume` work). Renaming it would
have cost a migration and a behaviour change to buy nothing.

A fifth, `<step status="done">` in `what-next.md`, is an *attribute* and cannot collide with an
element. It is named in the core and defined in `prd-format.md`.

### Deviations from the plan

- **The `<definition>` enum is not extended here.** Item 45's table lists five values including
  `excluded` and `superseded`; the template ships three. Extending the value set is a different
  act from renaming the tag, and doing both in one commit makes the two indistinguishable in a
  diff — which matters more than usual when the diff is the migration's evidence. Items 1 and 4
  own the extension; core §3 says so in place.

- **A backward-read policy, which item 45 does not specify.** *Accepted on read; never written.*
  This is the rule item 57 already set for `<affected-apis>`, stated once in the core so that
  three renames share one policy instead of each reader inventing its own. The exception is the
  fourth row: `<status>` was never renamed, so a `<definition>` at document level is not an old
  artefact, it is a mistake.

- **`--status` stays a flag on `/crd` while the element becomes `<workflow>`.** *"What is the
  status of this change request"* is what a person asks. The collision was between elements
  inside documents, and renaming a published flag to fix it would change an interface for no
  reason.

- **`setup_fixture.py` stops hardcoding the version, against item 43's stated preference.** That
  file carried a comment explaining that a hand-edited constant was chosen over a glob, because a
  glob would silently pick whichever directory sorted last. The argument is right about a glob
  and does not apply to reading `SCHEMAS.json`, which is an explicit declaration and the one the
  suite already trusts. Two places declaring which schema is current is the duplication this
  phase exists to remove — and item 45 proved it, because the constant did not move when the
  second version arrived.

### The debt this closed, and the signal that fired on schedule

**`SCHEMAS.json`'s frozen-fixture rule now has content hashes.** Item 43 wrote rule 2 — a
non-current fixture changes only when the migration's expected output changes — and had nothing
to enforce it with, because nothing was frozen yet. Item 45 created the first frozen fixture, so
the hash and its check land here rather than as a standing debt.

**And the `expect_fail="item 1"` golden-pair check fired exactly as designed.** Registering
schema-2 turned it green, the run failed with `fixed 1`, and that was the signal to delete the
marker rather than a breakage. It is now a permanent regression guard. The migration comparison
it unblocks is item 41's, which is next.

### A fixture defect, recorded because item 41 needs it

`staff-service/index.md` and its `what-next.md` both declare `<status>defined</status>` at
**document** level, where the enum is `in-progress|complete`. `defined` is a *feature* value.
Both fixtures were carried into schema-2 unchanged rather than corrected, deliberately: schema-1
is frozen and the copy must differ from it by the rename alone.

It is a good case for item 41 to have. A migration that "fixes" it is doing more than a rename;
the correct behaviour is the one item 41 already specifies for a file matching no precondition —
**stop and report this file**, never transform it anyway.

### Verification

Three checks. Suite 68 → **72**, and `known` back to 0.

**`three status vocabularies, three distinct names -- and the fourth keeps the word`** reads core
§3's table as data: four rows, four distinct tags, exactly one still spelled `<status>`,
`in-progress` present in at least three of the four value sets, and the rename reaching every
template in each defining document.

**`a frozen fixture is frozen -- by hash, not by intention`** recomputes the digest and prints
the actual value when it disagrees, so a deliberate change is a copy-paste and an accidental one
is a named failure.

**`nothing hardcodes a schema fixture version`** scans the test harness for a literal
`"schema-N"`.

Mutation: **10/10 caught** against a stated-green baseline (`tests/mutants/phase4-45.py`) — but
only after the round found two assertions that were satisfied at more sites than they checked.

### The same defect twice more, and it now has a name

Item 44's round found one assertion that could not be falsified by a single edit. Item 45's found
two more, in a check I had written *after* learning that lesson:

| Assertion | Sites satisfying it | Mutant that survived |
|---|---|---|
| *some pair of vocabularies shares a value* | 6 pairs | changing one vocabulary's values |
| *some template in this file writes the new tag* | 4 `<feature>` entries | changing one of them back |

Both are `any()` where the claim was universal. The fixes are the claim stated properly:
`in-progress` appears in **at least three of four** — the specific overlap that made the collision
dangerous rather than untidy — and **every** feature entry in `project-format.md` carries
`built=`.

> **The rule, now stated once for the phase.** Before a check is finished, count the sites that
> satisfy it. If more than one does, no single edit can break it, and it will pass through
> exactly the regression it was written to catch. `any()` over a document is the usual shape;
> the fix is usually `all()`, or naming the one site that carries the claim.

This is Phase 3's *scope to the region that owns the claim*, arrived at from the other side.
Phase 3 learned it by watching a mutant survive overnight; here it cost three mutants across two
items, which is the cheap version.

### Two instrument failures, both the same one, and both already in memory

`\b` in a check's regex was written through a shell heredoc and arrived as byte `0x08`; `\0` in
the fixture-digest helper arrived as a NUL, which made the suite file **binary** and unparseable.
Both are the failure recorded after item 21's grading, where a stray `0x08` had silently disabled
two word-boundary anchors and produced a confident 0-of-17.

The lesson was already written down and it did not prevent a repeat, so the operational form is
worth stating: **write files containing regex escapes with a file-writing tool, not through a
heredoc.** A repo-wide scan for `[\0\a\b\v\f]` now runs after any such edit — it takes a second
and it is the only thing that makes this class of defect visible at all, since `grep` prints
`Binary file matches` and moves on.
---

## 41 — the migration, and the marker that turned out not to be needed

**Addresses:** the precondition for items 1, 2, 5, 11, 29, 33, 34, 35 · **Files:**
`schema/migration.md` (new), `schema/scripts/migrate.py` (new),
`agents/schema-migrator.md` (new), `skills/migrate/SKILL.md` (new), `schema/core.md`,
`tests/test_toolchain.py`, `tests/mutants/phase4-41.py` (new), `CLAUDE.md`

### What landed

The guide, in the four-part shape the item specifies — precondition, transformation,
postcondition, escalation, per rule — with the schema-1 → schema-2 rules written out and the
schema-2 → schema-3 **boundary** settled in advance: which transformations are mechanical, which
are judgements, and which judgement belongs to whom.

Three consumers, because a guide with no consumer is the defect this plan exists to remove:
`migrate.py` for the mechanical rules, `schema-migrator` for the judgements, and a thin
`/migrate` skill that dispatches one agent per file.

**And the golden comparison the fixture registry promised since item 43**: run the migration over
the frozen schema-1 tree and assert the result is byte-for-byte the schema-2 tree. It is the only
check in the suite whose expected output was authored independently of the thing producing it.

### The marker: item 41 asked for one, and the answer is that there isn't one

The item requires that *"the marker of already migrated must be in the file rather than in a
side-car that can drift from it."* The natural reading is a stamp — `<schema>schema-2</schema>`
in every artefact's `<meta>`.

**The shape is the marker.** A feature file carrying `<definition>` is migrated; one carrying
`<status>` is not. Nothing is added. A version stamp beside the content would be a second source
of truth about the same file, free to disagree with it — which is the defect this plan spends
most of its items removing, reintroduced by the tool meant to apply them.

**The corollary is a real constraint, and it is the part worth carrying forward.** If completion
is not visible in the shape, the transformation must be made **total** until it is. Item 34's
criterion `priority` is the case that forced this: *unassigned* and *deliberately absent* look
identical, so the migration must assign `P1` to every criterion lacking one rather than leaving
the default implicit. A partial transformation with an invisible completion state cannot be
resumed at all — and the guide now refuses to define one, which is a constraint on items 34, 2
and 5 that they do not yet know they are under.

### Deviations from the plan

- **A skill and an agent, neither of which the item mentions.** It says the work "will be done by
  an agent" and stops there. The regression suite refuses an agent nothing dispatches — F20's
  shape — so the invoker is not optional; `/migrate` is the smallest thing that makes the agent
  reachable, and it is what makes *per file, reviewed as a diff* an instruction someone follows
  rather than a sentence in a guide.

- **The mechanical half is a script, not the agent.** The item frames the whole migration as
  agent work, which is right for 550 EARS criteria and wrong for a rename. Splitting it is what
  makes the golden comparison possible at all: a deterministic transformation can be asserted
  byte-for-byte, and a model's cannot.

- **Escalation gets its own exit code.** The item says *stop and report this file, never
  transform it anyway*. Exit 2 is separate from exit 1 so that *"nothing was written for these"*
  is sayable — a failed postcondition restores one file, while an escalation never touched it.

- **`--check` is not in the item.** *"The migration ran"* and *"the migration finished"* are
  different claims, and only a run that asserts postconditions against the tree as it stands can
  make the second. It is item 55's lesson — the ledger states what it verified — arriving on a
  different artefact.

### Verification

Three checks, two of which **run the script**. Suite 72 → **75**.

**`the migration turns the old fixture into the new one, exactly`** copies the frozen schema-1
tree, migrates it, and compares the result to the schema-2 fixture with `filecmp.dircmp` — then
runs it again and asserts nothing changed, and calls `--check` before and after.

**`a file the migration cannot place stops it, and is named`** builds a tree holding one
migratable file, one file with no root element and one `<feature>` in neither shape. It asserts
exit 2, that both unplaceable files are named, that **neither was modified**, and that the
migratable one was still migrated. The last assertion is the one that matters: a run that gives
up wholesale on one bad file cannot be resumed.

**`the migration guide has an executor, and the executor cites the guide`** is item 23's rule
applied to item 41's own output.

Mutation: **12/12 caught** (`tests/mutants/phase4-41.py`) — after the round found three more
assertions of the kind item 45 named.

### The site-counting rule earned its third and fourth confirmations

| Assertion | Sites satisfying it | Mutant that survived |
|---|---|---|
| `--check` returns 0 on a migrated tree | every branch agrees there | `--check` always returning 0 |
| `"migration.md" in body` | the link **and the frontmatter description** | deleting the link |
| *some sentence says "stop and report"* | 3 sentences per document | reversing the exit-2 row |

The first is a new variant and worth naming separately: **the check ran the command in the only
state where its answer could not be wrong.** `--check` was called on an already-migrated tree,
where a correct implementation and one that always returns 0 are indistinguishable. Counting
sites would not have found it; the question that does is *"in what state would this command give
the wrong answer, and is that the state I am testing?"*

The second and third are the same `any()`-where-the-claim-is-universal defect item 45 named, and
the fixes are the same two moves: require a **resolving link** rather than a mention, and scope
the escalation assertion to the one line in each document that owns the claim.

### A note on where the guide's authority sits

`migrate.py`'s docstring says outright that `schema/migration.md` is the authority and that a
rule existing in the script and not in the guide is a bug in the script. That sentence is doing
real work: it is what stops the guide becoming documentation of the program, which is the
direction these pairs always drift when nobody says which one is upstream.
---

## 33 + 34 — the criterion becomes a requirement, and the migration meets its first judgement

**Addresses:** P23, P1's residue · **Files:** `schema/core.md`, `schema/prd-format.md`,
`schema/migration.md`, `schema/scripts/migrate.py`, `commands/prd.md`, `commands/crd.md`,
`skills/crd/SKILL.md`, `skills/crd/references/crd-format.md`, `skills/breakdown/SKILL.md`,
`skills/breakdown-generate-tasks/SKILL.md`, `tests/fixture/prd/schema-3/**` (new),
`tests/fixture/prd/SCHEMAS.json`, `tests/test_toolchain.py`,
`tests/mutants/phase4-33-34.py` (new)

### Why the two are one commit

Item 34's `priority` is an attribute on item 33's element. Landing them apart would mean writing
the criterion schema twice, migrating twice, and versioning the fixture twice — and the second
migration would have to be written against a shape that existed for one commit.

### What landed

`<criterion>` is one EARS sentence carrying `pattern` and `priority`, defined once in core §2 and
cited by both paths. `/breakdown` gains `--requirement-level <P0|P1|P2>`, applied after the
feature-level filter. `breakdown-generate-tasks` maps each pattern to the kind of test it implies
— which is what makes the attribute a consumer's input rather than a label.

**The interview asks for the unwanted case explicitly, on both paths.** Neither `/prd` nor `/crd`
did, and the corpus that motivated item 33 contains **zero** `optional-feature` criteria — a
number that says as much about the questions asked as about the format. A phase that only asks
what should happen produces criteria that are entirely `event-driven`, and a feature that has
described success and nothing else reads as complete.

### The migration's first judgement boundary, and the state it forced

schema-2 → schema-3 is **the first step that is not fully mechanical**. `priority` and
`derived-from` are the script's; the EARS sentence and its `pattern` are judgements item 41's
guide forbids a machine to make.

A script that stopped at that boundary would leave 550 criteria un-stamped; one that crossed it
would invent the attribute the whole taxonomy depends on. **Neither failure announces itself.** So
the migration gained a third verdict:

| Verdict | Shape that identifies it | `--check` |
|---|---|---|
| `MIGRATED` | every postcondition holds | passes |
| **`PARTIAL`** | `priority` present, `pattern` absent | **refuses** |
| `ALREADY` | at or beyond the target | passes |

**`PARTIAL` is detectable from the file alone**, which is the marker rule from item 41 meeting
its first hard case and surviving it. And `--check` refusing a `PARTIAL` tree is what stops *"the
script ran"* being read as *"the migration finished"*.

**`priority="P1"` is written into the file rather than left to the documented default.** It looks
like noise and is not: an absent attribute and a deliberate `P1` are indistinguishable, so a
partly-assigned corpus could not be told from a finished one. This is the constraint item 41's
marker rule predicted, arriving one item later on the item that triggered it.

### Deviations from the plan

- **The golden comparison had to be split in two.** Item 43 promised one: migrate the old fixture,
  assert the result equals the new one. That works only for a fully mechanical step. There are now
  two checks — a byte-for-byte comparison over a step `SCHEMAS.json` calls `mechanical`, and an
  invariants check over a step it calls `mixed` that asserts *everything the script was supposed
  to do, it did; everything it was forbidden to do, it left*.

  **Which step is which is declared in the registry, not in the suite.** Hardcoding
  schema-1 → schema-2 would have quietly stopped exercising the comparison the moment a fourth
  version arrived — the same defect item 45 found in `setup_fixture.py`, one file along.

- **`migrate.py` became a chain rather than a single hop.** A file three versions behind takes
  every step it needs in one pass, and each file in a tree is decided on its own. This is item
  24's *"select the right migration, not the newest one"* arriving early, because two versions
  could not have shown it and three can.

- **A rule may be vacuously satisfied, and R4 is.** A feature with no criteria at all is
  `excluded` or `superseded` — legitimate under the schema. The first version of R4 required at
  least one criterion, which turned a rule about criteria into a rule about features and
  escalated a valid file. Found by the escalation check, which had a feature with no criteria in
  it for an unrelated reason.

- **`schema-3` carries items 33 and 34 only.** The plan's own registry entry had six items
  arriving together. Splitting it means the golden comparison has exactly one kind of change to
  account for, which is the same argument item 45 made for keeping its rename clean. The rest —
  1, 2, 5, 27, 29, 35 — is now `schema-4` in the registry's `planned` block.

### Verification

Suite 75 → **78**.

**`a criterion is one EARS sentence with a pattern and a priority`** parses every criterion in
every template on both paths as XML and asserts `pattern` is one of the six, `priority` matches
`P[012]`, the body contains `shall`, and no `<given>` survives. It also asserts the taxonomy is
enumerated where a person assigning one would read it, and that
`breakdown-generate-tasks` says something different about each of the six — an attribute the
consumer treats uniformly is decoration.

**`the two priority levels stay in two vocabularies, and the filter says so`** reads core §4's
table as data and asserts the two value sets are **disjoint**. That is item 34's actual design
claim: not that `P0|P1|P2` exists, but that it shares nothing with MoSCoW, so no flag or report
line is ambiguous about which level it means.

**`a migration it may not finish does the half it can, and says which half`** runs the mixed step
and asserts all three of: `PARTIAL` reported, `--check` refusing, and per criterion —
`priority` and `derived-from` present, `pattern` **absent**. Two of those three passing without
the third is exactly the failure that reads as success.

Mutation: **15/15 caught** against a stated-green baseline (`tests/mutants/phase4-33-34.py`).

### An instrument note: the round outgrew the tool's timeout

The suite now takes ~42 seconds, because five checks run real subprocesses. Fifteen mutants plus a
baseline is eleven minutes, and the shell tool caps at ten — the round was killed mid-mutant and
left `migrate.py` modified.

**It was recoverable only because the tree had been staged first.** `git restore --worktree`
took the file back from the index, which held the correct content. Had it not been staged, the
memory's own warning applies with full force: `git checkout --` would have reverted to HEAD and
discarded the item's work along with the mutation.

The operational fix is to run long rounds in the background rather than to shrink them. The
standing rule against running the suite concurrently with a mutation round still holds, so the
useful work while one runs is writing, not checking.
---

## 29 + 27 + 35 + 1 + 2 + 5 — the rest of the feature template, as one schema version

**Addresses:** P19, P11, P25, P8, P4, P12 · **Files:** `schema/core.md`, `schema/prd-format.md`,
`schema/migration.md`, `schema/scripts/migrate.py`,
`skills/breakdown/scripts/check-references.py`, `skills/breakdown/SKILL.md`,
`skills/breakdown-analyze-prd/SKILL.md`, `skills/breakdown-plan-layers/SKILL.md`,
`skills/breakdown-review-tasks/SKILL.md`, `skills/breakdown/references/review-criteria.md`,
`skills/breakdown/references/task-format-spec.md`, `tests/fixture/prd/schema-4/**` (new),
`tests/fixture/prd/SCHEMAS.json`, `tests/test_toolchain.py`,
`tests/mutants/phase4-schema4.py` (new), `CLAUDE.md`

### Why six items are one commit

They are one template. Landing them apart would mean six schema versions of one project, six
migration steps over the same file, and six golden comparisons that each have to account for the
other five. `SCHEMAS.json`'s `planned` block had already grouped them for exactly that reason.

### What landed

| Item | Element | Reader |
|---|---|---|
| 29 | `<gaps>` / `<gap kind= raised=>` | `analyze-prd` carries them, task files preserve them, `review-criteria` lets them through, `/breakdown` reports them |
| 27 | `<depends-on slug= kind=>` | `analyze-prd` emits `feature_edges`; `plan-layers` derives the ordering from them |
| 35 | `<architecturally-significant because= criteria=>` | `check-references.py` reports a flagged feature no record drives |
| 1 | `<user-story>`, `<rationale>`, `<superseded-by>`, and `<priority>` **removed** from `<meta>` | the index is the only home for feature priority |
| 2 | `<notes>` → `<data-model>` + `<considerations>` | `analyze-prd` reads the first and is told to leave the second alone |
| 5 | no `<phases>` element, and the argument for never adding one | — |

### The one that had to be given a reader before it could land

**Item 35's flag had none.** The plan gives it two — item 6 screens for candidates and item 38's
gate asserts every significant feature is named by a record — and both are Phase 5. A flag landing
now with its readers a phase away is the unread element this plan exists to remove, and the
regression suite would have been right to say so.

So `check-references.py` gained the smallest honest reader available: **a significant feature that
no decision record names in `**Drives:**` is reported STALE, never DANGLING.** The asymmetry is
item 35's own — the flag is a judgement and its absence proves nothing, so the script says which
features are in that state and stops. The one thing it *does* refuse is an
`<architecturally-significant>` with an empty `because`, which records that something matters
without saying what kind of thing it is.

This is item 38's first assertion arriving early, minus the gate. Recorded as a deviation because
the gate is still item 38's, and someone reading Phase 5 should find this already done rather
than do it twice.

### Item 29's corollary was the substantive half, not the element

`<gaps>` is a schema addition and a small one. **The change that matters is to
`review-criteria.md`: the placeholder ban now applies to *unmarked* vagueness only.**

Banning `TBD` outright is precisely what makes invention the compliant answer — an author who
cannot write *"we have not decided this"* writes something plausible instead, and nothing
downstream can tell the difference. A marked gap **passes review and blocks execution**; unmarked
vagueness keeps failing exactly as it did.

The placeholder scan is now scoped *around* the `<gaps>` element rather than over the whole task,
which is the mechanical form of the same rule. Without that scoping the mechanism item 29 built
to make honesty possible would itself have failed review.

### Deviations from the plan

- **`<data-model>` extraction is mechanical only where the heading is.** Item 2 keys the split on
  a bold `**Data model**` heading measured at zero false positives *on the corpus*. The fixture
  has no such heading, so its `<data-model>` blocks are authored rather than migrated — which is
  the honest outcome and is declared: `judgement_elements` in `SCHEMAS.json` lists `data-model`
  for this step.

- **`<definition>` is part of the judgement surface too.** Reclassifying a feature against its
  migrated content is item 4, and a `specification` gap barring `defined` is a decision about the
  feature rather than about its format. The fixture's `quokka-telemetry` is held at `in-progress`
  for exactly that reason — **which is item 43's untested rule firing for the first time.** It
  recorded the bar as *"sound in principle and unexercised in fact"* and named the fixture as
  where it should first fire; it now does.

- **Item 5 is a decision with a guard, not a deletion.** `<phases>` never existed in this
  toolchain — it was proposed and superseded within the plan's own item. So what landed is the
  *argument* for never adding it, in `prd-format.md`, plus a check that no template declares one.
  An absence with no argument beside it is an omission somebody will helpfully correct.

- **The schema-4 fixture is built by running the migration and then authoring the judgements.**
  The first attempt hand-wrote the whole file, and the golden comparison then failed on
  indentation — it was asserting whitespace rather than behaviour. Building it the way a real
  migration runs makes the mechanical half byte-identical by construction, which leaves the check
  exactly one thing to assert.

### Verification

Suite 78 → **82**, and the two migration checks now exercise a second mixed step.

**`uncertainty has a channel that survives the handoff, and review lets it through`** reads core
§6's kind table as data, asserts at least two kinds warn rather than stop, and follows the gap
through every hop — analysis, task file, reviewer. The last assertion is scoped to *the line that
carries the placeholder ban* in each of the two reviewers, and requires the word **unmarked** on
it.

**`feature dependencies are declared edges, and ordering is derived from them`** asserts the three
kinds, that `reference` carries **no** ordering constraint, that the analyser refuses to derive
edges from markdown links, and that `plan-layers` is told the ordering is its own job.

**`the feature template carries intent, significance, and no second priority`** parses the
template as XML: eight elements present, no `<priority>` in `<meta>`, `excluded` and `superseded`
in the `<definition>` enum, no `<phases>` in any template and no `phase=` on any criterion — and
that item 35's flag has a reader that reports rather than refuses.

**``<considerations>` is unread by design, and says so`** asserts the distinction between *unread
by design* and *unread by oversight* is actually written down, along with the verbatim promise
that makes the two-way split safe.

Mutation: **20/20 caught** against a stated-green baseline (`tests/mutants/phase4-schema4.py`) — after a first pass at 14/20, whose six misses are below.

### Six misses in the first round, and five were one defect

| Miss | Satisfied by | Fix |
|---|---|---|
| the `specification` gap stops barring `defined` | the row's *other* `yes` column | assert the **cell**, not the row |
| the analyser starts answering gaps | heading **and** body both matched | scope to the **section heading** |
| task files stop carrying gaps | the prose describing the rule | assert a **parsed `<gaps>` block** |
| the `<phases>` argument is deleted | the mutant hit a neighbouring sentence | assert the *reason*, and mutate that |
| the significance flag loses its reader | the script's **docstring** | **run the script** and assert the report |

The sixth was a mutant whose anchor spanned a line wrap: the harness reported `ANCHOR NOT FOUND`
rather than `MISSED`, which is a distinction it was built to draw and which saved a wrong
conclusion about the check.

**The last row is the one to keep.** `"architecturally-significant" in refs` passed while the
script's pattern had been renamed to match nothing at all — the docstring satisfied it. The check
now builds a temporary PRD with a flagged feature and asserts **both halves of the asymmetry**:
reported when no record drives it, silent when one does, exit 0 either way. That is this
repository's own *"by running the guard"* pattern, arriving at a check that had been written as a
grep.

> **The site-counting rule, stated for the third time in one phase and now with its own memory.**
> Before a check is finished, count what satisfies it. If more than one thing does, no single
> edit can break it. Three items running, and the same defect each time — which says the rule is
> right and that knowing it is not sufficient. Only the round finds them.

### Two of my own checks were wrong, both in ways this ledger has recorded before

**A pattern containing backticks, matched against `prose()`.** The helper strips ` * _ so that a
check does not fail on emphasis — which means a pattern written with backticks can never match.
The assertion passed nothing for a run and reported green until an unrelated failure exposed it.

**And `"<phases>" not in fmt`**, which failed on the heading of the section explaining why there
is no `<phases>` element. That is item 9's F3 lesson exactly: *a check that fails when the
absence is documented is a check pinned to prose*. The fix is the same one Phase 3 arrived at —
assert over the **parsed template**, which is a structural claim about what the block is, rather
than a word hunt over the document that describes it.
---

## 4 + 11 + 12 + 36 — the conventions, the derived list, the dual read, and the record

**Addresses:** P8, P12, P24, F3 · **Files:** `schema/decision-record.md` (new),
`schema/scripts/build-what-next.py` (new), `schema/scripts/migrate.py`, `schema/migration.md`,
`schema/prd-format.md`, `schema/core.md`, `skills/breakdown/scripts/rename-feature.py`,
`skills/breakdown/scripts/check-references.py`, `commands/prd.md`,
`tests/fixture/prd/schema-4/**`, `tests/fixture/prd/SCHEMAS.json`, `tests/test_toolchain.py`,
`tests/mutants/phase4-4-11-12-36.py` (new)

### Item 4 became two rules that refuse, and one that item 3 inherits

Most of item 4's text — *"migrate the corpus conventions into the templates"* — landed with the
schema-4 group, because the conventions **are** the template. What was left was the half that
makes them mean something:

- **R7:** an `excluded` feature carries a non-empty `<rationale>`.
- **R8:** a `superseded` feature carries `<superseded-by slug=>`, the slug resolves, and **no
  index entry points at it**.

**Both transform nothing.** A migration cannot invent a rationale for a decision it was not
present for. What it can do is refuse to finish while one is missing, which turns *"somebody will
notice"* into an exit code at the moment the file is being touched anyway.

**And they are checked on every feature file, not only on the ones being transformed.** The first
version attached them to a step, so an already-migrated tree could violate them in silence — a
rule about the artefact, wired as if it were a rule about the transformation. The distinction is
worth keeping: *what must be true of this file* and *what this change must do* are different
assertions, and only one of them belongs to a step.

**The reclassification itself is item 3's, and what it inherits is written down**: derive a
**ceiling**, never a value. A derivation that reports a value can contradict an author; one that
reports a ceiling cannot. Item 3 arrives a phase later and should implement rather than invent
it.

### Item 11 shipped with its producer, because the alternative is measured

Item 11 specifies `<authoring-gaps>` as *"DERIVED by item 6, never hand-maintained"* — and item 6
is in Phase 5. **An element with no producer is the defect item 51 exists because of**, so
`build-what-next.py` lands with the schema and item 6 becomes its caller rather than its author.

The argument is not theoretical. The corpus this schema was measured against listed **zero** TBD
items while carrying **twenty-one**. Hand-maintaining twenty-one entries against twenty-one files
has never once happened.

**It aggregates pointers, never copies.** A `<gap>` row carries slug, id, kind and date and *not*
the body, so a gap is written in one place and corrected in one place. A `<feature>` row covers
the other case: short of `defined` with no `<gaps>` block at all, so there is nothing to point at
and the shortfall is named directly.

**`excluded` and `superseded` are not shortfalls** and do not appear in the list. They are
decisions, and putting a resolved thing on a list of unresolved ones is how a list stops being
read.

### Item 12 is one line of behaviour and the check is the deliverable

`<status>` moved under `<meta>`. `list-prds.py` takes the *first* `<status>` in the file, so both
shapes work — but that had been true by accident of a regex, and item 12's whole content is that
it must stay true **on purpose** until every artefact is migrated.

So the check puts a migrated and an unmigrated `what-next.md` in one directory in front of the
real finder and asserts both are seen, neither reports `NO MARKER`, and the pair does not read as
`DISAGREE`. A PRD that cannot be found is a PRD that gets overwritten — F3, which cost an
interview before it was fixed.

### Item 36 was adopted, and the load-bearing part is not the section list

The template came from a project with nineteen records and a settled house style, so the checks
read a convention that already exists rather than asking for a migration.

**The part worth checking is the test, not the shape:** *no rejected alternatives means it is not
a decision record — it is a principle.* Without that line a principle gets filed as a decision and
read as though something was weighed, which is item 37's failure mode in its most ordinary form.

`**Drives:**` already had a reader before the template existed — `check-references.py` has
validated it since item 39 — so this item gave an existing check something to validate *against*.

### The finding this group produced: a rename has three new sites

Item 11 changed `what-next.md`'s feature references from `ref="features/x.md"` paths to
`slug="x"` rows in the derived block. The rename check caught it immediately, and the fix widened
`rename-feature.py` by one pattern — `slug="…"` as an **attribute**, which also covers
`<depends-on slug=>` and `<superseded-by slug=>`.

| Site | Arrived with |
|---|---|
| the filename | original |
| `<slug>` | original |
| `index.md`'s `file=` | original |
| `what-next.md`'s `ref=` | original |
| inbound markdown links | original |
| `what-next.md` (the sixth) | found by the fixture, item 42 |
| `<depends-on slug=>` | item 27 |
| `<superseded-by slug=>` | item 1 |
| `<gap slug=>` in `<authoring-gaps>` | item 11 |

Item 42 listed five. There are nine. **That is the argument for the postcondition rather than for
the list** — the script asserts that nothing resolves to the old slug afterwards, which is a claim
that survives the schema growing, and the list never could.

### Verification

Suite 82 → **86**. Three of the four checks run something rather than read it.

Mutation: **19/19 caught** against a stated-green baseline (`tests/mutants/phase4-4-11-12-36.py`) — after two passes at 14/19 and 18/19.

### Five misses, and one of them is a new variant

| Miss | Why it survived | Fix |
|---|---|---|
| an empty `<rationale>` is accepted | the test built a *missing* rationale, never an empty one | build the empty case |
| a dangling successor is accepted | the same fixture violated **two** rules, so the other one satisfied the assertion | one assertion, one rule — two fixtures |
| the guide's `ceiling` sentence is deleted | the word appears three times | scope to the sentence that *binds* reclassification to it |
| *never hand-maintained* is deleted | the phrase is also in the template's XML comment | scope to the section that argues it |
| the record names no reader | the script is also named in the `**Drives:**` prose, and a second row looked like a path | require a **link that resolves to a file on disk** |

**Two rules, one assertion** is the variant worth naming. The `superseded` fixture was both
missing a resolvable successor *and* still listed in the index, so the assertion `exit 1 and
"R8" in stderr` was satisfied whichever rule fired. Disabling either one left the check green.
It is the site-counting defect in a place counting sites would not have found it — the sites were
in the **fixture**, not in the document.

> **The rule, extended.** Count what satisfies a check — and count what satisfies its *fixture*
> too. A fixture that breaks two rules at once tests neither.

The last row took three attempts, which is the clearest measure of how hard this class is to see
by reading: *"the script is mentioned"*, then *"some row looks like a path"*, then *"a link that
resolves"*. Only the third is a claim about the world rather than about the text.

### And an orphan, left visible on purpose

The `list-prds.py` mutant also trips `/prd`'s overwrite-guard check, which runs the same script.
The harness reported it as an orphan — *a check failed that no mutant expected* — which is
exactly the ambiguity that warning exists to surface, and the reason one round earlier in this
build reported 6/13 when the truth was 11/13. Here it is a second check firing rather than a
MISSED being misattributed, and the spec file says so rather than silencing it.

---

## Phase 5 — Consumers, and the parity pass.

Plan order: `16` · `17` · `3` · `6` · `7` · `8` · `40` · `58` · `13` · `14` · `15` · `19` · `20` ·
`30` · `32` · `46` · `47` · `48` · `49` · `50` · `38` · `24` · `10` · `59`, on branch
`phase-5-consumers-and-parity`.

**Twenty-four items, and the plan calls them "small, once the schema carries the data."** That is
true of most of them and false of two, which is the reason this section exists before any of them
have landed: **Phase 5 is the first phase that will not fit in one sitting**, and deciding where it
breaks is cheaper done once, here, than rediscovered four times.

The measurement, rather than the impression. Phase 5 carries ~560 lines of specification against
Phase 4's ~595 — comparable volume, spread across 24 items instead of 15. But Phase 4 edited
`schema/` (~1,200 lines) and shipped in six commits; Phase 5 edits the **consumers** — five
breakdown skills (~2,000 lines), five execute skills (~2,000), the CRD path (~1,300), and a
regression suite that is already 4,813 lines and 86 checks. Two items are not small at any reading:
**40** is eight tests, a contract-grep across 93 edges and a second mode on item 8's agent, and
**59** needs the toolchain driven headlessly under `bypassPermissions`.

### The split, and why it falls where it does

**This is a sequencing decision, not a schema one, which is why it is recorded here.** The plan
stays a specification; it already fixes the *constraints* inside this phase — 30 after 16, 59 once
17 and 30 land, 46 and 47 immediately after 33 and 34. Those constraints admit exactly one
grouping that keeps each commit a single concern:

| Group | Items | Why these are one commit |
|---|---|---|
| **5a — CRD parity** | 46 · 47 · 48 · 49 · 50 | The plan says 46 and 47 land *"immediately after 33 and 34"* — which landed in `4f81d54`. **They are already lagging**, and lagging is precisely how two vocabularies acquire consumers. 48 and 49 are the same reach-across in the other direction; 50 is the check that stops the distance reopening. |
| **5b — the carry** | 16 · 17 · 30 · 59 · **19** · **20** | The boundary chain, in dependency order. 30 has nothing to check until `<source-feature>` exists; 59 is the first test that crosses the boundary 16, 17 and 30 specify. **19 and 20 were put in 5c and moved here** — both read `<moscow>` on a *task*, which is item 16's, and the plan opens Phase 5 with 16 for that reason. See the 13/14/15 entry. |
| **5c — the filters** | 13 · 14 · 15 | Three refusals and two flags, all reading tags that now exist. One commit because they are one behaviour: *the toolchain declines work it was told not to do, and says which.* |
| **5d — the definition bar** | 58 · 3 · 6 · 7 · 40 · 8 | 58 is the table of assertions, 6 is its caller, 3 feeds it, 40 supplies the mechanical tests and 8 takes the judgement half. Splitting these means designing the same checker four times — the argument Phase 3 made about `architecture.md`, arriving again. |
| **5e — the residue** | 10 · 24 · 32 · 38 | Independent of each other and of the above. Last because nothing waits on them. |

**5a and 5c are complete.** Neither matched its own row: 46-48 were a whole schema version with a migration and a new fixture, so 5a took two commits; and 5c turned out to be three items rather than five, because 19 and 20 depend on item 16 and belong in 5b. **The split was right about the seams and wrong twice about the contents**, which is the ledger doing its job rather than failing at it.

**Phase 5 is complete: five groups, seven commits, twenty-four items.** The boundary this row warned about did move, exactly where it said it would. 5d predicted it — *"item 40 is adapted from a policy written elsewhere and has not yet been read against this corpus"* — and read against it, two of its eight tests needed a different mechanical half and one of its two gate conditions turned out to be a schema change. **5e's row was right that the four items are independent and wrong about why they belong together**: three of the four are the same defect, an artefact carrying a stamp or a switch that nothing reads.

**Three groups found a defect on their first real run** — 59 at the boundary, 40 in four of six `defined` fixture features, 38 in a feature carrying an open decision and tasks. That is the phase's most useful output, and none of the three was visible to a static reading of the same files.

The phase's shape, in one line each:

| | What it established |
|---|---|
| **46 · 47 · 48** | the CRD path takes the parity changes, as schema-5 with a migration |
| **49 · 50** | two required fields get a reader, and parity becomes a table with probes |
| **13 · 14 · 15** | the toolchain declines work it was told not to do, and names what it declined |
| **16 · 17 · 30 · 19 · 20** | the pipeline stops discarding the document it came from |
| **59** | the boundary is crossed for the first time, and the crossing found two defects |
| **58 · 3 · 6 · 7 · 40 · 8** | one assertion, one owner — and `defined` acquires a bar it can fail |
| **10 · 24 · 32 · 38** | three stamps, a summary and a switch that nothing had ever read |

**Twenty-four items, seven commits, 86 → 109 regression checks, `known 0`**, and five mutation
rounds across the phase — 17/17, 6/6, 18/18 and one re-run — every one with a green baseline and
every file restored by hash. **Not pushed to `origin`**, which is now 13 commits behind `main`
before this phase is merged at all.

**5a and 5c first, in that order.** Both are edits to existing consumers with checkable
postconditions and no new design; 5a is overdue by the plan's own ordering. That leaves 5b and 5d —
the two expensive ones — a full sitting each, which is what they need rather than what is left over.

**What this split does not claim.** It does not reorder the phase: every constraint the plan states
between items is preserved, and the groups run in an order that satisfies all of them. It prices
nothing (A9 still holds), and 5d's boundary in particular is the one most likely to move, because
item 40 is adapted from a policy written elsewhere and has not yet been read against this corpus.

> **Read against it, and the prediction held.** Two of item 40's eight tests needed a different
> mechanical half than the plan implies, one of its two gate conditions turned out to be a schema
> change, and the boundary between its script and its agent is where both moved. The sentence
> above is kept rather than corrected: a prediction that was right about *where* the uncertainty
> lay is the evidence that the split was reasoned rather than guessed.

| Item | Status | Commit |
|---|---|---|
| **46 + 47 + 48** — the CRD path takes the parity changes (**schema-5**) | **Landed** 2026-08-27 | `6381ed8` |
| **49 + 50** — the PRD's scope/confidence readers, and parity as a check | **Landed** 2026-08-27 | `cfc8796` |
| **13 + 14 + 15** — the filters | **Landed** 2026-08-27 | `134a424` |
| **16 + 17 + 30 + 19 + 20** — the carry, and the two reporters that need it | **Landed** 2026-08-27 | `4bda3ca` |
| **59** — the runtime test across the boundary | **Landed** 2026-08-27 | `6fb646f` |
| **58 + 3 + 6 + 7 + 40 + 8** — the definition bar | **Landed** 2026-08-27 | `7966ed7` |
| **10 + 24 + 32 + 38** — the residue | **Landed** 2026-08-28 | `af42e48` |

**Suite:** 86 checks at branch point → **89** (46-48) → **91** (49/50) → **92** (13/14/15) → **95** (16/17/30/19/20) → **96** (59) → **103** (58/3/6/7/40/8) → **109** (10/24/32/38). `failed 0`, `known 0` throughout.

---

## 46 + 47 + 48 — the CRD path takes the parity changes, and becomes schema-5

**Commit:** `6381ed8` · **Addresses:** P31, P32 · **Files:** `schema/core.md`,
`schema/migration.md`, `schema/scripts/migrate.py`, `skills/crd/references/crd-format.md`,
`commands/crd.md`, `skills/crd/SKILL.md`, `skills/breakdown/SKILL.md`,
`skills/breakdown/scripts/check-writable.py`, `tests/fixture/prd/SCHEMAS.json`,
`tests/fixture/prd/schema-4/link-shelf/crd/archive-links.md`, `tests/fixture/prd/schema-5/`,
`tests/mutants/crd_parity.py`, `tests/test_toolchain.py`

### Why three items are one commit, and one schema version

The plan groups 46 and 47 as *"the same change reaching the CRD path"* and says they should land
immediately after 33 and 34, which they did not — they lagged by four commits, which is exactly
the interval in which two vocabularies acquire consumers. 48 joins them because all three rewrite
the same document and a schema version is the unit a migration can be written against. Splitting
them would have meant three migrations over one file, or two versions nobody could name.

`SCHEMAS.json` had already predicted this, listing 46, 47 and 48 under a `planned` schema-5 — and
listing item 11 with them, which had in fact landed in schema-4. That correction is recorded in
the file rather than deleted: a planned entry being wrong about *when* is the normal case, and the
correction is the only evidence anyone ever checked.

### What landed

- **46** — `<requirements>` is retired. Its entries are criteria, in one list with one id space.
  P31's unanswerable question, *which criteria discharge requirement 3?*, is dissolved rather than
  answered: there is no requirement 3 that is not itself a criterion.
- **47** — requirement-level MoSCoW becomes `P0|P1|P2`, and MoSCoW moves **up** to
  `<meta><priority>`. The vocabularies swapped levels rather than one absorbing the other. Both
  of `/breakdown`'s filters now have something to read on this path; before, `--requirement-level`
  selected nothing and `--priority` had no field to threshold against.
- **48** — `<gaps>` reaches the CRD, and with it a mechanical test for `draft` versus `ready`:
  a CRD marked `ready` must not carry a `<gap kind="specification">`. That is core §6's
  `<definition>` rule with one word changed, and it runs one way only, so nothing is ever promoted
  **to** `ready` by it.
- **48, the other half** — `/crd` gained a pre-write guard and `--resume`.

### The guard was generalised, not duplicated — and that is the repository's most repeated lesson

`/crd` was documented as stateless and wrote `docs/crd/{slug}.md` with no check at all. That is F3,
which cost an interview on the PRD path before item 9 turned the guard into a program. The CRD path
had the identical hole and had simply not been caught by it yet.

The obvious implementation was a second script. Instead `check-writable.py` now takes **a PRD
directory or a single file**, because the problem it solves — *an artefact representing a long
conversation is about to be replaced* — was never PRD-specific. This ledger has recorded the same
shape three times now: `keep_awake` written inside one caller with its own docstring describing the
identical failure it was written for; item 60, a rule added without removing what it contradicted;
P18's TDD mandate enforced in three places and documented in a fourth. **A fix applied at the site
of discovery rather than at the level of the problem** is this repository's characteristic defect,
and this is the first time it was caught before shipping rather than after.

### The `wont-have` requirement has no honest target, and that is an escalation

The plan says only that CRD requirement priorities *"migrate from MoSCoW under item 41"*. Writing
the map exposed a value the plan had not considered.

`must-have → P0`, `should-have → P1`, `could-have → P2` are one to one. `wont-have` is not:
**`P0|P1|P2` has no *"not building this"* level, deliberately**, because that judgement belongs to
the whole item — which on this path is the document, in the MoSCoW that item 47 just put there.
So sending it to `P2` would make a declined requirement buildable by default, since
`--requirement-level` defaults to `P2`; and dropping it would delete something a person wrote down.
Both are decisions about the change rather than about its format.

**It escalates**, using machinery that already existed: exit 2, the file named, nothing written.
The first draft of core §4 collapsed `must-have` and `should-have` into `P0` and sent `wont-have`
to `P2` — that was written, read back, and replaced before it reached a test. It is recorded here
because a lossy map that looks tidy is the easy mistake, and the corpus would have carried it
silently.

### The first step whose mechanical half MOVES content, and the invariant it broke

R10 is the first rule that creates elements rather than relabelling them, and it walked straight
into an invariant `apply_steps` had held since item 41:

    if criterion_ids(text) != criterion_ids(before):
        "criterion ids changed -- count in must equal count out"

Equality was correct for every rule that existed, and wrong as a statement of the property worth
holding. What matters is that **an id which resolved before the step still resolves after it** —
`id` exists so that a citation from a commit message or a task file survives. Appending is
legitimate; renumbering an existing criterion is not. The invariant became a prefix check, which
is strictly stronger for every rule that adds nothing and is the actual claim.

That is also why the migration renumbers the **requirements** and not the criteria: an existing
criterion id may already be cited, and a requirement id was only ever local to a list that is
ceasing to exist. `derived-from="requirement-3"` carries the other half of the history, prefixed
rather than bare because after the merge a bare `3` is ambiguous across the two former spaces.

### Two of my own checks were wrong, and both in the same direction

The suite went red twice on assertions that were true of every artefact that existed when they
were written, and false the moment a new shape arrived. Both were **overreach**, and neither was a
defect in the change:

1. **`every criterion must carry derived-from`.** Core §2 says `derived-from` is *migration only*.
   Until schema-5 every criterion in a mixed step came from a migration, so the sweep was
   accidentally correct. The fixture CRD is the first artefact carrying **authored** criteria beside
   **migrated** ones, and demanding the attribute on all six would have required back-dating a
   provenance the authored pair does not have.
2. **`no criterion may carry a pattern`.** Same shape: the authored criteria legitimately have one.

Both are now asserted **per criterion, against the same criterion in the source, and only where
the step touched it** — a criterion the step left byte-identical is the author's and is not the
migration's to be judged on. This does not weaken the earlier steps: mutating R4/R5 so they stop
writing `derived-from` still turns four checks red, which was measured rather than assumed.

The third failure was `the two priority levels stay in two vocabularies`, which swept **every**
table row in core §4 and reported eight levels once item 47 gave the section a second table. That
is *prose checks need a region and a shape* arriving again — the region was right and the shape was
missing. It now takes the first contiguous run of table rows.

### The fixture problem, and the rule that decided it

schema-5 changes CRDs and nothing else, and **there was no structured CRD anywhere in the corpus**.
`tests/fixture/crd/change-request.md` is stakeholder prose — `/crd`'s *input*, deliberately
unstructured — so the CRD rows in `migration.md`'s table had never been exercised by a golden
comparison at all.

The honest place for a first CRD was schema-1, so it would have a history like everything else.
Item 43's rule 2 forbids it: *a non-current fixture is frozen, and needing something new to
exercise is a reason to touch the current schema only.* Back-filling it into three frozen versions
would have broken the rule that makes versioned fixtures affordable, to buy a provenance the file
does not have. So `link-shelf/crd/archive-links.md` arrives at schema-4 and says so in the
registry's notes.

It is the same project as the existing prose fixture — archiving links rather than deleting them —
which was not a coincidence worth avoiding: the two now sit either side of `/crd`, one the input
and one the output.

### Verification

`python tests/test_toolchain.py` — **86 → 89**, `failed 0`, `known 0`.

Three new checks, all of which run something:

| Check | The mechanism it runs |
|---|---|
| a CRD carries one list, not two | migrates a synthetic CRD and asserts the merged id space, not the format document's prose |
| requirement priority is `P0\|P1\|P2` on both paths | migrates one mappable CRD and one holding a `wont-have`; asserts exit 2 **and that the file is byte-identical afterwards** |
| `/crd` cannot silently replace a CRD | runs the guard on a file three ways — refuse, `--resume`, absent |

And the behaviour was watched before the checks were trusted:

- **R10, run by hand** on the schema-4 fixture: `<requirements>` gone, ids continuing from 3,
  `must/should/could` landing as `P0/P1/P2`, no `pattern` assigned, verdict `PARTIAL`.
- **the escalation, run by hand**: exit 2, the requirement named, `<requirements>` still in the
  file afterwards.
- **the guard, run by hand** on a CRD file: refuse / `--resume` / absent.

**Mutation round:** `tests/mutants/crd_parity.py`, seven mutants, **7/7 caught**, every file
restored byte-for-byte. It took four attempts, and two of the three failures were instrument
faults rather than results — recorded below, because one of them was a real hole.

### The round found a hollow check, and it is the site-counting rule's fifth confirmation

Round three reported `MISSED /crd stops running the overwrite guard -- NOT CAUGHT`. The mutant
replaced `/crd`'s guard invocation with the `test -e` prose it was written to retire, and **the
suite stayed green.**

The check asserted `"check-writable.py" in text`. `/crd` names the script **twice** — once plainly
and once with `--resume` — so breaking one invocation left the substring true. *If more than one
site satisfies a check, no single edit can break it*, which this ledger has now recorded five
times. The check asserts the invocation **with the path it guards**, both forms, and the absence
of the prose guard beside it; the round then reported 7/7.

**This is the one that would have shipped.** Every other mutant here broke something a reader
would notice. That one restored a defect the item exists to fix, and the only thing that saw it
was a mutant.

### Two instrument faults, and both were the same one

Rounds one and two reported `ANCHOR NOT FOUND -- mutant never applied` for that same mutant — the
harness's guard 2 doing its job, distinguishing *"never ran"* from *"survived"*. Without it the
round would have read 6/7 twice with a MISSED that meant nothing, and the real survivor in round
three would have looked like the same benign line.

Both faults were **backslashes eaten by a heredoc**, which is already in this session's memory and
which I walked into twice more:

1. Writing `commands/crd.md`, `\` before a newline reached Python as a **line continuation**, so
   the two-line command collapsed into one with a doubled space — and the mutant's two-line anchor
   could never match a file that no longer had two lines.
2. Fixing the mutant file, the patch script's own search string was mangled the same way, its
   `assert` fired, and — because it was a separate command rather than part of the `&&` chain —
   the round ran anyway against an unchanged anchor.

The fix both times was to stop routing text with backslashes through a shell: `Edit` for the
mutant file, and **verifying the anchor matched exactly once before launching the round** rather
than after. A harness that reports on an anchor it never applied is not lying, but it is a result
that needs reading rather than skimming.


---

## 49 + 50 — two required fields get a reader, and the parity ledger becomes a test

**Commit:** `cfc8796` · **Addresses:** P19, P21, P30 · **Files:** `schema/core.md`,
`schema/parity.md` (new), `skills/breakdown-analyze-prd/SKILL.md`, `skills/breakdown/SKILL.md`,
`skills/breakdown/scripts/check-scope.py` (new), `tests/mutants/scope_and_parity.py`,
`tests/test_toolchain.py`

### Why these two are one commit

49 is the last thing the CRD path had that the PRD path lacked, and 50 is the check that stops
the gap reopening. Landing 49 without 50 would have closed the last measured asymmetry with
nothing measuring the next one — which is exactly how the twelve in §5 J accumulated.

### What landed

- **49** — `<scope>` and `<confidence>` reach the PRD path and, more to the point, **get a reader
  on both**. `breakdown-analyze-prd`'s feature pass emits one prediction per feature into
  `analysis.json`; `check-scope.py` holds it against the task count in `manifest.json`.
- **50** — [`schema/parity.md`](../../schema/parity.md): sixteen capabilities, each with a
  verdict, and each claim carrying a `file :: string` probe the suite runs.

### The defect being fixed was not "the PRD path lacks two fields"

It was that **both fields were required on the CRD path and read by nothing at all.** A required
field nobody reads is worse than an absent one, because it looks like a signal — and this one
misled the plan itself: items 29 and 31 were each written as if from nothing, when `<confidence>`
and `<scope>` had been sitting in `crd-format.md` the whole time.

So the shape of the fix is the reverse of what the item title suggests. Giving the PRD path the
fields was the cheap half. The half that mattered was `check-scope.py`, which is the first thing
in this toolchain that reads either.

### Three decisions inside the cross-check, and each is about not being ignored

**It exits 0 even when it reports.** A prediction losing an argument with an observation is
information, not a failure. A check that can block on a model's size estimate is one that gets
disabled the first time it is wrong, and then it protects nothing.

**It fires on gross disagreement only.** Core §5's bands are counted in **files**; the observation
is counted in **tasks**; a task creates at most three files. The units do not line up, so the
comparison is band against band and only *non-adjacent* bands disagree — `small` against `medium`
is noise and `small` against `large` means one of the two is wrong. **The quiet case is as much
the subject as the loud one**, and it is mutated like one: a mutant that makes the check fire on
every adjacent pair is caught, because a cross-check nobody can silence is a cross-check nobody
reads.

**`confidence` is reported and never compared.** It grades the analysis, not the output, so there
is nothing to hold it against. It says *where the analyser was guessing*, which is the one thing
its output cannot otherwise recover.

### Item 49's PRD half is blocked on item 16, and the script says so in a number

The per-feature comparison needs tasks attributed to features, and a task file carries no
`<source-feature>` until **item 16** — which is in this same phase, in group 5b, and the plan's
sequencing note does not mention the dependency.

The script does not paper over it. It counts what it could not attribute and prints
*"4 of 4 task(s) name no source feature, so they were not compared (item 16 adds the
attribution)"*. **A cross-check that silently compares nothing is indistinguishable from one that
found no disagreement**, and this repository has shipped that exact mistake before. The
document-level comparison — the CRD path, where one document means the total *is* the observation
— works today and is what the check currently exercises.

### Item 50: the ledger had to become an artefact before it could become a test

The plan's fourth bullet asks that *"a capability present on one path and absent on the other is
listed, with a reason — the ledger above becomes a test rather than a paragraph that goes stale."*

The ledger in question is §5 J's *"Who is ahead where"*, and it lives in the **plan**, which is a
specification written at a moment in time. A check reading it would assert that the toolchain
still matches a snapshot, which is the opposite of what is wanted. So the table moved into the
repository as `schema/parity.md`, and it is core.md's counterpart: one file is what the two paths
share, the other is the distance between them.

**Every claim carries a probe**, and the probes are what make it a test rather than a document.
`Uncertainty recorded as gaps | schema/prd-format.md :: <gaps> | crd-format.md :: <gaps> | both`
fails if either file stops containing the string. A `prd-only` row fails if the CRD side quietly
grows evidence. An asymmetric row fails if its reason is missing. All three are mutated.

**`open` is a verdict, not a failure.** Three rows carry it — declared dependency edges, a data
model channel, and the architecturally-significant flag are all PRD-only with nobody having
decided whether they should be. The suite **lists** them rather than refusing them, because an
unexamined asymmetry is a fact about this project and the defect the file prevents is one nobody
has written down.

**Verdicts are about capability, not spelling.** `<scope>` is an element in a CRD and a field in
`analysis.json` on the PRD path, and the row says `both`. A table keyed on element names would
have reported a difference that means nothing — and the symmetric difference of the two format
documents is sixty elements, almost all of which are legitimately one path's own.

### The same mistake twice in one session, one commit after writing it down

The round reported `6/8`, and **both survivors were the site-counting rule** — the defect recorded
in the previous entry, made again immediately:

- `feature_signals` appears twice in `breakdown-analyze-prd` — in the output block and in a
  paragraph about the output block. Asserting the bare string was satisfied by the prose while the
  schema was renamed out from under it.
- `check-scope.py` appears **three** times in `/breakdown` — once as a command and twice in prose
  about the command. Deleting the command left two mentions and a green suite.

Both now assert a **region and a shape**: `"feature_signals"` inside a fenced ```json block, and
the runnable `scripts/check-scope.py {tasks_dir}` rather than the filename. The round then
reported 8/8.

**This is the rule's sixth and seventh confirmation, and knowing it was not enough.** The previous
entry states it plainly, and it was written the same afternoon. What actually caught both was a
mutant — which is the argument for the harness, and it is a stronger argument than the rule.

### Verification

`python tests/test_toolchain.py` — **89 → 91**, `failed 0`, `known 0`. The parity check prints its
open rows on every run: *(3 open asymmetry/ies: Declared dependency edges; A data model channel;
Architectural significance flag)*.

Behaviour watched by hand before the checks were written, over all three of `check-scope.py`'s
shapes: a gross disagreement reported at both levels, an adjacent pair staying quiet, and a
missing input exiting 1 rather than reporting nothing.

**Mutation round:** `tests/mutants/scope_and_parity.py`, eight mutants, **8/8 caught** after the
two survivors above were fixed. Every anchor was verified to match exactly once **before** the
round was launched — the correction to last round's method, where two attempts were wasted on
anchors that never applied.

---

## 13 + 14 + 15 — `/breakdown` declines work, and names what it declined

**Commit:** `134a424` · **Addresses:** P1 · **Files:** `skills/breakdown/SKILL.md`,
`skills/breakdown/scripts/select-features.py` (new), `tests/mutants/filters.py`,
`tests/test_toolchain.py`

### The group is three items, not five — and that is a correction to this ledger's own split

**Items 19 and 20 moved to 5b.** Both read `<moscow>` on a *task*, which item 16 puts there, and
item 16 is in 5b. The plan's own Phase 5 ordering opens with 16 for exactly this reason; the
five-group split published two commits ago claimed *"every constraint the plan states between
items is preserved"*, and for these two it was not.

Building them here was possible and would have been wrong. Item 20 refuses a task carrying
`<moscow>wont-have</moscow>`; with no producer for that element the refusal can never fire, which
is a **guard with no producer** — the exact mirror of the field-with-no-reader defect this plan
has spent forty items removing, and which item 49 had just finished removing two commits earlier.

### What `/breakdown` did before this

**It filtered nothing.** Every feature named in the index became tasks. A `wont-have` feature
nobody intends to build, a `superseded` one already absorbed into another, and a `tbd` one
consisting of a name and a sentence all reached `/execute` as work. That is P1, and the useful
observation is that it is **three rules wearing one symptom**:

| Rule | Drops | Kind of rule |
|---|---|---|
| **13** | `wont-have`, `excluded`, `superseded` | **correctness — no flag, no override** |
| **14** | anything below `--priority` | the operator's choice |
| **15** | a `<gap kind="specification">`, or `tbd` without `--include-tbd` | a defect in the PRD, **named** |

Only the middle one is a preference, and most of the check is about that distinction rather than
about the filtering. A selector that filters correctly but lets item 13 be overridden has turned
somebody's decision into a suggestion.

### `--include-tbd` reaches the status and never the gap

This is item 15's real content and it is easy to get backwards. `<definition>` is a **summary**;
`<gaps>` is the **detail**. So:

- a `<gap kind="specification">` refuses the feature **whatever its declared status**, because it
  is the author saying the specification is incomplete — and `--include-tbd` does not reach it
- the other four kinds — `dependency`, `decision`, `evidence`, `ownership` — **warn and do not
  refuse**. They say the feature is specified but not yet *buildable*, which is a scheduling fact
  rather than a definition defect

A boolean `blocking=` could not have drawn that line, which is why item 29 gave `<gap>` a `kind`.
The mutant that makes every kind refuse is caught, and it is the one worth having: a selector that
halts an overnight run on an open question is one that gets switched off.

### Every reason is reported, not the first that matched

The plan does not ask for this; the fixture did. `quokka-telemetry` is `wont-have` **and** carries
a `specification` gap **and** is `in-progress`. Reporting the first match would make the other
reasons invisible, so fixing one would appear to change nothing — and an operator would learn that
the report cannot be acted on.

**The same property is why the checks use synthetic PRDs rather than the fixture.** A feature
satisfying three rules at once tests none of them: remove any two and the check still passes.
That is [[count-the-sites-that-satisfy-a-check]] in the fixture rather than in the assertion, which
Phase 4's last round had already recorded as the extension to that rule. Each probe PRD here gives
one feature exactly one property.

### The sentence item 15 exists to make sayable goes to stderr

*"5 must-have features are not defined enough to break down"* is, as the plan says, the single most
useful sentence `/breakdown` could say about a PRD. It is on **stderr**, separately from the
per-feature listing, precisely so it cannot become line eleven of twenty and read as routine. The
skill is told to relay it verbatim before anything else.

Two of the ten mutants attack the report rather than the filtering, and they matter as much: a
selector that drops exactly the right features and says nothing has failed the item. A silently
omitted must-have is worse than the unfiltered behaviour this replaced.

### Item 14 gave item 47 its reader, one commit later

`--priority` reads `priority=` from the index on the PRD path and `<meta><priority>` on the CRD
path. The second only exists because item 47 moved MoSCoW up to the document last commit — and the
plan predicted exactly this: *"it makes `/breakdown`'s `--priority` threshold mean something on the
CRD path, where today it means nothing."* A `should-have` change request is now declined by
`--priority must-have`, which is asserted by running it.

**The default is `could-have`, and the default is the load-bearing part.** It preserves today's
behaviour minus item 13, so the flag adds capability without silently changing what an existing
invocation builds. Two mutants attack it — a drifted default and an off-by-one threshold — because
both are silent.

### Verification

`python tests/test_toolchain.py` — **91 → 92**, `failed 0`, `known 0`.

Watched by hand before the check was written, over every path: all three rules in isolation, the
warn path on a `decision` gap, `--include-tbd` reaching `tbd` but not a specification gap, the
stderr call-out, multi-reason reporting, exit 1 when nothing is selectable, and the CRD threshold.

**Mutation round:** `tests/mutants/filters.py`, ten mutants, **10/10 caught on the first
attempt** — the first round in this phase to open at 100%. Two method changes account for it, both
of them corrections made earlier in the same session: every anchor was verified to match exactly
once **before** launching, and every assertion about a script names a **runnable invocation or a
fenced block** rather than a filename that prose also satisfies.

---

## 16 + 17 + 30 + 19 + 20 — the pipeline stops discarding the document

**Commit:** `4bda3ca` · **Addresses:** P1, P15, P20 · **Files:**
`skills/breakdown/references/task-format-spec.md`, `skills/breakdown-generate-tasks/SKILL.md`,
`skills/breakdown/SKILL.md`, `skills/breakdown/scripts/build-manifest.py`,
`skills/breakdown/scripts/check-coverage.py` (new), `skills/breakdown/scripts/check-scope.py`,
`skills/execute/SKILL.md`, `skills/execute/scripts/write-state.py`,
`skills/execute/scripts/preflight.sh`, `skills/execute/references/state-schema.md`,
`tests/fixture/prd/SCHEMAS.json`, `tests/mutants/carry.py`, `tests/test_toolchain.py`

### What actually changed

A task now knows where it came from. Before item 16 it did not — attribution downstream was a
**string match on the task's `<name>`**, which is why item 21's tier probe had to invent slugs
that could not occur by coincidence, and why `check-scope.py` shipped with nothing to attribute.

- **16** — `<meta>` gains `<source-feature>`, `<moscow>`, `<satisfies-criteria>` and
  `<requirement-level>`. `build-manifest.py` carries all four into `manifest.json` (`1.0` → `1.1`).
- **17** — `<context>` carries the criteria **verbatim with their ids** and the feature's own
  `<data-model>`, instead of `<prd-excerpt>` prose somebody rewrote. Each `<test covers=>` names
  the criterion it discharges.
- **30** — `check-coverage.py`: does the task set match the document.
- **19** — both tiers reach `execute-state.json` per task, and a derived `tiers` block groups them.
- **20** — `preflight.sh` refuses a task carrying `<moscow>wont-have</moscow>`, naming the file.

### `<priority>` is untouched, and that is why the others have the names they do

P3. `<priority>` is an integer meaning *merge order within the layer* and has meant that since the
beginning. Overloading it with MoSCoW would leave every reader ambiguous about which of two
unrelated orderings it was reading, so the feature's tier arrives as `<moscow>` — a name that was
free.

**A check asserting only "the tier is somewhere in `<meta>`" would pass on the overload**, so the
mutant that puts `must-have` inside `<priority>` is in the round, and it is caught.

### Two items were moved here from 5c, and this is why

Items **19 and 20 both read `<moscow>` on a *task***, which nothing wrote until item 16. Building
item 20 in 5c would have shipped a refusal that can never fire — a **guard with no producer**,
which is the mirror of the field-with-no-reader defect item 49 had just finished removing. The
plan opens Phase 5 with item 16 for exactly this reason and the five-group split had missed it.

### A defect I shipped two commits ago, found by wiring the next item to it

`check-scope.py` (item 49, `cfc8796`) read `manifest["tasks"]`. **The manifest key is
`task_inventory`**, and has been since it existed — `write-state.py` reads it correctly.

The reason it passed: **its test seeded the same invented key.** The fixture agreed with the
implementation, so the check validated the code against itself and attributed nothing on a real
manifest. That is the failure mode that reads exactly like a pass, and no amount of mutation of
`check-scope.py` would have caught it, because the mutants and the fixture shared the mistake.

The fix is not the one-word key change. **The test now builds the manifest by running
`build-manifest.py`**, so the check is held against the artefact the toolchain actually produces
rather than against a dict I wrote to match my own code. Reverting the key and watching the
corrected test fail is what established that it now catches it.

**The general rule, which this ledger has not previously stated:** a fixture hand-written to match
the reader is not a fixture, it is a restatement of the reader. Where a producer exists, run it.

### Item 30 does not restate the assertion that already has a home

The plan lists five assertions for the coverage check. The fourth — every architecturally
significant feature named by a decision record's `**Drives:**` — **is not in `check-coverage.py`**,
because `check-references.py` already runs it. A rule stated in two programs is a rule that gets
changed in one of them, and the script names where the fifth lives so a reader does not conclude
it was dropped.

### The shortfall is named, and the mutant that proves it keeps the count right

*"1 should-have feature has no task: tag-links"* is the sentence. A check reporting *"1 feature has
no task"* passes any test that a check naming the **wrong** feature would also pass — which is
item 59's third assertion, arriving early as a mutant that leaves the count correct and removes
only the name.

### Items 16 and 17 are not a schema version, and the registry now says so

`SCHEMAS.json` had them listed under a `planned` schema-6. They are not: **a task is not a
versioned artefact.** `migrate.py` recognises five roots and a task is none of them, because tasks
are *regenerable output* — the way to move a task set to a new shape is to re-run `/breakdown`,
not to migrate it. Versioning them would have meant a fixture and a migration step for files
nobody hand-edits. `manifest.json`'s own `MANIFEST_SCHEMA_VERSION` went `1.0` → `1.1` instead,
which is the right granularity.

The prediction is corrected in the file rather than deleted, per the convention item 11's
correction established.

### Verification

`python tests/test_toolchain.py` — **92 → 95**, `failed 0`, `known 0`.

Watched by hand before the checks were written: `check-coverage.py` over all five outcomes
(complete → exit 0; a feature with no task, named; a missing criterion; a criterion id that does
not resolve; a task from a `wont-have` feature); `preflight.sh` refusing and then permitting; and
`write-state.py` producing the `tiers` block from a real manifest.

**Mutation round:** `tests/mutants/carry.py`, eleven mutants, **11/11 caught on the first
attempt** — the second consecutive round to open at 100%, on the two method corrections made
earlier in this phase.

**Item 59 is not in this commit.** It is the runtime test across this boundary, it needs the
toolchain driven headlessly, and it is the assertion that everything above is *specified* rather
than *demonstrated*.

---

## 59 — the boundary is crossed, and the first crossing found two defects

**Commit:** `6fb646f` · **Addresses:** A8/R13 · **Files:** `tests/boundary-test.py` (new),
`tests/test_toolchain.py`

### What the item was for, and it delivered exactly that

*"Items 13–17, 19, 20 and 30–32 all specify behaviour at that boundary and **no run has ever
crossed it with an input this plan's schema describes**. For a document whose central
methodological complaint is that static agreement is not evidence, that ratio is the wrong way
round."*

It has now been crossed, three times, and **the first crossing found two defects that no static
reading would have shown.** That is the item paying for itself on the day it landed.

### The shape: a grader, and a live mode, split

`probe-p1.py` established this and stated why: *"a grader that has only ever been exercised by
the expensive path is a grader nobody has checked."* So `--grade` runs offline against any task
set, and `--run` builds a workspace, runs `/breakdown` live, and grades what it produced.

The regression suite drives `--grade` on every run, **breaking each of the five assertions in
turn** — a compliant task set passing is the weakest half, and a grader returning 0
unconditionally would pass that and nothing else.

**Assertion 3's break is the one worth naming.** It mutates `check-coverage.py` so it reports the
**wrong** feature while keeping the count correct, and asserts the grader is not fooled. A test
that does not force that cannot distinguish a check that counts from one that attributes.

### The live result

Three runs. The first two failed for reasons in the harness, and both are worth recording because
one of them is a compliment to the toolchain.

**Run 1 — `acceptEdits` was the wrong permission mode.** `/breakdown` is script-gated at Phases 1,
2, 2a and 5, and `acceptEdits` permits file edits without permitting a bundled script to run.
Every validator was denied.

**What the agent under test did then is the finding.** It refused to hand-simulate them, and said
why: *"These exist as scripts specifically because prose guards get ignored (the skill cites F15
and P16 on this), so a run that fakes them produces output nobody has actually checked."* The
skill's own argument for why guards are programs reached the agent reading it, and a run graded on
simulated gates would have been worse than no run. The script now uses `bypassPermissions` and
says why in a comment.

**Run 2 — the harness nested the PRD inside the project**, and `preflight.sh` refuses a target
containing `docs/prd/` (F15's own guard). The grader diagnosed it correctly rather than reporting
a toolchain defect: *"preflight refused a clean tree, so its refusal below proves nothing."* That
guard was written into assertion 5 on the assumption it would never fire; it fired on the second
run, against the harness.

**Run 3 — all five assertion groups ran.** Four clean:

| | Result |
|---|---|
| 1 | **19 criterion copies verbatim against the PRD, zero reworded** |
| 2 | 3 features named by 8 attributed tasks, resolving both ways |
| 3 | removing `list-links`'s 2 tasks was reported as `list-links` **and nothing else** |
| 4 | `{'must-have/P0': 5, 'should-have/P0': 3}` |
| 5 | preflight refused the won't-have task and named it |

**Assertion 1's headline held, and it is the one the plan singled out** as *"the one assertion
that would have failed for the whole life of the toolchain"*. Nineteen criteria arrived with their
ids and their text unaltered. P2 is fixed, demonstrated rather than specified.

### Defect one: `<source-feature>` is single-valued, and a real run invented a notation

The generator wrote `<satisfies-criteria>2,3</satisfies-criteria>` — bare, as the spec requires —
while carrying the criteria as `<criterion id="list-links#2">`. **It invented `feature#id`**, and
applied it in one of the two places, so the two halves of a task no longer refer to each other.

The cause is a gap in **item 16**, not a defect in the run. A task that legitimately covers
criteria from more than one feature — an integration task, most obviously — has no way to say
whose criterion it is carrying, because `<source-feature>` holds one slug. Item 30's coverage
check scopes cited ids per feature, so the neighbour's criterion is then reported as covered by
nothing.

**Run 2 hit the same wall and solved it differently**: it *split* the task rather than qualifying
the ids, and said so — *"`<source-feature>` is single-valued and `check-coverage.py` scopes cited
criteria per feature, so tag-links 3 would have been reported as covered by no task."* Two runs,
two independent workarounds, one gap. That is as strong as this kind of evidence gets, and the
plan never considered the case.

**The grader reports it as a FINDING rather than a failure**, because the criterion *text* is
unaltered — the thing item 17 exists to protect held. Conflating a qualified id with a reworded
one would bury the interesting half. **It needs a plan item**; it is not fixed here, because item
59's job is to measure and a schema change is the plan's decision to make.

### Defect two: a task cited a criterion it did not carry

`L1-003` declares `<source-feature>save-link</source-feature>` and
`<satisfies-criteria>1</satisfies-criteria>` and carries **no `<criterion>` at all** — while its
own prose asserts that *"its traceability is nonetheless real"*. It is not: item 17 requires the
criterion to be carried, and validation rule 0 in `task-format-spec.md` says both directions must
resolve within one file.

**The live run therefore exits 1, and that is the honest result.** It is recorded here rather than
worked around; a runtime test whose first crossing is made to pass by adjusting the test is a
runtime test that has measured nothing.

### What the run also produced, unprompted

The `/breakdown` run reported three defects it found and fixed in its own output — a `conftest.py`
that seven downstream tasks assumed and one task explicitly forbade; the orphaned criterion above;
and a `4-integration` layer dropped against the documented rule by a criterion in neither skill.
It also reported that a `breakdown-generate-tasks` fork made **false claims about a competing
concurrent task set that did not exist**, and generated all four layers when scoped to one.

None of that is graded here and none of it is this item's to fix. It is recorded because it is the
first evidence of any kind about how these skills behave under a real run, and because the last
one is a defect in a skill rather than in an artefact.

### Verification

`python tests/test_toolchain.py` — **95 → 96**, `failed 0`, `known 0`. The new check breaks all
five assertions and confirms the grader notices each.

**A bug in my own check, worth recording because it produced a false negative.**
`open(path, "w").write(open(path).read().replace(...))` truncates the file *before* the inner read
is evaluated, so it wrote an empty task — and the check then reported a missing failure that the
grader had in fact produced. Read first, then write. It is the same species as the `check-scope.py`
key defect two commits ago: **the test was wrong in a way that made the subject look wrong.**

**No mutation round.** The check *is* a mutation round — it breaks five things and asserts five
detections — and wrapping it in `mutate.py` would have mutated the mutator.
---

---

## 58 + 3 + 6 + 7 + 40 + 8 — the definition bar, and the first run of it found four defects

**Commit:** `7966ed7` · **Addresses:** A7/R12, P26, P16, P23 · **Files:**
`schema/checks.md` (new), `schema/core.md`, `skills/breakdown/scripts/check-status.py` (new),
`skills/breakdown/scripts/check-definition.py` (new), `skills/breakdown/scripts/check-rename.py`
(new), `skills/breakdown/scripts/check-references.py`, `agents/prd-criteria-author.md` (new),
`commands/prd.md`, `tests/fixture/prd/SCHEMAS.json`, `tests/mutants/definition-bar.py` (new),
`tests/mutants/significance-screen.py` (new), `tests/test_toolchain.py`

### Why six items are one commit

The group's own row said it: *"58 is the table of assertions, 6 is its caller, 3 feeds it, 40
supplies the mechanical tests and 8 takes the judgement half. Splitting these means designing the
same checker four times."* That held. Item 6's eleven-assertion prose list cannot be split from
the table that gives each assertion an owner, and the owners cannot be written without deciding
which half of item 40 is mechanical — which is item 8's boundary from the other side.

### What landed

- **58** — [`schema/checks.md`](../../schema/checks.md): twenty-one assertions, one owning script
  each, every caller named. Modelled on `parity.md` deliberately: **every owner and every caller
  is checked by running it**, so a row whose script has been deleted or whose caller has stopped
  invoking it fails rather than reads well.
- **3** — `check-status.py`. Declared `<definition>` against the ceiling the file's own structure
  supports, `<gaps>` well-formedness, and gap age.
- **6** — `/prd`'s Phase 7 becomes a **caller**: four runnable invocations, a table of what each
  output line means, and the trailing *Consistency Checks* section stops restating them.
- **7** — `--resume` re-runs those checks across **every** feature before resuming, in
  Initialization, where the resume decision is actually made.
- **40** — `check-definition.py`. Five of the eight tests, mechanically; the other three named and
  routed rather than approximated.
- **8** — `agents/prd-criteria-author.md`, two modes, `tools: Read Glob Grep` — the proposal-only
  rule enforced by what the agent *holds* rather than by what it says.

### Departure 1 — item 3's rule was restated in elements, and its byte counts are gone

The measured rule tested for *"a data-model / dependency / relationship marker in the notes"* and
*">=1000 bytes of notes"*, with `<=2 criteria` scoring `tbd`. Both were proxies for elements that
did not exist when it was written: at schema-4 the marker became `<data-model>` and the dependency
became `<depends-on>`.

**Run as specified, against the reference fixture, that rule scores three of four `defined`
features as `tbd`** — because the fixture's features are small on purpose. A small feature that is
completely specified is not under-defined, and a proxy kept alongside the thing it stood for is a
second answer to one question. So the ceiling is now section 4.2's `Required content` column and
nothing else: 0 criteria → `tbd`; ≥1 criterion → `in-progress`; plus `<user-story>` and no
specification gap → `defined`. **Zero contradictions on both fixture projects**, which is the same
baseline Rule B recorded, reached by reading elements instead of counting bytes.

### Departure 2 — the ambiguous band moved rather than disappeared

Item 3's rule was three-valued, and the third value meant *the counters cannot see this one*. The
element ladder is deterministic and has no ambiguous band — but the question it could not answer
did not go away, it went to `check-definition.py`, which has eight tests for it. `check-status.py`
asks whether the label is **contradicted by the file's own structure**; the bar asks whether the
feature is **actually well defined**. Two questions, two scripts, two exit codes.

**The silent direction is asserted as hard as the loud one.** A feature declared *below* its
ceiling exits 0 and prints `ESCALATE`; only `--strict` raises it. That is the case the whole
ceiling design exists for, and the mutation round breaks it in that direction specifically.

### Departure 3 — item 58's table was wrong about two owners, and the corrections are in it

The plan's table named `check-banned.py` (56) and `check-artefacts.py` (22, 43, 44). Neither name
exists:

| Plan said | Actually |
|---|---|
| `check-banned.py` owns `<banned>` and `<task-limits>` | landed at item 56 as **`check-rules.py`**, with `check-architecture.py` owning the `<rules>` parse |
| `check-artefacts.py` owns schema conformance | **not built.** Item 22 is Phase 6, deliberately last |

The second is carried as a **row with no owner** rather than omitted, and the suite asserts at
least one such row exists. An assertion this plan has specified and not built is a fact about the
project; deleting the row would make Phase 6 invisible in the only place that enumerates it.

### Departure 4 — one half of item 40's gate is deferred, and it is a schema change

The gate is *"the mechanical tests pass **and** a review has been recorded"*. The first half is
`check-definition.py`. **The second half has nowhere to be recorded**: no artefact carries a
review marker, and adding one is a schema version — a migration step, a fixture, a frozen hash.

`SCHEMAS.json` already predicted this, listing schema-6 as arriving with items 38 and 40. That
entry is now updated to say what it is *for* rather than that it is a placeholder, and item 38 is
in the next group. `/prd` says the missing half out loud rather than treating its absence as a
pass, which is the honest reading of a gate with one working half.

### Departure 5 — two of item 40's tests got a different mechanical half than the plan implies

- **Test 5** (*external dependencies as providers with roles, not brand names*) has no per-feature
  home on the PRD path — external dependencies live in `index.md`. Its mechanical half is
  therefore *every `<dependency>` names a `<purpose>`*: a name with no role is exactly a brand
  name, which is the half a script can settle.
- **Test 6** (*decision records discharged, not merely cited*) splits. `check-references.py`
  already resolves every `ADR-NNN` and reports a citation of a superseded record; whether the
  record's obligations appear as criteria is judgement. So the bar asserts **neither** and names
  both — a rule stated in two programs is a rule that will be changed in one of them.

### Departure 6 — the ASR screen reads two of six `because` values, and says which four it will not

Item 6 asks for *"architecturally-significant candidates, screened by the published ASR heuristics
and reported as candidates only, never applied"*. Only two of the six `because` values leave a
mark in a file a script can read: a **quality attribute** named in the feature's own text, and
**cross-cutting** reach, measured as the number of other documents that chose to name this
feature. `first-of-a-kind`, `risk` and `constraint` are judgements with no signal in the file, and
guessing them produces a candidate list nobody reads.

It lives in `check-references.py` rather than in a new script, because that file already reads
`<architecturally-significant>` from the other direction — a flagged feature no record drives.
One element, one reader, now in both directions: flagged-and-undriven is `STALE`, unflagged-and-
qualifying is `CANDIDATE`.

**A candidate never reaches the exit code, including under `--strict`.** A heuristic that can fail
a build has been promoted to a rule behind everyone's back, and the mutation round breaks it in
exactly that direction. Reach also excludes `index.md` and `what-next.md`, which name every
feature by construction and would otherwise hand each one two free edges; the check asserts the
number, not merely that a candidate was reported.

### The finding: the bar fires on four of six `defined` features in the reference fixture

First run, no mutation:

| Feature | Fails |
|---|---|
| `list-links` | t2 — no `unwanted-behaviour` criterion; t4 — no `<data-model>` |
| `zebra-signin` · `walrus-export` · `narwhal-theme` | t4 — no `<data-model>` |

`save-link` and `tag-links` pass every mechanical test, so this is a bar with both controls
present rather than one that reports on everything.

**The fixture is not relabelled and not rewritten, and both refusals have reasons.** Section 4.2's
own principle is that a wrong status usually signals wrong *content*, so lowering four
`<definition>` tags to silence the bar is the failure mode the gate is deliberately too weak to
force. And fixing the content means editing `schema-4`, whose PRD features are byte-identical to
`schema-5`'s and whose hash is frozen — plus `schema-1` through `schema-3`, since the migration's
golden comparison would otherwise stop matching. That is a schema-6 change, and it is recorded as
one in `SCHEMAS.json` rather than left as a surprise for whoever runs the check next.

**This is item 59's shape arriving one commit later**: the first time an assertion is actually run
against the corpus, it finds something. Four somethings, all of them real, none of them visible to
a static reading of the same files.

### What item 6's eleven bullets became

| Item 6 said | Owner |
|---|---|
| derive status for every feature, report each mismatch with a reason | `check-status.py` |
| index ↔ `features/` reconcile; orphans, dangling entries, a feature file still carrying `<priority>` | `check-rename.py` |
| a `superseded` pointer nothing references any more | `check-rename.py`, reported not refused |
| no reference anywhere to a slug that has no file | `check-rename.py` |
| criterion `id` uniqueness within a feature | `check-definition.py` |
| `<user-story>` present, in three parts, with a non-tautological *so that* | `check-status.py` (presence, for the ceiling) · `check-definition.py` (shape and screen) |
| `excluded` without `<rationale>`; `superseded` without a successor or still indexed | `check-status.py` |
| EARS pattern coverage; a criterion whose `pattern` is missing | `check-definition.py`, test 2 |
| unassigned criterion priority, as a count | `check-definition.py` |
| architecturally-significant candidates, screened and reported as candidates | `check-references.py` |
| external references resolve | `check-references.py` (item 39, already) |
| `<gaps>` well-formed, and the status rule | `check-status.py` |
| gap age, reported rather than judged | `check-status.py` |

Nothing in that list is unimplemented and nothing is implemented twice — which is what item 58 was
for, and it took writing the table to notice that *"no reference to a slug that has no file"* had
four claimants and *"user story present"* needed two, for different reasons.

### Verification

`python tests/test_toolchain.py` — **96 → 103**, `failed 0`, `known 0`.

**Two mutation rounds, 23 mutants, 23 caught**, both with a green baseline and every file restored
by hash:

| Round | Mutants | Result |
|---|---|---|
| `tests/mutants/definition-bar.py` | 17 | **17/17 caught** |
| `tests/mutants/significance-screen.py` | 6 | **6/6 caught** |

**A second file rather than an amended first one.** The first round is a measurement of seventeen
mutants against the code as it stood; the significance screen and the priority spread were written
after it, and re-running an edited first round would have replaced that record rather than
extended it.

**The four mutants worth naming** are the ones a looser check would have survived:

- the ceiling turned back into a *value*, so a feature held **below** what its content supports
  becomes a defect — the exact failure the first version of item 3's rule had on a real corpus
- test 7's **inbound** half silenced, which is the half that gets skipped and the half that
  catches contract gaps
- reach counting `index.md` and `what-next.md`, which name every feature by construction: the
  screen still reports candidates, it just reports *everything*. A check asserting only that a
  candidate appeared would pass it, which is why the check asserts the number
- a candidate made to fail under `--strict`, promoting a heuristic to a rule

Every script was also watched failing by hand before any check was written: a copy of the fixture
with one element removed at a time, including the three off-ladder rules (`excluded` with no
rationale, `superseded` with no successor, `superseded` still indexed) which no fixture exercises
and which were run against a scratch PRD built for them.

---

## 10 + 24 + 32 + 38 — the residue, and three stamps that finally have readers

**Commit:** `af42e48` · **Addresses:** P5, P22, P25, P28 · **Files:**
`commands/prd.md`, `schema/checks.md`, `schema/migration.md`, `schema/prd-format.md`,
`schema/scripts/build-what-next.py`, `skills/breakdown/SKILL.md`,
`skills/breakdown/references/architecture-format.md`, `skills/breakdown/scripts/build-manifest.py`,
`skills/breakdown/scripts/check-architecture.py`, `skills/breakdown/scripts/check-gate.py` (new),
`skills/breakdown/scripts/list-prds.py`, `skills/execute/SKILL.md`,
`skills/execute/scripts/check-compatibility.py` (new), `tests/mutants/residue.py` (new),
`tests/test_toolchain.py`

### Why these four are one commit, which the split row got right for the wrong reason

The row said *"independent of each other and of the above; last because nothing waits on them."*
Independent they are. What the row did not see is that **three of the four are the same defect**:
an artefact carrying a stamp, a summary or a switch that **nothing reads**. Item 24's two version
stamps had been written since item 4.5 and never read. Item 32's review view did not exist. Item
38's `<design-track>` was specified in `decision-record.md` with **no host artefact to write it
in** and no gate to read it. Grouping them turned out to be right for a reason nobody recorded.

### What landed

- **10** — `/prd` Phase 9 writes `features/{slug}.md` **one file at a time**, and a later edit
  re-reads only the feature being edited plus its index entry and its `<depends-on>` neighbours
  — the same three things item 8's agent is given, for the same reason.
- **24** — `check-compatibility.py` reads the manifest's two stamps at `/execute`;
  `build-what-next.py` writes `<toolchain-version>` into `what-next.md`; `list-prds.py` reports
  it before a resume.
- **32** — `build-manifest.py` renders `tasks-summary.md` from the traversal it already makes:
  one row per task with its source feature, tier, criteria, objective and files.
- **38** — `check-gate.py` at the `/breakdown` → `/execute` boundary, and `<design-track>` gets
  a host artefact at `architecture.md` format version **1.1**.

### Departure 1 — item 24's first bullet was already done, and was worth nothing

The plan says *"`/prd` writes `<toolchain-version>` into `what-next.md`"*. It already did:
`prd-format.md`'s template carried the element. It carried it **hardcoded as `2.0.0`**, with no
producer filling it in and no reader looking at it — a literal in a template, which is the exact
shape of the defect this plan spends most of its items removing, sitting inside the schema that
removes them.

So the work was not the element. It was the **producer** (`build-what-next.py` stamps it from
`plugin.json`) and the **reader** (`list-prds.py` reports it before a resume, so a PRD written by
an older toolchain is a sentence rather than a surprise).

### Departure 2 — the stamp is written once and never updated

The obvious reading of *"stamping"* is *keep it current*. That is wrong here, and the reason is
the same one that makes `check-status.py` derive a ceiling rather than a value: **a provenance
stamp that must equal the current version is not provenance, it is a constraint.** Rewriting it on
every derivation would make every `what-next.md` in every project read as stale on every plugin
release, and a file that is always stale is a check nobody runs.

So `stamp()` inserts when the element is **absent** and never touches an existing one, and
`--check` never fails on it. An older stamp is the ordinary case; it is exactly what
`list-prds.py` reports.

### Departure 3 — the plan predicted this stamp would replace shape detection. It does not

`migration.md` said `--detect` reads the file's *shape* *"until item 24 stamps
`toolchain_version`"*. Item 24 has now stamped it and detection stays keyed on the shape, for two
reasons the sentence had not considered: a `2.0.1` toolchain writes schema-4 and schema-5
artefacts alike, so the stamp cannot say which shape a file is in; and the shape is
self-correcting where a stamp is not — a hand-edited file has the shape it has, whatever the stamp
still claims. **The forward reference is corrected in place rather than left to be discovered**,
which is the whole reason the ledger records departures.

### Departure 4 — `<design-track>` was a switch with nowhere to live

`decision-record.md` specified it — `enabled`, `adr-dir`, off by default, *"with `enabled="false"`
the gate prints its report and returns"* — and **no artefact had a slot for it**. A reference
describing a setting no file can hold, read by a gate that did not exist. Both halves land here:
`architecture.md` gains it under `<rules>` at format version 1.1, and `check-architecture.py`
parses it.

**An element present with no `enabled` is refused, not defaulted.** An absent element means off,
which is the shipped behaviour; an element a project wrote and left incomplete is a project that
meant to say something and did not, and guessing which way would decide whether a gate stops a
run.

### Departure 5 — item 38's third assertion names an element that no longer exists

The plan says *"no blocking `<needs-clarification>` remains"*. That element was replaced by
`<gaps>` at item 29, and `kind` is what makes the assertion possible at all: core §6's
`specification`, `dependency` and `decision` block execution while `ownership` and `evidence`
warn. A boolean `blocking=` could not have made that distinction, which is item 29's own argument
arriving at its first real consumer.

**And the gate asks it of a different set than `select-features.py` does.** That script refuses a
feature carrying a specification gap at *selection* time; the gate asks, after generation, over
the features that **actually produced tasks** — a different set whenever `--include-tbd` or a
`--priority` threshold was passed, and a different question from *should we have started*.

### Departure 6 — the gate scopes significance to what was built

`check-references.py`'s assertion is about the PRD: *this feature is flagged and no record drives
it*. The gate's question is narrower — *may THIS task set proceed* — and a significant feature
nobody built cannot block a run of the ones that were. So the gate filters that script's output to
the features its tasks descend from.

**That is the gate's decision, not a re-reading of the owner's**, and the distinction matters:
the gate never recomputes coverage or significance, it *runs* `check-coverage.py` and
`check-references.py` and aggregates. A gate with its own opinion about coverage would be a second
answer to one question, which is the failure item 58's table exists to prevent.

### The finding: the gate's first run found a real one

On the reference fixture, with every feature built, assertion 3 fires:

> `tag-links: carries a <gap kind="decision"> and has tasks. An undecided question built anyway
> is an invented one`

`tag-links` genuinely does declare an open decision — whether a tag with no remaining links is
deleted or kept — and the toolchain has been generating tasks for it since the fixture was
written. **That is the third assertion earning its place on the day it landed**, and it is the
same shape as item 59's and item 40's first runs: the first time something is actually asked, it
finds something.

### The manifest goes to 1.2, and the reader's version is declared in the reader

Item 32's two fields (`objective`, `files`) are additive, so `MANIFEST_SCHEMA_VERSION` moves
`1.1 → 1.2` and a reader written against 1.1 still works. That is the rule item 24's check then
enforces — and the check **declares its own accepted version rather than importing the
producer's**.

That is the one design decision in this group most likely to look like duplication and be
"cleaned up". It is not duplication: importing `MANIFEST_SCHEMA_VERSION` would make producer and
reader equal by construction, every comparison would pass, and the check would be a function that
returns `True`. The producer's version and the reader's accepted range are different facts about
different programs. A regression check asserts the reader does not borrow it.

### A defect in my own work, recorded because the suite is one module

The 5e checks introduced a helper called `_task_tree`. **A helper of that name already existed**,
600 lines earlier, with a different signature — and Python resolves the name to the last
definition, so two unrelated checks (items 30 and 20) started failing with
`ValueError: not enough values to unpack`. Neither had been touched.

The suite is a single module with 109 checks and a flat namespace, and a helper added at the
bottom silently rebinds one added at the top. **The failure presented as a defect in the subject
and was a defect in the instrument** — the same species as item 59's truncating `open(...,"w")`
and the `check-scope.py` invented key. It was caught because the suite runs whole rather than per
check, which is the argument for keeping it that way.

### Verification

`python tests/test_toolchain.py` — **103 → 109**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/residue.py` — **17 of 18 caught**, then **18 of 18**
after the survivor was fixed.

### The one that survived, and why it is the most useful result in the group

> *"the gate stops caring what the coverage check returned"* — `if cov_code != 0:` becomes
> `if False:`.

The check asserted `SHORTFALL` and the feature's name were in the gate's output, and **both still
were**: the report prints the coverage verdict from its own exit code, independently of whether
that verdict is counted as a *finding*. So under the mutant the gate printed a shortfall naming
`tag-links` and then said `nothing to confirm` — with the design track on, a PRD feature carrying
no task at all would have gone to `/execute` unremarked.

**The check was reading the visible half.** The report is what a person sees; the finding count is
what does something. The fix asserts the consequence: with the track on and a coverage shortfall as
the only finding, the gate must exit 1 and say `confirmation required`. Re-run against the same
mutant, it caught it.

This is *"assert the mechanism, not the prose"* arriving in a new disguise — the assertion was not
pinned to a *sentence*, it was pinned to a *report*, which is one layer better and still one layer
short of the behaviour. **A report and the decision it feeds are two different claims, and a check
that tests the first passes when the second is deleted.**

**One orphan warning, and it is benign.** `every assertion has one owning script` also failed on
the mutant that removes `check-compatibility.py`'s invocation from `/execute` — correctly, since
`checks.md` lists that file as its caller and the table is checked by running it. Two checks
catching one mutant is the table doing its job, not a duplicate.

Every script was watched failing by hand first: every branch of the compatibility rule against a
built manifest (future major, older major, newer minor, absent, unparseable, provenance
mismatch); the summary absent, stale and current; the gate with the track off, on, with a coverage
shortfall and with an undriven significant feature; and `<design-track>` valid, unset and
non-boolean.

---

## Phase 6 — Hold it in place.

Plan order: `22` · `23`, on branch `phase-6-hold-it-in-place`.

**Last, deliberately**, and the plan's reason held: *"a schema check written against a schema still
moving is a check that gets edited rather than obeyed."* The schema stopped moving at Phase 4 and
its consumers caught up in Phase 5; this is the phase that makes both checkable rather than
observed.

| Item | Status | Commit |
|---|---|---|
| **22 + 23** — the artefact check, and the reader audit | **Landed** 2026-08-28 | `56f4554` |

**Suite:** 109 checks at branch point → **112**. `failed 0`, `known 0`. **Not pushed to
`origin`.**

**Phase 6 is complete, and so is the plan.** Six phases, **60 items** (plus `23a`, Phase 1's
split of item 23's first bullet), 62 commits over four days, and **39 → 112 regression checks**
with `known 0` throughout.

> **That sentence was true for about an hour, and it is kept rather than corrected.** Running the
> toolchain end to end the same afternoon produced five findings and five new items, and Phase 7
> is what came of them. The claim was not wrong about the *plan*; it was wrong about what
> completing the plan proves. **`the plan is implemented` and `the toolchain works` are different
> claims, and only the second one can be measured by running it** — which nothing had done against
> the current schema until after this line was written.

| Phase | Items | What it established |
|---|---|---|
| **1** | 8 | Fix what is broken today. No schema change |
| **2** | 4 | Make the rest testable — a fixture per schema version, and size refused before a prompt is built |
| **3** | 6 | The architecture artefact: five vendored opinions become a project's own file |
| **4** | 15 | The schema core, its migration, and four schema versions |
| **5** | 24 | Every consumer catches up, and the parity pass between the two paths |
| **6** | 2 | Hold it in place: one shape check, one reader audit |

**Four items found a defect the first time they were actually run** — 59 at the `/breakdown` →
`/execute` boundary, 40 in four of six `defined` fixture features, 38 in a feature carrying an
open decision and tasks, and 23 in three CRD elements with a producer and no consumer. **None was
visible to a static reading of the same files**, which is the plan's own thesis surviving contact
with its own corpus.

**What is left is not plan items.** `SCHEMAS.json` records the schema-6 content work these runs
turned up — five fixture files whose content predates the bars now applied to them — and
`readers.md` carries three `open` rows. Both are written down, which is the whole point.

---

## 22 + 23 — one shape check, one reader audit, and the audit found three

**Commit:** `56f4554` · **Addresses:** P10, P4, P2 · **Files:** `schema/readers.md` (new),
`schema/scripts/check-artefacts.py` (new), `schema/scripts/check-readers.py` (new),
`schema/checks.md`, `schema/core.md`, `commands/prd.md`, `skills/breakdown/SKILL.md`,
`tests/mutants/hold-it-in-place.py` (new), `tests/test_toolchain.py`

### Why two items are one commit

They are the two halves of one sentence. Item 22 asks *is this artefact the shape the schema
says*; item 23 asks *does anything read the elements that shape is made of*. Writing the first
without the second produces a validator that enforces a schema nobody consumes — which is P2
exactly, rebuilt with more rigour.

### What landed

- **22** — `check-artefacts.py`. Element and enum conformance for all five artefact kinds, run at
  the end of `/prd`, at the **start** of `/breakdown`, and over every fixture version in the
  suite.
- **23** — `check-readers.py` and [`readers.md`](../../schema/readers.md). Every element any
  schema document defines must be named by some script, skill, command or agent, or appear in
  `readers.md` with a verdict and a reason. Plus item 23's named smaller checks: each fixture
  validated against **its own** schema, and the `<definition>` enum asserted identical across the
  document and the two programs that implement it.

### Departure 1 — item 22 asked artefacts to declare a `schema_version`. They must not

The item says *"validating … against the declared schema"*, and `checks.md` carried that wording
as an ownerless row for the whole of Phase 5. It was written before item 41, which settled the
question in the other direction and gave the reason: **the marker is the shape.** A stamp drifts
from a hand-edited file; a shape cannot. Item 24 then confirmed it from the other end — a `2.0.1`
toolchain writes schema-4 and schema-5 artefacts alike, so a provenance stamp cannot answer a
shape question.

So `check-artefacts.py` **imports `migrate.py`'s detector** rather than reading a stamp or
deriving a second answer. Two answers to *"which schema is this file in"* is precisely the defect
this script exists to catch, and building it into the catcher would have been the plan's own
central finding arriving one more time.

The consequence is worth stating because it is not obvious: **an artefact that has lost an element
reads as an EARLIER version, not as a broken current one**, and is then judged by that version's
laxer rules. That is correct and it is also a blind spot, so the script reports the version it
landed on — *"is at schema-3; this toolchain writes schema-5"* — which turns a silence into a
sentence.

### Departure 2 — item 23's registry is an exception list, and the reader is measured

The obvious build is one row per element naming its reader. On this corpus that is **128 rows**,
hand-maintained, and every row a *claim* — which is the failure the rule exists to catch, rebuilt
as a maintenance chore. A declared reader is an assertion; a found one is a measurement.

So the script looks, in two tiers — a `.py`/`.sh` that names the element, or a skill, command or
agent that does — and `readers.md` records only what the search cannot explain. **13 of 128**, and
the file is 13 rows rather than 128.

**The defining document is not a reader**, which is the one line that makes the whole thing work:
count `prd-format.md` as a reader of `<user-story>` and every element reads itself, the audit
reports a clean 128 of 128, and it is a function that returns `True`. The mutation round breaks
exactly that.

### Departure 3 — the reverse direction is a report, and the numbers are why

Item 23 asks for the same test in reverse: every element a component *reads* must have a named
producer. Run naively it produces **32 candidates, of which 29 are usage-string placeholders** —
`check-coverage.py <prd-dir> <tasks-dir>` reads as two undefined elements, because an element name
and a CLI argument are the same token.

Three stated filters take it to **six**: drop docstrings, skip shell scripts, and treat a name the
file declares as an argument as an argument. What survives is three real signals —
`<affected-apis>`, `<phases>` and `<tbd-items>`, all **retired spellings a migration must still
recognise**, correctly read and correctly undefined — and three placeholders in comments.

It stays a **report**, because a filter tuned against one corpus is a heuristic rather than a rule,
and a heuristic that can fail a build has been promoted behind everyone's back. That is
`check-references.py`'s significance argument arriving independently at a second script, which is
some evidence it is the right shape.

### The findings, and there are two kinds

**One artefact is invalid, at every schema version.** `staff-service` declares
`<status>defined</status>` at document level in both `index.md` and `what-next.md` — outside core
§3's enum for that tag, which is `in-progress|complete`. Both files agree, so F3's `DISAGREE`
check passes; nothing had ever validated the *value*. It matters more than it looks:
`/prd --resume` finds incomplete PRDs by that tag, so a PRD saying `defined` is one nothing can
classify.

It is **reported and not fixed**, for the same reason item 40's four features were: the fixtures
are frozen and identical across five versions, so the fix reaches all of them and the migration's
golden comparison. `SCHEMAS.json` records it as schema-6 content work beside the other four.

**Three CRD elements have a producer and no consumer at all**, and one of them is `Required`:

| Element | |
|---|---|
| `project-ref` | **Required** in every CRD. Names the `PROJECT.md` the change is against — which `/breakdown` resolves by convention instead |
| `prd-ref` | The only structured link from a CRD back to the PRD that produced the feature |
| `feature-ref` | Carries an `id` into `PROJECT.md`, and nothing resolves it |

**This is P2's shape on the CRD path, found by the check written to find it.** P2 was
`<acceptance-criteria>` required and unread for the life of the toolchain; §5 J's parity pass
compared *capabilities* and never asked whether either side had a reader, so it could not have
seen this. All three are recorded `open` — a legitimate verdict, listed rather than refused,
exactly as `parity.md` does it.

### A check of my own that had to be relaxed, recorded because that is the ledger's job

Item 58's suite check asserted that `checks.md` always carries at least one **ownerless row**, on
the argument that an assertion specified and not built must be recorded rather than omitted. Item
22 was the last such row, and landing it made the assertion false: the suite went red for the
correct reason.

The rule was right and its encoding was wrong. What must hold is that an ownerless row **names the
item that will build it** — not that one must exist. Asserting the count made *finishing the plan*
a failure, which is a check that punishes the outcome it was written to encourage.

### Verification

`python tests/test_toolchain.py` — **109 → 112**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/hold-it-in-place.py` — **12 of 14 caught**, then **14 of
14** after both survivors were fixed. Both survivors were worth the round on their own.

**Survivor 1 was a defect in the script, not only in the check.** The mutant made the pre-rename
`<status>` spelling a *refusal* instead of a warning, and nothing changed — because the warning
was behind `at_least(version, "schema-2")` and **that branch can never run**. `<status>` is the
shape schema-2's rename keys on, so any file spelling it that way detects as schema-1, and the
gate excluded exactly the files the rule was written for. The fix gates on what *this toolchain*
writes rather than on the artefact's own version, which is the right semantic anyway: *you are
running a toolchain where this is called `<definition>`; this file says `<status>`.*

The check had passed on `"OLD" in stdout` — satisfied by the *other* warning the same edit
triggers, `is at schema-1`. **A token that appears in two different messages is not an assertion
about either**, which is Phase 3's whole lesson arriving in a new place. It now asserts the line.

**Survivor 2 was an unobservable guard.** `check-readers.py` excludes `docs/` and `tests/` from
the reader search, and removing the exclusion changed nothing: a markdown file outside
`skills`/`commands`/`agents`/`schema` is not a candidate reader anyway, so the guard only bites on
a `.py` under those directories — and the synthetic repository the check builds had no such file.
It has one now. The guard matters: **this suite names every element in the schema**, and counting
it would make *"somebody documented it"* indistinguishable from *"somebody consumes it"*, which is
the distinction the whole audit is made of.

**One orphan warning, benign and familiar.** `every assertion has one owning script` also failed
on the two mutants that remove a caller's invocation, because `checks.md` lists those files as
callers and the table is checked by running it. Two checks catching one mutant is the table doing
its job.

Both scripts were watched failing by hand first. `check-artefacts.py` against a mutated copy of
the reference fixture, one enum at a time, plus a retired element and a pre-rename spelling;
`check-readers.py` against a synthetic four-file repository where the answer is known by
construction — an element nobody names, an element declared away, a declaration for an element
that no longer exists, an invented verdict, and an element defined in a schema document and named
nowhere else.

---

## Phase 7 — What the run found.

Plan order: `61` · `62` · `64` · `63` · `65` · `66`, on branch `phase-7-what-the-run-found`. **66 was added to the plan while 63 was being built** — see §3.5 and section L there; the paragraph in item 63's entry below is the discovery note.

**Not planned; measured.** Phases 1–6 were specified by reading the corpus. This phase was
specified by watching the toolchain run, on 2026-08-28, immediately after the plan was declared
complete and merged — which is the only reason it exists, because the question *"is the plan fully
implemented"* has a different answer from *"does the toolchain work"* and only the second one can
be measured by running it.

| Item | Status | Commit |
|---|---|---|
| **61 + 62** — the two contradictions the run reported | **Landed** 2026-08-28 | `1aee6ad` |
| **64** — the generator is told where its commands run | **Landed** 2026-08-28 | `7709000` |
| **63** — a task file is not editable by the run it judges | **Landed** 2026-08-28 | `f16b982` |
| **65** — a task may name every feature it descends from | **Landed** 2026-09-07 | `a9964ea` |
| **66** — `/execute` takes its layer set from the plan (P44) | **Landed** 2026-09-07 | `6949f57` |

**Suite:** 112 checks at branch point → **125**. `failed 0`, `known 0`.

**Phase 7 is complete.** `61` · `62` · `64` · `63` · `65` · `66` — four items on 2026-08-28 and two on 2026-09-07,
**112 → 125 regression checks** with `known 0` throughout and every round watched failing first:
8/8, 11/11, 17/17 (after 13/15), 17/17 (after 14/16) and 12/12.

**Its shape is the argument for it.** Five of the six items came from *running* the toolchain the
afternoon the plan was declared complete and merged; the sixth came from *building* one of those
five. **None of the six was visible to the 112 checks that were green when the plan was closed**,
and the reason is uniform: four are contradictions *between* correct statements, and a check that
asserts a mechanism cannot see a second instruction about that mechanism. The fifth needed a task
spanning two features to expose it, and the sixth needed a consumer read while wiring a guard into
it.

| Item | From | What it fixed |
|---|---|---|
| **61** | the run | `plan-layers` forbade the derivation its own opening section requires |
| **62** | the run | the task schema rejected every Layer 0 task the toolchain has ever written |
| **64** | the run | the generator asserted `.git` is a directory; in a worktree it is a file |
| **63** | the run | `/execute` could rewrite the acceptance criteria it is judged against |
| **65** | the run | a task could not name every feature it descends from |
| **66** | building 63 | `/execute` recited a layer list the producer stopped writing |

**Three of the six are guards that did not exist rather than code that was wrong** — the task-file
hash, the layer resolution, the escalation path — and each replaces a sentence a model could
reason past with an exit code it cannot. That is item 4.13 applied five phases later to the half
of the toolchain the corpus could not describe.

**What is left is not plan items.** `SCHEMAS.json` still records the schema-6 content work,
`readers.md` still carries three `open` rows, and both were true before this phase started.

---

## The third live crossing — the first clean one, and five findings

**Commit:** `1aee6ad` · **Addresses:** P39–P43 · **Files:**
`docs/skills/plugin-2.0-plan.md`, `skills/breakdown-plan-layers/SKILL.md`,
`skills/breakdown/references/task-format-spec.md`, `tests/mutants/live-run.py` (new),
`tests/test_toolchain.py`

### What was run, and why it was worth running

`/breakdown` and `/execute`, end to end, on the **schema-5** fixture, headless under
`bypassPermissions`, with item 59's grader on the output. The previous crossing was run against
schema-2 and exited 1. The plan had since been declared complete and merged, and the honest answer
to *"is it finished"* was: **the plan is implemented and the toolchain is not demonstrated.** This
is the demonstration.

### The result

```
ok  1: 21 criterion copies checked against the PRD, verbatim
ok  2: 3 feature(s) named by 10 attributed task(s)
ok  3: removing `list-links`'s 1 task(s) was reported as `list-links` and nothing else
ok  4: reported as {'must-have/P0': 5, 'should-have/P0': 5}
ok  5: preflight refused the won't-have task and named it

5 assertion group(s) held, 0 failure(s)
```

Then `/execute`, verified **independently rather than from the run's own summary**:

| Checked by | Result |
|---|---|
| `ledger-status.sh`, derived from git rather than from a state file | `verified 14 / 14`, `missing: []` |
| `pytest`, run by hand afterwards | **61 passed** |
| `git status`, `git worktree list` | clean; no worktrees left behind |
| `check-project-md.py` and `check-artefacts.py` on the generated `PROJECT.md` | valid, 0 invalid |

**Neither of the second crossing's two defects recurred.** No task invented a `feature#id`
notation, and no task cited a criterion it did not carry — both checked mechanically over the
generated set rather than read.

### And five findings, none of which 112 checks could see

Two are shipped-instruction contradictions, one is a missing guard, one is a missing brief, and
one is a schema gap. **The reason the suite missed all five is uniform and worth stating:** four
are contradictions *between* correct statements, and a check that asserts a mechanism cannot see a
second instruction about that mechanism. The fifth needs a task spanning two features to expose it,
which a corpus read feature-by-feature never produces.

| | Finding | Item |
|---|---|---|
| **P39** | `plan-layers` forbade the derivation it performs | 61, **landed** |
| **P40** | `task-format-spec.md` required a layer its own constraints could not express | 62, **landed** |
| **P41** | `/execute` may rewrite the acceptance criteria it is judged against | 63 |
| **P42** | the generator does not know the execution model | 64 |
| **P43** | `<source-feature>` is single-valued, and an integration task spans features | 65 |

### P41 is the one that qualifies the 14/14

The run met a Layer 0 task whose `<verification>` block was **unsatisfiable**: one step asserted a
substring absent that another requirement mandated present. Its diagnosis was right, its fix was
reasonable, and it **edited the task file and continued.** Nothing forbids that, nothing records
it, and the git ledger records commits rather than task edits.

`execute-verify` is documented as *"independent from the implementing agent"*. It is — and that is
the wrong independence: the orchestrator above it can rewrite what it verifies against. So the
`14/14` is a weaker result than it reads as, by item 59's own standard: *a runtime test whose
crossing is made to pass by adjusting the test has measured nothing.*

**The run reported what it had done, in detail, unprompted.** That is the finding stated precisely:
the failure is not that the agent was dishonest, it is that **honesty was the only thing standing
between a rewritten acceptance criterion and a green result.** Item 63 replaces it with a hash.

### P43, and why three runs is the strongest evidence available

`<source-feature>` holds one slug. Three live runs met a task covering more than one feature and
produced three different workarounds:

| Run | What it did | Why it is wrong |
|---|---|---|
| 1 | invented `feature#id`, applied to the criteria and not to `<satisfies-criteria>` | the halves of a task stopped referring to each other |
| 2 | split the task, and said why | correct, and it changes the task set to suit the schema |
| 3 | narrowed the attribution to one feature, silently | **worst of the three, because nothing says so** |

Run 3's `L4-002` walks `save-link`, `tag-links` and `list-links` criterion 2, and declares
`tag-links` alone. **No check catches it**: item 30's coverage passes because those criteria are
covered by other tasks. What is lost is that the coverage report, the scope cross-check,
`tasks-summary.md` and the gate all believe the task belongs to one feature — so dropping that
feature from scope would silently take the only end-to-end assertion of the other two with it.

The plan never considered this case, and could not have: **a document read feature by feature does
not produce an integration task.**

### A defect in my own fix, caught by the check written for it

Item 61's first attempt removed the contradicting instruction and **quoted it in the replacement**,
as a historical note explaining what had been rescinded. The new check failed immediately —
correctly. A skill is instructions to a model, and a model reads a quoted rule with the same weight
as a stated one; *"this used to say every project needs all 4 layers"* is the forbidden sentence,
present in the file, with a preamble.

The history belongs in the plan and in this ledger, which is where P39 and item 61 now hold it. The
check keeps its strictness deliberately and says so in a comment, because the next person to add a
historical note will hit it too.

### Verification

`python tests/test_toolchain.py` — **112 → 114**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/live-run.py` — **6 of 7 caught**, then **8 of 8** with the
survivor's sibling added.

**The survivor was an `or` across two locations**, which is a failure this suite already has a name
for and which I wrote anyway. The rule *a dropped layer must be named* is stated twice — once in
the derivation paragraph, once in the `Do NOT` list — and the check accepted either:

```python
re.search(r"name (the ones|what) you dropped|never drop one silently|drop a layer", flat)
```

Deleting it from the derivation paragraph left the `Do NOT` bullet matching, and the mutant walked
through. It is now asserted at **both** sites, each scoped to its own region, and the round gained
a second mutant that breaks the other end — because a rule stated in two places needs two checks
or it has one and a decoy.

**Both new checks guard prose, which is the weakest thing to guard** — and is precisely why these
two defects survived 112 checks. So each rule is broken twice in the round: once by restoring the
old wording, once by removing the half that makes the check non-vacuous. A check that only forbids
a bad sentence passes on a file that has lost the good sentence too.

**The first attempt at this round was killed by a ten-minute timeout mid-mutant**, leaving
`task-format-spec.md` mutated in the working tree. It was restored with `git checkout-index` from
the index staged before the round — which is the reason `git add -A` before a round is a rule here
rather than a habit, and the reason `mutate.py` verifies restoration by hash rather than assuming
it. The round was re-run in the background with room to finish.

## 64 — the generator is told where its commands run, and told to stop guessing

**Commit:** `7709000` · **Addresses:** P42 · **Files:**
`skills/breakdown-generate-tasks/SKILL.md`,
`skills/breakdown/references/review-criteria.md`,
`tests/mutants/generator-context.py` (new), `tests/test_toolchain.py`

### What landed

Two halves, as the plan specified, in the two files that own them.

**The brief.** `breakdown-generate-tasks` now states where a `<verification>` step runs, as five
facts in a block: `cwd` is the worktree root, `.git` is a **file**, the branch is
`worktree-{task-id}` and never the base branch, the tree is a fresh checkout of the base branch,
and the other tasks of this layer are not visible. The generator was writing environment-shaped
assertions with none of this in front of it, which is the whole of P42 — `Path('.git').is_dir()`
is not a careless line, it is a correct claim about a checkout and a wrong one about a worktree.

**The preference**, which the plan called the durable half and is. *Assert the artefact, not the
environment*: a three-row table pairing a claim about the task's own output against the
environment claim it replaces, and the rule that generalises it — a step you cannot phrase as a
claim about a file this task creates, a command it makes runnable, or a behaviour one of its
criteria names, is a step you should not write.

**The review question.** `review-criteria.md` §6 gains both as **critical** criteria, not
warnings, because a step that cannot pass is exactly what P41's run edited a task file to get
past. *Common Issues* gains an `Environment-Shaped Verification Steps` block re-aiming five
patterns at what the task actually produced.

### The check measures the claim rather than quoting it

This is the part worth keeping. The first check parses the five facts out of the brief and then
**builds a worktree with the toolchain's own `create-worktree.sh` and asks git whether they are
still true**: `.git` is a file and not a directory, the branch is `worktree-L1-001` and not
`trunk`, a sibling's committed file is absent, an untracked `node_modules` in the primary tree did
not come along.

So the brief can fail in two directions and the message says which: *the brief no longer says
this*, or *the brief now states something false*. Phase 1's lesson was that a check pinned to
prose breaks when the prose improves. A brief full of environment facts has the opposite failure —
prose that stays put while the thing it describes moves — and only a measurement catches that one.

### The eleventh mutant found a duplication, and it is not item 64's to fix

That mutant renames the branch in `create-worktree.sh`, and the named check fired: the brief now
describes a toolchain that has moved. **A second check fired with it**, reported as an orphan by
the harness, and it is a true positive rather than harness noise — `merge-task.sh:53` recomputes
`branch="worktree-${task_id}"` for itself, so the prefix is stated independently in two scripts
and documented in a third place by the brief. Renaming it breaks the merge before the brief ever
gets a chance to be wrong.

Left as it is, deliberately, and recorded here instead: the fix is a shared source for the name,
which is a change to `/execute`'s scripts and has nothing to do with telling the generator where
its commands run. The mutants file says the orphan is expected, so the next round does not read it
as a rename.

### Two of my own errors

**The prefer/over table did not parse, and the check said so on its first run.** One `over` cell
is a shell pipeline, `git log --oneline \| wc -l`, and the escaped pipe split that row into four
cells; the check counted two rows of guidance where there were three, and failed. That is a check
doing its job on the first document it ever read. It now splits on unescaped pipes only.

**The first two `review-criteria.md` mutants were one-line cuts and would have survived.** Cutting
the first line of a multi-line checkbox bullet leaves the indented remainder in place — still
saying *worktree* and *.git* — and the check reads the bullet, not the line. Both now delete the
whole bullet. This is item 61's `or across locations` failure in different clothes: a mutant must
remove the thing the check reads, not the thing a reader's eye lands on.

### Verification

`python tests/test_toolchain.py` — **114 → 116**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/generator-context.py` — **11 of 11 caught**, baseline green,
every file restored by hash.

Eleven mutants for two checks, because both guard prose and one of them guards prose that can be
made false without being edited. Four break the facts (the section renamed, `.git` back to a
directory, the branch fact deleted, siblings declared visible); six break the preference at both
ends — where the step is written and where it is judged, since a rule stated in two places needs
two mutants or it has one check and a decoy; and the eleventh edits neither document.

## 63 — a task file is not editable by the run it judges

**Commit:** `f16b982` · **Addresses:** P41 · **Files:**
`skills/execute/scripts/task-integrity.py` (new), `skills/execute/SKILL.md`,
`skills/execute-layer/SKILL.md`, `skills/execute-batch/SKILL.md`,
`skills/execute-verify/SKILL.md`, `agents/task-implementer.md`,
`tests/mutants/task-integrity.py` (new), `tests/test_toolchain.py`

### The rule, and the three parts the plan asked for

**An implementer and an orchestrator may not modify a task file.** One sentence, and the
interesting half is what to do instead — the live run had that right in every respect except
where it wrote it down. It diagnosed an unsatisfiable `<verification>` step correctly and then
repaired it, when the same diagnosis reported would have fixed the task for every future run.

**A guard, not a paragraph.** `task-integrity.py record` snapshots every task file before
anything is dispatched; `verify` re-hashes and prints a unified diff of what changed. Exit 0
unchanged, 1 edited, **2 nothing recorded** — a third code because *"nothing to compare against"*
must never be reported as *"unchanged"*, which is the same false green one level up.
`/execute-layer` runs `verify` before the merge queue, so an edit stops the run **before** work
is merged against a rewritten criterion, and `/execute` runs it again before it reports.

**An escalation path**, which is what makes the guard bearable: `status: "blocked"` with a
`blocker` object quoting the step and what it contradicts, from the implementer or the verifier;
`execute-batch` neither retries it nor spends an attempt on it; `execute-layer` and `/execute`
carry it as `task_defect`, whose report names the task, the contradiction and `/breakdown` as the
place to fix it. A rule that leaves the operator stuck is a rule that gets removed.

**The record.** An edit appends to `.execute/{slug}/task-edits.jsonl` with both hashes and a path
to the diff, beside `ledger.jsonl` and under the same self-ignoring `.gitignore` — so a run's
edits share a fate with the commits it produced.

### Departure 1 — the record goes beside the ledger, not in it

*The plan said the edit "must be visible afterwards" and left the place open. This is the place, and the reason the obvious one is wrong.*

**Not in `ledger.jsonl`.** It is the obvious place — one record of what a run did — and it is
wrong: `ledger-status.sh` reads every line there as a task with a commit, and an entry without one
reads as *a task whose commit has vanished*, which sets `gap=1` and truncates `verified_tasks`. A
resume would then redo work that was done. A guard against a false green that manufactures a false
red is not an improvement.

The check asserts this by **running `ledger-status.sh` before and after an edit is recorded and
comparing the JSON**, and the round includes the mutant that writes to `ledger.jsonl` instead. It
is caught.

### Departure 2 — the edited task is held back, and nothing restores the file

*The plan said a changed task is "a stop with the diff" and did not say what happens to the batch around it.*

**The edited task is held back; its siblings still merge.** `should_stop` used to mean *merge
what verified anyway*, and that rule stays for the tasks whose files were untouched — they were
verified against their own snapshots and are exactly as sound as they were a minute ago. Only the
edited task is unsound, because only its criteria moved. Dropping the batch would lose real work
for someone else's defect.

**Nothing restores the file.** Not the agent, not the layer, not the orchestrator. The diff is the
only record of what happened, and rewriting the task back is one more edit by a run that has just
been told it may not make them.

### A defect found in `/execute` while wiring this, and left alone

`/execute` Step 6 iterates a **hardcoded** layer list —
`["0-setup", "1-foundation", "2-backend", "3-frontend", "4-integration"]` — and Critical Rule 1
still reads *"Never skip layers: Execute in order (0→1→2→3→4)"*. Items 31 and 61 made the layer
set derived, item 62 made the task schema admit any of them, and item 28 lets a project declare
its own graph instantiated per service. A project whose layers are named anything else gets a run
that iterates five names, finds no tasks under any of them, and reports a completed run of zero.

This is P39's shape exactly — a consumer pinned to the five shipped names while the producer
derives them — arriving in the file that consumes the derivation. **It is not item 63**, and
fixing it here would be the fix-at-the-site-of-discovery habit this plan keeps naming. Recorded
as **P44**, and now placed: plan §3.5 states the finding, section L holds item 66, and Phase 7's ordering carries it.

### The round found two of my own checks doing nothing, and it is the same defect twice

**13 of 15 on the first pass, and neither survivor was a mutant that should have lived.** Both
checks asserted a string against a whole file, and both strings existed somewhere else in it:

| The check said | What it actually matched |
|---|---|
| `"task_edited" in text` | the stop-kind table row and a cross-reference in Step 9 — so deleting the **report section** left it passing |
| `re.search("(do not\|never).{0,60}(retry\|increment)", whole_file)` | the usage-limit step's *"Do not increment the task's attempt count"*, four sections away |

**This is the third time this exact shape has been caught by a round in this build**, and the
second time I have written it after documenting it — item 61's survivor was an `or` across two
locations, and Phase 2's rule already says *scope to the region that owns the claim*. Writing the
rule down does not stop you writing the bug; the round does.

Both are now region-scoped: the stop kinds are read out of Step 8's table **and** each must have
its own `#### stop_reason_kind` section containing a `STOPPED:` report, and the retry ban is read
from `### Step 7b` alone. The round gained two mutants that break the other half of each — the
table row, and the step itself — because a check that only forbids a bad state passes on a file
that has lost the good state too.

### Verification

`python tests/test_toolchain.py` — **116 → 119**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/task-integrity.py` — **17 of 17 caught**, after 13 of 15 on the first pass.

Seventeen mutants for three checks, and the shape of the round follows the shape of what is
guarded. Six break the script and are caught by running it — the stop stops being a stop, the
diff becomes a summary, the record is never written, the record goes into the ledger, an appeared
task stops counting. Five break the wiring, including the one that is not a deletion: the layer
re-**records** instead of verifying, which is the plausible wrong version of this whole feature —
it blesses the edit and reports success. Six break the escalation path, at each of the four files
that carry it.

## 65 — a task may name every feature it descends from

**Commit:** `a9964ea` · **Addresses:** P43 · **Files:**
`skills/breakdown/references/task-format-spec.md`, `skills/breakdown-generate-tasks/SKILL.md`,
`skills/breakdown/references/review-criteria.md`, `skills/breakdown/SKILL.md`,
`skills/breakdown/scripts/build-manifest.py`, `check-coverage.py`, `check-scope.py`,
`check-gate.py`, `skills/execute/scripts/preflight.sh`, `write-state.py`,
`skills/execute/references/state-schema.md`, `tests/boundary-test.py`,
`tests/mutants/multi-feature.py` (new), `tests/test_toolchain.py`

### What landed

`<source-feature>` repeats, and each one carries its own tier, criteria and level:

```xml
<source-feature slug="save-link"  moscow="must-have"   satisfies-criteria="1"   requirement-level="P0"/>
<source-feature slug="tag-links"  moscow="should-have" satisfies-criteria="1,3" requirement-level="P1"/>
```

The old single-valued shape — the element with sibling `<moscow>`, `<satisfies-criteria>` and
`<requirement-level>` — is **read by every reader and written by none**, item 45's rule, for the
same reason: a corpus of task files does not migrate itself, and a reader that refuses the old
shape strands every task set generated before today. The siblings still fill in an attribute the
new form omits, which is what makes a half-migrated task readable rather than an error.

Ten consumers moved with it: the manifest (1.2 → **1.3**), `tasks-summary.md`, the coverage check,
the scope cross-check, the gate's slug scan, preflight's refusal, `write-state.py`,
`state-schema.md`, the generator's brief and `review-criteria.md`. And item 59's grader, which is
where the finding came from.

### Deviations from the plan — three decisions it left open

**1. `<from-feature>` — the criteria are grouped too, not just the citations.** The plan says
`<satisfies-criteria>` is qualified by the feature it belongs to. The criteria a task *carries*
have exactly the same ambiguity — `save-link` criterion 1 and `tag-links` criterion 1 are two
requirements with one name — and P43's first live run is the proof that qualifying one half is
worse than qualifying neither: it invented `feature#id` for the carried criteria, left
`<satisfies-criteria>` bare, and the two halves of a task stopped referring to each other.

So the criteria are wrapped, per feature, and only when the task names more than one. **A wrapper
rather than an attribute or a `feature#id` spelling, because item 17 requires the `<criterion>`
copied byte-for-byte** — every other option edits the copy.

**2. The compatibility key is omitted, never guessed.** `source_feature` — singular — is written
only when there is exactly one edge. A 1.2 reader then sees a multi-feature task as
**unattributed** rather than attributed to whichever edge came first. Writing the first slug would
have been the friendlier shim and it would have reintroduced run 3's silent narrowing *inside the
compatibility layer*, which is the one place nobody would look for it.

**3. Filters take the strongest edge; the wont-have refusal takes any.** `moscow` and
`requirement_level` become the strongest across the edges, because a task is built or not built as
a unit. Preflight's refusal (item 20) is the exception and is deliberate: a task carrying
`moscow="wont-have"` on any edge is refused even when another edge is `must-have`. The strongest
rule answers *how important is this task*; the refusal answers *should this task exist at all*,
and reading the effective tier there would let the exact case through that the refusal exists for.

### What the plan warned about, and the mutant that proves we did not do it

> **Do not fix this by relaxing the consumer.** The tempting cheap version is to let
> `check-coverage.py` accept a criterion cited by a task from another feature.

Every feature in the check's fixture declares criteria `1` and `2`, so a pooled reading reports
full criterion coverage for a task that touches one feature of three. That is a mutant in the
round — `got = set().union(*cited.values())` — and it is caught.

### The item 23 audit caught the new element before the suite did

`<from-feature>` landed in the spec with nothing reading it, and `check-readers.py` said so on the
next run: *NO READER — give it a reader, or record it in `readers.md` with a verdict*. Its reader
is `review-criteria.md`, which is the file that fails a task whose criteria are not grouped — a
real reader rather than a registration. **This is item 23 doing exactly the job it was built for**,
on an element that was four minutes old.

### Three of my own defects, one of them a repeat

**`attributed_tasks` counted edges.** One task naming three features reported *"3 of 1 task(s)
attributed"* — a summary line that disagrees with the set it summarises, which is run 6's state
file in miniature. Caught by the new check on its first run, and now counted over distinct ids.

**Two suite mutations were pinned to literals this item moved**, and both silently stopped
applying: preflight's `wont=$(grep -rl "<moscow>wont-have</moscow>" ...)` line, and the grader
self-test's `<source-feature>tag-links</source-feature>` and `<requirement-level>P0</...>`. A
mutation that matches nothing *passes the check it was supposed to break*, so each one turned into
a failing assertion that says nothing about the thing under test. All three now match by regex and
**assert the substitution count**, which is the general rule this repository can state after three
instances: **a mutation that does not apply must fail loudly, not quietly measure nothing.**

### Verification

`python tests/test_toolchain.py` — **119 → 123**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/multi-feature.py` — **17 of 17 caught**, after 14 of 16 on the first pass.

Seventeen mutants for four checks. Six break the producer — only the first edge read, the singular
key written for a multi-edge task, the effective tier taken from the first rather than the
strongest, the old shape refused, the version left behind, the summary showing one slug of three.
Three break the consumers, including the relaxed-consumer version the plan forbids. Two break the
raw-text guards back to the retired shape. Five break the instructions, at each of the three files
that have to agree about them.

## 66 — /execute takes its layer set from the plan, not from a list in its own prose

**Commit:** `6949f57` · **Addresses:** P44 · **Files:**
`skills/execute/scripts/resolve-layers.py` (new), `skills/execute/SKILL.md`,
`tests/mutants/layer-set.py` (new), `tests/test_toolchain.py`

### Departure — a script, not the instruction the plan specified

The plan asked for three things: iterate `layer_plan.json`, delete *"Never skip layers: Execute in
order (0→1→2→3→4)"*, and refuse a `--layer` the plan does not declare. All three landed — but the
first two are instructions to a model about a list, and **a list in prose is exactly what went
stale here**. So the resolution is `resolve-layers.py`, and Step 6 iterates its stdout.

It answers the question from two files, because they answer different halves of it:

| Source | Says |
|---|---|
| `layer_plan.json` | **order** — what `/breakdown` intended, in dependency order |
| `manifest.json` | **existence** — what was generated, derived from the files on disk |

So: planned order, filtered to layers that have tasks, then any layer that has tasks and no plan
entry — reported as a `/breakdown` defect and **executed anyway**, because the task files are the
deliverable and refusing to run work that exists helps nobody. A planned layer with no tasks is
reported too: usually item 31 dropping a tier correctly, occasionally generation failing quietly,
and only an operator can tell those apart.

Two refusals, both exit 1: **no layer has any task**, and **`--layer` names a layer this run does
not have**. The first is P44 stated as an exit code — a run with nothing to execute must not
report a completed run of zero.

### The refusal prints nothing on stdout, and that was a defect I wrote first

The first version printed the layer list and *then* refused. A caller reading stdout before the
exit code would have acted on the layer set of a run that was refused — the same shape as every
*"it printed something so it must have worked"* failure in this repository. The refusals now come
before any output, and the check asserts stdout is empty on both of them.

### The history is not quoted, and that is item 61 paying out

The obvious way to explain the change is to write *"this step used to iterate `["0-setup",
"1-foundation", …]`"*. Item 61's first attempt did exactly that with a rescinded instruction, and
the check written for it failed immediately and correctly: **a model reads a quoted rule with the
same weight as a stated one.** The list is therefore described and not reproduced, the history
lives in the plan and here, and the round contains the mutant that brings it back as a historical
note — caught by a check that forbids the list anywhere in the file, iterated or quoted.

### Verification

`python tests/test_toolchain.py` — **123 → 125**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/layer-set.py` — **12 of 12 caught**, no survivors and no orphans.

Twelve mutants. Seven break the resolution in each direction it could plausibly break — order
lost to the alphabet, the plan ignored entirely, unplanned layers dropped, the empty run reported
as success, `--layer` accepting anything, and each of the two `NOTE:` lines silenced. Five break
the wiring and the prose, including the quoted-history trap and the pair that removes the true
half of the Critical Rule as well as the false one.

## Phase 8 — The residue.

Group order: `8a` schema-6 · `8b` the three `open` reader rows, on branch `phase-8-the-residue`.

**Not plan items, and that is the point of the phase.** Both were written down rather than
carried: `SCHEMAS.json` recorded the schema-6 content work through four phases, and `readers.md`
has carried three `open` rows since item 23's audit. Neither is a new finding; both are things the
plan finished by *naming* and left for somebody to do. **The grouping is this ledger's, not the
plan's** — the same arrangement as Phase 5's five commit groups.

| Group | Status | Commit |
|---|---|---|
| **8a** — schema-6: item 40's second gate half, and the content the bar had been failing | **Landed** 2026-09-07 | `3c61ed9` |
| **8b** — `project-ref`, `prd-ref`, `feature-ref`: a producer with no consumer, three times | **Landed** 2026-09-07 | `147d38e` |

**Suite:** 125 checks at branch point → **128**. `failed 0`, `known 0`. **Both groups landed; the phase is complete.**

---

## 8a — the review the gate always required, and the four features it had been failing

**Commit:** `3c61ed9` · **Addresses:** P26 (item 40's deferred half), P10 (item 22's finding) ·
**Files:** `schema/core.md`, `schema/migration.md`, `schema/scripts/migrate.py`,
`skills/breakdown/scripts/check-definition.py`, `tests/fixture/prd/SCHEMAS.json`,
`tests/fixture/prd/schema-6/**` (new), `tests/mutants/review-gate.py` (new),
`tests/test_toolchain.py`

### The content work could not be content alone, and that is the finding

The item was recorded as *"schema-6 content work"* — five fixture files whose content predates the
bars now applied to them. It is not content work, for two mechanical reasons found on opening it:

- **A version with no shape delta is not a schema version.** The registry's rule 2 defines a
  frozen fixture as one that changes only when *the migration's expected output* changes.
- **Applying the fixes to `schema-5` in place breaks the step before it.** That comparison strips
  `acceptance-criteria`, `gaps` and `priority`; a `<data-model>` appearing in schema-5 would have
  to be added to *those* judgement elements — weakening an existing check to accommodate new
  content, which is P2's mistake with the arrow reversed.

So the content rides with the shape change `SCHEMAS.json` predicted all along: item 40's second
gate half, which had been deferred since Phase 5 with *"the second half has nowhere to be
recorded, and adding one is a schema version"*.

### `<review by= at= sha=>`, and why the hash is the whole element

The bar is *the mechanical tests pass **and** a review has been recorded*. Four phases had only
the first half, so a feature labelled `defined` and one labelled `defined` **after somebody read
it** were the same file.

```xml
<review by="lee" at="2026-09-07" sha="15538c7661d0"/>
```

**Without `sha` this element records nothing.** It would say a review happened once and let the
file be rewritten underneath it — a ledger recording adjectives, which is the defect
`record-task.sh` was written to avoid one artefact along. With it there are three states, and the
middle one exists only because the hash does:

| | |
|---|---|
| **reviewed** | `sha` matches the file with the `<review>` element removed |
| **stale** | it differs — reviewed, then edited |
| **not reviewed** | absent |

**The hash excludes the element it lives in**, or writing a review would change the file the
review describes and every review would be stale on arrival. That is the first mutant in the
round, because it is the version somebody writes first and it looks entirely reasonable.

**Any edit invalidates it, a reflow included.** Deliberate: the alternative is a canonicaliser
deciding which edits are cosmetic, and that judgement is what the reviewer was there to supply.
It was exercised without being planned — adding `<considerations>` to three features mid-build
invalidated their reviews, and they had to be re-recorded.

**Reported, never refused; `--strict` is the exit code.** §4.2's principle is that a wrong label
signals wrong content, so a gate that blocks the label invites relabelling rather than fixing.

### R13 is the first migration rule with no mechanical half at all

| Rule | What it does |
|---|---|
| **R11**, **R12** | a document `<status>` outside `in-progress\|complete` becomes `in-progress` — the **weaker** claim, because a machine resolving toward `complete` asserts an interview finished that nobody finished |
| **R13** | a `defined` feature must carry a `<review>`. There is nothing in the file to derive one from, so the transform is the identity and every such feature reports `PARTIAL` |

**The rejected alternative was a placeholder review** written by the migration so the shape would
be present. It is in the round as a mutant: the schema would be satisfied, the gate would pass,
and nobody would have read anything.

R11/R12 also needed adding to `applied_adds_values` — the per-rule exemption from the rename
invariant, which R10 already needed for the same reason: mapping one value onto another is not a
rename. The invariant caught it on the first run and refused to write the files, which is the
exemption list working as intended rather than an obstacle.

### Three checks used the fixture's defects as their positive control

Fixing the corpus broke them, and each said so by name — one of them in so many words: *"If the
fixture has been fixed, update this check deliberately."*

| Check | Had asserted | Now |
|---|---|---|
| the well-defined bar | the fixture FAILS t2/t4 | the fixture passes, and every test is broken here instead |
| artefact conformance | the fixture carries an invalid document status | the current version is clean; the check injects one |
| coverage | criterion ids listed by hand | derived from the fixture, so a new criterion cannot orphan it |

**A control that depends on a defect staying unfixed is a control that argues against fixing it.**
Three of them had accumulated, all pointing at the same five files, and the item that fixed those
files is the item that had to rewrite them.

### Two of my own, caught by guards that already existed

**A `<notes>` holding only a `<data-model>` is a schema-3 shape.** Item 27 split notes into
`<data-model>` and `<considerations>`, and R6 reads the second as the marker that the split
happened — so three features silently regressed a version until `check-artefacts.py` reported
them as `OLD`. They now carry the consideration that belongs with each data model.

**My new check hardcoded `schema-5` and `schema-6`**, and the suite's own *nothing hardcodes a
schema fixture version* check rejected it. Both ends are now derived from the registry, which is
what makes the check exercise the newest step rather than the step it was written against.

### What the fixture is now

**12 artefacts, `0 invalid, 0 written in an older spelling`** — the first time the current corpus
has been clean on both counts. schema-5 reported 2 invalid and 8 files in an older spelling, and
those numbers were the reason this item existed.

### Verification

`python tests/test_toolchain.py` — **125 → 127**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/review-gate.py` — **10 of 10 caught**, no survivors.

Five mutants break the hash rule, because the hash is the difference between a record and a claim:
it covers the review element (stale on arrival), it is never compared, staleness is reported and
then passed by `--strict`, absence stops being reported, the recorder signs the review itself.
Four break the migration, including the placeholder review and the status resolving toward
`complete`. The tenth breaks the fixture back to failing the bar it is the reference for.

**Two orphan checks fired**, both expected: the fixture mutant and the migrate mutants also trip
the golden comparison and the bar's own check, which read the same files.

---

## 8b — three references nothing followed, and the two defects found by following them

**Commit:** `147d38e` · **Addresses:** P24 (item 39's rule, on the path that never had it),
P2 (a producer with no consumer) · **Files:**
`skills/breakdown/scripts/check-references.py`, `skills/breakdown/scripts/check-gate.py`,
`skills/crd/references/crd-format.md`, `schema/readers.md`,
`tests/mutants/crd-refs.py` (new), `tests/test_toolchain.py`

### One reader for three elements, because it is one rule

`readers.md` carried three `open` rows from item 23's audit: `<project-ref>` — **`Required` in
every CRD and read by nothing** — with `<prd-ref>` and `<feature-ref>`. A producer with no
consumer three times over, one of them required, which is P2's shape on the CRD path.

They resolve in `check-references.py`, the script that already resolved the PRD path's citations.
**The same program rather than a second one, because it is the same rule**: a reference that names
something must resolve to it, or be reported by name. That is item 39, arriving where it had never
been applied.

| Element | What follows it now |
|---|---|
| `<project-ref>` | resolves to a file, and is **compared** against the project the run is for |
| `<prd-ref>` | resolves, when present |
| `<feature-ref id=>` | resolves against `PROJECT.md`'s `<feature id=>` |

**`<project-ref>` is compared, never used to resolve.** Letting a document choose which
`PROJECT.md` a run reads would hand a file authority over where the run points; comparing catches
the case that matters — a CRD describing a change to one project, executed against another.
Without `--project-path` the check says it could not make that comparison rather than reporting a
check it did not make.

### The gate had been skipping it by construction

`check-references.py` took a PRD *directory*, so `check-gate.py` short-circuited it for a CRD:
`(0, "") if os.path.isfile(args.document)`. **That is why three elements could sit unread through
two audits** — the one caller that would have followed them could not call the script at all. The
gate now runs it for a CRD and carries what it says.

### Two defects found by making the check run rather than read

Both were invisible to the first version of the check, which asserted that the word `dangling`
appeared in the gate's source. A mutant dropped the findings loop and left the word — the fifth
presence-assertion in this build to fail the same way — and forcing the check to *run* the gate
found two real things behind it:

- **The gate counted the dangling reference and printed it nowhere.** `gate: 2 finding(s)` with
  every visible section reading `OK`. It now has a fourth section, on the CRD path only.
- **`--json` was not JSON.** It printed the object and then the human summary line, so
  `--json | jq` failed on trailing data. **Nothing had ever parsed that output until this check
  did**, which is how a flag stays wrong for months. `--json` now emits the object and nothing
  else; the exit code carries the same decision the line described.

And the second fix was not enough either: asserting the *printed* line still passed while the
finding was dropped, because the print does not read `findings`. The check asserts both halves of
the contract — the human report names the reference, the machine report counts it.

### A fourth control that depended on the state it was measuring

`every element the schema defines has a reader` asserted that some `open` rows existed, using
their presence as evidence its parser worked. Closing the last three broke it. It now asserts the
`open` **verdict is still defined** and that the table parses: the vocabulary has to survive a
corpus with no instances of it, or the next producer with no consumer arrives to a verdict nothing
exercises.

**That is four such controls in one phase** — three in 8a against the fixture's defects, one here
against the exception list. They accumulate for a reason worth naming: a control written *while*
a defect is live is free, and the cost lands on whoever fixes the defect.

### Verification

`python tests/test_toolchain.py` — **127 → 128**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/crd-refs.py` — **9 of 9 caught**, after 8 of 9 twice.

Six mutants break the resolver in each direction it could quietly stop resolving; two break the
wiring, separately, because *the gate calls it* and *the gate does something with what it says*
are different claims and the second one survived twice; the ninth restores an `open` row, which
would put this file back into disagreement with the reader it now has.

**The round was killed by the ten-minute timeout mid-mutant**, leaving the tree mutated. Restored
with `git checkout-index` from the index staged before it — which is why `git add -A` before a
round is a rule here — and re-run in the background, where a round that takes longer than a
foreground call allows belongs.

---

## Phase 8 is complete

`8a` · `8b`, both landed. **125 checks at branch point → 128.**

**Neither group was a plan item, and both were things the plan finished by naming.**
`SCHEMAS.json` carried the schema-6 content work through four phases and `readers.md` carried
three `open` rows through two audits; each was recorded rather than done, and each turned out to
be larger than its record — the content work was a schema version, and the three unread elements
were unread because their one caller could not call the script.

**What the phase actually removed** is two places where the toolchain described itself
inaccurately: a `defined` label that nobody had to have read, and a `Required` element that
nothing resolved. Both had been true for months, both were written down, and neither was visible
in any run.

---

## Phase 9 — The guard at the right boundary.

One group, `67`, on branch `phase-9-the-guard-at-the-right-boundary`. **Specified by the fourth
live crossing**, which is the first run item 63's guard was ever active for — and the first to
find a defect in it.

| Item | Status | Commit |
|---|---|---|
| **67** — a snapshot that replaces another says what changed between them | **Landed** 2026-09-07 | `91b90ef` |

**Suite:** 128 checks at branch point → **129**. `failed 0`, `known 0`.

---

## The fourth crossing — the first against schema-6, and the first with the guard live

**Run:** 2026-09-07, `/breakdown` then `/execute`, headless under `bypassPermissions`, on the
schema-6 fixture. **Workspace:** `boundary-run-p02rsano`, deleted after this entry was written.

### What held

```
ok  1: 19 criterion copy/copies checked against the PRD, verbatim
ok  2: 3 feature(s) named by 7 attributed task(s)
ok  3: removing `list-links`'s 4 task(s) was reported as ['list-links'] and nothing else
ok  4: reported as {'must-have/P0': 5, 'should-have/P0': 2}
ok  5: preflight refused the won't-have task and named it
```

Then `/execute`, verified **independently rather than from the run's own summary**:

| Checked by | Result |
|---|---|
| `ledger-status.sh`, derived from git | `verified 10 / 10`, `missing: []` |
| `pytest`, run by hand afterwards | **44 passed** |
| `git status`, `git worktree list` | clean; no worktrees left behind |
| `check-project-md.py` | valid — 5 features, 3 registries, 1 open gap |
| `resolve-layers.py` | `0-setup · 1-foundation · 2-backend · 4-integration` |

**Four items were exercised doing what they were built for**, which is the first time any of them
has been seen working outside its own check:

| Item | What the run did |
|---|---|
| **61** | derived four layers and dropped `3-frontend`, the behaviour a contradicting instruction used to forbid |
| **64** | wrote 24 verification steps and **not one** asserts the environment — the single `git` command present checks the `.gitignore` the task itself wrote |
| **65** | `L4-002` names three features with per-edge criteria and groups its carried criteria under `<from-feature>` — the case three earlier runs each worked around differently |
| **66** | executed exactly the layers `layer_plan.json` declared |

### And one finding, in the guard itself

**The run stopped on `L4-001`, the task file was edited, and the run resumed.** Item 63's
`record` runs on every invocation, so the resume snapshotted the *edited* file as its baseline.
`verify` has said `UNCHANGED 10 task file(s)` ever since, and `task-edits.jsonl` was never
written.

The timeline is not inferred; it is in the artefacts:

| | |
|---|---|
| ledger | `L0-001` … `L2-003` merged **18:37 → 19:07** |
| snapshot | `recorded_at` **19:18:46** — after those merges, before the rest |
| ledger | `L4-001` merged **19:23**, `L4-002` **19:27** |
| snapshot copy of `L4-001` | byte-identical to the live file, i.e. post-edit |
| `task-edits.jsonl` | absent |

**That behaviour was deliberate, and the assumption inside it was the defect.** Item 63's own
note reads *"a `--resume` re-records too, so an operator who fixed a task between runs is not
fighting the previous run's snapshot"* — which is true of an operator and false of an agent that
stops, edits and resumes as one continuous act. **The guard protected a dispatch, and a run is
not a dispatch.**

**The second half is worse.** `record` deleted the previous snapshot before taking the new one,
so the file as originally dispatched was not merely unreported — it was unrecoverable. Item 63's
third requirement was that the edit be visible afterwards, and the resume path erased the only
artefact that could have shown it.

---

## 67 — the re-record says what it replaced

**Commit:** `91b90ef` · **Addresses:** P45 · **Files:**
`skills/execute/scripts/task-integrity.py`, `skills/execute/SKILL.md`,
`docs/skills/plugin-2.0-plan.md`, `tests/mutants/record-replaces.py` (new),
`tests/test_toolchain.py`

**The rule does not change: an operator may fix a task between runs.** Forbidding that would
leave an unsatisfiable task with nowhere to go, which is the failure item 63's escalation path
exists to prevent. What changes is that the fix stops being invisible.

`record` now compares before it replaces. Every task file differing from the existing snapshot is
appended to `task-edits.jsonl` as `edited-between-runs`, with both hashes and a diff, and printed
— then the new snapshot is taken and the run carries on. `/execute` is told to report those lines
at the top of the run, because a resume that begins by naming what changed is a resume whose
operator knows what they are resuming into.

**`kind` is the whole of the difference between the two edits**, and that is deliberate. Nothing
on disk distinguishes *the operator* from *the run*, and a guard that tried would be guessing at
intent. Both leave the same trace; one of them is legitimate; the record says which is which and
lets a reader decide.

### Departure — what this deliberately does not do

It does not catch a run that stops itself, edits, and resumes **within one invocation**. That is
indistinguishable on disk from an operator doing the same thing between two, and item 63's
`verify` already covers the case that matters: any edit made while a dispatch is in flight is a
stop. What 67 removes is the silence, not the possibility.

### A defect in my own fix, caught by the check written for it

The diff file was named with a timestamp at second resolution. Two edits to one task inside the
same second produced one filename, and the second overwrote the first — **P45's erasure, one
directory down**, in the fix for P45. The check asserted two diff files for two edits and failed
on the first run.

Diffs are now named by the hash of the content they record, which also makes re-recording the
same edit idempotent rather than duplicated.

### Verification

`python tests/test_toolchain.py` — **128 → 129**, `failed 0`, `known 0`.

`python tests/mutate.py tests/mutants/record-replaces.py` — **9 of 9 caught**, one expected
orphan (item 63's check reads the same script).

The round breaks the *moment* rather than the comparison, because the comparison was never wrong:
the re-record stops comparing, compares and records nothing, records without a diff, records both
kinds under one name, drops the count from stdout, turns a legitimate between-runs edit into a
stop, undoes item 63's mid-dispatch stop, and names the diff by the clock again.

---

## Phase 10 — What verifying the implementation found.

One group, `68` · `69` · `70` · `71`, on branch `phase-10-what-verification-found`. **Specified by
[`plugin-2.0-verification.md`](plugin-2.0-verification.md)** — a static reading of the repository
against the plan, 67 items one at a time, looking for the thing each item said it would build.

| Item | Status | Commit |
|---|---|---|
| **68 + 69 + 70 + 71** — the four defects verification found | **Landed** 2026-09-08 | `de812a2` |

**Suite:** 129 checks at branch point → **133**. `failed 0`, `known 0`.

**Its shape is the argument for it, and it is a different shape from Phase 7's.** Phase 7 came
from *running* the toolchain and found things a static suite could not see. This phase came from
*reading* it, and found four things the suite could not see for the opposite reason: **every one
of them is a gap between two correct statements, or a statement that stopped being true when a
later item landed.** No decision recorded in this ledger was wrong. What went wrong is that
nothing was watching the seam.

| Item | The seam it closes |
|---|---|
| **68** | schema-6 shipped `<review>` with a reader and no producer, and `/prd` said there was nowhere to record one |
| **69** | `checks.md` asserted that every caller is named and was only ever checked forward |
| **70** | two Phase 8 commands used a path that resolves against the target project |
| **71** | three artefacts describe a state the toolchain has left, one of them to an operator |

---

## 68 + 69 + 70 + 71 — four seams, and the registries found two of them

**Commit:** `de812a2` · **Addresses:** P46–P49 (findings V1–V4) · **Files:**
`schema/prd-format.md`, `schema/checks.md`, `schema/readers.md`, `schema/parity.md`,
`schema/migration.md`, `commands/prd.md`, `skills/crd/references/crd-format.md`,
`skills/breakdown/scripts/check-scope.py`, `tests/mutants/verification.py` (new),
`tests/test_toolchain.py`

### Why four items are one commit

They are four instances of one thing: **an artefact that stopped being true and had nothing
watching it.** Splitting them would produce four commits whose messages are the same sentence, and
the four checks share a property that is easier to argue once than four times — each asserts
against a *mechanism* rather than against the text it is fixing, because three of the four fixes
are prose and prose is what this repository has watched pass while doing nothing five times.

### Item 68 — the element that had a reader, a fixture and a migration rule, and no producer

`<review>` is item 40's second gate half and the whole content of schema-6. It shipped with
`check-definition.py` reading it, six fixture features carrying it, and migration rule R13 naming
it — and **zero** occurrences of `<review` or `record-review` anywhere in `commands/`, `skills/`
or `schema/prd-format.md`. Core §7 was the only section of the core that no format reference
pointed at.

**The omission was not the worst half.** `/prd` Phase 7 read *"where the PRD carries no place to
record that review, say so plainly to the author rather than treating the absence as a pass"* —
true before schema-6, false after it. A run following its own command file would meet a feature
that passes the mechanical tests, look for the place to record the review, and **report the
absence as unfixable.** That sentence is replaced rather than softened; it now says what to report
instead.

**The check asserts the flag is real, not merely cited.** `commands/prd.md` names
`--record-review`, and the check reads `check-definition.py`'s argparse to confirm it exists. A
cited producer that cannot run is the same defect one step along, and this is the cheapest possible
place to catch it.

### Item 69 — the table that could only be checked in the direction it was written

`checks.md` says every assertion names its owner **and its callers**, and the suite walked that
forward: the owner exists, each claimed caller cites it. Backward, five gaps — two scripts that own
assertions and had no row at all (`task-integrity.py`, `resolve-layers.py`, both Phase 7, both with
`REFUSED` exit codes), and three caller lists that had gone stale, two of them because group 8b
wired `check-references.py` into a CRD.

**`check-references.py` reached a CRD for a whole phase with this table saying otherwise**, which
is the argument for the item in one sentence.

**"Runs it" is the whole of the design, and getting it wrong would have made the check useless.**
Half the repository names these scripts in a docstring or a cross-reference; a substring match
reports thirty files and is therefore ignored — the fate of every alarm nobody can silence. A
caller is a line that *runs* it: an interpreter and a path, a `run("<script>")` helper, or an
interpolated plugin root. That rule finds exactly the five real gaps and no others, and it was
prototyped against the repository before it was written into the suite, because a rule tuned after
the fact against its own output is not a rule.

**One correction it forced.** The rule initially missed `build-what-next.py`, which
`commands/prd.md` invokes inside backticks with no `python` prefix. That is a real invocation and
the rule was too narrow, not the document — widened to match an interpolated plugin path on its own.

### Item 70 — two commands that cannot resolve

Open question 1 measured this and item 9 states it. Every invocation site obeyed it until Phase 8
added two that do not: one in `migration.md`, **87 lines from four of its own that are correct**,
and one in `crd-format.md` which is the only documented invocation of the producer item 68 exists
to supply — so an operator who found it could not run it.

### Item 71 — three artefacts describing a state the toolchain has left

Three instances, and the check generalises past all three rather than pinning each.

- **The landed set is derived from the ledger, not listed in the check.** Any script claiming a
  numbered item is pending, where this file records it landed, fails. `check-scope.py` was telling
  an operator that item 16 *"has not landed"* — it landed two commits later — and attributing an
  unattributed task to a missing feature rather than to a Layer 0 task or a generator defect.
- **`readers.md`'s count is asserted against `check-readers.py`'s own output.** It said six; the
  script prints seven. A figure in prose is what went stale, so the fix cannot be another figure
  in prose.
- **Every schema stamp equals `SCHEMAS.json`'s current**, not only the core's.

### The stamp was already saying it, and nothing read it

`checks.md`, `parity.md` and `readers.md` carried `schema-5` against a core carrying `schema-6`,
and only the core's stamp was ever asserted. **Either reading of that stamp indicts it.** If it
means what the core's means, all three were wrong. If it means *last reconciled at*, then it was
**announcing that these three files were a version behind** — and item 69's five missing rows and
`readers.md`'s wrong count are two independent confirmations that they were.

Settled as the first reading: **one meaning for one syntax.** The *reconciled at* claim is real and
is better served by item 69's reverse check, which measures reconciliation rather than asserting
it. A stamp nobody reads is P28's own finding, one level in.

### What the registries earned here

Two of the four findings were found *by* the machinery this plan built, and a third was found *in*
it. `check-readers.py` cannot see item 68 — it asserts every element has a reader and the reverse
is a report by design — but `readers.md`'s own wrong count and `checks.md`'s own missing rows are
both self-reports from files that exist to be checkable. **A registry that can be caught out of
date is worth more than a paragraph that cannot**, and this phase is the first evidence for that
claim that did not come from the person who wrote it.

### Verification

`python tests/test_toolchain.py` — **129 → 133**, `failed 0`, `known 0`.

**Each of the four checks was watched failing before its fix**, and item 68's three assertions
were watched failing *separately* — the template, then the producer, then the denial — by fixing
one at a time. The third was proved live by mutation rather than by ordering: the stale sentence
was reinstated, the check failed naming it, and the file was restored.

`python tests/mutate.py tests/mutants/verification.py` — ****14 of 14 caught**, baseline green, every file restored by hash**.

Four mutants break item 68 in each direction it could quietly stop working, including the one that
matters most — `/prd` citing a flag the script does not register. Four break item 69's table, two
by removing a row that never existed until this item and two by removing a caller. Two revert the
paths. Three break item 71's three halves. The fourteenth breaks **the check's own control**: item
71 derives its landed set from the ledger, and a parse that silently returned nothing would let the
check pass over its entire subject in silence. That is the failure group 8b named, and this is
where it gets tested rather than asserted.

**Three orphans, and they were checked rather than waved through.** The harness reported three
checks that failed while matching no mutant's expectation — the bar's mechanical tests, the
schema-6 migration and the `defined` gate. All three run `check-definition.py --record-review`,
and mutant 3 renames that flag, so the suspicion was that they are collateral from one mutant
rather than a fourth thing broken. **That is the benign one of MISSED's two meanings and it is
not the one to assume**, so it was reproduced: mutant 3 applied alone, the three checks run, all
three fail, the file restored and confirmed byte-identical. Collateral, and real checks firing
for a real breakage.

---

## Phase 11 — The documents catch up.

One item, `72`, on branch `phase-11-the-documents-catch-up`. **B7 of
[`plugin-2.0-verification.md`](plugin-2.0-verification.md)**, which named it and deferred it: 643
lines of `ARCHITECTURE.md` describing a toolchain six schema versions ago is not a footnote to
another phase.

| Item | Status | Commit |
|---|---|---|
| **72** — the documents that describe the repository are checked against it | **Landed** 2026-09-08 | `d603c74` |

**Suite:** 133 checks at branch point → **137**. `failed 0`, `known 0`.

**The content was the easy half and is not why the phase exists.** Every check in the suite reads
`skills/`, `commands/`, `agents/`, `schema/` or `tests/`. **Nothing read the four documents at the
repository root** — so the artefacts with no automated reader at all were the ones a human reads
first, and they were free to drift for nine phases. Four checks now read them.

---

## 72 — the only artefacts with no reader were the ones a human reads first

**Commit:** `d603c74` · **Addresses:** P50 (findings V12, V13) · **Files:**
`ARCHITECTURE.md`, `README.md`, `CLAUDE.md`, `docs/skills/target-state-data-flow.md`,
`tests/mutants/documents.py` (new), `tests/test_toolchain.py`

### Two of the four were worse than staleness

Most of what was fixed is ordinary drift — counts, a file tree, a directory that did not exist
when the tree was written. Two were not.

**`ARCHITECTURE.md` taught `allowed-tools:` in its fork example.** That is the *command* key which
silently stops `context: fork` taking effect — the single defect item 4.11 existed to remove, and
the one the suite forbids in every real skill. It sat in the section that *explains what a fork
is*, on `execute-task`, a skill removed at item 4.15. A reader copying it writes a skill that does
not fork and cannot be told why, and F13's guard scans `skills/` rather than the document that
teaches the pattern.

**`README.md` gave the one-flag load command.** `--plugin-dir` loads the plugin and does not make
its bundled scripts readable; without `--add-dir`, `/breakdown` stops in Phase 1. That was measured
on 2026-08-26 and written into `CLAUDE.md` — and `README.md`, which is what a new reader opens
first, kept the form that does not work.

### The model table was wrong in every row that mattered

It assigned `sonnet` to almost everything. The files declare a mix: `claude-opus-5` for
`breakdown` and `breakdown-generate-tasks`, `claude-haiku-4-5` for `analyze-prd`, `plan-layers`,
`review-tasks`, `execute-verify` and the CRD's two incremental skills, `claude-sonnet-5` for the
rest. Commands declare no model at all, which the table gave as `sonnet` for three rows.

**So the check compares the table to the frontmatter rather than asserting its shape.** A table of
assignments nobody compares to the files is a table of intentions, and this one had been one since
before the models in it were renamed.

### Both directions again, and the omission is the worse one

The layout check walks the trees in `ARCHITECTURE.md` and `CLAUDE.md` against the disk **in both
directions**, for the reason item 69 gave one level down. A document naming something that does
not exist sends a reader to a missing file. **A document silently omitting something real is
worse: there is nothing to look up and no way to notice.** `execute-task` was the first kind for
nine phases; `schema/` — item 44's whole artefact, and the single definition of every element both
paths share — was the second, appearing **zero** times in 643 lines.

### `target-state-data-flow.md` is corrected, not rewritten

It opened *"Status: Target state. None of this is built."* — true when written on 2026-08-25,
false since Phase 6 closed the plan. The temptation is to rewrite it in the present tense; that
would delete the only record of the starting state. Its value now is the **before and after**: the
left column of its §0 table is what the toolchain was, and everything below it is what the plan
changed. `ARCHITECTURE.md` describes what runs. So the status says *Reached*, says when it was
corrected and why, and the table's first column is relabelled.

The check asserts both halves: the false claim is gone **and** the header says something either
way. Removing a wrong status leaves a reader with no status, which is the same problem quieter.

### Two of my own, and both are rules this ledger already carries

**A `git checkout` discarded the work.** Proving the model check fires meant breaking the table,
and restoring it with `git checkout ARCHITECTURE.md` reverted to `HEAD` — deleting every Phase 11
edit in the file, which were all uncommitted. `mutate.py`'s own docstring warns about exactly this
("never with `git checkout`... copy aside, copy back"), and it was written after the same mistake
cost an afternoon in item 54. Recovered from the copy-aside backup, which is the reason the rule
says to make one.

**A check asserted a string where it wanted a shape.** *The tree mentions `schema/`* was satisfied
by two sites: the top-level entry and an incidental `schema/checks.md` inside a comment about a
different directory. **Two sites, so no single mutant could break it** — the site-counting rule's
sixth confirmation. Tightened to a line that *starts* with `schema/`, which is the claim the check
was actually making, and then watched failing.

**And a third, smaller:** the checks used `skill_files()` and `agent_files()` as if they returned
paths. They return `(name, path)` pairs, and the check raised `TypeError` rather than failing —
which the harness reports as a failure, correctly, but it is a broken check rather than a caught
defect. The suite distinguishes those two; I did not, for one run.

### Verification

`python tests/test_toolchain.py` — **133 → 137**, `failed 0`, `known 0`.

Each of the four checks was watched failing before its fix, and the two that were later
*tightened* were watched failing again afterwards.

`python tests/mutate.py tests/mutants/documents.py` — **12 of 15 caught on the first pass**, and
the three survivors are the most useful thing this phase produced. **15 of 15**, baseline green, no orphans, every file restored by hash after the
fixes below.

**Every mutant restores a real historical state rather than inventing a plausible one**:
`execute-task` in the model table and the file tree, `allowed-tools` in the frontmatter example,
the one-flag load command, the stale counts, and *"None of this is built"*. These are checks over
prose, which is the class this repository has watched pass while doing nothing more often than any
other, so a mutant that merely looked wrong would prove less than one that was wrong here.

### Three survivors, and two were real holes in checks I had already watched failing

This is the round's actual finding, and it is a correction to something this ledger has repeatedly
claimed: **watching a check fail proves it fires for the case you had in mind, and nothing else.**
All four checks had been watched failing. Two of them still could not see a whole class of the
thing they existed to guard.

**1. The load-command check read only fenced blocks.** `CLAUDE.md` gives the command in inline
backticks inside a block quote — so the one document that had the rule *right*, and had had it
right since it was measured, was the document the check could not see. It now reads every line
carrying `--plugin-dir`, fenced or not, and asserts it found at least two: a check that finds
fewer has stopped reading one of them.

**2. The status check was satisfied by six sites.** It asked whether any of
`built|landed|implemented|reached` appeared in the first twenty lines. Six did. Deleting the
verdict itself changed nothing. Scoping it to the `**Status:**` line was not enough either — that
line still contains *"every box in it was built across Phases 1-9"* — so the assertion is now that
the verdict **leads** the field, which is what a status field means. **That is the site-counting
rule three times in one phase**, once in the `schema/` assertion before the round and twice here.

**Fixing it exposed a second defect in the fix.** Making the negative assertion case-insensitive
made it fire on the document's own *quotation* of the claim it had corrected. A check that cannot
tell an assertion from a quotation of one **forbids documenting the history it enforces** — which
this suite did once before, in Phase 2, on the words *"full PRD content"*. Quoted spans are now
stripped before the negative assertion is made.

### The third survivor is not a hole, and it is recorded rather than deleted

The mutant that unscoped the layout check — `return blocks[0]` → `return text` — **survives, and
should.** Read against the whole of `ARCHITECTURE.md` rather than its fenced tree, every assertion
still holds, because nothing outside the tree happens to look like a directory entry. The scoping
is **defensive rather than load-bearing on today's content**, and a mutant that cannot fail proves
nothing about it.

Deleting it quietly would have bought a 15/15 that meant less than the 12/15 did. It is replaced
by a control that *can* fire — breaking the heading lookup, so the check has no subject at all —
and the reason sits in the mutants file beside it. **A round that reports a number it did not earn
is the failure this harness exists to prevent**, one level up from the checks it tests.

---

## Phase 12 — The graph is load-bearing.

One item, `73`, on branch `phase-12-the-graph-is-load-bearing`. **V5 of
[`plugin-2.0-verification.md`](plugin-2.0-verification.md)**: open question 7's experiment, which
the plan specified with a decision rule written in advance and then did not run for six phases.

| Item | Status | Commit |
|---|---|---|
| **OQ7's experiment** — designed and committed before it ran | **Run** 2026-09-08 | `3035f42`, `00196b4` |
| **73** — no task may depend on an interface a later layer exports | **Landed** 2026-09-08 | `93d30b5` |

**Suite:** 137 checks at branch point → **138**. `failed 0`, `known 0`. Mutation **6/6**.

**The answer is LOAD-BEARING**, and the three arms are in the plan at open question 7. What
belongs here is what the experiment cost and what it got wrong.

### The design was committed before the measurement, and that was the point

`3035f42` holds the harness, the poor graph, the metric and the decision rule, and it precedes
either arm. The plan writes OQ7's decision table before the run for R15's reason — an experiment
with no decision attached is a measurement nobody has to act on — and committing the design first
is the other half: **"the criteria were chosen in advance" becomes checkable rather than
asserted.**

The metric was made **categorical on purpose**. One run per arm cannot separate a graph effect
from sampling noise if the metric is a matter of degree, so the primary one is a forward
reference — unbuildable rather than worse, and one is material. Everything else was demoted to a
report.

### Three defects in the experiment, and the first is one this ledger already recorded

**The fixture explained the experiment to its subject.** The first poor arm's `architecture.md`
prose said *"the dependency direction is inverted"*, and `plan-layers` read it and wrote back
*"the inverted direction is reported rather than corrected"*. That is item 21's finding exactly —
its probe PRD described the tier experiment to the model under test — **repeated one phase after
being written down in this file.** The arm was re-run with prose saying only *"The layer graph for
this project."*

The re-run is the arm that counts, and it behaved completely differently: it produced **no tasks
at all**, because `generate-tasks` diagnosed the graph and refused. So the two poor arms
contradict each other, and that contradiction is the phase's real finding.

**An arm was lost to a workspace inside the checkout.** `resolve-output.sh` refused it at Phase 1,
correctly — F4 is a run whose entire output landed in the toolchain tree. The run exited **0**,
produced nothing, and the grader reported `no task XML`, which is indistinguishable from a
toolchain finding until the transcript is read. *A negative result whose instrument has not been
checked is not a result.* The harness now refuses such a path itself, with the reason.

**A secondary metric was measuring nothing.** `unresolved` counted dependencies on `python`,
`pip`, `sqlite3` and `fastapi.testclient.TestClient` — external libraries declared as interfaces —
as unmet contracts, and reported nine of them against a task set that was sound. It was discounted
from the verdict, and the same mistake is now a mutant.

### The finding that changed the mitigation

OQ7 asked `/breakdown` to *report when a supplied graph decomposes materially differently from
the shipped default*, which needs a baseline, a second decomposition and a threshold. **The
measurement showed the defect is visible inside a single task set**, so item 73 checks that
instead — no baseline, no threshold, and it catches the case on the run that produces it.

And the reason it is an exit code rather than better instructions: **the two poor arms behaved
differently on the same graph.** One obeyed and emitted 16 unsatisfiable edges with every check
green; one refused. The protection was a model judgement and it fired in one run of two. That is
item 4.13 arriving at a question this plan left open since Phase 3.

### P52 is recorded with no item — and both halves of that sentence were wrong

`breakdown-plan-layers` resequenced the declared graph — declared `0-setup, 1-integration,
2-frontend, 3-backend, 4-foundation`, emitted `0-setup, 4-foundation, 3-backend`.

**Corrected the same day, and the correction is the more useful entry.** This was written here, in
the plan and in a commit message as a ***silent*** override, and it was not silent:
`layer_plan.json` carries an `ordering_conflicts` entry at `severity: critical` naming both layers,
the declared order and the required one, in the very file that also carries the resequencing.

The word came from the neutral arm's own transcript — *"plan-layers did silently override it"*. I
verified the **override** against `architecture.json` and `layer_plan.json`, wrote *"rather than
taken from the run's own report"* in this section, and then carried the run's adjective through
three documents unchecked. **Half the claim was measured and half was quoted, under a sentence
asserting the whole of it was measured.** That is the sharper form of *a run describing its own
behaviour is a claim*: the danger is not believing a report wholesale, it is verifying the part
that is easy to verify and inheriting the rest.

**It was also wrong that this needed a design decision.** The reason given for leaving it
ownerless was that choosing between *obey the graph* and *refuse it* is a judgement. The skill had
already chosen, in its Dependency Ordering section: *"a contradiction, not an ordering. **Report it
and place the tasks by layer**."* Two obligations, and it discharged the first and not the second.
The question that dissolved this was not a new measurement — it was *what is this skill for*,
asked of the file rather than of the run. Item 74.

### Verification

`python tests/test_toolchain.py` — **137 → 138**, `failed 0`, `known 0`.

The check's three halves were each watched failing before the fix, by breaking the rank
comparison, the external-library exclusion and the order source in turn.

`python tests/mutate.py tests/mutants/layering.py` — **6 of 6 caught**, baseline green, no orphans,
anchors pre-verified.

Both directions are broken, because a checker that refuses everything passes any test fed only the
bad arm and one that refuses nothing passes any test fed only the good one. The sixth mutant breaks
the **fixture** rather than the script: a positive control that drifts to zero is a check with
nothing left to detect, and it would pass in silence.

---

## Phase 13 — The declared order is obeyed.

One item, `74`, on branch `phase-13-the-declared-order-is-obeyed`. **P52**, which Phase 12 recorded
as ownerless and got wrong in two ways.

| Item | Status | Commit |
|---|---|---|
| **74** — a declared layer order is obeyed, not improved on | **Landed** 2026-09-08 | `447e9ea` |

**Suite:** 138 checks at branch point → **139**. `failed 0`, `known 0`. Mutation **6 of 6**, after 5/6 whose survivor was a badly built mutant.

**The phase exists because of a question, not a measurement.** Phase 12 spent two live runs and a
mutation round on the layer graph and left P52 open, described as a silent override needing a
design decision. Asked *"what is `breakdown-plan-layers` for?"*, the skill answered both points in
its own text, and neither answer was the one this ledger had written down.

### What the skill is for, and what it therefore may not do

Three jobs: decide **which** layers exist (item 31 — a tier with no work is not a tier), assign
work to them, and own the task ordering derived from `feature_edges`. The graph itself is not its
to choose — a declared one is used *"exactly as declared"*, already validated by the caller, with
*"nothing"* from the shipped tiers grafted on.

And its Dependency Ordering section rules on precisely the case that arose:

> A `data` or `runtime` edge that would order a later layer before an earlier one is a
> contradiction, not an ordering. **Report it and place the tasks by layer**; a feature edge cannot
> override the layer graph, because the layer graph is the project's declared rule and the edge is
> one author's note.

**Two obligations.** The run discharged the first and not the second.

### Correction 1 — it was not silent, and that word was never checked

Phase 12 recorded P52 as a ***silent*** override, in the plan, in this ledger and in commit
`93d30b5`. `layer_plan.json` carries an `ordering_conflicts` entry at `severity: critical`, naming
both layers, the declared order and the required one — in the same file that carries the
resequencing.

The word came from the neutral arm's own transcript. **The override was verified against
`architecture.json` and `layer_plan.json`; the adjective was quoted** — under a sentence in this
ledger asserting the finding was measured *"rather than taken from the run's own report"*.

> That is the sharper form of the rule this repository already had. The danger in an agent's
> self-report is not believing it wholesale — it is **verifying the half that is easy to verify
> and inheriting the rest under the same sentence.**

### Correction 2 — there was no design decision to make

P52 was left ownerless because choosing between *obey the graph* and *refuse it* looked like a
judgement. The skill had chosen: report the conflict, place the tasks by layer, leave
`architecture.md` for a person to fix. An item with a specified fix had been filed as an open
question.

### The fix is an instruction with an exit code behind it

`breakdown-plan-layers/SKILL.md` gains the missing half directly under the rule it broke —
*reporting a contradiction does not license resolving it* — and `check-layer-order.py` refuses a
plan that comes back resequenced, so the sentence is not standing on its own. The emitted list
must be a **subsequence** of the declared one: dropping `2-frontend` from `0,1,2,3,4` is item 31
working; emitting `0,4,3` is not, whatever its merits.

### Why this is a second script and not a widening of item 73

The two are orthogonal, and the fixtures show it rather than the argument doing so.

| Fixture | declared order | `check-layer-order.py` | `check-layering.py` |
|---|---|---|---|
| `inverted/` | **obeyed** | pass | **refuses** — 16 unbuildable dependencies |
| `inverted-halted/` | **violated** | **refuses** | exit 2 — no task files to read |

**P52 happens in `layer_plan.json`, before a single task exists**, which is why a check reading
task dependencies cannot be the one that catches it. Both controls come from the *same* declared
graph and differ only in the behaviour under test.

### Verification

`python tests/test_toolchain.py` — **138 → 139**, `failed 0`, `known 0`.

Each of the check's four assertions was watched failing. **The fourth did not fail on the first
attempt**, and that is the entry worth keeping: it asserted the word *"declared"* appeared in the
refusal, which the refusal's own opening sentence — *"the emitted layer order is not the declared
one"* — already satisfied. Two sites, so deleting the line that prints the declared sequence
changed nothing. It now asserts `1-integration` and `2-frontend`, layers that were **dropped** and
can therefore only have come from that line.

**That is the site-counting rule for the fourth time in three phases**, three of them in Phase 11
and this one here. It is the most reliably recurring mistake in this work and it always presents
as a passing check.

`python tests/mutate.py tests/mutants/layer-order.py` — **6 of 6**, after 5/6 whose survivor was a badly built mutant.

Both directions, plus the equality-instead-of-subsequence mutant that would turn item 31's dropped
layers into violations, plus one that repairs the **fixture** rather than the script: a positive
control that stops being positive is a check with nothing left to detect.

**The first pass was 5/6, and the survivor was that last mutant being wrong rather than the check
having a hole.** It renamed the control's layer to `1-foundation` — a name no declared graph
contains — so the fixture stayed illegal by a *different* route, the check went on refusing it
correctly, and the mutant could never be caught. `1-integration` *is* declared, which makes the
emitted list a legal subsequence and the control genuinely stop being positive.

**That is a third distinct meaning for `MISSED`**, after a stale anchor and collateral from another
mutant: **a mutant that does not remove the thing it claims to remove.** All three read identically
in the report, and all three are the same shape as the site-counting rule — one property changed
while a second quietly went on satisfying the assertion. The diagnosis is recorded in the mutants
file beside the corrected substitution, because the next person to touch that fixture meets the
same trap.

---

## V6 — the authoring after-measurement, and it went the other way

Not a phase and not an item: **a measurement item 21 has owed since Phase 1**, on branch
`v6-the-authoring-after-measurement`, commit `fd07de5`. Suite **139 → 140**, `failed 0`, `known 0`.

The full trajectory is in the plan at item 21. Three things belong here.

**The before was recomputed, not quoted.** Phase 1 recorded 394 words / 8 criteria / 64 elements,
and the frozen `schema-1` fixture was re-measured with today's script rather than that number
being carried forward — both ends of a comparison have to come off one ruler. It returns
394/8/64 exactly, so the recorded figure holds and the instrument is stable across twelve phases.

**The result contradicts the plan's own fear.** Item 33 is graded a likely failure point and
priced as the migration's hardest step; at `schema-3` it takes **8 words and 24 elements out**.
The criteria count never moves — 8 throughout — so that is a per-criterion saving. What roughly
doubled the prose by `schema-6` is content the bar asks an author to know: a user story, gaps, a
data model, a recorded review. **Elements went down, 64 → 59. The tagging got cheaper and the
thinking got dearer**, which is the trade item 40 exists to make.

**The figures are asserted against the probe, not written down.** `readers.md` claimed six against
a script printing seven, and this is the same class of claim — a measurement recorded in prose.
Five of the six fixtures are frozen and `schema-6` is not, so the check guards exactly the drift
that can happen.

### An instrument note, and it is the session's fourth of this kind

The check was watched failing in both directions, and **the first attempt at the second direction
was a no-op**: an HTML comment appended to a feature file, which the word counter strips along
with every other tag. The metric never moved, the check passed, and it read as the check having a
hole. Redone with real prose.

That is now four times in this session that a mutation failed to move the thing it claimed to
move — a stale anchor, another mutant's collateral, a layer renamed to something no graph
declares, and now a comment inside a tag-stripping counter. **All four look identical to a check
with no teeth, and all four are the site-counting rule in other clothes.**

### What is still owed

**The timing half, and no script can take it.** *Is this tolerable to write?* is a stopwatch
against a person authoring the same four features under both templates. One caveat for whoever
takes it: `schema-6`'s +237 words includes the fixture's own content debt being paid — four
features that failed the bar and were fixed — so part of that is not a per-feature cost.

---

## Phase 14 — What the fifth crossing found.

Two items, `77` and `78`, on branch `item-78-a-run-writes-nothing-into-the-toolchain` (77 landed
on its own branch first). **Specified by the fifth live crossing** — the first CRD run since the
fidelity plan began.

| Item | Status | Commit |
|---|---|---|
| **77** — the gate's assertions reach a CRD | **Landed** 2026-09-09 | `d141a66` |
| **78** — a run writes nothing into the toolchain | **Landed** 2026-09-09 | `eadd0d8` |

**Suite:** 142 checks at branch point → **144**. `failed 0`, `known 0`.

### The crossing, and why it was worth running at all

§5.3 ran end to end on **2026-08-14** and passed. Everything numbered 44 upward landed *after* it,
so this was a regression question — what did six schema versions do to a sequence that worked —
and the answer is that **the sequence still works and three of its guards had stopped reaching
it.**

All four steps passed, verified against git and pytest rather than the runs' own summaries:
`PROJECT.md` valid with `stale=no`; a CRD with 7 EARS criteria, 2 gaps and a correct significance
flag; 4 tasks with layers derived; **4/4 verified, 4 merge commits, 27 tests from a baseline of 8,
0 worktrees left, and the delete trap held.**

**Items 75 and 76 both worked on their first live run, hours after landing.** Every task carried
`<data-model>` sourced from `<affected-contracts>` under the *touches* rule, and `/crd` wrote
`because="cross-cutting"` from unstructured prose — which was the open question when 76 shipped.

### Three findings, and the third came from `git status`

**P55 and P56** are in the plan at §R. Both are `os.path.isdir(...)` treating *PRD directory* as
the general case and letting a CRD fall through — item 29's execution stop unreachable, and a
CRD's significance never reaching the gate.

**P57 arrived differently and is the one worth dwelling on.** It was not found by a check, a run
report or a review. It was two untracked files in `git status` after the item-77 commit, noticed
because the tree should have been clean and was not. `skills/execute/preflight_err.txt` — a stderr
capture the model invented, written to a relative path that resolved inside the plugin.

> **Nothing in the toolchain could have caught it.** `resolve-output.sh` and `preflight.sh` guard
> the paths somebody *declared*. There was no rule about paths a model *invents*, and every live
> harness verified the target while none looked at the checkout. F4 is the same finding, resolved
> at item 4.6 for declared paths and open ever since for undeclared ones.

### The shape all three share

`check-references.py` at group 8b, `check-gate.py` twice, `check_crd()` at item 76 — and now a
skill with no rule about where it may write. **The CRD path is not under-tested by accident: it
is the `else` branch everywhere**, and the toolchain's guards were written from the PRD path
outward. That is worth a check of its own and does not have one.

### P56 is mine, and it is the third instance of one mistake

Item 76 added the CRD significance branch **the previous day**. I verified the screen *fired* and
not that anything downstream *acted* on what it emitted — which is the question item 76 existed to
answer.

> That is three times in two days: P52's *silent*, P54's *live reader*, and this. Every time, **an
> adjacent fact was measured and the load-bearing one inferred from it** — and this instance was
> introduced while fixing the second. The pattern is not carelessness about evidence; it is
> stopping one question short of the one that matters.

### Three defects in my own work on these two items

**A hand-built ADR fixture that did not match the producer.** `**Drives:**` takes a markdown link
and I wrote a bare filename, so `index_records()` parsed no drives at all — the undriven case
passed for the wrong reason and the driven case failed for the wrong one. Found by dumping what
the parser returned rather than reading the output. That is *a fixture must not agree with the
reader* inverted: one that does not match the **producer's** format tests nothing and fails in the
direction that looks like success.

**A helper nobody called.** Item 78's first pass added `checkout_guard()` to three harnesses and
called it in none; a failed edit in a loop then left three of six call sites missing — two
snapshotting without checking, one checking without a snapshot. Either half alone is decoration.
The check asserts both per harness, which is what caught it.

**A teardown that raised over a mutant's work.** The *guard deletes the evidence* mutant was
caught, and the cleanup then failed on the file the mutant had removed, turning a clean catch into
a traceback. Tolerant now, and re-verified failing cleanly.

### Verification

`python tests/test_toolchain.py` — **142 → 144**, `failed 0`, `known 0`. Every assertion of both
items watched failing: four for 77, four for 78.

**Item 77's fixes were verified against the crossing's own CRD**, which is the strongest available
control — the gate went from `3 blocked OK` to `1 blocking gap(s)` attributed by slug, and from
`2 significance OK` to `1 undriven`, on the document that exposed both.

---

## Phase 15 — The else branch, measured before it was believed.

Three fixes and one item, on branch `enforcement-parity-f1-f3`. **Specified by a measurement
rather than by the plan**: Phase 14 ended by saying *"the CRD path is the `else` branch
everywhere… that is worth a check of its own and does not have one"*, and this is that check —
after establishing that the sentence was true about something other than what it named.

| Item | Status | Commit |
|---|---|---|
| **P58 / P59 / P60** — three assertions with a PRD directory's shape | **Landed** 2026-09-09 | `a49112a` |
| **79** — every assertion says which paths it reaches, probed by running | **Landed** 2026-09-09 | — |
| **F2 / P62** — the placeholder names the shape, on a skill that takes either | **Landed** 2026-09-09 | — |

**Suite:** 144 checks at branch point → **149**. `failed 0`, `known 0`.

### The measurement said the class was not `isdir`, and that changed what got built

The plan for this work was a lint. The count killed it:

| `isdir` / `is_dir` calls | 43, across 28 files |
|---|---|
| on a tasks directory, repo root, worktree or discovery candidate | 22 |
| on a document, PRD-only and refusing a CRD with `exit 2` and a reason | 7 |
| on a document, dispatching correctly | 10 |
| on a document, defective | 2 |

**A syntactic check would flag `select-features.py`**, which this ledger names the canonical
dispatch, and would have found none of the three defects below — they are about a *value*, a
*caller* and a *printed line*, not a branch. The four known sites were the visible members of a
class whose defining property is not the call.

What the class actually is: **`parity.md` measures whether an element is on both paths;
nothing measured whether the check over it *runs* on both.** Four of the six known sites are
capabilities that file already records as `both`. The element was on two paths and its
assertion on one, and no file in the repository could express the difference.

### Three more sites, each with a PRD positive control

**P58 — a CRD's `<gaps>` were never validated.** `check-status.py` owns *`<gaps>` well-formed,
and aged* and had one caller. Misspelling both blocking kinds in the fifth crossing's own CRD:
the PRD control exits 1 with two named contradictions; the CRD got `exit 0` from every script
that reads it, and the gate printed `3 blocked OK`. **Item 29's execution stop, defeated by one
letter.** Generalised rather than duplicated — `check_gaps()` was already path-agnostic, so this
is a dispatch in `main()`, and *what document is this* still has one answer because it reads
`migrate.py`'s `ROOTS` instead of growing a second root regex.

**P59 — the gate reported a pass it had not established, twice.** An unrecognised `kind` was
`does not block` rather than `cannot be classified`. And `gap_err` was appended to `findings`
while the printed line keyed on `gaps` alone, so an assertion that could not run at all printed
`3 blocked OK` while `--json` carried `could not read the document`.

> **The comment three lines below records that identical defect being fixed for assertion 4** —
> *"counted in findings from the start and printed nowhere, which made the count the only
> evidence"* — and left it standing for assertion 3. A fix applied at the site of discovery
> rather than at the level of the problem, which is this repository's most repeated shape, here
> inside a single function.

**P60 — the significance-candidate screen had never seen a CRD**, sitting behind
`if os.path.isdir(features_dir)`. Item 76 gave the CRD branch the assertions about a *declared*
flag; this is the other direction. The cross-cutting half is **not ported literally**: a CRD is
one document, so counting documents that name it is structurally zero, and
`<impact-analysis><affected-features>` is the same claim in the vocabulary this document has.
One threshold, not a second.

All three verified against the fifth crossing's own artefacts, which is the strongest control
available.

### Item 79 — the column, and why it is four-valued rather than three

`Paths` in `checks.md`: `both`, `prd-only`, `crd-only`, `n/a`, with a reason required for
everything except `both`.

**`n/a` is not a hedge and it is the largest group — 12 of 30.** Classifying every row is what
produced it: `check-layering.py` reads task XML, `check-architecture.py` reads the project's
rule file, `task-integrity.py` reads a task against a ledger. Forcing a PRD/CRD answer onto
those invents an asymmetry on an axis that does not exist there — `parity.md`'s own warning
about reading the spelling, one level up.

The split: **9 `both`, 7 `prd-only`, 2 `crd-only`, 12 `n/a`.**

### The finding: filling in the column produced an ownerless row

Two `prd-only` rows had no written reason, and one of them would not settle by argument.
`check-prd-size.py` asks *does each prompt fit the model's context* — a question about a
document, and a CRD is a document — and it refuses one with `exit 2`. Deciding it needed a
measurement, which is the route that was chosen over settling it by assertion.

**No CRD corpus exists to measure.** The sample data is 67 features and one index, no CRDs and
no `PROJECT.md`. So the question was answered structurally instead, and the answer moved:

> The unbounded input on the CRD path is **not the CRD**. A CRD is one document authored by a
> person in an interview. `PROJECT.md` is generated from an existing codebase — one `<feature>`
> per feature, one entry per registry item — and **it scales with the codebase, not with an
> author.** The format spec sets no ceiling; the investigator's checklist sets only a floor
> (*at least 5 features cataloged*). On the reference fixture it is ~1,382 chars per feature, so
> **~156 features crosses the 60k budget and ~521 exhausts a 200k window.** Nothing measures it.

P5 is the same failure — a silently truncated read that everything downstream is built from —
and it is now an ownerless row, written on the day it was found. `check-prd-size.py`'s cell is
`prd-only` on a decided basis rather than an assumed one, and the risk it does not cover has
somewhere to live.

**That is the column paying for itself before a single probe ran.**

### The probes, and the two that were wrong

Nine `both` rows, nine probes, each running its owner twice — a well-formed CRD and one mutated
to carry the defect that assertion exists to catch. Seven key on the mutated **value**
(`decsion`, `wont-have`, `nope.md`, `banana`); a marker that is a *sentence* fails the next time
somebody improves a message, which is this plan's second recorded lesson.

**Two could not, and are recorded rather than bent into the shape.** `check-writable.py`'s
assertion is about a file that already exists, so no document carries a bad value and the two
states are `absent` and `present`; it keys on `REFUSED`, the token every script here prints to
refuse — a contract, not a phrasing. `migrate.py` keys on `R2`, a rule id from `migration.md`'s
registry.

**Both of those are second attempts.** The first pair — the filename, and `schema-` — appeared
in the *good* run as well as the broken one, so those probes distinguished nothing and reported
green. The good-run assertion caught them. **That is the first false pass in this project caught
by an instrument rather than by a person**, and it is the argument for asserting the negative
control inside the check rather than trusting the author to have run one.

### Verification

`python tests/test_toolchain.py` — **144 → 148**, `failed 0`, `known 0`, runner exit 0.

Every assertion of P58, P59 and P60 watched failing first, with both controls each: a well-formed
CRD must still pass, a correctly spelt blocking kind must still block, and a CRD that already
declares the flag must not be offered as a candidate.

**Item 79's own round: 7 mutants, 7 caught, baseline green before and after.** Three of the seven
are real historical regressions rather than invented ones — undoing P58, undoing item 77's
dispatch, and undoing group 8b's CRD branch. **The instrument catches the defects that took five
live crossings to find**, which is the only evidence that matters for a check written after the
fact.

### Three of my own, and one is a rule already written down

**A `\b` that became byte `0x08`.** A regex added through a heredoc arrived as `<\s*crd\x08`,
which matches nothing — so the new CRD branch would have refused every CRD, in the direction
that looks like a working refusal. `grep` renders the byte invisibly and the line read correctly;
`od -c` is what showed it. **This is a memory in this repository already** — *heredocs eat
backslash escapes* — broken by the person carrying it, one command after choosing the tool.

**Two probe markers that appeared in both runs**, described above. Worth separating from the
first: that one was a tool defect, this one was *not running my own negative control before
believing a green result*, which is Phase 1's first lesson.

**A separator row left at four columns** while the header went to six, because the rewrite keyed
on `startswith("| ")` and a markdown separator starts `|---`. Caught by asserting the column
count per row rather than by reading the diff.

### F2 — the fix reached the script and the instruction kept the old name

**Landed 2026-09-09, finding P62.** Suite **148 → 149**.

Item 77 taught four scripts to dispatch on document shape. `/breakdown` went on passing them
`{prd_dir}`, defined exactly once, at the only place the skill says what the placeholder is:

> *"the directory holding `index.md` and `features/` — the input file's directory, not the input
> file."*

That one definition governed five invocations, four of which take **either** shape — including
`check-coverage.py` and the gate. Followed literally on the CRD path, `{prd_dir}` is `docs/crd/`,
which is a directory, so the PRD branch **accepts it** and reads it as empty:

| Invocation | Given the CRD's directory | Given the CRD file |
|---|---|---|
| `check-references.py` | exit 0, `0 references checked` | 6 references, findings by name |
| `check-coverage.py` | exit 2, `no index.md in docs/crd` | `4 of 4 attributed` |

**The fifth crossing passed the file and got the right answer, contradicting its own
instructions.** That is P16 exactly — a prose guard that had held by luck — and it is the reason
this is a defect rather than a tidy-up.

`{document}` now names the four dual invocations and says what it is on **both** paths.
`{prd_dir}` survives at `check-prd-size.py`, the one script that takes a PRD directory and
nothing else. **The two names are different because the two arguments are**, which is the whole
content of the fix.

#### Item 79's check is structurally blind to this, and that is worth stating

`check-enforcement.py` builds its own argv and always passes a CRD in its CRD shape. It probes
whether the **script** reaches the CRD path and can say nothing about whether the **skill** hands
it the right thing. Two adjacent questions, two checks — and the second was found by asking what
the first could not see, a day after building it.

#### The population is derived, not named

A document that dispatches on root element takes both shapes. **Exactly one file does**, and the
check fails if that stops being true rather than quietly measuring an empty set. `/prd` passing
`{prd_dir}` to the same dual scripts is **correct and must stay** — a single-shape placeholder in
a single-shape command — so the rule is scoped to documents that take both, not to the scripts.

#### The round found two defects in the check itself, and one is a rule already written down

**A negative control satisfied by a second site.** The rule *"renaming every placeholder must
fail"* was a count — *at least one PRD-only script still gets a PRD-shaped name* — and its mutant
**survived**: renaming `check-prd-size.py`'s placeholder left `check-artefacts.py
{input_path_or_prd_dir}` keeping the total above zero. That is the site-counting rule, in this
project's own memory, hit while writing the check that enforces a different one. It is now
per-script — a script whose first positional is named for a PRD must be handed a PRD-shaped
placeholder — so each site is individually load-bearing.

**No converse direction.** A placeholder promising either shape handed to a script that accepts
one would have passed. Item 69's lesson, and the mutant that removed a `metavar` failed on a
downstream count rather than on the thing that broke. Both directions now.

#### And three unrelated checks broke, which is the second lesson arriving on schedule

`select-features`, `check-coverage` and `check-gate` each asserted the literal string
`scripts/X.py {prd_dir} ...`. **The prose improved and three checks failed** — Phase 1's second
lesson, and the same rule as item 6: one assertion stated in four places gets changed in one of
them. Each now asserts the *runnable shape*, `python …/X.py {placeholder}`, which is what they
were always about; **the placeholder's name is P62's assertion and belongs to it alone.**

**Verification.** 5 mutants, 5 caught, baseline green either side: the gate's invocation reverted,
the definition losing its CRD half, every placeholder renamed, the definition deleted, and a
script dropping its dual `metavar`.

---

## Phase 16 — The sixth crossing, and the first driven end to end by a program.

**Run 2026-09-09** against a fixture rebuilt with `--clean`: 5 commits, 17 files, 8 passing
tests, no `PROJECT.md`. **All four steps pass.** Suite unchanged at 149 — every finding below is
one no static check can see, which is the sixth time that sentence has been written here.

| Step | Result | Cost |
|---|---|---|
| 1 `/crd-context` | PROJECT.md written, 5 features, 2 registries | 98s, $0.76 |
| 2 `/crd` | 7 EARS criteria, 1 gap, aged by the check item 79 added | 154s, $0.90 |
| 3 `/breakdown` | 5 tasks in 3 layers, coverage OK, gate names the gap | 1114s, $10.25 |
| 4 `/execute` | 5/5 verified, 5 merges, 25 tests from a baseline of 8 | 1654s, $6.40 |

**Verified against git and pytest rather than against the runs' own summaries**: `ledger-status.sh`
derives 5 verified with no missing commits, 5 merge commits exist, 0 worktrees are left, the
`test_delete_is_permanent` trap held, and `checkout-clean.py` reports the run added nothing to the
toolchain.

### What this crossing was for, and both changes worked

**Item 79's `check-status.py` invocation in `commands/crd.md` had never been executed.** It ran,
and aged a real gap: `gap 1 (decision) raised 2026-09-09, 0 days ago`.

**And `/crd` recorded that gap rather than inventing an answer** — *"Whether archiving an
already-archived link, or restoring one that is not archived… is undecided. Not covered by the
stakeholder's answers."* Nothing in the prompt told it to do that; the prompt supplied product
decisions and said only *"anything not covered above has not been decided."* The rule held on
its own.

**P62's `{document}` reached a live run.** `/breakdown` was handed the CRD file, the run's text
carries no `no index.md`, and `check-coverage.py` attributed 5 of 5 tasks.

**P60's candidate screen ran and correctly stayed silent** — no quality word, one affected
feature against a threshold of three, no declared flag. The `0 significance candidate(s)` count
is what proves the screen executed, which is why it is in the summary line rather than only in
the findings.

### The instrument was wrong first, and the run said so

The first attempt at step 2 got four clarifying questions and no document. **That is `/crd`
behaving correctly**: it is an interview, one non-interactive turn is not one, and it asks what
only a person can answer before it stops rather than inventing. *A refused run is not a failed
measurement* — this repository's own rule, and the second time it has been the first result of a
crossing.

The harness now supplies the stakeholder's answers up front, exactly as a hand-driven session
supplied them by typing. **The line it must not cross is item 21 run 2's**: nothing in the prompt
says what shape to write, which elements to fill, what to do about anything it is not told, or
that an undecided question belongs in `<gaps>`. Had it said the last of those, the finding above
would have measured the prompt.

### Four findings, each reproduced before it was recorded

**P63 — both `PROJECT.md` producers omit a required attribute, and the validator has no branch
for it.** **Closed by item 81, below — which also corrects this entry's claim about `name`.** `crd-investigator` and `project-context-finalizer` each wrote
`<feature id="save-link" name="Save a link">`. `built=` is **Required: Yes** in
`project-format.md` and appears in the investigator's own template; `name=` is not defined
anywhere. Two independent producers, the same substitution.

> `check_project_context()` validates `built` **if present** and warns about the pre-item-45
> `status` **if present**. There is no branch for neither — **the else-branch shape item 79 is
> about, in a validator rather than a dispatch.** The refusal that does happen comes from version
> detection: *"matches no known schema version. `migrate.py --detect` escalates rather than
> guessing"* — and `migrate.py` then correctly answers `ESCALATE … no migration can be selected`.
> The message names a remedy that cannot apply, because R3's precondition needs the `status=`
> that is also absent.

**P64 — nothing asserts a task file is well-formed XML, and three readers hide it in turn.**
**Closed by item 80, below.**
Reproduced from scratch: one well-formed task and one with `<contract kind="schema">` unescaped
in prose.

| Reader | What it said |
|---|---|
| `build-manifest.py` | `2 task(s)`, exit 0 — it parses with `ElementTree` behind `except Exception` |
| `check-coverage.py` | `1 of 2 task(s) attributed`, exit 0 |
| `breakdown-review-tasks` | PASSED, *"all required sections present"* — it reads the file as text |

The number points at **attribution**; the cause is a **broken file**. `checks.md` has no row for
*a task file parses*, and this is the ownerless row it should have had.

**P65 — `check-scope.py` no-ops silently on a key it does not know.** Given an `analysis.json`
carrying `scope_declared` instead of `scope` it prints *"nothing to compare: the analysis carried
no scope or confidence"* and exits 0. The key names are documented nowhere; `/breakdown` Phase 2
names the elements to extract and not the fields to write.

**P66 — a first `build-manifest.py` build writes none of the fields `/execute` documents
reading.** **Closed by item 82, below — which corrects this entry about `prd.project_path`.** Its output carries `schema_version`, `summary`, `task_inventory`, `toolchain_version`
and nothing else; `/execute` Step 2 says to extract `prd.slug`, `prd.project_path` and `layers`.
The second of those is the fallback for a run given no `--project-path`, so the fallback can
never fire.

### And one the run got right about itself

`task-generator` **refused an instruction from its own orchestrator.** The run had told it
`requirement-level` was the lowest level among carried criteria; the format spec says the
highest, and the agent flagged the contradiction with the spec's rationale rather than complying.
It was right. That is the shape item 63 and item 3 were both built to protect, working without
being asked.

### `run_5_3.py` drives all four steps, which its docstring always claimed

`build_steps()` returned only `/execute`; steps 1-3 lived in a terminal history and their pass
criteria in someone's head — the exact thing the file was written to stop. Each new step asserts
by **running the script that owns the assertion**, never by reading the run's summary of itself.
The CRD path is **discovered**, because the slug is `/crd`'s decision and hardcoding it would turn
*it chose a different name* into *it wrote nothing*.

---

## Phase 17 — Item 80: a task file parses, and three readers stop deferring.

**P64, from the sixth crossing.** Suite **149 → 150**. The first of that crossing's four findings
to be closed, chosen because it is the only one where **three readers each reported a different
symptom for one cause**.

### What the crossing produced, and what each reader said about it

A generated `L4-001` carried `<contract kind="schema" ref="Link">` unescaped in prose. It was not
well-formed XML.

| Reader | Verdict | What it points at |
|---|---|---|
| `build-manifest.py` | `2 task(s)`, exit 0 | nothing |
| `check-coverage.py` | `1 of 2 attributed`, `criterion 7 named by no task` | **attribution** |
| `breakdown-review-tasks` | PASSED — *"all required sections present"* | **the file is fine** |

**Not one of those points at a broken file.** The coverage line is the one an operator would act
on, and it sends them to look at criteria. The reviewer's verdict is the most confident wrong
answer in the chain — `build-manifest` at least dropped the task and coverage at least reported a
number that was off.

### Why it was nobody's job, which is the finding rather than the bug

`build-manifest.py` parsed with `ElementTree` behind a bare `except Exception` whose comment read:

> `pass  # a malformed task file is item 4.x's problem, not this script's`

**The deferral was deliberate, and the owner it deferred to was never assigned.** `checks.md` had
no row for *a task file parses*. `check-coverage.py` then imported `edges_of` from that script —
correctly, because the rules for reading a task live in one place — and inherited the silence: a
file that cannot be parsed has no `<source-feature>` edges, and no edges reads as *attributed to
nothing*.

**The idiom was already in the repository three times over.** `check-architecture.py`,
`check-rules.py` and `check-project-md.py` all catch `ET.ParseError` by name and report its
position. `build-manifest.py` is the one that departed from it.

### What landed

`check-task-xml.py` is the owner, with a row and three callers. It asserts that a task file is
well-formed XML **and nothing else** — sections are `review-criteria.md`'s, rules are
`check-rules.py`'s, coverage is `check-coverage.py`'s — because a parse failure has to be settled
before any of those three can mean anything, which is also why it runs first in all three places.

| Caller | Where, and why there |
|---|---|
| `skills/breakdown/SKILL.md` | Phase 5 step 1, **before** the manifest is built |
| `skills/breakdown-review-tasks/SKILL.md` | criterion 7b, before every criterion that reads text |
| `skills/execute/SKILL.md` | after compatibility — **the consumer side, and the one that must refuse** |

`/execute` earns its caller on item 22's argument, one artefact further down: nothing on that path
parses a task. `task-integrity.py` hashes it and `execute-batch` hands it to an implementer to
*read*, so a malformed task arrives at a model as text and what it does with the region it cannot
delimit is unspecified — a plausible implementation of a subset nobody chose.

**`build-manifest.py` does not re-implement the check; it names the owner.** *The manifest matches
the files on disk* is its own assertion, and a manifest that silently omits a file it could not
read does not match them — so it now refuses, and points at the script that decides. That is the
pattern `check-status.py` already uses for a dangling index entry (*"check-rename.py owns that"*).

### Two defects in my own edit, both caught before the check ran

**A shadowed function.** Importing `task_files` from the new owner overwrote `build-manifest`'s
own `task_files()`, which means something narrower — the files matching `TASK_RE`, not every
`*.xml` — and the later `def` won anyway, so a 4-tuple would have reached a function expecting a
path. Only `parse_failures` is imported now, and the name collision is recorded where it happened.

**A missing `import importlib.util`**, in the same edit that added an `importlib` call.

Both are the ordinary cost of editing by patch script rather than by hand, and both surfaced
immediately because the file was run rather than read.

### Verification

`python tests/test_toolchain.py` — **149 → 150**, `failed 0`, `known 0`.

**7 mutants, 7 caught**, baseline green either side: the owner not refusing, the owner refusing
everything, the position dropped from the message, `build-manifest` reporting success again,
`build-manifest` refusing without naming the owner, the original `except Exception` restored, and
the registry row renamed away.

**And against the artefact that produced the finding**: the crossing's own five-task set passes,
and the same `L4-001` with the same unescaped `<` put back is refused by name at
`line 41, column 61`. That is the strongest control available for a check written after the fact.

---

## Phase 18 — Item 81: a feature declares its build state, and an unplaceable file says why.

**P63, from the sixth crossing.** Suite **150 → 151**. Two holes, and the second is the one that
made the first invisible.

### A correction to this ledger's own account of the finding, made by reading the spec

Phase 16 recorded that both producers *"omit the required `built=` and add an undefined `name=`"*.
**`name` is not undefined** — `project-format.md` marks it Required, as a *child element*. And
**both agent templates are correct**: `crd-investigator.md` and `project-context-finalizer.md`
each show `<feature id="…" built="…">` with `<name>` inside. The runs departed from templates
that were right.

That correction is what decided the work. If the templates were wrong, the fix would be prose. They
are not, so **the fix is the validator** — a rule stated in a template that nothing enforces is
P16, and two independent models drifted from it on the same day.

### Hole 1 — the branch that was missing

```python
if "built" in f:      enum(...)          # the current spelling
elif "status" in f:   warnings.append()  # the pre-item-45 one, accepted on read
                                         # and nothing for NEITHER
```

Item 79's else-branch shape, in a validator rather than a dispatch. A `<feature>` with no build
state passed every reader: `check-project-md.py` called the file *valid* with `features 5`.

### Hole 2 — and it would not have fired anyway

```python
if version is None:  escalate                       # <- the crossing's file landed here
else:                CHECKERS[kind](text, ...)      # <- so this never ran
```

**A file whose version cannot be detected was never content-checked at all.** And the two
conditions are frequently one file: a version is detected *from shape*, so an artefact that has
lost a required element loses its version with it. R3's `done` predicate requires every feature
entry to carry `built=` — which makes *missing required attribute* and *unknown schema version*
the same observation.

So the operator got one line:

> `matches no known schema version. `migrate.py --detect` escalates rather than guessing`

ran `/migrate`, and was correctly told `ESCALATE … no migration can be selected`. **A remedy named
by the only message they got, which cannot apply.**

**The escalation is not routed around** — that was a deliberate decision and it stands. The
diagnosis is added beside it: an unplaceable artefact is now judged against the current schema
*to say why*, labelled as such, because judging it against a version nobody could determine is the
guess the script refuses to make.

Against the crossing's own `PROJECT.md`, one line about schema versions became seven, each naming
a feature and the attribute it lacks.

### What is NOT built, and why it is written down instead

`project-format.md` marks four things Required on a `<feature>`: `id`, `built`, `name`, `files`.
This asserts the first two. **`name` and `files` are unchecked and stay that way** — there is
evidence of the `built` failure from a live run and none for the other two, and building checks
without evidence is how a check comes out wrong. Recorded here rather than silently added, which
is `checks.md`'s own rule about an assertion somebody specifies and does not build.

**A smaller correction inside the validator, which is the nicest detail here.** The old error
message read `f"<feature name=\"{f.get('name', '?')}\">"` — it reached for `name` as an
*attribute*, which the spec does not define. **The validator was modelling the wrong shape in its
own error text**, which is a plausible source for the shape both producers then wrote. It names
`id` now.

### Verification

`python tests/test_toolchain.py` — **150 → 151**, `failed 0`, `known 0`. Watched failing first,
with the message the crossing actually received.

**6 mutants, 6 caught**, baseline green either side: the else-branch removed, the diagnosis
removed, the feature no longer named, the legacy `status=` turned into a refusal, the enum check
removed, and the checker made to refuse everything.

**Two were caught by a different assertion than predicted, and that is worth recording rather
than tidying.** Removing the else-branch does not change the *exit code* — the file is still
unplaceable, so it still exits 1 — and what breaks is that no feature is named. **The exit code
alone never was the evidence here**; the naming assertion is what carries the finding, and the
mutation round is what showed which of the two was load-bearing.

---

## Phase 19 — Item 82: the manifest carries what `/execute` reads, and its reader keeps up.

**P66, from the sixth crossing.** Suite **151 → 152**. The finding was three-quarters right; the
quarter that was wrong is corrected here, and measuring it turned up a second defect that was
firing on every single run.

### What `/execute` documents reading, measured against what is written

| Documented at Step 2 | Measured |
|---|---|
| `prd.slug` | **never written on a first build** — only preserved on a rebuild that already had one |
| `prd.project_path` | **written** when `--project-path` is passed |
| `layers` | **stale** — item 66 superseded it |
| `summary.total_tasks` | written |

**The claim that `prd.project_path` could never fire was wrong**, and the record is corrected
rather than quietly dropped: `build-manifest.py`'s own docstring says it fills that field, and it
does. Phase 16's entry said otherwise because the probe ran the script without the argument.

**`layers` is the interesting one.** Item 66 made the layer set *derived* — `resolve-layers.py`
takes order from `layer_plan.json` and existence from `task_inventory` — and the manifest has
never carried a `layers` key. `/execute` went on documenting the extraction of a field that does
not exist, which is the same shape as F2 one artefact along: **a consumer instruction left behind
by the producer change that superseded it.**

### `prd.slug` is load-bearing, and the gap was filled by a model guessing

It is not a label. It names `{project_path}/.execute/{prd_slug}/` — so **the ledger path depends
on it** — and `task-integrity.py record`, `ledger-status.sh` and `write-state.py` all take it. It
appears nine times in `/execute`.

With nothing to read, the value is inferred. The sixth crossing's run inferred it correctly and
then **hand-wrote a whole `prd` block into the manifest** — `slug`, `name`, `source_document`,
`input_format`, `project_type`, `repo_structure` — and re-ran the build to check they survived. The
workaround is in the run's own report, and it is the clearest possible statement of the gap.

That a guess is usually right is P16: the tasks directory's basename *is* the slug, by
construction, because `resolve-output.sh` resolves `docs/tasks/{slug}`. **So the derivation is
sound and now belongs to the producer**, which is why `build-manifest.py` derives it from exactly
that rather than growing an argument every caller would have to pass correctly to reach the same
string.

### The second defect: a correct design decision with no guard on it

`build-manifest.py` declares `MANIFEST_SCHEMA_VERSION`; `check-compatibility.py` declares
`READER_SCHEMA`. **Separately and on purpose** — the reader's docstring says importing the
producer's constant would make the comparison vacuous, and that reasoning is right.

Item 65 moved the producer to `1.3` (`a9964ea`) and left the reader at `1.2`. For two phases:

```
WARN   manifest schema_version 1.3 is newer than this toolchain reads (1.2) ...
NOTE   produced by toolchain 2.0.0, which is this one
```

**Every manifest this toolchain wrote warned against a reader inside the same toolchain**, with
the contradiction printed on the next line. A warning that fires on every correct run is one an
operator stops reading — and it is the same warning that would matter if a manifest really were
from a newer toolchain.

The two constants stay independent. **The regression suite is the one place allowed to know both
numbers**, and it now compares them: same major, reader's minor at or above the producer's. Both
moved to `1.4` here, together, and each declaration now says in a comment that moving it means
moving the other.

### A check of my own repaired, and it is a named variant

That comment broke an existing check. Item 24's assertion scanned `check-compatibility.py` for any
line mentioning `MANIFEST_SCHEMA_VERSION`, to stop the reader importing the producer's constant —
and a comment saying *keep this at or above `MANIFEST_SCHEMA_VERSION`* tripped it.

**That is the "too broad — forbidding a word" row of this project's own mutation table**: a
different, legitimate mechanism trips a check aimed at another one. A cross-reference in prose is
what `checks.md` asks every script to carry; an import is what the check exists to stop; only one
of them is code. It scans executable lines now, and was **watched still catching a real
`from build_manifest import MANIFEST_SCHEMA_VERSION`** before being called fixed.

### Verification

`python tests/test_toolchain.py` — **151 → 152**, `failed 0`, `known 0`.

**6 mutants, 6 caught**, baseline green either side: the first build not writing the slug, the
producer moving without the reader, the reader falling behind alone, the majors diverging,
`/execute` documenting `layers` again, and the `prd` block no longer preserved across a rebuild.

**The last one survived its first round**, and the reason is worth keeping: the check asserted the
*slug* survived a rebuild, and the slug is re-derived on every build — so it survives even with
preservation deleted entirely. `project_path` is the field that can only come from the existing
manifest, and it is what the assertion tests now. **A rebuild assertion that only checks a derived
value tests nothing about preservation.**

---

## What the machine sleeping taught, which was not about sleep

A mutation round launched on the evening of 2026-08-26 was suspended overnight and resumed on
wake. **Nothing was lost and the result was correct** — but it occupied twelve hours of wall
clock, and a harness timeout cannot fire against a suspended process, so the run neither
finished nor failed until someone moved the mouse.

**The fix already existed and covered one caller.** `keep_awake` was defined inside
`tests/fixture/run_5_2.py`, used once, and its own docstring records the *identical* failure it
was written for: *"a run 10 resume was suspended from 23:24 to 08:13… a 2-hour run occupied 10
hours of wall clock, and the harness's own timeout never fired."* Written where it was
discovered, never generalised. It is now `tests/keep_awake.py`, used by the fixture runner, the
regression suite and every mutation harness.

That is this repository's most repeated shape, arriving in the test tooling rather than in the
skills: **a fix applied at the site of discovery rather than at the level of the problem.** Item
60 was the same (a rule added without removing what it contradicted); so was P18's TDD mandate
enforced in three places and documented in a fourth.

### Two of my own errors, recorded because one of them broke a rule that was already written down

**1. Wrapping `main()` swallowed the entry point.** The first `keep_awake` wrap indented
`if __name__ == "__main__":` into the function, so the suite defined `main()`, never called it,
printed nothing and **exited 0**. A harness that runs no checks and reports success is the worst
available failure — and it is the reason the exit code alone is never the result.

**2. `git checkout -- tests/test_toolchain.py` on a file with uncommitted work.** Item 54's entry
says exactly this must not be done, and the reason. It discarded the item 26 and 57 checks;
they were recovered by re-running the scratchpad patch script, which was luck rather than design.

**A rule broken by the person who wrote it is a prose guard**, which is P16 — so it is now an
exit code. `tests/dirty-guard.sh` refuses a checkout that would discard uncommitted work and
names the line counts at risk. Watched refusing on a dirty file and passing on a clean one.


## What six mutation rounds taught

Phase 3 wrote **ten new regression checks and ran 71 mutants across six rounds.** The suite was
green after every single check was first written, and **five of the first ten did no work at
all.** That is the phase's most useful output, ahead of any of the eight items.

### Every failure had the same root: asserting text rather than the claim it carries

| Variant | How it presents | Example |
|---|---|---|
| **Too loose** — token presence | mutant deletes the mechanism, the word survives elsewhere, check passes | `architecture.md` appears five times in `plan-layers` |
| **Too tight** — pinned phrasing | the document *improves* and the check fails | `"replaces the five tiers below"` after item 31 removed the list |
| **Too broad** — forbidding a word | a different, *legitimate* mechanism trips it | banning "architecture" in `execute-batch`'s args, then item 56 added a legitimate `--rules` forward |
| **`or` across locations** | either end alone satisfies a producer/consumer pair | the degenerate case, asserted in Phase 3 **or** Phase 4 |
| **Whole-file scope** | finds the *explanation* of a mechanism after the mechanism is deleted | both callers of `check-rules.py` also describe it in prose |

The last one generalises: **when a document mentions something twice — once to do it, once to
explain it — a substring check finds the explanation.** Prose about a mechanism outlives the
mechanism.

### What works, strongest first

1. **Find something to parse.** `plan-layers`' documented JSON is parsed and compared key-for-key
   against live `check-architecture.py --json` output; `crd-format.md`'s `<affected-contracts>`
   sample is parsed as XML and its `kind` set asserted. This is 23a's pattern and it survives any
   rewording.
2. **Scope to the region that owns the claim.** The invocation sentence, not the section. A
   *table row*, not the table — the mutant that survived overnight reverted one row of the layer
   derivation while the other row kept the words the check looked for.
3. **Assert a shape.** A fenced block containing `<step kind="decision">`; a runnable invocation
   inside a ```bash fence; a parsed phase sequence checked for ascending uniqueness.
4. **Assert what must be TRUE, never what must be absent.** The `execute-batch` assertion took
   three attempts before it stopped hunting for forbidden words and simply required the sentence
   *"Read the task instead"*.

### The instrument needs the same scepticism as the subject

Four harness failures, each of which produced a confident wrong number:

| Defect | Reported | Actually |
|---|---|---|
| stale expected check name after a rename | 6/13 | 11/13 |
| suite **red before mutating** — a failing check catches everything | 13/13 | hollow |
| suite run **concurrently** with a mutation harness | 2 FAILs | phantom |
| `main()` never called after a bad wrap | exit 0, silent | zero checks run |

Phase 1's rule gains two companions:

> A green result whose mechanism has not been shown is not a result.
> **A red result whose baseline has not been shown is not a result either.**
> **And a result from an instrument that was itself modified mid-run is not a result at all.**

The harness now refuses a non-green baseline, warns when a check fails that no mutant expected,
and holds `keep_awake` so a long round is not suspended.


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
