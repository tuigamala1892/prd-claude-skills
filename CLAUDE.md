# CLAUDE.md

Instructions for Claude when working in this repository.

> **Two notes on what follows, both measured rather than assumed.**
>
> - **Layout:** `skills/`, `agents/` and `commands/` are at the repository root as a Claude
>   Code plugin, not under `.claude/`. Load with
>   `claude --plugin-dir <checkout> --add-dir <checkout>`. **Both flags, and they do
>   different jobs**: `--plugin-dir` loads the plugin, `--add-dir` makes its bundled scripts
>   readable. Without the second, `/breakdown` cannot run `resolve-output.sh`,
>   `check-references.py` or `build-manifest.py`, and stops in Phase 1 — measured 2026-08-26.
> - **Context fork works as of item 4.11.** It is described below as the key innovation,
>   and it now is one — but it did not function at all until that item landed, because
>   every skill also declared `allowed-tools`, a *command* key that stopped `context: fork`
>   taking effect. If you reintroduce that key to a skill, forking silently stops again;
>   `tests/test_toolchain.py` guards against exactly that.
>
> When a skill and the agent it names declare different models, **the skill's wins** —
> so the agent's `model:` is the one silently ignored. Measured, see finding F6.

---

## Project Overview

This repository contains Claude Code skills demonstrating an autonomous software development pipeline:

### Greenfield (New Projects)
1. **`/prd`** - Interactive PRD creation command
2. **`/breakdown`** - PRD to task conversion skill
3. **`/execute`** - Parallel task execution skill

### Brownfield (Existing Projects)
1. **`/crd`** - Change Request Document creation with context management
2. **`/crd-context`** - Standalone PROJECT.md management
3. **`/breakdown`** - CRD to task conversion (reused)
4. **`/execute`** - Parallel execution with context finalization (reused)

The key innovation demonstrated is **context fork** - skills that run in isolated contexts.

---

## Key Directories

All three live at the **repository root**, not under `.claude/` — see the note at the top.

```
schema/                       # Artefact schema owned by neither path (item 44)
├── core.md                   # The single definition of every shared element
└── prd-format.md             # What /prd writes; cites core.md

commands/                     # User-invocable commands (all three entry points)
├── prd.md                    # /prd
├── crd.md                    # /crd
└── crd-context.md            # /crd-context

skills/                       # Skills, each a directory holding SKILL.md
├── breakdown/                # PRD or CRD → tasks (orchestrator)
│   ├── references/           # layer-definitions, task-format-spec, review-criteria, layer0-templates
│   └── scripts/              # resolve-output.sh, build-manifest.py
├── breakdown-analyze-prd/    # ┐
├── breakdown-plan-layers/    # ├ breakdown sub-skills, in phase order
├── breakdown-generate-tasks/ # │
├── breakdown-review-tasks/   # ┘
├── execute/                  # Task execution (orchestrator)
│   ├── references/           # options, state-schema
│   └── scripts/              # preflight.sh, write-state.py, ledger-status.sh, check-project-md.py
├── execute-layer/            # One layer: dispatches batches, then merges
├── execute-batch/            # One batch: worktrees + task agents
├── execute-verify/           # Independent verification
├── execute-merge/            # Merges one verified task
├── crd/                      # CRD orchestration
├── crd-investigate/          # Deep codebase analysis
├── crd-context-update/       # Incremental context update
└── crd-impact-analysis/      # Change impact analysis

agents/                       # Agent definitions for the Task tool
├── task-implementer.md       # Implements one task inside its worktree
├── task-generator.md
├── task-reviewer.md
├── verification-runner.md
├── crd-investigator.md            # PROJECT.md generation
├── crd-context-updater.md         # Incremental updates
├── crd-impact-analyzer.md         # Impact analysis
└── project-context-finalizer.md   # Post-execute updates

docs/skills/                  # The only docs directory that exists
├── toolchain-assessment-and-plan.md
├── plugin-2.0-plan.md
├── sdd-comparison.md
├── resumable-execution-proposal.md
└── probes/                   # Phase 0 measurement harness

tests/                        # Regression suite; run before and after any skill change
```

