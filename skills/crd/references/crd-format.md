# CRD (Change Request Document) Format Specification

CRD documents capture focused change requests for existing codebases. They are designed to be processed by `/breakdown` for task generation.

**Elements shared with the PRD path are defined in
[`core.md`](../../../schema/core.md), not here** — identity, acceptance criteria, the status
vocabularies, priority, `<scope>` and `<confidence>`. This file shows them in place and states
what is CRD-specific about their use; it does not redefine them. Three documents held three
copies of the criterion shape before the core existed, and they had already drifted.

## File Location

`{project_root}/docs/crd/{slug}.md`

## Document Structure

```xml
<crd>
  <meta>...</meta>
  <context>...</context>
  <change-request>...</change-request>
  <impact-analysis>...</impact-analysis>
  <requirements>...</requirements>
  <acceptance-criteria>...</acceptance-criteria>
</crd>
```

## Sections

### Meta Section

```xml
<meta>
  <name>Add Dark Mode Toggle</name>
  <slug>dark-mode-toggle</slug>
  <type>feature-add</type>
  <created>2026-01-12</created>
  <workflow>ready</workflow>
</meta>
```

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | String | Human-readable change name |
| `slug` | Yes | String | URL-safe identifier (lowercase, hyphens) |
| `type` | Yes | `feature-add`, `feature-modify`, `feature-remove`, `refactor` | Change type |
| `created` | Yes | YYYY-MM-DD | Creation date |
| `workflow` | Yes | see [core §3](../../../schema/core.md#3-status) | Where this change is in the process |

**`<slug>` and `<workflow>` are core elements.** The slug is core §1 — stable, global, and the
filename under `docs/crd/`. `<workflow>` is core §3's *third* row: it records where the change is
in the **process**. Its values and their transitions are at the foot of this document.

**It was `<status>` until item 45.** The word was shared with a PRD feature's tag, which records
something else entirely — how completely a feature is *specified* — and a script reading the
right name from the wrong file got a plausible answer rather than an error. A CRD that still says
`<status>` is read as `<workflow>` and rewritten by item 41's migration, never refused.

### Context Section

```xml
<context>
  <project-ref>PROJECT.md</project-ref>
  <prd-ref>docs/prd/my-project/index.md</prd-ref>
  <related-features>
    <feature-ref id="settings">User Settings (will be modified)</feature-ref>
    <feature-ref id="auth">Authentication (depends on)</feature-ref>
  </related-features>
</context>
```

| Element | Required | Description |
|---------|----------|-------------|
| `project-ref` | Yes | Path to PROJECT.md |
| `prd-ref` | No | Path to PRD if project was created with /prd |
| `related-features` | Yes | List of features affected by this change |
| `feature-ref` | - | Reference to feature in PROJECT.md with relationship note |

### Change Request Section

```xml
<change-request>
  <summary>Add a dark mode toggle to the settings modal that persists user preference</summary>
  <motivation>Users have requested dark mode support for better accessibility and reduced eye strain during evening use</motivation>
</change-request>
```

| Element | Required | Description |
|---------|----------|-------------|
| `summary` | Yes | 1-2 sentence description of the change |
| `motivation` | Yes | Why this change is needed |

### Impact Analysis Section

```xml
<impact-analysis>
  <affected-files>
    <file action="modify">src/components/SettingsModal.tsx</file>
    <file action="modify">src/api/settings.py</file>
    <file action="create">src/hooks/useTheme.ts</file>
    <file action="create">src/styles/themes.css</file>
    <file action="delete">src/styles/deprecated.css</file>
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

  <breaking-changes>none</breaking-changes>
  <!-- Or: -->
  <!--
  <breaking-changes>
    <change severity="high" mitigation="Version bump to v2">
      API response shape changes for /api/settings
    </change>
  </breaking-changes>
  -->

  <new-dependencies>
    <!-- Or: none -->
    <dependency name="@radix-ui/react-switch" version="^1.0.0" purpose="Accessible toggle component"/>
  </new-dependencies>

  <scope>small</scope>
  <confidence>high</confidence>
</impact-analysis>
```

| Element | Required | Description |
|---------|----------|-------------|
| `affected-files` | Yes | List of files with action (create, modify, delete) |
| `affected-features` | Yes | Features from PROJECT.md that are impacted |
| `affected-contracts` | No | Contracts that change, of any kind the project's registries declare |
| `affected-apis` | No | **Deprecated.** Accepted on read; equivalent to `affected-contracts` with `kind="api"` |
| `affected-schemas` | No | **Deprecated.** Accepted on read; equivalent to `kind="schema"` |
| `breaking-changes` | Yes | "none" or list of breaking changes with severity |
| `new-dependencies` | No | External packages to add |
| `scope` | Yes | Core [§5](../../../schema/core.md#5-scope-and-confidence) — `small` (1-3 files), `medium` (4-8), `large` (9+) |
| `confidence` | Yes | Core [§5](../../../schema/core.md#5-scope-and-confidence) — `high`, `medium`, `low` |

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


### Requirements Section

```xml
<requirements>
  <requirement id="1" priority="must-have">
    Toggle switch component in settings modal under new "Appearance" section
  </requirement>
  <requirement id="2" priority="must-have">
    Theme preference persisted to user settings via existing PUT /api/settings endpoint
  </requirement>
  <requirement id="3" priority="must-have">
    CSS custom properties (variables) for light and dark color schemes
  </requirement>
  <requirement id="4" priority="should-have">
    Respect system preference (prefers-color-scheme) on first load if no saved preference
  </requirement>
  <requirement id="5" priority="could-have">
    Smooth transition animation when switching themes
  </requirement>
</requirements>
```

| Attribute | Required | Values | Description |
|-----------|----------|--------|-------------|
| `id` | Yes | Core [§1](../../../schema/core.md#1-identity) — integer, unique within `<requirements>` | Citable requirement ID |
| `priority` | Yes | Core [§4](../../../schema/core.md#4-priority) — MoSCoW | Which requirements are in scope |

**This list is CRD-only, and it exists because Given/When/Then cannot state a requirement.** A
scenario says what happens in one case; a requirement says what the system must do. The PRD path
has no equivalent list because it has no equivalent need — it carries criteria alone.

Item 46 retires this section once item 33 lands: an EARS criterion *is* a requirement, so the
split stops being necessary and the two unlinked lists become one with one id space.

### Acceptance Criteria Section

```xml
<acceptance-criteria>
  <criterion id="1" pattern="event-driven" priority="P0">
    When the user toggles the dark mode switch on, the system shall apply the dark theme
    immediately.
  </criterion>
  <criterion id="2" pattern="state-driven" priority="P0">
    While a saved theme preference exists, the system shall apply it on every page load.
  </criterion>
  <criterion id="3" pattern="optional-feature" priority="P1">
    Where no saved preference exists, the system shall follow the operating system's dark
    mode setting.
  </criterion>
  <criterion id="4" pattern="unwanted-behaviour" priority="P1">
    If the operating system's setting changes while a saved preference exists, then the
    system shall keep the saved preference.
  </criterion>
</acceptance-criteria>
```

**Defined in [core §2](../../../schema/core.md#2-acceptance-criteria), and identical to the PRD
path's.** Same element, same attributes, same meaning — which is what lets
`breakdown-generate-tasks` read a CRD's criteria and a feature file's criteria without a branch.
The examples above are examples; the rules are in the core.

**Four criteria, four patterns, and that is the point of the example.** Given/When/Then could
express the first two and had to contort the other two, which is why the corpus it was measured
on contained no `optional-feature` criteria at all. A CRD written before item 33 carries
`<given>`/`<when>`/`<then>`; it is read as one requirement with no `pattern`, and item 41's
migration rewrites it.

**Priority on a criterion is `P0|P1|P2`, and the `<requirements>` list above is still MoSCoW.**
Two vocabularies for one concept, which is exactly what item 47 resolves by migrating the
requirement priorities and retiring the list. Until then, a CRD carries both — recorded here
rather than left to be discovered.

## Complete Example

```xml
<crd>
  <meta>
    <name>Add Dark Mode Toggle</name>
    <slug>dark-mode-toggle</slug>
    <type>feature-add</type>
    <created>2026-01-12</created>
    <workflow>ready</workflow>
  </meta>

  <context>
    <project-ref>PROJECT.md</project-ref>
    <related-features>
      <feature-ref id="settings">User Settings (will be modified)</feature-ref>
    </related-features>
  </context>

  <change-request>
    <summary>Add a dark mode toggle to the settings modal that persists user preference</summary>
    <motivation>Users have requested dark mode support for better accessibility</motivation>
  </change-request>

  <impact-analysis>
    <affected-files>
      <file action="modify">src/components/SettingsModal.tsx</file>
      <file action="modify">src/api/settings.py</file>
      <file action="create">src/hooks/useTheme.ts</file>
      <file action="modify">src/styles/globals.css</file>
    </affected-files>
    <affected-features>
      <feature id="settings">Add theme toggle component</feature>
    </affected-features>
    <breaking-changes>none</breaking-changes>
    <scope>small</scope>
    <confidence>high</confidence>
  </impact-analysis>

  <requirements>
    <requirement id="1" priority="must-have">
      Toggle switch in settings modal under "Appearance" section
    </requirement>
    <requirement id="2" priority="must-have">
      Theme preference saved to user settings via existing API
    </requirement>
    <requirement id="3" priority="must-have">
      CSS variables for light/dark themes
    </requirement>
    <requirement id="4" priority="should-have">
      Respect system preference on first load
    </requirement>
  </requirements>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0">
      When the user toggles the dark mode switch on, the system shall apply the dark theme
      immediately.
    </criterion>
    <criterion id="2" pattern="state-driven" priority="P0">
      While a saved theme preference exists, the system shall apply it on every page load.
    </criterion>
  </acceptance-criteria>
</crd>
```

## Compatibility with /breakdown

CRD format is designed to be processable by `/breakdown`:

| CRD Section | Maps to /breakdown |
|-------------|-------------------|
| `<requirements>` | Feature requirements for task generation |
| `<acceptance-criteria>` | Test requirements for tasks |
| `<impact-analysis>` | Layer planning (which files/features affected) |
| `<context>` | Project context for task generation |
| `<affected-files>` | File scope for tasks |

When running `/breakdown` on a CRD:
```bash
/breakdown docs/crd/dark-mode-toggle.md --project-path /path/to/project
```

The breakdown skill:
1. Detects CRD format (vs PRD format)
2. Reads PROJECT.md for full context
3. Uses `<impact-analysis>` to scope task generation
4. Generates fewer layers (typically 2-3 vs 5 for PRD)
5. Tasks reference existing code from PROJECT.md context

## Workflow Transitions

```
draft → ready → in-progress → complete
              ↘ abandoned
```

| `<workflow>` | Meaning |
|--------|---------|
| `draft` | Still being edited, not ready for implementation |
| `ready` | Approved for implementation, can run /breakdown |
| `in-progress` | Tasks generated and being executed |
| `complete` | All tasks finished, PROJECT.md updated |
| `abandoned` | Cancelled, not implemented |
