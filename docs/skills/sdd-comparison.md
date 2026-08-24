# Spec-Driven Development — This Toolchain Against the Field

**Status:** Assessment only. No remediation item here is implemented, and §8 is a proposal.
**Date:** 2026-08-24
**Subject:** `/prd`, `/crd`, `/crd-context`, `/breakdown`, `/execute` — the 3 commands, 14 skills
and 8 agents in this repository — compared against four published spec-driven approaches.
**Relationship to the other plans:** [`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md)
fixed the *mechanics* (forking, worktrees, merges, state). [`plugin-2.0-plan.md`](plugin-2.0-plan.md)
addresses *fidelity* (what a PRD carries and how much reaches the code). This document addresses
*position*: what the toolchain is relative to the field, and which of its gaps are gaps only
because everyone else has filled them.

**Findings are graded** as in the other two plans — Blocking / Correctness / Consistency /
Structural / Measured — and numbered **C1–C10** (comparison) and **S1–S5** (strength) so they do
not collide with F1–F24 or P1–P17. Where an item restates a P-finding from a different angle it
says so rather than claiming novelty.

**Verification status is stated per finding.** *Static* means every file in `skills/`,
`commands/` and `agents/` was searched and the thing described is or is not there. *External*
means it comes from the comparator's own documentation, cited in §10. *Measured* means it comes
from the corpus figures in `plugin-2.0-plan.md` §2.

---

## 1. Scope, and how to read this

Four comparators, chosen because they span the design space rather than because they are the four
most popular:

| | What it is | Distribution |
|---|---|---|
| **spec-kit** (GitHub) | CLI that installs a `/speckit.*` command set into your agent | Open source, 30+ agents |
| **Kiro** (AWS) | IDE/CLI/web product built around a three-file spec | Commercial product |
| **Tessl** | Spec-as-source framework (private beta) plus a public skills/plugins registry with evals and governance | Commercial platform |
| **Böckeler, *Exploring Gen AI*** | Not a tool — a comparative critique of the first three, and the taxonomy this document uses | Article |

The comparison is deliberately asymmetric. spec-kit and Kiro are compared feature-for-feature,
because they occupy the same slot as this toolchain. Tessl is compared on one axis only —
spec-as-source — because that is the only axis on which it is public enough to compare, plus one
observation about where its product has moved. Böckeler supplies the frame.

Two things this document does **not** do. It does not evaluate output quality; nobody has run
spec-kit and this toolchain against the same PRD, and until someone does, any claim about which
produces better code is opinion. And it does not treat feature parity as a goal — several absences
below are defensible design choices, and are marked as such.

---

## 2. The comparators, in one paragraph each

**spec-kit.** A CLI (`specify init`) that installs commands into whichever agent you use. The
workflow is `/speckit.constitution` → `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` →
`/speckit.implement`, with three optional quality passes: `/speckit.clarify` (resolve
underspecified areas before planning), `/speckit.analyze` (cross-artefact consistency, after tasks
and before implement), and `/speckit.checklist` (generated quality checklists that act as "unit
tests for the specification"). `/speckit.converge` re-assesses the codebase against
spec/plan/tasks and appends remaining work; you loop implement/converge until it reports
convergence. The constitution — `memory/constitution.md` — holds numbered architectural articles
enforced as "Phase -1 gates" the plan must pass. Templates mandate
`[NEEDS CLARIFICATION: question]` markers wherever the spec is thin, so ambiguity is recorded
rather than assumed away.

**Kiro.** Three files per feature — `requirements.md` (user stories with acceptance criteria),
`design.md` (architecture, data flow, error handling, testing strategy), `tasks.md` (discrete
trackable tasks traced back to requirements) — produced in three sequential phases with the user
approving each before the next. Execution groups independent tasks into dependency "waves" that
run concurrently. Two supporting mechanisms: *steering files* carry project conventions across
sessions and interfaces, and *agent hooks* run background work (tests, doc updates) on file
events.

**Tessl.** Two products. The **Framework** (private beta) is the field's only serious attempt at
spec-as-source: `.spec.md` files are the maintained artefact, `@generate` and `@test` directives
drive generation, generated code is marked `DO NOT EDIT`, and spec and code sync bidirectionally.
The **Registry** (open beta) is something else entirely — a package manager for skills and plugins
with versioning and rollback, plus governance (security scanning, RBAC), scenario evals that
measure a skill's actual effect on agent performance, observability of where skills fire, and
cross-repository inventory.

**Böckeler.** Establishes three levels: **spec-first** (good specs precede code, then are
discarded), **spec-anchored** (specs persist and drive evolution), **spec-as-source** (specs are
primary, code is generated output). All three tools implement spec-first; only Tessl targets the
upper two. Her critiques: the workflows do not scale down to small changes; the generated markdown
is verbose and worse to review than code; agents ignore or over-apply spec instructions despite
checklists; and the whole enterprise risks repeating model-driven development's failure — this
time combining MDD's inflexibility with the LLM's non-determinism.

---

## 3. Placement

**This toolchain is spec-first, more emphatically than either comparable tool.**

The greenfield path consumes the PRD once, into `analysis.json`, and never reads it again.
`plugin-2.0-plan.md` measured the loss: of the four kinds of content `/prd` writes, one is
consumed. `<acceptance-criteria>` (up to 36 per feature, median 15 among fully-defined ones),
`<notes>` (up to 28 KB per feature), and MoSCoW priority all reach `analysis.json` or stop earlier,
and none reaches a task. *(Measured; restated from P1/P2/P4.)*

The brownfield path is a real attempt at spec-anchored and is the more interesting half of this
repository. But the artefact that persists is `PROJECT.md`, and `PROJECT.md` is **descriptive** —
generated from the code by [`crd-investigator`](../../agents/crd-investigator.md), refreshed from
`git diff` by [`crd-context-updater`](../../agents/crd-context-updater.md), and finalised from
completed task exports by
[`project-context-finalizer`](../../agents/project-context-finalizer.md). The loop is
code → context → change request → code. The PRD is not in it, and neither is any prescriptive
statement of intent.

**C1 — Nothing in this toolchain can detect that code has diverged from intent.** *Structural.
Static.*

`check-project-md.py --status` compares a recorded hash against HEAD and reports staleness — that
is *code changed since we described it*, which is a different and much weaker statement than *code
no longer does what we said it would do*. There is no artefact that both persists and asserts
intent, so there is nothing for drift to be measured against. This is the definitional gap between
spec-first and spec-anchored, and it is shared with Kiro and spec-kit; only Tessl addresses it. It
is called out here not as a competitive deficiency but because the CRD loop is *nearly* the right
shape to carry it and currently does not.

---

## 4. What this toolchain has that the field does not

These are genuine, and none of them appears in the three tools' published material.

**S1 — Execution isolation is a substrate, not a loop.** `/speckit.implement` is a single agent
executing a task list. Kiro groups tasks into concurrent waves. This runs one **git worktree per
task** ([`create-worktree.sh`](../../skills/execute-batch/scripts/create-worktree.sh), invoked by
the caller since F20), dispatches a [`task-implementer`](../../agents/task-implementer.md) into it,
has a **separate agent on a different model** verify the result
([`execute-verify`](../../skills/execute-verify/SKILL.md) — Haiku, independent of the implementer),
and drains a **sequential merge queue** so parallel tasks cannot conflict on merge. Neither
comparator isolates, and neither separates implementation from verification.

**S2 — State is derived from git, never asserted.** The rule in
[`execute/SKILL.md`](../../skills/execute/SKILL.md) — completion is a commit SHA verified with
`git cat-file -e`, counts come from the ledger and are never incremented, `status: completed`
requires `verified == expected` *and* an empty `missing` list — is the strongest idea in this
repository. spec-kit's nearest equivalent is `/speckit.converge`, which is an LLM re-reading the
codebase and forming a judgement; Kiro shows "real-time status updates" with no stated
verification. The history behind S2 is the argument for it: run 6 succeeded and still reported 23
completed of 18, 19 entries in an 18-slot list, and an invented elapsed time — every wrong figure
maintained by hand, the one right figure derived.

**S3 — Guards that cannot be reasoned with.** Böckeler's instruction-non-compliance critique is the
one she raises with no proposed fix. This repository hit it in its sharpest form (F15: pointed at a
documentation tree with no git repository, `/execute` produced a full plan and explained that the
missing repository *"is expected since this is a greenfield project where L0-002 initializes
git"* — reasonable, fluent, and false) and answered it structurally. Six formerly-prose steps are
now scripts whose exit status is the decision: `preflight.sh`, `resolve-output.sh`,
`create-worktree.sh`, `record-task.sh`, `ledger-status.sh`, `build-manifest.py`, `write-state.py`.
**An exit code cannot be talked past.** This is the most transferable thing here and it is
currently documented only inside an internal assessment.

**S4 — Per-phase model economics.** Haiku for analysis, layer planning, review, verification and
implementation; Opus for task generation and breakdown orchestration; Sonnet for the execute and
CRD orchestrators. No comparator does model tiering. It is undercut by C7 below, but the idea is
sound and unmatched.

**S5 — Interface contracts as the coupling mechanism.** A task's `<exports>` becomes the next
task's `<dependencies>`, carrying complete type signatures with imports rather than prose. This is
a better answer to task self-containment than spec-kit's global `contracts/` directory, because it
is generated per-edge and scoped to what the consumer actually needs.

---

## 5. What the field has that this toolchain does not

**C2 — There is no constitution, and no steering. The architectural opinions are vendored into the
plugin.** *Structural. Static.* **This is the largest gap in the document.**

spec-kit has `memory/constitution.md` with numbered articles enforced as gates. Kiro has steering
files. Searching `skills/`, `agents/` and `commands/` for *constitution*, *steering*, *coding
standard* or *conventions* returns exactly two files —
[`crd-investigate/SKILL.md`](../../skills/crd-investigate/SKILL.md) and
[`crd-investigator.md`](../../agents/crd-investigator.md) — and both only *infer* conventions from
existing code. Nothing lets a project *declare* them.

Meanwhile the toolchain holds strong opinions and holds them in skill text:

| Opinion | Where it lives | Overridable? |
|---|---|---|
| Five layers, `foundation → backend → frontend → integration` | [`layer-definitions.md`](../../skills/breakdown/references/layer-definitions.md) | No |
| TDD is mandatory | [`tdd-workflow.md`](../../skills/execute-batch/references/tdd-workflow.md) | No |
| Max 3 files per task | [`task-format-spec.md`](../../skills/breakdown/references/task-format-spec.md) | No |
| Templates are `python` / `go` / `tanstack` | `layer-definitions.md` | No |
| A task's verification is runnable commands | task format | No |

Every one of those is defensible. None is universal, and a user who disagrees with any of them must
fork the plugin. The fix is not to soften the opinions but to move them into an artefact the
*target project* owns.

**C3 — Ambiguity has no channel, and the design actively suppresses it.** *Correctness. Static.*

spec-kit mandates `[NEEDS CLARIFICATION: …]` markers wherever the spec is thin, and
`/speckit.clarify` exists to resolve them. Kiro gates each phase on human approval. This toolchain
does neither, and worse, the two halves of its design push against each other:

- [`breakdown-analyze-prd`](../../skills/breakdown-analyze-prd/SKILL.md) is *instructed* to infer —
  data models "inferred from feature descriptions", API endpoints inferred, frontend components
  inferred, with the guidance *"Infer carefully: data models and APIs should be reasonable
  inferences, not guesses."*
- [`review-criteria.md`](../../skills/breakdown/references/review-criteria.md) makes `TBD`, `TODO`,
  `[to be determined]`, `appropriate`, `suitable`, `as needed` and *"necessary (without
  specifics)"* **critical** failures. One critical issue fails the batch and forces regeneration.
- Grepping `breakdown/SKILL.md` and `execute/SKILL.md` for user confirmation points returns
  **nothing**. `/breakdown` and `/execute` never ask a human anything.

So the toolchain requires inference, forbids the marking of it, and provides nowhere to escalate.
The only output that satisfies all three constraints is confident invention — and the reviewer,
reading a task file whose entire design goal is self-containment, has no way to distinguish an
invented field name from a specified one. That the retry loop then re-runs generation with the
reviewer's complaint attached makes it worse, not better: the second attempt is under more pressure
to sound specific than the first.

Note that `/prd` itself is the counter-argument, and a good one. Its eight-phase interview is a
better ambiguity-resolution mechanism than `/speckit.clarify`, because a human is answering. The
failure is that nothing the interview *fails* to resolve survives the handoff — `what-next.md` TBD
items have no consumer in `/breakdown` (P10 covers the format problem; this is the consumption
problem).

**C4 — No cross-artefact consistency pass.** *Correctness. Static.*

`/speckit.analyze` reconciles spec ↔ plan ↔ tasks before implementation runs.
[`breakdown-review-tasks`](../../skills/breakdown-review-tasks/SKILL.md) reviews each task **in
isolation** — completeness, self-containment, interface contracts, requirement specificity, test
requirements, verification steps, file scope. It never asks the two questions that matter across
the set:

- Is every must-have feature covered by at least one task?
- Does any task implement something the PRD did not ask for?

Combined with P1 (won't-have features are built, because priority is extracted into
`analysis.json` and then never read), the second question is not hypothetical.

**C5 — No traceability from code back to requirement.** *Structural. Static. Restates P15.*

Kiro traces tasks back to requirements as a documented property of `tasks.md`. Here a task carries
`<id>`, `<name>`, `<layer>`, `<priority>` and no `source-feature`. After `/execute`, the question
*"which commit satisfies acceptance criterion 3 of `save-link`?"* is unanswerable — and it is
exactly the question that would make the PRD durable rather than disposable. Worth noting that the
ledger already records a commit SHA per task, so half the link exists; only the other half is
missing.

**C6 — No artefact schema validation.** *Correctness. Static.*

[`tests/test_toolchain.py`](../../tests/test_toolchain.py) is 31 static checks on the *toolchain* —
frontmatter keys, model identifiers, the absence of `allowed-tools`. Nothing validates a generated
PRD, CRD, task file or `PROJECT.md` against a schema. `review-criteria.md` is a prose checklist
executed by an LLM, which is the same enforcement model spec-kit's checklists use and which S3 has
already established is the weaker one.

The cost is on record. F24's sibling: the finalizer wrote `?tag=python&status=archived` into a
`<description>`, a bare `&` is not valid XML, `<project-context>` stopped parsing, and
`crd-impact-analysis` — which reads `<api-registry>` out of that block — broke silently, as did the
finalizer's own next run. `check-project-md.py --fix` now escapes ampersands in that one file.
Nothing does it for the other four artefact types. Item 22 of `plugin-2.0-plan.md` proposes the
general fix.

**C7 — The model tiering is not sized against its inputs.** *Correctness. Measured.*

S4 is real but it is asserted rather than budgeted. `breakdown-analyze-prd` runs on Haiku and takes
the whole PRD; the corpus measures 64 feature files at ~594 KB ≈ 165k tokens, with `index.md` alone
at ~13k. The first step of `/breakdown` does not fit in the model it is assigned (P5, graded
Blocking there). Tiering that does not measure its input is a cost decision dressed as an
architecture.

**C8 — Portability and distribution.** *Structural. External.*

spec-kit is a CLI installing into 30+ agents. Kiro spans IDE, CLI, web and mobile. Tessl ships a
registry with versioning, rollback, RBAC and security scanning. This is a Claude Code plugin loaded
with `--plugin-dir` from a checkout, not published to a marketplace. Entirely reasonable for a
repository whose stated purpose is demonstrating Claude Code features — recorded because "14 skills
you must clone and path-mount" is a real adoption ceiling, and because §7 argues the toolchain now
contains ideas worth exporting.

---

## 6. Böckeler's critiques, applied here

**C9 — The workflow does not scale down, and the concession does not go far enough.** *Structural.
Static.*

Her finding was Kiro bloating a bug fix with user stories and spec-kit over-engineering moderate
features. The greenfield path here is worse than either: eight interview phases, five layers,
batched generate → review → retry with up to three attempts per batch of five tasks. `/crd` is the
intended concession and it is the right instinct — CRDs skip Layer 0, use `<impact-analysis>` to
scope generation, and typically produce two or three layers. But a dark-mode toggle still costs a
full `PROJECT.md` investigation (or an incremental update), eight CRD phases, an impact-analysis
sub-skill, layer planning, task generation, review, and the whole worktree/verify/merge machinery
for what the impact analysis itself estimated at three files.

There is no path in this repository for a change small enough that the ceremony costs more than the
change.

**C10 — Self-containment amplifies the review burden that the field already has.** *Structural.
Measured.*

Böckeler's complaint was repetitive verbose markdown, tedious to review, possibly worse than
reviewing the code. Here the duplication is not incidental, it is **mandated**: every task inlines
its PRD excerpt, its tech stack, its full project structure, and complete interface contracts with
imports for every dependency. `review-criteria.md` makes the alternative a critical failure —
*"As described in the PRD" → Copy relevant PRD text inline*.

That is correct for the consumer. Tasks target ~50k-token models, and self-containment is what
makes Haiku a viable implementer. It is expensive for the human: on a corpus of 165k tokens, the
task set will exceed the PRD in volume while containing no information the PRD did not have. Two
aggravating factors are worth separating from the general problem — the format is XML, which is
machine-parseable (right for `/execute`) and strictly harder to skim than markdown (wrong for the
review pass that is already the bottleneck); and there is no rendered view of a task set, only 18
to 48 XML files.

**The MDD parallel lands on the layer model specifically.** Böckeler's sharpest line is that
LLM-based SDD risks combining MDD's inflexibility with the LLM's non-determinism. Layers 0–4, in a
fixed `setup → foundation → backend → frontend → integration` order, encode one architecture — a
CRUD web application built from a template — as though it were the shape of software. A CLI tool, a
library, a data pipeline, an embedded target or anything event-driven does not decompose that way,
and the toolchain offers no way to say so. This is C2 seen from the other end: the inflexibility is
not that the layers are wrong, it is that they are not the project's to change.

---

## 7. Summary

| Axis | This toolchain | spec-kit | Kiro | Tessl |
|---|---|---|---|---|
| Böckeler level | spec-first | spec-first | spec-first | spec-as-source (beta) |
| Project-owned rules | **none (C2)** | constitution + gates | steering files | — |
| Ambiguity marking | **suppressed (C3)** | `[NEEDS CLARIFICATION]` + `/clarify` | phase approval gates | — |
| Human gates after authoring | **none** | optional passes | one per phase | — |
| Cross-artefact check | **none (C4)** | `/speckit.analyze` | — | sync |
| Traceability to requirement | **none (C5)** | via contracts/entities | tasks → requirements | inherent |
| Artefact schema validation | **none (C6)** | LLM checklists | — | typed spec |
| Execution isolation | **worktree per task (S1)** | single loop | dependency waves | — |
| Independent verification | **separate agent + model (S1)** | — | — | `@test` |
| State derived from VCS | **yes (S2)** | `/converge` (LLM) | status updates | — |
| Non-negotiable guards | **exit codes (S3)** | prose gates | — | — |
| Model tiering | **yes (S4/C7)** | — | — | — |
| Scales down to small change | **no (C9)** | no | no | — |
| Distribution | plugin dir | CLI, 30+ agents | product | registry |

Read as a shape: **this is the strongest execution engine of the four and the weakest specification
discipline.** spec-kit and Kiro spend their rigour on getting the spec right and then largely
hand-wave the build. This repository does the reverse, and does it with unusual honesty about what
has actually been measured. The two halves are not equally mature, and the gap between them is the
subject of both this document and `plugin-2.0-plan.md`.

---

## 8. Remediation items

Ordered by what each unblocks, not by size. Items that duplicate `plugin-2.0-plan.md` are marked
and not restated.

### 1. A project-owned constitution — `PRINCIPLES.md` in the target *(C2, C9, and the MDD parallel)*

One file in the target project, read by `/breakdown` and enforced by `/execute`, declaring:
architecture style and layer definitions (replacing the fixed five), test policy (making TDD a
default rather than a law), file-scope limits, banned patterns, and the template or scaffold to
build from. This is the highest-leverage item in the document because it simultaneously resolves
C2, defuses the MDD critique, removes the hardcoded template list, and makes the layer model a
parameter instead of an axiom.

It should follow S3, not the prose it replaces: a script validates the file and exits non-zero if
`/breakdown` is about to proceed against a constitution it did not parse.

### 2. A clarification channel that survives the handoff *(C3)*

A `<needs-clarification>` element that `/prd` may emit, `analysis.json` must carry, task files must
preserve, and `review-criteria.md` **requires rather than forbids** — with `/execute` refusing to
start on any task that still has one unresolved. The current design applies the honesty discipline
of S2 rigorously to *state* and not at all to *knowledge*; this is that discipline extended one
step.

The corollary is a change to `review-criteria.md`: the placeholder ban must apply to *unmarked*
vagueness only. Banning `TBD` outright is what makes invention the compliant answer.

### 3. A consistency pass between `/breakdown` and `/execute` *(C4)*

The `/speckit.analyze` equivalent, and cheap because `manifest.json` already exists and is already
built from the files rather than the plan. Three assertions: every must-have feature has at least
one task; every task names a source feature; no task exists without a requirement behind it. A
script, exit code, non-zero blocks.

### 4. `source-feature` on every task *(C5; = item 16 of `plugin-2.0-plan.md`)*

Not restated. Noted here because the ledger already stores a commit per task, so this one field
completes a requirement → task → commit chain that is otherwise two thirds built.

### 5. A `--small` path *(C9)*

Below a threshold — say three files, from the impact analysis that already computes it — skip layer
planning entirely: one task, one worktree, one verification, one merge. The execution substrate
(S1) is worth keeping at any size; the planning ceremony is not.

### 6. Artefact schema validation in the test suite *(C6; = item 22 of `plugin-2.0-plan.md`)*

Not restated, except to record that C6 is the general form of the bare-`&` incident, and that
`check-project-md.py --fix` currently solves it for one of five artefact types.

### 7. Size the tiering against measured inputs *(C7)*

Depends on item 18 of `plugin-2.0-plan.md` (per-feature analysis plus a size refusal). Once
analysis is per-feature, Haiku is defensible; until then the assignment should either change model
or refuse.

### 8. Extract S3 as a document in its own right

"Prose guards are weighed; exit codes are obeyed" is the most transferable finding this repository
has produced, it answers a critique the field has published and not solved, and it is currently a
paragraph inside a 140 KB internal assessment. It belongs in `docs/` as a standalone note, with F15
as its worked example.

### 9. Housekeeping

- [`CLAUDE.md`](../../CLAUDE.md) documents an `execute-task` skill that no longer exists (removed by
  item 4.15 / F20 — the worktree is now created by the caller and the path passed in) and a
  `.claude/` layout the repository does not use. Its own preamble warns about the layout; the
  directory tree below it contradicts the warning.
- [`docs/skills/probes/`](probes/) is a homegrown eval harness. It is conceptually the same thing
  Tessl now sells as scenario evals, and it is better than anything spec-kit or Kiro publish. It is
  also a one-off measurement script. Deciding whether it becomes a permanent capability is worth
  doing deliberately.

**Suggested order.** 1 first — it is the largest, and items 3 and 5 both become easier once layers
are declared rather than assumed. Then 2, because every later item is more valuable once tasks can
admit what they do not know. Then 3 and 4 together, since the consistency pass needs
`source-feature` to check anything interesting. Then 5, 6, 7. Items 8 and 9 are independent and can
go at any time.

---

## 9. Open questions

1. **Should the constitution and `PROJECT.md` be one file?** They answer adjacent questions — *what
   this project is* versus *what this project must obey* — and `plugin-2.0-plan.md` §7 already asks
   a near-identical question about `architecture.md`. Three files describing one project is probably
   one too many. The argument for keeping them apart is the same as there: one is descriptive and
   hash-stamped against a commit, the other is prescriptive and authored before any code exists.
2. **Is spec-anchored actually the goal?** C1 identifies the gap honestly, but closing it means the
   PRD must be maintained after `/execute` finishes, and nothing in this repository suggests anyone
   would. The cheaper alternative is to be deliberately spec-first and say so — treat the PRD as
   scaffolding, invest in the CRD loop as the durable path, and drop the implication that
   `docs/prd/` means anything six months later. That is a defensible position and it is not the one
   the documentation currently implies.
3. **Does the XML format survive contact with C10?** It is right for `/execute` and wrong for the
   human review pass. A renderer — task set to a single readable markdown summary — may be a cheaper
   answer than changing the format.
4. **Unmeasured:** none of the comparisons in §7 is an output-quality claim, because no comparator
   has been run against this repository's fixture. Running `specify` against
   `tests/fixture/prd/link-shelf` would make several rows in that table falsifiable, and is the
   single most useful experiment this document suggests.

---

## 10. Sources

- Birgitta Böckeler, *Exploring Gen AI: Three tools for spec-driven development* —
  https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- GitHub spec-kit, `spec-driven.md` — https://github.com/github/spec-kit/blob/main/spec-driven.md
- GitHub spec-kit, README (current `/speckit.*` command set) — https://github.com/github/spec-kit
- Kiro — https://kiro.dev/ and https://kiro.dev/docs/specs/
- Tessl — https://tessl.io/ , https://docs.tessl.io/ , and
  https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry

Retrieved 2026-08-22. Tessl Framework details are from its launch material and Böckeler's account
of the private beta; the Framework's own documentation is not public, and every Framework claim
here should be treated as second-hand.
