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
| **feature** | one file from `features/` | `analysis.feature.{slug}.json` | 3, 4, 5, plus the feature's own criteria |

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
  `"feature": "<slug>"` at the top level, so a fragment is self-identifying.

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
  ]
}
```

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
4. **Note uncertainties**: If something is unclear, include it with a note
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
- Include your own opinions about architecture
- Truncate or summarize features

Return the complete JSON analysis.
