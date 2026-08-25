# Plugin 2.0 — Fidelity Plan (PRD and CRD paths)

**Status:** Proposed. Nothing here is implemented yet.
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
Structural / Measured) and are numbered **P1–P37** so they do not collide with its F1–F24.

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
Template allows `defined|tbd|in-progress`. The corpus uses `defined`, `tbd`, `excluded` (7) and
`superseded` (2), and uses `in-progress` **zero** times. Two of the four values in use are
undefined by the template; the one value the template offers beyond the obvious pair is unused.

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
| Architecture decision records | **19** | **136** | 25 of 68 |
| Open questions register | **22** | **44** | — |
| Product principles | — | 4 | — |

**184 references, none validated and none followed** — up from 157 a fortnight earlier, which is
the point: this class of reference is the fastest-growing thing in the corpus. `analyze-prd` receives PRD XML and nothing
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

---

## 4. Two design decisions that resolve most of the above

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
| `defined` | Criteria cover the edge cases — *measured* as EARS pattern coverage, not asserted; notes carry the data model and relationships. | ≥1 `unwanted-behaviour` criterion + structured notes |
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

**"Cover the edge cases" needed a definition, and P23 is what happens without one.** Seven
features carry `defined` while having no criterion that mentions a failure at all. Item 33's
`pattern` attribute makes the test mechanical: a feature whose criteria are entirely
`event-driven` has not covered its edge cases, whatever its notes say. That is a deterministic
attribute count, not a judgement, and it is the half of this definition item 3 has never checked.

Two consequences worth stating plainly:

- `excluded` and `superseded` are **definition states, not priorities**. `excluded` pairs with
  `priority="wont-have"` in the index; `superseded` has no index entry at all.
- The corpus's zero uses of `in-progress` are a symptom, not a preference. Under these
  definitions, several features currently labelled `tbd` — thin criteria, real scope in the
  description — are `in-progress`. The migration in item 4 will reclassify them.

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
    <relationships>...</relationships>
    <considerations>...</considerations>
  </notes>

  <rationale>...</rationale>                <!-- required when status=excluded -->
  <superseded-by slug="..."/>               <!-- required when status=superseded -->
