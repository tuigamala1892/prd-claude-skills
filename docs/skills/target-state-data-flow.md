# Target State — Data Flow

**Status:** Target state. **None of this is built.** It is the shape the toolchain takes if
[`plugin-2.0-plan.md`](plugin-2.0-plan.md) is implemented in full.
**Date:** 2026-08-25
**Companion to:** [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) §Data Flow, which describes what
exists today. Read that first; this document is the delta.

Item numbers in `(n)` refer to the plan. Where a box is new or changed, the marker says which item
puts it there.

---

## 0. What changed, in one table

| Today (ARCHITECTURE.md) | Target state |
|---|---|
| Two schemas defined independently, PRD templates inside a command file | One **shared core** both paths cite (44) |
| `analyze-prd` receives the whole PRD in one prompt | **Per-feature** analysis, with a size refusal (18) |
| Layers `[0,1,2,3,4]` fixed for every PRD | Layer **graph** from the project (28), layer **set** derived from content (31) |
| Acceptance criteria read on the CRD path only | Carried verbatim into tasks on both (17) |
| `<notes>` and MoSCoW written, never read | Structured and consumed (2, 16, 34) |
| No architecture input, none recorded on greenfield | `architecture.md` in, `PROJECT.md` out (25, 26) |
| Nothing asks about architecture; nothing writes the rules | A **Design phase** between 3 and 4 (51) |
| `/prd` never looks for `PROJECT.md` | Context check at initialization (52) |
| Nothing between `/breakdown` and `/execute` | A coverage check and a gate (30, 38) |
| Guards are prose | Guards are exit codes (9, 22, 39, 43) |

---

## 1. The shared schema core

Everything else in this document depends on this existing. It is item 44, and it is why the two
paths can be drawn with the same boxes.

```
                        schema/core  (44)
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐
   │  <criterion>  │  │    <gaps>     │  │   identifiers     │
   │  pattern=     │  │  kind=        │  │  <source-feature> │
   │    EARS (33)  │  │  raised=      │  │  <satisfies-      │
   │  priority=    │  │  id=          │  │    criteria>      │
   │    P0|P1|P2   │  │        (29)   │  │      (16, 30)     │
   │       (34)    │  │               │  │                   │
   └───────┬───────┘  └───────┬───────┘  └─────────┬─────────┘
           │                  │                    │
           └──────────────────┼────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     PRD artefacts                   CRD artefacts
     index.md, features/*.md         docs/crd/{slug}.md
     architecture.md                 PROJECT.md
              │                               │
              └───────────────┬───────────────┘
                              ▼
                      task XML  (17)
```

Three vocabularies are **disjoint by construction** (45), so no value appears in two of them:

```
   <definition>   tbd · in-progress · defined · excluded · superseded   (feature: how specified)
   <workflow>     draft · ready · in-progress · complete · abandoned    (CRD: where in the process)
   built=         planned · partial · complete                          (PROJECT.md: what exists)
```

---

## 2. `/prd` — authoring

