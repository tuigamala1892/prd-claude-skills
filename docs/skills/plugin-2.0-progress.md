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
| **25 + 28 + 37** — the artefact, its guard, its readers | **Landed** 2026-08-26 | `_` |
| **51** — a Design phase in `/prd`, the producer | **Landed** 2026-08-26 | `_` |
| **31** — derive the layer set from content, both paths | **Landed** 2026-08-26 | `_` |
| **56** — enforce `<banned>` and `<task-limits>` | **Landed** 2026-08-26 | `_` |
| **26** — seed PROJECT.md on greenfield | **Landed** 2026-08-27 | `_` |
| **57** — impact analysis reports contracts, not APIs | **Landed** 2026-08-27 | `_` |

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
| **5b — the carry** | 16 · 17 · 30 · 59 | The boundary chain, in dependency order. 30 has nothing to check until `<source-feature>` exists; 59 is the first test that crosses the boundary 16, 17 and 30 specify. Splitting it means writing 59 twice. |
| **5c — the filters** | 13 · 14 · 15 · 19 · 20 | Five refusals and two flags, all reading tags that now exist, spread across `/breakdown` and `/execute`. Genuinely small — and they are one commit because they are one behaviour: *the toolchain declines work it was told not to do, and says which.* |
| **5d — the definition bar** | 58 · 3 · 6 · 7 · 40 · 8 | 58 is the table of assertions, 6 is its caller, 3 feeds it, 40 supplies the mechanical tests and 8 takes the judgement half. Splitting these means designing the same checker four times — the argument Phase 3 made about `architecture.md`, arriving again. |
| **5e — the residue** | 10 · 24 · 32 · 38 | Independent of each other and of the above. Last because nothing waits on them. |

**5a is complete** (two commits, not one: 46-48 were a schema version with a migration and a new fixture, which is not "small"). **5c is next.**

**5a and 5c first, in that order.** Both are edits to existing consumers with checkable
postconditions and no new design; 5a is overdue by the plan's own ordering. That leaves 5b and 5d —
the two expensive ones — a full sitting each, which is what they need rather than what is left over.

**What this split does not claim.** It does not reorder the phase: every constraint the plan states
between items is preserved, and the groups run in an order that satisfies all of them. It prices
nothing (A9 still holds), and 5d's boundary in particular is the one most likely to move, because
item 40 is adapted from a policy written elsewhere and has not yet been read against this corpus.

| Item | Status | Commit |
|---|---|---|
| **46 + 47 + 48** — the CRD path takes the parity changes (**schema-5**) | **Landed** 2026-08-27 | `6381ed8` |
| **49 + 50** — the PRD's scope/confidence readers, and parity as a check | **Landed** 2026-08-27 | `PENDING` |
| **13 + 14 + 15 + 19 + 20** — the filters | *Next* | — |
| **16 + 17 + 30 + 59** — the carry | *Not started* | — |
| **58 + 3 + 6 + 7 + 40 + 8** — the definition bar | *Not started* | — |
| **10 + 24 + 32 + 38** — the residue | *Not started* | — |

**Suite at branch point:** 86 checks, `failed 0`, `known 0`.

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

**Commit:** `PENDING` · **Addresses:** P19, P21, P30 · **Files:** `schema/core.md`,
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
