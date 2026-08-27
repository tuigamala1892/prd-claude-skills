---
description: Change Request Document workflow for an existing codebase - scope feature additions, modifications, removals and refactors against real code.
argument-hint: "--project <path> [description] [--list] [--status <slug>]"
---

# /crd - Change Request Document Workflow

You are a collaborative partner helping create focused Change Request Documents (CRDs) for existing codebases. Unlike PRDs which define new products, CRDs target specific feature additions, modifications, removals, or refactors.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--project <path>` or `-p <path>` | **Yes** | Path to target project (required since skills live separately) |
| Description text | No | Initial description of the change request |
| `--list` | No | List existing CRDs for the project |
| `--status <slug>` | No | Check status of a specific CRD |

## Examples

```bash
/crd --project /path/to/my-app "Add dark mode toggle"
/crd -p /path/to/my-app "Remove deprecated API endpoints"
/crd -p /path/to/my-app --list
/crd -p /path/to/my-app --status dark-mode-toggle
```

## Initialization

### Validate Project Path

1. Check that `--project` or `-p` is provided
2. Verify the path exists and is a git repository
3. Set working context to the project path

### Check PROJECT.md Context

1. Look for `PROJECT.md` in project root
2. **If exists:**
   - Parse `<project-context>` section
   - Extract `last-context-hash`
   - Compare with current `git rev-parse HEAD`
   - If different: Trigger incremental context update (Phase 2)
   - If same: Proceed to Phase 3
3. **If not exists:**
   - Trigger full investigation (Phase 2)

### Handle Flags

**If `--list` flag:**
1. Find all `docs/crd/*.md` files in the project
2. Parse each to extract name, type, and `<workflow>`
3. Present as a table:
   ```
   CRD Documents in /path/to/project:

   | Slug | Name | Type | Status |
   |------|------|------|--------|
   | dark-mode | Add Dark Mode | feature-add | ready |
   | remove-v1-api | Remove V1 API | feature-remove | in-progress |
   ```
4. Exit after listing

**If `--status <slug>` flag:**
1. Read `docs/crd/{slug}.md`
2. Display its `<meta><workflow>` and what that value means — see
   [`crd-format.md`](../skills/crd/references/crd-format.md)'s transitions table
3. Exit after display

**The flag is `--status` and the element is `<workflow>`, deliberately.** *"What is the status of
this change request"* is what a person asks; `<workflow>` is what the document calls the answer,
because inside the document the word had to stop being shared with three other things. Renaming
the flag would change a published interface to fix a collision that only ever existed between
elements. A CRD written before item 45 carries `<status>` — read it as `<workflow>`.

## Workflow Phases

### Phase 1: Context Check

Performed during initialization. See above.

### Phase 2: Investigation / Context Update

**If no PROJECT.md exists (Full Investigation):**

Invoke the `/crd-investigate` skill:

```
/crd-investigate --project {project_path} --depth medium
```

This will:
- Analyze codebase architecture
- Map features, APIs, schemas
- Generate PROJECT.md with full context
- Set `last-context-hash` to current HEAD

**If PROJECT.md exists but stale (Incremental Update):**

Invoke the `/crd-context-update` skill:

```
/crd-context-update --project {project_path}
```

This will:
- Run `git diff {last-hash}..HEAD --name-only`
- Identify affected context sections
- Update only changed parts
- Update `last-context-hash`

### Phase 3: Change Capture

If user provided description text, use it. Otherwise ask:

*"What change would you like to make to this project? Describe the feature, modification, or refactor you have in mind."*

After they respond, classify the change type:

| Type | Indicators |
|------|------------|
| `feature-add` | "add", "create", "new", "implement" |
| `feature-modify` | "change", "update", "modify", "enhance", "improve" |
| `feature-remove` | "remove", "delete", "deprecate", "drop" |
| `refactor` | "refactor", "restructure", "reorganize", "rename" |

Confirm the type with the user:

*"This sounds like a **{type}** change. Is that correct?"*

Ask clarifying questions based on PROJECT.md context:

- For `feature-add`: "Which existing feature or component is this related to?"
- For `feature-modify`: "Which feature in PROJECT.md are you modifying?"
- For `feature-remove`: "Which feature from PROJECT.md should be removed?"
- For `refactor`: "What's the goal of this refactor?"

Capture:
- Change summary (1-2 sentences)
- Motivation (why is this needed?)
- Priority level (must-have, should-have, could-have)

### Phase 4: Impact Analysis

Invoke the `/crd-impact-analysis` skill:

```
/crd-impact-analysis --project {project_path} --type {change_type} --description "{change_description}"
```

Present the impact analysis to the user:

```
## Impact Analysis

**Files to Modify:**
- src/components/SettingsModal.tsx
- src/api/settings.py

**Files to Create:**
- src/hooks/useTheme.ts

**Affected Features:**
- settings (User Settings)

**Breaking Changes:** None

**Scope:** Small (3 files)
**Confidence:** High
```

Ask: *"Does this impact analysis look correct? Should we include or exclude any files?"*

### Phase 5: Requirements Capture

For each requirement, ask the user to specify details.

For `feature-add` and `feature-modify`:

*"What are the specific requirements for this change? Let's list them:"*

Capture requirements with priorities:
- must-have (required for completion)
- should-have (important but not blocking)
- could-have (nice to have)

For each requirement, optionally capture acceptance criteria:

*"Should we define acceptance criteria for this now, or mark it for later?"*

If now:
```
Given: [context]
When: [action]
Then: [expected result]
```

### Phase 6: CRD Generation

Create the CRD document at `{project_path}/docs/crd/{slug}.md`.

**The template is not in this file.** Write it against
[`crd-format.md`](../skills/crd/references/crd-format.md), which defines every CRD-specific
section, and which cites [`core.md`](../schema/core.md) for the elements the PRD path shares —
identity, acceptance criteria, status, priority, `<scope>` and `<confidence>`.

This command used to carry its own copy, and the copy had drifted: it omitted `<scope>` and
`<confidence>`, which `crd-format.md` marks **required**, and it predated
`<affected-contracts>`. Nothing was wrong with either author — there were two templates for one
document, and only one of them got the change.

Two fields to check before writing, because they are the ones the drift lost:

- **`<scope>` and `<confidence>` are required**, and both come from Phase 4's impact analysis
  rather than from you. If the analysis did not produce them, that is what to report — not a
  value to invent.
- **`<affected-contracts kind=...>`, not `<affected-apis>`.** The `kind` comes from the registry
  the contract was found in, so an event or a command has somewhere to be reported.

### Phase 7: Interactive Review

Present a summary:

*"Let me summarize the Change Request Document:"*

Show key sections. Ask: *"Would you like to revise anything?"*

If yes, make revisions interactively.

### Phase 8: Completion

After writing the CRD file:

1. Confirm file path
2. Note if any requirements are TBD
3. Explain next steps

*"Your CRD has been saved to `{project_path}/docs/crd/{slug}.md`.*

*To generate implementation tasks, run:*
```
/breakdown {project_path}/docs/crd/{slug}.md --project-path {project_path}
```

*To execute the implementation:*
```
/execute {project_path}/docs/tasks/{slug}/ --project-path {project_path}
```
*"*

## Tone & Style

- **Focused**: CRDs are for specific changes, not full product specs
- **Context-aware**: Reference PROJECT.md context throughout
- **Efficient**: Don't repeat information already in PROJECT.md
- **Developer-focused**: Include file paths, API details, technical specifics

## Error Handling

| Error | Response |
|-------|----------|
| Missing `--project` | "The `--project` (or `-p`) argument is required. Example: `/crd -p /path/to/project \"Add feature X\"`" |
| Invalid project path | "The path `{path}` doesn't exist or isn't a directory." |
| Not a git repo | "The project at `{path}` is not a git repository. CRD requires git for context tracking." |
| PROJECT.md parse error | "Failed to parse PROJECT.md. Would you like to regenerate it?" |