---

## Skill Architecture

### Context Modes

Skills declare their context mode in SKILL.md frontmatter:

```yaml
---
name: execute-batch
context: fork              # ← Runs in isolated context
model: claude-sonnet-5
---
```

**Do not add `allowed-tools:` to a skill.** It is a *command* key; in a skill it restricts nothing
and silently disables `context: fork` (F13). `tests/test_toolchain.py` fails if any skill
declares it.

- **`context: fork`** - Isolated context, no parent visibility
- **Default** - Shares context with parent

### Skill Hierarchy

**Execute Pipeline:**
```
/execute (fork)
    └─► execute-layer (fork)
            ├─► execute-batch (fork)
            │       ├─► task-implementer (agent, one per task, in its own worktree)
            │       └─► execute-verify (fork)
            └─► execute-merge (fork)   ← sequential, one task at a time
    └─► project-context-finalizer (agent, only when PROJECT.md already exists)
```

**There is no `execute-task` skill.** The implementer is the `task-implementer` *agent*,
dispatched by `execute-batch` into a worktree the caller has already created (item 4.15). And
`execute-merge` is called by `execute-layer`, not by `execute-batch` — the merge is sequential
while batches are parallel, which is why it sits a level up.

**CRD Workflow:**
```
/crd (fork)
    ├─► /crd-investigate (fork)     ← If no PROJECT.md
    ├─► /crd-context-update (fork)  ← If PROJECT.md stale
    └─► /crd-impact-analysis (fork) ← Analyze change impact
```

### Reference Files

Skills can have reference files in `references/` subdirectory:

```
.claude/skills/breakdown/
├── SKILL.md
└── references/
    ├── layer-definitions.md
    └── task-format-spec.md
```

---

## Conventions

### Naming

- Skill files: `SKILL.md` (exactly)
- Commands: lowercase with hyphens (e.g., `prd.md`)
- Agents: lowercase with hyphens (e.g., `task-generator.md`)
- Layers: `{n}-{name}` (e.g., `2-backend`)
- Tasks: `L{layer}-{seq}-{slug}.xml` (e.g., `L2-003-project-crud.xml`)

### Task XML Format

Tasks are XML with these sections:
- `<meta>` - ID, name, layer, priority
- `<context>` - PRD excerpt, tech stack
- `<dependencies>` - Interface contracts from previous tasks
- `<objective>` - What to achieve
- `<requirements>` - Detailed specifications
- `<test-requirements>` - TDD test cases
- `<files-to-create>` - File paths (max 3)
- `<verification>` - Runnable commands
- `<exports>` - Interface contracts for downstream

### State Files

- `analysis.json` - PRD/CRD analysis output
- `layer_plan.json` - Layer organization
- `manifest.json` - Task inventory
- `execute-state.json` - Execution state
- `PROJECT.md` - Codebase context (brownfield only)

### CRD Document Format

CRDs are XML documents with these sections:
- `<meta>` - Slug, type (feature-add/modify/remove/refactor), status
- `<context>` - PROJECT.md reference, related features
- `<change-request>` - Summary, motivation
- `<impact-analysis>` - Affected files, features, APIs, schemas
- `<requirements>` - MoSCoW prioritized requirements
- `<acceptance-criteria>` - Given/When/Then test criteria

---

## Testing Documentation

When editing documentation:

1. **Verify internal links**
   ```bash
   # Check that linked files exist
   grep -r '\[.*\](.*\.md)' docs/ | while read line; do
     # Extract and verify paths
   done
   ```

2. **Validate code examples**
   - Commands match actual skill definitions
   - XML examples match task-format-spec.md

3. **Check ASCII diagrams**
   - Render correctly in terminal
   - Alignment is preserved

