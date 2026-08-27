---
name: crd-impact-analysis
description: Analyze the impact of a proposed change on an existing codebase. Identifies affected files, features, and potential breaking changes.
context: fork
agent: crd-impact-analyzer
model: claude-haiku-4-5
---

# Impact Analysis Skill

You analyze how a proposed change will affect an existing codebase using PROJECT.md context.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--project <path>` | Yes | Path to project root |
| `--type <type>` | Yes | Change type: `feature-add`, `feature-modify`, `feature-remove`, `refactor` |
| `--description "<text>"` | Yes | Description of the proposed change |

## Analysis Process

### Step 1: Load Context

Read PROJECT.md and parse:
- `<features>` - Map of existing features
- **Any `<*-registry>` the project declares.** `<api-registry>` and `<schema-registry>` are the
  two `PROJECT.md` has always carried; a project may also declare `<event-registry>`,
  `<command-registry>`, `<service-registry>` or `<screen-registry>` (item 25). Read whichever
  are present — the set is open because API-plus-schema is REST plus relational, and that is the
  wrong pair for most architectures.

**Refuse clearly when the registry you are about to read is absent.** `check-project-md.py`
requires *at least one* registry rather than a particular pair, so it will not have stopped a
project that has none of the kind you need. Say which registry is missing and what that means
for the analysis; do not report an empty impact as though you had looked and found nothing.

### Step 2: Parse Change Description

Extract keywords and concepts from the description:

```
"Add dark mode toggle to settings modal that persists preference"

Keywords: dark mode, toggle, settings, modal, persist, preference
Components: SettingsModal, settings API, user preferences
```

### Step 3: Match to Existing Context

Search PROJECT.md context for matches:

**Feature matching:**
```xml
<feature id="settings">
  <name>User Settings</name>
  <files>src/api/settings.py, src/components/SettingsModal.tsx</files>
</feature>
```
→ Match! "settings" appears in description

**API matching:**
```xml
<endpoint method="PUT" path="/api/settings">
  <request>{ settings: object }</request>
</endpoint>
```
→ Match! Settings API will likely be used

**Schema matching:**
```xml
<model name="User">
  <field name="settings" type="jsonb"/>
</model>
```
→ Match! User.settings will store preference

### Step 4: Identify Affected Files

Based on matches, list files:

**Files to Modify:**
- Files from matched features
- Files that import matched components

**Files to Create:**
- New components for new functionality
- New hooks/utilities
- New test files

Use grep to find additional dependencies:
```bash
grep -r "import.*SettingsModal" {project_path}/src --include="*.tsx" -l
grep -r "/api/settings" {project_path}/src --include="*.ts" -l
```

### Step 5: Assess Breaking Changes

For each affected area, check for:

**API breaking changes:**
- Does the change require new required fields?
- Does the change alter response shape?
- Does the change require authentication changes?

**Schema breaking changes:**
- Does the change require new columns?
- Does the change alter existing column types?
- Does the change require data migration?

**Interface breaking changes:**
- Does the change alter component props?
- Does the change alter function signatures?
- Does the change remove exports?

### Step 6: Estimate Scope

| Scope | Criteria |
|-------|----------|
| `small` | 1-3 files, no breaking changes, single component |
| `medium` | 4-8 files, minor API changes, multiple components |
| `large` | 9+ files, schema changes, cross-cutting concerns |

### Step 7: Assess Confidence

| Confidence | When |
|------------|------|
| `high` | Change maps clearly to existing features, all files identified |
| `medium` | Some new patterns needed, not all code cataloged |
| `low` | Novel functionality, incomplete context, cross-cutting |

### Step 8: Generate Output

Return structured impact analysis:

```xml
<impact-analysis>
  <affected-files>
    <file action="modify">src/components/SettingsModal.tsx</file>
    <file action="modify">src/api/settings.py</file>
    <file action="create">src/hooks/useTheme.ts</file>
    <file action="modify">src/styles/globals.css</file>
  </affected-files>

  <affected-features>
    <feature id="settings">Add theme toggle to Appearance section</feature>
  </affected-features>

  <affected-contracts>
    <contract kind="api"     ref="PUT /api/settings">Theme field added to settings object</contract>
    <contract kind="schema"  ref="User">No change -- uses the existing JSONB settings column</contract>
    <contract kind="event"   ref="OrderPlaced@v2">New optional field; consumers unaffected</contract>
    <contract kind="command" ref="deploy --dry-run">New flag</contract>
  </affected-contracts>

**`kind` matches the registry the contract came from**, so the enum extends when the registry set
does rather than being a second list to keep in step. `api` and `schema` for the two registries
`PROJECT.md` has always had; `event`, `command`, `service` and `screen` for the four item 25
opened up.

**This replaces `<affected-apis>` and `<affected-schemas>`.** Opening the registry set without
this would be half a change, and the half that shows: impact analysis could *read* an event or a
command registry and would have had nowhere to report the impact.

**`<affected-apis>` is still accepted on read** — every CRD written before this exists — and is
equivalent to `<affected-contracts>` holding only `kind="api"` entries. Item 41's migration
rewrites them.

  <breaking-changes>none</breaking-changes>

  <new-dependencies>
    <dependency name="@radix-ui/react-switch" version="^1.0.0" purpose="Accessible toggle"/>
  </new-dependencies>

  <scope>small</scope>
  <confidence>high</confidence>

  <notes>
    Theme preference will be stored in existing User.settings JSONB field.
    No database migration required.
  </notes>
</impact-analysis>
```

## Special Cases

### Feature Removal (`feature-remove`)

Focus on:
- Files to delete completely
- Files that reference the removed feature (need cleanup)
- Database orphan data considerations
- API endpoint removal

### Refactor

Focus on:
- All files affected by rename/restructure
- Import path updates needed
- Test file updates
- String references (logs, errors, docs)

### Unknown Feature

If change doesn't match any existing feature:
- Mark confidence as `low`
- Note that full investigation may be needed
- Suggest running `/crd-investigate --depth deep`

## Error Handling

| Situation | Action |
|-----------|--------|
| PROJECT.md not found | Return error, suggest running /crd-context |
| No matching features | Note as new feature area, expand scope |
| Ambiguous matches | List all possibilities, note medium confidence |
| Missing context | Note gaps, proceed with available info |
