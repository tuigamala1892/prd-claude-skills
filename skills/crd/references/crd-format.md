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
  <acceptance-criteria>...</acceptance-criteria>
  <gaps>...</gaps>
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
  <priority>should-have</priority>
  <!-- optional; a judgement, never derived. Core §8 -->
  <architecturally-significant because="cross-cutting" criteria="2,3"/>
</meta>
```

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | String | Human-readable change name |
| `slug` | Yes | String | URL-safe identifier (lowercase, hyphens) |
| `type` | Yes | `feature-add`, `feature-modify`, `feature-remove`, `refactor` | Change type |
| `created` | Yes | YYYY-MM-DD | Creation date |
| `workflow` | Yes | see [core §3](../../../schema/core.md#3-status) | Where this change is in the process |
| `priority` | Yes | Core [§4](../../../schema/core.md#4-priority) — MoSCoW | Whether this change request is in scope at all |
| `architecturally-significant` | No | Core [§8](../../../schema/core.md#8-architecturally-significant--a-judgement-declared) | Whether this change warrants a design step |

### `<architecturally-significant>` — core §8, and it arrived last (item 76)

**Defined in [core §8](../../../schema/core.md#8-architecturally-significant--a-judgement-declared),
identically to the PRD's.** Optional, `because` from the six-value enum, `criteria` naming the
criterion ids that carry it.

**A refactor CRD is the document item 35 was written for.** *"Replace the session store"* is
architecturally significant in a way that *"add a column"* is not, and until item 76 a change
request had no way to say which it was — while `check-references.py` was already reading the
element and `check-gate.py` was already running that script for a CRD. A live reader with no
producer, which is P46's shape on the path item 68 did not reach.

**It needed no schema version**, and that was measured: the element is optional and
`check-artefacts.py` closes a child set only for `<notes>`, so a CRD carrying it validates against
schema-6 unchanged. Core §8 records the reasoning.

**`<priority>` is the whole document's, and it is the only MoSCoW in the file.** Change requests
compete for attention the way features compete for a release, and `--list` is the survey that
shows the competition — a listing that cannot show tiers is a worse listing. It arrived at item
47 together with the retirement of requirement-level MoSCoW, which is what made the word
unambiguous here: within a CRD, MoSCoW now means exactly one thing.

**This is core §4.1's rule and not an exception to it.** On the PRD path the index owns feature
priority because a ranking has no meaning inside the thing ranked. A change request has no index
— `/crd --list` is the survey, derived by scanning — and the document *is* the planning unit, so
the two coincide and it carries its own.

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
| `project-ref` | Yes | Path to PROJECT.md. **Resolved and compared** — see below |
| `prd-ref` | No | Path to PRD if project was created with /prd. Resolved when present |
| `related-features` | Yes | List of features affected by this change |
| `feature-ref` | - | Reference to feature in PROJECT.md with relationship note. `id` is resolved against `PROJECT.md`'s `<feature id=>` |

**All three are resolved by `check-references.py`, and until group 8b none of them was.** They
were a producer with no consumer three times over — one of them `Required` — which is P2's shape
on this path. The rule is item 39's, arriving where it had never been applied: *a reference that
names something must resolve to it, or be reported by name.*

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-references.py docs/crd/<slug>.md \n    --project-path <path>
```

**`<project-ref>` is compared against the project the run resolved, never used to resolve it.**
Letting a document choose which `PROJECT.md` a run reads would hand a file authority over where
the run points. Comparing them catches the case that matters: a CRD describing a change to one
project, executed against another. Without `--project-path` the check says it could not make the
comparison rather than reporting a check it did not make.

`/breakdown`'s gate runs this for every CRD. It used to skip it entirely — the script only took a
PRD directory — so a change request's references were followed by nothing at all.

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


### Requirements Section — retired at item 46

**There is no `<requirements>` element. Its entries are criteria.**

A CRD used to carry `<requirements>` *and* `<acceptance-criteria>` as two separate, unlinked
lists. The split was not a design; it was a consequence of Given/When/Then being a **scenario**
format. A scenario says what happens in one case, so it cannot state an obligation, so a second
list was needed to hold the obligations. Item 33 removed the cause: an EARS criterion *is* a
requirement — *"When the user toggles the dark mode switch on, the system shall apply the dark
theme immediately"* is not a scenario about a toggle, it is a thing the system must do.

So the two lists became one, with one id space, and P31's unanswerable question — *which criteria
discharge requirement 3?* — is dissolved rather than answered: there is no requirement 3 that is
not itself a criterion.

**The resolution deletes a CRD concept rather than adding a PRD one, and that was the decision.**
The alternative — giving PRD features a `<requirements>` layer above their criteria — was
considered and rejected: it would add a level to 64 features to accommodate a split that exists
only because of a format both paths have left. This is recorded here rather than buried in the
plan, because it is the change most likely to be questioned by someone reading the CRD schema
first and seeing a layer removed. **The layer was never carrying meaning of its own.** It was
carrying the requirements Given/When/Then had no way to state.

**Accepted on read; never written.** A CRD that still has `<requirements>` is read as though each
entry were a criterion with no `pattern` — the same policy core §2 and §3 apply to the other
pre-migration shapes, and for the same reason: a document is authored in one place and broken
down in another, and a hard cutover strands whatever is in flight. Item 41's migration rewrites
them, converting each requirement's MoSCoW priority to `P0|P1|P2` on the way.

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