</feature>
```

**2. Give `<notes>` an internal shape.**
The corpus already writes notes in three recurring kinds — data model, dependencies and
relationships, and free considerations — signalled with bold markdown headings. Promoting those
to elements is what makes P4 fixable: `analyze-prd` can then *read* `<data-model>` instead of
inferring one. Free markdown stays legal inside each element; the corpus proves markdown-in-XML
is comfortable. **Migration must not be lossy** — unrecognised note content goes to
`<considerations>` verbatim, never dropped.

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
notes. On the corpus that single rule reclassifies seven features the current rule scores as
agreeing — see P23, which is the measurement this item's 63/64 concealed.

> **Read this honestly.** The rule was tuned on the same corpus it was scored against, so 63/64
> is an in-sample figure and not evidence it generalises. What does generalise is the shape:
> **zero contradictions and a one-file escalation band.** The design is safe because it refuses
> rather than guesses — an ambiguous file is escalated to the model, never silently relabelled.

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

> **A filtered set is not automatically a buildable set.** 9 of the corpus's 13 must-have
> features reference lower-tier features, 49 times in total. Resolve open question 4 before
> building this item — the flag is easy, but what it should do about a must-have that points at
> a could-have is not.

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

**22. One artefact schema check, shared by producer and consumer.**
P10 is a general failure: the spec says XML, the run produced markdown, and nothing noticed for
weeks. A single `check-artefacts.py` validating `index.md`, `what-next.md` and every feature file
against the declared schema, invoked in three places:

- at the end of `/prd` — before claiming the PRD is written
- at the **start** of `/breakdown` — refusing on mismatch, in the `resolve-output.sh` idiom
- in `tests/test_toolchain.py`, against a fixture

A producer/consumer mismatch should fail at the boundary, not silently degrade three skills later.

**Item 39 extends this outward**, to the 157 references that leave the PRD entirely (P24). Same
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
  `<notes><data-model>` and `<relationships>` (item 2). Most of the corpus's index block is
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

  **And each registry needs a reader, or this is P4 in a new file.** `analyze-prd` loads them
  alongside `<rules>`, exactly as it loads the feature's `<data-model>` — a registry *is* a data
  model, at project scope. `generate-tasks` carries the entries a task touches into its
  `<context>`. The existing API registry already has a reader on the CRD path
  (`crd-impact-analysis` reads it), so the open set must not be the one shape that does not.
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
file at `docs/prd/{slug}/architecture.md`, sharing PROJECT.md's schema, with a reader in
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
  <banned><pattern reason="...">...</pattern></banned>
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
  and `review-criteria.md` makes it critical twice over. A project declaring `policy="none"`
  would therefore have every task fail batch review at `/breakdown` time and never reach
  `execute-batch` at all. So `<testing policy>` has to be read in three places — by
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

**Migration is the risky part, and it gets its own rules.** 519 criteria rewritten by a model is
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

The residual cost is real: someone assigns a level to 519 criteria. Item 33's migration is the
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

The project the corpus came from already has 16 of these and a settled house style. **It is
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

Cheap, and **157 references currently go unchecked**. This is also the minimum that makes the
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

Test 7's inbound half is the one that gets skipped and the one that catches contract gaps, which
is why it is mechanical and why it is worth running first.

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

What it must contain, per schema change:

- **Preconditions** — what must be true of a file before the transformation applies, so a partly
  migrated tree is safe to re-enter.
- **The transformation**, stated as a rule over the old shape rather than an example of the new
  one. `<priority>` is deleted only after the index entry is confirmed to carry it (item 1);
  `<notes>` prose becomes `<data-model>` / `<relationships>` / `<considerations>` with
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

`/prd --rename <old-slug> <new-slug>`, doing all five edits a slug requires: the filename, `<slug>`,
the index entry's `file=` attribute, the index entry's content, and every inbound cross-reference
in every other feature file.

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

- `<scope>` is a **cross-check, not a routing input** (item 31). Carried onto the PRD path it is
  derived from the feature's task count after breakdown rather than declared at authoring time, and
  its job on both paths is the same: to disagree loudly when the analysis and the generation
  produce different pictures of how big the work is.
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

**`<banned>` is checked twice, deliberately.**

| Where | Catches | Cost of a miss |
|---|---|---|
| `review-tasks`, per generated task | a task that *specifies* a banned pattern | none — no code exists yet |
| `execute-verify`, per implemented task | code that contains one anyway | a rejected task, before merge |

Review is primary because it is free: a task saying *"call the billing service over HTTP"* under a
rule banning cross-context calls is wrong before anybody writes a line. Verification is the
backstop, because a task can be innocently worded and implemented badly, and because a pattern
matched against real code catches what a pattern matched against a description cannot.

**Both report the `reason` verbatim**, which is why item 28 made `reason` mandatory. *"Banned:
HTTP client to another context's service — ADR-004: contexts communicate by event, never by call"*
tells an implementer what to do instead. A bare rule number does not.

**`<task-limits>` is enforced where the limit already lives.** Today `max-files` is a constraint in
`task-format-spec.md` and a critical criterion in `review-criteria.md` — both hardcoded to 3. They
become readers of `<task-limits>`, honouring the scoped overrides. This is the same three-reader
shape item 28 found for `<testing policy>`: a rule is only overridable if every place that
currently hardcodes it learns to ask.

**A false positive must be answerable.** A banned-pattern check that cannot be overridden becomes a
reason to stop declaring patterns. An explicit, reasoned exemption in the task
(`<exempt pattern="…" reason="…"/>`) is reported in the run summary rather than silently allowed —
visible, attributable, and not a fight with the tool.

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
| 56 | Enforce `<banned>` and `<task-limits>` at both ends | P16, **P35** | **Correctness** |

**Suggested order.** 21 first — measure P1 before changing it. Then 18, since nothing else can be
tested end to end on a realistic PRD until analysis fits in context.

Then the schema block (1–5, 25, **28**, 27) and its migration, because 13–17 depend on the shapes
it defines, because 27 is what makes item 14 decidable, and because **28 is now the largest thing
in that block** — it is the only item that turns the fixed pipeline into a parameter, and both 31's
layer derivation and 30's priority filter want to read values it defines. Do 25 and 28 as one piece
of work; splitting them means designing the same file twice.

Then 29, before the `/breakdown` items rather than after: every later item is worth more once a
task can admit what it does not know, and 15 and 30 both get less blunt when partial uncertainty
has somewhere to go.

Then the `/breakdown` and `/execute` items (13–17, 19, 20), which are small once the schema
carries the data, with **30** immediately after 16 — it has nothing to check until
`<source-feature>` exists. **31** belongs with 28 rather than after the rest: it makes the layer set a function of content,
which is the same change 28 makes to the layer *graph*, and the two are one design decision seen
from two sides. It is no longer a bypass around the pipeline — it is the pipeline asking what the
work needs. **32** wants to be early rather than late: it is an
output format over a traversal that already runs, and every item before it makes the task set
bigger. 22 and 23 last, to hold the result in place.

**Where the new items go.** **33 and 34 belong with the schema block**, and 33 belongs at the
front of it: it changes the criterion element that items 1, 5, 16, 17 and 35 all build on, and
every day it waits is more content to migrate. Do 34 in the same pass — the criterion is being
touched anyway, and assigning a level while a human is already reviewing each feature's diff is
far cheaper than a second sweep.

**39 can go immediately, ahead of everything.** It depends on nothing in this plan, it is a
reference check over files that already exist, and 157 unchecked citations is a defect today.

**56 belongs with 28**, not after it: `<banned>` and `<task-limits>` are two of the five opinions
item 28 exists to make overridable, and shipping the declaration without the enforcement would
leave an operator believing a rule is in force — item 28's own stated failure mode for a
silently-ignored rule file.

**53, 54 and 55 are small and independent.** 53 is a declaration plus a refusal in the same idiom
Phase 1 already uses; 54 is one optional element and two readers; 55 is a field in the ledger.
None depends on anything else in the plan, and 54 is worth doing early because monorepo
verification is wrong today.

**51 and 52 come with the schema block, not after it.** Item 51 is the producer for the artefact
items 25 and 28 define, so defining those without it leaves a file nothing writes; and 52 is a
`test -f` that item 51's opening question depends on. Both are small and neither has dependencies
beyond the shape of `<rules>`.

**44 and 45 come before every schema item, with 43.** A shared core defined after the elements it
is meant to share is a merge rather than an extraction, and 45's renaming is cheap now and
expensive once three vocabularies have consumers. 46 and 47 follow 33 and 34 immediately — they are
the same change reaching the other path, and letting them lag is how the two vocabularies get
consumers. 48, 49 and 50 can come with the rest of their concerns.

**43 comes before every schema item, including 41.** The regression suite validates the fixture
against the current schema, so item 1 breaks it unless a second fixture exists to land beside the
first. It is also what makes 41 and 24 testable rather than merely specified. Nothing else in the
plan is a precondition for this many items.

**41 is a precondition, not a follow-up.** Items 1, 2, 5, 11, 33, 34 and 35 all rewrite artefacts
that exist; none of them can land until the migration they imply is specified and verifiable. Write
it with the first schema item, not after the last.

**42 is small and can go whenever**, but it is worth doing before item 41 rather than after: it is
the same shape of problem across a handful of files instead of sixty-five, and getting the
postcondition-assertion pattern right on a rename is much cheaper than getting it wrong on a
migration.

**40 belongs with 6 and 8**, whose machinery it uses — the mechanical tests are exit codes in one
and the judgement tests are a second mode of the other. Its contract-rule script can go earlier
still: it needs nothing from this plan and has 93 one-way edges to triage today.

**35, 36 and 38 are one piece of work**, after the schema block and after 30. They are also the
one block that can be deferred wholesale: with `<design-track enabled="false">` none of them
changes behaviour, so they can land late without blocking anything. **37 is the exception** — it
is a paragraph of definition in items 25 and 28, costs nothing, and should land with them.

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
   filtered set is coherent. Three options, in increasing cost: filter and report the dangling
   references; filter with dependency closure, pulling in lower-tier features a must-have needs
   (which quietly rebuilds the tier boundary); or treat the reference graph as the real
   ordering and let MoSCoW select roots rather than members. **This needs deciding before item
   14 is built, not after** — and distinguishing a genuine dependency from a cross-reference is
   itself work the schema does not currently support, since both are plain markdown links.
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
7. **Reframed: is the layer graph load-bearing for quality, or only for convention?**
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
   sets.** If quality tracks the graph, it is load-bearing and the default must be protected. If it
   does not, the graph was convention and P18 costs nothing.

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
<registries><api/><schema/></registries>
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
  <pattern reason="ADR-004: contexts communicate by event, never by call">
    HTTP or gRPC client targeting another context's service
  </pattern>
  <pattern reason="published events are immutable; add a version, never edit">
    modifying an existing event schema in place
  </pattern>
  <pattern reason="ADR-011: consumers must tolerate replay">
    handler with side effects that are not idempotent
  </pattern>
</banned>
<registries><event/></registries>
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
  <pattern reason="ADR-002: no shared datastore across services">
    connection string pointing at another service's database
  </pattern>
</banned>
<registries><service/><api/></registries>
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
  <policy match="tests/cli/**" kind="golden"/>    <!-- stdout is a contract -->
</testing>
<banned>
  <pattern reason="core must be usable as a library">network access from core/**</pattern>
  <pattern reason="a CLI must not surprise its caller">writes outside the working directory</pattern>
</banned>
<registries><command/></registries>       <!-- subcommands, flags, exit codes, output format -->
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
</testing>
<banned>
  <pattern reason="ANR: the main thread is not for I/O">blocking I/O on the main thread</pattern>
  <pattern reason="the bundle is readable by anyone who downloads it">secrets in the app bundle</pattern>
  <pattern reason="offline-first is a product requirement">network call with no offline fallback</pattern>
</banned>
<registries><screen/><schema/></registries>   <!-- navigation graph + on-device store -->
```

Two platforms are two instantiations of one graph — the same `applies-to` that microservices need,
for an unrelated reason. **The one thing with nowhere to go is the release constraint** — minimum
OS version, signing identity, store submission. It is arguably `<scaffold>`'s business, and it is
the weakest of P35's findings because it is genuinely absent rather than mis-shaped.

### 8.6 What the exercise established

| | Held up | Broke |
|---|---|---|
| `<layers>` as a DAG | chain, diamond, degenerate | one graph per project (`applies-to`) |
| `<banned>` | all five, unchanged | — |
| `<scaffold>` | all five, with `none` | release/target constraints |
| `<testing>` | — | one runner, one policy |
| `<task-limits>` | — | one limit |
| Registries | monolithic SPA | the other four |

**The bones are right and three leaves were CRUD-shaped.** Nothing here argues against item 28 — it
argues that item 28 stopped one level above where the vendoring actually lived, and that the way to
find out was to write the thing out five times.
