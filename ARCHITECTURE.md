# Architecture

> **Reconciled with the repository 2026-09-08** (item 72), after nine phases of
> `docs/skills/plugin-2.0-plan.md` landed without this file being touched. What that cost is
> recorded as findings V12 and V13 in
> [`docs/skills/plugin-2.0-verification.md`](docs/skills/plugin-2.0-verification.md), and it is
> the reason regression checks now read this file: **an onboarding document that nothing
> checks describes the project as it was on the day somebody wrote it.**
>
> **Layout.** Skills, agents and commands live at the repository **root** as a Claude Code
> plugin, not under `.claude/`. Load a checkout with **both** flags —
> `claude --plugin-dir <checkout> --add-dir <checkout>` — because `--plugin-dir` loads the plugin
> and does not make its bundled scripts readable.
>
> **Context fork works** (item 4.11). It did not for the life of this toolchain until then:
> every skill also declared `allowed-tools`, a *command* frontmatter key that stopped
> `context: fork` taking effect, so nothing forked, `agent:` never fired and no skill's `model:`
> applied. Removing that one line fixed all of it. Verified on real skills, not inferred —
> `toolUseResult.status == "forked"`, with the declared model appearing in `modelUsage`. See
> finding **F13**. **Never put `allowed-tools:` in a SKILL.md**, and note that the example below
> deliberately does not.

This document describes the system architecture for developers who want to understand, extend, or contribute to the PRD Breakdown Execute workflow.

---

## System Overview

```
                                    USER
                                      │
                                      ▼
          ┌───────────────────────────────────────────────────────┐
          │                    Claude Code CLI                    │
          └───────────────────────────────────────────────────────┘
                                      │
      ┌───────────────────────────────┼───────────────────────────────────┐
      │                               │                                   │
      │          ┌────────────────────┼────────────────────┐              │
      │          │                    │                    │              │
      ▼          ▼                    ▼                    ▼              ▼
┌─────────┐┌─────────────┐     ┌─────────────┐      ┌─────────────┐┌──────────────┐
│  /crd   ││    /prd     │     │  /breakdown │      │  /execute   ││/crd-context  │
│ Command ││   Command   │     │    Skill    │      │    Skill    ││  Command     │
│         ││             │     │             │      │             ││              │
│ context:││  context:   │     │  context:   │      │  context:   ││  context:    │
│  fork   ││  (default)  │     │  fork       │      │  fork       ││   fork       │
└────┬────┘└──────┬──────┘     └──────┬──────┘      └──────┬──────┘└──────────────┘
     │            │                   │                    │
     │            │                   │                    │
     │            ▼                   │                    │
     │      ┌─────────────┐           │                    │
     │      │  Phased     │           │                    │
     │      │  Interview  │           │                    │
     │      └──────┬──────┘           │                    │
     │             │                  │                    │
     │             ▼                  │                    │
     │      docs/prd/{slug}/          │                    │
     │      ├── index.md              │                    │
     │      ├── what-next.md          │                    │
     │      └── features/             │                    │
     │                                │                    │
     ▼                                │                    │
┌─────────────────────┐               │                    │
│  CRD Sub-Skills     │               │                    │
│                     │               │                    │
│  crd-investigate    │◄──PROJECT.md  │                    │
│  crd-context-update │  (generated)  │                    │
│  crd-impact-analysis│               │                    │
└─────────┬───────────┘               │                    │
          │                           │                    │
          ▼                           │                    │
   docs/crd/{slug}.md                 │                    │
                                      │                        │
                    ┌─────────────────┴─────────────────┐      │
                    │                                   │      │
                    ▼                                   │      │
          ┌───────────────────┐                         │      │
          │  breakdown-       │                         │      │
          │  analyze-prd      │                         │      │
          │  context: fork    │                         │      │
          └─────────┬─────────┘                         │      │
                    │                                   │      │
                    ▼                                   │      │
          ┌───────────────────┐                         │      │
          │  breakdown-       │                         │      │
          │  plan-layers      │                         │      │
          │  context: fork    │                         │      │
          └─────────┬─────────┘                         │      │
                    │                                   │      │
                    ▼                                   │      │
          ┌───────────────────┐                         │      │
          │  breakdown-       │◄────────────────────────┘      │
          │  generate-tasks   │                                │
          │  context: fork    │                                │
          └─────────┬─────────┘                                │
                    │                                          │
                    ▼                                          │
          ┌───────────────────┐                                │
          │  breakdown-       │                                │
          │  review-tasks     │                                │
          │  context: fork    │                                │
          └─────────┬─────────┘                                │
                    │                                          │
                    ▼                                          │
          docs/tasks/{slug}/                                   │
          ├── analysis.json                                    │
          ├── layer_plan.json                                  │
          ├── manifest.json                                    │
          ├── 0-setup/                                         │
          ├── 1-foundation/                                    │
          ├── 2-backend/                                       │
          ├── 3-frontend/                                      │
          └── 4-integration/                                   │
                                                               │
                              ┌────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   execute-layer   │
                    │   context: fork   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   execute-batch   │
                    │   context: fork   │
                    └─────────┬─────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │task-        │    │task-        │    │task-        │
    │implementer  │    │implementer  │    │implementer  │
    │agent, in a  │    │agent, in a  │    │agent, in a  │
    │worktree     │    │worktree     │    │worktree     │
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │exec-verify  │    │exec-verify  │    │exec-verify  │
    │context: fork│    │context: fork│    │context: fork│
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   execute-merge   │
                    │   (sequential)    │
                    └───────────────────┘
```

