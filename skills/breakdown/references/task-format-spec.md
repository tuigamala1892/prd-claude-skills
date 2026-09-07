# Task File Format Specification

This document defines the XML schema for implementation task files.

## Root Element

```xml
<task>
  <!-- All sections below are REQUIRED unless marked optional -->
</task>
```

## Sections

### 0. Constraints (Optional)

What [`architecture.md`](architecture-format.md) binds this task to. Absent when the project
declares no rule file, or declares nothing that reaches this task's files.

```xml
<context>
  ...
  <constraints>
  Banned: httpx|requests under contexts/** -- ADR-004: contexts communicate by event, never by
    call. Exception: contexts/*/adapters/outbound/** (third-party APIs are called over HTTP).
  Test policy: tdd, runner vitest (web/**)
  Max files: 5 (contracts/**)
  Principle P-001: prefer deleting code to configuring it
  </constraints>
</context>
```

**Constraints:**

- A rule the task does not carry is a rule that does not exist at implementation time. Task files
  are self-contained by mandate and the implementer cannot open `architecture.md`.
- Carry the rule's **`reason` verbatim**. *"Banned: HTTP client to another context's service —
  ADR-004: contexts communicate by event, never by call"* says what to do instead; a rule number
  does not.
- Carry a rule's `<except>` when it also covers this task's files. An implementer who cannot see
  the exception writes around a rule that does not apply to them.
- Carry only what reaches this task. The whole rule file in every task is the volume cost P22
  describes, paid for content the task never reads.
- **Never invent one.** An absent element means the project declared nothing relevant. An empty
  one is indistinguishable from an invented one at the far end.

### 1. Meta (Required)

Task identification and classification.

```xml
<meta>
  <id>L1-001</id>                    <!-- Layer number + sequence: L{layer}-{seq} -->
  <name>Create Project Model</name>   <!-- Human-readable task name -->
  <layer>1-foundation</layer>         <!-- Layer identifier -->
  <priority>1</priority>              <!-- Execution order within layer (1 = first) -->
  <estimated-files>2</estimated-files> <!-- Number of files to create/modify -->
  <cwd>packages/billing</cwd>         <!-- Optional; where commands run. See below -->

  <!-- item 65: one per feature this task descends from. Repeatable. -->
  <source-feature slug="save-link" moscow="must-have"
                  satisfies-criteria="1,4,7" requirement-level="P0"/>
</meta>
```

**Constraints:**
- `id`: Must match pattern `L[0-9]+-[0-9]{3}`
- `layer`: `{id}-{name}`, from the layer set `plan-layers` derived — `0-setup`, `1-foundation`,
  `2-backend`, `3-frontend` and `4-integration` are the shipped defaults, not the enum

**Neither is a fixed list any more, and the old ones contradicted this file.** `id` was
`L[1-4]-[0-9]{3}` and `layer` was an enum of four, while the three fields below say *"Required
except in Layer 0"* — so this document required a layer its own constraints could not express, and
a live run generating `L0-001` in `0-setup` was writing tasks its own schema rejected (P40).

The deeper reason is item 28: `architecture.md`'s `<layers>` lets a project declare its own graph,
and a microservices project instantiates it per service with ids scoped to their block. An enum of
four names could not survive that, and pinning one here would have made the layer file advisory.
- `priority`: Integer 1-99
- `estimated-files`: Integer, 1 to the task's effective limit — `<task-limits>` from
  `architecture.md`, defaulting to 3
- `cwd`: Optional. **Relative to the worktree root**, and must stay inside it
- `source-feature`: **Repeatable.** Required except in Layer 0, at least once. Attributes:
  - `slug` — a feature slug, or a CRD slug on that path
  - `moscow` — `must-have`, `should-have` or `could-have` for **this** feature; never
    `wont-have`, which `/execute` refuses (item 20)
  - `satisfies-criteria` — comma-separated criterion ids **of this feature**, no spaces
  - `requirement-level` — `P0`, `P1` or `P2`: the highest among the ids named here

#### A task names every feature it descends from (item 65)

**`<source-feature>` repeats, and each one carries its own tier, criteria and level.** A task that
legitimately covers criteria from more than one feature — an end-to-end integration task is the
ordinary case — used to have no way to say whose criterion it carried, and **three live runs met
one and invented three different workarounds** (**P43**):