```
User idea ──────────────────────────────┐
                                        ▼
                          ┌─────────────────────────────┐
                          │  Initialization   CHECK     │
                          │  existing PRDs?      (F3)   │
                          │  PROJECT.md?         (52)   │
                          │  architecture.md?    (52)   │
                          └──────────────┬──────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │  Phases 1–3                 │
                          │    idea, stack, features    │
                          └──────────────┬──────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │  Phase 3.5   DESIGN   (51)  │
                          │                             │
                          │  "discuss architecture, or  │
                          │   take the default graph?"  │
                          │                             │
                          │  default → writes nothing;  │
                          │    the shipped graph applies│
                          │  discuss → <rules> + ASR    │
                          │    flags (35) + ADRs (36)   │
                          │    layers · testing · limits│
                          │    banned · repo-structure  │
                          │  existing file → follow /   │
                          │    extend / override   (52) │
                          └──────────────┬──────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │  Phases 4–5                 │
                          │    dependencies, options    │
                          │  (deps follow architecture) │
                          └──────────────┬──────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
                    ▼  (optional, per feature)                ▼
      ┌───────────────────────────────┐          ┌─────────────────────────┐
      │  prd-criteria-author  (8, 40) │          │  Phase 6   CHECK        │
      │  agent · context: fork        │          │  check-prd.py  (6, 9)   │
      │                               │          │                         │
      │  mode: propose-criteria       │          │                         │
      │    + drafts <user-story>      │          │  · derive a status      │
      │    EARS patterns unrepresented│          │    CEILING, not a value │
      │  mode: review-definition      │          │  · EARS pattern cover   │
      │    the seven tests            │          │  · index ↔ features/    │
      │                               │          │  · gaps well-formed     │
      │  proposes; never writes       │          │  · ADR/OQ refs resolve  │
      └───────────────┬───────────────┘          │  · contract rule (40)   │
                      │                          └────────────┬────────────┘
                      │  user accepts/rejects                 │
                      └───────────────┬───────────────────────┘
                                      │  reports — never auto-corrects
                                      ▼
                          ┌─────────────────────────────┐
                          │  Phase 8   write            │
                          │  refuses on collision (F3)  │
                          └──────────────┬──────────────┘
                                         ▼
   architecture.md        ◄── NEW (25, 28, 51): PROJECT ROOT, not per-PRD —
                              <rules>: layers, testing, task-limits, banned,
                              scaffold, repo-structure — ENFORCED
                              <principles>: guidance, NOT enforced      (37)
                              *-registry: root siblings of <rules>,
                              read not obeyed, PROJECT.md's names  (25)

   docs/prd/{slug}/
   ├── index.md            ◄── features + MoSCoW priority (§4.1), tech stack
   ├── what-next.md        ◄── XML skeleton, markdown bodies (11)
   │                            <authoring-gaps> DERIVED from features' <gaps>
   │                            <next-steps kind="…">, <risks>, <open-questions href=…>
   └── features/
       └── {feature}.md    ◄── <user-story> (1, 40), <definition>,
                                EARS criteria (33) with P0|P1|P2 (34),
                                <gaps> (29), <notes><data-model> (2),
                                <architecturally-significant> (35), <depends-on> (27)
                                no <phases> — retired to priority + gaps (5)

   ../../architecture/decisions/NNN-*.md   ◄── ADRs (36), **Drives:** back to features
   ../../product/open-questions.md         ◄── cross-feature unknowns (40)
```

**`--resume` re-runs the Phase 6 check across every feature** (7), not only the ones it touched —
the untouched ones are exactly where labels have gone stale.

---

## 3. `/crd` and `/crd-context` — brownfield authoring

```
User change description + --project ────┐
                                        ▼
                          ┌─────────────────────────────┐
                          │  /crd   Phase 1  context    │
                          │  check-project-md.py        │
                          └──────────────┬──────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │ no PROJECT.md            │ stale hash               │ current
              ▼                          ▼                          │
   ┌────────────────────┐    ┌────────────────────┐                 │
   │ /crd-investigate   │    │ /crd-context-update│                 │
   │  full sweep        │    │  git diff since    │                 │
   │                    │    │  last-context-hash │                 │
   └─────────┬──────────┘    └─────────┬──────────┘                 │
             └───────────┬─────────────┘                            │
                         ▼                                          │
                   PROJECT.md  ◄── architecture, built= per feature │
                         │          registries (open set, item 25)  │
                         └──────────────────┬───────────────────────┘
                                            ▼
                          ┌─────────────────────────────┐
                          │  Phase 4  impact analysis   │
                          │   affected files/features/  │
                          │   apis/schemas              │
                          │   <scope>  — a CROSS-CHECK  │
                          │             not routing (31)│
                          │   <confidence>  → gaps (49) │
                          └──────────────┬──────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │  Phase 5  requirements      │
                          │  EARS criteria only —       │
                          │  <requirements> RETIRED (46)│
                          │  deferrals become <gaps>(48)│
                          └──────────────┬──────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │  Phase 7  write             │
                          │  --resume + pre-write guard │
                          │             NEW (48)        │
                          └──────────────┬──────────────┘
                                         ▼
   {project}/docs/crd/{slug}.md
   ├── <meta>  <workflow> (45) · MoSCoW <priority> NEW (47) · schema_version (43)
   ├── <context>  project-ref · prd-ref · related-features
   ├── <impact-analysis>  … <scope> <confidence>
   ├── <acceptance-criteria>  EARS, P0|P1|P2  ◄── one list, one id space (46)
   └── <gaps>  NEW (48)
```