---

## Context Fork Mechanics

### What is Context Fork?

Skills can declare `context: fork` in their SKILL.md frontmatter:

```yaml
---
name: execute-batch
context: fork
model: claude-sonnet-5
---
```

**There is no `allowed-tools:` line, and its absence is the point.** It is a *command* key: in a
skill it restricts nothing and silently disables `context: fork` (F13). `tests/test_toolchain.py`
fails if any skill declares it, and — since item 72 — if this document shows one.

When a skill with `context: fork` is invoked:
1. A new, isolated context is created
2. The skill receives only the information passed to it
3. It cannot see parent context or sibling forks
4. Only the final result is returned to the parent

### Why Context Fork Matters

**Without fork:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Single Context                         │
│                                                             │
│  Task 1: Wrote User model...                               │
│  Task 1: Error in line 42...                               │
│  Task 1: Fixed error...                                    │
│  Task 2: Now confused by Task 1 details...                 │
│  Task 2: Incorrectly references Task 1 patterns...         │
│  Task 3: Context window nearly full...                     │
│  Task 3: Losing early context...                           │
│                                                             │
│  Result: Degraded quality, context exhaustion              │
└─────────────────────────────────────────────────────────────┘
```

**With fork:**
```
Main Context                       │
(Orchestrator)                     │ Returns: "L1-001 completed"
    │                              │
    ├── Fork: Task L1-001 ─────────┘
    │   └── Clean context
    │   └── Only task spec
    │   └── Full focus
    │
    ├── Fork: Task L1-002 ────────────── Returns: "L1-002 completed"
    │   └── No knowledge of L1-001
    │   └── Fresh context
    │
    └── Fork: Task L1-003 ────────────── Returns: "L1-003 completed"
        └── Completely independent
