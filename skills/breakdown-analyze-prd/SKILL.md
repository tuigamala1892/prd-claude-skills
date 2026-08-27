---
name: breakdown-analyze-prd
description: Analyze a PRD to extract features, tech stack, and implementation requirements. Called by /breakdown skill during Phase 2.
context: fork
model: claude-haiku-4-5
---

# PRD Analysis

You are analyzing a PRD (Product Requirements Document) to extract structured information for task breakdown.

## Input

**One of two passes, never the whole PRD.** The caller states which, and gives you exactly one
file's content:

| Pass | Input | You write | Sections below |
|---|---|---|---|
| **index** | `index.md` alone | `analysis.index.json` | 1, 2, 6, 7 |
| **feature** | one file from `features/` | `analysis.feature.{slug}.json` | 3, 4, 5, 8, plus the feature's own criteria |

If you are handed a whole PRD — an index *and* its feature files in one prompt — **stop and say
so** rather than analysing it. That is the caller skipping Phase 2's split, and the result is the
silent truncation this split exists to prevent (**P5**). The caller's own size check refuses
before this point; reaching you unsplit means it was not run.

**Your model is `claude-haiku-4-5`, and the split is what makes that adequate.** One feature file
is a few thousand tokens; the corpus this skill used to be handed was ~174k. Do not treat the
window as spare capacity to read more than you were given.

## Your Task

Extract and structure the information below **for the pass you were asked to do**. An index pass
that infers data models is doing a feature pass's job on a file that does not contain the
evidence, and a feature pass that re-lists the tech stack duplicates a fact the index already
owns — two fragments disagreeing about one value is the drift the merge cannot resolve.

### 1. Features

