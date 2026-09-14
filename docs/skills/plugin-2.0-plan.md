# Plugin 2.0 — Fidelity Plan (PRD and CRD paths)

**Status:** **Phases 1–22 complete and merged as of 2026-09-10.** Phases 10 and 11 hold items
68–72 from [`plugin-2.0-verification.md`](plugin-2.0-verification.md) — a static verification of
the implementation against this document, which found four defects that arrived *after* the
decisions they sit beside, and four documents that had described a smaller project than exists
since before the plan began. Phases 12–22 hold items 73–85, from an experiment, two live
crossings, and one measurement of this document's own closing sentence. Phase 5 was the only
phase large enough to need splitting, and **the split into five commit groups is in the ledger**,
being a sequencing decision rather than a change to what is specified here. This document
stays a **specification**; what has actually landed, and where the implementation departed from
what is written here, is recorded in [`plugin-2.0-progress.md`](plugin-2.0-progress.md). Nothing
is implemented except what that file lists.

### How this document grows, which has been re-argued three times

**Two rules, and only the second one restricts what may be added here.**

**1. A discovery made after this plan was written is PLACED IN IT** — a finding in §3, an item in
its own lettered section, and a slot in §6's ordering — *labelled as found after the fact rather
than presented as foresight*. That is the practice `49d5c8b` set at item 60: *"Item 60 was found
by implementing 23a, not by planning, so the plan gains the finding and the item after the fact.
Recorded that way in both places rather than presented as foresight."* Sections **K** through
**U** are that rule in use: each holds the findings and items from one episode of discovery, and
each says which episode.

**2. Existing text is NEVER REFRAMED to accommodate a later discovery.** A heading, a claim or a
grade written before is left as it was written; where the implementation departed from it, the
departure is recorded in the ledger under `### Deviation(s) from the plan` or `### Departure N`.
That is the ledger's own charter — *"a companion to this file, which stays a specification"* — and
it has been broken once, at `4a36c62`, by retitling a Phase 7 heading. That was reverted.