```

### Benefits

| Aspect | Without Fork | With Fork |
|--------|--------------|-----------|
| Context isolation | None | Complete |
| Parallelism | Sequential only | True parallel |
| Error propagation | Spreads to all | Contained |
| Context usage | Cumulative | Per-task |
| Verification bias | High | None |
| Scalability | Degrades | Linear |

---

## Model Selection Strategy

Different components use different models based on their requirements:

| Component | Model | Reasoning |
|-----------|-------|-----------|
| `/prd` · `/crd` · `/crd-context` | *(none declared)* | Commands run in the session's model; the interview is the user's conversation |
| `breakdown` | `claude-opus-5` | Orchestration, and the phase that refuses |
| `breakdown-analyze-prd` | `claude-haiku-4-5` | Per-feature after item 18, so the prompt is small |
| `breakdown-plan-layers` | `claude-haiku-4-5` | Assignment against a validated graph, not invention |
| `breakdown-generate-tasks` | `claude-opus-5` | The task is the deliverable; this is where fidelity is won or lost |
| `breakdown-review-tasks` | `claude-haiku-4-5` | Fast quality validation against `review-criteria.md` |
| `crd` | `claude-sonnet-5` | Context management, impact analysis |
| `crd-investigate` | `claude-sonnet-5` | Deep codebase analysis |
| `crd-context-update` | `claude-haiku-4-5` | Incremental, diff-scoped |
| `crd-impact-analysis` | `claude-haiku-4-5` | Reads registries rather than inferring them |
| `execute` | `claude-sonnet-5` | Orchestration logic |
| `execute-layer` | `claude-sonnet-5` | Layer coordination and the sequential merge |
| `execute-batch` | `claude-sonnet-5` | Worktrees and parallel dispatch |
| `execute-verify` | `claude-haiku-4-5` | Fast, focused, and a different model from the implementer |
| `execute-merge` | `claude-sonnet-5` | Git operations |
| `migrate` | `claude-sonnet-5` | One artefact, one schema version, judgements escalated |
| `task-implementer` (agent) | `claude-haiku-4-5` | Small context by construction — one task, one worktree |
| `task-generator` (agent) | `claude-opus-5` | Same reasoning as `breakdown-generate-tasks` |
| `prd-criteria-author` (agent) | `claude-sonnet-5` | Adversarial: the case the author missed |
| `schema-migrator` (agent) | `claude-sonnet-5` | The judgement half `migrate.py` is forbidden to guess |

**The table is checked against the frontmatter, since item 72.** It previously said `sonnet` for
almost every row while the files declared a mix of haiku, sonnet and opus, and named
`execute-task`, which item 4.15 removed. A table of assignments nobody compares to the files is a
table of intentions.

**Where a skill and the agent it names disagree, the skill's `model:` wins** — so the agent's is
the one silently ignored (finding F6).

### Selection Principles

1. **Sonnet for reasoning**: Architecture, implementation, orchestration
2. **Haiku for speed**: Verification, review, quality checks
3. **Independent verification**: Verifier uses different model than implementer

---

## File Structure

Everything below is at the **repository root**. There is no `.claude/` directory in this plugin.

```
.claude-plugin/plugin.json        name, version, author
│
schema/                           the single definition both paths cite (item 44)
├── core.md                       every shared element: criteria, gaps, definition, review
├── prd-format.md                 what /prd writes; cites core.md
├── decision-record.md            the ADR template and its **Drives:** convention (item 36)
├── migration.md                  one section per version step, and who may judge what (item 41)
├── checks.md                     one assertion, one owning script, every caller (item 58)
├── readers.md                    the elements with no reader, and why (item 23)
├── parity.md                     where the two paths differ, and whether that is settled
└── scripts/
    ├── migrate.py                one artefact, one version forward, or escalate
    ├── check-artefacts.py        every artefact is the shape its schema describes
    ├── check-readers.py          every element has a reader, or a recorded reason
    └── build-what-next.py        what-next.md is derived, never hand-maintained
