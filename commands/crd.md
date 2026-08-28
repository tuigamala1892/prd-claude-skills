---
description: Change Request Document workflow for an existing codebase - scope feature additions, modifications, removals and refactors against real code.
argument-hint: "--project <path> [description] [--list] [--status <slug>] [--resume]"
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
| `--resume` | No | Continue an existing CRD instead of refusing to overwrite it |

## Examples

```bash
/crd --project /path/to/my-app "Add dark mode toggle"
/crd -p /path/to/my-app "Remove deprecated API endpoints"
/crd -p /path/to/my-app --list
/crd -p /path/to/my-app --status dark-mode-toggle
/crd -p /path/to/my-app --resume
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

**One list, not two.** Until item 46 this phase captured `<requirements>` and then, optionally,
acceptance criteria for each — two lists that nothing linked. An EARS criterion *is* a
requirement, so there is now one list with one id space, and capturing it is this phase's whole
job. Do not ask for requirements and criteria separately; you will get the same content twice
under two ids.

For `feature-add` and `feature-modify`:

*"What must the system do once this change is in? One sentence each."*

Write **one EARS sentence per criterion** — the six patterns and the rules are in
[`core.md`](../schema/core.md#2-acceptance-criteria):

```
When <trigger>, the system shall <response>.          # event-driven
While <state>, the system shall <response>.           # state-driven
If <condition>, then the system shall <response>.     # unwanted-behaviour
```

**Ask for the unwanted case explicitly.** *"What should happen when that goes wrong?"* An
interview that only asks what should happen produces criteria that are all `event-driven`, and a
feature that has said nothing about its failure modes reads as complete.

`pattern` is yours to assign here, with the person who just described the behaviour present. It
is the one attribute a migration is forbidden to guess.

**Two priorities, at two levels, and they are not the same question.**

- **`priority` on each criterion** is `P0`, `P1` or `P2` — *which parts of this change get built*.
  Ask it per criterion; an unassigned one is `P1` and you should write that in rather than leave
  it off, because *unassigned* and *deliberately P1* are indistinguishable when the attribute is
  absent. This was MoSCoW until item 47, and two vocabularies for one concept are why
  `--requirement-level` used to select nothing on this path.
- **`<priority>` in `<meta>`** is MoSCoW — *whether this change request is in scope at all*.
  One per document. Ask it once: *"Against everything else waiting, is this a must, a should or a
  could?"* It is what `--list` shows as a tier and what `/breakdown --priority` filters on.

**Whatever the interview did not settle becomes a `<gap>`, not an absence.**

*"Anything here we can't pin down yet?"*

A deferred criterion is a `<gap kind="specification">`, an undecided question is
`kind="decision"`, and something waiting on other work is `kind="dependency"`. Core
[§6](../schema/core.md#6-gaps--what-a-document-knows-it-is-missing) has all five kinds and says
which block and which warn.

**This is not a licence to stop asking.** The interview is the best resolution mechanism this
toolchain has, because a person is answering. A gap is for what it *failed* to resolve. But
before item 48 the CRD path had nowhere to put an unresolved point at all, so *"we'll define that
later"* left no trace and reached `/breakdown` as a task with nothing to build.

A `specification` gap bars `<workflow>ready</workflow>`. If one is open, the CRD is `draft`.

### Phase 6: CRD Generation

**Check what you are about to overwrite, before writing anything.**

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-writable.py {project_path}/docs/crd/{slug}.md
```

- **Exit 0** — nothing would be lost. Write.
- **Exit 1** — `REFUSED`. **Stop.** Show the user what is about to be replaced, then either take
  a different slug or, once they confirm this is the CRD they meant, re-run with `--resume`.

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-writable.py {project_path}/docs/crd/{slug}.md --resume
```

**This command was documented as stateless and wrote the file with no check at all.** That is F3,
which cost an interview on the PRD path before it was fixed; this path had the identical hole and
had simply not been caught by it yet (item 48). The script is the PRD guard generalised to take a
file — one guard, because the problem was never PRD-specific.

Never pass `--resume` to get past a refusal you did not expect.

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
- **`<meta><priority>` is required and is MoSCoW**; every `<criterion priority=>` is `P0|P1|P2`.
  A MoSCoW value on a criterion is the pre-item-47 shape and must not be written.
- **There is no `<requirements>` element.** If Phase 5 produced one, it produced the old shape.

### Phase 7: Interactive Review

Present a summary:

*"Let me summarize the Change Request Document:"*

Show key sections. Ask: *"Would you like to revise anything?"*

If yes, make revisions interactively.

### Phase 8: Completion

After writing the CRD file:

1. Confirm file path
2. **Name every open `<gap>`, by id and kind** — not "some requirements are TBD". A gap reported
   vaguely is one nobody goes back to, and `specification` gaps are the reason the document is
   still `draft`
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