**Item 46 is the structural change.** A CRD carried `<requirements>` *and* `<acceptance-criteria>`
as separate, unlinked lists, because Given/When/Then cannot state a requirement. An EARS criterion
can, so the split has nothing left to carry.

---

## 4. `/breakdown` — both inputs, one pipeline

```
   docs/prd/{slug}/           OR      {project}/docs/crd/{slug}.md
   + architecture.md                  + PROJECT.md
            │                                  │
            └──────────────────┬───────────────┘
                               ▼
             ┌───────────────────────────────────┐
             │  Phase 1   resolve + REFUSE       │
             │   resolve-output.sh               │
             │   parse <rules>; refuse if        │
             │     present and unparseable  (28) │
             │   schema_version compatible? (43) │
             └─────────────────┬─────────────────┘
                               ▼
             ┌───────────────────────────────────┐
             │  Phase 2   analyse                │
             │                                   │
             │   index pass      ~13k tokens     │
             │        │                          │
             │        ▼                          │
             │   per-feature pass, one at a time │
             │   REFUSE if a prompt would exceed │
             │   the window            (18)      │
             │                                   │
             │   reads <notes><data-model>       │
             │   rather than inferring one   (2) │
             └─────────────────┬─────────────────┘
                               ▼  analysis.json  (+ criteria, + gaps)
             ┌───────────────────────────────────┐
             │  Phase 2.5   FILTER               │
             │   --priority        MoSCoW  (14)  │
             │   --requirement-level P0|P1|P2(34)│
             │   skip wont-have/excluded/        │
             │        superseded          (13)   │
             │   refuse <gap kind=specification> │
             │                        (15, 29)   │
             │   report every skip BY NAME       │
             └─────────────────┬─────────────────┘
                               ▼
             ┌───────────────────────────────────┐
             │  Phase 3   plan layers            │
             │   graph  ← <rules><layers>  (28)  │
             │           else shipped default    │
             │   set    ← DERIVED from content   │
             │           a tier with no work is  │
             │           not a tier         (31) │
             │   edges  ← <depends-on>      (27) │
             │   no unconditional integration    │
             └─────────────────┬─────────────────┘
                               ▼  layer_plan.json
             ┌───────────────────────────────────┐
             │  one tier + one task?             │
             │     └─► no plan. run it.     (31) │
             └─────────────────┬─────────────────┘
                               ▼
             ┌───────────────────────────────────┐
             │  Phase 4   generate → review      │
             │   criteria carried VERBATIM with  │
             │     their ids               (17)  │
             │   tests derived from criteria;    │
             │     unwanted-behaviour gives the  │
             │     negative test outright  (33)  │
             │   <testing policy> read here AND  │
             │     in review AND in execute (28) │
             │   marked uncertainty PASSES review│
             │     unmarked vagueness fails (29) │
             └─────────────────┬─────────────────┘
                               ▼
             ┌───────────────────────────────────┐
             │  Phase 5   finalize               │
             │   build-manifest.py               │
             │   + coverage check          (30)  │
             │     every in-scope feature has a  │
             │       task                        │
             │     every in-scope criterion is   │
             │       named by a task             │
             │     every ASR feature is named by │
             │       an ADR's **Drives:**        │
             │   + rendered summary        (32)  │
             └─────────────────┬─────────────────┘
                               ▼
   docs/tasks/{slug}/
   ├── manifest.json     ◄── toolchain_version + schema_version (24, 43)
   ├── summary.md        ◄── NEW (32): one row per task, no XML to read
   └── {layer}/L{n}-*.xml
           <meta>  <source-feature> · <moscow> · <satisfies-criteria> ·
                   <requirement-level> · <cwd>                    (16, 54)
           <acceptance-criteria>  verbatim, original ids          (17)
           <context>  data model, binding <rules> constraints     (2, 28)
```

---

## 5. The gate, and `/execute`