│
commands/                         the user-invocable entry points
├── prd.md                        /prd -- a phased interview
├── crd.md                        /crd -- change request against an existing codebase
└── crd-context.md                /crd-context -- build and maintain PROJECT.md
│
skills/
├── breakdown/                    PRD or CRD -> tasks (orchestrator)
│   ├── references/               layer-definitions · layer0-templates · review-criteria
│   │                             task-format-spec · architecture-format
│   └── scripts/                  guards and generators; see schema/checks.md for which
│                                 assertion each one owns
├── breakdown-analyze-prd/        per feature after item 18, never per corpus
├── breakdown-plan-layers/        assigns work to the layer graph it was handed
├── breakdown-generate-tasks/     the task is the deliverable
├── breakdown-review-tasks/       PASS/FAIL against review-criteria.md
│
├── execute/                      task execution (orchestrator)
│   ├── references/               options · state-schema
│   └── scripts/                  preflight · write-state · ledger-status · check-project-md
│                                 check-compatibility · resolve-layers · task-integrity
├── execute-layer/                one layer: dispatch batches, then merge sequentially
├── execute-batch/                one batch: worktrees, then a task-implementer per task
├── execute-verify/               independent verification
├── execute-merge/                merges one verified task
│
├── crd/                          CRD orchestration
│   └── references/               crd-format · project-format
├── crd-investigate/              deep codebase analysis -> PROJECT.md
├── crd-context-update/           incremental update against a git hash
├── crd-impact-analysis/          what this change touches, in contracts not just APIs
└── migrate/                      artefact schema migration (item 41)
│
agents/
├── task-generator.md             task XML creation
├── task-implementer.md           one task, one worktree, small context
├── task-reviewer.md              quality validation
├── verification-runner.md        runs a task's verification commands
├── prd-criteria-author.md        proposes criteria and reviews a definition (item 8)
├── crd-investigator.md           deep codebase analysis
├── crd-context-updater.md        incremental updates
├── crd-impact-analyzer.md        impact analysis
├── project-context-finalizer.md  post-execute PROJECT.md updates
└── schema-migrator.md            one artefact, one schema version forward
│
tests/                            regression suite, mutation harness, versioned fixtures
docs/skills/                      the plan, the ledger, the reviews, the probes
```

**Two artefacts live in the *target* project, not here.** `PROJECT.md` describes a codebase as it
is; `architecture.md` prescribes what it must obey — the layer graph, test policy, task limits,
banned patterns. Both sit at that project's root, and item 26 is the seeding step between them.

### Skills vs Commands vs Agents

| Type | Location | Purpose | Invocation |
|------|----------|---------|------------|
| Command | `commands/` | User-invocable entry points | `/command-name` |
| Skill | `skills/<name>/SKILL.md` | Reusable workflow components | Called by other skills |
| Agent | `agents/` | Specialized task executors | Used with the Task tool |
| Schema | `schema/` | The single definition both paths cite (item 44) | Read, never invoked |

---

## Data Flow

*Current state: the diagrams below describe the toolchain as built.*

### PRD Phase

```
User Input (idea description)
         │
         ▼
    ┌─────────────────────┐
    │    /prd Command     │
    │                     │
    │  Phase 1: Idea      │
    │  Phase 2: Tech      │
    │  Phase 3: Features  │
    │  Phase 4: Design    │◄── item 51: writes architecture.md
    │  Phase 5: Deps      │
    │  Phase 6: Options   │
    │  Phase 7: Validation│◄── five scripts; exit codes, not questions
    │  Phase 8: Review    │
    │  Phase 9: Output    │◄── one feature per write (item 10)
    └─────────┬───────────┘
              │
              ▼
    docs/prd/{slug}/
    ├── index.md         ◄── Full PRD in XML format
    ├── what-next.md     ◄── Progress tracking
    └── features/
        ├── feature-1.md ◄── Feature details
        └── feature-2.md
```

### Breakdown Phase

```
docs/prd/{slug}/index.md
         │
         ▼
    ┌─────────────────────┐
    │  breakdown-         │
    │  analyze-prd        │──────► analysis.json
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  breakdown-         │
    │  plan-layers        │──────► layer_plan.json
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────────────────────────┐
    │  For each layer the plan emitted:       │
    │  (derived from content -- item 31 --    │
    │   never a fixed 0-4)                    │
    │                                         │
    │    ┌─────────────────────┐              │
    │    │ breakdown-          │              │
    │    │ generate-tasks      │──► L{n}-*.xml│
    │    └─────────┬───────────┘              │
    │              │                          │
    │              ▼                          │
    │    ┌─────────────────────┐              │
    │    │ breakdown-          │              │
    │    │ review-tasks        │──► PASS/FAIL │
    │    └─────────────────────┘              │
    │              │                          │
    │         (retry if fail)                 │
    └─────────────────────────────────────────┘
              │
              ▼
    docs/tasks/{slug}/
    ├── analysis.json      ◄── per feature, merged (item 18)
    ├── layer_plan.json    ◄── the layers that have work in them
    ├── architecture.json  ◄── only when the project declares architecture.md
    ├── manifest.json      ◄── final inventory, schema 1.2
    ├── tasks-summary.md   ◄── the set, reviewable without opening every task (item 32)
    └── {layer}/           ◄── one directory per surviving layer, named by the graph