| Run | What it did | Why it is wrong |
|---|---|---|
| 1 | invented `feature#id`, applied to the carried criteria and not to `<satisfies-criteria>` | the two halves of one task stopped referring to each other |
| 2 | split the task, and said why | correct, and it changes the task set to suit the schema |
| 3 | narrowed the attribution to one feature, silently | **worst of the three, because nothing says so** |

Run 3's `L4-002` walked `save-link`, `tag-links` and `list-links` criterion 2 and declared
`tag-links` alone. **No check caught it** — item 30's coverage passes, because those criteria are
covered by other tasks. What was lost is that the coverage report, the scope cross-check,
`tasks-summary.md` and the gate all believed the task belonged to one feature, so dropping that
feature from scope would have silently taken the only end-to-end assertion of the other two.

```xml
<meta>
  <source-feature slug="save-link"  moscow="must-have"   satisfies-criteria="1"   requirement-level="P0"/>
  <source-feature slug="tag-links"  moscow="should-have" satisfies-criteria="1,3" requirement-level="P1"/>
  <source-feature slug="list-links" moscow="should-have" satisfies-criteria="2"   requirement-level="P1"/>
</meta>
```

**The old shape is read and never written.** One `<source-feature>slug</source-feature>` with
sibling `<moscow>`, `<satisfies-criteria>` and `<requirement-level>` elements is still accepted by
every reader, and the siblings still fill in an attribute the new form omits — that is what makes
a half-migrated task readable rather than an error. New tasks carry the attribute form. This is
item 45's rule, and it applies here for the same reason: a corpus of task files does not migrate
itself, and a reader that refuses the old shape strands every task set generated before today.

**The task's effective tier is the strongest of its edges**, and the same for its level:
`must-have` over `should-have` over `could-have`, `P0` over `P1` over `P2`. A task is built or not
built as a unit, so a filter — `/execute`'s `--priority`, `check-coverage.py`'s
`--requirement-level` — must see the strongest obligation it carries. `build-manifest.py` computes
both and writes them beside the list.

**One exception, and it is deliberate: `/execute`'s preflight refuses on ANY edge.** A task
carrying `moscow="wont-have"` anywhere is refused (item 20) even when another edge is
`must-have` and the effective tier is therefore `must-have`. The strongest-wins rule answers *how
important is this task*; the refusal answers *should this task exist at all*, and nothing should
ever produce that edge — which is precisely why finding one is worth stopping for.

#### Traceability: four elements, and none of them is `<priority>`

Item 16. Before these, **a task named the feature it came from nowhere at all** — attribution was
a string match on the task's `<name>`, which is why item 21's tier probe had to invent slugs that
could not occur by coincidence, and why `check-scope.py` could attribute nothing.

**`<priority>` is untouched, deliberately, and that is why these have the names they do.** It is
an integer meaning *merge order within the layer*, and it has meant that since the beginning
(**P3**). Overloading it with MoSCoW would leave every reader ambiguous about which of two
unrelated orderings it was reading, so the feature's tier arrives as `<moscow>` — a name that was
free.

**`<satisfies-criteria>` is the finer half, and it survives only because something checks it.**
Kiro's spec asks for exactly this traceability and its own samples fail to keep it — the workflow
specifies `_Requirements: 1.2_` and the sample degrades to `_Requirements: 1_`. Fine-grained
traceability decays wherever nothing verifies it, which is item 30's job and why the two items sit
together in the plan's ordering.

**`<requirement-level>` is the *highest* of the criteria named**, not a list. A task is built or
not built as a unit, so the level that matters to `--requirement-level` is the strongest
obligation it carries.

**Layer 0 is exempt, and it is the only exemption.** Its tasks create directories, config and a
test harness; they descend from the tech stack rather than from any feature, and inventing a
`<source-feature>` for them would put a false attribution into the coverage check item 30 builds
on.

#### Criteria from more than one feature are grouped by feature (item 65)

**Criterion ids are per feature.** `save-link` criterion 1 and `tag-links` criterion 1 are two
different requirements with the same name, so a task carrying both must say which is which:

```xml
<acceptance-criteria>
  <from-feature slug="save-link">
    <criterion id="1" pattern="event-driven" priority="P0">
    When a user submits a link, the system shall store it and return the stored record.
    </criterion>
  </from-feature>
  <from-feature slug="tag-links">
    <criterion id="1" pattern="state-driven" priority="P1">
    While a link has tags, the system shall list it under each of them.
    </criterion>
  </from-feature>
</acceptance-criteria>
```