```
   docs/tasks/{slug}/
            │
            ▼
   ┌─────────────────────────────────────┐
   │  GATE  between breakdown & execute  │   ◄── NEW (38)
   │                                     │
   │   · coverage assertions       (30)  │
   │   · every ASR has a decision (35,36)│
   │   · no blocking <gap> remains (29)  │
   │                                     │
   │   design-track off → report         │
   │   design-track on  → confirm        │
   └──────────────────┬──────────────────┘
                      ▼
   ┌─────────────────────────────────────┐
   │  /execute   preflight               │
   │   preflight.sh · ledger-status.sh   │
   │   REFUSE a task whose <moscow> is   │
   │     wont-have               (20)    │
   │   REFUSE on schema_version          │
   │     incompatibility          (24)   │
   └──────────────────┬──────────────────┘
                      ▼
        execute-layer ──► execute-batch ──► task-implementer (worktree)
              │                 │
              │                 └──► execute-verify (independent)
              │
              └──► execute-merge   sequential, one task at a time
                          │
                          ▼
                    execute-state.json   schema_version (28, 43)
                    + <moscow> per task  → tier reported  (19)
                          │
                          ▼
   ┌─────────────────────────────────────┐
   │  project-context-finalizer          │
   │   if PROJECT.md exists → update     │
   │   if NOT and run came from a PRD    │
   │     → CREATE it, seeded from        │
   │       architecture.md        (26)   │
   └─────────────────────────────────────┘
```

Item 26 closes the loop: a greenfield project currently runs the whole pipeline and ends with no
architecture record, so the first `/crd` against it pays for a full investigation to rediscover
what the PRD already stated.

---

## 6. Where a guard fires

Every row is an exit code, not a paragraph — P16's lesson, and item 4.13's principle before it.

| Guard | Fires in | Item |
|---|---|---|
| Output path resolves, and is not inside a plugin | `/breakdown` Phase 1 | 4.6 |
| `<rules>` present but unparseable | `/breakdown` Phase 1 | 28 |
| `<repo-structure>` is `multi-repo` | `/breakdown` Phase 1 | 53 |
| `<layers>` graph is cyclic, or strands a task | `/breakdown` Phase 1 | 28, 43 |
| `schema_version` incompatible | `/breakdown` Phase 1, `/execute` preflight | 24, 43 |
| Prompt would exceed the model's window | `/breakdown` Phase 2 | 18 |
| Feature is `wont-have` / `excluded` / `superseded` | `/breakdown` Phase 2.5 | 13 |
| Feature carries `<gap kind="specification">` | `/breakdown` Phase 2.5 | 15, 29 |
| Artefact fails the shared schema | `/prd` end, `/breakdown` start, suite | 22, 44 |
| `ADR-NNN` / `OQ-NNN` reference does not resolve | `/prd` Phase 6, `/breakdown` start | 39 |
| A feature is `defined` while declaring a specification gap | `/prd` Phase 6 | §4.2, 3 |
| Coverage: an in-scope feature or criterion has no task | `/breakdown` Phase 5, gate | 30 |
| A task's `<moscow>` is `wont-have` | `/execute` preflight | 20 |
| A task specifies a `<banned>` pattern | `/breakdown` review-tasks | 56 |
| Implemented code contains a `<banned>` pattern | `/execute` execute-verify | 56 |
| A task exceeds `<task-limits>` for its path | `/breakdown` review-tasks | 56 |
| `PROJECT.md` carries no `*-registry` at all | `check-project-md.py` | 25 |
| A consumer's specific registry is absent | `crd-impact-analysis` | 25 |
| Rename left a reference to a slug with no file | `/prd --rename`, Phase 6 | 42 |

---

## 7. What is still undecided

These are open questions in the plan, and each one changes a box above.

- **`architecture.md` and `PROJECT.md`: one file or two?** Drawn here as two, joined by item 26's
  seeding step. (OQ2)
- **`<depends-on kind="data|runtime|reference">` — is that the right axis?** It feeds Phase 3's
  edges above. (OQ3)
- **Is the layer graph load-bearing for quality, or only convention?** If load-bearing, the shipped
  default in Phase 3 must be protected rather than merely provided. Answerable by experiment once
  item 43's fixtures exist. (OQ7)
