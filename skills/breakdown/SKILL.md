---
name: breakdown
description: Break down a PRD or CRD into self-contained implementation tasks for LLM execution. Use when you have a PRD/CRD file and want to generate executable task files for autonomous implementation.
context: fork
model: claude-opus-5
---

# /breakdown - PRD/CRD Task Breakdown

You are orchestrating the breakdown of a PRD (Product Requirements Document) or CRD (Change Request Document) into implementation tasks optimized for autonomous LLM execution.

## Arguments

- `<input-path>`: Path to PRD index.md or CRD document (required)
- `--layer <N>`: Only generate tasks for specific layer (optional, 0-4)
- `--review-only`: Only run review pass on existing tasks (optional)
- `--output-dir <path>`: Target directory for greenfield projects (overrides default)
- `--project-path <path>`: Existing project path for brownfield/CRD (overrides PRD value)
- `--auto-setup`: Automatically execute Layer 0 tasks after generation (greenfield only)
- `--requirement-level <P0|P1|P2>`: Only build criteria at or above this level (default `P2`)

### `--requirement-level` — which criteria, not which features

Two filters, two levels, and they compose in one direction only:

| Filter | Selects | Reads | Vocabulary |
|---|---|---|---|
| `--priority` (item 14, not yet built) | which **whole items** are in scope | PRD: `priority=` in `index.md` · CRD: `<meta><priority>` | MoSCoW |
| `--requirement-level` | which **criteria** within them are built | `priority=` on each `<criterion>`, both paths | `P0` · `P1` · `P2` |

**Both columns now have something to read on both paths.** Until item 47 a CRD carried MoSCoW at
the *requirement* level and nothing at the document level, so `--requirement-level` selected
nothing here and `--priority` had no field to threshold against. The vocabularies swapped levels:
MoSCoW moved up to `<meta><priority>`, and the criteria took `P0|P1|P2` — one vocabulary per
level, on both paths.

**Applied second, always.** `--priority` chooses the features or the change request;
`--requirement-level` then chooses inside them. Running it the other way round would filter criteria out of features that were about
to be dropped whole, which changes nothing and costs a pass.

**Default `P2` — everything.** No existing invocation changes behaviour, which is the point of
choosing the permissive end as the default.