```

**The layer names are the graph's, not this document's.** A project declaring its own `<layers>`
in `architecture.md` gets those; everything else gets the five-tier default. `/execute` asks
`resolve-layers.py` which layers to run rather than reciting a list (item 66) — reciting one is
what P44 was.

### CRD Phase (Brownfield)

```
User describes change + existing project path
         │
         ▼
    ┌─────────────────────┐
    │        /crd         │
    │   (orchestrator)    │
    └─────────┬───────────┘
              │
    ┌─────────┴─────────────────────────────────────┐
    │  Phase 1: Context Management                  │
    │                                               │
    │  PROJECT.md exists?                           │
    │    NO  ──► crd-investigate ──► PROJECT.md    │
    │    YES ──► context stale?                     │
    │              YES ──► crd-context-update       │
    │              NO  ──► proceed                  │
    └─────────────────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │  Phase 2: Capture   │
    │                     │
    │  - Change type      │
    │  - Motivation       │
    │  - Requirements     │
    └─────────┬───────────┘
              │
              ▼
    ┌─────────────────────┐
    │  crd-impact-        │──────► Impact report
    │  analysis           │        (files, features, APIs)
    └─────────┬───────────┘
              │
              ▼
    docs/crd/{slug}.md     ◄── CRD document
```

### Execute Phase

```
docs/tasks/{slug}/
         │
         ▼
    ┌─────────────────────┐
    │     /execute        │──────► execute-state.json
    │   (orchestrator)    │        (created/updated)
    └─────────┬───────────┘
              │
    ┌─────────┴─────────────────────────────────────────┐
    │  For each layer resolve-layers.py returns:        │
    │  (the plan's order, filtered to layers that have  │
    │   tasks -- item 66, never a list written here)    │
    │                                                   │
    │    ┌─────────────────────┐                        │
    │    │   execute-layer     │                        │
    │    └─────────┬───────────┘                        │
    │              │                                    │
    │    ┌─────────┴─────────────────────────────┐      │
    │    │  For each batch of ready tasks:       │      │
    │    │                                       │      │
    │    │    ┌─────────────────────┐            │      │
    │    │    │   execute-batch     │            │      │
    │    │    └─────────┬───────────┘            │      │
    │    │              │                        │      │
    │    │         (parallel)                    │      │
    │    │    ┌─────────┼─────────┐              │      │
    │    │    │         │         │              │      │
    │    │    ▼         ▼         ▼              │      │
    │    │  ┌───┐     ┌───┐     ┌───┐            │      │
    │    │  │T1 │     │T2 │     │T3 │  task-     │      │
    │    │  └─┬─┘     └─┬─┘     └─┬─┘  implementer     │
    │    │    │         │         │    in a worktree   │
    │    │    ▼         ▼         ▼              │      │
    │    │  ┌───┐     ┌───┐     ┌───┐            │      │
    │    │  │V1 │     │V2 │     │V3 │  execute-  │      │
    │    │  └───┘     └───┘     └───┘  verify    │      │
    │    └───────────────┬───────────────────────┘      │
    │                    │                              │
    │      task-integrity.py verify  ◄── item 63: a     │
    │                    │               task file the  │
    │                    │               run edited is  │
    │                    │               a stop         │
    │               (sequential)                        │
    │         ┌──────────┴────────┐                     │
    │         │   execute-merge   │  called by the      │
    │         │   (one at a time) │  LAYER, not the     │
    │         └───────────────────┘  batch              │
    │    │                                       │      │
    │    └───────────────────────────────────────┘      │
    │                                                   │
    └───────────────────────────────────────────────────┘
              │
              ▼
    Working code in project directory
              │
    ┌─────────┴───────────────────────────────────────┐
    │  PROJECT.md exists? (CRD execution)             │
    │                                                 │
    │    YES ──► project-context-finalizer            │
    │            ├── Extract exports from tasks       │
    │            ├── Update <features> section        │
    │            ├── Update <api-registry>            │
    │            ├── Update <schema-registry>         │
    │            └── Update <last-context-hash>       │
    │                                                 │
    │    NO ──► Skip (greenfield PRD project)         │
    └─────────────────────────────────────────────────┘