**The two are easy to conflate because both protect this document's integrity**, and the search
that settled it is on record: on 2026-09-07 every session transcript was searched for an argument
that later work should stay out of the plan. **There is none**, and the precedent runs the other
way. Written here so it is not re-derived a fourth time.
**Date:** 2026-08-17
**Subject:** what `/prd` and `/crd` write, and how much of it survives into `/breakdown` and `/execute`
**Supersedes:** items **4.4** and **4.5** of [`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md), which are folded in below as items 12 and 18.
**Target state:** the data flow these items produce is drawn in
[`target-state-data-flow.md`](target-state-data-flow.md), which is the companion to
`ARCHITECTURE.md` §Data Flow.
**Evidence base:** a sample PRD corpus of 64 feature files (~628 KB, ~174k tokens) plus a full reading of the CRD path, measured rather than assumed.

---

## 1. Scope, and how this differs from the assessment

The assessment plan fixed the toolchain's *mechanics* — forking, worktrees, merges, state, path
resolution. All of that now works end to end. This plan is about **fidelity**: the assessment
never asked whether the content a requirements document carries actually reaches the code.

It began as a PRD-only plan and was extended to the CRD path at item 44; §5 J holds the parity
work, and opens with a ledger of which path is ahead on which concern. That ledger is worth reading
before the rest, because the CRD path is ahead on five counts and the more common repair direction
turns out to be CRD → PRD rather than the reverse.

It does not. Measured against a real corpus, `/prd` writes four kinds of content and the
pipeline consumes one of them:

| What `/prd` writes | Consumed downstream? |
|---|---|
| `<description>` | Yes — via `analysis.json` summaries |
| `<acceptance-criteria>` (up to 36 per feature) | **No** — no consumer on the PRD path (P2) |
| `<notes>` (up to 28 KB per feature) | **No** — zero consumers anywhere (P4) |
| MoSCoW priority | Extracted into `analysis.json`, then **never read** (P1) |

Three quarters of the document is written and discarded. Everything below follows from that.

Findings use the same grades as the assessment (Blocking / Correctness / Consistency /
Structural / Measured) and are numbered **P1–P38** so they do not collide with its F1–F24.

**Verification status is stated per finding.** "Static" means every file in `skills/`,
`commands/` and `agents/` was searched and the consumer does not exist. "Measured" means a
script was run against the corpus and its output is reproduced. Two items are explicitly
**unverified** and carry a probe to run rather than a fix to apply.

**Amended 2026-08-24.** P18–P22 and items 28–32 (§5 H) were folded in from
[`sdd-comparison.md`](sdd-comparison.md), which compares this toolchain against spec-kit, Kiro,
Tessl and Böckeler's taxonomy. They are recorded here rather than there because they are changes
to *this* toolchain, and the comparison document should hold the comparison. Each carries its
C-number from that document. Nothing numbered 1–27 or P1–P17 moved, so every existing
cross-reference still holds.

Their arrival changes one earlier item. Item 28 does **not** add a new file: item 25 already
proposes `architecture.md` as a prescriptive greenfield artefact, and it turns out to claim most
of the ground a project's rule file needs. Item 28 widens 25 rather than competing with it — see
the note there.

**Reviewed, and corrected, 2026-08-25.** An external critique
([`plugin-2.0-plan-review.md`](plugin-2.0-plan-review.md), findings R1–R17) found seventeen
executability defects, seven of them this document contradicting itself. R1–R7 are corrected here
and item 3's probe has been **re-run** rather than re-cited (A2). Ten of the seventeen were
independently verified against the plan and the repository before acting; all ten held, and R8 —
`check-project-md.py` hard-requires the two registries item 25 opens up — was a defect this
document had not found on its own. The remaining items are tracked in that review.

**Audited against itself, 2026-08-25.** Every element this plan introduces was checked for a named
reader, and every reader for a producer. **Nine failures, in a plan whose closing argument is that a
producer should have a reader** — two of them contradictions between items rather than omissions.
All are resolved in place: `<banned>` and `<task-limits>` gain enforcers (item 56), principles fold
into `architecture.md` rather than a file nothing creates (37), registries gain a reader (25),
`<confidence>` gains a producer on the PRD path (49), and the open-questions register is declared
**human-maintained and validate-only** (39, 40) rather than left looking like an oversight. Item 23
gains the check that would have caught all nine.

**Extended 2026-08-24 to cover the `/crd` path.** Findings P29–P32 and items 44–50 (§5 J) come
from reading the CRD command, its three sub-skills, its four agents and both of its format
references against this plan. The plan was PRD-only until then, which was a scoping choice that had
stopped being defensible: most of P1–P28 apply to both paths, the two paths define overlapping
schemas independently, and **the CRD path is ahead of the PRD path on five counts** — §5 J opens
with the ledger of who is ahead where, because that is what "best of both" has to be built from.

This is an extension rather than a counterpart document, deliberately. Two plans specifying one
shared schema is the producer/consumer drift this plan exists to describe (P10, item 22), and it
would duplicate items 33, 34, 40, 41 and 43 immediately.

**Re-measured 2026-08-24 against an updated corpus.** Every figure in §2 was re-taken; the
material changes are recorded there and in P9, P23 and P24. Two of them matter beyond the
arithmetic. The corpus has begun using a `<gaps>` element the plan had not anticipated, which
**replaces item 29's proposed `<needs-clarification>`** rather than sitting beside it — see item
29. **P9 has no live instance after all, and the retraction is recorded rather than quietly removed.**
An unindexed feature file was read here first as a dropped must-have, then as a rename residue. It
is neither: the sample was refreshed by overwriting the folder without clearing it, so the file is
a leftover from the previous copy of the corpus and never existed in the PRD. P9 is a predicted
failure again. What survives is P27 and the §2 method note.

Items **40 and 41** were added at the same time: a definition gate drawn from a policy written for
another project built with the original commands, and the migration guide that everything in
§5 A and §5 I now requires.

**Amended again 2026-08-24, after a study of Kiro's open-source spec formats.** P23–P25 and
items 33–39 (§5 I) come from that study and from the conventions of the project the sample corpus
was taken from. Three of them are format decisions rather than additions — EARS replaces
Given/When/Then (item 33), priority gains a second level (item 34), and the ADR template is
adopted wholesale from the corpus project rather than invented here (item 36). Nothing numbered
1–32 or P1–P22 moved. See [`sdd-comparison.md`](sdd-comparison.md) §11 for the comparative
argument.

**Re-verified after the fold, same day.** The folded claims were re-checked against the files
rather than against the comparison document, and three needed narrowing: P19 overstated the
absence of an uncertainty channel, P18's table misattributed two of its five rows, and items 28
and 31 both mis-costed themselves — 28 downwards, 31 upwards. Those corrections are in place
below. **P22 and item 32 were added at the same time**, because the comparison's C10 was the one
gap the first fold dropped.

---

## 2. What the corpus measures

Aggregate figures only; the corpus itself stays out of version control.

Figures re-taken 2026-08-24; the first-review value is shown where it moved.

| Measure | Value | First review |
|---|---|---|
| Feature files | 64 | 64 |
| Feature entries in `index.md` | 62 | 62 |
| Unindexed feature files | 2, both `superseded` | 2 |
| Total corpus size | **~628 KB ≈ 174k tokens** | ~594 KB ≈ 165k |
| Largest single feature file | **52 KB** | 38 KB |
| `index.md` alone | 49 KB ≈ 13k tokens | 48 KB |
| Features carrying `<gaps>` | **3** (6 gaps) | — |
| Total criteria | **550** | 519 |
| Declared statuses | `defined` 34, `tbd` **20**, `excluded` 7, `superseded` 2, **`in-progress` 1** | no `in-progress` |
| Declared priorities | must 13, should 25, could 19, wont 7 | unchanged |
| Decision records referenced | **19 distinct, 136 mentions** | 16 / 113 |
| Open questions referenced | **22 distinct, 44 mentions** | 19 / 40 |

Four rows carry the story.

**`excluded` and `superseded` are still not in the template's enum**, and **`in-progress` is now
in use** — the plan previously recorded zero uses of the one status the template does offer beyond
the obvious pair (P6). The template is now wrong about three of the five values in play.

**A `<gaps>` element has appeared that the plan did not anticipate**, in 3 files carrying 6 gaps.
It is a better answer than item 29's proposed `<needs-clarification>` and replaces it outright;
see item 29 and item 40.

**The feature count did not move; the depth did.** Still 64 features and still 13 must-haves,
against 519 → 550 criteria, +34 KB, `<gaps>` appearing and `in-progress` entering use. The corpus
is not growing outward, it is being specified more deeply — which is the growth that matters for
P5, since `analyze-prd` is handed all of it.

> **How these figures were taken, because the first attempt was wrong.** The sample directory had
> been refreshed by overwriting it without clearing it first, leaving one file from the previous
> copy that never existed in the PRD. Read naively it inflated the file count, the `tbd` tally,
> the must-have tally and the criteria total, and it was initially written up here as a P9
> instance.
>
> The contamination is bounded, and provably so: `index.md` was overwritten too, so it describes
> the current PRD, and a feature deleted upstream cannot appear in it. Every stale file is
> therefore unindexed. There are two unindexed files besides the leftover and both declare
> `superseded`, so **62 indexed + 2 pointers = 64 reconciles exactly** and the leftover is the
> only one. The figures above exclude it.
>
> The lesson generalises past this corpus and is the reason it is written down: **a measurement
> taken by globbing a directory inherits every defect of how that directory was populated.** It is
> also what the toolchain does at every step.

**The corpus is growing faster than the plan is shrinking it.** 165k → 174k tokens in a fortnight
makes item 18 more urgent, not less: `analyze-prd` is handed the whole of it, on Haiku.

---

## 3. Findings

### 3.1 Correctness

**P1 — MoSCoW priority is extracted, then discarded. Won't-have features are built.**
*Verification: static, exhaustive.*
`breakdown-analyze-prd` reads the priority attribute and writes `features[].priority` into
`analysis.json`. No skill downstream of that ever reads it. `breakdown-plan-layers` does not
mention priority at all; in `breakdown-generate-tasks` and every `/execute` skill, the only
`priority` is the integer described in P3. Consequences, in order of severity:

1. Won't-have features are broken down into tasks and implemented.
2. There is no way to build an MVP — a could-have's backend precedes a must-have's frontend,
   because layer order is the only order.
3. `/execute` cannot report what tier it is building, because the tasks do not carry one.

In corpus terms: 7 features the product owner explicitly rejected would be built, and the 13
must-haves would be interleaved with 44 others.

> **Runtime confirmation still owed.** The static result is unambiguous — the consumer does not
> exist — but the user asked for a test, and a passing static grep is not a run. See item 21.

**P2 — `<acceptance-criteria>` has no consumer on the PRD path.**
*Verification: static, exhaustive.*
Across the whole toolchain, `acceptance-criteria` appears in exactly three kinds of place: the
`/prd` and `/crd` templates that *write* it; the CRD branch of `breakdown/SKILL.md`, which
reads it; and two **XML comments** — `<!-- Include feature description, acceptance criteria -->`
— in `task-format-spec.md` and `breakdown-generate-tasks`. A comment inside a template is not a
consumer. On the PRD path the criteria are never read, so `<test-requirements>` in every
generated task are invented from a summary rather than derived from the criteria that already
exist. The CRD path does this correctly, which makes the gap an inconsistency as well as a loss.

**P4 — `<notes>` has no consumer anywhere.**
*Verification: static, exhaustive.*
Zero reads. Meanwhile `breakdown-analyze-prd` is instructed to **infer** data models and
relationships from feature descriptions. In the corpus, 28 of the 34 defined features state
their data model and their dependencies explicitly in `<notes>` — entity names, field lists,
relationship semantics, and warnings about modelling traps. The toolchain re-derives, by
inference on a small model, what the document already says.

**P5 — The first step of `/breakdown` does not fit in its model's context.**
*Verification: measured.*
`breakdown/SKILL.md` Phase 2 says: *"Invoke the `breakdown-analyze-prd` skill with the full PRD
content."* For this corpus that is **~174k tokens** and rising, sent in one prompt to a skill declaring
`model: claude-haiku-4-5` (200k window). It nominally fits and practically cannot work: it
leaves ~35k for a structured extraction of 64 features, against an explicit instruction not to
"truncate or summarize features". There is no chunking, no per-feature pass, and no size check.
This is graded **Blocking** for any PRD of realistic size — it is the first thing `/breakdown`
does.

**P19 — On the PRD path, ambiguity has no channel — and the design actively suppresses it.**
*Verification: static, exhaustive. From `sdd-comparison.md` C3.*
Three facts that are individually defensible and jointly produce invention:

- `breakdown-analyze-prd` is *instructed* to infer — data models "inferred from feature
  descriptions", endpoints inferred, components inferred, under the guidance *"Infer carefully:
  data models and APIs should be reasonable inferences, not guesses."*
- `review-criteria.md` makes `TBD`, `TODO`, `[to be determined]`, `appropriate`, `suitable`,
  `as needed` and *"necessary (without specifics)"* **critical** failures. One critical issue
  fails the batch and forces regeneration.
- Grepping `breakdown/SKILL.md` and `execute/SKILL.md` for user-confirmation points returns
  **nothing**. Neither skill asks a human anything, by design — `/execute` is the unattended
  overnight case.

So the toolchain requires inference, forbids the marking of it, and provides nowhere to escalate.
The only output satisfying all three is confident invention — and a reviewer reading a task file
whose entire design goal is self-containment cannot distinguish an invented field name from a
specified one. The retry loop makes it worse rather than better: attempt two runs with the
reviewer's complaint attached, under more pressure to *sound* specific than attempt one.

**One channel does exist, on the other path, and nothing reads it.**
`<confidence>high|medium|low</confidence>` is a **required** field of the CRD format, and
`crd-impact-analysis` ties it directly to ambiguity: *"Ambiguous matches | List all possibilities,
note medium confidence"* and *"Incomplete context | Note low confidence, suggest investigation"*.
No skill consumes it. So the precise claim is not that the toolchain cannot express uncertainty —
it is that it expresses it on one path, at whole-analysis granularity, to no reader. That is the
producer-without-a-reader shape of P1, P2 and P4, and the same PRD/CRD asymmetry P2 records for
acceptance criteria. Item 29 should extend that vocabulary rather than invent a second one.

This is P2's mechanism seen from the other end. P2 says the criteria never arrive; P19 says that
when they do not, nothing is allowed to say so. Item 15 refuses `tbd` *features*, which is the
same instinct applied at the wrong granularity — a `defined` feature can still have one
undefined field.

**P20 — Nothing reconciles the task set against the PRD.**
*Verification: static, exhaustive. From `sdd-comparison.md` C4.*
`breakdown-review-tasks` reviews each task **in isolation** — completeness, self-containment,
interface contracts, requirement specificity, test requirements, verification steps, file scope.
Its declared `## Input` is two things: a path to the generated task files, and the layer name. It
never receives the PRD, the feature files or `analysis.json`, so it **cannot** check coverage
rather than merely omitting to — which makes item 30 a new consumer, not a new criterion.
Two questions are asked nowhere: *is every must-have feature covered by at least one task?* and
*does any task implement something the PRD did not ask for?* With P1 unfixed the second is not
hypothetical, since won't-have features are built.

This is P9 one level up. P9 is that nothing reconciles the index against the feature directory;
P20 is that nothing reconciles the task set against either. Same absent check, later boundary,
and the later one is the expensive one — it is discovered after `/execute` has run.

### 3.2 Consistency

**P6 — The `<status>` enum cannot express what real use needs.**
*Verification: measured.*
Template allows `defined|tbd|in-progress`. The corpus uses **five** values — `defined` 34, `tbd`
20, `excluded` 7, `superseded` 2 and `in-progress` 1 — of which **two are undefined by the
template**.

*Corrected 2026-08-25 (R1).* This finding previously read *"uses `in-progress` zero times"* and
concluded that the one value the template offers beyond the obvious pair is unused. The §2
re-measurement recorded `in-progress` entering use and did not propagate here. The finding survives
the correction and is narrower: the template is missing two values in active use, rather than
missing two and over-providing one.

**P7 — `<status>` has no definitions, and nothing checks it.**
*Verification: measured — see item 3.*
Three enum values, no statement of what any of them means, no derivation, no guard. A status is
whatever was true when the file was written, and nothing notices when that stops being true.

**P8 — Priority is stored twice.**
*Verification: measured.*
`priority=` on the index entry, and `<priority>` in the feature file. Across the 62 shared
entries the two agree — but the file set does not: 64 files, 62 entries. The two `superseded`
files still declare `should-have` for a feature that no longer exists in the plan.

**P13 — Excluded features carry an undocumented `<rationale>` element.**
*Verification: measured — present in exactly the 7 `excluded` files and nowhere else.*
The corpus needed somewhere to record *why* something was rejected and invented a slot for it.
It is a good idea that the template should adopt, not an error.

**P14 — Excluded and superseded features keep a stale priority.**
A won't-have that carries `should-have`, or a merged-away feature that still claims a tier, is
a contradiction the schema permits.

### 3.3 Structural

**P3 — `priority` means two unrelated things.**
On a feature it is MoSCoW. On a task it is *"Execution order within layer (1 = first)"*, an
integer 1–99 (`task-format-spec.md` line 24), also used as a merge-queue ordinal. **Any fix that
"carries priority onto the task" must not use the element name `priority`** — it is taken, by a
field `/execute` depends on for merge sequencing. This is the single most likely way to
implement items 14–16 wrongly.

**P9 — Nothing reconciles the index against the feature directory.**
*Verification: static. Still a predicted failure, not an observed one — see the retraction below.*
Orphans, dangling links and priority mismatches are all silently possible. The corpus's two
unindexed files are legitimate — P6's `superseded` convention — so the check must *understand*
that convention rather than flag every orphan.

> **Retracted, and left visible on purpose.** A third unindexed file was written up here twice:
> first as a must-have silently dropped from the index, then as a rename residue. It was neither.
> The sample directory had been refreshed by overwriting without clearing, and the file was a
> leftover from the previous copy that never existed in the PRD (§2). **P9 has no live instance.**
>
> The episode is worth keeping because the error was not in the measurement but in the inference
> from it, twice over — a file present on disk was read as a fact about the document rather than
> as a fact about how the directory came to be. That is the same mistake the toolchain makes
> structurally: every step globs a directory and trusts what it finds.

**Two things the investigation established that do survive.** The only discriminator that works
between a legitimate orphan and a defective one is the **declared `<status>`**: a rule based on
whether anything still references the file separates nothing, because **both `superseded` pointers
have zero inbound references** — measured. And that same measurement shows both have reached the
exit condition they state for themselves — *"Safe to delete once nothing links here"*, and nothing
links there — which nothing evaluates. Item 6 should report a `superseded` pointer whose references
have all gone, rather than leaving a convention with an exit nobody checks.

**P10 — `what-next.md` is prose markdown where the spec says XML.**
*(This is assessment finding F3/F10; carried forward as item 12.)* The divergence produced a
**better** artefact — the prose version carries task-generation order, spikes, infrastructure,
data-model work, UX gaps and a risk table, none of which the XML template has a slot for. The
skill's own note on this is the right diagnosis: its "next steps" are all *post-PRD activities*,
while the template assumes *authoring gaps*. Both are real and they are not the same list.

**P11 — `index.md` has grown sections the template does not define.**
The corpus's index carries a large `<architecture>` block (data model, hierarchy, relationships)
and cross-references documents outside the PRD directory — ADRs and an open-questions register.
The template defines neither, and neither has a reader (P17). The block was not authored against
a spec; it was invented mid-invocation when the author needed somewhere to constrain
architecture and found no slot. That makes it the third instance of the same pattern, alongside
`<rationale>` (P13) and prose phasing (P12): **where the template is silent, the model invents
structure, and the invention is usually right.** Treat these as requirements discovered by use,
not as deviations to be corrected.

**P17 — The greenfield path has no architecture channel, in either direction.**
*Verification: static, exhaustive.* This is the finding P11 was a symptom of.

*Nothing accepts architecture as an input.* The layer graph in `layer-definitions.md` is a
fixed, hardcoded five-tier DAG — setup → foundation → backend → frontend → integration — with no
override, and nothing in a PRD can influence it. `breakdown-analyze-prd` is explicitly
instructed **"Do NOT ... include your own opinions about architecture"**, and infers data models,
endpoints and components instead. So `/breakdown`'s pre-baked tiering is the entire answer, and
an authored architectural constraint has nowhere to enter.

*Nothing records architecture as an output either.* `/execute` dispatches
`project-context-finalizer` only after `test -f {project_path}/PROJECT.md` — **if it exists**.
A greenfield project has no PROJECT.md, so the finalizer never runs, so one is never created.
A greenfield project can therefore run the entire pipeline and end with no architecture record
at all; the first `/crd` against it then pays for a full `crd-investigate` to rediscover
architecture the PRD had already stated.

*The brownfield path, by contrast, is well served.* PROJECT.md carries `## Architecture` — tech
stack, component structure, key patterns — plus machine-readable schema and API registries;
`crd-investigate` produces it, and `/breakdown` loads it for CRD input. The asymmetry is the
finding: **the toolchain has an architecture artefact, and greenfield is the only path that
cannot reach it.** Note the direction of flow differs — PROJECT.md is *descriptive*, discovered
from code, whereas a PRD-time constraint is *prescriptive*. Same shape, opposite direction.

**P12 — Intra-feature phasing exists in prose, with no slot for it.**
Seven features already split themselves into "phase 1 / phase 2" in prose, with real semantics:
a phase 2 that depends on external access, criteria mapped to specific phases, and an open
question about whether a phase 2 should exist at all. `/breakdown` cannot see any of it, so it
would build both phases at once or neither.

**P15 — Tasks have no link back to the feature they came from.**
`<meta>` carries id, name, layer, priority, estimated-files. Nothing identifies the source
feature, so coverage cannot be reported, criteria cannot be traced, and a failed task cannot be
attributed to a requirement.

**P16 — `/prd`'s guards are prose, in a repository that has learned better.**
Items 4.6, 4.12, 4.13, 4.14 and 4.17 all converted prose instructions into programs, each time
because the prose guard was documented and ignored. `/prd` is now the largest remaining
concentration of prose guards: the pre-write existence check, the consistency checks, and the
status marker are all instructions to a model rather than exit codes.

**P18 — The toolchain's architectural opinions are vendored into the plugin, and no project can
override them.**
*Verification: static, exhaustive. From `sdd-comparison.md` C2.* This is P17 generalised: P17 is
that architecture has no channel *in*; P18 is that architecture is only one of five things with
that problem.

| Opinion | Where it lives | Overridable? |
|---|---|---|
| Five layers, `setup → foundation → backend → frontend → integration` | `layer-definitions.md` | No |
| TDD is mandatory | enforced by `task-format-spec.md` + `review-criteria.md`; only *described* in `tdd-workflow.md` | No |
| Max 3 files per task | `task-format-spec.md` | No |
| Templates are `python` / `go` / `tanstack` | `breakdown-analyze-prd/SKILL.md` (detection) and `layer0-templates.md` | No |
| Verification is runnable shell commands | task format | No |

**Two of those rows resist a single pointer, and that matters for item 28.** TDD is not enforced
where it is described: `tdd-workflow.md` carries the Red/Green/Refactor procedure and mandates
nothing, while the requirement is imposed upstream by `task-format-spec.md`, which marks
`<test-requirements>` a required section, and by `review-criteria.md`, which makes it critical
twice — once in criterion 1, which names the section among the required elements, and again in
criterion 5, which sets its quality bar. The template enum likewise lives in the detection table
in `breakdown-analyze-prd/SKILL.md` and in `layer0-templates.md`; `layer-definitions.md` only
names one of the three, in a commands table. **An opinion enforced in more places than it is
documented is harder to make overridable, not easier.**

Searching `skills/`, `agents/` and `commands/` for *constitution*, *steering*, *coding standard*
or *conventions* returns two files — `crd-investigate/SKILL.md` and `crd-investigator.md` — and
both only **infer** conventions from existing code. Nothing anywhere lets a project *declare*
them. Every one of the five opinions is defensible; none is universal; and disagreeing with any
of them currently means forking the plugin.

The comparison document grades this the largest gap against the field, because both comparable
tools have solved it — spec-kit with `memory/constitution.md` enforced as gates, Kiro with
steering files. It is also where Böckeler's model-driven-development parallel lands: her charge
is that LLM-based SDD risks combining MDD's inflexibility with the LLM's non-determinism, and a
hardcoded five-tier DAG that encodes one architecture — a CRUD web application built from a
template — as though it were the shape of software is exactly the inflexibility she means. A CLI
tool, a library, a data pipeline or anything event-driven does not decompose that way. The
finding is not that the layers are wrong. It is that they are not the project's to change.

**P21 — There is no path for a change too small to be worth the ceremony.**
*Verification: static. From `sdd-comparison.md` C9.*
Böckeler's scale critique — Kiro bloating a bug fix with user stories, spec-kit over-engineering
moderate features — applies here with the greenfield path being the worse of the two: eight
interview phases, five layers, batched generate → review → retry at up to three attempts per
batch of five.

`/crd` is the intended concession and the instinct is right — CRDs skip Layer 0, scope generation
from `<impact-analysis>`, and typically produce two or three layers. But a three-file change
still costs a `PROJECT.md` investigation or incremental update, eight CRD phases, an
impact-analysis sub-skill, layer planning, generation, review, and the full
worktree/verify/merge machinery. The impact analysis computes the size of the change and nothing
consumes that number as a routing decision.

**P22 — Self-containment makes the task set harder to review than the PRD it came from.**
*Verification: static, with one projection labelled as such. From `sdd-comparison.md` C10, which
the first fold omitted.*
Duplication between task files is not incidental here, it is **mandated**: every task inlines its
PRD excerpt, tech stack, project structure, and complete interface contracts with imports for
every dependency. `review-criteria.md` makes the alternative a critical failure — *"As described
in the PRD" → Copy relevant PRD text inline*.

That is correct for the consumer and expensive for the human. Self-containment is what makes a
small model a viable implementer, and **item 17 deliberately increases it**, carrying criteria and
data models in as well. The cost lands on the review pass: the task set grows toward exceeding the
PRD in volume while containing nothing the PRD did not already have, in a format chosen for
machines — XML, spread across 18 to 48 files, with no rendered view of the set.

Two clarifications, because this is easy to misread as an argument against self-containment. It is
not: the mandate is right, and P22 is the price of a correct decision rather than evidence against
it. And the volume claim is a **projection** from §2's corpus measurements, not a measurement of a
generated task set — no PRD of this size has been broken down, because P5 stops it first. Item 21
is the earliest point at which it could be measured.

**P23 — The criterion format cannot express most of what a requirement needs to say.**
*Verification: measured.*
All 550 criteria in the corpus are Given/When/Then — still all of them, after a fortnight of
editing that added 33 more. GWT is a **scenario** format: it renders one
event and its outcome. Mapped onto the six EARS patterns, four of them have no natural rendering
in it at all:

| EARS pattern | Template | Expressible as GWT? | In the corpus |
|---|---|---|---|
| Event-driven | `When <trigger>, the system shall <response>` | naturally | essentially all 550 |
| Unwanted behaviour | `If <trigger>, then the system shall <response>` | awkwardly | 85 (15.5%) |
| State-driven | `While <precondition>, the system shall <response>` | awkwardly | rare |
| Ubiquitous | `The system shall <response>` | no natural form | — |
| Optional feature | `Where <feature> exists, the system shall <response>` | no natural form | **0** |
| Complex | combination of the above | no | — |

**84.6% of criteria touch no failure path** — no failure, invalid state, conflict, expiry,
refusal or absence anywhere in the block. And **8 of the 34 features labelled `defined` have none
at all.**

*Re-measured 2026-08-24.* The share was 15.4% at 519 criteria and is 15.5% at 550 — the ratio did
not move while a tenth of the corpus was rewritten, which is stronger evidence than the original
snapshot. The count of `defined` features with no edge case rose from 7 to 8.

The last figure is the one that matters, because §4.2 defines `defined` as *"criteria cover the
edge cases"*. Those seven do not satisfy the definition they are labelled under. **Item 3's
derivation did not catch it**: it keys on the structured-notes marker, so it validates the notes
half of the definition and never looks at the criteria. Its 63/64 agreement means the rule and
the labels agree — which is not evidence that either is right.

*Method, stated so the numbers are not over-read.* Failure paths were counted by keyword search
across the whole criterion block. It over-counts a criterion that mentions an error in passing
and under-counts one that describes a failure without any of the keywords. Read 15.4% as an order
of magnitude. The zero for optional-feature is structural rather than statistical: the shape has
no GWT rendering, so its absence is a property of the format, not of the authors.

**P24 — The PRD cites three artefact classes the toolchain cannot see.**
*Verification: measured.*

| Artefact class | Distinct items | Mentions | Corpus files citing one |
|---|---|---|---|
| Architecture decision records | **19** | **136** | 31 of 66 |
| Open questions register | **22** | **44** | — |
| Product principles | — | **10** | — |

**190 references, none validated and none followed** — up from 157 a fortnight earlier, which is
the point: this class of reference is the fastest-growing thing in the corpus. *Figures re-taken
2026-08-25 (A2); the denominator is 64 feature files plus `index.md` and `what-next.md`.* `analyze-prd` receives PRD XML and nothing
else, so a feature whose scope is settled by a decision record is broken down without it. Nothing
detects a reference to a record that does not exist, one that has been superseded, or one that
contradicts the feature citing it.

This is P4's shape at document scale — content the PRD depends on, with no reader — and it is
larger, because a dangling reference is wrong rather than merely unread.

**P35 — `<rules>` has the right bones and three CRUD-shaped leaves.**
*Verification: measured against five architecture patterns — monolithic SPA, event-driven,
microservices, CLI, mobile — in §8.*

Item 28 frees the layer graph from the plugin. Writing `<rules>` for five patterns shows it then
**re-vendors the same class of opinion one level down**, in three places:

- **Registries are fixed at two.** Item 25 has `architecture.md` share PROJECT.md's schema *"plus
  its schema registry"* — an **API Registry** (method, path, request, response) and a **Schema
  Registry** (model, table, fields). That is REST plus relational. Four of the five patterns need
  a different primary contract: an **event registry**, a **service registry**, a **command
  registry** (subcommands, flags, exit codes, output format), a **screen registry**.
- **One runner, one test policy.** `<testing policy="tdd" runner="pytest"/>` cannot express that
  contracts need compatibility tests, consumers need consumer-driven contracts and projections
  need replay tests — **nor that a monolithic SPA has two toolchains**, pytest behind and vitest
  in front. The default case breaks it, which is the strongest evidence available that it is
  wrong.
- **One task limit.** Three files is right for a UI change and wrong for adding an event type,
  where schema, producer, consumer, projection and test are one change.

And one structural limit rather than a leaf: **`<layers>` assumes a single graph for the whole
project.** Microservices and multi-platform mobile need the same graph *instantiated per unit*,
and flattening them is not merely inconvenient — it destroys the independent deployability that
motivated the architecture, by ordering *all* services' data layers before *any* service's API.

`<banned>` and `<scaffold>` generalise across all five without change, and the degenerate CLI case
needs no special handling because item 31 collapses a single-layer plan on its own. The bones are
right.

**P36 — The execution model assumes one repository, and says so nowhere until it fails.**
*Verification: static, exhaustive.* No file in `skills/`, `commands/` or `agents/` mentions
monorepo, multi-repo or submodules. `manifest.json` carries one `project_path`,
`execute-state.json` tracks one target, and the ledger derives completion from commits in that one
repository.

**The assumption is defensible; its lateness is not.** `create-worktree.sh` refuses a
subdirectory — *"The target must be the repository root, not a subdirectory of one"* — which is
correct, but it fires during batch execution, several phases after the point where the layout was
knowable. A project split repo-per-service gets a plan, a manifest and a task set before anything
objects.

*Not a git limitation.* A repo-per-service layout would create a worktree **per repository**,
which is ordinary. What is missing is a *target* model with dependencies — contracts must land in
one repository before consumers in another — and an explicit account of the window in which a
change spanning three repositories has merged into one of them. That window is a property the
architecture chose, not a defect to remove, which is why supporting it is a scope decision rather
than a fix.

**P37 — The ledger reports a merge and implies a build.**
*Verification: static.* `execute-verify` runs the task's **own declared** verification steps in
the worktree before merge, which is real and is more than the field does (S1). The ledger then
records the merge. In any project with a build pipeline, a task that merges green and breaks CI is
invisible: the ledger says done.

The claim to fix is small and the principle is the plan's own. S2 is *"state is derived from git,
never asserted"* — so the ledger should state **what it verified** rather than leave a reader to
assume the stronger thing. Running the project's pipeline is out of scope; implying it was run is
not.

**P38 — `execute-layer` maintains a file that is rebuilt from git on every write.**
*Verification: static, exhaustive. Found while implementing item 23a, 2026-08-25.*
`write-state.py` derives `execute-state.json` from the manifest and the ledger and rebuilds it
whole; `execute-layer` was written against the hand-maintained 2.0 file and still instructs four
writes into it and two reads out of it. The reads are the live half:

| Step | What it does | Consequence |
|---|---|---|
| 5d | Iterates `merge_queue` for `status == "ready"` | **Merges nothing.** Every entry is `merged` by construction — the list is derived from the ledger *after* the fact |
| 2 | Takes `completed` from the state file | Over-reports completion, which starts a task before its dependency landed. Step 3 forbids this four lines later |
| 4, 5a, 6 | Write `current_layer`, `current_batch`, per-layer counters | Fields absent from 3.0; erased rather than merged, since the script rebuilds rather than patches |

**The skill already contained the correct rule** — *"There is no queue to maintain in a file…
writing one by hand would make that untrue"* — added at some point without removing the blocks it
contradicts. That is the same shape as the plan's own nine (item 23): the fix was written and the
thing it replaced was left in place, so the document says both.

**And the regression suite had a check for exactly this that did not fire.** F21's mutation
pattern was an allowlist of seven field names, so `state["current_batch"] = batch_number` was
never in scope. A check scoped to the fields that were wrong last time cannot catch the next one.

**P34 — `/prd` does not know what project it is writing into.**
*Verification: static, exhaustive.* `commands/prd.md` mentions `PROJECT.md` **zero times**.

`/crd` opens with a context check: find `PROJECT.md`, compare `last-context-hash` against `HEAD`,
investigate or update before doing anything else. `/prd` has no equivalent. A greenfield PRD
authored inside a repository that already has a codebase, a `PROJECT.md`, and an established
architecture notices none of it, and proceeds to ask what the tech stack should be.

This is the P17 asymmetry seen from the authoring end rather than the breakdown end: the brownfield
path is context-aware by construction and the greenfield path is context-blind by construction,
and *greenfield* describes the document rather than the repository it lands in.

It matters more once item 28 exists, because then there are **project-scoped rules** to conflict
with. Two PRDs in one repository — which `/prd` explicitly supports, globbing `docs/prd/*/` and
offering to *"start a new one alongside it"* — could otherwise state two different layer graphs
and two different test policies for one codebase.

**P33 — Layer selection is derived on one path, hardcoded on the other, and wrong on both.**
*Verification: static, exhaustive.*

`/breakdown` Phase 4 selects layers like this:

- **PRD greenfield**: `[0-setup, 1-foundation, 2-backend, 3-frontend, 4-integration]` —
  **unconditional**. A PRD with no frontend still gets a frontend layer.
- **PRD brownfield**: the same list minus Layer 0. Also unconditional.
- **CRD**: derived from content — *"if `<affected-schemas>` has changes: include Layer 1; if
  `<affected-apis>`: Layer 2; if frontend files in `<affected-files>`: Layer 3"*.

So the CRD path already asks the question that matters — **does this change span tiers?** — and
answers it from what the change touches. The PRD path does not ask it at all.

**And the CRD derivation ends with a line that undoes it:** *"Always include Layer 4 (integration)
for wiring changes together."* A change confined to one tier is given a second tier
unconditionally, so the minimum possible plan is two layers, two batches, and two rounds of
generate → review → retry, for a change that might be one edit to one file. There is nothing to
integrate when only one tier moved.

This is P21's ceremony complaint with a located cause, and it is a better one than P21 had. The
cost is not that the workflow lacks a small path — it is that **the derivation which would have
produced one is overridden by a hardcoded line on one path and absent on the other.**

**P29 — `status` means three unrelated things, and two of the vocabularies overlap.**
*Verification: static, exhaustive.*

| Tag | Values | What it records |
|---|---|---|
| PRD feature `<status>` | `tbd`, `in-progress`, `defined`, `excluded`, `superseded` | definition completeness (§4.2) |
| CRD `<meta><status>` | `draft`, `ready`, `in-progress`, `complete`, `abandoned` | workflow position |
| PROJECT.md `<feature status=>` | `complete`, `partial`, `planned` | build completeness |

Three artefacts, one word, three meanings — and `in-progress` and `complete` appear in more than
one of them meaning different things. §4.2 already warns that *"`in-progress` reads as build
progress to every developer who sees it, and `/execute` has its own `in-progress` meaning exactly
that"*. The collision is not hypothetical or future: **it exists across the two paths today.**

A reader cannot tell which `status` they are looking at without knowing which file they are in, and
neither can a script. Any shared schema (item 44) has to settle this before anything else, because
every other shared element hangs off knowing what a feature's state is.

**P30 — The two paths define overlapping schemas independently, and neither cites the other.**
*Verification: static, exhaustive.*
`<criterion>` with `<given>/<when>/<then>` is defined twice — in `commands/prd.md` and in
`crd-format.md` — with no shared definition and no reference between them. So is priority, in two
different vocabularies. So is the notion of a feature: PRD features carry slugs, PROJECT.md
features carry `id` attributes, and nothing states whether they are the same namespace even though
PROJECT.md records a `prd-path` pointing at the document the other set lives in.

The PRD templates are inline in a **command file**; the CRD schema is a **reference file** under a
skill; the task schema is a third reference file. There is no shared core, so every change in this
plan to `<criterion>`, `<gaps>`, priority or traceability has to be made two or three times and
kept in step by hand. That is the condition item 22 exists to detect after the fact, present here
by construction.

**P31 — CRD requirements and acceptance criteria are unlinked, and the criteria carry no priority.**
*Verification: static.*
A CRD has `<requirements>` with `id` and `priority`, and a separate document-level
`<acceptance-criteria>` with its own `id` sequence. **Nothing connects the two.** Criterion 3 does
not say which requirement it verifies, and requirement 3 does not say which criteria discharge it,
so a CRD with five requirements and four criteria cannot be checked for coverage — the same defect
as P20, inside a single document.

The criteria also carry no priority, while the requirements do. Filtering a CRD by priority
therefore selects requirements and leaves every criterion in scope, which is the mirror image of
the PRD path's problem, where criteria are all that exist.

**P32 — The CRD path has no deferral mechanism and no resume.**
*Verification: static.*
`/crd` Phase 5 asks *"Should we define acceptance criteria for this now, or mark it for later?"* —
the same question `/prd` Phase 3 asks. On the PRD path "later" has somewhere to go: `what-next.md`,
and now `<gaps>`. **On the CRD path it has nowhere.** There is no `what-next` equivalent, no gaps
element, and no `tbd` state for a requirement, so a deferred criterion is simply absent and
indistinguishable from one nobody thought of.

`skills/crd/SKILL.md` also records that *"CRD workflow is stateless per invocation"* and that no
resume tracking is needed. `/prd` has `--resume` and an entire initialization phase built around
not overwriting an interview in progress (F3). A CRD interview that is interrupted is lost, and a
second `/crd` run on the same change writes over the first with no equivalent of `/prd`'s
pre-write existence check.

**P28 — One version where two are needed, and the one schema version there is, is wrong.**
*Verification: measured.*

The toolchain has a single version concept: `.claude-plugin/plugin.json` declares `2.0.0`, and
`build-manifest.py` stamps it into the manifest as `toolchain_version`. That conflates two
different questions — *what produced this artefact* and *how should this artefact be read*. A
patch release changes the stamp without changing any schema; a schema change need not bump the
plugin version at all. Item 24 proposes comparing recorded against running and refusing on a known
incompatibility, which cannot be decided from a provenance stamp.

**The pattern already exists, applied to exactly one artefact.** `execute-state.json` carries a
`schema_version`, separate from the plugin version, for precisely this reason — so the concept
does not need inventing, only generalising to the artefacts this plan rewrites.

**And that one schema version is already out of step with itself.**
`skills/execute/references/state-schema.md` says *"Current version: `2.0`"* and shows
`"schema_version": "2.0"` in both of its examples;
`skills/execute/scripts/write-state.py` writes `"schema_version": "3.0"`. The script is the
producer and the reference is the spec, so the spec is wrong — **P10's exact shape, in the one
place the toolchain versions a schema at all**, and it is live in the repository now.

Two things follow. A declared version that nothing tests drifts from what is written, which is the
argument for item 43 rather than for a stamp alone. And item 22's schema check is currently scoped
to PRD artefacts; the state file needs it too, or this recurs where it has already happened once.

**P27 — There is no rename operation, and a slug lives in five places.**
*Verification: measured — as cost and exposure, not as an observed failure. The rename that
prompted this finding was carried out correctly.*
Renaming a feature means changing: the filename, `<slug>` inside it, the index entry's `file=`
attribute, the index entry's own content, and **every inbound cross-reference in every other
feature**. A rename in the corpus touched **20 references across 8 files**, and every one of them
is right — the old slug appears nowhere, the new one resolves everywhere. The finding is not that
it went wrong. It is that nothing made it go right except care, and nothing would have said so
either way.

The corpus makes the exposure plain: **231 inter-feature reference edges** (P26), so a rename is a
multi-file refactor whose blast radius is bounded only by how popular the feature is — the
most-referenced one carries 19 inbound consumers. There is no command for it, no check after it,
and no record that it happened: a renamed feature's history is a new file with no stated
relationship to the old one, and its accumulated criteria, gaps and decisions are re-anchored
silently.

This also makes rename a **miniature of item 41's migration**: a mechanical transformation across
many files, with preconditions, an invariant (no reference to the old slug survives), and a
postcondition nobody currently asserts. Whatever machinery item 41 builds should be able to do
this, and a rename is the cheapest possible test of it.

**P26 — Nothing checks that a feature discharges what other features expect of it.**
*Verification: measured.*
Features reference each other constantly: **231 inter-feature reference edges** across the corpus,
with 51 of 64 features referenced by at least one other and the most-referenced carrying **19
inbound consumers**. **93 of those edges (40%) are one-way** — a feature names another that never
names it back.

A one-way edge is not a defect on its own; plenty are "see also". But it is exactly the population
a contract review has to read, and nothing reads it. Two failure shapes recur, both silent because
neither file is wrong on its own terms:

- **A consumer reading an interface that was never specified** — one feature describes reading
  another's query; the owning feature has never mentioned that query exists.
- **An orchestrator invoking a capability that never said it was invocable** — one feature
  schedules another and evaluates what it emits; the scheduled feature says nothing about running
  unattended.

This is P20's shape one level earlier and one level cheaper. P20 is that nothing reconciles tasks
against the PRD; P26 is that nothing reconciles the PRD against itself, and a contract gap found
here costs a paragraph rather than a rebuilt task.

**P25 — There is no design step, and no way to say which requirements would need one.**
*Verification: static, corroborated by the corpus author.*
The pipeline is requirements → tasks with nothing in between. Every comparable tool has three
phases with a design artefact and an approval gate between each (see `sdd-comparison.md`).

The evidence that this is a real gap rather than a theoretical one is the corpus itself. The
`<architecture>` block in the index (P11) and the data-model blocks in feature notes were produced
by the author **forcing architecture conversations the workflow does not provide**, and the 16
decision records were created the same way and then kept outside the PRD because nothing linked
them to `/prd`. The compensation worked. That it was necessary, and that its output had nowhere
schema-defined to land, is the finding.

There is also no notion of **architectural significance** — the established idea that a subset of
requirements measurably affects the architecture and merits separate treatment. Without it a
design step cannot be afforded: it would run across all 64 features rather than the handful that
warrant it. Item 35 is what makes item 38 affordable.

### 3.4 From the live crossings

**Everything above was found by reading. These five were found by running**, across three live
crossings of the `/breakdown` → `/execute` boundary (item 59) on 2026-08-27 and 2026-08-28. None
of them was visible to the 112 regression checks, and the reason is uniform: four are internal
contradictions in prose or missing guards, and the fifth is a schema gap that only a task spanning
two features can expose.

**P39 — `plan-layers` forbade the derivation it performs.**
Its *Do NOT* list ended with *"Skip layers (every project needs all 4 layers)"* while its own
opening section says *"First, decide which layers exist at all. A tier with no work in it is not a
tier."* Item 31 derived the layer set from content and left the instruction forbidding the
derivation standing eight sections below. The third live run followed the derivation, dropped
`3-frontend` correctly, and **reported the contradiction as a defect in its own instructions.**
This is the repository's most repeated shape — a fix applied at the site of discovery rather than
at the level of the problem — arriving in the one place that had documented it.

**P40 — `task-format-spec.md` required a layer its own constraints could not express.**
`id` was pinned to `L[1-4]-[0-9]{3}` and `layer` to an enum of four names, neither admitting
`0-setup` — while three fields ten lines below read *"Required except in Layer 0"*. Every Layer 0
task the toolchain has ever generated was invalid under its own schema. Item 28 makes the enum
wrong for a second reason: a project declaring its own `<layers>` graph, instantiated per service,
cannot be described by four fixed names.

**P41 — `/execute` may rewrite the acceptance criteria it is being judged against.**
The third live run met a Layer 0 task whose `<verification>` block was unsatisfiable — one step
forbade a substring another requirement mandated. Its diagnosis was correct and its fix was
reasonable, and **it edited the task file and carried on.** Nothing in the toolchain forbids that,
nothing records it, and the ledger records commits rather than task edits. `execute-verify` is
"independent" of the *implementing agent* and not of the orchestrator that can edit what it
verifies against. A `14/14` obtained this way is weaker evidence than it looks, and it is item
59's own rule turned on the toolchain: *a runtime test whose crossing is made to pass by adjusting
the test has measured nothing.*

**P42 — the generator does not know the execution model.**
The same task asserted `pathlib.Path('.git').is_dir()`. Inside a git worktree `.git` is a *file*,
so the assertion is false for the execution model the plugin itself uses. It was invented by
`breakdown-generate-tasks` rather than shipped in `layer0-templates.md`: nothing tells the
generator where its verification commands will run. Every environment-shaped assertion it writes
is a guess.

**P43 — `<source-feature>` is single-valued, and an integration task spans features.**
Item 16 gives a task one `<source-feature>`. A task that legitimately covers criteria from more
than one feature has no way to say whose criterion it carries, and **three live runs produced three
different workarounds**: the first invented `feature#id` and applied it in one of the two places,
so the halves of a task stopped referring to each other; the second split the task and said why;
the third narrowed the attribution and said nothing. The third is the worst of the three because
it is silent — `L4-002` walked `save-link`, `tag-links` and `list-links` criterion 2, and declared
`tag-links` alone.

**Nothing catches it**, because item 30's coverage check passes: the unattributed criteria are
covered by other tasks. The cost is that every downstream consumer — the coverage report, the
scope cross-check, `tasks-summary.md`, the gate — believes the task belongs to one feature, so
removing that feature from scope would silently take the only end-to-end assertion of the other
two with it.

### 3.5 From implementing the phase

**One finding, and its provenance is the point.** P39–P43 were found by running the toolchain.
This one was found by *building* item 63 — reading `/execute` closely enough to wire a guard into
it — which is a third way of finding things and worth keeping separate from the other two.

**P44 — `/execute` iterates a layer list that stopped being true three items ago.**
Step 6 loops over a hardcoded `["0-setup", "1-foundation", "2-backend", "3-frontend",
"4-integration"]`, and Critical Rule 1 still reads *"Never skip layers: Execute in order
(0→1→2→3→4)"*. Item 31 made the layer set derived from content, item 61 removed the instruction
that forbade the derivation, item 62 made the task schema admit any layer id, and item 28 lets a
project declare its own `<layers>` graph instantiated per service. **The producer derives; the
consumer still recites.**

The failure is silent and total rather than partial. A project whose layers are named anything
else — `2-service-billing`, or simply a set that drops `3-frontend`, which the third live run
correctly produced — gets a run that iterates five names, finds no tasks under any of them, skips
every layer, and **reports a completed run of zero tasks**. Nothing fails, because nothing runs.

**This is P33 with the arrow reversed.** P33 found the layer set hardcoded in the *producer* and
derived on the CRD path; item 31 fixed the producer on both. Neither P33 nor item 31 mentions
`/execute`, because the plan was reading `/breakdown` at the time — which is exactly how a
consumer is left reciting a list the producer has stopped writing.

### 3.6 From the fourth crossing

**The first crossing after Phase 8, and the first that item 63's guard was live for.** It ran
clean — five grader assertions held, `10/10` tasks verified from git, 44 tests passing by hand,
no worktrees left, `PROJECT.md` valid — and items 61, 64, 65 and 66 were all exercised doing what
they were built for. The one finding is in the guard.

**P45 — the task-file guard protects a dispatch, and a run is not a dispatch.**
`/execute` stopped on `L4-001`, **the task file was edited**, and the run resumed. Item 63's
`record` runs on every invocation including a resume, so the resume snapshotted the *edited* file
as its new baseline and `verify` has said `UNCHANGED 10 task file(s)` ever since.
`task-edits.jsonl` was never written.

That behaviour was deliberate — *"a `--resume` re-records too, so an operator who fixed a task
between runs is not fighting the previous run's snapshot"* — and the assumption inside it is the
defect: **the distinction between *the operator* and *the run* collapses when the same agent is
both.** Stop, edit, resume is one continuous act by one participant, and it is the path an
unsatisfiable task makes most likely.

**The second half is worse than the first.** `record` deletes the previous snapshot before taking
the new one, so the file as originally dispatched is not merely unreported — it is
unrecoverable. Item 63's third requirement was *"whatever the policy, the edit must be visible
afterwards, or the next `14/14` is unauditable in the same way"*, and the resume path erases the
only artefact that could have shown it.

**This is P41 one level up**, and the shape is worth naming: a guard that measures the right thing
at the wrong boundary reports honestly and proves nothing.

---

## 4. Three design decisions that resolve most of the above

### 4.1 Ownership rule: the index owns *planning*, the file owns *definition*

> **Priority lives in `index.md`. Status lives in the feature file. Neither is duplicated.**

This settles P8 by choosing, not by synchronising. The reasoning is not aesthetic:

- Priority is a **portfolio decision** — a feature's place relative to others. It belongs where
  the others are visible. Re-prioritising is then one edit to one file, not 64.
- Status is a **property of the file's own content** — how completely this feature is specified.
  It is derivable from the file and from nothing else (item 3), which is only true if it lives
  there.
- `analyze-prd` already reads the index entry, so the priority is on the path it already walks.
- It fixes P14 for free: removing a superseded feature from the index removes its priority,
  because the priority was never in the file. A stale tier becomes unrepresentable.

**Change:** delete `<priority>` from the feature template. Keep `priority=` on the index entry.

**One exception, stated so it does not look like a violation.** Item 34 puts a second priority on
each *criterion*. That is a planning judgement, which the rule above would place in the index —
but the index does not know criteria exist, and cannot without duplicating them. So criterion
priority lives with the criterion. The rule holds at the granularity it was written for: **feature
-level planning belongs to the index; anything finer belongs where the thing itself is.**

### 4.2 Status records definition completeness, not build progress

The five values, defined — and the definitions go **in the template**, where the writer sees them:

| Status | Meaning | Required content |
|---|---|---|
| `tbd` | No criteria written. A name and an intent. | — |
| `in-progress` | Criteria exist; the feature is deliberately being held short of `defined`. | ≥1 criterion |
| `defined` | Criteria cover the edge cases — *measured* as EARS pattern coverage, not asserted; notes carry the data model; intent is stated. | `<user-story>` + ≥1 `unwanted-behaviour` criterion + `<data-model>` |
| `excluded` | Won't-have. Deliberately not built. | `<rationale>` (adopts P13) |
| `superseded` | Merged into another feature; file retained as a pointer. | successor link; **removed from `index.md`** |

**The tag records how completely the feature is *defined*, not how far it is *built*.** This must
be said explicitly, because `in-progress` reads as build progress to every developer who sees
it, and because `/execute` has its own `in-progress` meaning exactly that.

**`defined` now has a mechanical test, and the corpus supplied it — but it runs in one direction
only.** A `defined` feature **must not** carry a `<gap kind="specification">`; it may carry gaps of
every other kind, because *being specified* and *being unblocked* are different things.

The converse is deliberately **not** asserted. Absence of a specification gap does not make a
feature `defined`, because an author may hold something at `in-progress` for reasons the file
cannot express — a review not yet done, a boundary they expect to move, a judgement that the
criteria read thinner than they look. `in-progress` stays a **declared** state, not a derived one.

What that buys is a guard with no false positives: *a feature cannot claim to be fully specified
while declaring that its specification is incomplete.* That contradiction is checkable and worth
stopping. Everything softer than it stays with the author.

**"Cover the edge cases" needed a definition, and P23 is what happens without one.** Eight
features carry `defined` while having no criterion that mentions a failure at all. Item 33's
`pattern` attribute makes the test mechanical: a feature whose criteria are entirely
`event-driven` has not covered its edge cases, whatever its notes say. That is a deterministic
attribute count, not a judgement, and it is the half of this definition item 3 has never checked.

Two consequences worth stating plainly:

- `excluded` and `superseded` are **definition states, not priorities**. `excluded` pairs with
  `priority="wont-have"` in the index; `superseded` has no index entry at all.
- **`in-progress` has entered use, exactly once, and that one use argues for keeping it declared.**
  The single feature carrying it derives a *ceiling* of `defined` — its content would support the
  higher label — and the author has held it lower anyway. That is precisely the case §4.2 says a
  checker must not overturn, and it is now an observation rather than a hypothesis. Under these
  definitions several features still labelled `tbd` are `in-progress`; item 4's migration
  reclassifies them.

### 4.3 Structure earns its place by what a machine must *do* with the content

The review's R16 is that this plan responds to every gap by adding a slot to a schema, and never
states why schema-tightening beats prose-plus-validation — while collecting four pieces of evidence
pointing the other way (P10–P13), each recording that prose the model invented was *better* than
the template it replaced.

**The plan has been applying a test all along and never wrote it down.** Written down, it is:

| If… | Then | Because |
|---|---|---|
| A machine must **locate** it | an identifier or attribute, prose body | finding it is all the reader needs |
| A machine must **understand** it | an element | the reader consumes the content, not the position |
| Only a human reads it | prose, marked **unread by design** | structure would be cost with no consumer |

**Two things this settles that were being argued as taste.**

*Why item 33 is not a contradiction.* EARS is constrained natural language — a **sentence** with an
`id`, a `pattern` and a `priority`. The plan's largest schema item therefore chose
prose-plus-convention, because a machine must *locate* a criterion and know its pattern and tier,
while only a human needs to *understand* what it says. That is the rule, not an exception to it.

*Why more schema would not have prevented the plan's own central finding.* `<acceptance-criteria>`
was well-formed XML throughout and still had no reader (P2). **P2 was a missing consumer, not a
malformed producer**, and no amount of structure catches that. This is the argument for the third
decision below.

**Consumer-side validation is primary; producer-side is early warning.** Item 22 refuses a
malformed artefact where it is written, which is worth having because a defect is cheapest at its
source. But the check that *matters* is the one item 23 states — every element has a named reader,
every reader a named producer — and it lives at the consumer. A producer-side schema can only
assert that a document is well-formed; it cannot assert that anybody needs it.

**And the authoring cost is measured, not assumed** (R17). The plan's evidence base is one author's
behaviour and its output is that author's new workflow: a ninth `/prd` phase, a replaced criterion
format, a renamed status tag, a second priority vocabulary, two project-root artefacts and 550
re-annotated criteria. Item 21 gains one line for it. A workflow nobody can bear to use is a
failure mode this document has no other way to detect.

---

## 5. Remediation items

### A. Schema — `/prd` templates

**1. Feature template: remove `<priority>`, extend `<status>`, add the missing slots.**

```xml
<feature>
  <meta>
    <name>{{Feature Name}}</name>
    <slug>{{feature-slug}}</slug>
    <!-- priority is NOT here: it lives on the index entry (§4.1) -->
    <status>tbd|in-progress|defined|excluded|superseded</status>
    <!-- status = how completely this feature is DEFINED, not how far it is BUILT -->
  </meta>

  <user-story>                               <!-- intent, before its elaboration -->
  As a {{actor}}, I want {{capability}}, so that {{benefit}}.
  </user-story>

  <description>...</description>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0">   <!-- items 33, 34 -->
      When <trigger>, the system shall <response>.
    </criterion>
  </acceptance-criteria>

  <gaps>                                    <!-- what this feature knows it is missing -->
    <gap id="1" kind="dependency" raised="2026-08-18">
    Markdown, including links, exactly as elsewhere.
    </gap>
  </gaps>

  <notes>
    <data-model>...</data-model>            <!-- item 2 -->
    <considerations>...</considerations>
  </notes>

  <rationale>...</rationale>                <!-- required when status=excluded -->
  <superseded-by slug="..."/>               <!-- required when status=superseded -->
</feature>
```

**`<user-story>` is new, and the corpus is the argument for it.** Measured across the 64 features:
**0** descriptions use *"As a…"*, **4** say *"so that"*, and **44 name no user at all**. This is not
formalising something authors already do — it is closing a gap that is nearly total, and the missing
half is the *benefit*, which is what MoSCoW is judged on.

**A separate element, not part of `<description>`.** Item 40's test 1 is *about* the description —
scope, and the boundary naming who holds each excluded part. Intent and elaboration are different
jobs, and one element serving two tests serves neither. The story goes first because the
description elaborates it.

**Prose with a three-part convention, not parsed attributes** (§4.3). No consumer needs to
*understand* a user story: item 8's agent could use the persona and MoSCoW is argued from the
benefit, but those are *could use*, not *must parse*. Locate it, check its shape, leave it in prose.

**The actor may be a consuming feature, not only a person.** Five reference-data features have no
human user, and forcing one yields *"As a system, I want…"* — the degenerate case that teaches
people to stop taking the field seriously. *"As **Best Value Engine**, I want price bands per
venue, so that I can compare offers without re-deriving them"* is a better story **and** it forces
a reference-data feature to name who consumes it, which is item 40's test 7 arriving from the other
direction. The features least able to state a human benefit are exactly the ones whose consumers
are least clear.

**Required for `defined`, not for `tbd`** (item 40, test 8). That means **34 stories now, not 64**;
the rest acquire one on promotion, and early authoring stays cheap. It is **new content, not a
transformation**, so it adds nothing to item 41 — this is authoring work, and item 8's agent can
propose a draft from the description, which it already reads.

**2. Give `<notes>` an internal shape — two elements, not three.**
*Narrowed by §4.3 (A10/D2).*

The corpus writes notes in three recurring kinds — data model, dependencies and relationships, and
free considerations — signalled with bold markdown headings. **Only one of the three needs to be an
element.**

- **`<data-model>` — element.** `analyze-prd` must *understand* it: it reads entities and fields
  and stops inferring them (P4). Locating it is not enough, so §4.3's second row applies.
- **`<relationships>` — dropped.** Item 27's `<depends-on slug= kind=>` already carries the
  outbound edges in machine-readable form, and item 40's contract rule finds inbound references by
  **grepping the feature's slug across the PRD** — locating, not parsing. A second structured list
  of the same relationships would be two producers for one idea, which items 29 and 46 both
  refused. Relationship *prose* stays in the notes; the edges live in `<depends-on>`.
- **`<considerations>` — prose, unread by design.**

**Migration must not be lossy** — unrecognised note content goes to `<considerations>` verbatim,
never dropped.

> **This removes one of the migration's four judgement axes** (item 41, R14). Restructuring notes
> across 64 files, three-way and losslessly, was on the plan's critical path; it is now a two-way
> split where one side is a catch-all. The prose convention that item 3's derivation already
> depends on — a bold `**Data model**` heading, measured at zero false positives — is what the
> migration keys on, rather than a shape a human must invent per file.

**`<considerations>` is deliberately unread**, and the template should say so. It is the catch-all
that makes migration safe and prose survivable; nothing machine-consumes it and nothing should.
Marking it explicit is what distinguishes *unread by design* from *unread by oversight*, which is
the distinction this plan exists to draw.

**3. Status derivation, as a script — and it is feasible.**
*Measured, with the caveat below.* A probe deriving each feature's status from its own content:

```
64 feature files
  defined    -> defined     34   OK
  excluded   -> excluded     7   OK
  superseded -> superseded   2   OK
  tbd        -> tbd         20   OK
  tbd        -> ambiguous    1   escalate
agree=63  ambiguous=1  contradicted=0
```

The rule, in order:

| Test | Verdict |
|---|---|
| 0 criteria + `<rationale>` | `excluded` |
| 0 criteria + successor link | `superseded` |
| 0 criteria, neither | **error** — no criteria and no reason |
| Notes carry a data-model / dependency / relationship marker | `defined` |
| ≥3 criteria and ≥1000 bytes of notes | `defined` |
| ≤2 criteria, or <400 bytes of notes | `tbd` |
| anything else | **ambiguous → escalate** |

The structured-notes marker was the decisive signal: present in 28 of 34 `defined` files and in
**none** of the other 30. Zero false positives.

**Re-run 2026-08-25 against the current corpus (A2), because the 63/64 figure was taken on a
snapshot this document elsewhere marks as superseded (R6).** Both rules were run separately so that
corpus drift and the rule change are not confounded. The ghost file is excluded; 62 indexed + 2
`superseded` pointers = 64.

| Rule | Result |
|---|---|
| **A** — the rule as first written, deriving a *value* | agree 60 · ambiguous 3 · **contradicted 1** |
| **B** — the rule as this item now specifies it, deriving a *ceiling* | **violations 0** of 64 |

**Rule A has degraded, and the way it degraded is the argument for Rule B.** Its single
contradiction is the feature declared `in-progress` whose content supports `defined` — an author
holding something back for reasons the file cannot express. Deriving a value calls that a defect.
Deriving a ceiling calls it fine, because *declared ≤ ceiling*. The three ambiguous files resolve
the same way.

**So the baseline item 23 commits is 0 violations under Rule B, not 63/64 under Rule A.** Recording
the superseded figure as a regression baseline would have repeated P9's mistake exactly one
revision later — a measurement inheriting the defects of the snapshot it was taken on.

> **One rule is untested.** No feature in the corpus carries a `<gap kind="specification">`; the
> only kinds in use are `dependency` and `decision`. §4.2's bar on `defined` is therefore sound in
> principle and **unexercised in fact**, and the fixture pair (item 43) is where it should first be
> made to fire.

**One half of the ambiguous band closes by declaration; the other half stays open on purpose.** A
`<gap kind="specification">` bars `defined` outright — that is a contradiction, and the derivation
should report it as one rather than escalate it. But the absence of such a gap proves nothing, so
a feature the author has marked `in-progress` is **never** contradicted upward to `defined`; the
derivation may only ever report *at most* what the content supports.

So the rule becomes: derive a **ceiling**, not a value. Report where the declared status exceeds
the ceiling; stay silent where it sits below. The escalation path survives for the band between,
and during item 41's migration that band is every file written before `<gaps>` existed.

**Item 33 adds the signal this rule is missing.** Every test above reads the notes or counts
criteria; none reads what the criteria *say*. Once criteria carry a `pattern` attribute, add:
a feature whose criteria are entirely `event-driven` is at most `in-progress`, however rich its
notes. On the corpus that single rule reclassifies eight features the current rule scores as
agreeing — see P23, which is the measurement this item's headline figure concealed.

> **Read this honestly.** Both rules were tuned on the corpus they were scored against, so neither
> figure is evidence of generalisation. What generalises is the shape: **a rule that reports a
> ceiling cannot contradict an author, and one that reports a value can.** The design is safe
> because it refuses rather than guesses — an ambiguous file is escalated, never silently
> relabelled.

And the escalation band is not a defect: **"criteria exist but scope is carried by the
description alone" is precisely what a counter cannot see.** The ambiguous band *is*
`in-progress`. The third status exists exactly where the deterministic rule must stop, which is
why the check is three-valued by construction rather than by concession.

**4. Migrate the corpus conventions into the templates, then reclassify.**
`excluded` + `<rationale>`, `superseded` + pointer + index removal, structured notes. Then re-derive
every status: expect a cohort of `tbd` files to become `in-progress`, and expect the two orphans
to validate as legitimate rather than flag.

**5. Retire `<phases>`: phasing is priority plus gaps.**
*Superseded in its own proposal, like items 29 and 46. P12 stands; its answer changes.*

This item originally proposed `<phases>` with `phase=` on criteria. Items 34 and 29 have since
arrived, and between them the toolchain now has **three** ways to say *not now*:

| Mechanism | Says | Carries |
|---|---|---|
| `priority="P2"` (34) | less important | a rank |
| `<gap kind="dependency\|decision">` (29) | blocked | *why*, and *since when* |
| `phase="2"` | later | nothing else |

**The corpus's phase-2 usage is the second, not the first.** Its phase 2s depend on external access
that does not exist and on questions that are open — one feature says outright that *whether phase
2 should exist at all* is undecided. Those are a dependency gap and a decision gap, and a gap
records why and when, which `phase="2"` cannot.

The case that looked like it needed a third axis — **a criterion that is essential but blocked** —
is handled better by the pair than by phases: priority keeps its `P0` because it matters, and the
gap blocks execution because it cannot proceed. Folding that into a phase would force an author to
*demote* something important in order to say it is stuck.

What is genuinely lost is naming a coherent increment: priority ranks, it does not group. That is
recovered from the filter rather than the schema — `--requirement-level P0` **produces** the
increment, so the grouping is a query result instead of a fourth thing to maintain.

**Removed with it:** `<phases>` from item 1's template, `phase=` from `<criterion>`, item 6's
check that `phase` references resolve, and `<feature-phase>` from item 16's task `<meta>`.

### B. `/prd` — the command

**6. Phase 6 becomes a real consistency check, run by script.**
Today Phase 6 asks the model four prose questions about the tech stack. It gains, as exit codes:

- derive status for **every** feature; report each mismatch as `declared X, derived Y, because Z`
- reconcile index against `features/` — orphans that are not `superseded`, dangling entries,
  and any feature file still carrying a `<priority>`. **Three causes, one test:** a `superseded`
  file may be unindexed, and anything else unindexed is a defect — a rename residue (P27) or real
  drift. Do not try to tell those two apart by counting references; P9 records why that fails
- a `superseded` pointer that **nothing references any more**, which has reached the exit condition
  the convention states and nobody evaluates
- **no reference anywhere to a slug that has no file**, which is the postcondition a rename has to
  satisfy and currently does not (P27)
- criterion `id` uniqueness within a feature
- `<user-story>` present on every `defined` feature, in three parts, with a *"so that"* clause that
  is not a restatement of the *"I want"* clause (item 40, test 8)
- `excluded` without `<rationale>`; `superseded` without a successor or still present in the index
- **EARS pattern coverage** per feature (item 33): report any `defined` feature with no
  `unwanted-behaviour` criterion, and any criterion whose `pattern` attribute is missing
- **unassigned criterion priority** (item 34), as a count — a corpus where everything is `P0`
  carries no information, and neither does one where nothing is set
- **architecturally-significant candidates** (item 35), screened by the published ASR heuristics
  and reported as candidates only, never applied
- **external references resolve** (item 39) — every `ADR-NNN`, `OQ-NNN` and principle citation
- **`<gaps>` well-formed**: unique stable `id`, a `kind` from the enum, an ISO `raised` date; and
  the status rule — `defined` with a `specification` gap, or `in-progress` without one, is a
  contradiction
- **gap age**, reported rather than judged. A gap raised months ago is a different object from one
  raised yesterday, and only the date shows it

Mismatches are **reported, not auto-corrected**. A wrong status is often a signal that the
*content* is wrong, and silently relabelling hides that.

**7. `--resume` re-runs the check across all features, before resuming.**
This is the point of item 6. A PRD is edited over weeks; the features `/prd` did not touch this
session are exactly the ones whose labels have gone stale. Stamping only what it touched is how
the label drifts from the content in the first place.

**8. A criteria-authoring sub-agent — worth building, with a specific persona.**
*Recommended: yes.* Not a second author with the same voice — a **challenger**. The corpus makes
the case: the best-defined features carry negative cases, abstention behaviour and
irreversibility warnings, and those are precisely what an author who just wrote the happy path
does not think to add. A same-persona agent would deepen the bias; an adversarial one corrects it.

- `agents/prd-criteria-author.md`, `context: fork` — 64 features must not accumulate in one context.
- Input: one feature file, plus the index entry and the named related features. Output: proposed
  criteria only, never a rewritten file.
- Persona: a QA lead trying to find the case the author missed — edge cases, empty and error
  states, the negative assertion, the thing that must *not* happen.
- It also **drafts the `<user-story>`** from the description, for the same reason it drafts
  criteria: it has already read the feature, and 44 of 64 features name no user for a proposer to
  start from. The author accepts or rejects, as everywhere else in this item.
- **Its checklist is the six EARS patterns** (item 33), which turns a vague brief into a specific
  question: which patterns are unrepresented here? A feature with fifteen `event-driven` criteria
  and no `unwanted-behaviour` one has a named gap rather than a hunch, and P23 says that describes
  most of the corpus.
- It also proposes the `<data-model>` note, since `defined` requires it (§4.2).

> **Keep it opt-in, per feature.** Run unattended across 21 `tbd` features it would produce
> plausible criteria that nobody has agreed to, and a `defined` status derived from them would be
> *true* and *worthless*. The user accepts or rejects each set. This is the one item where
> automation must not close the loop.

**9. Make `/prd`'s prose guards executable (P16).**
The Phase 8 pre-write existence check, the status marker, and item 6's checks all become scripts.

> **Measured, 2026-08-24 — the mechanism exists and the fallback is not needed.** A command
> reaches a bundled script as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`, expanded by the harness
> before the model sees the command body. Open question 1 has the evidence;
> [`probes/README.md`](probes/) has the method.
>
> Two rules follow for every script this item adds. **Pass the plugin path as an argument rather
> than reading `CLAUDE_PLUGIN_ROOT` inside the script** — it is not exported to the shell. And
> **never write a bare relative path**: the working directory is the target project, so
> `scripts/foo.sh` resolves against the wrong tree and fails with a bare *No such file or
> directory* that reads like a missing file rather than a wrong assumption.

**10. Feature files are read per feature, never as one blob.**
`/prd` writing 64 files in one context is the same P5 problem at the authoring end.

### C. `what-next.md`

**11. Design: XML skeleton, markdown bodies, derived TBD list.**
This subsumes assessment item 4.4 and answers the skill's own critique — that its "next steps"
were post-PRD activities while the template expected authoring gaps. **They are two different
lists and the file needs both.**

```xml
<what-next>
  <meta>
    <prd-slug>...</prd-slug>
    <status>in-progress|complete</status>   <!-- what /prd --resume greps for -->
    <last-updated>YYYY-MM-DD</last-updated>
    <next-command>/breakdown</next-command>
    <toolchain-version>2.0.0</toolchain-version>
  </meta>

  <!-- DERIVED by item 6. Never hand-maintained. Aggregates the feature files' own
       <gaps> blocks rather than re-deriving a shortfall from status. -->
  <authoring-gaps>
    <summary defined="34" in-progress="1" tbd="21" excluded="7" superseded="2"/>
    <gap slug="..." id="2" kind="dependency" raised="2026-08-18"/>   <!-- carried, not restated -->
    <feature slug="..." status="tbd">no criteria written</feature>   <!-- no <gaps> to carry -->
  </authoring-gaps>

  <!-- HUMAN-AUTHORED. Post-PRD work. Markdown bodies. -->
  <next-steps>
    <step kind="breakdown">...ordered task-generation sequence...</step>
    <step kind="spike">...technical validation, with what it must measure...</step>
    <step kind="infrastructure">...</step>
    <step kind="data-model">...</step>
    <step kind="ux">...</step>
  </next-steps>

  <risks>
    <risk><description>...</description><mitigation>...</mitigation></risk>
  </risks>

  <open-questions href="../../product/open-questions.md"/>  <!-- pointer or inline -->
  <session-notes>...</session-notes>
</what-next>
```

Three things this gets right that neither the current template nor the corpus file does:

- **`<authoring-gaps>` is derived.** The corpus file lists no TBD items at all — with 21 of them,
  hand-maintenance was never going to happen. Generating it is what makes it survive.
- **`kind=` on steps** preserves the prose file's real value — the spikes and what they must
  measure, the infrastructure, the design work. It routes: item 40 sends a spike to investigation
  and a cross-feature question to the register, and `kind=` is what tells them apart.
  *It is **not** justified by `/breakdown` consuming the sequence — item 27 concludes it must not,
  and an earlier draft of this bullet claimed otherwise.*
- **`<risks>` is deliberately unread.** It is for the human resuming the work. Recorded so that its
  absence from every consumer list reads as intent.
- **`<open-questions>` may be a pointer.** The corpus moved its questions to a project-wide
  register; the template must permit that instead of forcing them back inline.

Markdown stays inside the elements. The goal is a parseable skeleton, not the loss of prose depth.

**12. Migrate the existing prose file, and keep the marker readable in both.**
`/prd`'s initialization greps `<status>in-progress</status>` from `what-next.md` *or* `index.md`.
Keep the dual check until every artefact is migrated — a PRD that cannot be found is a PRD that
gets overwritten.

### D. `/breakdown`

**13. Skip `wont-have`, `excluded` and `superseded` unconditionally.**
Correctness, not preference. No flag, no override.

**14. Add `--priority <threshold>`, mirroring `--layer`.**
`must-have` = must only; `should-have` = must+should; `could-have` = all three. **Default
`could-have`** — that preserves today's behaviour minus item 13, so the flag adds capability
without silently changing what an existing invocation builds.

**Item 34 adds a second, finer filter** — `--requirement-level <P0|P1|P2>`, applied after this
one. The two compose: this flag selects *features*, that one selects *criteria within them*.

> **A filtered set is not automatically a buildable set — and item 34 is what makes that
> computable rather than blocking.** 9 of the corpus's 13 must-have features reference lower-tier
> features, 49 times in total, so filtering on this flag alone yields an open set. Criterion-level
> priority closes it: a must-have depending on a could-have pulls **that feature's `P0` criteria**,
> not the whole feature. **Build 34 with this item, not after it** — the flag is easy, and on its
> own it is the wrong half.

**15. Refuse to break down features that are not defined enough — loudly.**
A `tbd` feature has a name and roughly one criterion. Breaking it down does not produce a thin
task; it produces an **invented** one, and TDD then locks the invention in as passing tests.
Skip `tbd` unless `--include-tbd`. **Once `<gaps>` exists the rule gets finer and better**: refuse
any feature carrying a `<gap kind="specification">`, whatever its status, and *warn* on
`dependency`, `decision`, `evidence` and `ownership` gaps rather than refusing — those say the
feature is specified but not yet buildable, which is a scheduling fact rather than a definition
defect. A status is a summary; the gap block is the detail, and the detail is what should drive
the decision. In the corpus this would skip 21 features — **including 5
must-haves**, which is exactly the point: the report must name them, because "5 must-have
features are not defined enough to break down" is the single most useful sentence `/breakdown`
could say about that PRD. Silent omission would be worse than the current behaviour.

**16. Carry the feature through to the task — under names that are free.**
In `task-format-spec.md` `<meta>`, **not** as `<priority>` (P3):

```xml
<meta>
  <id>L2-003</id>
  <priority>1</priority>                    <!-- UNCHANGED: integer, merge order -->
  <source-feature>{{feature-slug}}</source-feature>   <!-- P15 -->
  <moscow>must-have</moscow>                          <!-- P1, feature level -->
  <satisfies-criteria>1,4,7</satisfies-criteria>      <!-- item 34, criterion level -->
  <requirement-level>P0</requirement-level>           <!-- highest among those criteria -->
</meta>
```

`<satisfies-criteria>` is the finer traceability Kiro's spec asks for and its own samples fail to
keep — their workflow specifies `_Requirements: 1.2_` and the sample degrades to
`_Requirements: 1_`. Fine-grained traceability survives only where something checks it, which is
item 30's job and the reason the two items are paired in the ordering below.

**17. Carry the criteria and the data model, structurally.**
`<prd-excerpt>` as free prose is how P2 and P4 happen. Add to the task format:

- `<acceptance-criteria>` — the source criteria, **verbatim with their original ids**, so a task
  cites `criterion 7` and coverage is reportable
- the feature's `<data-model>` note carried into `<context>` rather than re-inferred
- `<test-requirements>` **derived from** the criteria, with each test naming the criterion it covers.
  Item 33 improves this concretely: an `unwanted-behaviour` criterion states its negative case
  explicitly, so the failing test is read off rather than invented — which is what the toolchain
  currently does, and what P19 says it cannot be trusted to do

This is where the pipeline stops discarding the document.

**18. Fix P5: analyse per feature, not per corpus.**
*Amended 2026-08-26 after the first real run: the merge is not purely arithmetic. A feature pass
cannot see the index and the index pass sees no feature, so the split CREATES contradictions
visible nowhere else — components inferred for a backend-only project, a template path the PRD's
own rationale disclaims, a test dependency no feature declares. The merge reconciles those and
records each in `merge_notes`. The instruction it replaces ("do not re-infer during the merge")
was disobeyed on the first run, correctly, and the model invented `merge_notes` to say so — P10's
shape, arriving in an element this plan had just specified.*
Two stages: an index-level pass (~13k tokens — tech stack, feature list, priorities,
architecture) and a per-feature pass fanned out one file at a time, each writing its own
fragment. `generate-tasks` receives only the feature files for its batch. Add a hard **size
check with a refusal**, in the idiom of `resolve-output.sh`: if a single prompt would exceed a
threshold, refuse with `REFUSED:` rather than silently truncating. Re-examine
`model: claude-haiku-4-5` on `analyze-prd` once the per-feature split lands — the split may
make haiku adequate; without it, no model choice rescues the design.

### E. `/execute`

**19. Report the tier being built — both tiers.**
Carry `<moscow>` **and `<requirement-level>`** into `execute-state.json` per task, and group the
final report by both. Requires item 16 and nothing else.

The second is the one that would otherwise have no reader at all. Item 16 puts
`<requirement-level>` on the task; item 30 checks criteria against the *threshold* rather than
against the element; nothing else looks at it. Reporting it is both the cheapest reader and the
useful one — *"built 14 tasks: 9 must-have/P0, 5 should-have/P0"* is a sentence an operator can act
on, and it is the only place the two-level filter (items 14 and 34) becomes visible in the output
rather than only in the invocation.

**20. Refuse won't-have tasks at execution time.**
Defence in depth, as an exit code, matching item 4.13's principle that guards must be executable.
A task carrying `<moscow>wont-have</moscow>` reaching `/execute` means item 13 failed, and it
should stop there rather than be built.

### F. Cross-cutting

**21. The runtime test P1 still owes.**
Minimal PRD: 4 features, one per tier, each with 2 criteria. Run `/breakdown`. Assert
task count and that no task derives from the won't-have. Run before and after items 13–16 — the
"before" run is what converts P1 from static to measured. Keep it small deliberately: P5 means a
realistic PRD would fail for an unrelated reason and confound the result.

**And time the authoring** (§4.3, R17). Author the same four features under the current templates
and under the new ones, and record how long each takes and where the time goes. It is a sample of
one and it is not a measurement of quality — but the plan adds a phase, replaces the criterion
format, and re-annotates 550 criteria, and *"is this still tolerable to write?"* currently has no
answer at all. One number beats none, and the fixture is where it costs nothing to take.

**Split into two halves when built, because only one of them is automatable.** `probe-p1.py
--baseline` takes the *size* — words, criteria and elements per feature — which is the instrument
the after-measurement compares against, and it is worth having on record before items 33 and 34
move it. The *timing* is a stopwatch against a person and no script can take it; the probe says so
in its own output rather than reporting the size half as though it were the whole. Whoever runs
the after-measurement records both numbers together.

> **The two paragraphs above are the specification as written, and the timing half of it was
> withdrawn on 2026-09-10 without being taken** — see the dated note below. The size half and the
> judgement count were both taken and stand.

**The probe's third exit code is the one to keep.** A run that generates no tasks, or none from
the must-have, exits `INVALID` rather than clean: *"no won't-have tasks"* is vacuous when nothing
was generated at all. That guard is not hypothetical — two checks in Phase 1 passed against
nothing before it was added to them.

> **Taken 2026-09-08 — the size half, and the answer is the opposite of the worry (V6).**
> Item 21's *before* was recorded in Phase 1 as 394 words, 8 criteria and 64 elements across the
> four `staff-service` features. Rather than trust that figure, it was **recomputed from the
> frozen `schema-1` fixture with today's script**, so both ends of the comparison come off one
> ruler: it returns 394 / 8 / 64 exactly. Every version between was measured too, because two
> points hide the shape.
>
> | Fixture | Words | Criteria | Elements | What landed in it |
> |---|---:|---:|---:|---|
> | `schema-1` | 394 | 8 | 64 | the baseline |
> | `schema-2` | 394 | 8 | 64 | item 45's renames — no size change, by design |
> | `schema-3` | **386** | 8 | **40** | items 33, 34 — EARS replaces Given/When/Then |
> | `schema-4` | 526 | 8 | 47 | items 1, 2, 5, 27, 29, 35 — the rest of the template |
> | `schema-5` | 526 | 8 | 47 | the CRD path only; PRD features unchanged, as declared |
> | `schema-6` | **763** | 8 | 59 | item 40's `<review>`, and the content the bar had been failing |
>
> **The format change this plan worried most about made features smaller.** Item 33 was graded a
> likely failure point and priced as the migration's hardest step; at `schema-3` it takes 8 words
> and **24 elements** out. One EARS sentence carrying two attributes is cheaper to write than a
> three-element Given/When/Then triple, and the criteria count never moves — 8 throughout, 2 per
> feature — so that is a per-criterion saving rather than a smaller sample.
>
> **What roughly doubled the prose is content, not syntax.** `schema-4` adds `<user-story>`,
> `<gaps>` and `<data-model>`; `schema-6` adds a recorded review and the data models four features
> were missing. Those are things the bar now asks an author to *know*, and the growth is uniform
> across all four features rather than concentrated in one. Elements went **down**, 64 → 59.
>
> So the size half answers: **the tagging got cheaper and the thinking got dearer.** That is the
> trade item 40 exists to make, and it is now measured rather than assumed.
>
> **The timing half is WITHDRAWN, 2026-09-10, and was never taken.** *Is this tolerable to
> write?* was a proxy for *did we accept too much cost*, and the person who bears the cost has
> answered it directly: **the 32 judgements were asked for, and the time they take is an accepted
> consequence of the fidelity they buy.** A stopwatch would have priced a decision already made.
>
> Two things about the protocol below, which is kept rather than deleted. It was never a
> measurement of the activity anybody performs — **`/prd` writes the feature files**, so a person
> hand-authoring XML under two templates is timing work the toolchain does. And the mismatch was
> not something that crept in: **the sample corpus was itself produced by the original commands**,
> so machine authorship was the case on the day item 21 was written, not a later development.
>
> The caveat that would have mattered, recorded in case the question is ever reopened:
> `schema-6`'s increase includes the fixture's own content work — four features that failed the
> bar and were fixed — so part of that 237 words is a debt being paid, not a per-feature cost.
>
> ---
>
> **The other half of the sentence, taken 2026-09-08.** Item 21 asks for the time *"and where the
> time goes"*. The stopwatch needs a person; **where it goes does not**, and measuring it changes
> how the size table above reads.
>
> `probe-p1.py --decisions` counts the judgements a template demands that **a machine is forbidden
> to make** — a stricter test than *a field an author fills in*, because `<slug>` is authored and
> mechanical while `pattern` is authored and forbidden. Only the second kind drives an interview.
>
> | Fixture | Author judgements | What was added |
> |---|---:|---|
> | `schema-1` · `schema-2` | **0** | — |
> | `schema-3` | **16** | `pattern` 8, criterion `priority` 8 (items 33, 34) |
> | `schema-4` · `schema-5` | **26** | `<user-story>` 4, `<depends-on kind>` 2, `<gap kind>` 2, `<architecturally-significant>` 2 |
> | `schema-6` | **32** | `<review by>` 3, `<data-model>` 3 |
>
> **This inverts the comfortable reading of the size table.** `schema-3` is the version that made
> features *smaller* — 8 words and 24 elements out — and it introduces **half of every judgement
> the author now owes**. Item 33 is simultaneously the largest saving in bytes and the joint
> largest cost in decisions. A byte count alone would have scored it a clear win; it is a trade.
>
> **Nought to thirty-two across four features is the honest headline** — eight per feature, from a
> template that demanded none. That is why the prose doubled: each judgement produces sentences.
>
> **What this is not.** It is not a timing and does not stand in for one. It is the quantity a
> stopwatch would be explaining.
>
> ---
>
> **The protocol for the timing half — WITHDRAWN 2026-09-10, kept for the record.** It is left
> here in the idiom `parity.md` uses for a resolved row: a decision is easier to revisit than to
> reconstruct, and *"we chose not to measure this, and why"* is a fact worth being able to check.
> **Nothing below is outstanding.** Were the question ever reopened, step 1 is the one to rewrite
> first — it times hand-authoring, which is not the activity `/prd` performs.
>
> 1. **Author `staff-service`'s four features from the same brief**, twice: once against
>    `schema/prd-format.md` as it stood at `schema-1` (`git show` the frozen fixture's templates),
>    once against it as it stands now. Use the brief, not the existing files — copying is not
>    authoring.
> 2. **Record wall-clock per feature**, not per session, so a single interruption does not spoil
>    the run.
> 3. **Record where it went**, against the eight judgements in the table above. *Which decision
>    took longest* is the number that changes anything — if it is `pattern`, item 33 needs better
>    guidance; if it is `<data-model>`, that is §4.2 doing its job and costing what it should.
> 4. **Second author, or say it is n=1.** One person's timing is a sample of one and this plan has
>    twice recorded a figure that was true of one snapshot and not of the thing it named (P9, R6).
> 5. **Record it beside the two tables above**, which is what item 21 asks for and why they are
>    kept here rather than in the ledger.
>
> **What would have changed the answer, had it been taken.** If the after-timing were within noise
> of the before, the schema changes were free. If materially longer, the question is *which* of the
> 32 judgements bought it — and item 8's `prd-criteria-author` agent already exists to propose
> exactly those, which is the lever that remains available whether or not anybody ever holds a
> stopwatch.

**22. One artefact schema check, shared by producer and consumer.**
P10 is a general failure: the spec says XML, the run produced markdown, and nothing noticed for
weeks. A single `check-artefacts.py` validating `index.md`, `what-next.md` and every feature file
against the declared schema, invoked in three places:

- at the end of `/prd` — before claiming the PRD is written
- at the **start** of `/breakdown` — refusing on mismatch, in the `resolve-output.sh` idiom
- in `tests/test_toolchain.py`, against a fixture

A producer/consumer mismatch should fail at the boundary, not silently degrade three skills later.

**Item 39 extends this outward**, to the 190 references that leave the PRD entirely (P24). Same
script, same boundary, one more class of thing that is currently asserted and never checked.

**23. Extend the regression suite.**
New checks in the existing `@check(name, finding=...)` style: no `<priority>` in the feature
template (item 1); the status enum in the template matches the one the derivation script
implements; task-format-spec declares `source-feature` and `moscow`; `<acceptance-criteria>` has
a non-comment consumer on the PRD path; the derivation script scores 0 contradictions against a
committed fixture.

**Three checks come from item 43 and P28**, and the first is a live defect rather than a
regression guard: `execute-state.json`'s documented `schema_version` must equal what
`write-state.py` writes — today they are `2.0` and `3.0`. Then: each fixture validates against
**its own** schema rather than the current one, and exactly one schema is marked current, since
the end-to-end checks must run against that one.

**And the check that would have caught this plan's own nine.** Every element the schema defines
must have either a named reader or an explicit *unread by design* marker — `<considerations>` and
`<risks>` are the second kind, and everything else must be the first. Run the same test in reverse:
every artefact a component reads must have a named producer, or be declared externally maintained
as the open-questions register now is (item 39).

An audit of this plan against that rule on 2026-08-25 found **nine failures**, two of them
contradictions between items rather than omissions — in a document whose closing argument is the
sentence below. That is the strongest possible evidence that the rule needs a script rather than a
principle.

That last one matters most. **P2 and P4 were both invisible to a test suite that reads the
files, because the failure is an absent consumer rather than a wrong string.** A check that a
producer has a reader is the general form of this whole plan.

**24. Toolchain version stamping — the residue of item 4.5.**
Mostly delivered: `plugin.json` declares `2.0.0` and `build-manifest.py` writes
`toolchain_version` into the manifest. What remains:

- `/prd` writes `<toolchain-version>` into `what-next.md` (item 11's `<meta>`)
- `/execute` compares the manifest's recorded version against the running plugin and warns on a
  mismatch, refusing on a known-incompatible one

**Two versions, not one** (P28). `toolchain_version` records *what produced* an artefact;
`schema_version` records *how to read* it, and it is the one the compatibility decision reads. A
patch release moves the first and not the second, which is why a provenance stamp cannot answer a
compatibility question. The concept already exists for `execute-state.json` — generalise it rather
than invent it, and fix it there while passing: the reference says `2.0` and the script writes
`3.0`.

Item 43 supplies the artefacts without which none of this can be tested.

The schema changes in this plan are exactly the kind of break that makes this worth finishing:
an artefact written by 2.0 and read by 2.1 must not be misread silently.

### G. Architecture

**25. Give architecture an artefact, and make it the greenfield counterpart of PROJECT.md.**
*Addresses P11, P17. **Widened by item 28**, which carries the other four vendored opinions
(layers, test policy, file limits, scaffold) in the same file rather than a new one — read them
together.*

Architecture divides cleanly by scope, and the two halves belong in different places:

- **Feature-local** — the entities, fields and relationships a single feature owns. Home:
  `<notes><data-model>`, with edges in `<depends-on>` (items 2, 27). Most of the corpus's index block is
  this, and it only ended up in the index because the feature file had no structured slot.
- **Cross-cutting** — inheritance strategy, bounded-context rules, ownership conventions,
  patterns no single feature owns. Home: a **new artefact**.

**Not `what-next.md`.** That file is transient by design — a status marker, a to-do list, and
session notes, consumed and then stale. An architectural constraint is durable and must be read
*every time* `/breakdown` generates tasks, not once when someone resumes. Putting a durable
constraint in a transient file is the same category error as §4.1's priority-in-the-feature-file:
right content, wrong lifetime. A `<step kind="architecture">` also mixes *decisions already made*
in with *work not yet done*, which is the one distinction `<next-steps>` exists to draw.

**Recommended shape:** `architecture.md` at the **project root, beside `PROJECT.md`** — not under
`docs/prd/{slug}/` — written in the **same schema as PROJECT.md's `## Architecture` section plus
its schema registry**. Four reasons, and the first was a correction:

- **It is project-scoped content, so it needs project scope.** `/prd` explicitly supports several
  PRDs in one repository — it globs `docs/prd/*/` and offers to *"start a new one alongside it"*.
  Layer graphs, test policy, task limits and banned patterns are properties of the **codebase**,
  so a per-PRD file would let two PRDs state two different architectures for one repository, and
  item 26 would then seed a single project-scoped `PROJECT.md` from whichever ran last.
- One architecture format rather than two — **with registries as an open set** (P35). PROJECT.md's
  API and schema registries are the right pair for a REST-and-relational project and the wrong pair
  for four of the five patterns in §8. `architecture.md` may declare any registry its architecture
  needs — `<event-registry>`, `<command-registry>`, `<service-registry>`, `<screen-registry>` —
  and PROJECT.md gains the same freedom when item 26 seeds it. Fixing the pair would be item 28's
  own defect, one level further down.

  **Registries are direct children of the root, beside `<rules>` and not inside it. Decided (A3,
  D1).** `<api-registry>`, `<schema-registry>`, `<event-registry>`, `<command-registry>`,
  `<service-registry>`, `<screen-registry>` — the names PROJECT.md already uses, at the level it
  already uses them.

  Two reasons, and the first is decisive. `PROJECT.md` keeps `<meta>`, `<features>`,
  `<api-registry>` and `<schema-registry>` as **root children**, and `check-project-md.py` reads
  `[c.tag for c in root]`. This item's whole premise is *the same schema as PROJECT.md*, and item
  26 seeds one from the other; nesting registries inside `<rules>` would make that seeding a
  *transform* rather than a copy and would put the validator out of reach — defeating the reason
  for sharing the schema at all. And item 37 reserves `<rules>` for what the toolchain **obeys**; a
  registry is read, not obeyed, so an inventory does not belong in the enforced set.

  **And each registry needs a reader, or this is P4 in a new file.** `analyze-prd` loads them, as
  it loads the feature's `<data-model>` — a registry *is* a data model at project scope.
  `generate-tasks` carries the entries a task touches into its `<context>`.

  **Two readers already exist and both must change (R8).**
  `skills/execute/scripts/check-project-md.py` hard-requires `meta`, `features`, `api-registry`
  and `schema-registry`, so a CLI project seeded by item 26 with only a `<command-registry>` fails
  a guard it should pass. That file appeared nowhere in this plan before this revision.

  **Decided (A3, D2): the validator requires *at least one* registry, and each consumer checks what
  it reads.** The script's own docstring says it exists because a bare `&` broke parsing and *"the
  run reported success"* — its job is well-formedness, and the two named registries were a proxy
  for *consumers can read this*. Requiring any one `*-registry` keeps the proxy honest without
  mandating a shape. `crd-impact-analysis` then refuses clearly when the specific registry it is
  about to read is absent. Each checks what it actually understands, which is items 6 and 22's
  split applied one level down.
- `/breakdown` already knows how to load that shape for CRDs, so the greenfield reader is a small
  change rather than a new one.
- It lets item 26 close the P17 loop — after `/execute`, the finalizer seeds `PROJECT.md` from it
  instead of being skipped, so a greenfield project ends with the architecture record it currently
  never gets. **With both files at project root, that seeding no longer widens scope**; it is one
  project-scoped artefact informing another.

ADRs stay where the corpus already puts them: outside the PRD, holding the rationale and the
history. `architecture.md` holds the *binding constraints* and may cite an ADR by pointer. The
distinction that matters is not prose-versus-XML but **whether the toolchain has to read it** —
a constraint that binds task generation must be machine-readable and local; a rationale that
explains it to a human need be neither.

**Then give it a reader**, or this becomes P11 again in a new file: `analyze-prd` must load it,
its "no opinions about architecture" instruction must be narrowed to *"do not invent
architecture; do apply what `architecture.md` states"*, and `generate-tasks` must carry the
binding constraints into `<context>`.

**26. Fix P17's output half: seed PROJECT.md on greenfield.**
Replace `/execute`'s `test -f PROJECT.md` gate with: if it exists, update it; if it does not and
the run came from a PRD, create it from `architecture.md` plus the task exports. The current
condition means PROJECT.md is only ever updated where it already exists, which no greenfield run
can satisfy.

**27. Capture feature dependencies structurally, and let ordering be derived.**
*Addresses P1's residue, open question 4, and the ordering duplication described below.*

`what-next.md`'s task-generation order in the corpus was **deduced by the model during `/prd`**,
not authored by a human. That reframes it: it is not an authority to defer to, it is a *second
model's unvalidated inference* — produced with more context than `/breakdown` has, but with no
dependency graph, no validation, and no awareness that `breakdown-plan-layers` exists to do
exactly this job. Two producers of the same artefact, out of band, neither aware of the other.

So `/breakdown` should **not** consume the sequence. But the sequence is evidence of something
real: while writing the features, the model noticed dependencies it had nowhere to record, and
emitted an ordering because ordering was the only expressible form of that knowledge. **The
durable artefact is the dependencies, not the order.**

Capture them where they are noticed:

```xml
<depends-on slug="{{feature-slug}}" kind="data|runtime|reference"/>
```

This is the fourth instance of P11's pattern, and it pays for itself three times over: it
disambiguates the 49 cross-tier references that are currently plain markdown links indistinguishable
from "see also"; it makes open question 4 answerable — whether a `--priority` filter yields a
closed set becomes a computation rather than a guess; and it gives `plan-layers` real input, so
the ordering is derived once, by the component that owns ordering, from evidence rather than
from recollection.

`<next-steps>` then keeps the *rationale* — why a spike matters, what it must measure — and
drops the sequence.

### H. Rules the project owns, and scale

Five items folded in from [`sdd-comparison.md`](sdd-comparison.md) on 2026-08-24, numbered 28–32
so that 1–27 keep their cross-references. They span components rather than belonging to one, which
is why they are a section rather than additions to A–G. Item 32 is the late one: it answers the
comparison's C10, which the first fold dropped and the re-verification pass put back.

**28. Widen `architecture.md` into the project's rule file.**
*Addresses P18. Extends item 25 — read that first.*

Item 25 already establishes the right artefact in the right place: a prescriptive, machine-readable
file at the **project root** beside `PROJECT.md` (item 25, corrected — *not* under
`docs/prd/{slug}/`), sharing PROJECT.md's schema, with a reader in
`analyze-prd` and a carrier into `<context>`. It scopes that artefact to *architecture*. P18 is
that architecture is one of five vendored opinions, and the other four need the same channel.

**So this is not a second file.** Adding `PRINCIPLES.md` alongside `architecture.md` and
PROJECT.md would make three files describing one project, which open question 2 is already
uneasy about at two. Widen the one item 25 defines:

```xml
<rules>
  <layers>                                  <!-- replaces the hardcoded five-tier DAG -->
    <layer id="1" name="foundation" depends-on=""/>
    <layer id="2" name="backend"    depends-on="1"/>
  </layers>
  <!-- depends-on is a COMMA LIST and the result is a DAG, not a chain: an event-driven
       graph fans contracts out to producers and consumers independently, then converges.
       A single-valued attribute could not express the case P18 uses as its example.
       Optional applies-to instantiates the graph once per matching directory, which is
       what microservices and multi-platform mobile need (P35, §8). -->
  <layers applies-to="services/*/"> ... </layers>
  <testing default="tdd" runner="pytest">          <!-- scoped, because one runner is never enough -->
    <policy match="services/**"  kind="consumer-contract" runner="pytest"/>
    <policy match="web/**"       kind="component"         runner="vitest"/>
  </testing>
  <task-limits default="3">
    <limit match="contracts/**" max-files="5"/>
  </task-limits>
  <repo-structure>single|monorepo|multi-repo</repo-structure>   <!-- item 53 -->
  <banned>                                       <!-- every rule carries a kind: item 56 -->
    <rule kind="import|edge|change|content|judgement" reason="..." ...>
      <except match="..." reason="..."/>         <!-- exceptions belong to the rule, not the task -->
    </rule>
  </banned>
  <scaffold template="python|go|tanstack|none" path="..."/>
</rules>
```

Three consequences, and the first is the one that makes this the largest item in the plan:

- **`layer-definitions.md` stops being the layer graph and becomes its default.**
  `breakdown-plan-layers` reads the graph from `<layers>` when present. This is what actually
  answers Böckeler; every other change here is a refinement of a fixed pipeline, and this one
  makes the pipeline a parameter. It also composes with item 27: `<depends-on>` supplies
  feature-level edges, `<layers>` supplies the tiers those edges are grouped into, and ordering
  is derived from both rather than recalled from either.
- **TDD becomes a default, not a law — and this is a three-reader change, not a one-line read.**
  The mandate does not live in `tdd-workflow.md`, which only describes Red/Green/Refactor (P18).
  It is imposed upstream: `<test-requirements>` is a *required* section in `task-format-spec.md`,
  and `review-criteria.md` makes it critical twice over. A project declaring `default="none"`
  would therefore have every task fail batch review at `/breakdown` time and never reach
  `execute-batch` at all. So `<testing>`'s `default=` — and any `kind=` on a scoped `<policy>` —
  has to be read in three places, by
  `generate-tasks` (whether to emit the section), by `review-tasks` (whether to require it), and
  by `execute-batch` (whether to run the tests first) — and `task-format-spec.md` has to stop
  marking the section unconditionally required. The current mandate is right for most projects
  and wrong for a spike, and the toolchain should be able to say which it is running.
- **The template list stops being an enum in a reference file.** `<scaffold>` names a path.

**Four revisions from §8's worked examples** (P35), each of which the five patterns forced:

- `depends-on` is a **comma list**; the graph is a DAG. Item 43's validation — acyclic, every layer
  reachable, no task stranded — stops being nice-to-have and becomes the thing that makes a
  hand-written graph safe.
- `<layers applies-to="…">` instantiates a graph **per matching directory**, for microservices and
  for multi-platform mobile. A monolith declares one unscoped block and never meets the feature.
- `<testing>` and `<task-limits>` take **scoped overrides**, using the same `fileMatch` mechanism
  this item already borrowed for `<banned>`. A monolithic SPA needs two runners, so this is not an
  exotic requirement.
- `<repo-structure>` is declared rather than assumed (item 53).
- **Registries are deliberately not here** (item 25, A3/D1). `<rules>` is what the toolchain obeys;
  a registry is an inventory it reads. They sit beside this block as root children, with the names
  and at the level `PROJECT.md` already uses, so that item 26's seeding stays a copy.

**Guard it the way this repository has learned to (S3 / P16):** a script parses `<rules>`, and
`/breakdown` refuses in the `resolve-output.sh` idiom if a rule file is present and unparseable.
A silently-ignored rule file is worse than none, because the operator believes the rule is in
force. Absent is fine and means defaults; present-and-broken must stop the run.

**29. Give uncertainty a channel that survives the handoff.**
*Addresses P19.*

**Superseded in its own proposal: use `<gaps>`.** This item originally invented a
`<needs-clarification>` element. The corpus has since grown one of its own, and it is better in
every respect — stable ids that survive citation from a commit or a review, a `kind` taxonomy
instead of a boolean, and a `raised` date, without which an open item and a stale one look
identical. Adopt it rather than adding a second element for the same idea; two mechanisms for one
concept is exactly the drift item 22 exists to catch.

```xml
<gaps>
  <gap id="3" kind="specification" raised="2026-08-18">
  Retention period for archived links is unspecified.
  </gap>
</gaps>
```

`kind` replaces `blocking=` with something more useful than a boolean, and the mapping is the
substance of this item:

| Kind | Blocks definition? | Blocks execution? |
|---|---|---|
| `specification` | **yes** — it bars `defined` outright (§4.2) | yes |
| `dependency` | no | yes, until named and available |
| `decision` | no | yes — an undecided question built anyway is an invented one |
| `ownership` | no | warn: the boundary may move under the task |
| `evidence` | no | warn |

`analysis.json` must carry gaps, task files must preserve them, and item 38's gate reads them.
The overnight-run objection that motivated `blocking="false"` is answered better here: three of
the five kinds warn rather than stop, so a run is halted by a genuine unknown rather than by every
open item.

**Extend the vocabulary that already exists rather than inventing a second one.** P19 records
that the CRD path already carries `<confidence>high|medium|low</confidence>` as a required field,
tied explicitly to ambiguous matches and incomplete context, with no reader. Two mechanisms for
one idea would be one too many: `<needs-clarification>` marks a *specific* unresolved point while
`<confidence>` grades a *whole analysis*, and both should end up feeding the same gate in item
30's script and the same line in the run report. Giving `<confidence>` its first consumer is the
smaller half of this item and can land first.

The corollary is the part that matters, and it is a change to `review-criteria.md`: **the
placeholder ban must apply to unmarked vagueness only.** Banning `TBD` outright is precisely what
makes invention the compliant answer (P19). Marked uncertainty should *pass* review and *block*
execution; unmarked vagueness should keep failing review exactly as it does now.

Two boundaries to respect. `/prd`'s eight-phase interview is a better resolution mechanism than
anything downstream, because a human is answering — this item is for what the interview *failed*
to resolve, not a licence to stop asking. And `blocking="false"` must exist, or every open
question stops an overnight run; non-blocking items belong in the report, alongside item 15's
named skips.

This item applies the discipline of the ledger to knowledge. `/execute` already refuses to
report completion it cannot verify against git; it should equally refuse to build a requirement
that admits it is not one.

**30. A coverage check between `/breakdown` and `/execute`.**
*Addresses P20. Depends on item 16.*

One script, three assertions, run at the end of `/breakdown` and again in `/execute`'s preflight:

- every feature above the `--priority` threshold has ≥1 task naming it in `<source-feature>`
- every task's `<source-feature>` resolves to a feature that exists and was not skipped
- every **criterion** above the `--requirement-level` threshold is named by some task's
  `<satisfies-criteria>` (item 34), and every id named resolves to a criterion that exists
- every **architecturally-significant** feature is named by a decision record's `**Drives:**`
  field, or carries an explicit no-decision-needed (items 35 and 36, when the design track is on)
- no task exists whose `<source-feature>` is `wont-have`, `excluded` or `superseded` (item 13's
  runtime backstop, and the thing item 21 is being written to measure)

Cheap, because `build-manifest.py` already enumerates the generated files and already refuses on
a manifest that disagrees with them — this is the same check extended from *do the files match
the manifest* to *do the tasks match the PRD*. It is also the general form of item 23's closing
observation: a check that a producer has a reader. Here it is a check that every requirement has
an implementer.

Report the shortfall by name. "4 must-have features have no task" is the sentence, in the idiom
of item 15.

**31. Derive the layer set from content, on both paths. No threshold.**
*Addresses P21 and P33. Rewritten: the earlier version proposed a `--small` flag with a file-count
threshold, and the threshold was the wrong instrument.*

**A file count is a proxy for effort, and a bad one.** Three files across three unrelated
subsystems is not a small change; twelve files that are one regenerated client is. And effort is
not even the question layering answers. Layering answers **does this change span dependency
tiers** — is there a model that must exist before an endpoint, before a screen? That is a question
about *what the change touches*, and the CRD path already answers it from exactly that (P33).

So there is no threshold to set, and nothing to own. Three changes:

- **Extend the CRD derivation to the PRD path.** A layer appears when the work requires it: a
  foundation layer when there are schema changes, a backend layer when there are endpoints, a
  frontend layer when there are components. The PRD path currently takes all five unconditionally,
  so a PRD with no frontend gets a frontend layer and a batch that generates nothing worth having.
  Item 28 supplies the layer graph; item 27's `<depends-on>` supplies the edges; this supplies the
  rule that a tier with no work in it is not a tier.
- **Delete "always include Layer 4."** Integration exists to wire tiers together, so it earns its
  place when **more than one tier is present**, or when a requirement is explicitly cross-cutting.
  A single-tier change has nothing to integrate, and forcing the layer on it is what makes the
  minimum plan two layers instead of one.
- **Collapse the degenerate case.** When the derivation yields **one layer holding one task**,
  there is no plan to make: run the task. This is the "skip layering" the earlier version tried to
  buy with a flag, arriving instead as a consequence of asking the right question.

**Two different decisions, kept apart.** *Skip layering* when the change spans one tier. *Skip
batching* when a layer holds few enough tasks. Twenty endpoints in one tier is a large change that
needs no layering and still wants batching, and a threshold on files would have got it backwards.

**`<scope>` is demoted from routing input to a reported cross-check.** It keeps its value without
being authoritative: *"impact analysis said `small`, breakdown produced 14 tasks"* is worth
flagging as a sign that the analysis or the generation is wrong. It is not worth *routing* on,
because the derivation above already knows more than a band boundary does.

The routing decision is still reported rather than silent — an operator who expected four tasks
and got one must be told why. That was right in the earlier version and survives the rewrite.

**32. Make the task set reviewable without reading every task.**
*Addresses P22. Cheap, and worth doing early.*

Nothing here changes the task format — self-containment stays, because it is right for the
consumer. What is missing is a view *over* it:

- **A rendered summary generated alongside the task files**: one row per task with its
  `<source-feature>`, `<moscow>`, objective and file list. `build-manifest.py` already walks every
  generated file and already reads each task's declared name, so this is an output format on a
  traversal that exists, not a new pass.
- **Diff the derived content, not the whole file.** What a reviewer actually needs to check is
  whether the criteria a task carries match the feature they came from; item 17's verbatim
  criterion ids turn that from a read-through into a set comparison, which item 30's script can
  do mechanically.

The general point is that every other item in this plan adds fidelity — more content carried,
more faithfully — and the review burden scales with it. A summary view is the cheapest thing that
keeps a human able to check the result at all.

### I. Requirement format, design, and decisions

Seven items from the study of Kiro's open-source spec formats and from the conventions of the
project the sample corpus came from. Items 33 and 34 change the criterion schema and everything
in A–H that touches criteria inherits from them; 35–38 are a design track that is **off by
default**; 39 stands alone and is worth doing regardless.

**33. Adopt EARS as the criterion format, replacing Given/When/Then.**
*Addresses P23.*

```xml
<criterion id="1" pattern="event-driven" priority="P0">
  When a user submits a response, the system shall persist it and return a confirmation.
</criterion>
```

`pattern` is one of the six EARS patterns: `ubiquitous`, `state-driven`, `event-driven`,
`optional-feature`, `unwanted-behaviour`, `complex`. `priority` is item 34.

**Replace rather than measure against.** The alternative considered was keeping GWT and scoring it
against the EARS taxonomy. That is incoherent: the checker would flag the absence of patterns the
format cannot express, and P23 shows the corpus has zero `optional-feature` criteria for exactly
that reason. If EARS is the right taxonomy for judging coverage, it is the right format for
writing it.

Three further reasons, in descending order of weight:

- **The `pattern` attribute makes §4.2's definition mechanical.** "Covers the edge cases" becomes
  an attribute count rather than a judgement or a keyword heuristic. This is the single thing item
  3 has never been able to check.
- **The schema is being rewritten anyway** by items 1, 2, 5, 16, 17 and 35. Migrating once, now,
  is cheaper than migrating later against more content.
- **It is less verbose than a GWT triple**, which is a small credit against P22.

**Migration is the risky part, and it gets its own rules.** 550 criteria rewritten by a model is
exactly the shape of change that loses meaning quietly.

- Per feature, never per corpus. Reviewed as a diff, feature by feature.
- Criterion count in equals criterion count out. Each migrated criterion carries
  `derived-from="{{old id}}"` until the migration is signed off.
- `pattern` is **assigned by the migrator**, not inferred afterwards by a checker. A pattern
  attribute derived by the same heuristics it is meant to replace would be circular.
- Every existing criterion is event-shaped by construction, so the mechanical part is large and
  the judgement is concentrated: the work is finding requirements that are *actually* ubiquitous
  or state-driven and were forced into an event shape. **A count cannot find those** — which is
  the argument for a per-feature human diff rather than a bulk pass.

**34. Priority on every requirement, and a threshold to select by.**
*Addresses P1's residue. Closes open question 4.*

Two levels, deliberately in different vocabularies so that no flag, report line or conversation
is ambiguous about which one it means:

| Level | Where | Vocabulary | Selects |
|---|---|---|---|
| Feature | `priority=` on the index entry (§4.1) | MoSCoW | which features are in scope |
| Requirement | `priority=` on the criterion | `P0` / `P1` / `P2` | which criteria within them are built |

`/breakdown` gains `--requirement-level <P0|P1|P2>`, applied **after** item 14's `--priority`.
Default `P2` — everything — so no existing invocation changes behaviour. Unassigned criteria
default to `P1`, and item 6 reports the unassigned count: a corpus where everything is `P0` says
nothing, and neither does one where nothing is set.

**Why this closes open question 4.** We measured 9 of 13 must-have features carrying cross-tier
references, 49 in total, which made a `--priority must-have` set open rather than closed.
Criterion-level priority changes what closure costs: a must-have that depends on a could-have
pulls in **that feature's `P0` criteria**, not the whole feature. The tier boundary stops
collapsing under its own dependencies, and "what does this filter actually build" becomes a
computation rather than a guess.

The residual cost is real: someone assigns a level to 550 criteria. Item 33's migration is the
moment to do it, and item 8's agent can propose while a human accepts.

**35. `<architecturally-significant>` — the flag that makes a design step affordable.**
*Addresses P25. Prerequisite for 36 and 38.*

```xml
<architecturally-significant
    because="quality-attribute|risk|first-of-a-kind|cross-cutting|external-dependency|constraint"
    criteria="3,7"/>          <!-- optional: which criteria drive the significance -->
```

In the feature file's `<meta>`, because significance is a property of the requirement's nature
rather than of its place in the plan.

The literature's non-obvious point is the one to encode: **not all non-functional requirements are
architecturally significant, and some functional requirements are.** So this cannot be derived
from a `<non-functional>` section or from any structural property — it is a judgement, which is
why it is a declared flag rather than a query.

Item 6 screens for candidates using the published heuristics — requirements specifying quality
attributes, defining core features, imposing constraints, or describing operational environments —
and reports them as candidates, three-valued like item 3, **never applied automatically**.

Without this flag a design step is unaffordable, because it would run across all 64 features
rather than the handful that warrant one. That is the whole reason item 38 is tractable.

**36. The decision record: adopt the corpus project's template and conventions wholesale.**
*Addresses P24 and P25.*

The project the corpus came from already has **19** of these and a settled house style. **It is
adopted as-is rather than redesigned**, and the check reads the convention that exists rather than
asking for a migration: `**Status:**` and `**Date:**` are already regular bolded fields, and links
to features and other records are already regular markdown.

Sections, in order: **Context** (what exists, with links; what has accumulated against it, one
bolded lead-in per pressure) → *The Problem* (optional) → **Options Considered** (each with Pros
where they exist, Cons, and a **Verdict**) → **Decision** (a single bolded sentence, then the
mechanics) → *Scope Boundary* (optional) → **Rationale** (prose, not a summary of the Cons) →
**Consequences** (what changes in `index.md` or a feature file, concretely enough to act on).
Titles state a claim, not a topic.

Three conventions come with it, and each earns its place:

- **`Status: Accepted` on every current record.** Supersession amends the old record's status
  line and never rewrites its decision. This is the same principle as §4.2's `superseded` feature
  status, arrived at independently — which is a good sign for §4.2.
- **Resolved questions are annotated in place**, as a heading naming what resolved them and when.
  This is also the answer to a question item 29 leaves open: a resolved `<needs-clarification>`
  should be annotated, not deleted.
- **No rejected alternatives means it is not a decision record** — it is a principle. See item 37.

**One addition to the template: a `**Drives:**` field.**

```
**Drives:** [Feature Name](../../prd/{{slug}}/features/{{feature-slug}}.md), [Another](...)
```

A third bolded field in the style of the two that already exist. It is what lets item 30 and item
38 assert something real — *every architecturally-significant feature is named by some record, or
explicitly needs no decision*. That is derivable today from the Context links, but those are
load-bearing by accident rather than by declaration, and they will drift. A declared field is the
difference between a check that holds and one that erodes.

**Where the template lives.** The plugin ships it as a default reference; `architecture.md`'s
`<rules>` may point at a project's own. Shipping ours as unoverridable would be a sixth vendored
opinion (P18) — and this template came from a project rather than from the plugin, which rather
makes the point.

**Off by default**, with the rest of the design track:

```xml
<design-track enabled="false" adr-dir="../../architecture/decisions"/>
```

`adr-dir` points outside the PRD deliberately. Decision records outlive the PRD that prompted
them, which is why the corpus keeps them in a project-wide directory and why item 25 already
said ADRs stay where they are and are cited by pointer.

**37. Decision, principle, constraint — a test for which one you are writing.**
*Sharpens items 25 and 28. Addresses P16's boundary.*

| Kind | Test | Home | Enforced? |
|---|---|---|---|
| **Decision** | has rejected alternatives to record | a decision record (item 36) | no — it is a record |
| **Principle** | a rule, with no alternatives weighed | a `<principles>` section of `architecture.md` | no — it is guidance |
| **Constraint** | the toolchain must obey it | `<rules>` in `architecture.md` (item 28) | **yes — exit code** |
| **Advisory** | stated, checked, but not decidable by comparison | `<rule kind="judgement">` (item 56) | reports, never refuses |

The fourth row is the one A4 added. It exists because `<banned>` turned out to carry rules of both
kinds, and collapsing them would have meant either dropping the undecidable ones or claiming
enforcement the toolchain cannot deliver — P16's failure mode, chosen deliberately.

**Principles live inside `architecture.md`, not in a file of their own.** Item 28 already rejected
a separate `PRINCIPLES.md` — three files describing one project — and an earlier draft of this
table then routed principles to exactly that file, so the plan named a destination it had declined
to create. A `<principles>` section sits beside `<rules>` in the same artefact, **outside** it and
explicitly non-enforced: `<rules>` is what a script obeys, `<principles>` is what a reader is told.
Keeping them in one file and distinct within it is the whole point of the row above.

The test in the first column comes from the corpus project's own conventions. Items 25 and 28
currently blur the second and third rows, and that blur is dangerous in exactly the way P16
describes: something written as a principle when it needed to be a constraint will be weighed
rather than obeyed, while the operator believes it is in force. That is item 28's own stated
failure mode for a silently-ignored rule file, arriving one level earlier.

It is also where this toolchain is ahead of the field by design rather than by accident: Kiro's
steering collapses all three kinds into one undifferentiated prose channel.

**38. A gate between `/breakdown` and `/execute`.**
*Addresses P25. Depends on 30, 35 and 36.*

**Placed at that boundary and nowhere else.** Not inside `/execute`, which is the unattended
overnight case P19 correctly refuses to block. `/breakdown` and `/execute` are already separate
invocations, so an approval between them costs nothing at 2am — and item 30's coverage check
already runs exactly there, which makes the gate a report-and-confirm over work that is happening
anyway rather than a new phase.

It asserts, and reports by name:

- every feature above both thresholds has at least one task (item 30)
- every architecturally-significant feature is named by a record's `**Drives:**`, or carries an
  explicit no-decision-needed (items 35, 36)
- no blocking `<needs-clarification>` remains (item 29)

With `<design-track enabled="false">` it prints the report and returns. With it enabled, it
requires confirmation. **The report is the valuable half** — the confirmation only matters if
somebody is there, but the three assertions are worth running either way.

**39. Validate the references that leave the PRD.**
*Addresses P24. Extends item 22.*

Every `ADR-NNN`, `OQ-NNN` and principle citation resolves to a file that exists; a citation of a
superseded record is reported together with its successor; every `**Drives:**` link resolves to a
feature that exists.

**The open-questions register is human-maintained, and the toolchain only validates it. Decided.**
Item 40 makes it the required home for any unknown binding more than one feature, and no item
creates or maintains one — which read as an oversight and is a choice. A register is a product
artefact with a life longer than any PRD, and a toolchain that generated entries into it would be
writing into a document it does not own. So: validate that citations resolve, report a citation of
a question already closed, and never write. *Stated here because a consumer with no producer should
be deliberate or fixed, and this one is deliberate.*

**Principle citations are excluded, and the exclusion is the honest part.** A principle has no
home until item 28 gives `architecture.md` its `<principles>` section (item 37), so there is
nothing for a citation to resolve against and validating one would assert a file that does not
exist. That is 10 of the 190; the other **180 are checked**, and the script says which it skips
rather than skipping quietly. The remainder lands with Phase 3, not here.

Cheap, and **190 references currently go unchecked**. This is also the minimum that makes the
decision-record track useful even if 35, 36 and 38 are never switched on: a dangling reference in
a feature that `/breakdown` is about to turn into tasks is a defect whether or not the design
track is enabled.

**40. The well-defined bar, as a gate on the `defined` label.**
*Addresses P26, and gives §4.2 the review it has always implied. Adapted from a policy written for
a separate project built with the original commands — so it is tested against real use, not
designed here.*

§4.2 says what `defined` means in a sentence. This is that sentence as **seven tests that can be
applied one at a time**, split by what a script can settle and what needs a reader.

| # | Test | Mechanical? |
|---|---|---|
| 1 | Scope states what the feature owns **and what it does not**, naming the feature that holds each excluded part | no |
| 2 | Each distinct failure mode has its own criterion — and each pair of states that must stay distinguishable | **yes**, via item 33's `pattern` |
| 3 | Strike out every criterion that exists only to serve another feature; what remains still describes this one | no |
| 4 | A data model, including **what is deliberately absent** and where it lives instead | partly — presence only |
| 5 | External dependencies as providers with roles, not brand names; and what they gate | partly — presence only |
| 6 | Cited decision records are **discharged**, not merely cited: their obligations appear as criteria | partly — citation vs criteria |
| 7 | A relationships list **in both directions** — outbound and inbound | **yes** |
| 8 | A `<user-story>` naming an actor, a capability and a **benefit** — where the actor may be a consuming feature | partly — shape is mechanical, substance is not |

Test 7's inbound half is the one that gets skipped and the one that catches contract gaps, which
is why it is mechanical and why it is worth running first.

**Test 8 has one cheap screen and no more.** A story degrades into *"As a user, I want X, so that I
can X"*, and the tautology is catchable: **the "so that" clause must not merely restate the "I
want" clause.** That is crude, it catches only the worst case, and it is worth having because the
worst case is the common one. Everything beyond it — is this a real benefit, is this the right
actor — is judgement, and sits with tests 1 and 3.

**The contract rule is the highest-yield check, and it is a script.** *Every expectation another
feature places on this one must be discharged by something in this one.* Grep the feature's slug
and display name across the PRD, read each hit as a claim someone is relying on, and report the
ones this feature does not answer. On the corpus that is 93 one-way edges to triage rather than
231 to read. **When it finds a gap, the fix belongs in the owning feature** — weakening the
consumer's claim to match an under-specified owner loses a requirement that had a reason.

**Two tiers, matching the plan's existing machinery.** The mechanical tests go into item 6, as
exit codes. The judgement tests go to item 8's agent, which gains a second mode: it already needs
the feature, its neighbours and its decision records loaded to propose criteria, and that is
exactly the context a definition review needs. One agent, two modes — `propose-criteria` and
`review-definition` — rather than two agents loading the same thing twice.

**The gate itself:** a feature cannot be *labelled* `defined` until the mechanical tests pass and
a review has been recorded. Item 6 reports; the label is the author's to set. This is deliberately
weaker than refusing the label, because §4.2's own principle is that a wrong status usually signals
wrong *content*, and a gate that blocks the label invites relabelling rather than fixing.

**Three conventions come with the bar**, and each closes a hole the plan had left:

- **Unknowns are not under-definition.** A feature need not have every answer; it must know which
  answers it lacks and record each in the place that makes it findable — a spike where
  investigation settles it, the open-questions register — **human-maintained; the toolchain
  validates citations and never writes entries (item 39)** — where the question binds more than one
  feature, or a `<gap>` where this feature owns it and can close it alone. *Prose in one feature is
  not a place other features can be expected to look.*
- **What does not belong in a feature file**, all three checkable by item 6: priority argument
  (features do not settle their own priority, or each other's), restated status (the tag is the
  single source and prose about it drifts), and task lists (a bounded pointer to work in flight is
  legitimate, and is removed by the commit that completes it).
- **Moving a boundary has an order**: decide it in a decision record *before* writing the feature,
  write the feature against it, then sweep every consumer in one pass, and split the commits by
  concern in that order. The record is committed first and the forward reference stated, because a
  feature whose rationale rests on nothing is worse than a decision whose link resolves one commit
  later. An ADR is owed only where the boundary is **contested or moving** — the signal is having a
  rejected alternative worth recording, which is item 37's test arriving from the other direction.

**The anti-patterns are the review's checklist**, each observed rather than imagined:
neighbour-authored criteria; ownership asserted rather than drawn; a decision record discharged by
citation; a consumer without a counterpart; providers named as websites; a data model living in
the neighbour that uses the entity; status frozen at birth; uncertainty parked in prose.

**One thing the bar deliberately does not do: touch priority.** Definition completeness and MoSCoW
are orthogonal — a could-have can be fully defined and a must-have can be a sketch, and the corpus
contains both. A feature is never promoted because it is well written, nor elaborated only as far
as its priority seems to justify. That is §4.1 and §4.2's separation, arrived at independently by a
different project, which is the best evidence available that the split is right.

**41. A migration guide an agent can execute.**
*Required by items 1, 2, 5, 11, 33, 34, 35 and the `<gaps>` adoption in 29. Nothing in §5 A or
§5 I can land without it.*

Every schema decision in this plan implies rewriting artefacts that already exist — on this corpus,
64 feature files, 550 criteria, an index and a `what-next.md`. That work will be done by an agent,
so the guide is not prose for a human to follow: it is **a specification with a consumer**, and it
is subject to the same discipline this plan applies to every other producer/consumer pair.

**It covers the CRD path too, which this item did not say until §5 J existed.** Seven items in that
section change artefacts that are already written, and a migration scoped to PRDs would leave every
existing CRD and `PROJECT.md` behind:

| Artefact | Transformation | Item |
|---|---|---|
| `docs/crd/{slug}.md` | `<requirements>` retired; each becomes an EARS criterion in the single list | 46, 33 |
| | requirement `priority` MoSCoW → `P0\|P1\|P2` on the criterion | 47 |
| | `<meta>` gains a document-level MoSCoW `<priority>` | 47 |
| | `<meta><status>` → `<workflow>` | 45 |
| | deferred criteria become `<gap kind="specification">` | 48 |
| | `<affected-apis>` → `<affected-contracts kind="api">` | 57 |
| `PROJECT.md` | `<feature status=>` → `built=` | 45 |
| | registries stay at root; **none is added or removed by migration** | 25 |

**Two CRD-specific rules.** A CRD whose `<workflow>` is `complete` or `abandoned` is **migrated but
not re-reviewed** — it is a record of something that already happened, and rewriting its criteria
into EARS is a formatting change, not a re-specification. And `<affected-apis>` is **accepted on
read** for a full release after the migration, because a CRD is often authored in one place and
broken down in another, and a hard cutover would strand the ones in flight.

What it must contain, per schema change:

- **Preconditions** — what must be true of a file before the transformation applies, so a partly
  migrated tree is safe to re-enter.
- **The transformation**, stated as a rule over the old shape rather than an example of the new
  one. `<priority>` is deleted only after the index entry is confirmed to carry it (item 1);
  `<notes>` prose becomes `<data-model>` / `<considerations>` — two, not three (item 2) — with
  **unrecognised content going to `<considerations>` verbatim, never dropped** (item 2).
- **Postconditions and invariants**, checkable without judgement. Criterion count in equals count
  out (item 33). Every migrated criterion carries `derived-from`. No feature gains or loses a
  status. `<gaps>` lands between `</acceptance-criteria>` and `<notes>`.
- **What must not be migrated mechanically**, named explicitly: assigning item 33's `pattern`,
  assigning item 34's `priority`, and deciding item 35's significance flag are all judgements. The
  guide's job is to stop an agent guessing them, not to help it.
- **Escalation** — what to do when a file does not match any precondition, which is *stop and
  report this file*, never *transform it anyway*.

Three properties the guide itself must have:

- **Idempotent and resumable.** A 65-file migration will be interrupted. Re-running must be safe,
  and the marker of "already migrated" must be in the file rather than in a side-car that can drift
  from it.
- **Per-file, reviewed as a diff.** Never a bulk pass. This is item 33's rule generalised, for the
  same reason: a silent semantic loss across dozens of files is the failure mode, and only a diff
  catches it.
- **Versioned against `toolchain_version`** (item 24), so an artefact stamped by an older toolchain
  selects the right migration rather than the newest one.

### What it costs, and what happens if it stops (A9/R14)

The migration is the precondition for items 1, 2, 11, 16, 17, 30, 35 and 40. **If this plan dies in
execution it dies here**, and "idempotent and resumable" is not a cost estimate.

**Three judgement axes, not four.** §4.3 removed one: `<relationships>` is dropped and `<notes>`
becomes a two-way split keyed on a heading convention that already measures at zero false
positives (item 2). What remains:

| Judgement | Count | Axis | Mandatory in the pass? |
|---|---|---|---|
| `pattern` on each criterion | 550 | six-way | **yes** — it is the format |
| `priority` on each criterion | 550 | three-way | **no** — see below |
| `<architecturally-significant>` | 64 | six-way `because=` | no — item 51's Design phase |
| `<user-story>` | 34 | prose | no — new content, drafted by item 8 |

**Priority defaults to `P1` in the migration pass and is refined afterwards.** Item 34 argued for
doing it together because *"the criterion is being touched anyway"* — sound for *when*, and silent
about *how much*. Two six-hundred-item judgement axes on one critical path is how a migration
stalls. `pattern` is not optional because it *is* the new format; `priority` is a planning
judgement that can follow, and item 6 already reports the unassigned count so the debt is visible
rather than forgotten.

**The partial-completion contract, stated properly.** *Per-file atomic*: a feature file is either
fully migrated or untouched, never half-written — so an interrupted run leaves a tree where every
file is valid under one schema or the other. *Marked in the file*: `schema_version` in the feature's
own `<meta>`, not in a side-car that can drift. *And `/breakdown` refuses a mixed tree*, naming the
count — `REFUSED: 30 of 64 features migrated`. Supporting mixed input would mean two readers for
every element, which is the drift item 44 exists to prevent.

**If the review stops at feature 30 of 64**, the answer is that nothing is broken and nothing is
blocked except `/breakdown`, which says so. The tree is valid, the migrated files are correct, and
the work resumes where it stopped. That is the whole benefit of per-file atomicity, and it is worth
more than any estimate.

**A per-feature estimate belongs in this item and cannot be written from here.** Take it from the
first ten features migrated, and revise the plan if the number is bad. Item 21's authoring measure
(§4.3) is the same instrument pointed at a different question, and both are cheap because the
fixture is already there.

**And it needs a checker**, or it becomes P10 in a new place: a script that reads a migrated tree
and asserts the postconditions above. **Item 43 supplies a stronger one** — a golden pair of
fixtures, the same project in the old schema and the new, so the migration is verified by
*comparison* rather than by a list of properties somebody remembered to assert. Keep the
postcondition script for the real corpus, where there is no golden output to compare against, and
use the pair to test the script itself. Writing a migration spec with no verifier, in a plan whose
central finding is that this repository ships producers without readers, would be the most
embarrassing possible outcome.

**42. A rename operation, and the postcondition that proves it finished.**
*Addresses P27. Small, and the cheapest possible test of item 41's machinery.*

`/prd --rename <old-slug> <new-slug>`, doing every edit a slug requires: the filename, `<slug>`,
the index entry's `file=` attribute, `what-next.md`'s `ref=`, and every inbound cross-reference in
every other feature file.

**Corrected while building it: that is six sites, not the five listed here, and one of the five
was wrong.** `what-next.md` carries `ref="features/{slug}.md"` and was missing from the list —
found by running the operation against the §5.1 fixture rather than by re-reading. And *"the index
entry's content"* is prose, not a reference: the `<name>` and `<summary>` may mention the old slug
in a sentence, and a script that rewrites English is a worse failure than a stale sentence. Prose
mentions are **reported with file and line, never rewritten**, which is the same
refuses/reports split item 39 draws.

**The postcondition is the whole point.** The rename that prompted this item was done correctly,
across 20 references in 8 files, and produced no evidence of that fact — which is the actual
problem. A refactor that is right by care and unverifiable by construction is one distraction away
from being wrong and silent:

- no reference anywhere resolves to the old slug
- no file exists under the old slug
- the new slug appears in exactly one index entry and one file

Assert those three and a residue becomes impossible rather than merely unlikely. Item 6 runs the same assertions over the whole
PRD, so a rename done by hand is caught even when the command was not used — which matters,
because the command will not always be used.

**And roll back when one fails, which is the finding this rehearsal was for.** Asserting a
postcondition *after* writing, and then reporting the failure, leaves a half-done rename plus a
message — worse than not starting, because the operator now has to work out how far it got. The
operation snapshots every file it will touch, restores them all on failure, and then **asserts the
restore**: an unverified undo is the same class of claim as the unverified rename the item exists
to replace. Item 41's per-file atomicity across 64 files is this shape, and it was cheaper to
learn on 8.

Two things to carry rather than lose. A rename should leave a record: the decision to re-slug a
feature is a decision, and where the rename accompanies a change of scope it is a decision record
(item 36), not a silent file move. And a rename is not a supersession — §4.2's `superseded` status
is for a feature *merged into another*, and using it for a rename would claim two features existed
where there was always one.

**43. A fixture per schema version, and the golden pair it creates.**
*Addresses P28. Unblocks item 1, and gives items 24 and 41 the tests they currently cannot have.*

`tests/fixture/prd/` gains a directory per schema version — `schema-1/link-shelf/`,
`schema-2/link-shelf/` — **the same project, the same three features, expressed in each schema.**
Keeping the project identical across versions is the entire point; the difference between two
fixtures must be the schema and nothing else.

**Introduce an artefact schema version distinct from the plugin version** (P28). Artefacts stamp
both: `toolchain_version` for provenance, `schema_version` for compatibility. Item 24's comparison
reads the second. The first cannot answer the question it is being asked, because a patch release
changes it without changing anything about how an artefact should be read.

**It also gives the graph validator something to validate against.** P35 makes `<layers>` a DAG
with comma-list edges and optional per-directory instantiation, all hand-written. The fixture pair
is where *acyclic, every layer reachable, no task stranded* is exercised on a graph somebody
actually wrote rather than on the shipped default.

**Three things become testable that are not testable today:**

- **Item 41's migration gets a golden test.** Run the migration over `schema-1`, assert the result
  equals `schema-2`. That is a far stronger check than the postcondition list item 41 specifies,
  because it catches losses nobody thought to assert — and item 41's own closing line is that
  shipping a migration with no verifier would be the worst possible outcome.
- **Item 24 becomes exercisable at all.** "Warn on mismatch, refuse on a known incompatibility"
  cannot be tested without an artefact of an older schema, and no such artefact exists anywhere in
  the repository. As specified, item 24 is currently unfalsifiable.
- **Backward-read behaviour gets pinned.** Whatever `/breakdown` should do when handed an older
  PRD — migrate it, refuse it, or read it — becomes a decision with a test rather than an
  assumption.

**It also removes a sequencing blocker nobody had noticed.** The regression suite asserts that the
fixture PRD is valid and self-consistent, and the fixture is written in the current schema. Without
this item, **item 1 cannot land without breaking the suite in the same commit**, and the same is
true of items 2, 5, 11, 33, 34 and 35. With it, each lands by *adding* a `schema-2` fixture beside
the existing one, and the suite stays green throughout.

**Bound the set, or it rots.** Two rules:

- **One fixture per schema version the toolchain still claims to accept.** Dropping read support
  drops the fixture. Without this the directory grows for ever and most of it is decoration.
- **A non-current fixture is frozen.** It changes only when the migration's expected output
  changes. If the fixture project needs a fourth feature to exercise something new, that is a
  reason to touch the current schema only — otherwise the same project is being maintained twice,
  which is the cost that makes people abandon versioned fixtures.

The older fixture is not decoration under these rules: it is the *input* to the migration test and
to item 24's comparison, so it is exercised on every run rather than merely stored.

### J. Parity between the two paths

Seven items, from reading the `/crd` command, its three sub-skills, its four agents and both format
references against everything above. The goal is **parity of capability and a shared schema wherever
the two paths overlap** — not one path absorbing the other.

#### Who is ahead where

This is the ledger "best of both" has to be built from. The PRD path is not the better of the two;
it is the more thoroughly examined one, which is a different thing.

| Concern | PRD path | CRD path | Take from |
|---|---|---|---|
| Acceptance criteria have a consumer | **no** (P2) | **yes** — `breakdown` reads them | **CRD** |
| Architecture / structure context | none (P17) | `PROJECT.md`, generated and maintained | **CRD** |
| Change size recorded | none (P21) | `<scope>`, with a stated rubric | **CRD** |
| Uncertainty recorded | none (P19) | `<confidence>`, required | **CRD** |
| Priority stored once | duplicated (P8) | single, on the requirement | **CRD** |
| Status values documented | undefined (P7) | a transitions table | **CRD** |
| Data model / rationale | `<notes>` (unread, P4) | **nowhere at all** | **PRD** |
| Deferral of unfinished work | `what-next.md`, `<gaps>` | **nothing** (P32) | **PRD** |
| Resume of an interrupted interview | `--resume`, pre-write guard (F3) | **stateless, none** (P32) | **PRD** |
| Requirement-level granularity | criteria only | requirements **and** criteria (P31) | *see item 46* |
| Design step | none (P25) | `<impact-analysis>` — a partial one | **CRD** |
| Layer set chosen by content | no — all five, unconditional | yes, from impact (P33) | **CRD** |

Five of the six things this plan spent its first forty items building for the PRD path already
exist on the CRD path in some form. **Anything below that reads as "add X to CRD" should be checked
against this table first**, because the more common direction is the other one.

**44. One schema core, included by both paths.**
*Addresses P30. Precondition for 45–50, and for items 33, 34 and 29 landing on both paths.*

Extract the elements both paths use into a single reference that each cites rather than restates:
`<criterion>` (item 33's EARS shape, with `pattern` and `priority`), `<gaps>` (item 29), the status
vocabularies (item 45), traceability identifiers (items 16, 30), and `<scope>` and `<confidence>`
(item 49).

Three consequences worth stating:

- **`/prd`'s templates stop living inside a command file.** They are schema, and schema in a
  command cannot be cited by a skill. This is the same mistake in a different register as `<notes>`
  having no reader: a definition nobody can reference gets copied instead.
- **The task schema cites the core too**, so `<satisfies-criteria>` means the same thing whether the
  task came from a feature or from a change request.
- **The core carries the `schema_version`** (item 43), so both paths version together. Two paths
  versioning independently would need a compatibility matrix, and there is no appetite for one.

**45. Three status vocabularies, three distinct names.**
*Addresses P29. The first decision, because everything else hangs off it.*

The three tags record genuinely different things, so they should not be merged — they should stop
sharing a word:

| Now | Becomes | Records | Values |
|---|---|---|---|
| PRD feature `<status>` | `<definition>` | how completely specified | `tbd`, `in-progress`, `defined`, `excluded`, `superseded` |
| CRD `<meta><status>` | `<workflow>` | where in the process | `draft`, `ready`, `in-progress`, `complete`, `abandoned` |
| PROJECT.md `<feature status=>` | `built=` | how much exists in code | `complete`, `partial`, `planned` |

Renaming is cheap now and expensive later, and it removes the class of bug where a script reads the
right tag from the wrong file. §4.2's warning that `in-progress` reads as build progress stops
being a warning once the tag is called `<definition>`.

> **The rename is deliberately not propagated through this document, and that is stated rather
> than left to be noticed (R7).** Every schema passage in §4 and §5 still says `<status>`, because
> each is specified against the tag *as it exists today* — a plan describes a change from something
> to something. Propagating the new name into items 1, 3, 4, 6, 13, 15 and §4.2 **is this item's
> own work**, not a precondition for reading them.
>
> [`target-state-data-flow.md`](target-state-data-flow.md) uses `<definition>` throughout, correctly:
> it draws the end state, where this item has landed. The two documents are in different tenses, and
> a reader comparing them should expect exactly this difference and no other.

**`in-progress` stays. Decided.** Retiring it was considered, on the grounds that item 29 makes it
derivable from the presence of a `<gap kind="specification">`. It is not derivable, and the reason
is the useful one: **an author may want to hold a feature short of `defined` for reasons the file
cannot express** — a review not yet run, a boundary they expect to move, a sense that the criteria
read thinner than they count. Removing the value would remove the ability to say so.

The guard survives without the biconditional, and runs one way: a `defined` feature must not carry
a `specification` gap. That catches the contradiction — claiming to be fully specified while
declaring an incomplete specification — and leaves every softer judgement with the author. §4.2
carries the same rule; item 3 implements it as a ceiling rather than an equality.

**46. EARS collapses the CRD's requirement/criterion split.**
*Addresses P31. Depends on item 33.*

A CRD carries `<requirements>` *and* `<acceptance-criteria>` as separate, unlinked lists. The PRD
path carries only criteria. The split exists because Given/When/Then is a **scenario** format that
cannot state a requirement — so a second list was needed to hold the requirements themselves.

Item 33 removes the reason for the split. An EARS criterion **is** a requirement: *"When the user
toggles the theme, the system shall persist the preference."* So:

- CRD `<requirements>` is retired, its entries becoming EARS criteria in the shared core (item 44)
- criteria gain `priority` (item 47) — the attribute requirements had and criteria lacked, which is
  what made priority filtering select nothing on the CRD path
- the unlinkable pair becomes one list with one id space, so P31's coverage question — *which
  criteria discharge requirement 3?* — stops being unanswerable by becoming meaningless

**The one genuine structural incompatibility, and it is decided in EARS's favour.** The resolution
deletes a CRD concept rather than adding a PRD one. The alternative — giving PRD features a
`<requirements>` layer above their criteria — was considered and rejected: it adds a level to 64
features to accommodate a split that exists only because of a format both paths are leaving.

Recorded rather than buried, because this is the item most likely to be questioned later by someone
who reads the CRD schema first and sees a layer being removed. The answer is that the layer was
never carrying meaning of its own — it was carrying the requirements that Given/When/Then had no
way to state.

**47. Requirement-level priority is `P0|P1|P2`, on both paths.**
*Extends item 34 to the CRD path. Decided.*

Item 34 chose `P0|P1|P2` for criterion priority on the PRD path specifically so it would not share a
vocabulary with feature-level MoSCoW. The CRD path already has requirement-level priority **in
MoSCoW**, so landing item 34 unchanged would give the toolchain two vocabularies for one concept —
exactly what item 29 refused when it retired `<needs-clarification>` rather than run it beside
`<gaps>`.

**Resolution: `P0|P1|P2` everywhere a requirement is prioritised, on both paths.** CRD requirement
priorities migrate from MoSCoW under item 41. MoSCoW survives only where it is a *portfolio*
judgement across items — which on the PRD path is the feature, per §4.1.

**A CRD carries a document-level MoSCoW. Decided.** Change requests compete for attention the way
features compete for a release, and `--list` already exists to survey them — a listing that cannot
show tiers is a worse listing. So `<meta>` gains a MoSCoW `<priority>`, giving the CRD path the
same two-level shape as the PRD path: MoSCoW for *which work*, `P0|P1|P2` for *which parts of it*.

**This is §4.1's rule, not an exception to it.** The rule is that feature-level planning belongs to
the index — and for change requests **the document is the unit and there is no index**, so the
document carries it. `--list` is the survey view, derived by scanning, which is what an index would
otherwise have been. The test §4.1 actually applies is *"anything finer than the planning unit
belongs where the thing itself is"*, and here the planning unit and the thing are the same object.

It also makes `/breakdown`'s `--priority` threshold (item 14) mean something on the CRD path, where
today it means nothing: a filter can now decline to break down a could-have change request.

**48. The CRD path gains the PRD's deferral and resume machinery.**
*Addresses P32. Depends on 29 and 44.*

- **`<gaps>` in the CRD**, in the shared shape from item 44. A deferred criterion becomes a
  `<gap kind="specification">` rather than an absence, which also gives the CRD's `<workflow>` tag
  a mechanical test for `draft` versus `ready` — the same move item 29 made for `<definition>`.
- **`--resume`, and a pre-write existence check.** `/crd` is documented as stateless and writes
  `docs/crd/{slug}.md` with no equivalent of `/prd`'s check. F3 was exactly this defect on the PRD
  path, and it cost an interview before it was fixed. The CRD path has the same hole and has not
  been caught by it yet.
- **No `what-next.md` equivalent.** A CRD is a single document about a single change; the deferral
  belongs in `<gaps>` inside it and the next-command line in `<meta>`. *Recorded because the
  symmetric answer — a `what-next` per CRD — is the wrong one.*

**49. The PRD path gains `<scope>` and `<confidence>`.**
*Addresses P19 and P21 from the other direction. Depends on 44.*

Both already exist on the CRD path, both are required fields, and **neither has a reader** — which
is why items 29 and 31 were written as if from nothing. They should be lifted into the shared core
and given consumers on both paths:

- `<scope>` is a **cross-check, not a routing input** (item 31), and a cross-check needs *two*
  pictures. On the CRD path both exist: impact analysis declares a scope, breakdown produces a task
  count. **On the PRD path there was no declared picture at all** — an earlier draft derived
  `<scope>` from the task count *after* breakdown, which is not a prediction to disagree with, and
  which would have had `/breakdown` writing back into the PRD, a mutation nothing else in this plan
  contemplates and §4.1 has no rule for (A5).

  **So `analyze-prd` predicts it, per feature, beside the `<confidence>` it already emits.** Two
  signals from the analyser — *how big* and *how sure* — and the cross-check then works the same way
  on both paths: *"analysis called this small; generation produced 14 tasks"* flags a feature that
  is under-specified or a generator that ran away. Nothing is written back to the PRD; the
  prediction lives in `analysis.json` and the observation in `manifest.json`.

  *A size estimate from a model is soft, and that is tolerable precisely because it routes nothing.*
  It fires on gross disagreement, which is the only kind worth reporting — and item 31 demoted
  `<scope>` from routing for exactly this reason.
- `<confidence>` is item 29's whole-analysis counterpart to a per-item `<gap>`, and item 38's gate
  reads both. **On the PRD path `analyze-prd` produces it, per feature** — it is the component
  doing the analysing, exactly as `crd-impact-analysis` is on the other path, and a per-feature
  confidence says where the analysis was guessing. Without that this item would have given the PRD
  path a field with a reader and no writer.

**50. Parity as a check, not an aspiration.**
*Addresses P30. Extends item 23.*

Both paths drift apart the moment nothing measures the distance. Add to the regression suite:

- every element in the shared core is cited, not restated, by both paths — the `<criterion>`
  double definition is the case that motivates it
- the three status vocabularies are disjoint (item 45), so no value appears in two of them
- both paths produce artefacts carrying the same `schema_version` (item 43)
- a capability present on one path and absent on the other is listed, with a reason — **the ledger
  above becomes a test rather than a paragraph that goes stale**

The last one is the point. Five of the asymmetries this section resolves existed because nobody had
read the two paths side by side, and the plan itself was PRD-only for forty-three items.

**51. A Design phase in `/prd`, between Phase 3 and Phase 4.**
*The producer items 25 and 28 never named. Addresses P17 and P25 at the authoring end.*

Items 25 and 28 specify where `architecture.md` lives, its schema, who reads it, and what happens
to it after `/execute`. **No item said who writes it.** A reader with no producer is the mirror of
this plan's own central finding, and it went unnoticed for twenty-six items.

**Between 3 and 4, and the order is the argument.** After features, so the conversation knows what
is being built. Before dependencies, because Phase 4 asks *"what external services will this
depend on?"* — and dependencies are partly **decided by** the architecture, so asking them first
inverts the causality.

**It opens with a question that can be answered in one word:**

> *"Do you want to discuss architecture for this project, or take the default layering?"*

**Default writes nothing.** The shipped five-tier graph applies, and a PRD with no
`architecture.md` stays a valid PRD — which is what keeps every existing artefact working on the
day item 28 lands, and is the OQ7 mitigation stated as a workflow rather than as a principle.

**Discussing captures all of `<rules>` in one place** — `<layers>`, `<testing>`, `<task-limits>`,
`<banned>`, `<scaffold>`, plus the structure conventions P17 identified as the actual gap (file
organisation, naming, import patterns). One producer, one file, one phase. The alternative
considered was splitting it — conventions at Phase 2 where the stack is chosen, layering here —
and rejected: two producers for one file is how two producers for one file drift.

Three things it must do beyond asking:

- **Read before it writes** (item 52). If `architecture.md` or `PROJECT.md` already exists, the
  question becomes *follow / extend / override* rather than a blank-page interview.
- **Record the choice either way.** "Defaults, deliberately" and "nobody was asked" must be
  distinguishable later, so the default branch still stamps a `<rules>` file recording that the
  default was chosen — or `what-next.md` records that the phase ran and was declined.
- **Feed item 35.** Architecturally-significant features are identified from this conversation, so
  the ASR flags and any decision records (item 36) are its natural output alongside `<rules>`.

**52. A context check at `/prd` initialization.**
*Addresses P34. Mirrors `/crd` Phase 1.*

`/prd` mentions `PROJECT.md` zero times. `/crd` begins by finding it, comparing
`last-context-hash` against `HEAD`, and investigating or updating before anything else. `/prd`
gains the same check, in the same place — beside the existing-PRD scan that F3 added, which is
already exactly this shape of guard.

When a `PROJECT.md` or a project-root `architecture.md` is present, `/prd` says so, and item 51's
Design phase offers **follow / extend / override** instead of asking from scratch.

**A check rather than a flag.** A `--greenfield` flag would let the context be missed by omission,
and project type is already asked in Phase 2 — the check should fire regardless of how that is
answered, because *greenfield* describes the document and not the repository it lands in. A PRD
for a new product inside an existing monorepo is a real and ordinary case.

The cost is one `test -f` and a sentence. The benefit is that the two paths stop disagreeing about
whether knowing the project matters, which is item 50's parity check applied to the thing that
prompted it.

**53. Declare the repository structure, and refuse `multi-repo` at `/breakdown`.**
*Addresses P36. **Decided: multi-repo is out of scope.***

```xml
<repo-structure>single|monorepo|multi-repo</repo-structure>
```

| Value | Meaning | Behaviour |
|---|---|---|
| `single` | one repository, one component | supported; the default when absent |
| `monorepo` | one repository, several components | supported; enables `applies-to` (28) and `cwd` (54) |
| `multi-repo` | several repositories | **refused at `/breakdown`, with the reason** |

**The refusal is the feature.** The assumption is already there and already enforced —
`create-worktree.sh` will not accept a subdirectory — but it fires during batch execution, several
phases after the layout was knowable. A project split repo-per-service currently gets a layer plan,
a manifest and a full task set before anything objects, and then fails with a message about
worktrees that does not name the actual cause. Refusing in Phase 1, in the `resolve-output.sh`
idiom, converts a confusing late failure into an accurate early one.

**Say why, not just no.** The refusal should state what would be needed rather than implying the
layout is wrong: a *target* model with dependencies, so contracts land in one repository before
consumers in another, and an explicit account of the window in which a change spanning three
repositories has merged into one of them. That window is a property repo-per-service **chose** — it
is why those teams version contracts — so supporting it means modelling the window, not removing
it. That is a scope decision comparable in size to §5 I, and it is deliberately not taken here.

*It is not a git limitation, and the refusal should not pretend otherwise.* A repo-per-service
layout would create a worktree per repository, which is ordinary. What is missing is the data
model, not the mechanism.

**54. A working directory for verification.**
*Addresses P36's monorepo half. Small, and needed whatever happens to 53.*

`execute-verify` does `cd {worktree_path}` and nothing more, so every verification command runs
from the repository root. In a monorepo, a task in one package must therefore hand-write
`cd packages/billing && pytest` into each of its steps, and the task format has no working-directory
concept at all.

```xml
<meta>
  <cwd>packages/billing</cwd>     <!-- optional; relative to the worktree root -->
</meta>
```

`execute-verify` and the implementer both honour it. This is where P18's fifth vendored opinion —
*verification is runnable shell commands* — meets repo structure: the opinion is fine, and it
quietly assumed there was one place to run them from.

**55. The ledger states what it verified.**
*Addresses P37. A wording change with a principle behind it.*

`execute-verify` runs each task's **own declared** steps in its worktree before merge — real
verification by a separate agent on a different model, which is more than the field does (S1). The
ledger then records the merge, and a reader supplies the rest.

So record the narrower true thing: **`verified: task-steps`** beside the merge SHA, rather than a
bare completion. In any project with a build pipeline, a task that merges green and breaks CI is
currently indistinguishable from one that did not.

Running the project's pipeline stays out of scope — it belongs to CI, and `/execute` has no
business owning it. What is in scope is not implying it ran. S2 is *"state is derived from git,
never asserted"*; this is the same rule applied to the claim rather than to the count.

**56. Enforce `<banned>` and `<task-limits>`, at both ends.**
*The enforcers item 28 assumed and never named. Item 37 puts `<rules>` in the exit-code column;
these two rows had nothing behind them.*

**`<banned>` was four mechanisms sharing one element name, which is why "is it an exit code?" had
no single answer (A4).** Every rule now carries a **required `kind`**, and the kind decides both
what detects it and whether it can refuse:

| `kind` | Detected by | Refuses? | Fires in |
|---|---|---|---|
| `import` | forbidden symbol × path glob | **yes** | review *and* verify |
| `edge` | dependency graph — module under X importing from Y | **yes** | verify |
| `change` | **the diff against the base branch** | **yes** | verify |
| `content` | regex over file contents at a path | **yes** | review *and* verify |
| `judgement` | a model reading the code | **no — reports** | verify |

**`change` is the kind that made the rest legible.** *"Modifying a published event schema in
place"* is not a property of the code at all — it is a property of the **diff**, and `/execute`
already holds both the base branch and the worktree. It is fully mechanical and it looked
unenforceable only because it was being read as a pattern match.

**`judgement` is a prose guard and is labelled as one.** S3 says prose guards get weighed rather
than obeyed, so these report and never block a merge. A rule that reports is useful; a rule that
claims to enforce and does not is exactly what P16 is about. Item 37's table gains a fourth row for
them.

**Two checkpoints, and the kind decides which apply.**

| Where | Kinds | Catches | Cost of a miss |
|---|---|---|---|
| `review-tasks`, per generated task | `import`, `content` | a task that *specifies* a banned thing | none — no code exists yet |
| `execute-verify`, per implemented task | all five | code that does it anyway | a rejected task, before merge |

Review is primary where it applies, because it is free: a task saying *"call the billing service
over HTTP"* under a rule banning cross-context calls is wrong before anybody writes a line.
`edge` and `change` cannot fire there — there is no dependency graph and no diff until something is
implemented.

**Both report the `reason` verbatim**, which is why item 28 made `reason` mandatory. *"Banned:
HTTP client to another context's service — ADR-004: contexts communicate by event, never by call"*
tells an implementer what to do instead. A bare rule number does not.

**`<task-limits>` is enforced where the limit already lives.** Today `max-files` is a constraint in
`task-format-spec.md` and a critical criterion in `review-criteria.md` — both hardcoded to 3. They
become readers of `<task-limits>`, honouring the scoped overrides. This is the same three-reader
shape item 28 found for `<testing>`: a rule is only overridable if every place that
currently hardcodes it learns to ask.

**A false positive must be answerable — but the answer belongs to the rule, not the instance
(A5).** An earlier draft of this item put an `<exempt pattern= reason=>` in the *task*, and never
said who wrote it. Every candidate producer inside the pipeline is disqualified by the same
argument: **a component that can exempt itself makes the check advisory with extra steps.**
`generate-tasks` would pre-authorise its own violation at authoring time, before anyone knows the
implementation needs it; the implementer would do the same one stage later, in a worktree diff
rather than in a reviewed task. That is exactly what this item exists to prevent, so `<exempt>` is
**dropped**.

Exceptions are declared on the rule:

```xml
<rule kind="import" match="contexts/**" symbol="httpx|requests|grpc" reason="ADR-004: …">
  <except match="contexts/*/adapters/outbound/**"
          reason="third-party APIs are called over HTTP by definition"/>
</rule>
```

*"This rule does not apply to outbound adapters"* is reviewed once, lives in `architecture.md`
where a reader can see it, applies consistently, and composes with the `match=` scoping already
here. *"This task is special"* is unreviewable and accumulates.

**The genuine one-off keeps a route, and it is deliberately the slow one.** A human at item 38's
gate edits the rule. If the rule truly should not apply to that case, editing it is the correct
change; if it should apply, the task is wrong. There is no third answer worth automating.

Two things make this cheaper than it sounds. `judgement` rules report rather than refuse, so
**exemptions concern only the four refusing kinds**. And a one-off is rare by construction — the
rules that generate false positives repeatedly are the ones whose `match=` is wrong, which is a
rule edit either way.

**57. Generalise impact analysis from APIs to contracts.**
*Addresses A3/D3. Depends on item 25's open registry set; without it the open set is an input
nothing can report on.*

`crd-impact-analysis` reads `<api-registry>` and `<schema-registry>` and emits `<affected-apis>`.
Opening the registry set (item 25) lets it *read* an event or command registry and leaves it
**nowhere to report the impact** — half a change, and the half that shows.

```xml
<affected-contracts>
  <contract kind="api"     ref="POST /api/settings">Add theme field</contract>
  <contract kind="event"   ref="OrderPlaced@v2">New optional field; consumers unaffected</contract>
  <contract kind="command" ref="deploy --dry-run">New flag</contract>
</affected-contracts>
```

`kind` matches the registry the contract came from, so the enum extends when the registry set does
rather than being a second list to keep in step — which is the mistake item 25 has just corrected
one level up.

**This changes a published artefact shape**, which nothing else in §5 J does: `crd-format.md`
declares `<affected-apis>` and every existing CRD is written against it. `<affected-apis>` is
accepted on read and rewritten as `<affected-contracts kind="api">` by item 41, which now covers
the CRD path (see there). That is the only part of A3 that is not cheap, and it is the reason A3
reaches into item 41 at all.

Layer selection reads it too: item 31 derives a foundation layer from schema changes and a backend
layer from API changes. With contracts generalised, an **event** contract change is what puts work
in an event-driven graph's `contracts` layer — which is §8.2's first tier and currently unreachable
from an impact analysis.

**58. One table of assertions, and item 6 becomes a caller.**
*Addresses A7/R12. No new checks — the same checks, with an owner each.*

Item 6 had accumulated eleven assertions, and items 22, 39, 40 and 42 each claim some of the same
ground. *"No reference anywhere to a slug that has no file"* is currently owned by four items. The
repository's own idiom is one script, one job, one exit code — `resolve-output.sh`,
`build-manifest.py`, `check-project-md.py` — and item 6 is the first thing in this plan to depart
from it.

| Assertion | Owning script | Invoked by |
|---|---|---|
| Output paths resolve; not inside a plugin | `resolve-output.sh` *(exists)* | `/breakdown` Ph.1 |
| `PROJECT.md` parses; ≥1 `*-registry` | `check-project-md.py` *(exists)* | `/crd` Ph.1, `/execute` finalize |
| Manifest matches the files on disk | `build-manifest.py` *(exists)* | `/breakdown` Ph.5 |
| Artefacts match the shared schema + `schema_version` | `check-artefacts.py` (22, 43, 44) | `/prd` end · `/breakdown` Ph.1 · suite |
| Declared status ≤ derived ceiling; `defined` has no `specification` gap | `check-status.py` (3) | `/prd` Ph.6 · suite |
| `ADR-NNN` / `OQ-NNN` / principle citations resolve | `check-references.py` (39) | `/prd` Ph.6 · `/breakdown` Ph.1 |
| Index ↔ `features/` reconcile; no slug without a file | `check-rename.py` (42) | `/prd` Ph.6 · after `--rename` |
| `<rules>` parses; `<layers>` acyclic and reachable | `check-rules.py` (28, 43) | `/breakdown` Ph.1 |
| `<banned>` and `<task-limits>` | `check-banned.py` (56) | `review-tasks` · `execute-verify` |
| Every in-scope feature and criterion has a task | `check-coverage.py` (30) | `/breakdown` Ph.5 · gate (38) |
| The seven mechanical definition tests | `check-definition.py` (40) | `/prd` Ph.6 |

**Item 6 is the *caller*, not the container.** `/prd` Phase 6 invokes `check-artefacts`,
`check-status`, `check-references`, `check-rename` and `check-definition`, and reports their
combined output. Each script is independently runnable, independently testable, and owns its
assertion — so *"which script says a slug has no file"* has one answer.

**59. A runtime test across the `/breakdown` → `/execute` boundary.**
*Addresses A8/R13. Depends on item 43's fixture pair; item 21 is its sibling.*

Items 13–17, 19, 20 and 30–32 all specify behaviour at that boundary and **no run has ever crossed
it with an input this plan's schema describes**. For a document whose central methodological
complaint is that static agreement is not evidence, that ratio is the wrong way round.

Run the `schema-2` fixture end to end and assert, in this order:

1. **Criteria arrive verbatim, with their ids.** Every `<criterion id>` in the fixture appears in
   some task's `<acceptance-criteria>` with the same id and the same text (item 17). This is P2's
   fix, and it is the one assertion that would have failed for the whole life of the toolchain.
2. **`<source-feature>` resolves both ways.** Every task names a feature that exists; every
   in-scope feature is named by a task (items 16, 30).
3. **The coverage report names a real shortfall.** Remove one feature's tasks and assert the report
   names *that feature*, by slug — not a count (item 30).
4. **The tier is reported.** `<moscow>` and `<requirement-level>` appear in the run output (19).
5. **A won't-have task is refused at preflight**, not merely absent (20).

**Assertion 3 is the one worth insisting on.** A coverage check that reports *"4 features have no
task"* passes a test that a check reporting the wrong four would also pass. Naming the shortfall is
what makes item 30 falsifiable, and a test that does not force it will not detect a check that
counts correctly and attributes wrongly.

**60. `execute-layer` stops maintaining a derived file.**
*Addresses P38. Phase 1: no schema change, and it fixes a merge loop that cannot fire.*

Six edits to one skill, all of them removals of instructions the same file contradicts elsewhere:

- **5d takes its merge set from 5c's `verified` array**, not from `merge_queue`. This is the one
  with teeth — the loop as written matched nothing.
- **Step 2 takes only `failed` and `abandoned`** from `execute-state.json`, the two fields
  `write-state.py` carries forward because they cannot be derived. Completion comes from
  `ledger-status.sh`, as Step 3 already says.
- **Steps 4 and 6 become explicit no-ops**, stating why: layer status is `merged` against `total`,
  computed on every write, and `/execute-merge` has already run the script by then.
- **`batch_number` is a local counter**, not a state field.
- **The `merge_queue` example shows real 3.0 output** — merges that happened, with the commits
  that prove it, six lines above the paragraph that says so.

**And F21's mutation check is widened from seven field names to any key.** The allowlist is why
the defect survived: a check scoped to last time's wrong fields cannot catch this time's. Confirm
it by running it against the unfixed file — a check nobody has watched fail is not yet a check.

*This item is small and it is not a schema change, which is why it belongs in Phase 1 rather than
with the consumer work. It is also evidence for item 23's rule in a place the rule did not reach:
every element having a reader does not help when the reader looks for a value the producer stopped
emitting.*

### K. What the live run found

**Five items from three live crossings, and the section exists because they are a different kind
of item.** Everything above was specified by reading the corpus; these were specified after
watching the toolchain run. Two were one-line contradictions and are already fixed; three are
outstanding, and one of those needs a schema change.

**61. `plan-layers`' instructions stop contradicting its derivation.**
*Addresses P39. Landed with this section — no schema change.*

The *Do NOT* list forbade skipping layers while the section above it required deciding which
layers exist. The line is replaced by the two rules that are actually true: **emit no layer with
no work in it**, and **never drop one silently** — name what was dropped and why, because the
caller reports that list to an operator who expected four tasks and got one.

**The general form is worth stating once.** Item 31 changed a behaviour and updated the section
that describes it; the instruction that forbade the new behaviour was eight sections away and
survived. A check that asserts a *mechanism* cannot see that, because the mechanism was right —
what was wrong was a second instruction about it. **`/breakdown` reads both.**

**62. The task schema admits every layer the layer graph can produce.**
*Addresses P40. Landed with this section — no schema change to any artefact.*

`id` becomes `L[0-9]+-[0-9]{3}` and `layer` becomes `{id}-{name}` drawn from the derived set, with
the five shipped names given as defaults rather than as an enum. Two independent reasons force
this and either would be sufficient: Layer 0 has always existed and was never expressible, and
item 28 lets a project declare its own graph — instantiated per service, with ids scoped to their
block — which no fixed list of four names can describe.

**63. A task's `<verification>` block is not editable by the run it judges.**
*Addresses P41. The highest-value item in this section, and the cheapest.*

The rule is one sentence: **an implementer and an orchestrator may not modify a task file.** What
to do instead is the interesting half, and the live run had the answer right in every respect
except where it wrote it down — it *diagnosed* an unsatisfiable verification step correctly and
should have **stopped and reported it**, exactly as `migrate.py`'s `ESCALATE` does.

Three parts, in order of value:

- **A guard, not a paragraph** (P16). `/execute` hashes each task file before dispatch and
  re-checks after; a changed task is a stop with the diff. Prose here is the guard a model can
  reason past, and this run reasoned past a guard that did not exist.
- **An escalation path**, so the correct behaviour has somewhere to go: an unsatisfiable
  verification step is a `/breakdown` defect, and the run should end naming the task and the
  contradiction rather than repairing it. That is what makes the guard bearable — a rule that
  leaves the operator stuck is a rule that gets removed.
- **The record.** The ledger records commits; a task edit leaves no trace at all. Whatever the
  policy, the edit must be visible afterwards, or the next `14/14` is unauditable in the same way.

**This is the one item in the plan that a passing run argues for.** The run reported what it did,
in detail, unprompted — the failure is not that the agent was dishonest but that honesty was the
only thing standing between a rewritten acceptance criterion and a green result.

**64. The generator is told where its verification commands will run.**
*Addresses P42. Depends on nothing.*

`breakdown-generate-tasks` writes `<verification>` steps that execute **inside a git worktree**,
and nothing tells it so. The concrete instance was `Path('.git').is_dir()`, false in a worktree
where `.git` is a gitlink file; the class is every environment-shaped assertion the generator
invents.

Two halves, and the second is the durable one:

- State the execution context in the generator's brief: a worktree of the target repository, cwd
  at the worktree root, `.git` a **file**, and the branch not the base branch.
- **Prefer assertions about the artefact over assertions about the environment.** `import
  link_shelf` is a claim about the task's own output; `Path('.git').is_dir()` is a claim about
  somebody else's execution model. `review-criteria.md` is where that becomes a review question.

**65. A task may name every feature it descends from.**
*Addresses P43. The only item here that changes an artefact, and the only one that needs a schema
version.*

`<source-feature>` becomes repeatable, and `<satisfies-criteria>` is qualified by the feature it
belongs to. The shape is item 16's and the change is to its cardinality, not to its meaning:

```xml
<source-feature slug="tag-links" moscow="should-have" satisfies-criteria="1,3"/>
<source-feature slug="save-link" moscow="must-have"   satisfies-criteria="1"/>
```

**Three runs invented three workarounds, which is as strong as this kind of evidence gets** — and
the plan never considered the case, because a document read feature by feature does not produce an
integration task. The corpus could not have shown it; only a run could.

**What it costs, stated plainly.** `<moscow>` and `<requirement-level>` are per-feature today and
become per-edge, so `/execute`'s tier filter (item 19) and preflight's refusal (item 20) must take
the *highest* tier across edges rather than the only one. `check-coverage.py` scopes cited ids per
feature already and gets simpler. The manifest gains a list where it had a string, so
`MANIFEST_SCHEMA_VERSION` moves — additively, which is what item 24's reader was built to
tolerate.

**Do not fix this by relaxing the consumer.** The tempting cheap version is to let
`check-coverage.py` accept a criterion cited by a task from another feature. That makes the report
pass and leaves the task set exactly as unattributable as it is now, which is P2's mistake with
the arrow reversed: a consumer weakened to match an under-specified producer.

---

## L. What implementing the phase found

**One item, and it exists as its own section for the same reason K does** — not because it is
bigger, but because it was found a different way. K's five came from watching the toolchain run.
This one came from reading `/execute` while wiring item 63's guard into it, which is the third
kind: found by building.

**66. `/execute` takes its layer set from the plan it was handed, not from a list in its own
prose.**
*Addresses P44. Depends on nothing, and does not wait for 65.*

Three parts, and the first is the whole fix:

- **Iterate `layer_plan.json`.** The layers of a run are the ones `/breakdown` derived and
  recorded, in the order it recorded them. `/execute` already reads that file for its dry run;
  Step 6 is the one place that does not use it.
- **Delete "Never skip layers: Execute in order (0→1→2→3→4)."** It contradicts Step 6's own
  skip-what-is-verified rule as well as the derivation, and it is the same shape as **P39**: an
  instruction eight sections away from the behaviour it forbids, surviving the change that made
  it false. What replaces it is the rule that is actually true — **execute the layers the plan
  declares, in the order it declares them, and skip only what git says is done.**
- **Refuse a layer the plan does not declare.** `--layer 3-frontend` against a plan with no such
  layer is an operator error and must say so, rather than iterating to a silent zero.

**A run that executes nothing must never report completion.** That is the half worth checking by
test: the failure here is not that a layer is missed, it is that missing every layer looks
exactly like a project with nothing to do. `ledger-status.sh` already knows the expected total —
`verified 0 / 18` is available at the point the report is written, and item 4.9's rule that a
shortfall is named applies unchanged.

---

## M. What the fourth crossing found

**One item, and the section exists for the same reason K and L do:** it was found a different way
again — by the first live run in which item 63's guard was active. K's five came from crossings
against a toolchain that had no such guard; this one came from watching the guard work correctly
and stop nothing.

**67. A snapshot that replaces another says what changed between them.**
*Addresses P45. Depends on item 63 and on nothing else.*

The rule stays as it is: **an operator may fix a task between runs.** Forbidding that would leave
an unsatisfiable task with no way forward, which is the failure item 63's escalation path exists
to prevent. What must change is that the fix stops being invisible.

- **`record` compares before it replaces.** When a snapshot already exists, every task file that
  differs from it is appended to `task-edits.jsonl` as an edit between runs, with both hashes and
  a diff, *before* the new snapshot is taken. The same record, the same file, the same shape as a
  mid-dispatch edit — the two differ in `kind` and in nothing else.
- **Report it at the top of the run.** A resume that begins by naming the task files that changed
  since the last one is a resume whose operator knows what they are resuming into. Silence there
  is what made the fourth crossing's `10/10` weaker than it reads.
- **Never block on it.** An edit between runs is legitimate; an edit nobody can see is not. This
  is the same distinction item 63 drew for the label `defined` and item 40 drew before it.

**What this does not do** is make the guard cover the case where a run stops itself, edits, and
resumes *within one invocation*. Nothing on disk can tell that apart from an operator doing the
same thing between two invocations, and a guard that tried would be guessing at intent. What it
does instead is make both of them leave the same trace, which is the honest version of the same
protection.

---

## N. What verifying the implementation found

**Four items, and the way they were found is again different from K, L and M.** Those three came
from *running* the toolchain, from *building* an item, and from *watching a guard work*. These came
from reading the repository against this document — 67 items, one at a time, looking for the thing
each one said it would build. Full method, limits and findings V1–V13 in
[`plugin-2.0-verification.md`](plugin-2.0-verification.md); the four below are the ones that are
changes to the toolchain rather than to a document.

**None of them is a decision that was wrong.** Every one arrived *after* a correct decision, in the
gap between an item landing and the next item noticing — which is the same shape as Phase 7 and is
why the count keeps being small and the causes keep being uniform.

**P46 — `<review>` has a reader, a fixture and a migration rule, and no producer.**
*Verification: static, exhaustive, and confirmed by running the reader.*
schema-6 exists to give item 40's gate its second half. The element is defined in core §7, read by
`check-definition.py`, written by migration rule R13, and carried by all six schema-6 fixture
features — and a search of `commands/`, all of `skills/` and `schema/prd-format.md` for `<review`
or `record-review` returns **zero matches**. §7 is the only section of the core that no format
reference points at. Worse, `/prd` instructed the opposite: *"where the PRD carries no place to
record that review, say so plainly to the author"* — true before schema-6, false after it, so a run
following its own command file reports the absence as unfixable. **This is item 23's rule failing
in the direction it does not check**: `check-readers.py` asserts every element has a reader, and
the reverse is a report by design.

**P47 — the assertion registry drifted, in the one direction nothing checks.**
*Verification: measured, by running the table.*
`checks.md` asserts that every assertion names its owner *and its callers*, and the suite walked
that forward only — owner exists, claimed caller cites it. Backward, five gaps: `task-integrity.py`
and `resolve-layers.py` own assertions with `REFUSED` exit codes and had no row at all, and three
caller lists were stale, two of them because group 8b wired `check-references.py` into a CRD. **A
table that can only be checked forward records what somebody wrote, not what is true.**

**P48 — two documented commands use a path that cannot resolve.**
*Verification: static, exhaustive.*
Open question 1 measured it and item 9 states it: the working directory is the target project, so
`python skills/x/y.py` resolves against the wrong tree. Every invocation site obeyed that until
Phase 8 added two that do not — one in `migration.md`, 87 lines from four of its own that are
correct, and the other the only documented invocation of the producer P46 says is missing.

**P49 — three shipped artefacts describe a state the toolchain has left.**
*Verification: measured, by running each.*
`check-scope.py` still told an operator that item 16 *"has not landed"* and attributed a real
generator defect to a missing feature; `readers.md` stated a count of six against a script that
prints seven; and `checks.md`, `parity.md` and `readers.md` stamped `schema-5` against a core
carrying `schema-6`. The third is the interesting one. Either the stamp means what the core's
means — in which case it was wrong — or it means *last reconciled at*, in which case **it was
already announcing that these files were a version behind, and nothing read it.** P47 and the
`readers.md` count are independent confirmations of the second reading. A stamp nobody reads is
P28's own finding, one level in.

**68. Give `<review>` a producer, and stop denying it has one.**
*Addresses P46. Depends on schema-6 and on nothing else.*

Three edits and one check, and the third edit is the one that matters:

- `schema/prd-format.md`'s feature `<meta>` template carries `<review by= at= sha=>`, with a
  pointer to core §7. It is the template `/prd` writes from, and the element was absent from it.
- `commands/prd.md` Phase 7 runs `check-definition.py --record-review --by NAME`, beside the agent
  dispatch that produces the judgement it records. **Nothing may hand-write the element**: `sha` is
  a digest over the file with the review removed, and a hash written by hand is right four times.
- The sentence telling the author there is nowhere to record a review is **replaced**, not
  softened. It is the instruction that made the element unproducible, and it now says what to
  report instead — a feature that passes the mechanical tests and carries no review is not yet
  `defined`.

The check asserts all three, and asserts the flag it names is really registered in the script it
names: **a cited producer that cannot run is the same defect one step along.**

**69. The caller table is checked in both directions.**
*Addresses P47. The reverse check is the item; the five corrections are its first output.*

For every owner in `checks.md`, every file that *runs* it must appear in its column — and
`task-integrity.py` and `resolve-layers.py` get the rows they never had.

**"Runs it" is the whole of the design.** Half the repository names these scripts in a docstring or
a cross-reference, so a substring match reports thirty files and is therefore ignored — the fate of
every alarm nobody can silence. A caller is a line that *runs* it: `python <path>/<script>`,
`sh <path>/<script>`, a `run("<script>")` helper, or an interpolated plugin path. That rule finds
exactly the five real gaps and nothing else, and the column definition is widened to say that a
caller may be another script, because two of the five are `check-gate.py`.

**70. A documented invocation names the plugin root.**
*Addresses P48.* Mechanical, and worth a check for one reason: this stopped being a convention with
no violations and became a rule with two. The check scans every `.md` outside `docs/` and `tests/`
for an interpreter followed by a repository-relative script path.

**71. No shipped artefact describes a state the toolchain has left.**
*Addresses P49. Three instances, one shape, and the check generalises past all three.*

- **The landed set is derived from the ledger**, not listed in the check. Any script claiming a
  numbered item is still pending, where the ledger records it landed, fails — so this catches the
  next one rather than only these two.
- **`readers.md`'s count is asserted against `check-readers.py`'s own output.** A figure in prose
  is exactly what went stale, so the fix cannot be another figure in prose. The seventh candidate
  is `<requirement-level>`, which is live rather than retired and undefined in `schema/` because a
  task is not a versioned artefact — stated in the file, because a report that names something and
  does not explain it invites somebody to "fix" it.
- **Every schema stamp equals `SCHEMAS.json`'s current**, not only the core's. **Decided: one
  meaning for one syntax.** The *last reconciled at* reading is real and is better served by item
  69's reverse check, which measures reconciliation instead of asserting it.

---

## O. What the documents said

**P50 — the documents that onboard a reader describe a smaller project than exists.**
*Verification: static, exhaustive, and confirmed by running four new checks against them.*
Nine phases landed without `ARCHITECTURE.md`, `README.md` or `target-state-data-flow.md` being
touched once, and the ledger mentions none of the three — not as done, not as deferred. What they
said on 2026-09-08:

| Document | The claim |
|---|---|
| `ARCHITECTURE.md` | the `.claude/` layout `CLAUDE.md` warns against; an `execute-task` skill in four places, removed at item 4.15; **zero** occurrences of `schema/`; a model table assigning `sonnet` to almost every component against files declaring haiku, sonnet and opus; and a fork example teaching `allowed-tools:` |
| `README.md` | *14 skills* and *8 subagent definitions* against 15 and 10; no `schema/`; and `claude --plugin-dir <path>` alone |
| `target-state-data-flow.md` | **Status: Target state. None of this is built.** |
| `CLAUDE.md` | a tree omitting `prd-criteria-author`, `architecture-format.md`, three of the seven `schema/*.md` and most of the 33 scripts |

**Two of these are worse than staleness.** The `allowed-tools:` example is the defect item 4.11
existed to remove, taught as a positive example on a skill that does not exist — a reader copying
it writes a skill that does not fork and cannot be told why, and the suite's F13 guard scans
`skills/`, not the document that teaches the pattern. And README's one-flag load command is the
first thing a new user runs; without `--add-dir`, `/breakdown` stops in Phase 1, which was
measured on 2026-08-26 and written into `CLAUDE.md` alone.

**Why it went unnoticed for nine phases is the interesting half.** Every check in the suite reads
`skills/`, `commands/`, `agents/`, `schema/` or `tests/`. **Nothing read the four documents at the
repository root**, so the only artefacts with no automated reader at all were the ones a human
reads first. That is P4's shape — a producer with no consumer — inverted: a *consumer-facing*
artefact with no producer-side check.

**72. The documents that describe the repository are checked against it.**
*Addresses P50. Depends on nothing; deliberately last.*

The content fixes are ordinary editing. The item is the four checks, because this file went stale
for nine phases precisely by being the thing nobody checked:

- **The layout, in both directions.** Every skill and agent named in `ARCHITECTURE.md`'s file tree
  and `CLAUDE.md`'s must exist, and every one on disk must be named. A ghost sends a reader to a
  missing file; **an omission is worse, because there is nothing to look up and no way to notice**
  — `execute-task` was the first kind and `schema/` the second. `README.md` states counts rather
  than enumerating, so its counts are compared to the directories.
- **A documented frontmatter example must be one a skill could declare.** No `allowed-tools:` in
  any `yaml` block, and every row of the model table must name a real component and the model its
  own file declares. A table of assignments nobody compares to the frontmatter is a table of
  intentions.
- **The documented way to load the plugin must be the one that works** — both flags, in both
  documents that give the command.
- **A document describing a target state must say whether it was reached**, and removing the false
  claim is only half: a reader still needs the true one.

**`target-state-data-flow.md` is corrected, not rewritten.** Its value now is the *before and
after* — the left column of its §0 table is what the toolchain was, and everything below it is
what the plan changed. Rewriting it in the present tense would delete the only record of the
starting state, and `ARCHITECTURE.md` already describes what runs.

---

## P. What the experiment found

**One item, and its provenance is a fifth kind.** K came from running the toolchain, L from
building an item, M from watching a guard work, N and O from reading the repository against this
document. This one came from **an experiment this plan specified and then did not run for six
phases** — open question 7's, whose full result and three self-inflicted defects are recorded at
the foot of that question.

**P51 — a wrong layer graph produces an unbuildable task set, and nothing mechanical notices.**
*Verification: measured, three live `/breakdown` arms, 2026-09-08.*
An `architecture.md` declaring the five default layer names with the dependency direction
reversed is accepted by `check-architecture.py` — correctly: it is acyclic, its ids are unique and
every layer is reachable. **Structural validity is not buildability.** The arm that obeyed it
emitted 14 tasks carrying **16** dependencies on interfaces exported by a layer that runs *after*
them — backend endpoints importing `Link`, `get_db` and `db_session` from `4-foundation` — and
`check-coverage.py` and `check-gate.py` both exited **0**.

**A second run of the same graph refused instead**, diagnosing it correctly and stopping. That
disagreement is the finding rather than a footnote to it: **the toolchain's protection against a
wrong graph was a model judgement, and it fired in one run of two.** OQ7 predicted this failure
would be *"silent and hard to attribute"*; it is worse than predicted, because it is silent
*sometimes*, which is the case no amount of reading the output can be relied on to catch.

**P52 — `breakdown-plan-layers` resequenced the declared graph, which its own spec forbids.**
*Verification: measured, and checked against the artefacts.*
Given a graph declaring `0-setup, 1-integration, 2-frontend, 3-backend, 4-foundation`, it emitted
`0-setup, 4-foundation, 3-backend` — foundation moved ahead of backend, reversing the declared
direction into the buildable one.

**The skill rules on exactly this case and it did half of what the rule says.** Its Dependency
Ordering section: *"A `data` or `runtime` edge that would order a later layer before an earlier one
is a contradiction, not an ordering. **Report it and place the tasks by layer**; a feature edge
cannot override the layer graph, because the layer graph is the project's declared rule and the
edge is one author's note."* Two obligations. It discharged the first — `layer_plan.json` carries
an `ordering_conflicts` entry at `severity: critical`, naming both layers, the declared order and
the required one — and not the second.

> **Corrected 2026-09-08, and the correction matters more than the finding.** This was first
> written up here, in the ledger and in a commit message as a *silent* override. **It was not
> silent**; the conflict is reported prominently in the same file that carries the resequencing.
> The word came from the neutral arm's own transcript — *"plan-layers did silently override it"* —
> and was carried through three documents while only the *override* had been checked against the
> artefacts. **A run describing its own behaviour is a claim, and half of this one was verified
> and half was quoted.**

**It also dissolves the reason this was left ownerless.** The open question was said to be whether
the toolchain should obey a bad graph or refuse it; the spec had already answered — report the
conflict, place by layer, and leave `architecture.md` for a person to fix. Item 74.

**73. No task may depend on an interface a later layer exports.**
*Addresses P51. Depends on nothing.*

**This is not the mitigation open question 7 specified, and the departure is the experiment's own
result.** That text asks `/breakdown` to *report when a supplied graph decomposes materially
differently from the shipped default* — which needs a baseline, a second decomposition, and a
threshold for "materially". The measurement showed something cheaper and stronger: **the defect
is visible inside a single task set.** A task naming an interface that a later task exports is
unbuildable on its own terms. No default to compare against, no judgement about degree, and it
would have caught the silent arm on the run that produced it.

- **An exit code, not an instruction.** The protection that already existed was a model reading
  the graph and reasoning about it, and it worked once in two runs. Item 4.13's principle,
  arriving where OQ7 left the question open.
- **Order comes from `layer_plan.json`, not from the layer number.** A layer id is not a rank —
  the graph that produced this finding has ids ascending while its dependencies do not, which is
  the whole point of it.
- **An unexported dependency is not a violation.** `python`, `pip`, `sqlite3` and
  `fastapi.testclient.TestClient` are external libraries declared as interfaces; a first version
  of this metric counted them and reported nine findings against a task set that was sound.
- **It names both causes and chooses neither.** Either the declared graph orders these wrongly or
  generation put a task in the wrong layer, and deciding between them is a judgement about the
  project rather than something a script may settle.

**Item 43 gains its third arm here**, which is what the LOAD-BEARING outcome buys.
`tests/fixture/layering/` holds real generator output from all three runs — the sound decomposition
as the negative control, the inverted one as the positive. **Neither was hand-built**: a fixture
written to match the checker validates the code against itself, which is the defect item 21 hit
from the other direction.

**74. A declared layer order is obeyed, not improved on.**
*Addresses P52. Depends on nothing.*

`plan-layers` may decide **which** layers exist — item 31, and a tier with no work in it is not a
tier — and may not decide **what order they run in** when the project has declared one. Its own
Dependency Ordering section already says so, in two obligations; the run met the first.

- **The emitted list must be a *subsequence* of the declared one.** Dropping `2-frontend` from
  `0,1,2,3,4` to give `0,1,3,4` is item 31 working. Emitting `0,4,3` is not, whatever its merits.
- **The instruction gains its missing half, and an exit code behind it.** `check-layer-order.py`
  refuses a resequenced plan, so *reporting a contradiction does not license resolving it* is not
  a sentence standing on its own — which is the whole argument of item 4.13 and F15.
- **No declared graph means nothing to check.** The shipped default promises nothing about order
  beyond its own definition, and refusing there would fire on every ordinary run.
- **It is a second script rather than a widening of item 73, and the fixtures decide that rather
  than the argument.** `inverted/` obeys the declared order and carries 16 unbuildable
  dependencies; `inverted-halted/` violates the order and has no task files at all, so
  `check-layering.py` exits 2 for want of a subject. **P52 happens in `layer_plan.json`, before a
  single task exists.**

**What it does not do is judge whether the declared graph is good.** Item 73 answers that from the
consequences. This one answers only whether the project's rule was obeyed — and where it cannot
be, the fix belongs in `architecture.md` and to a person, with `ordering_conflicts` as the thing
that makes it cheap.

---

## Q. What deciding the parity rows found

**Two items, and neither is built.** V7 asked what to do about the three `open` rows in
[`parity.md`](../../schema/parity.md), which had been recorded as legitimately undecided since
item 50. Deciding them settled one outright, showed a second was reading the *spelling* rather
than the capability, and turned the third into a defect with a name. The two below are what
survives; both are specified here and neither has landed, which is the state `checks.md` describes
for an assertion somebody has specified and not yet built.

**P53 — a CRD declares a schema change and no task ever sees it.**
*Verification: static, exhaustive.*
The PRD path carries `<notes><data-model>` into a task's `<context>` — item 17, and the task
format defines the element as *"the feature's own `<notes><data-model>`, carried. NOT
re-inferred."* The CRD path has the same information in `<contract kind="schema" ref="...">`
(item 57) and **no route for it**: `breakdown-analyze-prd` does not mention a CRD anywhere in its
instructions, and `generate-tasks` carries `architecture.md`'s registry entries rather than the
document's own `<affected-contracts>`. So a change request that adds or alters an entity states it
in the document, has it read by `crd-impact-analysis`, and then hands the implementer a task that
does not carry it. **This is P4 on the path P4 was not measured on** — a producer whose consumer
stops one step short.

**P54 — the significance flag exists on one path and is unsayable on the other.**
*Verification: static, exhaustive — and corrected below, because the first statement of it was
wrong in a way that would have changed the fix.*
`crd-format.md` mentions `<architecturally-significant>` **zero** times, so a refactor CRD — the
document item 35 exists for — has no way to say that it warrants a design step.

> **Corrected 2026-09-08 while building item 76.** This was first written as *a live reader with
> no producer*: `check-references.py` reads the element, `check-gate.py` runs that script for a
> CRD, therefore the consumer was said to be scanning for something the schema forbade anyone to
> write — P46's shape, item 68's defect on the other path.
>
> **It was not scanning.** `main()` takes the CRD branch at `os.path.isfile()` and **returns
> before** the significance screen, which iterates a PRD *directory*. The element had neither a
> producer nor a reader here.
>
> **Both halves of that inference were checkable and only one was checked.** *The gate runs the
> script for a CRD* is true and was verified; *therefore the screen inside it runs on a CRD* was
> assumed. It is the same failure as P52's *silent*, four items earlier: **the adjacent fact was
> measured and the one that mattered was inferred from it.**
>
> It changes the fix rather than only the wording. Adding the element alone — which is what the
> original P54 implied was enough — would have shipped a producer with no consumer, **the exact
> defect item 76 exists to remove, inverted.**

**75. The CRD's schema contracts reach the task that implements them.**
*Addresses P53. Depends on nothing.*

`generate-tasks` carries a CRD's `<contract kind="schema">` entries into `<context><data-model>`,
the way item 17 carries a feature's. **Copied, never re-inferred**, on the same rule and for the
same reason. The task format needs no new element — it needs its existing one to have a second
producer, and its spec sentence widened from *the feature's own* to name both sources.

**76. `<architecturally-significant>` on a CRD.**
*Addresses P54. Not a schema version, and that was measured.*

The element, its `because` enum and its `criteria` list, defined once in **core §8** and cited by
both format references rather than copied — the rule item 44 exists for. `prd-format.md` gives up
its own copy in the same pass, so the PRD path stops being the definition and starts being a
citation.

**The reader ships with it, and the original text of this item was wrong to say otherwise.**
`check_crd()` gains the same two assertions the PRD screen makes plus the enum: a `because` that
is empty or outside core §8's six values is a refusal, and a flag no decision record drives is a
warning, because the flag is a judgement and its absence proves nothing.

**It is not a schema version, and the reason is measured rather than argued.** The element is
optional, so no existing CRD becomes invalid; `check-artefacts.py` closes a child set only where
the schema says *exactly these* — `<notes>` — and `<meta>` has never been closed. A schema-6 CRD
carrying the element **validates unchanged**, which was run before this was decided. A version
would have bought a frozen fixture and a migration step whose transform is the identity, against
`SCHEMAS.json`'s own warning that maintaining the same project twice is what makes people abandon
versioned fixtures.

**What it buys** is a design step for refactor CRDs: *"replace the session store"* is
architecturally significant in a way that *"add a column"* is not, and until this the difference
was unsayable.

---

## R. What the fifth crossing found

**The first CRD crossing since the fidelity plan began.** §5.3 ran end to end on 2026-08-14 and
passed; everything numbered 44 upward landed after it. So this was a *regression* question — what
did six schema versions do to a sequence that worked — and the answer is that the sequence still
works and two of its guards had stopped reaching it.

**Steps 1–4 all passed**, verified against git and pytest rather than the runs' own summaries:
`PROJECT.md` valid with `stale=no` and five features on `built=`; a CRD with 7 EARS criteria, 2
gaps and a correct significance flag; 4 tasks with layers derived and the backend three chained
because they share files; **4/4 verified, 4 merge commits, 27 tests passing from a baseline of 8,
0 worktrees left, and the delete trap held.**

**Items 75 and 76 both worked on their first live run**, hours after landing. Every task carried
`<data-model>` sourced from `<affected-contracts>` under the *touches* rule, and `/crd` produced
`because="cross-cutting"` from unstructured prose — the open question when item 76 shipped was
whether an interview would ever *write* one.

**P55 — item 29's execution stop was unreachable on the CRD path.**
*Verification: measured, by running the gate.*
`check-gate.py` guarded assertion 3 with `os.path.isdir(args.document)`, and a CRD is a file, so
`blocking_gaps()` never ran. It also called `features_of_prd()` unconditionally, so removing the
guard alone would have traded a silent skip for a read error. The crossing's CRD carried two
`<gap kind="decision">` — core §6 makes `decision` a stop — and the gate printed `3 blocked OK`.
**Any change request could carry an undecided question into `/execute` and be waved through.**

**P56 — a CRD's architectural significance never reached the gate, and item 76 built half of it.**
*Verification: measured, by running the gate.*
Two significance branches write to one `warnings` list and print under different prefixes: the CRD
branch as `NOTE`, the PRD branch as `STALE`. `check-gate.py` filters for `STALE`. **And the CRD
branch never resolved `**Drives:**` at all** — it reported *that* a change was significant, never
*that no record drove it*. The crossing's CRD declared itself significant with no decision record
naming it, and the gate printed `2 significance OK`.

> **The second is the instructive one, and it is mine.** Item 76 added that branch the previous
> day. I verified the screen *fired* on a CRD and not that anything downstream *acted* on what it
> emitted — which is the question item 76 existed to answer. That is the third time in two days
> the adjacent fact was measured and the load-bearing one inferred from it (P52's *silent*, P54's
> *live reader*, and now this), and this instance was introduced while fixing the second.

**The shape is the finding, not the two instances.** `os.path.isdir(...)` treats *PRD directory*
as the general case and lets a CRD fall through to a default. Four sites now:
`check-references.py` (group 8b), `check-gate.py` twice, and `check_crd()` itself.
**The CRD path is not under-tested by accident — it is the `else` branch everywhere.**

**77. The gate's assertions reach a CRD.**
*Addresses P55 and P56. One item because they are one shape in one file.*

- **`blocking_gaps()` dispatches on file-versus-directory**, the way `select-features.main()`
  already does, and the `isdir` guard at its call site goes. **Both lines**, because either alone
  leaves the assertion unreachable.
- **`check_crd()` resolves `**Drives:**`** — records are discovered from the CRD's own directory,
  falling back to the project — and reports the undriven case under **`STALE`**, in a list
  separate from `NOTE`. One list per prefix is what stops two channels sharing one name again.
- **Without records it says it could not look**, rather than reporting that nothing drives the
  flag. The PRD branch has always drawn that distinction and the CRD branch now does too.

**P57 — a live run wrote scratch files into the toolchain checkout.**
*Verification: measured. The files are in the run's own timestamp range and no instruction names
them.*
Step 4 of the fifth crossing left `skills/execute/preflight_err.txt` and
`skills/execute/resolve_err.txt` in the plugin, timestamped inside the `/execute` run. The first
holds `preflight.sh`'s NOTE, captured by a stderr redirect.

**Nothing instructs it.** No `SKILL.md` in the execute tree contains a `2>` redirect and no
instruction names `_err.txt`: the model invented the capture, wrote it to a *relative* path, and
the path resolved inside the checkout.

**This is F4's class**, which item 4.6 resolved — *"a previous run's entire output landed in
`skills/breakdown-generate-tasks/output/` and the caller was never told"*. What 4.6 built guards
the **declared** output paths: `resolve-output.sh` refuses a tasks directory inside a plugin and
`preflight.sh` refuses a plugin as a target. **Neither constrains a path a model invents
mid-run**, and there is no rule saying where scratch may go.

Three things make 82 bytes worth an item:

- **It is silent.** Nothing reports it, and the operator learns of it from `git status` or not at
  all.
- **It is in the plugin**, which is shared by every project that loads it — unlike a stray file in
  a target, which belongs to one run.
- **No live harness checks.** `boundary-test.py`, `graph-experiment.py` and `run_5_3.py` all
  verify the *target* and none looks at the checkout. `dirty-guard.sh` guards `git checkout --`
  during a mutation round, which is a different moment entirely.

**78. A run writes nothing into the toolchain, and the harness proves it.**
*Addresses P57. Depends on nothing.*

Two halves, because the rule and the evidence are different jobs — the split this plan has made
since item 4.13.

- **`/execute` says where scratch goes:** `{project_path}/.execute/{prd_slug}/`, never a relative
  path. That directory already exists, already holds the ledger and the task-file snapshot, and is
  already under a self-ignoring `.gitignore`. **A redirect with no directory in it is the defect**
  — the cwd of a skill is not a thing the skill may assume.
- **Every live harness checks the checkout afterwards** and fails if it is dirty. That is the half
  that would have caught this: the rule above is prose, and P16 is this plan's finding about
  prose. A run that dirties the toolchain must end red rather than end quietly.

**It reports rather than deletes.** The files are evidence of what a run did, and a harness that
tidied them away would leave the next person with the same surprise and no trace.

---

## S. What measuring the else branch found

**Section R closed by saying the CRD path is the `else` branch everywhere, and that this was
worth a check of its own.** Measuring that sentence before building the check is what this
section records — because the sentence turned out to be true about something other than what it
named.

**43 `isdir`/`is_dir` calls across 28 files.** Twenty-two are on a tasks directory, a repo root,
a worktree or a discovery candidate. Of the twenty-one on a document, **seven are PRD-only
scripts that refuse a CRD with `exit 2` and a named reason**, ten dispatch correctly, and two
were defective. A lint on the call would have flagged `select-features.py` — the dispatch this
plan's ledger calls canonical — and found none of the three findings below, which are about a
*value*, a *caller* and a *printed line* rather than a branch.

**P61 — capability parity is recorded and enforcement parity is not.**
*Verification: measured, against both registries.*
`parity.md` measures whether an ELEMENT is documented on both paths, with a substring probe
against a format reference. `checks.md` measures ownership, in both directions since item 69.
**Neither can say *this assertion runs on the CRD path***, and four of the six known sites are
capabilities `parity.md` already records as `both` — the element on two paths and the check over
it on one. 144 static checks saw none of them; every one was found by a live run.

**P58 — a CRD's `<gaps>` were never validated, and a typo defeats item 29 there.**
*Verification: measured, by mutating the fifth crossing's own CRD.*
`check-status.py` owns *`<gaps>` well-formed, and aged* and had one caller, `commands/prd.md`.
Misspelling both blocking kinds — `decision` → `decsion` — and dropping a `raised` date: the PRD
control exits 1 with two named contradictions; every script that reads the CRD exits 0, and the
gate prints `3 blocked OK`. Item 77 made the assertion *reach* a CRD; nothing validated the value
it dispatches on.

**P59 — the gate reports a pass it has not established, in two ways.**
*Verification: measured, by running the gate.*
An unrecognised `kind` is `does not block` rather than `cannot be classified`, on **both** paths,
since `/breakdown` runs `check-status.py` on neither. And `gap_err` is appended to `findings`
while the printed line keys on `gaps` alone, so an assertion that could not run at all prints
`3 blocked OK` while `--json` carries `could not read the document`. **The comment three lines
below in the same function records that identical defect being fixed for assertion 4** and left
standing for assertion 3.

**P60 — item 35's third direction has never seen a CRD.**
*Verification: measured, with a PRD positive control.*
The screen for a document nobody has flagged that the heuristics say is a candidate sits behind
`if os.path.isdir(features_dir)`. An unflagged CRD naming a quality attribute is offered to
nobody; the same mutation on a PRD prints `CANDIDATE … quality-attribute (names 'password')`.

**P62 — `/breakdown` names its document placeholder for one of the two shapes.**
*Verification: measured, by running the scripts as documented.*
`{prd_dir}` is defined once — *"the directory holding `index.md` and `features/`"* — and that one
definition governs five invocations, four of which take either shape, including the gate.
Followed literally on the CRD path it resolves to `docs/crd/`, which is a directory, so the PRD
branch accepts it: `check-references.py` returns `0 references checked` where the file form finds
six. **Item 77 fixed the scripts and left the instruction naming one of them.** The fifth
crossing passed the file anyway, contradicting its own instructions — P16's shape, holding by
luck.

---

**79. Every assertion says which paths it reaches, and each `both` is probed by running it.**
*Addresses the class behind P55, P56, P58, P60 and group 8b. Depends on nothing.*

`schema/checks.md` gains a **`Paths`** column — `both` · `prd-only` · `crd-only` · `n/a` — with a
reason required for every value except `both`. **Four-valued and not three**, because twelve of
its rows read a task file, a manifest or the project's `architecture.md` and have no PRD/CRD axis
at all; forcing a verdict there manufactures a difference that means nothing, which is
`parity.md`'s own warning about spelling one level up.

`schema/scripts/check-enforcement.py` owns it. **Every `both` row runs its owner twice** — against
a well-formed CRD and one mutated to carry the defect that assertion exists to catch — and the
good run must stay silent. A declared column alone is a documentation ratchet: it catches the row
nobody wrote down and nothing about whether the code reaches.

**And P58, P59, P60 and P62 are fixed with it**, since a column asserting that assertions reach
both paths is worth nothing while four of them do not.

---

## T. What the sixth crossing found

**The first crossing driven end to end by a program**, against a fixture rebuilt with `--clean`:
5 commits, 17 files, 8 passing tests, no `PROJECT.md`. **All four steps passed** — 5/5 tasks
verified against git, 5 merge commits, 25 tests from a baseline of 8, 0 worktrees left, the
delete trap held, and `checkout-clean.py` reporting the run added nothing to the toolchain.

**Both of the previous section's changes were exercised.** Item 79's `check-status.py` invocation
in `commands/crd.md` ran for the first time and aged a real gap — and `/crd` **recorded** that gap
rather than inventing an answer, writing *"Not covered by the stakeholder's answers"* when nothing
in the prompt told it to. P62's `{document}` reached a live run, and `no index.md` appears nowhere
in the output.

**The instrument was wrong first, and the run said so.** Step 2's bare invocation returned four
clarifying questions and no document — which is `/crd` behaving correctly, because it is an
interview and one non-interactive turn is not one. *A refused run is not a failed measurement.*

**P63 — both `PROJECT.md` producers omit a required attribute, and the validator has no branch
for it.**
*Verification: measured, and reproduced in isolation.*
`crd-investigator` and `project-context-finalizer`, independently, wrote
`<feature id="save-link" name="Save a link">`: no `built=`. `check_project_context()` had a branch
for `built`, a branch for the pre-item-45 `status`, and **none for neither**. And it would not
have fired anyway: `main()` reads `if version is None: escalate; else: CHECKERS[kind](...)`, so a
file whose version cannot be detected is never content-checked — and the two conditions are
frequently one file, since a version is detected *from shape*. The operator got one line about
schema versions, ran `/migrate`, and was correctly told no migration can be selected. **A remedy
named by the only message they got, which cannot apply.**

**P64 — nothing asserts a task file is well-formed XML, and three readers hide it in turn.**
*Verification: measured, and reproduced from scratch.*
A generated `L4-001` carried `<contract kind="schema" ref="Link">` unescaped in prose.
`build-manifest.py` reported `2 task(s)`, exit 0 — it parses with `ElementTree` behind a bare
`except Exception` whose comment reads *"a malformed task file is item 4.x's problem, not this
script's"*. **The deferral was deliberate and the owner it deferred to was never assigned.**
`check-coverage.py` imports `edges_of` from that script, correctly, and inherits the silence: a
file that cannot be parsed has no `<source-feature>` edges, and no edges reads as *attributed to
nothing*. `breakdown-review-tasks` **passed** it, because it reads the file as text.

**P65 — item 49's only reader could not see its input, and reported that as agreement.**
*Verification: measured, by running the check against the crossing's first analysis.*
`check-scope.py` reads `analysis["scope"]` and `analysis["confidence"]`, and `/breakdown` Phase
2's `**For CRD:**` block names neither — it lists eight things to extract and those two are not
among them. The run guessed `scope_declared` and got *"nothing to compare: the analysis carried
no scope or confidence"*, exit 0 — **the same sentence a correct run prints when a document
predicted nothing.**

**P66 — the manifest does not carry what `/execute` documents reading.**
*Verification: measured, with two corrections to the first reading.*
`prd.slug` is never written on a first build, only preserved by a rebuild that already had one —
and it names `{project_path}/.execute/{prd_slug}/`, so every ledger path depends on it. The
crossing filled the gap by hand. `layers` is **stale**: item 66 made the layer set derived and
the manifest has never carried the key. `prd.project_path` **is** written when `--project-path`
is passed, and the claim that its fallback could never fire was wrong.

**P67 — a format table that can be followed to the wrong answer.**
*Verification: measured across the crossing's seven features.*
`project-format.md`'s feature table had one column headed `Attribute/Element` that never said
which was which; the only statement of it lived in an example further up the page. `<files>` is
correct on all seven features and `name` is an **attribute** on all seven. **Both producer
templates are correct**, so the shape written matched neither template and matched a permitted
reading of the table. Nothing parses either form mechanically — `<files>` is read by an
instruction — which is why a required element was absent on every feature of an artefact two live
runs had already consumed.

---

**80. A task file parses, before any reader reports a symptom of one that does not.**
*Addresses P64. Depends on nothing.*
`check-task-xml.py` owns it, called from `/breakdown` Phase 5 before the manifest, from
`breakdown-review-tasks` before every criterion that reads text, and from `/execute` after
compatibility — **the consumer side, and the one that must refuse**, because nothing on that path
parses a task and a malformed one reaches an implementer as text. `build-manifest.py` stops
reporting success over a file it could not read and **names the owner** rather than growing a
second copy of the assertion.

**81. A feature declares its build state, and an unplaceable file says why.**
*Addresses P63. Depends on nothing.*
The missing `else`, and the diagnosis. The escalation is **not** routed around — that decision
stands — but an artefact whose version cannot be determined is now judged against the current
schema *to say why*, labelled as such.

**82. The manifest carries what `/execute` reads, and its reader keeps up.**
*Addresses P66. Depends on nothing.*
`build-manifest.py` derives `prd.slug` from the tasks directory, which `resolve-output.sh`
guarantees is the slug; `/execute` stops documenting a `layers` key item 66 superseded. **And a
second defect found while measuring the first:** `MANIFEST_SCHEMA_VERSION` moved to `1.3` at item
65 and `READER_SCHEMA` stayed at `1.2`, so every manifest this toolchain wrote warned against a
reader inside the same toolchain. The two constants stay separate — importing one would make the
comparison vacuous — and **the regression suite is the one place allowed to know both**.

**83. A field a check reads is named where the analysis is written.**
*Addresses P65. Depends on nothing.*
`/breakdown`'s CRD block names `scope` and `confidence` as destinations, the way item 75's line
above it already named `data_models`. And `check-scope.py` stops reporting a silence it cannot
distinguish from agreement: it says which keys it read, and names any top-level key containing
`scope` or `confidence` as a near-miss — a shape, not a spell-checker.

**84. A `PROJECT.md` feature carries the elements the format marks required.**
*Addresses P67. Depends on 81.*
The table's first column is split into *Field* / *Written as* / *Required*, and
`check_project_context()` asserts `<name>` and `<files>`, naming the attribute case as such
rather than reporting the element as absent. **Undefined extra children stay accepted**, and the
check asserts that they are: nothing measured says unknown content is a defect.

---

## U. What the registries did not cover

**Three files in this repository exist to tell an absence from a decision.** `readers.md`
distinguishes an element with no reader from one with a recorded reason it has none; `checks.md`
distinguishes an assertion with an owner from an ownerless row kept deliberately; `parity.md`
distinguishes a settled asymmetry from one marked `open`. Asking what had no such file produced
this section.

**P68 — the findings have no registry, and the plan is organised around them.**
*Verification: measured against the plan, the ledger and the suite.*
Of the ids in `P1..P68`: 57 are defined by a `**PN — claim**` heading here, 57 are guarded by a
`finding=` check in the suite, and **ten needed a judgement**. P9 was explicitly *retracted* and
P13 was *closed* by measurement — and both were simply absent from every index, so nothing could
tell a decision from an omission.

**And the most recent work was the worst offender.** P58–P68 — the findings in sections S, T and
this one — existed only as `finding=` tags in the suite and words in commit messages. **Eleven
findings with no definition anywhere**, created in two days by the work that was closing exactly
that shape of defect elsewhere. Placing them under headings in S and T is part of the remedy;
the registry is the rest of it.

> **A note on the id space, because it corrupted the first count.** `P0`, `P1` and `P2` are also
> core §4's criterion priority levels, so a bare `\bP\d+\b` matches `priority="P0"`. The first
> measurement said 58 findings and was wrong. **`P0` is not a finding.**

---

**85. Every finding has a status, and a closed one names where it was settled.**
*Addresses P68. Depends on nothing.*

`docs/skills/plugin-2.0-findings.md` — one row per finding: id, the claim in a line, a status in
`closed` · `retracted` · `open` · `superseded`, and what settled it. **`retracted` is not
`closed`**, and P9 is why the column has four values: recording a predicted failure with no live
instance as *closed* would claim a fix that never happened, and deleting the row would lose the
retraction the plan explicitly kept.

`tests/check-findings.py` owns it, and **has no `checks.md` row on purpose**: that table is
*every assertion the toolchain makes about an artefact*, and this asserts nothing about a PRD, a
CRD or a task — it audits the project's own record-keeping. `mutate.py` and `probe-p1.py` live in
`tests/` on the same basis.

Its load-bearing assertion is the one that decays without help: **a row naming a regression check
must name one that exists.** A check renamed in the suite leaves a row pointing at nothing, and
the row still reads as guarded.

---

## V. The row the registry kept, and what it cost to decide

**`checks.md` has carried an ownerless row since item 79, and it is the only one.** The rule that
put it there is that an assertion this plan specifies and does not build is a fact about the
project rather than an omission from it. The rule that takes it out is the other half of the
same idea: a row kept deliberately is also a row that might turn out not to be worth building,
so the question is answered by measurement rather than by the row's continued existence.

**P69 — the CRD path's unbounded input is generated, and nothing measures it.**
*Verification: measured against the live sixth-crossing artefact, and against both producers.*

Item 18 split the PRD into one prompt per feature and gave `check-prd-size.py` the job of making
the split honest. Item 79's `Paths` column asked why that script refuses a CRD, and the answer
moved the question: **the unbounded input on the CRD path is not the CRD.** A CRD is authored by
a person in an interview and is as long as a person writes. `PROJECT.md` is generated from a
codebase, and it is read whole because — unlike a PRD — there is nothing in it to split.

**Three measurements, and the first two are the ones that make it reachable rather than
arithmetical.**

- `crd-investigate/SKILL.md`'s Error Handling table already carries the row
  **`Very large codebase | Limit scope, note truncation`**. The situation is anticipated *in the
  producer's own instructions*, and the entire mitigation is a prose instruction to a model to
  truncate and mention it, with nothing measuring whether it did. **That is P5's shape one
  artefact over**, and it was written down before this finding was.
- `project-context-finalizer` is **additive and unconditional**: it runs after every `/execute`,
  adds one `<feature>` per implemented feature, one `<endpoint>` per api export and one `<model>`
  per schema export, and preserves what is there. Nothing compacts. So the file grows with the
  number of runs a project has had — which is why no single generation's output limit bounds it,
  and why the greenfield path is a producer of the brownfield path's input.
- On the live artefact: **13,803 chars for 7 features, 7 endpoints and 4 models** — 3,834
  estimated tokens, about 300 entries of headroom against the 60k budget. And **40% of it is the
  markdown half**, the component tree and the pattern list, which grow with *files*. The row's own
  arithmetic counted only features and registry entries, so it understated the rate.

**What nothing measured**: a `PROJECT.md` of 77,006 estimated tokens — 28% past the budget —
passes `check-project-md.py` with `exit 0` and the words *PROJECT.md valid*, and
`check-prd-size.py` exits 2 rather than looking at it. Measured 2026-09-10, before the check
existed.

---

**86. `PROJECT.md` fits the prompt it is about to be sent in.**
*Addresses P69. Depends on item 79 for the row, and on item 18 for the estimator.*

`check-project-size.py`, beside `check-prd-size.py` and taking the divisor and the budget **from
it by import** — 3.6 chars per token is this repository's own corpus measurement and there is to
be one copy of it. It measures the whole file, because the whole file is what every consumer
loads, and reports the decomposition — markdown half, `<features>`, each `<*-registry>` — plus
what one more entry costs, so that an author over the ceiling can see which term grew.

**A new owner rather than either script that already reads this file.** Extending
`check-prd-size.py` would contradict the `prd-only` cell item 79 decided and wrote a reason for.
Extending `check-project-md.py` would give one script two assertions, which
`tests/test_toolchain.py` already refuses — *"two assertions share an owner … a script that owns
two assertions has two reasons to exit 1"* — and that script's own docstring draws the line:
*well-formedness is this script's job*.

**Four callers, because four files load `PROJECT.md` into a prompt.** `commands/crd-context.md`
is the write side and the only one where a person can act on the answer; `commands/crd.md`,
`skills/crd/SKILL.md` and `skills/breakdown/SKILL.md` are the read sides. A guard wired into one
of them measures one of four reads.

**An absent `PROJECT.md` is exit 0**, following `check-project-md.py`: greenfield has none and
never will. It prints no measurement, so a run that measured nothing cannot be read as a run that
measured and was content.

---

## W. The rule the prose called mechanical

**Found while planning gap closure** ([`gap-closure-plan.md`](gap-closure-plan.md) §2.1), not by a
run: the plan needed a script on the CRD path to test, and there was none.

**P70 — a CRD's `ready` rule is stated as mechanical, and no script runs it.**
*Verification: every script under `schema/` and `skills/` searched for a comparison of `<workflow>`
with gaps; none exists.*

Item 48 gave the CRD `<gaps>` and, with it, the one-way test `<definition>` already had: a CRD
marked `ready` must not carry a `specification` gap. Core §6 says the CRD *"now has the same
one-way mechanical test"*. What existed was an instruction in `commands/crd.md` telling the model
to demote the document, a suite check that the sentence was written, and `check-status.py`'s CRD
branch, which validated gap shape and passed an empty escalation list. **P61's shape again**: the
element on both paths, the check over it on one.

Downstream still stopped the run — `select-features.py` refuses a `specification` gap whatever the
workflow says — so nothing was ever waved through. What was lost is the report at the one point a
person is there to act on it. Closed by `check-status.py`'s CRD branch, which now reports the
contradiction, accepting the pre-item-45 `<status>` spelling on read.

**P71 — the mutation harness drops a failing check printed directly below another.**
*Verification: one mutant reproduced as MISSED through the harness with the full suite, as CAUGHT
with a one-check suite, and the suite's raw output shown to contain both FAIL lines while
`failing_checks()` returned one.*

Found by the same work's mutation round. `failing_checks()` matched `^  FAIL\s+(.*?)\s{2,}` in
multiline mode, and `\s` matches a newline: the trailing run consumed the line break and the next
line's indent, so a second FAIL on the very next line had no `^` left to match. A `closed="soon"`
mutant broke two neighbouring checks and the one it expected was dropped. **It can only
under-count** — false MISSED, never false CAUGHT — which is why no earlier round looked wrong; but
it also hides an adjacent orphan, the thing guard 2 exists to show. Closed by matching `[ \t]`.

---

## X. What the gap-closure run reported and nobody verified

**Found by a run, verified afterwards.** The gap-closure live run
([`gap-closure-plan.md`](gap-closure-plan.md) §12) reported three things outside its change and
recorded them unverified. Each was then reproduced before it was given an id, and each turned out
to be at least as bad as reported.

**P72 — `/breakdown` resolves a CRD's references against the CRD's directory, and stops on every
well-formed CRD.**
*Verification: `check-references.py` run on the current fixture's CRD laid out as a project has
it: five `DANGLING` and exit 1 without `--project-path`, zero and exit 0 with it.*

Phase 1 step 11 documented `check-references.py {document}` and nothing else. The script's
`resolve()` tries the project only when one is given, so `<project-ref>PROJECT.md</project-ref>`,
the spelling every CRD template writes, became `docs/crd/PROJECT.md`, and every `<feature-ref>`
went unresolved with it. The run reported a misresolution. **Followed literally, the instruction
stopped the run.** The run got past it by passing a flag the instruction never named, which is
P62's shape one argument along. `check-gate.py` and `crd-format.md` already passed the flag; the
skill was the one caller that did not. Closed by naming it in step 11, with a check that runs the
documented command.

**P73 — every resume in `/breakdown` skips on existence, so a changed document is never
re-analysed.**
*Verification: the skip conditions in Phases 2, 3 and 4 read, and every script under
`skills/breakdown/scripts/` searched for a record of what an artefact was built from; none
exists.*

The report named Phase 2. The same test guards Phase 3's `layer_plan.json` and every layer's
`.done`, so a stale analysis carries through all three. Coverage cannot catch it, because it
reads the manifest those same skipped phases wrote. Closed by `check-resume.py`, run at step 8
before anything reads the document. It records the sources' hashes on a fresh run, and refuses to
resume from artefacts whose sources changed or were never recorded. **It refuses rather than
regenerating**: the artefacts may be a task set somebody reviewed.

**P74 — `analysis.json`'s `gaps` has no named shape where it is written, and a run wrote it
without the gap text.**
*Verification: both runs' `analysis.json` read. The PRD run's is `{open: [...], closed_count: 2}`
with rows copied from `check-status.py --json`, which have no `body`. The CRD run's is a list with
the text under `text`.*

The report said *"no script reads the field"*, which is true and is why nothing failed. Its reader
is the task generator, which carries each gap's text into `<context>`. A row with no `body`
reaches a task as a kind and a date. It did no harm only because that run's one gap sat in an
excluded feature. P65 again: `breakdown-analyze-prd` documents the shape, and `/breakdown`, which
writes the merged file, never named it. Closed by naming `{feature, id, kind, raised, body}` at
both writers, checked against the analyzer's parsed example.

**P75 — `/breakdown`'s tasks directory is resolved against whatever directory its fork is in.**
*Verification: `resolve-output.sh` calls extracted from the transcripts of five live runs of one
command. Each resolved `docs/tasks/<slug>` from a different directory: the plugin checkout
(refused), the workspace twice, and the target app twice.*

**Found by the live run that verified P73, and the reason it could not measure P73's refusal.**
The run edited the CRD between runs. The next run's tasks directory had moved, so the resume
check found an empty directory, reported `nothing to resume`, and every phase regenerated.
`resolve-output.sh` stated its premise as *"this process's working directory, which is the
caller's"*. That premise was never measured, and it is false: the caller is itself a fork that
changes directory freely. F4 was a sub-skill resolving a relative path against its own
directory; its fix moved the resolution one fork up and kept the assumption.

**Why nothing saw it.** The F4 check runs the script from a working directory the test sets
itself, so it tests the arithmetic and not the call. The brownfield harness started `/breakdown`
from the workspace and graded `app/docs/tasks/<slug>`. It passed because its fork **ignored the
documented default** and chose the project convention itself. The model's improvisation and the
grader agreed. And before P73 nothing depended on the directory staying put: a task set in the
other place was still a complete, valid one.

Closed by deriving the tasks directory from where the document sits. From the `docs/` holding
`crd/` or `prd/`, it is `tasks/<slug>`. That is `/crd`'s hand-off convention on the CRD path and
the fixture layout on the PRD path. A document anywhere else is refused unless `--tasks-dir`
names an absolute directory ending in the slug. The check runs step 5's documented command from
three working directories on both paths.

---

## 6. Summary

| # | Item | Addresses | Grade |
|---|---|---|---|
| 1 | Feature template: drop `<priority>`, extend `<status>` | P6, P8, P13 | Consistency |
| 2 | Structure `<notes>` | P4 | Correctness |
| 3 | Status derivation script | P7 | Consistency |
| 4 | Migrate corpus conventions, reclassify | P6, P14 | Consistency |
| 5 | Retire `<phases>`; phasing is priority plus gaps | P12 | Consistency |
| 6 | Phase 6 becomes an executable consistency check | P7, P9, P16 | Consistency |
| 7 | `--resume` re-checks all features | P7 | Consistency |
| 8 | Criteria-challenger sub-agent | P2 | Structural |
| 9 | `/prd` prose guards → scripts | P16 | Structural |
| 10 | Per-feature authoring | P5 | Structural |
| 11 | `what-next.md` hybrid design | P10 | Structural |
| 12 | Migrate `what-next.md`, keep dual marker | P10 | Structural |
| 13 | Skip won't-have / excluded / superseded | **P1** | **Correctness** |
| 14 | `--priority <threshold>` | **P1** | **Correctness** |
| 15 | Refuse `tbd`, and name what was skipped | P1, P2 | Correctness |
| 16 | `source-feature` + `moscow` on tasks | P1, P3, P15 | Correctness |
| 17 | Carry criteria and data model into tasks | **P2, P4** | **Correctness** |
| 18 | Per-feature analysis + size refusal | **P5** | **Blocking** |
| 19 | `/execute` reports tier | P1 | Correctness |
| 20 | `/execute` refuses won't-have | P1 | Correctness |
| 21 | Runtime test for P1 | P1 | — |
| 22 | Shared artefact schema check | P10, P11 | Structural |
| 23 | Regression checks | all | — |
| 24 | Finish version stamping | (4.5) | Structural |
| 25 | `architecture.md`, in PROJECT.md's schema, with a reader | **P11, P17** | **Correctness** |
| 26 | Seed PROJECT.md on greenfield | **P17** | **Correctness** |
| 27 | `<depends-on>`; derive ordering rather than authoring it | P1, P11 | Structural |
| 28 | Widen `architecture.md` into the project's rule file | **P18** | **Structural** |
| 29 | `<needs-clarification>`, and narrow the placeholder ban | **P19** | **Correctness** |
| 30 | Coverage check between `/breakdown` and `/execute` | **P20** | **Correctness** |
| 31 | Derive the layer set from content, both paths; no threshold | **P21, P33** | **Correctness** |
| 32 | A rendered view over the task set | **P22** | Structural |
| 33 | Adopt EARS; retire Given/When/Then | **P23** | **Correctness** |
| 34 | Priority per requirement + `--requirement-level` | **P1** | **Correctness** |
| 35 | `<architecturally-significant>` flag | **P25** | Structural |
| 36 | Decision-record template, conventions, `**Drives:**` | **P24, P25** | Structural |
| 37 | Decision / principle / constraint discriminator | P16 | Consistency |
| 38 | Gate between `/breakdown` and `/execute` | **P25** | Structural |
| 39 | Validate references that leave the PRD | **P24** | **Correctness** |
| 40 | The well-defined bar, as a gate on `defined` | **P26** | **Correctness** |
| 41 | A migration guide an agent can execute | (all schema items) | **Blocking** |
| 42 | A rename operation with a checkable postcondition | **P27** | Correctness |
| 43 | A fixture per schema version; schema version ≠ plugin version | **P28** | **Blocking** |
| 44 | One schema core, cited by both paths | **P30** | **Blocking** |
| 45 | Three status vocabularies, three distinct names | **P29** | **Correctness** |
| 46 | EARS collapses the CRD requirement/criterion split | **P31** | **Correctness** |
| 47 | `P0\|P1\|P2` on both paths | P1, **P31** | Consistency |
| 48 | CRD gains gaps, `--resume` and a pre-write guard | **P32** | **Correctness** |
| 49 | PRD gains `<scope>` and `<confidence>` | P19, P21 | Structural |
| 50 | Parity as a regression check | **P30** | — |
| 51 | A Design phase in `/prd`, between 3 and 4 | **P17, P25** | **Correctness** |
| 52 | A context check at `/prd` initialization | **P34** | **Correctness** |
| 53 | Declare `<repo-structure>`; refuse `multi-repo` early | **P36** | **Correctness** |
| 54 | A working directory for verification | P36 | Correctness |
| 55 | The ledger states what it verified | **P37** | Consistency |
| 56 | Typed `<banned>` kinds + `<task-limits>`, enforced at both ends | P16, **P35** | **Correctness** |
| 57 | Impact analysis reports contracts, not just APIs | **P35**, P30 | Correctness |
| 58 | One table of assertions; item 6 becomes a caller | P16 | Structural |
| 59 | A runtime test across the breakdown→execute boundary | **P22**, P20 | **Blocking** |
| 60 | `execute-layer` stops maintaining a derived file | **P38** | **Correctness** |
| 61 | `plan-layers` stops contradicting its own derivation | **P39** | **Correctness** |
| 62 | The task schema admits every layer the layer graph can produce | **P40** | **Correctness** |
| 63 | A task's `<verification>` is not editable by the run it judges | **P41** | **Correctness** |
| 64 | The generator is told where its verification commands run | **P42** | Correctness |
| 65 | A task may name every feature it descends from | **P43** | **Correctness** |
| 66 | `/execute` takes its layer set from the plan, not its own prose | **P44** | **Correctness** |
| 67 | A snapshot that replaces another says what changed between them | **P45** | Correctness |
| 68 | Give `<review>` a producer, and stop denying it has one | **P46** | **Correctness** |
| 69 | The caller table is checked in both directions | **P47** | Structural |
| 70 | A documented invocation names the plugin root | **P48** | Correctness |
| 71 | No shipped artefact describes a state the toolchain has left | **P49** | Consistency |
| 72 | The documents that describe the repository are checked against it | **P50** | Consistency |
| 73 | No task may depend on an interface a later layer exports | **P51** | **Correctness** |
| 74 | A declared layer order is obeyed, not improved on | **P52** | **Correctness** |
| 75 | The CRD's schema contracts reach the task that implements them | **P53** | **Correctness** |
| 76 | `<architecturally-significant>` on a CRD | **P54** | **Correctness** |
| 77 | The gate's assertions reach a CRD | **P55**, **P56** | **Correctness** |
| 78 | A run writes nothing into the toolchain, and the harness proves it | **P57** | **Correctness** |

**Sequence.** The previous version of this section was a set of pairwise constraints, each
correctly reasoned, that had never been composed — eight items were separately asserted to be first
(R11). Composed, they gave six phases; four more have since been added by measurement rather than
by reading — Phase 7 by running the toolchain, Phase 8 by finishing what the plan had only named,
Phase 9 by the fourth crossing, and Phases 10 and 11 by verifying the implementation
against this document.
**Every phase is independently shippable**, and each is defined by what becomes possible once it
lands rather than by size.

### Phase 1 — Fix what is broken today. No schema change.

`23a` · `60` · `39` · `54` · `55` · `42` · `21` · `9`

Nothing here touches `<criterion>`, `<status>`, `architecture.md` or the migration; all of it is
reversible; and every item fixes a defect that exists now rather than preparing for one that might.

- **23a** — `state-schema.md` says `2.0`, `write-state.py` writes `3.0`. A live producer/spec
  mismatch, in the one place the toolchain already versions a schema (P28).
- **60** — **immediately after 23a, and found by doing it.** `execute-layer` reads and writes the
  2.0 shape of the file 23a just documented, including a merge loop that cannot fire (P38).
- **39** — 190 unchecked citations. Depends on nothing in this plan.
- **54** — monorepo verification runs from the wrong directory today.
- **55** — the ledger implies a build it never ran.
- **42** — the cheapest possible rehearsal of item 41's postcondition machinery, on 8 files rather
  than 64. **This is the one to watch:** if the pattern is awkward here it will be far worse there.
- **21** — measure P1 and the authoring baseline *before* changing anything they describe.
- **9** — `/prd`'s prose guards become scripts; the mechanism is now measured, not assumed.

### Phase 2 — Make the rest testable.

`18` · `43` · `52` · `53`

**18 first, and it is Blocking**: nothing can be tested end to end on a realistic PRD while
`analyze-prd` is handed 174k tokens in one prompt. **43** supplies the fixture pair that makes 41
and 24 testable at all. 52 and 53 are a `test -f` and a declaration.

### Phase 3 — The architecture artefact. One piece of work.

`25` + `28` + `37` + `51` + `31` + `56` + `26` + `57`

25 defines the artefact, 28 fills it, 37 says what belongs in it, **51 is its producer** — and a
file nothing writes was the defect that produced item 51. 31 makes the layer *set* derived and 56
makes `<banned>` enforced, both being 28's opinions becoming real. 26 closes the greenfield loop;
57 follows the registries.

Splitting these means designing the same file four times.

### Phase 4 — The schema core and its migration.

`44` → `45` → `41` → `33` · `34` · `29` · `27` · `35` · `1` · `2` · `4` · `5` · `11` · `12` · `36`

**44 is first and the order inside it matters.** A shared core defined *after* the elements it
shares is a merge, not an extraction. **45** next, because renaming three vocabularies is cheap
before they have consumers and expensive after. **41 is written here, not after** — every item
below rewrites artefacts that exist, and none can land until the migration is specified and
verifiable.

**4 and 5 are the template's other half**: 4 migrates the conventions the corpus invented
(`excluded` + `<rationale>`, `superseded` + pointer) into the templates and reclassifies against
them, and 5 *removes* `<phases>`. A removal is a schema change like any other and belongs in the
same pass as the additions, or the migration runs twice.

### Phase 5 — Consumers, and the parity pass.

`16` · `17` · `3` · `6` · `7` · `8` · `40` · `58` · `13` · `14` · `15` · `19` · `20` · `30` · `32` ·
`46` · `47` · `48` · `49` · `50` · `38` · `24` · `10` · `59`

Small, once the schema carries the data. **30 immediately after 16** — it has nothing to check until
`<source-feature>` exists. **59 as soon as 17 and 30 land**, because it is the first test that
crosses the boundary those items specify. **46 and 47 immediately after 33 and 34**: they are the
same change reaching the CRD path, and letting them lag is exactly how two vocabularies acquire
consumers.

**Twenty-four items is more than one sitting**, and the constraints above admit one grouping that
keeps each commit to a single concern. It is recorded in
[`plugin-2.0-progress.md`](plugin-2.0-progress.md#phase-5--consumers-and-the-parity-pass), not here:
the order *within* this phase is a claim about dependencies and belongs to the specification, while
where the commits fall is a claim about a context window and does not.

### Phase 6 — Hold it in place.

`22` · `23`

Last, deliberately. A schema check written against a schema still moving is a check that gets
edited rather than obeyed.

### Phase 7 — What the run found.

`61` · `62` · `64` · `63` · `65` · `66`

**Not planned; measured.** Phases 1–6 were specified by reading the corpus and Phase 7 was
specified by watching the toolchain run, which is why it is last in the document and first in
usefulness: none of its five items was visible to 112 regression checks.

**61 and 62 land immediately** — both are one-line contradictions in shipped instructions, and a
document that requires a layer its own schema forbids should not survive the commit that noticed
it. **64 next**, because it is a brief and costs nothing. **63 before 65**: a guard on task files
is cheap and its absence makes every later result harder to trust, while 65 is a schema version
and wants the guard already in place before task files start changing shape.

**66 last, and it is not ordered by dependency.** It depends on nothing and could be done first;
it is last because it was found last — while implementing 63 — and because its severity is
easiest to misread. A silent zero-task run is worse than a loud failure, and the item is one
file's worth of work, so anyone reordering this phase should move it *earlier* rather than later.

### Phase 8 — The residue.

`8a` · `8b`

**Not plan items, and that is the point of the phase.** Both were things the plan finished by
*naming*: `SCHEMAS.json` had recorded the schema-6 content work through four phases, and
`readers.md` had carried three `open` rows since item 23's audit. The grouping is the ledger's
rather than this document's, which is why the two groups have letters and not numbers.

### Phase 9 — The guard at the right boundary.

`67`

**One item, specified by the fourth crossing** — the first run item 63's guard was ever active
for, and the first to find a defect in it. It is a phase of one because it depends on item 63 and
on nothing else, and because a guard measuring the right thing at the wrong boundary is worth
fixing before the next crossing rather than after it.

### Phase 10 — What verifying the implementation found.

`68` · `69` · `70` · `71`

**68 first**, because it is the only one of the four a user meets: a `/prd` run today is told that
a place to record a review does not exist, in the schema version whose headline change is that
place. **69 before 71**, because 71's third part is a decision about what a stamp means and 69's
reverse check is what makes *last reconciled at* measurable rather than asserted — the decision is
cheap once the alternative has been built. 70 is mechanical and depends on nothing.

**Three of the four are stale prose in a shipped artefact**, so every check here is watched failing
first and every fix carries a mutation round. This ledger has recorded five times that a check
asserting text rather than the claim it carries passes while doing nothing, and a phase made
entirely of text fixes is where that failure would be invisible.

### Phase 11 — The documents catch up.

`72`

**Last, and it could not have been earlier.** A check that the documents describe the repository
is a check against a repository still moving; written during Phase 4 it would have been edited
rather than obeyed, which is the argument Phase 6 made about item 22 and the reason this file
keeps making it.

**Its finding is about the suite rather than the documents.** Every check in the suite reads
`skills/`, `commands/`, `agents/`, `schema/` or `tests/`. Nothing read the four documents at the
repository root, so the only artefacts with no automated reader at all were the ones a human
reads first — and they drifted for nine phases without a single check going red.

---

### Phase 12 — The graph is load-bearing.

`73`

**Open question 7's experiment, finally run**, and the design was committed before the
measurement — which was the point. The layer graph turns out to be load-bearing, so a wrong one
is a defect rather than a preference, and item 73 makes it an exit code instead of a model's
judgement.

### Phase 13 — The declared order is obeyed.

`74`

**A second script rather than a widening of 73**, because *is this graph valid* and *did the run
obey it* are two questions and this repository gives each one an owner. Its finding corrected two
claims of its own along the way, both recorded in the ledger rather than smoothed out.

### Phase 14 — What the fifth crossing found.

`77` · `78`

**The first CRD run since this plan began**, so a regression question rather than a new one. Two
of the sequence's guards had stopped reaching it, and the third finding arrived from `git status`
rather than from any check: a run had written a stderr capture into the plugin checkout, which no
rule forbade because every guard covered paths somebody *declared*.

### Phase 15 — The else branch, measured before it was believed.

`79`

**Section R's closing sentence, measured.** The measurement changed what got built: the class is
not the `isdir` call — a lint would have flagged the canonical dispatch and found none of the
three defects — it is that nothing recorded which paths an assertion is supposed to reach. P58,
P59, P60 and P62 are fixed in the same phase, because a column asserting reach is worth nothing
while four assertions do not.

### Phase 16 — The sixth crossing.

*(no items)*

**The first crossing driven end to end by a program**, and the phase that specified the next
five. Four steps, four passes, four findings — and both of Phase 15's changes exercised live. Its
own instrument was wrong first, which is recorded because *a refused run is not a failed
measurement*.

### Phase 17 — A task file parses.

`80`

**P64 first of the four**, because it is the only one where three readers each reported a
different symptom for one cause and none of them pointed at the broken file.

### Phase 18 — A feature declares its build state.

`81`

**P63.** Two holes, and the second made the first invisible: a validator with a branch for each
known spelling and none for neither, behind an escalation path that skipped content checking
entirely.

### Phase 19 — The manifest carries what `/execute` reads.

`82`

**P66**, plus a second defect found while measuring it — two version constants that had disagreed
since item 65, so every manifest this toolchain wrote warned against a reader inside it.

### Phase 20 — The analysis fields have names.

`83`

**P65**, the last of the sixth crossing's four. Item 49's only reader could not see its input and
printed the same sentence it prints when a document predicted nothing.

### Phase 21 — Item 81's residue.

`84`

**P67.** The two fields item 81 deferred for *no evidence*, once the crossing's artefact was read
properly — and the format table that explains why two independent producers wrote the same wrong
shape.

### Phase 22 — The findings get a registry.

`85`

**P68**, and it is the axis this plan never gave itself. Three files already told an absence from
a decision; findings — the thing the whole document is organised around — had none.

---

**What this ordering does not do.** It does not price anything. The grades rank severity, not
effort, and the only cost estimate this plan can honestly carry is item 41's — taken from the first
ten features migrated rather than guessed here (A9). If the answer to *"we have a week"* is needed,
it is Phase 1, which is eight items, all reversible, all fixing something real.

---

## 7. Open questions

1. **Resolved by spike, 2026-08-24 — yes, via `${CLAUDE_PLUGIN_ROOT}`.** *(Was: can a command
   invoke a bundled script? Probe first.)* Measured against a throwaway plugin loaded with
   `--plugin-dir`; method and full results in [`probes/README.md`](probes/). The variable is
   expanded **by the harness at command-expansion time** — the transcript shows the user-role
   message already carrying the absolute path — so it is a harness feature rather than model
   inference, which is what item 9 needed.

   **One caveat that changes how scripts are written.** `CLAUDE_PLUGIN_ROOT` is *not* exported to
   the spawned shell: the probe script read it as unset while running from an absolute plugin path.
   Text substitution in a command body works; a script reading the variable from its own
   environment gets nothing. **Pass the path as an argument.**

   A bare relative path fails (cwd is the project), and a command that names no path leaves the
   model to brute-force it — the control took eight tool calls including a `find /`. Neither is a
   mechanism; the variable is mandatory.
2. **Resolved — see items 25 and 26.** *(Was: where does the index's `<architecture>` block
   belong?)* Feature-local architecture goes to `<notes><data-model>`; cross-cutting
   architecture goes to a new `architecture.md` sharing PROJECT.md's schema. The residual
   question is narrower: **should `architecture.md` and PROJECT.md be one file from the
   outset**, rather than two that converge after `/execute`? One file is simpler and removes a
   migration, but it means writing a *descriptive* artefact prescriptively, before any code
   exists — and `crd-context-update` compares PROJECT.md against a git hash it would not yet
   have. Two files with a defined seeding step is the safer default; one file is worth
   revisiting if the seeding proves lossy.

   **Item 28 settles this, in the direction of two files.** Once `architecture.md` also carries
   layer definitions, test policy and banned patterns, it is unambiguously the *prescriptive*
   artefact and PROJECT.md is unambiguously the *descriptive* one. Merging them would produce one
   file where half the content is hash-stamped against a commit and half must be read before any
   commit exists. Item 26's seeding step stays the join between them.

   **And the scope half is now settled too — both live at the project root.** The question that
   forced it: `/prd` supports several PRDs in one repository, so a per-PRD `architecture.md` would
   permit two layer graphs and two test policies for one codebase, and item 26 would seed a single
   `PROJECT.md` from whichever ran last. Two files, both project-scoped, one prescriptive and one
   descriptive, joined by item 26. **Resolved.**
3. **Resolved — see item 27.** *(Was: should `/breakdown` consume the task-generation order?)*
   No. The order was model-deduced during `/prd`, not human-authored, so consuming it means
   preferring one model's unvalidated inference to another's — while duplicating
   `breakdown-plan-layers`. Capture `<depends-on>` instead and derive the order. The residual
   question: **is `kind="data|runtime|reference"` the right axis?** It is the minimum that
   separates "needs this to exist first" from "mentions this", which is what items 14 and 27
   require; whether layer assignment needs a finer distinction will not be knowable until
   `plan-layers` consumes it.
4. **Resolved — see item 34.** *(Was: does `--priority must-have` produce a coherent build?)*
   Criterion-level priority dissolves the closure problem rather than working around it: a
   must-have that depends on a could-have pulls in **that feature's `P0` criteria**, not the whole
   feature, so the tier boundary stops collapsing and the cost of closure becomes computable. The
   measurement that made this urgent is kept below, because it is what item 34 has to answer for.

   *Measured, and the answer under feature-level filtering alone was
   probably no.* Filtering yields a buildable slice only if must-haves are closed under their
   dependencies. In the corpus, **9 of the 13 must-have features carry cross-tier references —
   49 of them in total** — to should-, could- and won't-have features.

   The measurement counts *references* (inter-feature links), which are not all build
   dependencies; some are "see also". But the ratio is high enough that item 14 cannot assume a
   filtered set is coherent, which is why the question was raised.

   *Three options were weighed before item 34 dissolved the problem*, and they are recorded because
   each has a cost worth knowing: filter and report the dangling references; filter with dependency
   closure, pulling in the lower-tier features a must-have needs (which quietly rebuilds the tier
   boundary it was meant to respect); or treat the reference graph as the real ordering and let
   MoSCoW select roots rather than members. **Item 34 took none of them** — criterion priority means
   closure costs a thin slice rather than a whole feature. What survives is item 27's problem, not
   item 14's: distinguishing a genuine dependency from a cross-reference is work the schema does not
   yet support, since both are plain markdown links.
5. **Resolved — see item 29.** *(Was: what is `blocking`'s default, and who sets it?)* The
   question presupposed a boolean on a `<needs-clarification>` element that no longer exists.
   `<gaps>` carries `kind` instead, and the kind decides: `specification` and `decision` stop a
   run, `dependency` stops it until the dependency is available, and `ownership` and `evidence`
   warn. Nobody sets a default, because there is no boolean to default — which is the better
   answer to the overnight-run objection that prompted the question, since three of the five kinds
   warn rather than halt.
6. **Dissolved — see item 31 and P33.** *(Was: does item 31's threshold belong to the change or
   to the project?)* The question presupposed a threshold, and item 31 no longer has one. Layering
   answers *does this change span dependency tiers*, which is decided by what the change touches;
   a file count was a proxy for effort, which is a different quantity and a worse one. The CRD path
   already derives tiers from `<impact-analysis>`; the fix is to extend that to the PRD path, drop
   the unconditional integration layer, and let the single-tier single-task case collapse on its
   own.

   *What the question got right, and it is worth keeping:* the `small` = 1–3 files rubric **is**
   vendored in the plugin where no project can change it, and so is the layer graph — both are
   rows for P18's table. Demoting `<scope>` to a cross-check means nothing routes on it, so the
   rubric being wrong for a given project is now a reporting nuisance rather than a wrong build.
7. **Resolved by experiment, 2026-09-08 — LOAD-BEARING.** *(Was: is the layer graph load-bearing for quality, or only for convention?)* The measurement, its three arms and the three defects in the experiment itself are at the foot of this item; the mitigations it mandates are item 73. Everything below is the reasoning as it stood before the run, kept because the decision rule was written in advance and the run has to be readable against it.
   *(Was: is P18 the point at which this stops being a PRD toolchain?)* The identity framing was
   the wrong one, and it made the question unanswerable. `/breakdown` knows three separable things
   and item 28 touches only the first:

   | | Touched by item 28? |
   |---|---|
   | **Domain opinion** — five tiers encoding a template-built CRUD web app | **yes**, becomes a parameter |
   | **Process** — batching, generate → review → retry, self-containment, interface contracts, task sizing | no |
   | **Mechanics** — path resolution, manifest from files that exist, worktrees, ledger, merge queue | no |

   The process and the mechanics are the bulk of what the tool knows, and neither is
   architecture-specific. So the tool does not hollow out. **Three real losses remain**, and they
   are what the question should be about:

   - **Free dependency ordering.** *Models before endpoints before UI* is a genuine dependency
     truth for that app class. Item 27 replaces it with declared `<depends-on>` edges — and on the
     corpus, inter-feature references are 40% one-way and ambiguous between *depends on* and *see
     also*. A known-good default traded for user-declared edges can be a downgrade.
   - **A guardrail on a small model.** `breakdown-plan-layers` runs on Haiku. A fixed graph is a
     strong prior that stops it inventing a bad decomposition. Removing the prior asks a small
     model to invent an architecture — which is what P18 says the toolchain should not do, but the
     toolchain at least does it *consistently*.
   - **The failure mode moves and gets quieter.** From *"the toolchain's opinion was wrong for my
     project"* — visible, and P18's complaint — to *"my rule file was wrong and the toolchain
     obeyed it"*, which is silent and hard to attribute.

   **Two things narrow the question further.** Item 31 already makes layer *selection*
   content-derived on correctness grounds, so part of the domain opinion is leaving regardless of
   how this resolves. And the one piece that genuinely does not generalise is
   `layer0-templates.md` — python/go/tanstack scaffolding is dead weight for a CLI tool or a
   library. That is a reference file, not the pipeline.

   **So the answer is mitigations rather than a decision, and one experiment.** Ship the five-tier
   graph as the *default* rather than requiring a rule file; validate any supplied `<layers>`
   (acyclic, every layer reachable, no task stranded); report which graph was used, so a bad rule
   file is attributable. Then answer the real question by experiment once item 43 exists: **run the
   fixture through the default graph and through a deliberately poor one, and compare the task
   sets.**

   **And the rule for reading the result, written before it is run (R15).** An experiment with no
   decision attached is a measurement nobody has to act on.

   | Outcome | Decision |
   |---|---|
   | The poor graph produces materially worse tasks | The graph is **load-bearing**. Item 28 still ships — but the shipped default becomes a *baseline*, not merely a fallback: item 43 gains a third arm comparing a project's graph against it, and `/breakdown` reports when a supplied graph decomposes materially differently. That is real cost, and it is only paid on this result. |
   | The two task sets are comparable | The graph was **convention**. P18 costs nothing, item 28 ships plain, and the shipped graph is a convenience. |
   | The difference is small or unclear | **Treat as load-bearing.** |

   The third row is the one that matters, and it is deliberately not "run a bigger experiment". The
   risk being measured is OQ7's own third loss — a failure mode that *"moves and gets quieter"* —
   and an ambiguous result about a silent failure is not evidence of safety. **Ambiguity resolves
   toward protection**, because the cost of protecting unnecessarily is a fixture arm and a report
   line, and the cost of not protecting when it mattered is a bad rule file obeyed without comment.

   *What this does not do is gate item 28 behind the experiment.* P18 is correctly graded the
   largest gap against the field, the experiment decides what ships **alongside** item 28, and
   Phase 3 does not wait for Phase 2's fixtures to have been run through twice.

   > **Run 2026-09-08, and the answer is LOAD-BEARING (V5).** Three live `/breakdown` arms on the
   > `schema-6` link-shelf fixture; harness, metric and decision rule committed at `3035f42`
   > *before* any arm ran, so "the criteria were fixed in advance" is checkable rather than
   > asserted.
   >
   > | Arm | `architecture.md` | Tasks | Result |
   > |---|---|---|---|
   > | **default** | none — shipped graph | 10 | `0-setup → 1-foundation → 2-backend → 4-integration`. **0 forward references.** `3-frontend` correctly dropped: link-shelf is API-only |
   > | **poor A** | inverted, prose said so | 14 | obeyed the graph. **16 forward references** — `L3-*` backend endpoints importing `Link`, `get_db`, `db_session` from `4-foundation`, which runs after them. `check-coverage.py` **0**, `check-gate.py` **0** |
   > | **poor B** | inverted, neutral prose | **0** | `plan-layers` silently reordered the declared graph to `0-setup, 4-foundation, 3-backend`; `generate-tasks` then refused — *"structural validity is not buildability… resolving that is not my call"* |
   >
   > **Neither poor arm is comparable to the default**, so the first row fires; and the two poor
   > arms contradict each other, which is the third row's definition of unclear. Both point the
   > same way. **The graph is load-bearing.**
   >
   > **The sharper finding is that the two poor arms differ at all.** The same graph produced a
   > silently unbuildable task set once and a clean halt once. **The toolchain's protection
   > against a wrong graph is a model judgement, not a guard** — it fired in one run of two. That
   > is item 4.13 arriving at open question 7, and it makes the mitigation an exit code rather
   > than the baseline comparison this item originally specified: a forward reference is
   > detectable *within* one task set, so nothing has to be compared against a default to find it.
   >
   > **Three defects in the experiment itself, recorded because they bound what it proves.**
   > *(1)* Poor A's `architecture.md` prose said the direction was inverted, and `plan-layers` read
   > it and wrote back *"the inverted direction is reported rather than corrected"* — **the fixture
   > explained the experiment to its subject**, which is item 21's lesson repeated one phase after
   > it was written down. Poor B is the re-run with neutral prose and is the arm that counts.
   > *(2)* One arm was lost to a workspace inside the checkout: `resolve-output.sh` refused it at
   > Phase 1 (F4's guard, correctly), the run exited 0 with no tasks, and that reads exactly like a
   > toolchain finding. The harness now refuses such a path itself. *(3)* The `unresolved`
   > secondary metric counts external libraries — `python`, `sqlite3`, `pydantic` — as unmet
   > contracts, so its `9 → 15` is noise. The verdict rests on the forward-reference count alone,
   > which is categorical and unaffected.
   >
   > **And one defect in the toolchain, found by the neutral arm and verified against the
   > artefacts rather than taken from the run's own report:** `breakdown-plan-layers` **silently
   > overrode the declared graph.** Declared `0-setup, 1-integration, 2-frontend, 3-backend,
   > 4-foundation`; emitted `0-setup, 4-foundation, 3-backend`. Its own SKILL.md says a project
   > that declares a graph gets its own and nothing grafted on. It is P16's shape — an instruction
   > the model improved on — and it is why poor B halted: the two phases disagreed. Carried as
   > **P52**.

---

## 8. Appendix — `<rules>` across five architecture patterns

These are the worked examples that produced **P35**, and they are kept for one reason: they are the
cheapest available test that item 28's schema still generalises. **Anyone changing `<rules>` should
re-express all five.** Three of the schema's leaves were CRUD-shaped until these were written, and
the defect that mattered most was exposed by the *default* case, not by an exotic one.

Only the distinguishing parts are shown; `<scaffold>` and boilerplate are elided.

### 8.1 Monolithic SPA — a chain, and two toolchains

```xml
<layers>
  <layer id="0" name="setup"       depends-on=""/>
  <layer id="1" name="foundation"  depends-on="0"/>   <!-- models, migrations -->
  <layer id="2" name="backend"     depends-on="1"/>
  <layer id="3" name="frontend"    depends-on="2"/>
  <layer id="4" name="integration" depends-on="2,3"/>
</layers>
<testing default="tdd" runner="pytest">
  <policy match="web/**"  kind="component" runner="vitest"/>
  <policy match="e2e/**"  kind="end-to-end" runner="playwright"/>
</testing>
<!-- registries are siblings of <rules>, not children: -->
<api-registry/> <schema-registry/>
<repo-structure>single</repo-structure>
```

The shipped default, and **it already needs two runners.** A single `runner="pytest"` cannot
describe the case the toolchain was built for, which is why P35 grades that leaf as wrong rather
than merely narrow.

### 8.2 Event-driven — a diamond

```xml
<layers>
  <layer id="1" name="contracts"      depends-on=""/>
  <layer id="2" name="infrastructure" depends-on="1"/>   <!-- topics, DLQs, retention -->
  <layer id="3" name="producers"      depends-on="1,2"/>
  <layer id="4" name="consumers"      depends-on="1,2"/>  <!-- independent of producers -->
  <layer id="5" name="projections"    depends-on="1,2"/>
  <layer id="6" name="orchestration"  depends-on="3,4"/>  <!-- sagas -->
  <layer id="7" name="integration"    depends-on="3,4,5,6"/>
</layers>
<testing default="tdd" runner="pytest">
  <policy match="contracts/**"   kind="schema-compatibility"/>
  <policy match="consumers/**"   kind="consumer-contract"/>
  <policy match="projections/**" kind="replay"/>
</testing>
<task-limits default="3">
  <limit match="contracts/**" max-files="5"/>   <!-- schema + producer + consumer + projection + test -->
</task-limits>
<banned>
  <rule kind="import" match="contexts/**" symbol="httpx|requests|grpc"
        reason="ADR-004: contexts communicate by event, never by call">
    <except match="contexts/*/adapters/outbound/**"
            reason="third-party APIs are called over HTTP by definition"/>
  </rule>
  <rule kind="change" path="contracts/**" action="modify"
        reason="published events are immutable; add a version, never edit"/>
  <rule kind="judgement"
        reason="ADR-011: consumers must tolerate replay">
    handler with side effects that are not idempotent
  </rule>
</banned>
<event-registry/>
```

Producers and consumers are **siblings**, which is the whole point of the architecture and the
shape a chain cannot express. This is what forced `depends-on` to be a comma list.

### 8.3 Microservices — the same graph, once per service

```xml
<layers>                                  <!-- shared -->
  <layer id="1" name="contracts"   depends-on=""/>
  <layer id="9" name="gateway"     depends-on="1"/>
  <layer id="10" name="integration" depends-on="1,9"/>
</layers>
<layers applies-to="services/*/">          <!-- instantiated per service -->
  <layer id="1" name="data"  depends-on=""/>
  <layer id="2" name="logic" depends-on="1"/>
  <layer id="3" name="api"   depends-on="2"/>
</layers>
<banned>
  <!-- "another service's database" is relational and a regex cannot express it, so the
       rule is re-expressed *stricter* and becomes exact: no service embeds a connection
       string in source at all; they come from the config that service owns. -->
  <rule kind="content" match="services/*/src/**" pattern="(postgres|mysql|mongodb)://"
        reason="ADR-002: no shared datastore across services"/>
  <rule kind="edge" from="services/*/" to="services/*/"
        reason="ADR-002: services are independently deployable; call by contract, not by import"/>
</banned>
<service-registry/> <api-registry/>
<repo-structure>monorepo</repo-structure>   <!-- multi-repo is refused: item 53 -->
```

**Flattening this is not a compromise, it is wrong.** One global graph would order every service's
data layer before any service's API, destroying the independent deployability the architecture was
chosen for. This is what forced `applies-to`.

### 8.4 CLI — nearly no layers at all

```xml
<layers>
  <layer id="1" name="core"     depends-on=""/>
  <layer id="2" name="commands" depends-on="1"/>
</layers>
<testing default="tdd" runner="pytest">
  <policy match="tests/cli/**" kind="golden"/>       <!-- stdout is a contract -->
  <policy match="tests/cli/**" kind="sandboxed"/>    <!-- was a <banned> rule: writes outside
                                                          the working directory. Runtime, so a
                                                          test asserts it. -->
</testing>
<banned>
  <rule kind="import" match="core/**" symbol="requests|httpx|urllib|socket"
        reason="core must be usable as a library"/>
  <!-- "writes outside the working directory" moved to <testing>: it is a runtime property,
       asserted by a test, not a pattern found in source. See 8.6. -->
</banned>
<command-registry/>       <!-- subcommands, flags, exit codes, output format -->
```

The degenerate case, and it needs **no special handling**: item 31 collapses a single-tier
single-task plan on its own. Worth keeping as an example precisely because nothing breaks — a
schema that only works for elaborate architectures would be its own kind of failure.

### 8.5 Mobile — a chain per platform, plus release constraints

```xml
<layers applies-to="platforms/*/">
  <layer id="1" name="models"      depends-on=""/>
  <layer id="2" name="data"        depends-on="1"/>   <!-- local store + sync -->
  <layer id="3" name="view-models" depends-on="2"/>
  <layer id="4" name="screens"     depends-on="3"/>
  <layer id="5" name="navigation"  depends-on="4"/>
</layers>
<testing default="tdd" runner="xctest">
  <policy match="**/screens/**" kind="widget"/>
  <policy match="e2e/**"        kind="device-matrix"/>
  <policy match="**/data/**"    kind="offline"/>     <!-- was a <banned> rule: network call with
                                                          no offline fallback. Runtime. -->
</testing>
<banned>
  <rule kind="judgement" reason="ANR: the main thread is not for I/O">
    blocking I/O on the main thread
  </rule>
  <rule kind="content" match="**/bundle/**" pattern="(api[_-]?key|secret|BEGIN [A-Z ]*PRIVATE KEY)"
        reason="the bundle is readable by anyone who downloads it"/>
  <!-- "network call with no offline fallback" moved to <testing>: runtime, see 8.6. -->
</banned>
<screen-registry/> <schema-registry/>   <!-- navigation graph + on-device store -->
```

Two platforms are two instantiations of one graph — the same `applies-to` that microservices need,
for an unrelated reason. **The one thing with nowhere to go is the release constraint** — minimum
OS version, signing identity, store submission. It is arguably `<scaffold>`'s business, and it is
the weakest of P35's findings because it is genuinely absent rather than mis-shaped.

### 8.6 What the exercise established

| | Held up | Broke |
|---|---|---|
| `<layers>` as a DAG | chain, diamond, degenerate | one graph per project (`applies-to`) |
| `<banned>` | the *idea* — every pattern re-expressed | **one element, four mechanisms** (A4) |
| `<scaffold>` | all five, with `none` | release/target constraints |
| `<testing>` | — | one runner, one policy |
| `<task-limits>` | — | one limit |
| Registries | monolithic SPA | the other four — and they are **not** part of `<rules>` (item 25) |

**The bones are right and three leaves were CRUD-shaped.** Nothing here argues against item 28 — it
argues that item 28 stopped one level above where the vendoring actually lived, and that the way to
find out was to write the thing out five times.

### 8.7 What re-expressing `<banned>` established (A4)

The nine `<banned>` patterns above were rewritten under item 56's typed kinds. **This is the
deciding test A4 called for, and it did not come out the way the question was framed.**

| Outcome | Count | Which |
|---|---|---|
| Exactly expressible, refuses | **6** | 2 × `import`, 1 × `change`, 2 × `content`, 1 × `edge` |
| Genuine judgement, reports only | **2** | non-idempotent handler; blocking I/O on the main thread |
| **Not bans at all** — moved to `<testing>` | **2** | writes outside the working directory; network call with no offline fallback |

Three things the exercise produced that the argument had not:

- **A fifth kind.** `content` — a regex over file contents at a path — was not in A4's proposed
  four. Secrets in a bundle and connection strings in source are neither imports nor edges, and
  both are exactly how secret scanners already work.
- **A rule got *stricter* and thereby became exact.** *"A connection string pointing at another
  service's database"* is relational and no regex expresses it. Re-expressed as *no service embeds
  a connection string in source at all*, it is both enforceable and a better rule — the original
  permitted a class of thing nobody wanted.
- **Two rules were in the wrong element.** Runtime properties asserted by a test had drifted into
  `<banned>`, and their presence is most of why `<banned>` looked as though it needed a model to
  evaluate it. Removing them leaves a much smaller judgement class than the objection assumed.

**Six of ten refuse, two report, two were miscategorised.** That is a better answer than either
horn of A4's original question, and it was only available by writing all nine out.