- **Required when the task has more than one `<source-feature>`.** An ungrouped criterion in such
  a task names two requirements at once, and item 59's grader fails it.
- **Omit it when there is one**, which is most tasks. There is nothing to disambiguate, and
  wrapping every existing task to no purpose is churn.
- **The `<criterion>` element inside is still copied byte-for-byte**, ids included. That is why
  the qualification is a *wrapper* rather than an attribute on the criterion or a `feature#id`
  spelling: item 17 requires the copy to be verbatim, and any of the alternatives edits it.

`<test covers=>` takes a `from-feature` attribute under the same rule — required when the task
spans features, omitted when it does not:

```xml
<test id="2" covers="1" from-feature="tag-links">
```

#### `<cwd>` — where this task's commands run

**Omit it and everything runs at the worktree root, which is what every task did before this
element existed.** It is only needed when a repository holds more than one component.

Without it, a task in a monorepo package has to hand-write the directory into every command it
declares — `cd packages/billing && pytest` in each of five steps, in a file whose other paths are
all relative to the repository. The commands then work in `execute-verify` and nowhere else,
because the `cd` is inside the string rather than around it.

```xml
<meta>
  <cwd>packages/billing</cwd>
</meta>
<verification>
  <step>Run: `pytest tests/test_invoices.py -v` - all tests pass</step>
</verification>
```

Both readers honour it: `execute-verify` runs every `<step>` from there, and the implementer runs
its build and test commands from there. **Neither changes where the commit happens** — that is the
worktree, always, and git does not care which subdirectory you are standing in.

**It must be relative and it must not escape the worktree.** An absolute path, a drive letter or
any `..` segment is refused rather than resolved: the worktree is the isolation boundary the whole
pipeline depends on, and a task that verifies outside it is verifying something no merge will
carry. `<files-to-create>` paths stay relative to the **worktree root**, not to `<cwd>` — they
describe what the task produces, and only commands have a working directory.

**Who writes it.** `breakdown-generate-tasks` emits it when the source names the component a
feature belongs to; otherwise a task author adds it by hand. It is not inferred from
`<files-to-create>`: two files sharing a parent directory is not evidence that the parent is where
the test runner lives. Item 53's `<repo-structure>monorepo</repo-structure>` is what will let the
generator produce it systematically.

### 2. Context (Required)

All background information needed to understand the task.

