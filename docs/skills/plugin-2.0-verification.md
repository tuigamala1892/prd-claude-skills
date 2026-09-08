# Plugin 2.0 — Implementation Verification

**Status:** Findings **V1–V13**, each re-verified against the repository before being written
down. **V1–V4 graduated to [`plugin-2.0-plan.md`](plugin-2.0-plan.md) as P46–P49 and items 68–71**;
V5–V13 are recorded here and remediated without new items, because each is either a measurement
the plan already specifies or a document that has gone stale.

**All of B1–B7 landed 2026-09-08.** B1–B6 as **Phase 10** (`de812a2`), suite 129 → 133, mutation
14/14; B7 as **Phase 11** (`d603c74`), suite 133 → **137**, mutation 15/15 after 12/15. `failed 0`,
`known 0` throughout. This line is here rather than left to be inferred — a status header that has
stopped being true is V8, and writing this document without one would have been the finding
arriving in the document that reported it.

**V5 is closed.** Open question 7's experiment ran on 2026-09-08; the answer is **LOAD-BEARING**,
and it landed as Phase 12 and item 73 along with a second finding, P52, left ownerless on purpose.

**V6's size half is taken.** The trajectory across all six fixture versions is recorded at item
21, and asserted against `probe-p1.py --baseline` rather than left as prose. The headline is the
opposite of what the plan feared: **item 33's EARS change made features smaller** — 8 words and 24
elements out — and what doubled the prose is the content the bar asks for, not the syntax. The
**timing half remains genuinely outstanding** and cannot be scripted: it is a stopwatch against a
person authoring the same features under both templates.

**Its second clause is taken, and it inverts the first result.** Item 21 asks for the time *"and
where the time goes"*. Where it goes is now measured — `probe-p1.py --decisions` counts the
judgements a template demands that a machine is **forbidden** to make, and it goes **0 → 32**
across four features. `schema-3`, the version that made features *smaller*, introduces half of
every judgement the author now owes: item 33 is at once the largest saving in bytes and the joint
largest cost in decisions, which the size table alone scored as a clear win.

**The stopwatch is still a person's**, but it is no longer undefined: item 21 carries a five-step
protocol, so the reason it sat undone through thirteen phases — *"time the authoring"* does not
say what to do — no longer holds.

**V7 is decided.** The three `open` rows were not three of a kind:

- **Declared dependency edges — settled as deliberate.** `<depends-on>` orders items *within* a
  document and a CRD is one item. Ordering between separate CRDs is a different capability that
  **nothing consumes**; adding the element would be a producer with no reader, which is what item
  27 itself refused.
- **A data model channel — the row was reading the spelling.** `<contract kind="schema">` is the
  CRD's channel and it has readers. What is genuinely missing is narrower and now its own row:
  that channel never reaches a task. **P53, item 75.**
- **The significance flag — sharpened into a defect.** `check-references.py` reads
  `<architecturally-significant>` and `check-gate.py` runs it for a CRD, while `crd-format.md`
  mentions it zero times. A live reader with no producer — P46's shape, on the other path.
  **P54, item 76.**

