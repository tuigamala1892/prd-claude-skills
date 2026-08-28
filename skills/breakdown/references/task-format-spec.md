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

  <source-feature>save-link</source-feature>          <!-- item 16: which feature, by slug -->
  <moscow>must-have</moscow>                          <!-- item 16: that feature's tier -->
  <satisfies-criteria>1,4,7</satisfies-criteria>      <!-- item 16: criterion ids, core §1 -->
  <requirement-level>P0</requirement-level>           <!-- item 16: highest among those -->
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
- `source-feature`: Required except in Layer 0. A feature slug, or a CRD slug on that path
- `moscow`: Required with `source-feature`. `must-have`, `should-have` or `could-have` — never
  `wont-have`, which `/execute` refuses (item 20)
- `satisfies-criteria`: Required except in Layer 0. Comma-separated criterion ids, no spaces
- `requirement-level`: Required with `satisfies-criteria`. `P0`, `P1` or `P2`

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

0. **Traceability resolves both ways**: every id in `<meta><satisfies-criteria>` appears in
   `<context><acceptance-criteria>`, and every criterion there is named by some `<test covers=>`.
   Item 30 checks this across the whole task set; here it is checkable within one file
1. **No placeholders**: No "TODO", "TBD", "...", or "[fill in]"
2. **No external references**: All information must be in the task file
3. **Concrete values**: Use specific names, paths, values - not "appropriate" or "suitable"
4. **Complete types**: All interfaces must have full type annotations
5. **Runnable verification**: All verification steps must be executable commands
