# Plugin 2.0 Plan — Review and Remediation Proposal

**Status:** Proposed. Nothing here is implemented, and this document changes no skill, agent or
command — its subject is a document, not the toolchain.
**Date:** 2026-08-25
**Subject:** [`plugin-2.0-plan.md`](plugin-2.0-plan.md) — 2,733 lines, findings P1–P37, items 1–56 —
read as a plan somebody has to execute.
**Relationship to the other plans:** [`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md)
fixed the *mechanics*; `plugin-2.0-plan.md` addresses *fidelity*;
[`sdd-comparison.md`](sdd-comparison.md) addresses *position*. This document addresses
**executability**: whether the fidelity plan can be carried out as written, and what it says that
is no longer true.

**Findings are graded** as in the other three documents — Blocking / Correctness / Consistency /
Structural / Measured — and numbered **R1–R17** so they do not collide with F1–F24, P1–P37, C1–C10
or S1–S5. Remediation items are lettered **A1–A10** for the same reason: the plan's items 1–56 are
changes to the *toolchain*, and these are changes to the *plan*.

**Verification status is stated per finding**, in the plan's own vocabulary:

- **In-document** — two or more passages of `plugin-2.0-plan.md` were compared and disagree. Line
  numbers are given and were taken at the revision dated 2026-08-25.
- **Against repository** — a claim in the plan, or an omission from it, was checked against the
  files in `skills/`, `agents/`, `commands/` or `tests/`.
- **Argued** — no measurement settles it; the finding is a judgement and is labelled as one.

> **The plan is worth this scrutiny, which is why it is getting it.** Section 2 is not a courtesy
> paragraph. Nine of the seventeen findings below exist *because* the plan established the rule
> they violate, and none of them argues for abandoning it.

---

## 1. Method, and its limits

Every numbered element was enumerated mechanically: findings P1–P37 are all defined and all
addressed in the §6 summary, and items 1–56 are all defined with no gaps. **The plan's numbering
discipline holds.** Its repeated assurances that "nothing numbered 1–32 or P1–P22 moved" are true.

What was checked beyond that:

- every figure in the body against the re-measured §2 table
- every element the plan introduces (`<gaps>`, `<rules>`, `<registries>`, `<exempt>`, `<scope>`,
  `<depends-on>`, `<architecturally-significant>`, `derived-from`) for a named producer *and* a
  named reader — item 23's own rule, applied to the revision that added it
- every artefact path and attribute name for agreement across the items that use it
- the plan's claims about existing repository state, where a claim was load-bearing

**What was not checked, and matters.** The corpus is out of version control by design, so every
figure in §2 is taken on trust. The findings below about stale figures are *internal* disagreements
— the plan contradicting its own re-measurement — not a re-measurement of the corpus. R5 and R6
would be settled properly by re-running the probes, which is A2.

---

## 2. What the plan gets right

Four things, stated because the remediation below is small relative to them and would otherwise
read as a rejection.

**The producer/consumer lens is the correct organising idea and it generalises.** P1, P2, P4, P19
and P24 are one finding at five scales — extracted-then-discarded, written-then-unread,
cited-then-unresolved — and naming that is worth more than any individual fix in the document. Item
23's closing rule, *every element must have a named reader or an explicit unread-by-design marker*,
is the generalisation, and it is right.

**The self-audit is the strongest move in the document.** Auditing the plan against its own rule,
finding nine failures, resolving them in place, and recording the count in the header is a
discipline almost no planning document applies to itself. Findings R1–R7 below are the *same* audit
run once more; that they exist is not evidence the practice failed but that it was run once and
needs to be a script, which is what item 23 already concludes.

**P9's retraction is exemplary.** A finding was written up twice, both readings were wrong, the
measurement error was traced to how the directory was populated rather than to the count, and the
whole episode was left visible with the generalisation attached. The §2 method note is the same
virtue. This is how measurement should be reported.

**§8 is the best-designed section in the plan.** Expressing `<rules>` across five architecture
patterns falsified three of item 28's leaves, and it did so using the **default** case — a
monolithic SPA needs two test runners, which `runner="pytest"` cannot say. Falsifying your own
schema with the case you built it for is the hardest kind of falsification to arrange. §8's
instruction to re-express all five whenever `<rules>` changes should be treated as binding.

---

## 3. Findings

### 3.1 Correctness — the document asserts things that are not true of itself

**R1 — `in-progress` is simultaneously in use and unused.**
*Verification: in-document.*
§2 line 132 records `in-progress` entering use, lists it in the status tally as 1, and names it one
of the four rows that "carry the story". P6 at line 269 still reads: *"uses `in-progress` **zero**
times"*, and derives from that the claim that *"the one value the template offers beyond the obvious
pair is unused"* — which is the substance of the finding. §4.2 at line 819 then builds an argument
on *"the corpus's zero uses of `in-progress`"*, concluding that several `tbd` features will
reclassify.

The re-measurement landed in §2 and propagated nowhere. **P6 as written is false**, and §4.2's
migration expectation rests on it.

**R2 — `architecture.md` has two different homes, in the two items that define it.**
*Verification: in-document.*
Item 25 at line 1289 is emphatic: *"`architecture.md` at the **project root, beside `PROJECT.md`**
— not under `docs/prd/{slug}/`"*, and gives four reasons, the first of which is a stated correction.
Open question 2 at line 2485 marks the scope question **Resolved** in the same direction.

Item 28 opens at line 1375 by summarising item 25 as establishing *"a prescriptive,
machine-readable file at `docs/prd/{slug}/architecture.md`"* — the location item 25 explicitly
rejects. Item 28 is the largest item in the plan, item 51 is its producer, item 52 is a `test -f`
against it, and item 26 seeds `PROJECT.md` from it. **Four items depend on a path two of them
disagree about.**

**R3 — `<testing>`'s attribute has two names, and the load-bearing argument uses the wrong one.**
*Verification: in-document.*

| Name | Where |
|---|---|
| `default=` | item 28's schema block (line 1395); all five §8 examples (2597, 2621, 2679, 2703) |
| `policy=` | P35 (522); item 28's three-reader argument (1419, 1421); item 56 (2303) |

The three-reader argument is the one that makes TDD overridable — *"`<testing policy>` has to be
read in three places"*, by `generate-tasks`, `review-tasks` and `execute-batch`, and
`task-format-spec.md` must stop marking `<test-requirements>` unconditionally required. It is
written against an attribute the schema does not declare, and `policy="none"` — the value a project
sets to disable TDD — appears in no example.

**R4 — `<registries>` has three shapes and is absent from the schema that owns it.**
*Verification: in-document.*

- Item 25 (line 1301) names standalone elements: `<event-registry>`, `<command-registry>`,
  `<service-registry>`, `<screen-registry>`.
- All five §8 examples use a nested container with short names:
  `<registries><event/><api/></registries>`, as a sibling of `<layers>` inside `<rules>`.
- **Item 28's canonical `<rules>` block (lines 1387–1405) contains no registry element at all**,
  while §8.6's results table grades "Registries" as a row of `<rules>`.

This is P30 — *"the two paths define overlapping schemas independently"* — occurring inside the
document that diagnoses it, and it blocks item 25's own instruction that each registry needs a
reader: nothing can be written to read an element with three names and no declaration.

**R5 — Five figures contradict the §2 re-measurement.**
*Verification: in-document.*

| Figure | §2 / re-measured | Still asserted at |
|---|---|---|
| External references (P24) | **184** | 157 — items 22 (1216), 39 (1791), §6 ordering (2403) |
| Criteria | **550** | 519 — items 33 (1616) and 34 (1652) |
| Decision records | **19 distinct** | 16 — item 36 (1682), P25 |
| `defined` features with no failure path | **8** | seven — item 3 (920), §4.2 |
| Corpus files citing an ADR | 64 feature files | "25 of **68**" — P24 table (497) |

Three of these are load-bearing rather than cosmetic. Item 39's *"157 unchecked citations is a
defect today"* is the whole argument for running it first. Item 33's *"519 criteria rewritten by a
model"* is the migration's cost estimate. And 68 is a denominator that matches nothing in §2.

**R6 — Item 3's headline result was taken on a corpus the plan has since superseded.**
*Verification: in-document, arithmetic.*
The probe output at lines 895–903 tallies `tbd -> tbd 20` plus `tbd -> ambiguous 1`, i.e. **21 files
declaring `tbd`**. §2's current tally is `tbd` 20 and `in-progress` 1. The probe was run before
`in-progress` entered use and has not been re-run.

The 63/64 agreement figure is cited three times as the evidence that mechanical status derivation is
feasible, and item 23 proposes committing it as a regression check. **It is a result from a corpus
snapshot the document elsewhere marks as replaced.** The same stale 21 appears in item 8 (1021),
item 15 (1133), and item 11's `<authoring-gaps>` example (1063) — where
`defined="34" in-progress="1" tbd="21" excluded="7" superseded="2"` **sums to 65** against a 64-file
corpus.

**R7 — Item 45 renames `<status>` and nothing else in the plan knows.**
*Verification: in-document.*
Item 45 renames the PRD feature tag to `<definition>`, argues that *"renaming is cheap now and
expensive later"*, and §6 orders it *"before every schema item"*. Every schema passage in the
document still says `<status>`: item 1's template (878–884), item 3's derivation table, item 4, item
6's checks, items 13 and 15's filters, and the whole of §4.2.

Item 45 is graded **Correctness** and bolded in the summary. As written, landing it first
invalidates the shapes six other items are specified against.

### 3.2 Structural — the plan cannot be executed as written

**R8 — Opening the registry set breaks a validator the plan never mentions.**
*Verification: against repository.*
`skills/execute/scripts/check-project-md.py` line 128 hard-requires four blocks to be present in
`PROJECT.md`:

```python
missing = [s for s in ("meta", "features", "api-registry", "schema-registry")
```

Item 25 makes registries an open set and states that *"PROJECT.md gains the same freedom when item
26 seeds it"*. A CLI project seeded per item 26 with only `<command-registry>` **fails this check**.
`crd-impact-analysis` reads the same two names.

`check-project-md.py` appears **zero times** in the plan's 2,733 lines. The script's own docstring
records that this validator exists because the finalizer once wrote malformed XML and *"the run
reported success"* — which is to say it is exactly the class of guard the plan's item 9 argues for,
and item 25 would silently invalidate it.

**R9 — `<banned>` is graded as an exit code and cannot be one.**
*Verification: against repository and §8, argued.*
Item 56 enforces `<banned>` twice — in `review-tasks` against the task text, and in `execute-verify`
against *"real code"* — and it is graded **Correctness**, in the exit-code column of item 37's
table.

Every pattern in §8 is a natural-language description:

- *"blocking I/O on the main thread"*
- *"network call with no offline fallback"*
- *"handler with side effects that are not idempotent"*
- *"connection string pointing at another service's database"*

There is no deterministic matcher for these. Either the patterns become machine-matchable — losing
the expressiveness §8 uses to argue `<banned>` *"generalises across all five without change"*, which
is its strongest evidence — or the check becomes a model judgement, and stops being an exit code and
stops being defence in depth in the sense item 56 claims. **The plan does not notice that this is a
choice**, and it is the only one of item 28's five opinions whose enforcement mechanism is not a
comparison.

A smaller instance rides along: item 28 at line 1435 credits `<banned>` with a *"`fileMatch`
mechanism this item already borrowed"*. `<banned><pattern>` carries no match attribute in any
example; `<testing>` and `<task-limits>` use `match=`; and `fileMatch` is a third name appearing
nowhere else.

**R10 — Three elements the plan's own audit rule would still flag.**
*Verification: in-document, against item 23's rule.*
The 2026-08-25 audit found nine producer/reader failures and resolved them. Three survive:

| Element | Missing | Where |
|---|---|---|
| `<exempt pattern= reason=>` | **producer** — nothing says whether `generate-tasks` or the implementer writes it, and `task-format-spec.md` is not listed as gaining it | item 56 |
| `<scope>` on the PRD path | **producer and location** — *"derived from the feature's task count after breakdown"*, by nothing named, into no stated file | item 49 |
| `<registries>` | **reader** — blocked by R4; no reader can be written against three shapes | items 25, 28, §8 |

`<scope>` is the interesting one. Deriving it after breakdown and writing it back into a feature
file would have `/breakdown` **mutating the PRD**, which no other item contemplates and which §4.1's
ownership rule has no answer for. Item 49 gave `<confidence>` a producer explicitly — *"without that
this item would have given the PRD path a field with a reader and no writer"* — and did not run the
same check on the element beside it.

**R11 — §6's suggested order is not an order.**
*Verification: in-document.*
Eight items are each asserted to be first or near-first: **21** (*"first"*), **39** (*"immediately,
ahead of everything"*), **43** (*"before every schema item, including 41"*), **44 and 45** (*"before
every schema item"*), **41** (*"with the first schema item, not after the last"*), **42** (*"before
item 41 rather than after"*), and **33** (*"at the front of it"*).

Roughly twenty items — 1–5, 25, 27, 28, 31, 33, 34, 37, 41, 42, 43, 44, 45, 51, 52, 56 — collapse
into a single "schema block" that four separate paragraphs each claim the head of. What the section
contains is a set of pairwise constraints, correctly reasoned individually, that has never been
topologically sorted. **There is no first increment**, and with ten items graded Blocking or bold
Correctness, that is the difference between a plan and a backlog.

**R12 — Item 6 is a kitchen sink, and four items assert the same things.**
*Verification: in-document.*
Item 6 now carries eleven checks: status derivation, index reconciliation, rename postconditions,
criterion id uniqueness, `excluded`/`superseded` well-formedness, EARS pattern coverage, unassigned
priority counts, ASR candidate screening, external reference resolution, `<gaps>` well-formedness,
and gap age.

Meanwhile item 22 proposes `check-artefacts.py` running *at the end of `/prd`* — where item 6 also
runs — item 39 *"extends item 22"* while its checks are also listed inside item 6, item 40's
mechanical tests *"go into item 6"*, and item 42's postconditions are stated twice, in item 42 and
in item 6. Item 42 acknowledges the overlap; the rest do not.

It is genuinely unclear whether the plan proposes **one script or five**, and which one owns the
assertion *"no reference anywhere to a slug that has no file"* — currently claimed by items 6, 22,
39 and 42.

**R13 — Fifty-six items, one runtime test.**
*Verification: in-document, argued.*
P22 concedes that *"no PRD of this size has been broken down, because P5 stops it first"*. That
concession is load-bearing far beyond P22: items 13–17, 19, 20, 30 and 32 all specify behaviour at
the `/breakdown` → `/execute` boundary, and **no run has ever crossed it with a realistic input**.

The proposed verification is item 21 — four features, two criteria each, asserting task count and
one exclusion — plus static checks (23), fixtures (43) and scripts (30, 39, 40, 50). For a plan
whose central methodological complaint is that static agreement is not evidence, and whose own §2
carries a note about measurements inheriting the defects of how they were taken, **the ratio of
runtime evidence to specified behaviour is the wrong way round.**

**R14 — The EARS migration is priced as a footnote and is the plan's likeliest failure point.**
*Verification: in-document, argued.*
Item 33 states that *"the mechanical part is large and the judgement is concentrated"*. The actual
judgement load, taking the plan's own instructions together:

| Judgement | Count | Axis | Source |
|---|---|---|---|
| `pattern` assignment | 550 | six-way, *"assigned by the migrator"*, never inferred | item 33 |
| `priority` assignment | 550 | three-way, *"in the same pass"* | item 34 |
| `<architecturally-significant>` | 64 | six-way `because=`, plus a criteria list | item 35 |
| Note restructuring | 64 | three-way, lossless | item 2 |

All of it reviewed **per feature, as a diff**, by a human, in one pass — because items 33, 34 and 35
are ordered together on the grounds that *"the criterion is being touched anyway"*. That reasoning
is sound for *when* and says nothing about *how much*.

This is the precondition for items 1, 2, 5, 11, 16, 17, 30, 35 and 40. **If the plan dies in
execution, it dies here**, and the document contains no estimate, no partial-completion story beyond
"idempotent and resumable", and no answer to what happens if the reviewer stops at feature 30 of 64.

**R15 — No triage, no cost, no abort criterion.**
*Verification: in-document, argued.*
Every item is justified; none is priced; the grades exist and are never used to rank. §6's ordering
is purely dependency-driven, so there is no answer to *"we have a week"*.

More seriously, there is **no falsification test for the plan's largest item**. Open question 7
identifies three real losses from item 28 — free dependency ordering, a guardrail on a small model,
and a failure mode that *"moves and gets quieter"* — and proposes an experiment: run the fixture
through the default graph and a deliberately poor one. That experiment is deferred behind item 43,
and nothing states what happens if it comes back badly. **Item 28 has an identified downside risk, a
proposed measurement of it, and no decision rule attached to the result.**

### 3.3 Premise — what the plan never audits

**R16 — The plan records four times that prose beat the schema, and never asks what that means.**
*Verification: in-document, argued.*

| Finding | What the model invented, unprompted | The plan's verdict |
|---|---|---|
| P10 | prose `what-next.md` carrying phasing, spikes, risks | *"produced a **better** artefact"* |
| P11 | an `<architecture>` block in the index | *"the invention is usually right"* |
| P12 | intra-feature phasing in prose | real semantics, no slot |
| P13 | `<rationale>` on excluded features | *"a good idea the template should adopt"* |

P11 generalises it explicitly: *"where the template is silent, the model invents structure, and the
invention is usually right. Treat these as requirements discovered by use."*

**The response, every single time, is to add a slot to the schema.** The counter-hypothesis is never
stated, let alone rejected: that the schema is the wrong instrument for a requirements document, and
that markdown-with-conventions plus validation at the *consumer* boundary would carry more fidelity
at a fraction of the migration cost. Items 33, 34, 41, 43 and 44 exist almost entirely to service
the schema-tightening choice, and item 41 is graded **Blocking**.

Item 11 half-concedes the point — *"XML skeleton, markdown bodies… the goal is a parseable skeleton,
not the loss of prose depth"* — and item 2 concedes it again for `<notes>`, where free markdown
stays legal inside every element and `<considerations>` is *"deliberately unread"*. Two items have
independently discovered that the valuable content is the prose and the valuable structure is the
envelope. **Nothing generalises that into a stated position**, and it is the one premise on which
the plan's largest costs depend.

**R17 — The corpus author appears as evidence and never as a stakeholder.**
*Verification: in-document, argued.*
The plan cites the author's behaviour a dozen times — the invented `<rationale>`, the forced
architecture conversations, the decision records kept outside the PRD, the rename done correctly
across 20 references. P25's evidence *is* the author compensating for a missing design step.

The result of the plan, for that same person: `/prd` grows a ninth phase, the criterion format is
replaced, the status tag is renamed, a second priority vocabulary is added, two new project-root
artefacts appear, a design track switches on, and 550 criteria are re-annotated by hand. **No item
asks whether authoring a PRD is still tolerable afterwards**, and no item proposes measuring it. P21
worries about ceremony for *small changes* and never about ceremony for the author of a large one.

---

## 4. Remediation

**A1. Correct R1–R7 in one editing pass.**
Mechanical, no design decisions, and several are load-bearing for arguments elsewhere. In order of
consequence: item 28's path (R2), item 45's rename propagation or an explicit note deferring it
(R7), P6 and §4.2's `in-progress` claims (R1), `<testing>`'s attribute name (R3), the five figures
(R5).

**A2. Re-run item 3's derivation probe and item 6's reference count against the current corpus.**
R6 says the 63/64 figure is from a superseded snapshot and item 23 proposes committing it as a
regression baseline. Re-run before that happens. The plan's own §2 method note is the argument:
*"a measurement taken by globbing a directory inherits every defect of how that directory was
populated."* A measurement inherited from a superseded corpus is the same defect one revision later.

**A3. Settle `<registries>` in one place, then reconcile it with the two readers that exist.**
Pick the nested-container shape (§8 uses it five times), declare it in item 28's `<rules>` block,
and amend item 25 to cite rather than restate — which is item 44's own rule applied to the plan.
Then **name `check-project-md.py` and `crd-impact-analysis` as the affected readers** (R8) and say
what happens to a `PROJECT.md` carrying `<command-registry>` and no `<api-registry>`.

**A4. Decide whether `<banned>` is an exit code or a judgement, and re-grade item 56 accordingly.**
Three defensible outcomes, and the plan should state which (R9):

1. Patterns are machine-matchable expressions — `<banned>` keeps its exit code, and §8's five
   examples are rewritten to prove the expressiveness survives.
2. Patterns stay natural-language — `review-tasks` and `execute-verify` check them by judgement, the
   check reports rather than refuses, and item 37's table gains a fourth row.
3. Both, split: a machine-matchable `expr=` attribute where one exists, prose as guidance where it
   does not, with only the first enforced.

Option 1 is the one §8 has not yet been tested against, which makes re-expressing all five the
deciding experiment — exactly as §8 instructs.

**A5. Run item 23's rule over the plan once more and pair the three survivors** (R10). `<exempt>`
needs a named producer and a line in `task-format-spec.md`. `<scope>` on the PRD path needs a writer
and a file, or an explicit statement that it is a run-report field and never persisted — which is
probably the right answer and dissolves the PRD-mutation problem. `<registries>` follows A3.

**A6. Replace §6's ordering prose with a sorted sequence and a named Phase 1.**
The pairwise constraints are individually right; they need composing once (R11). Phase 1 should be
independently shippable and should fix live defects rather than prepare for future ones — see §5.

**A7. Consolidate the checks into named scripts with owned assertions** (R12).
One table: assertion, owning script, invocation point. Item 6 becomes a caller rather than a
container. The plan already has the idiom — `resolve-output.sh`, `build-manifest.py`,
`check-project-md.py` are each one job with one exit code — and item 6 is the first thing in the
document that departs from it.

**A8. Add a `/breakdown` → `/execute` runtime test beside item 21, before specifying more items
across that boundary** (R13). Item 43's fixture pair is the natural vehicle and it is already
ordered early. The assertion set that matters: criteria carried verbatim with their ids (item 17),
`<source-feature>` resolving (items 16, 30), and the coverage report naming a real shortfall
(item 30). Without one, items 13–20 and 30–32 are specified entirely against projection.

**A9. Give the EARS migration its own cost section** (R14). Three things it needs and does not have:
a per-feature time estimate against the real corpus, a partial-completion contract stronger than
"idempotent" (what is true of a tree where 30 of 64 features are migrated, and can `/breakdown` run
against it?), and a stated fallback if the review does not finish. Consider splitting item 34's
priority assignment out of item 33's pass — the reasoning for combining them is convenience, and it
doubles the judgement load on the plan's critical path.

**A10. Write the half-page the plan is missing: why schema-tightening beats prose-plus-validation**
(R16). It may well win — parseability at the consumer boundary is a real argument and P10's
divergence is a real cost. But it is currently an assumption carrying items 33, 34, 41, 43 and 44,
and P10–P13 are four pieces of evidence pointing the other way that the plan itself collected. Add
the authoring-cost question (R17) to the same section: the plan's evidence base is one author's
behaviour, and the plan's output is that author's new workflow.

---

## 5. A first increment

R11 says the plan has no shippable Phase 1. This is the one it already contains, assembled: six
items that depend on nothing else in the plan, fix defects that are live in the repository today,
and leave the schema untouched.

| Item | What it does | Why it is in Phase 1 |
|---|---|---|
| **A1** | Corrects R1–R7 | An editing pass; blocks nothing and unblocks reading |
| **39** | Validates ADR / OQ / principle citations | *"depends on nothing in this plan"*; 184 unchecked citations today |
| **23 (partial)** | `state-schema.md` says `2.0`, `write-state.py` writes `3.0` | **A live defect**, verified: `write-state.py:169` against `state-schema.md:23` |
| **54** | A working directory for verification | *"monorepo verification is wrong today"*; one element, two readers |
| **55** | The ledger states what it verified | A field and a wording change, behind S2's existing principle |
| **42** | Rename with a checkable postcondition | Cheapest possible rehearsal of item 41's machinery, on 8 files rather than 65 |

None of these touches `<criterion>`, `<status>`, `architecture.md` or the migration. All of them are
reversible. **42 is the one to watch**: if the postcondition-assertion pattern is awkward on a
rename, it will be far worse on item 41, and that is worth learning for the price of a rename.

Phase 2 is then the decision block — A3, A4, A5, A10 — which are four choices, not four builds, and
which between them determine whether items 25, 28 and 56 are specified well enough to start.

---

## 6. What this proposal does not do

**It does not dispute a single finding P1–P37.** Every one that was spot-checked against the
repository held: P17's greenfield gap is real (`skills/execute/SKILL.md:356` — *"greenfield runs
skip this entirely and silently"*), P28's version mismatch is real and live, P36's late refusal is
real. The diagnosis is sound and the remediation above assumes it.

**It does not propose deferring item 28.** R15 asks for a decision rule attached to open question
7's experiment, not for the experiment to conclude before the item starts. P18 is correctly graded
as the largest gap against the field.

**It does not resolve R16.** A10 asks for the argument to be written; it does not assert which way
it comes out. The four data points the plan collected point one way and the consumer-side
parseability argument points the other, and one paragraph of honest reasoning would settle more than
this document can.

**It has one reader, named.** This proposal is input to the next revision of `plugin-2.0-plan.md`,
and its own producer/consumer status is: read once, acted on, then superseded by that revision. It
should not accumulate.