For each feature in `<features>`:
- Name
- Priority (must-have, should-have, could-have, won't-have)
- Summary
- File path to detailed spec (if exists)

### 2. Tech Stack

From `<tech-stack>`:
- **Project type**: Extract from `<type>` element (greenfield/brownfield)
- **Project path**: Extract from `<project-path>` element (brownfield only)
- All technologies with versions from `<selected>` element
- Template path: Detect from technologies (e.g., "Python + FastAPI" → `webapps/backends/python`)
- Rationale for choices from `<rationale>` element

### 3. Data Models (Inferred)

Analyze features to identify implied database models:
- Model name
- Key fields (inferred from feature descriptions)
- Relationships between models

### 4. API Endpoints (Inferred)

Analyze features to identify implied API endpoints:
- HTTP method
- Path
- Purpose
- Related feature

### 5. Frontend Components (Inferred)

Analyze features and UI layout to identify:
- Component name
- Type (page, layout, widget, form, etc.)
- Related feature

### 8. Scope and confidence — two signals, feature pass only

**Item 49. Both are predictions about *this feature*, and neither routes anything.**

- **`scope`** — `small` (1-3 files), `medium` (4-8), `large` (9+), per
  [core §5](../../schema/core.md#5-scope-and-confidence). How much code you expect this feature
  to take. Predict from the criteria and the data model, not from the prose length.
- **`confidence`** — `high`, `medium`, `low`. How sure you are of **this analysis**, not of the
  feature. Ambiguous wording, a data model you had to infer, and endpoints implied rather than
  stated all lower it.

**Neither is a judgement about whether the feature is good or ready.** `<gaps>` records specific
unknowns and `<definition>` records completeness; those are the author's and you do not touch
them. `confidence` is yours, and it says *where you were guessing* — which is the one thing
downstream cannot recover from your output.

**A low confidence is not a failure and must not be avoided.** An analyser that reports `high`
everywhere has told the gate nothing, and the gate then has to trust every inferred model
equally. If you inferred the data model because the feature declared none, say `medium` at best.

**The index pass emits neither.** `index.md` carries a summary line per feature, which is not
evidence of size and is certainly not evidence of how sure you are about a data model you have
not seen.

### 6. Dependencies

From `<dependencies>`:
- Name
- Version
- Purpose

### 7. Template Information

If tech-stack references a template:
- Template path
- What the template provides (auth, database setup, etc.)

## Output Format

**Which keys you emit depends on the pass.** The structure below is the merged shape; you write
your half of it and the caller's Step 4 combines them.

- **index pass** → `prd_meta`, `features`, `tech_stack`, `dependencies`, `template`. No
  `data_models`, no `api_endpoints`, no `components` — `index.md` does not hold the evidence for
  them, and inferring from a summary line is how a model gets invented that no feature asked for.
- **feature pass** → `data_models`, `api_endpoints`, `components`, `acceptance_criteria`, each
  carrying `"inferred_from": "<feature slug>"` so the merge can attribute every entry. Plus
  `"feature": "<slug>"`, `"scope"` and `"confidence"` at the top level, so a fragment is
  self-identifying and carries its own two signals.

Every inferred entry **must** carry `inferred_from`. The merge unions fragments and cannot ask
where an entry came from; an entry that cannot be attributed to a feature is one nobody can
later check against the feature's own text.

Return a JSON object with this structure:

```json
{
  "prd_meta": {
    "name": "Project Name",
    "slug": "project-slug",
    "status": "complete|in-progress"
  },
  "features": [
    {
      "name": "Feature Name",
      "priority": "must-have",
      "summary": "Brief description",
      "spec_file": "features/feature-slug.md"
    }
  ],
  "tech_stack": {
    "type": "greenfield",
    "project_path": null,
    "technologies": [
      {"name": "Python", "version": "3.11", "purpose": "Backend language"},
      {"name": "FastAPI", "version": "0.100+", "purpose": "API framework"}
    ],
    "template": {
      "path": "webapps/backends/python",
      "provides": ["auth", "database", "docker"],
      "detected_from": "Python + FastAPI in selected technologies"
    }
  },
  "data_models": [
    {
      "name": "Project",
      "fields": ["id", "name", "slug", "status", "content"],
      "relationships": ["has_many: Conversation"]
    }
  ],
  "api_endpoints": [
    {
      "method": "POST",
      "path": "/api/projects",
      "purpose": "Create new project",
      "feature": "Project Management"
    }
  ],
  "frontend_components": [
    {
      "name": "Dashboard",
      "type": "page",
      "feature": "Dashboard"
    }
  ],
  "dependencies": [
    {
      "name": "anthropic",
      "version": "latest",
      "purpose": "LLM API client"
    }
  ],
  "gaps": [
    {
      "feature": "save-link",
      "id": 3,
      "kind": "dependency",
      "raised": "2026-08-18",
      "body": "Retention period for archived links is unspecified."
    }
  ],
  "feature_edges": [
    {"from": "tag-links", "to": "save-link", "kind": "data"}
  ],
  "feature_signals": [
    {"feature": "save-link", "scope": "small", "confidence": "high"},
    {"feature": "tag-links", "scope": "medium", "confidence": "medium"}
  ]
}
```

**`feature_signals` is the merged shape.** A feature pass emits `"feature"`, `"scope"` and
`"confidence"` at its own top level; the caller's Step 4 collects one row per fragment. It is a
list rather than a map for the same reason every other section here is: the merge unions
fragments and never has to decide what a duplicate key means.

### `data_models` come from `<notes><data-model>`, not from inference

**When a feature declares one, copy it. Do not infer alongside it.** The element exists so that
this pass stops guessing at entities and fields, and a data model half-read and half-invented is
worse than either — nobody can tell which half is the author's.

Infer only for features that declare no `<data-model>`, and mark those entries as inferred, as
every inferred entry already must be.

**`<notes><considerations>` is not read.** It is the catch-all, and it is unread by design rather
than by oversight. Do not mine it for entities.

### `gaps` are carried, never resolved

Copy each feature's `<gap>` entries out verbatim, adding the feature slug. **Do not judge them,
do not merge them, and above all do not answer them** — a gap that this pass quietly resolves is
an invented requirement wearing an author's authority.

`kind` decides what happens downstream and it is the author's, not yours:

| `kind` | Downstream |
|---|---|
| `specification` | blocks `defined`, and blocks execution |
| `dependency`, `decision` | blocks execution |
| `ownership`, `evidence` | warn |

**A feature with no `<gaps>` block contributes nothing here.** Absence is not a gap; it is either
a complete specification or one whose author has not looked. Neither is yours to declare.

### `feature_edges` come from `<depends-on>`, and only from there

One entry per `<depends-on slug= kind=>` element. **A markdown link between features is not an
edge** — that ambiguity is the whole reason the element exists, and re-deriving edges from links
would put the guess back.

`plan-layers` orders from these. This pass records them and does not order.

## Template Detection

Detect the template from `<tech-stack><selected>` text using these mappings:

| Tech Stack Keywords | Template Path |
|---------------------|---------------|
| Python, FastAPI | `webapps/backends/python` |
| Go, Chi | `webapps/backends/go` |
| TanStack, TanStack Start | `webapps/backends/tanstack` |

If template is explicitly mentioned in the PRD (e.g., "from webapp template"), use that.
If no match found, set `template.path` to `null` and note in `detected_from`.

## Analysis Guidelines

1. **Be thorough**: Capture all features, not just the obvious ones
2. **Infer carefully**: Data models and APIs should be reasonable inferences, not guesses
3. **Use PRD language**: Match names and terminology from the PRD
4. **Note uncertainties**: If something is unclear, say so in the fragment. Where the *author*
   already marked it, carry their `<gap>` rather than restating it in your own words — one
   uncertainty should not arrive downstream twice under two descriptions
5. **Brownfield**: If `<type>brownfield</type>`, expect `<project-path>` to be present

## Example Inference

Given feature:
```xml
<feature priority="must-have">
  <name>Project Management</name>
  <summary>Create, switch, and list PRD projects with status visibility</summary>
</feature>
```

Infer:
- Data model: `Project` with fields (id, name, status, created_at)
- API endpoints: GET /projects, POST /projects, GET /projects/:id, PUT /projects/:id
- Frontend: ProjectList component, ProjectCard component

## Do NOT

- Make up features not in the PRD
- Guess at specific implementation details
- **Invent architecture.** Do *apply* what `architecture.md` states — see below. The distinction
  matters: this line used to read *"include your own opinions about architecture"*, which
  correctly forbade invention and also forbade obeying a rule the project had written down.
  There was nowhere for such a rule to come from until item 25, so the two were the same
  instruction; now they are not.
- Truncate or summarize features

## `architecture.md`, when the caller hands you one

The caller runs `check-architecture.py` in its Phase 1 and passes you the file's content when a
valid one exists. It is the project's **prescriptive** artefact — what must be true — and it
outranks anything you would otherwise infer.

**On the index pass**, record it into `analysis.index.json` under `architecture`:

```json
"architecture": {
  "declared": true,
  "layers": [{"id": "1", "name": "contracts", "depends_on": []}],
  "testing": {"default": "tdd", "runner": "pytest"},
  "task_limits": {"default": 3},
  "registries": {"event-registry": [ ... ], "api-registry": [ ... ]},
  "principles": [{"id": "P-001", "text": "..."}]
}
```

Copy it; do not paraphrase it. `"declared": false` with nothing else when no file was given.

**A registry is a data model at project scope**, so read one exactly as you read a feature's
`<notes><data-model>`: an entry that already exists is a fact, not an inference. When a feature
implies an endpoint the `<api-registry>` already records, emit the registry's shape rather than
your own, and mark it `"source": "registry"` instead of `"inferred_from"`. The same holds for
every other registry the file declares — the set is open, and a `<command-registry>` or
`<event-registry>` constrains a CLI or an event-driven project exactly as an API registry
constrains a REST one.

**This is the one thing that reduces inference rather than adding to it.** P19's charge is that
this skill is *instructed* to infer while the toolchain forbids marking the inference. Every
entry answered from a registry is one fewer place that applies.

Return the complete JSON analysis.