**A criterion with no `priority` counts as `P1`.** See [core §4](../../schema/core.md#4-priority):
the value is written into the file by migration rather than left implicit, so an unfiltered corpus
and a partly-assigned one are distinguishable. Where you meet one that is genuinely absent, treat
it as `P1` and **say how many** — a run that silently promoted 400 unassigned criteria into scope
looks identical to one that had them assigned.

**Report what the filter excluded, by feature.** *"3 features, 41 criteria, 12 excluded below
P1"* is the line. A filter whose effect is invisible is a filter nobody can check, and item 30's
coverage question — *does every in-scope feature have a task* — cannot be answered against a
scope nobody stated.

## Input Format Detection

The skill automatically detects whether the input is a PRD or CRD:

| Root Element | Format | Defined in |
|--------------|--------|-------------|
| `<prd>` | PRD | [`prd-format.md`](../../schema/prd-format.md) |
| `<crd>` | CRD | [`crd-format.md`](../crd/references/crd-format.md) |

**The two formats differ; the elements this skill actually consumes do not.** Acceptance
criteria, identity, status and priority are defined once in
[`core.md`](../../schema/core.md) and are the same on both paths — which is why detection
selects a *reader*, not a second set of rules. Where this skill treats a PRD and a CRD
differently below, that difference is in what the document is *about*, never in what a
`<criterion>` means.

**CRD handling:**
- CRDs are always brownfield (no Layer 0)
- CRDs require `--project-path` or a project with PROJECT.md
- CRDs use `<impact-analysis>` to scope task generation
- CRDs typically produce fewer tasks (focused changes)

## Output Location

Two different directories, and they are resolved by a script rather than assembled by hand:

| | What | Default |
|---|---|---|
| `{tasks_dir}` | Where task XML is written | `docs/tasks/<prd-slug>/` |
| `{target_dir}` | Where code will be built (`--output-dir` / `--project-path`) | none — must be given |

For greenfield with `--output-dir`:
- Layer 0 tasks reference `{target_dir}` as target
- Other layer tasks are still saved to `{tasks_dir}`

**Both are absolute from Phase 1 onward, and nothing downstream may use a relative path.**
`docs/tasks/<slug>` means nothing without saying what it is relative to, and every skill below
this one forks — so it does *not* share this working directory. Finding F4 is what that costs:
a whole run's output landed in `skills/breakdown-generate-tasks/output/`, because the sub-skill
resolved the relative path it was handed against its own directory. The caller was never told.

## Workflow

Execute these phases in order:

### Phase 1: Validate Input

1. Read the input file at the provided path
2. Detect format by checking root element (`<prd>` or `<crd>`)
3. Verify valid XML structure
4. Extract the slug from `<meta><slug>` tag
5. **Resolve both output paths, before creating anything:**

   ```bash
   sh {skill_dir}/scripts/resolve-output.sh docs/tasks/{slug} [{--output-dir or --project-path value}]
   ```

   `{skill_dir}` is the base directory given at the top of this skill — the one ending in
   `skills/breakdown`.

   - **Exit 0**: stdout is `tasks_dir=<absolute>` and, when a target was given,
     `target_dir=<absolute>`. Use those two values everywhere below — in your own file writes,
     in the paths you pass to sub-skills, and in the paths you bake into task XML. Never
     re-derive either by joining strings.
   - **Non-zero**: stderr begins `REFUSED:`. **Stop.** Report it verbatim and create nothing —
     no directory, no analysis, no tasks. In particular do not "helpfully" convert the path
     yourself and carry on; the refusal exists because the right answer was not knowable.

   What it refuses: a relative `--output-dir`/`--project-path`, and either path resolving
   inside a Claude Code plugin. The second is F4 directly, and is pointless as well as wrong —
   `/execute` refuses a plugin as a target, so tasks generated there could never be run.

6. **Echo both resolved paths** in your first line of output, before writing anything:

   ```
   Tasks:  /abs/path/docs/tasks/link-shelf
   Target: /abs/path/link-shelf-app
   ```

   A wrong target is then visible immediately, rather than found later in someone else's
   directory.

7. Create `{tasks_dir}`
8. If it exists, check for existing `.done` markers to resume
9. **Read the project's own rules first, and refuse a rule file that cannot be obeyed:**

   ```bash
   python {skill_dir}/scripts/check-architecture.py {target_dir}
   ```

   `architecture.md` is the project's prescriptive artefact — the layer graph, the test policy,
   the task file limit, the banned patterns and the scaffold. It lives at the project root
   beside `PROJECT.md`, it is **optional**, and it is read here rather than later because the
   two steps below both consult it.

   - **Exit 0, `no architecture.md`**: the common case, and not a problem. The shipped defaults
     apply — `references/layer-definitions.md` for the graph, TDD, three files per task —
     and everything proceeds exactly as it did before this file existed.
   - **Exit 0, `architecture.md valid`**: **write the parsed form down, and pass that on:**

     ```bash
     python {skill_dir}/scripts/check-architecture.py {target_dir} --json > {tasks_dir}/architecture.json
     ```

     Every later phase reads `{tasks_dir}/architecture.json`, never `architecture.md` itself.
     The graph has already been validated — acyclic, ids unique, every `depends-on` known — and
     a second reader re-parsing the markdown by eye would be a second parser that can disagree
     with the one that did the checking. `--json` is that parser's own output.

     Write nothing when the file is absent: a missing `architecture.json` is how every later
     phase knows to take the defaults, and an empty one is a different claim.
   - **Exit 1**: `REFUSED:` names every rule it could not read, with the element and the reason.
     **Stop and report it verbatim.** Create nothing.

   **Absent is fine; present-and-broken must stop the run.** A rule file that is silently
   ignored is worse than no rule file at all, because the rule is not in force and the operator
   believes it is — P16's failure mode, one level up from prose.

   For CRD input the project root is `{project_path}`. The file belongs to the codebase, not to
   the document that changes it.

10. **Read the repository structure, and refuse `multi-repo` here rather than at merge time:**

   ```bash
   python {skill_dir}/scripts/check-repo-structure.py {input_file} --project-root {target_dir}
   ```

   - **Exit 0**: stdout is `repo_structure=single|monorepo` and names where the value came from.
     Carry the value: `monorepo` is what lets a task declare `<meta><cwd>` (item 54), and
     `single` means tasks run at the repository root as they always have.
   - **Exit 1**: `REFUSED:`. **Stop and report it verbatim.** Create nothing.
   - A `DISAGREE:` line means `architecture.md` and the input document state different layouts.
     The project file wins — layout is a property of the codebase, not of a document about it —
     and the run continues. Report the line; the stale copy is for a human to delete.

   The assumption is already enforced — `create-worktree.sh` refuses a subdirectory — but it
   fires during batch execution, several phases after the layout was knowable. A repo-per-service
   project currently gets a layer plan, a manifest and a full task set before anything objects,
   then fails with a message about worktrees that does not name the cause (**P36**).

11. **Validate the references that leave the PRD, before Phase 2 reads a word of it:**

   ```bash
   python {skill_dir}/scripts/check-references.py {prd_dir} [--adr-dir DIR] [--questions FILE]
   ```

   `{prd_dir}` is the directory holding `index.md` and `features/` — the input file's directory,
   not the input file.

   - **Exit 0**: continue. Any `STALE` lines are reported to the operator and do not stop the
     run — a superseded decision record still exists, and a feature citing one is a judgement
     call rather than a defect.
   - **Exit 1**: `DANGLING` lines name a citation that resolves to nothing. **Report them and
     stop.** A feature whose scope was settled by a record that no longer exists will be broken
     down without it, and the task will look complete.

   `ADR-NNN`, `OQ-NNN`, `**Drives:**` links and `P-NNN` principle citations are all resolved.
   The last of those is why step 9 runs first: a principle resolves against
   `architecture.md`'s `<principles>` section, and the script discovers that file by walking up
   from the PRD. Pass `--architecture` when it lives somewhere the walk will not reach.

   Skip only when the PRD cites nothing: the script exits 0 on a PRD with no citations, so
   running it unconditionally costs nothing and there is no condition to evaluate.

**For CRD input:**
- Require `--project-path` argument (CRDs always target existing projects)
- Verify PROJECT.md exists at `{project-path}/PROJECT.md`
- Load PROJECT.md context for use in task generation

### Phase 2: Analyze Input

If analysis.json exists, skip this phase.

**For PRD — one index pass, then one pass per feature. Never the whole PRD in one prompt.**

This used to say *"invoke `breakdown-analyze-prd` with the full PRD content"*. On a real corpus
that is ~174k tokens in a single prompt to a 200k-window model, leaving no room for the
structured extraction it was asked to produce — and with no size check, the failure mode was a
silently truncated analysis that everything downstream is then built from (**P5**).

**Step 1 — measure before sending anything:**

```bash
python {skill_dir}/scripts/check-prd-size.py {prd_dir}
```

- **Exit 0**: every prompt fits. Continue.
- **Exit 1**: `REFUSED:` names the file and its size. **Stop and report it.** Do not send it
  anyway and do not summarise the file to make it fit — there is no truncation that leaves the
  analysis correct.

**Step 2 — the index pass.** Invoke `breakdown-analyze-prd` with **`index.md` alone**, asking for:
- All features with priorities, and the `file=` path of each feature's spec
- Tech stack with versions, project type, project path (brownfield only)
- External dependencies
- Template path if specified

It writes `{tasks_dir}/analysis.index.json`.

**Step 3 — one pass per feature.** For each feature named in the index, invoke
`breakdown-analyze-prd` again with **that one feature file**, asking for what only that feature
implies:
- Data models, API endpoints and frontend components implied by this feature
- The feature's own acceptance criteria, carried rather than summarised

Each writes `{tasks_dir}/analysis.feature.{slug}.json`. A feature file is read **once**, by the
pass that owns it, and never as part of a larger blob.

**Step 4 — merge.** Combine the index fragment and every feature fragment into
`{tasks_dir}/analysis.json`, with the same shape Phase 3 already expects. Union the inferred
models, endpoints and components, keeping every `inferred_from` so a later reader can tell which
feature produced an entry — when two features infer the same model, keep both attributions.

**The merge is mostly arithmetic, and the exception is the point.** A feature pass sees one
feature file and cannot see the index; the index pass sees no feature. So the merge is the only
place that holds both, and some contradictions are visible **nowhere else**:

- a feature pass infers frontend components for a project whose index says backend-only
- the index pass maps a keyword to a template path that the PRD's own rationale disclaims
- a dependency every task's verification needs that no feature thought to declare

Reconcile those, and **record each one in `merge_notes`** — an array of
`{kind, field, detail}` where `kind` is `unioned`, `reconciled`, `dropped` or `added`. Say what
the fragments claimed and why the merged file differs.

What the merge may **not** do is re-read a feature file to infer something new. Judgement about
what a feature *means* belongs to the pass that had it in front of it; judgement about what two
fragments say *together* belongs here, and has to leave a trace either way.

**Why this is worth four steps.** Only Step 1 can refuse, and only Steps 2 and 3 ever see a
prompt whose size is known in advance. `generate-tasks` later receives only the feature files
for its batch, for the same reason.

**For CRD:**
Extract directly from CRD structure:
- **Criteria from `<acceptance-criteria>` — one list, which is both the requirements and the
  tests.** There is no `<requirements>` section; item 46 retired it, because an EARS criterion
  *is* a requirement. A CRD written before that carries one, and it is **read** as criteria with
  no `pattern` rather than refused — the same policy the other pre-migration shapes get
- Document tier from `<meta><priority>` — MoSCoW, what `--priority` thresholds against
- Open gaps from `<gaps>`, reported with the PRD path's, below
- Affected files from `<impact-analysis><affected-files>`
- Affected features from `<impact-analysis><affected-features>`
- Tech stack from PROJECT.md context
- Related existing features from `<context><related-features>`

The CRD already contains impact analysis, so less inference is needed.

Save the analysis to `{tasks_dir}/analysis.json`

**Then report what the documents said they did not know**, before any task is generated:

```
gaps: 4 blocking (2 decision, 1 dependency, 1 specification), 2 warnings (1 ownership, 1 evidence)
  save-link#3     decision      raised 2026-08-18   Whether archived links keep their tags
  ...
architecturally significant: 2 features (cross-cutting, external-dependency)
```

**Blocking and warning are the author's call, not yours** — [core
§6](../../schema/core.md#6-gaps--what-a-document-knows-it-is-missing) maps `kind` to which is
which. `specification`, `dependency` and `decision` stop execution; `ownership` and `evidence`
warn. Generation continues either way: a gap is a fact about the source document, and refusing to
generate would leave the person with neither tasks nor a list.

**Never resolve a gap.** A gap this phase quietly answers becomes a requirement nobody wrote, and
it arrives at the implementer with the same authority as one somebody did.

Significant features are reported because a design step is affordable only over the handful that
warrant one. `check-references.py` says which of them no decision record names — a warning, never
a refusal, because the flag is a judgement and its absence proves nothing.

### Phase 3: Plan Layers

If layer_plan.json exists, skip this phase.

**Both paths, one planner.** Invoke the `breakdown-plan-layers` skill with the analysis JSON
**and, when it exists, `{tasks_dir}/architecture.json`** — the validated form of the project's
declared layer graph, written in Phase 1.

The two paths differ only in what the evidence is, not in how the question is answered: a PRD
supplies it as inferred models, endpoints and components; a CRD supplies it as
`<affected-schemas>`, `<affected-apis>` and `<affected-files>`. Both are answering *which tiers
does this work touch?*

**When `architecture.json` declares `layer_blocks`, that graph replaces the default tiers
entirely.** Not merged with them: a project that declared its own tiers did not ask for
`0-setup` or `4-integration`, and grafting them on is how a project acquires layers it
explicitly rejected. Pass the file and say which case applies.


**A tier with no work in it is not a tier.** Ask, of each candidate layer, whether this
document actually puts work there — and drop the ones it does not. The layer set is **derived**,
on both paths:

| Layer | Included when | Evidence |
|---|---|---|
| `0-setup` | greenfield **and** a scaffold is named | `<scaffold>`, or Phase 2's template |
| `1-foundation` | there are data models, migrations or shared types | analysis `data_models`; CRD `<contract kind="schema">` |
| `2-backend` | there are endpoints, services or background work | analysis `api_endpoints`; CRD `<contract kind="api|event|command">` |
| `3-frontend` | there are components, screens or routes | analysis `frontend_components`; CRD frontend paths in `<affected-files>` |
| `4-integration` | **more than one other tier is present**, or a requirement is explicitly cross-cutting | the count above |

**The PRD path used to take all five unconditionally**, so a PRD with no frontend got a frontend
layer and a batch that generated nothing worth having. The CRD path already asked the question
that matters — *does this change span dependency tiers?* — and answered it from what the change
touches. This is that derivation, extended rather than invented (**P33**).

**Layer 4 is no longer automatic, and that line was the expensive one.** *"Always include Layer 4
for wiring changes together"* made the minimum possible plan two layers, two batches and two
rounds of generate → review → retry, for a change that might be one edit to one file. **There is
nothing to integrate when only one tier moved.**

**When `architecture.json` declares a graph, derive over *that* graph**, not over the five above:
a declared layer with no work in it is dropped on the same rule. The graph says what tiers
*exist*; the document says which ones this work *touches*.

#### The degenerate case: no plan at all

**When the derivation yields one layer holding one task, there is no plan to make. Run the
task.** Skip layering, skip batching, skip the layer directory; generate the single task and say
so. This is the small path P21 asks for, arriving as a consequence of asking the right question
rather than as a `--small` flag with a file-count threshold.

**Two decisions, and they are not the same one.** *Skip layering* when the work spans one tier.
*Skip batching* when a layer holds few enough tasks. Twenty endpoints in one tier is a large
change that needs no layering and still wants batching — a threshold on file count would have got
that backwards, which is why there is no threshold here to set.

#### Report the routing decision

An operator who expected four tasks and got one must be told why:

```
Layers: 2-backend only (1 task)
  Dropped: 1-foundation (no schema changes), 3-frontend (no components),
           4-integration (single tier -- nothing to wire)
  Single task in a single layer: running it directly, no batching.
```

**And cross-check `<scope>` rather than routing on it.** A CRD's `<scope>` is no longer an input
to this decision — *"impact analysis said `small`, breakdown produced 14 tasks"* is worth
flagging as a sign that one of the two is wrong, but the derivation above already knows more than
a band boundary does.

Save the layer plan to `{tasks_dir}/layer_plan.json`

### Phase 4: Generate Tasks (Per Layer)

**Process exactly the layers `layer_plan.json` contains — never a list written here.**
Phase 3 derived the set from what the document actually puts work in, and re-deriving it from
input type would silently restore the five unconditional tiers it just dropped (**P33**).

Brownfield has no `0-setup` because nothing scaffolds an existing project, and a PRD with no
frontend has no `3-frontend` for the same reason: the layer is absent from the plan, not skipped
here.

**If the plan holds one layer with one task**, Phase 3 already said so: generate that task, skip
the batching loop below, and do not create a `.done` marker for a layer that was never a layer.

For each layer in order:

1. **Check completion**: If `{layer}/.done` exists, skip this layer

2. **Create directory**: `{tasks_dir}/{layer}/`

3. **Batch tasks**: Split layer tasks into batches of max 5 tasks each
   - If layer has ≤5 tasks: single batch
   - If layer has 6-10 tasks: 2 batches
   - If layer has 11-15 tasks: 3 batches
   - Example: 14 tasks → batches of [5, 5, 4]

4. **For each batch, with retry loop** (max 3 attempts per batch):
   ```
   for batch in batches:
       for attempt in [1, 2, 3]:
           # Generate
           invoke breakdown-generate-tasks with:
             - Layer name
             - Task batch (subset of layer tasks)
             - PRD analysis
             - Template path (if any)
             - Output directory: {tasks_dir}/{layer}/   # absolute, from Phase 1
             - Previous review feedback (if retry)

           # Review
           invoke breakdown-review-tasks with:
             - Path to generated task files
             - Layer name

           # Handle result
           if review.verdict == "PASSED":
               break  # Move to next batch
           elif attempt < 3:
               # Extract failures for next attempt
               feedback = {
                   "attempt": attempt + 1,
                   "previous_failures": review.critical_issues
               }
           else:
               # Max retries exceeded
               Report: "Batch failed after 3 attempts. Manual intervention required."
               Report: review.critical_issues
               Exit without creating .done
   ```

5. **Mark layer complete**: After ALL batches pass, create `{layer}/.done` marker

### Phase 5: Finalize

1. **Build `manifest.json` from the task files that exist**, using the bundled script:

   ```bash
   python {skill_dir}/scripts/build-manifest.py {tasks_dir} --project-path {target_dir}
   ```

   `{skill_dir}` is the base directory given at the top of this skill — the one ending in
   `skills/breakdown`. The script enumerates the generated `.xml` files, reads each task's
   declared name, and writes `task_inventory`, `summary.total_tasks` and
   `summary.tasks_per_layer` to match. Metadata already in the manifest (PRD slug and name,
   tech stack, project type, output dir) is preserved.

   It also records two fields the manifest previously lacked:

   - **`prd.project_path`** — `/execute` documents a fallback to this when `--project-path` is
     omitted, but the field was never in the manifest spec, so the fallback could never fire
     and `--project-path` was mandatory in practice. Pass `--project-path` so it is recorded.
   - **`toolchain_version`** — read from `.claude-plugin/plugin.json`, so a generated artefact
     records which toolchain produced it.

   **Do not write the inventory from `layer_plan.json`.** The plan is what you intended to
   generate; the files are what you generated, and generation legitimately consolidates,
   splits and renames tasks as it learns the shape of the work. On the reference fixture the
   plan called for six Layer 0 tasks and generation produced four — with different names — and
   the hand-written manifest kept the plan's version. `/execute` then reported "18 of 20" for
   a run that had done everything there was to do, and the six file paths it named did not
   exist.

2. **Verify before reporting anything:**

   ```bash
   python {skill_dir}/scripts/build-manifest.py {tasks_dir} --verify
   ```

   It exits non-zero and lists the discrepancies if the manifest and the files disagree. Treat
   that as a generation failure, not a formatting nit: every downstream consumer sizes the work
   from this file.

3. Report completion summary:
   - Total tasks generated — **the number the script reports**, not the number planned
   - Tasks per layer
   - Any review failures requiring attention
   - If the count differs from `layer_plan.json`, say so and say why; a plan revised during
     generation is the plan working, not failing

## Task File Format

Each task file follows this XML structure (see `references/task-format-spec.md` for full spec):

```xml
<task>
  <meta>
    <id>L1-001</id>
    <name>Task Name</name>
    <layer>1-foundation</layer>
    <priority>1</priority>
  </meta>
  <context>...</context>
  <dependencies>...</dependencies>
  <objective>...</objective>
  <requirements>...</requirements>
  <test-requirements>...</test-requirements>
  <files-to-create>...</files-to-create>
  <verification>...</verification>
  <exports>...</exports>
</task>
```

## Critical Constraints

- **Self-contained tasks**: Each task file MUST contain ALL information needed for implementation. No external lookups.
- **Small context**: Tasks are designed for ~50k token context models (Haiku, GLM 4.5-4.7)
- **Interface contracts**: Dependencies use type signatures, not full code
- **Max 3 files per task**: Keep scope manageable
- **TDD approach**: Test requirements come before implementation
- **Explicit verification**: Every task has runnable verification commands

## Error Handling

- If PRD file not found: Report error, exit
- If PRD invalid XML: Report parsing error with details, exit
- If skill invocation fails: Report which phase failed, suggest retry
- If review fails: Do NOT mark layer complete, report specific issues

## Example Usage

### Greenfield Project
```
/breakdown docs/prd/voice-prd-generator/index.md --output-dir /path/to/new-project
```

Output:
```
Analyzing PRD: voice-prd-generator
Detected: greenfield project (Python + FastAPI template)
Target directory: /path/to/new-project
Saved analysis to: docs/tasks/voice-prd-generator/analysis.json

Planning layers...
Saved layer plan to: docs/tasks/voice-prd-generator/layer_plan.json

Generating Layer 0 (Setup)...
Batch 1/1: [L0-001, L0-002, L0-003, L0-004]
- L0-001-copy-template.xml
- L0-002-commit-template.xml
- L0-003-configure-database.xml
- L0-004-verify-setup.xml
Reviewing batch... PASSED
Created: docs/tasks/voice-prd-generator/0-setup/.done

Generating Layer 1 (Foundation)...
Batch 1/1: [L1-001, L1-002, L1-003, L1-004, L1-005]
- L1-001-project-model.xml
- L1-002-conversation-model.xml
- L1-003-message-model.xml
- L1-004-prddocument-model.xml
- L1-005-personaworkflow-model.xml
Reviewing batch... PASSED
Created: docs/tasks/voice-prd-generator/1-foundation/.done

Generating Layer 2 (Backend)...
Batch 1/3: [L2-001, L2-002, L2-003, L2-004, L2-005]
Reviewing batch... PASSED
Batch 2/3: [L2-006, L2-007, L2-008, L2-009, L2-010]
Reviewing batch... FAILED (attempt 1)
  - L2-008: Contains placeholder 'TBD' for schema
Regenerating with feedback...
Reviewing batch... PASSED (attempt 2)
Batch 3/3: [L2-011, L2-012, L2-013, L2-014]
Reviewing batch... PASSED
Created: docs/tasks/voice-prd-generator/2-backend/.done

[continues for layers 3-4...]

Breakdown complete!
- Total tasks: 28
- 0-setup: 4 tasks
- 1-foundation: 5 tasks
- 2-backend: 14 tasks
- 3-frontend: 7 tasks
- 4-integration: 4 tasks
```

### Brownfield Project (PRD)
```
/breakdown docs/prd/new-feature/index.md --project-path /existing/project
```

Output:
```
Analyzing PRD: new-feature
Detected: brownfield project
Existing project: /existing/project
Skipping Layer 0 (setup)

[continues with layers 1-4...]
```

### CRD (Change Request)
```
/breakdown docs/crd/dark-mode-toggle.md --project-path /existing/project
```

Output:
```
Analyzing CRD: dark-mode-toggle
Detected: Change Request Document
Existing project: /existing/project
Loading PROJECT.md context...

Impact Analysis:
  - Affected files: 4 (2 modify, 2 create)
  - Affected features: settings
  - Breaking changes: none

Planning layers from impact...
  - Layer 2 (backend): 1 task (API endpoint)
  - Layer 3 (frontend): 2 tasks (component, hook)
  - Layer 4 (integration): 1 task (wiring)

Generating Layer 2 (Backend)...
Batch 1/1: [L2-001]
- L2-001-theme-settings-api.xml
Reviewing batch... PASSED
Created: docs/tasks/dark-mode-toggle/2-backend/.done

Generating Layer 3 (Frontend)...
Batch 1/1: [L3-001, L3-002]
- L3-001-theme-toggle-component.xml
- L3-002-use-theme-hook.xml
Reviewing batch... PASSED
Created: docs/tasks/dark-mode-toggle/3-frontend/.done

Generating Layer 4 (Integration)...
Batch 1/1: [L4-001]
- L4-001-wire-theme-toggle.xml
Reviewing batch... PASSED
Created: docs/tasks/dark-mode-toggle/4-integration/.done

Breakdown complete!
- Total tasks: 4
- 2-backend: 1 task
- 3-frontend: 2 tasks
- 4-integration: 1 task

To execute:
  /execute docs/tasks/dark-mode-toggle/ --project-path /existing/project
```