```

---

## Extension Points

### Adding New Templates

1. Create template in your templates directory
2. Update `layer0-templates.md` with setup instructions
3. Add template detection keywords

### Adding New Layers

**Usually you should not.** Since item 28 the layer graph is a *parameter*: a project declares
its own `<layers>` in an `architecture.md` at its root, validated acyclic and reachable by
`check-architecture.py`. The five tiers shipped here are the **default graph**, not the graph.

To change the default itself:

1. Update `layer-definitions.md`
2. Update dependency rules
3. Note that the layer *set* is derived from what the document puts work in (item 31) and the
   set `/execute` runs is `resolve-layers.py`'s (item 66) — neither is a list in prose, and
   restoring one is what P39 and P44 were

### Customizing Review Criteria

1. Edit `review-criteria.md`
2. Add/remove critical vs warning criteria
3. Adjust pass/fail thresholds

### Adding New Skills

1. Create `SKILL.md` in `skills/{skill-name}/`
2. Define context mode (`fork` or default)
3. Specify `model:` — and **never `allowed-tools:`**, which is a command key that silently
   disables the fork (F13)
4. Add reference files under `references/` and scripts under `scripts/` if needed
5. If it decides something and exits non-zero, give it a row in
   [`schema/checks.md`](schema/checks.md) — the suite checks that table in both directions
   (item 69), so an unlisted caller or an unrowed assertion fails the build

---

## Concurrency Model

### Parallel Execution

```
Batch with 3 tasks, max_parallel=3

t=0s:   Launch T1, T2, T3 in parallel
        ├── T1: worktree-L1-001
        ├── T2: worktree-L1-002
        └── T3: worktree-L1-003

t=8s:   T3 completes → merge queue
t=10s:  T1 completes → merge queue
t=15s:  T2 completes → merge queue

Merge (sequential):
t=16s:  Merge T3 to main
t=17s:  Merge T1 to main
t=18s:  Merge T2 to main
```

### Why Sequential Merge?

Multiple tasks may modify the same files (e.g., `__init__.py`). Sequential merging prevents conflicts and ensures clean git history.

### State Synchronization

- State file updated atomically (temp file + rename)
- Each task tracks its own status
- Merge queue processed in completion order

---

## Error Handling

### Task Failure Recovery

```
Task fails verification
         │
         ▼
    ┌─────────────────────┐
    │  Attempt < 5?       │
    │                     │
    │  YES → Retry with   │
    │        feedback     │
    │                     │
    │  NO → Abandon task  │
    │       Stop layer    │
    └─────────────────────┘
```

### State Recovery

If execution is interrupted:
1. Load `execute-state.json`
2. Identify incomplete tasks
3. Resume from last known state
4. Retry failed tasks (if attempts < 5)

### Worktree Preservation

Failed task worktrees are preserved for debugging:
```bash
ls .worktrees/
# L1-001/  ← Failed task, preserved
# L1-002/  ← Completed, merged and removed
```

---

## Security Considerations

- Tasks run in isolated git worktrees
- No cross-task file access
- Verification runs in separate context (cannot be biased)
- State file is local (no network exposure)
- Git history preserved for audit