4. **Consistent terminology**
   - "context fork" (not "context forking")
   - "skill" (not "plugin")
   - "task" (not "job")

---

## Common Tasks

> **The three subsections below describe a documentation structure that does not exist.**
> `docs/IMPLEMENTATION_GUIDE.md`, `docs/examples/` and the other `docs/` subdirectories have
> never been created; `docs/skills/` is the only one. Treat them as intent, not as instructions
> to follow.

### Adding Documentation

1. Follow structure in `docs/IMPLEMENTATION_GUIDE.md`
2. Use ASCII diagrams for architecture
3. Include practical examples
4. Link to related concepts

### Updating Skill Documentation

When a skill changes:
1. Update corresponding doc in `docs/skills/`
2. Check if reference files need updating
3. Verify examples still work

### Adding Examples

1. Create in `docs/examples/`
2. Include complete workflow (PRD → Breakdown → Execute)
3. Show actual file contents, not placeholders
4. Document expected outcomes

---

## GitHub Pages Website

> **No `gh-pages` branch exists**, locally or on `origin` — the only branch is `main`. This
> section describes an intended site, not a live one, and nothing below it can be carried out
> as written.

This project has a documentation website on the `gh-pages` branch.

**URL:** https://YOUR_USERNAME.github.io/prd-breakdown-execute/

### Updating the Website

When documentation changes on `main`, the `gh-pages` branch should be updated:

1. **Switch to gh-pages branch:**
   ```bash
   git checkout gh-pages
   ```

2. **Update documentation pages:**
   - Files are in `_docs/` directory
   - Update corresponding pages to match `docs/` changes
   - Jekyll structure:
     - `_docs/introduction/` - Intro docs
     - `_docs/quickstart/` - Getting started
     - `_docs/skills/` - Skill reference
     - `_docs/concepts/` - Core concepts
     - `_docs/examples/` - Walkthroughs
     - `_docs/reference/` - Technical reference

3. **Test locally (optional):**
   ```bash
   bundle install
   bundle exec jekyll serve
   ```

4. **Commit and push:**
   ```bash
   git add -A
   git commit -m "Update docs to match main"
   git push origin gh-pages
   ```

5. **Switch back to main:**
   ```bash
   git checkout main
   ```

### Website Tech Stack

- **Theme:** just-the-docs (dark mode)
- **Generator:** Jekyll
- **Hosting:** GitHub Pages

---

## Important Notes

- This repo demonstrates Claude Code features
- The context fork pattern is the key innovation
- **No skill declares `allowed-tools`** — it is a command key that silently disables
  `context: fork`, and the regression suite enforces its absence (F13, item 4.11)
- State management enables resume capability
- TDD is mandatory: `<test-requirements>` is a required section in `task-format-spec.md` and a
  critical criterion in `review-criteria.md`; `execute-batch` runs the red/green cycle
- Run `tests/test_toolchain.py` before and after any change to skill frontmatter or git commands
- **Four things used to be called `status`; three were renamed at item 45.** A PRD feature's
  definition completeness is `<definition>`, a CRD's process position is `<workflow>`, and a
  `PROJECT.md` feature's build state is `built=`. The document-level `<status>` in `index.md` and
  `what-next.md` kept the word — it is the only one with a shipped reader. All three old
  spellings are **accepted on read and never written**. Core §3 is the definition.
- **Nothing hardcodes a fixture schema version.** `tests/fixture/prd/SCHEMAS.json` declares which
  is `current`; a superseded fixture is frozen and its content hash is checked.
- **Artefact templates do not live in command files.** `commands/prd.md` and `commands/crd.md`
  cite `schema/prd-format.md` and `skills/crd/references/crd-format.md`; both cite
  `schema/core.md`, which is the single definition of every element the two paths share. A
  template in a command cannot be cited by a skill, so the skill grows a copy — that is how
  three definitions of `<criterion>` came to exist and disagree. Two checks enforce it.