**Priority on a criterion is `P0|P1|P2`, and it is the only requirement-level priority in the
file.** Until item 47 a CRD carried two vocabularies for one concept — MoSCoW on `<requirement>`,
`P0|P1|P2` on `<criterion>` — which is what made `/breakdown --requirement-level` select nothing
here. MoSCoW survives one level up, on the document, where the judgement is across whole items.

**This list is now the CRD's requirements.** Everything `<requirements>` used to hold is here,
which means it is also what `/breakdown` reads for task generation — not a supplementary list of
tests beside a list of obligations, but the obligations themselves.

### Gaps Section

```xml
<gaps>
  <gap id="1" kind="specification" raised="2026-01-12">
  Whether an archived link keeps its position in a manually ordered list is undecided.
  </gap>
  <gap id="2" kind="dependency" raised="2026-01-12">
  Restoring depends on the soft-delete column added by change request `soft-delete-links`,
  which is not merged.
  </gap>
</gaps>
```

**Defined in [core §6](../../../schema/core.md#6-gaps--what-a-document-knows-it-is-missing),
identically to the PRD path's.** Same element, same five kinds, same rules about what blocks and
what warns. The examples above are examples.

**Arrived at item 48, and what it replaced was nothing at all.** Before it, a CRD interview that
ended with *"we'll define that later"* left no trace: a change request that had deferred half its
behaviour was indistinguishable from one that had none, and the deferral surfaced as a task with
nothing to build. The PRD path had `<gaps>` and `what-next.md`; the CRD path had neither.

**A deferred criterion becomes a `<gap kind="specification">`, not an absence.** That is the whole
mechanism. It also gives `<workflow>` the mechanical test it lacked — see the transitions table at
the foot of this document.

**There is no `what-next.md` equivalent, and that is deliberate.** A CRD is one document about one
change; the deferral belongs in `<gaps>` inside it and the next command belongs in `<meta>`. The
symmetric answer — a `what-next` file per CRD — is the wrong one, and is recorded here because it
is the obvious thing to reach for.

## Complete Example

```xml
<crd>
  <meta>
    <name>Add Dark Mode Toggle</name>
    <slug>dark-mode-toggle</slug>
    <type>feature-add</type>
    <created>2026-01-12</created>
    <workflow>ready</workflow>
    <priority>should-have</priority>
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

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0">
      When the user toggles the dark mode switch on, the system shall apply the dark theme
      immediately.
    </criterion>
    <criterion id="2" pattern="state-driven" priority="P0">
      While a saved theme preference exists, the system shall apply it on every page load.
    </criterion>
    <criterion id="3" pattern="event-driven" priority="P0">
      When the user changes the theme, the system shall persist the preference through the
      existing settings endpoint.
    </criterion>
    <criterion id="4" pattern="optional-feature" priority="P1">
      Where no saved preference exists, the system shall follow the operating system's dark
      mode setting.
    </criterion>
    <criterion id="5" pattern="unwanted-behaviour" priority="P1">
      If the settings endpoint rejects the write, then the system shall keep the theme applied
      for the session and report that the preference was not saved.
    </criterion>
  </acceptance-criteria>

  <gaps>
    <gap id="1" kind="decision" raised="2026-01-12">
    Whether the toggle also appears in the top bar, or only in settings, is undecided.
    </gap>
  </gaps>
</crd>
```

## Compatibility with /breakdown

CRD format is designed to be processable by `/breakdown`:

| CRD Section | Maps to /breakdown |
|-------------|-------------------|
| `<acceptance-criteria>` | **Both** the requirements a task implements and its test requirements — one list, since item 46 |
| `<meta><priority>` | `--priority <threshold>`: whether this change request is broken down at all |
| `<criterion priority=>` | `--requirement-level <P0\|P1\|P2>`: which criteria within it are built |
| `<gaps>` | Reported, and a `specification` gap blocks; core §6 says which kinds warn |
| `<impact-analysis>` | Layer planning (which files/features affected) |
| `<context>` | Project context for task generation |
| `<affected-files>` | File scope for tasks |

**The first row is the item 46 change seen from the consumer's end.** `/breakdown` used to read
two lists and had no way to link them; it now reads one, and a criterion arrives at a task as both
the thing to build and the thing to test. That is the same shape the PRD path has always had,
which is what lets `breakdown-generate-tasks` read either without a branch.

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

**`draft` versus `ready` has a mechanical test since item 48**, and it is core §6's rule with one
word changed: **a CRD marked `ready` must not carry a `<gap kind="specification">`.** *Ready for
implementation* and *the specification is incomplete* cannot both be true.

It runs one way only, exactly as the `<definition>` rule does. The absence of a gap proves
nothing, so nothing is ever promoted **to** `ready` by this check — an author holding a change at
`draft` for a reason the document cannot express is never contradicted upward. What is caught is
the contradiction, and only that.

**`complete` and `abandoned` are records of the past.** Item 41's migration rewrites their shape
but never re-reviews their content: turning their criteria into EARS is a formatting change, and
treating it as a re-specification invites an agent to improve the record of something that already
happened.