**Neither item is built.** Both are specified in plan §Q, which is the state `checks.md` describes
for an assertion somebody has specified and not yet built.
**Date:** 2026-09-08
**Subject:** the repository at `2652266`, read against `plugin-2.0-plan.md` — 67 items, findings
P1–P45, nine phases, all recorded as landed in
[`plugin-2.0-progress.md`](plugin-2.0-progress.md).
**Relationship to the other documents:**
[`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md) fixed the *mechanics*;
`plugin-2.0-plan.md` addresses *fidelity*; [`sdd-comparison.md`](sdd-comparison.md) addresses
*position*; [`plugin-2.0-plan-review.md`](plugin-2.0-plan-review.md) addressed the *executability
of the plan*. This document addresses the **fidelity of the implementation to the plan**: whether
what the ledger says landed is what is on disk, and what landed beside it that nobody wrote down.

**Findings are graded** as in the other four documents — Blocking / Correctness / Consistency /
Structural / Measured — and numbered **V1–V13** so they do not collide with F1–F24, P1–P45,
C1–C10, S1–S5 or R1–R17. Remediation items are lettered **B1–B7**: A1–A10 belong to the plan
review, and the plan's own items are changes to the toolchain.

**Verification status is stated per finding:**

- **By running it** — a script or the suite was run and its output is reproduced.
- **Against repository** — files were compared; paths and line numbers are given at `2652266`.
- **Argued** — no measurement settles it; the finding is a judgement and is labelled as one.

> **The implementation is worth this scrutiny, which is why it is getting it.** Section 2 is not a
> courtesy paragraph. Three of the four defects in §3.1 and §3.2 were found *by* machinery this
> plan built, or *in* it, and none of them argues against the machinery.

---

## 1. Method, and its limits

Every one of the 67 items was read in the plan and then looked for on disk, rather than checked
against the ledger's claim about it. Beyond that:

- `python tests/test_toolchain.py` — **129 checks, `failed 0`, `known 0`**, matching the ledger.
- `schema/scripts/check-readers.py`, `skills/breakdown/scripts/check-definition.py` and the
  `checks.md` caller table were **run**, not read, and their output is quoted below.
- Every CLI flag the plan specifies (`--priority`, `--requirement-level`, `--include-tbd`,
  `--resume`, `--strict`, `--check`, `--dry-run`) was searched for and found.
- Every element the plan retires (`<phases>`, `<needs-clarification>`, `<relationships>`,
  `<feature-phase>`, a feature-level `<priority>`) was searched for and is either absent or
  present only as a retired spelling a reader still recognises.
- Every element the plan introduces was checked for a producer **and** a reader — item 23's rule,
  applied to the implementation that added it. That is what found V1.

**What was not done, and it matters.**

- **No live crossing was run.** Phases 7 and 9 were both specified by watching the toolchain run,
  and five of Phase 7's six items were invisible to 112 static checks. This document is static
  analysis, so it is blind in exactly the direction the ledger has twice proved matters most.
  V1 is the one finding here that a run would probably have surfaced.
- **The sample corpus is out of version control**, so every figure in the plan's §2 is taken on
  trust and was not re-derived.
- **No mutation round was run** against the fixes this document proposes. That is Phase 10's job,
  and this repository's rule is that a green check whose mechanism has not been shown failing is
  not a result.

**The findings were re-verified before being written up**, following the plan's own precedent —
ten of the review's seventeen were independently checked before A1 acted on them, and R8 was the
one the plan had not found on its own. **All thirteen held.** Two got sharper under re-checking,
and both are noted where they appear (V1 and V4).

---

## 2. What the implementation gets right

Four things, stated because the remediation below is small relative to them and would otherwise
read as a rejection.

**All 67 items are on disk, not merely claimed.** Every commit the ledger cites resolves, every
script it names exists and runs, and the departures it records are visible in the code as
described — item 16's attribute form on a repeatable `<source-feature>`, item 40's second gate
half deferred to schema-6 and then delivered, item 24's stamp written once and never updated.
Nothing in the ledger was found to be an overstatement.

**The schema chain is real.** `schema-1` through `schema-6` each have a fixture, five of the six
are frozen under a content hash, and the non-current ones are inputs to the migration comparison
rather than decoration. `SCHEMAS.json` carries two *corrected predictions* — items 16 and 17 not
being a schema version, item 11 arriving a version early — kept rather than deleted, which is the
only evidence a prediction was ever checked.

**R8 is fixed, and fixed in the direction the review argued.** `check-project-md.py` requires at
least one `*-registry` rather than two named ones, and each consumer checks what it actually
reads. A CLI project seeded with only a `<command-registry>` now passes the guard it should pass.

**The three registries are the plan's best invention, and this document is evidence for them.**
`checks.md`, `readers.md` and `parity.md` turn *who reads this* from a claim into a measurement.
Two of the four defects below were found by running that machinery, and a third is *in* it. A
registry that can be caught out of date is worth more than a paragraph that cannot.

---

## 3. Findings

### 3.1 Correctness

**V1 — `<review>` has a reader, a fixture and a migration rule, and no producer.**
*Verification: by running it, and against repository. Grade: Correctness.*

Schema-6 exists to give item 40's gate its second half. The element is defined in
[`core.md`](../../schema/core.md) §7, read by
[`check-definition.py`](../../skills/breakdown/scripts/check-definition.py), written by a
migration rule (R13), and carried by all six schema-6 fixture features. Running the gate on the
fixture confirms the reader works:

```
the bar applied to 3 features: 0 mechanical failures, 3 of 3 reviewed,
0 one-way edges to triage; criterion priority: P0 9, P1 3
```

**Nothing on the authoring path can produce one.** A search of `commands/`, all of `skills/` and
`schema/prd-format.md` for `<review` or `record-review` returns **zero matches** — that count is
the finding sharpened, having first been stated only as *prd-format.md omits it*. The feature
template at [`prd-format.md:216-270`](../../schema/prd-format.md#L216-L270) shows every other
`<meta>` element and cites core §1, §2, §3, §4 and §6; **§7 is the only section of the core that no
format reference points at.**

Worse, [`commands/prd.md:445-447`](../../commands/prd.md#L445-L447) instructs the opposite:

> `defined` needs both halves: the mechanical tests passing *and* a review recorded. **Where the
> PRD carries no place to record that review, say so plainly to the author** rather than treating
> the absence as a pass.

That sentence was true before schema-6 and is false after it. A `/prd` run following its own
command file will tell the author there is nowhere to record a review, in the schema version whose
headline change is the place to record a review.

**This is the plan's closing argument failing inside the version that shipped it**, and
`check-readers.py` cannot see it: the rule it enforces is *every element has a reader*, and the
reverse direction is a report rather than a check — a deliberate decision, recorded in
`readers.md`, and defensible. This is what it costs.

**V2 — two bare relative script paths, both added in Phase 8.**
*Verification: against repository. Grade: Correctness.*

Open question 1 measured this and item 9 states the rule: the working directory is the target
project, so a bare relative path resolves against the wrong tree and fails with a bare *No such
file or directory* that reads like a missing file rather than a wrong assumption. Every invocation
site in the repository uses `${CLAUDE_PLUGIN_ROOT}` or `{skill_dir}` — except two, both Phase 8
additions:

| Site | Command |
|---|---|
| [`crd-format.md:98`](../../skills/crd/references/crd-format.md#L98) | `python skills/breakdown/scripts/check-references.py ...` |
| [`migration.md:288`](../../schema/migration.md#L288) | `python skills/breakdown/scripts/check-definition.py ... --record-review --by ...` |

`migration.md` uses `${CLAUDE_PLUGIN_ROOT}` for the identical purpose 87 lines later, so the
inconsistency sits inside one file. And the second of the two is the **only documented invocation
of the producer V1 says is missing** — so an operator who finds it cannot run it.

### 3.2 Consistency — the registries describe a toolchain that has moved

**V3 — the assertion registry has drifted, and only one direction is checked.**
*Verification: by running it. Grade: Structural.*

`checks.md` carries 23 owner rows and states its own rule: *every assertion the toolchain makes
about an artefact names the script that makes it, and the callers that run it*, and *a script
nobody calls is not an assertion, it is a file*. The suite
([`test_toolchain.py:5936-5955`](../../tests/test_toolchain.py#L5936-L5955)) checks that each
owner exists and that each **claimed** caller names it. It never checks the reverse, so both kinds
of drift are invisible.

**Two Phase 7 assertions have no row at all.**

| Script | Decides | Exit codes |
|---|---|---|
| `task-integrity.py verify` | is every recorded task file byte-identical | `0` unchanged · `1` EDITED, a stop · `2` refused |
| `resolve-layers.py` | which layers this run executes | `0` resolved · `1` REFUSED · `2` unreadable |

Neither falls under the table's stated exclusions. The excluded list names seven scripts that *do*
things rather than decide them — all seven predate Phase 7 — and `resolve-output.sh`, a resolver
with a refusal, **is** in the table. `record` does a thing; `verify` decides one.

**Three caller lists are stale**, two of them by a Phase 8 change:

- `build-what-next.py` is run by [`commands/prd.md:494`](../../commands/prd.md#L494); the row
  names only `schema/prd-format.md`.
- `check-references.py` is invoked for a CRD by
  [`crd-format.md:98`](../../skills/crd/references/crd-format.md#L98) and by `check-gate.py:183`,
  both wired at group 8b; the row names neither.
- `check-coverage.py` is invoked by `check-gate.py`; the row names only `breakdown/SKILL.md`.

**V4 — three shipped artefacts describe a state the toolchain has left.**
*Verification: by running it, and against repository. Grade: Consistency.*

**(a) A script tells an operator that a landed item has not landed.**
[`check-scope.py:109`](../../skills/breakdown/scripts/check-scope.py#L109) still reads
*ATTRIBUTION IS ITEM 16's, AND IT HAS NOT LANDED. A task file carries no `<source-feature>` yet.*
Item 16 landed two commits later at `4bda3ca`, and the code twenty lines below already calls
`build_manifest.edges_of()` — item 65's multi-edge form. The docstring is a comment; the
operator-facing half is not. [Line 170](../../skills/breakdown/scripts/check-scope.py#L170) prints
*(item 16 adds the attribution)*, so a real generator defect now reads as a not-yet-built feature.

**(b) A registry states a count that is wrong.** `readers.md` says *Three filters take it to
**six***, and names three real signals plus three placeholders. Running it gives **seven**:

```
127 elements defined: 90 read by a script, 27 by an instruction, 10 unread (0 open), 0 undeclared
```

with seven `READ-ONLY` lines. The extra is `<requirement-level>`, and it is neither category the
prose accounts for — not a retired spelling and not a placeholder, but a live task-format element
read by `write-state.py`.

**(c) Three sibling registries stamp a superseded schema.** `checks.md`, `parity.md` and
`readers.md` all carry `schema="schema-5"` while `core.md` and `SCHEMAS.json` say `schema-6`, and
only `core.md`'s stamp is asserted by the suite. **This finding got sharper on re-checking, and
the sharper version is the useful one.** Either the stamp means what `core.md` says its own means —
the artefact schema currently written — in which case all three are simply wrong; or it means
*this table was last reconciled against schema-5*, in which case **the stamp was already saying the
registries were a version behind, and nothing read it.** The second reading is corroborated
independently: (b) is a schema-6-era element the prose does not cover, and V3's missing rows are
Phase 7 and 8 arrivals. A stamp nobody reads is P28's own finding, one level in.

### 3.3 Owed — two measurements the plan specifies and nobody has taken

**V5 — open question 7's experiment was never run.**
*Verification: against repository. Grade: Measured.*

OQ7 asks whether the layer graph is load-bearing or convention, specifies the experiment — run the
fixture through the default graph and through a deliberately poor one, compare the task sets — and
writes the **decision rule in advance**, including *the difference is small or unclear → treat as
load-bearing*. The mitigations shipped: the five-tier graph is a default rather than a
requirement, a supplied `<layers>` is validated acyclic and reachable, and `architecture.json`
records which graph was used. The experiment that decides what ships *alongside* them did not, and
`plugin-2.0-progress.md` does not mention it. On the load-bearing outcome item 43 owes a third
fixture arm and `/breakdown` owes a report line; on the convention outcome, neither.

**V6 — item 21's authoring after-measurement was never taken.**
*Verification: against repository. Grade: Measured.*

`probe-p1.py --baseline` recorded 394 words, 8 criteria and 64 elements across four features, on
what is now `schema-1`. Items 33, 34, 1, 2, 27, 29 and 35 then changed exactly what it measures.
The ledger records the *timing* half as half-delivered and says so, which was honest at the time;
what is outstanding is the **size** half, which is scriptable and would take one command against
the schema-6 fixture. The plan's argument was *one number beats none*, and there is still one
number.

**V7 — three `open` rows in `parity.md`.**
*Verification: by running it. Grade: Measured. No action proposed.*

The CRD path has no `<depends-on>`, no `<data-model>` and no `<architecturally-significant>`
([`parity.md:58-60`](../../schema/parity.md#L58-L60)). These are correctly recorded, with reasons,
under a verdict the file declares legitimate. Listed here only so a reader does not mistake them
for something this document missed.

### 3.4 The documents describe a smaller project than exists

*Verification for V8–V13: against repository. Grade: Consistency.*

**V8 — the plan's status header is stale by five phases.** It reads *Phases 1–4 complete, Phase 5
in progress on branch `phase-5-consumers-and-parity`* and, later, *Composed, they give six
phases*. There are nine, all landed and merged.

**V9 — §6's summary table stops at item 60.** Items **61–67 have no rows**, in the table that is
the plan's item index and whose numbering discipline the plan review specifically praised.

**V10 — §6 has no Phase 8 or Phase 9, and item 67 is in no phase list.** The ledger's grouping is
the only record of where the last three groups sit. That is defensible for Phase 8, which the
ledger explicitly claims as its own grouping rather than the plan's; it is not defensible for item
67, which is a plan item with a specification and no place in the sequence.

**V11 — Phase 3's six ledger rows carry `_` instead of commit hashes**
([`plugin-2.0-progress.md:739-744`](plugin-2.0-progress.md#L739-L744)), in a repository with a
dedicated commit type for *The ledger cites the commit it describes*. They are `3982022`
(25+28+37), `3c6781f` (51), `7d320b0` (31+56) and `95ac1fc` (26+57).

**V12 — three top-level documents were never reconciled.** Nine phases landed without touching
them, and the ledger never mentions any of the three.

| Document | What it still says |
|---|---|
| `ARCHITECTURE.md` | the `.claude/` layout `CLAUDE.md` warns against; an `execute-task` skill in four places including a diagram and the model table, which `CLAUDE.md` says does not exist; **zero** occurrences of `schema/`, item 44's central artefact |
| `README.md` | *14 skills* and *8 subagent definitions* against 15 and 10; no `schema/` in the layout; `claude --plugin-dir <path>` alone, where `CLAUDE.md` records — measured — that `--add-dir` is also required or `/breakdown` stops in Phase 1 |
| `target-state-data-flow.md` | **Status: Target state. None of this is built.** |

**V13 — `CLAUDE.md`'s Key Directories tree omits what four phases added.** No
`prd-criteria-author.md`, no `architecture-format.md`, none of `checks.md`, `parity.md` or
`readers.md`, and 2 of the 33 scripts under `skills/` and `schema/`.

---

## 4. Remediation

**B1. Give `<review>` a producer** (V1) → **item 68**. Three edits: the element in
`prd-format.md`'s `<meta>` template with a pointer to core §7; the `--record-review` invocation in
`commands/prd.md` Phase 7, beside the agent dispatch that produces the judgement it records; and
the replacement of the *carries no place to record that review* sentence, which is now the
instruction that causes the defect. A check that the authoring path names the producer, watched
failing first.

**B2. Register the two Phase 7 assertions and close the caller lists** (V3) → **item 69**. Two
rows for `task-integrity.py` and `resolve-layers.py`; three corrected `Invoked by` cells. **And
the reverse check**, which is the item's real content: for every owner in the table, every file
that invokes it must be listed. Without it these rows drift again the next time somebody wires a
script in — which has happened twice in the last two phases.

**B3. Replace the two bare relative paths** (V2) → **item 70**. Mechanical, and worth a check
because there is now a rule with two violations rather than a convention with none.

**B4. Correct the three stale artefacts, and decide what the sibling stamps mean** (V4) → **item
71**. (a) and (b) are edits. (c) is a decision: either the stamp on `checks.md`, `parity.md` and
`readers.md` means what `core.md`'s means, in which case bump all three and extend the suite's
existing assertion to cover them; or it means *last reconciled at*, in which case each file must
say so and the stamp needs a reader. **Recommended: the first** — one meaning for one syntax, and
the *reconciled at* claim is better served by the reverse check B2 adds.

**B5. Record the two owed measurements where a reader looks** (V5, V6). No new items: both are
already specified, and inventing items for them would be a second producer for one idea. A status
line on OQ7 and on item 21 saying *unrun as of 2026-09-08*, in the idiom of `parity.md`'s `open`
verdict and `SCHEMAS.json`'s `content_work` — a named-but-undone thing written down where somebody
will meet it.

**B6. One editing pass over the plan and the ledger** (V8–V11). Header, seven summary rows,
Phases 8 and 9 in §6's sequence with item 67 placed, and Phase 3's four commit hashes.

**B7. Reconcile the three top-level documents** (V12), and refresh `CLAUDE.md`'s tree (V13). **Its
own phase.** `ARCHITECTURE.md` is 643 lines describing a toolchain that has moved through six
schema versions, two new artefacts and 33 scripts; folding it into the same branch as B1–B4 would
produce one large phase in place of two shippable ones.

---

## 5. Sequence

**Phase 10 — B1 · B2 · B3 · B4 · B5 · B6.** Items 68–71 plus two status lines and an editing
pass. **B1 first**, because it is the only one a user meets: a `/prd` run today is told a place
does not exist. **B2 before B4(c)**, because the reverse check is what makes the stamp decision
cheap. **B6 last**, so the plan's summary table is edited once with items 68–71 already in it.

**Phase 11 — B7.** The three top-level documents, and `CLAUDE.md`'s tree.

Every fix in Phase 10 gets a regression check watched failing first, and a mutation round against a
stated-green baseline. Neither is optional here: three of the four findings are **stale prose in a
shipped artefact**, and this ledger has recorded five times that a check asserting text rather than
the claim it carries passes while doing nothing.

---

## 6. What this document does not do

**It does not re-open any settled decision.** Every departure the ledger records was checked and
none is disputed. The four items proposed above are defects that arrived *after* decisions that
were right, which is the same shape as Phase 7.

**It does not run the toolchain.** §1 says so plainly, and it is the limit that matters: the two
phases specified by watching a run found eleven things between them, and none was visible to a
suite that was green. A fifth live crossing would be worth more than this document, and V1 is the
finding that suggests one is due.

**It does not price anything.** As in the plan: the grades rank severity, not effort.