**Carry the source document's `<gaps>` into `<context>`, unchanged.** A gap the author declared
is the difference between *"this is not specified"* and *"the implementer will decide"*, and a
task file is self-contained by mandate — an implementer who cannot see the gap fills it in, which
is exactly the invention [core §6](../../../schema/core.md#6-gaps--what-a-document-knows-it-is-missing)
exists to prevent.

```xml
<gaps>
  <gap id="3" kind="decision" raised="2026-08-18">
  Whether archived links keep their tags is undecided.
  </gap>
</gaps>
```

Carry only the gaps that reach this task. `kind` travels with the gap: `specification`,
`dependency` and `decision` stop execution, `ownership` and `evidence` warn. **A carried gap is
not a placeholder** — `review-criteria.md` scopes its placeholder scan around this element for
that reason.

**`<prd-excerpt>` carries acceptance criteria, and they mean what
[core §2](../../../schema/core.md#2-acceptance-criteria) says they mean** — a `<criterion>` from
a PRD feature file and one from a CRD are the same element, so a task generated from either
carries the same thing. Copy a criterion's `id` with it: core §1 makes ids citable precisely so
that a task, a commit and a review can name the same requirement and be talking about it.

#### The criteria are carried structurally, not excerpted (item 17)

`<prd-excerpt>` as free prose is how **P2 and P4 happen**: the criteria arrive as a paragraph
somebody rewrote, so nothing downstream can name criterion 7, and the data model is re-inferred by
a generator that cannot see the one the author wrote. **This is where the pipeline stops
discarding the document.**

```xml
<context>
  <acceptance-criteria>
    <criterion id="4" pattern="event-driven" priority="P0">
    When a user submits a link, the system shall store it and return the stored record.
    </criterion>
    <criterion id="7" pattern="unwanted-behaviour" priority="P0">
    If the URL is not well-formed, then the system shall reject it and store nothing.
    </criterion>
  </acceptance-criteria>

  <data-model>
  <!-- The feature's own <notes><data-model>, carried. NOT re-inferred. -->
  Link: id, url, title, created_at. Tags are a separate entity, joined many-to-many.
  </data-model>

  <prd-excerpt>
  <!-- What remains: the feature description, and anything not carried structurally above -->
  </prd-excerpt>

  <tech-stack>
  <!-- List technologies and versions -->
  Python 3.11, FastAPI 0.100+, SQLAlchemy 2.x, PostgreSQL 15
  </tech-stack>

  <template-base>webapps/backends/python</template-base>  <!-- Optional: template path -->

  <project-structure>
  <!-- Optional: Relevant directory structure -->
  app/
    models/
    api/
    services/
  </project-structure>
</context>
```

**Constraints:**
- `acceptance-criteria`: The source criteria **verbatim, with their original ids**. Every id here
  must appear in `<meta><satisfies-criteria>`, and vice versa
- `data-model`: Present when the source feature declares a `<notes><data-model>`. **Copied, never
  inferred** — a data model half-read and half-invented is worse than either, because nobody can
  tell which half is the author's
- `prd-excerpt`: What is left after the two above. Must include all relevant requirements from PRD
- `tech-stack`: Must specify versions where known
- Do NOT reference external files - all context must be inline

**Verbatim means verbatim.** A criterion that arrives reworded is one no reviewer can match back
to the PRD, and the whole point of core §1's citable ids is that a task, a commit and a review can
name the same requirement and be talking about it. Copy the element; do not summarise it, split it
or improve its grammar.

### 3. Dependencies (Required)

Interface contracts this task depends on.

```xml
<dependencies>
  <interface name="Base" type="sqlalchemy-declarative-base">
  from sqlalchemy.orm import DeclarativeBase

  class Base(DeclarativeBase):
      pass
  </interface>

  <interface name="get_db" type="fastapi-dependency">
  from typing import Generator
  from sqlalchemy.orm import Session

  def get_db() -> Generator[Session, None, None]:
      """Yields database session, auto-closes on completion."""
      ...
  </interface>

  <!-- Add all interfaces this task needs -->
</dependencies>
```

**Constraints:**
- Each `<interface>` must have `name` and `type` attributes
- Include complete type signatures with imports
- Include docstrings for functions
- Do NOT include implementation details unless critical

### 4. Objective (Required)

Clear, concise description of what this task accomplishes.

```xml
<objective>
Create the SQLAlchemy model for storing PRD projects. The model should
support storing project metadata (name, slug, status) and the full PRD
content as JSONB for flexible schema.
</objective>
```

**Constraints:**
- 1-3 sentences
- Focus on WHAT, not HOW
- No implementation details

### 5. Requirements (Required)

Specific, verifiable requirements.

```xml
<requirements>
  <requirement id="1">
  Model class named `Project` in file `app/models/project.py`
  </requirement>

  <requirement id="2">
  Fields:
  - id: UUID, primary key, auto-generated
  - name: str, max 255 chars, required
  - slug: str, max 100 chars, unique, required
  - status: ProjectStatus enum (draft, in_progress, complete)
  - prd_content: JSONB, nullable
  - created_at: datetime, auto-set on create
  - updated_at: datetime, auto-set on update
  </requirement>

  <requirement id="3">
  Alembic migration file that creates the `projects` table
  </requirement>

  <requirement id="4">
  Export Project class in `app/models/__init__.py`
  </requirement>
</requirements>
```

**Constraints:**
- Each requirement has unique `id` attribute
- Requirements must be specific and verifiable
- No ambiguous terms like "appropriate", "good", "proper"
- Include exact file paths, class names, field names

### 6. Test Requirements (Required by default)

Tests to write BEFORE implementation (TDD).

> **`<testing default=>` decides whether this section is required, and three components must
> agree.** The TDD mandate does not live in `tdd-workflow.md`, which only describes
> Red/Green/Refactor — it is imposed here, by this section being required, and in
> `review-criteria.md`, which makes it critical twice. A project declaring
> `<testing default="none">` in [`architecture.md`](architecture-format.md) would otherwise have
> every task fail batch review at `/breakdown` and never reach `execute-batch` at all.
>
> So: **required when `<testing default="tdd">` or when no `architecture.md` declares otherwise**
> — which is every project that has ever run this toolchain — and **absent when the project
> declares `default="none"`**. Do not emit it empty; an empty required section is a different
> claim from a project that switched TDD off, and only one of them is a defect.
>
> TDD is right for most projects and wrong for a spike. The toolchain should be able to say which
> it is running.

**Each test names the criterion it covers (item 17).** A test citing no criterion is one nobody
can trace back, and a criterion no test cites is the coverage gap item 30 reports.

**An `unwanted-behaviour` criterion states its negative case explicitly**, so the failing test is
*read off* rather than invented. That is item 33 paying for itself here: inventing the failure
case is what the toolchain does today, and **P19** says it cannot be trusted to.

```xml
<test-requirements>
  <test id="1">
  Test file: `tests/models/test_project.py`
  </test>

  <test id="2" covers="7">
  Test: a malformed URL is rejected and nothing is stored
  - POST /links with url="not a url"
  - Assert 422
  - Assert the links table is unchanged
  </test>

  <test id="2">
  Test: Project can be created with valid name and slug
  - Create Project(name="Test", slug="test")
  - Assert project.id is UUID
  - Assert project.created_at is set
  </test>

  <test id="3">
  Test: Slug uniqueness is enforced
  - Create Project with slug="unique"
  - Attempt to create another with same slug
  - Assert IntegrityError is raised
  </test>

  <test id="4">
  Test: prd_content stores and retrieves dict correctly
  - Create Project with prd_content={"key": "value"}
  - Retrieve from DB
  - Assert retrieved.prd_content == {"key": "value"}
  </test>

  <test id="5">
  Test: Status enum works correctly
  - Create Project with status=ProjectStatus.draft
  - Assert stored value is correct
  </test>
</test-requirements>
```

**Constraints:**
- Tests are written FIRST (TDD)
- Each test has unique `id` attribute
- Test descriptions include:
  - Setup steps
  - Action to take
  - Expected assertion
- Use concrete values, not "some value" or "any value"

### 7. Files to Create (Required)

Explicit list of files this task creates or modifies.

```xml
<files-to-create>
  <file>app/models/project.py</file>
  <file>app/models/__init__.py</file>
  <file>app/migrations/versions/001_create_projects_table.py</file>
  <file>tests/models/test_project.py</file>
</files-to-create>
```

**Constraints:**
- Maximum `<task-limits>` files (excluding test file), **defaulting to 3**. Read
  `architecture.md`'s `<task-limits default=>` when the project declares one, and
  honour a scoped `<limit match= max-files=>` for files under that glob. Three is the
  shipped default, not a law — see
  [`architecture-format.md`](architecture-format.md)
- Use full relative paths from project root
- List in order of creation

### 8. Verification (Required)

Commands to verify task completion.

```xml
<verification>
  <step>Run: `alembic upgrade head` - migration applies without error</step>
  <step>Run: `pytest tests/models/test_project.py -v` - all tests pass</step>
  <step>Check: `app/models/__init__.py` exports Project class</step>
</verification>
```

**Constraints:**
- Each step is a runnable command or checkable condition
- Include expected outcome
- Steps should be executable in order

### 9. Exports (Required)

Interface contracts this task provides for later tasks.

```xml
<exports>
  <interface name="Project" type="sqlalchemy-model">
  from uuid import UUID
  from datetime import datetime
  from enum import Enum
  from sqlalchemy.orm import Mapped

  class ProjectStatus(Enum):
      draft = "draft"
      in_progress = "in_progress"
      complete = "complete"

  class Project(Base):
      __tablename__ = "projects"

      id: Mapped[UUID]
      name: Mapped[str]
      slug: Mapped[str]  # unique
      status: Mapped[ProjectStatus]
      prd_content: Mapped[dict | None]
      created_at: Mapped[datetime]
      updated_at: Mapped[datetime]
  </interface>
</exports>
```

**Constraints:**
- Include all public interfaces created by this task
- Use complete type annotations
- Include imports needed to use the interface
- This becomes the dependency for downstream tasks

## Validation Rules

0. **Traceability resolves both ways, per feature**: every id in a
   `<source-feature satisfies-criteria=>` appears in that feature's carried criteria, and every
   criterion carried is named by some `<test covers=>`. Item 30 checks this across the whole task
   set; here it is checkable within one file. **Per feature** is item 65: matching ids across
   features is how a task ends up citing criterion 2 of the wrong one and passing
1. **No placeholders**: No "TODO", "TBD", "...", or "[fill in]"
2. **No external references**: All information must be in the task file
3. **Concrete values**: Use specific names, paths, values - not "appropriate" or "suitable"
4. **Complete types**: All interfaces must have full type annotations
5. **Runnable verification**: All verification steps must be executable commands
