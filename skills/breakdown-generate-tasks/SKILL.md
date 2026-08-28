---
name: breakdown-generate-tasks
description: Generate implementation task files for a specific layer. Called by /breakdown skill during Phase 4.
context: fork
agent: task-generator
model: claude-opus-5
---

# Task Generation

You are generating implementation task files for autonomous LLM execution.

## Input

The calling skill will provide:
1. Layer name (e.g., "1-foundation" or "0-setup")
2. Layer plan (tasks assigned to this layer from plan-layers)
3. PRD analysis (from analyze-prd)
4. Template path (if any)
5. Output directory path
6. **Task batch** (optional): Subset of tasks to generate (for large layers)
7. **Previous review feedback** (optional): Critical issues from failed review attempt

### Batch Mode

When a task batch is provided:
- Only generate tasks listed in the batch
- Ignore other tasks in the layer plan
- Batch is a list of task IDs: `["L2-001", "L2-002", "L2-003", "L2-004", "L2-005"]`

### Retry Mode

When previous review feedback is provided, it will contain critical issues from the last attempt:

```json
{
  "attempt": 2,
  "previous_failures": [
    {
      "task_id": "L2-008",
      "issue": "Contains placeholder 'TBD' for schema field type"
    },
    {
      "task_id": "L2-009",
      "issue": "Missing interface methods in exports section"
    }
  ]
}
```

**CRITICAL**: When in retry mode, you MUST fix the reported issues. Do NOT repeat the same mistakes.

## CRITICAL CONSTRAINTS

These constraints are NON-NEGOTIABLE:

1. **Self-contained**: Each task file MUST contain ALL information needed. The implementing LLM cannot ask questions or look up external files.

2. **Small context**: Tasks are for ~50k token context models (Haiku, GLM 4.5-4.7). Be explicit, not clever.

3. **Interface contracts**: Dependencies use type signatures with imports, NOT full implementation code.

4. **Max files: `<task-limits>`, defaulting to 3.** Each task creates/modifies at most that
   many files (the test file is additional). Three is the *default*, not the law: read
   `<task-limits default=>` from `architecture.md` when the project declares one, and honour a
   scoped `<limit match= max-files=>` for tasks whose files fall under that glob. Three files is
   right for a UI change and wrong for adding an event type, where the schema, the producer, the
   consumer, the projection and the test are one change.

5. **TDD: `<testing default=>`, defaulting to `tdd`.** Test requirements come BEFORE
   implementation and tests are written first — **unless** `architecture.md` declares
   `<testing default="none">`, in which case omit `<test-requirements>` and say so in
   `<constraints>`. Do not emit an empty section: `review-tasks` reads the same declaration and
   will not require what the project switched off. Carry the matching `<policy kind= runner=>`
   for the paths this task touches into `<constraints>`, so the implementer runs the right
   runner rather than the default one.

6. **One criterion, one test.** A `<criterion>` is one EARS sentence naming one behaviour, so it
   becomes one `<test>`. Carry the criterion's `id` in the test so a failure names a requirement
   rather than a function. Its `pattern` tells you what kind of test to write, and the mapping is
   not decorative:

   | `pattern` | The test asserts |
   |---|---|
   | `ubiquitous` | an invariant — true after every operation, not just one |
   | `state-driven` | the behaviour holds for as long as the state does, including across a reload |
   | `event-driven` | one action produces one observable outcome |
   | `optional-feature` | the behaviour under the configuration, **and** its absence without it |
   | `unwanted-behaviour` | the error path — the thing that must NOT happen, does not |
   | `complex` | split it, and say in the task that you did |

   **A criterion with no `pattern` has not been migrated yet.** Write the test from the sentence
   and say so in the task; do not infer a pattern to fill the gap.

7. **No placeholders**: NEVER write "TODO", "TBD", "...", or any placeholder. If you don't know something, make a reasonable decision and document it.

8. **Concrete values**: Use specific names, paths, values. Never "appropriate" or "suitable".

## `architecture.md`, and what to carry from it

When the project declares one, the caller passes you its `<rules>` and `<principles>`. Task files
are self-contained by mandate, and the implementer cannot open `architecture.md` — so a rule the
task does not carry is a rule that does not exist at implementation time.

**Carry, into `<constraints>`:**

| From | Carry | Why |
|---|---|---|
| `<banned>` | every rule whose `match`/`path`/`from` glob covers a file this task touches, **with its `reason` verbatim** | the reason says what to do instead; a rule number does not |
| | the rule's `<except>` entries, when one also covers the task's files | an implementer who cannot see the exception writes around a rule that does not apply |
| `<testing>` | the `default`, and the `<policy>` matching this task's paths | the runner is not always the default one |
| `<task-limits>` | the effective limit for this task | it is the number `<files-to-create>` must satisfy |
| `<principles>` | any principle the source feature cites by id | a citation with no text at the far end is a dangling reference |

**Do not carry** the whole rule file, the layer graph, or the registries wholesale. A registry
entry comes in only where a task *touches* that contract, and then as the entry itself in
`<dependencies>` — a full inventory in every task is the volume cost P22 is about, paid for
content the task never reads.

**Never invent a constraint.** `<constraints>` holds what `architecture.md` says. If it declares
nothing relevant to this task, the element is absent — an empty rule list is not the same claim
as no rule file, and a reader downstream cannot tell an invented rule from a declared one.

## Task File Format

Generate XML files following this exact structure:

```xml
<task>
  <meta>
    <id>L1-001</id>
    <name>Create Project Database Model</name>
    <layer>1-foundation</layer>
    <priority>1</priority>
    <estimated-files>2</estimated-files>
    <!-- <cwd>packages/billing</cwd>  only when the source names a component; see below -->

    <source-feature>save-link</source-feature>
    <moscow>must-have</moscow>
    <satisfies-criteria>1,4</satisfies-criteria>
    <requirement-level>P0</requirement-level>
  </meta>

  <context>
    <acceptance-criteria>
    <!-- The source feature's criteria, VERBATIM, with their original ids. Copy the element. -->
    <criterion id="4" pattern="event-driven" priority="P0">
    When a user submits a link, the system shall store it and return the stored record.
    </criterion>
    </acceptance-criteria>

    <data-model>
    <!-- The feature's own <notes><data-model>, carried. Omit when it declares none. -->
    </data-model>

    <prd-excerpt>
    <!-- What is LEFT after the two above: the feature description, and nothing else -->
    <!-- Do NOT copy the entire PRD, and do NOT restate the criteria here -->
    </prd-excerpt>

    <tech-stack>
    Python 3.11, FastAPI 0.100+, SQLAlchemy 2.x, PostgreSQL 15
    </tech-stack>

    <template-base>webapps/backends/python</template-base>

    <project-structure>
    app/
      models/
        __init__.py
        base.py (exists - provides Base class)
      api/
      services/
    tests/
      models/
    </project-structure>
  
    <constraints>
    <!-- From architecture.md, when the project declares one. Copy the `reason` verbatim: -->
    <!-- Banned: httpx|requests under contexts/** -- ADR-004: contexts communicate by event, -->
    <!--   never by call. Exception: contexts/*/adapters/outbound/**                          -->
    <!-- Test policy: tdd, runner vitest (web/**)                                             -->
    <!-- Max files: 5 (contracts/**)                                                          -->
    <!-- Principle P-001: prefer deleting code to configuring it                              -->
    </constraints>

  </context>

  <dependencies>
    <interface name="Base" type="sqlalchemy-declarative-base">
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        """SQLAlchemy declarative base for all models."""
        pass
    </interface>

    <interface name="get_db" type="fastapi-dependency">
    from typing import Generator
    from sqlalchemy.orm import Session

    def get_db() -> Generator[Session, None, None]:
        """Yield database session. Auto-closes on request completion."""
        ...
    </interface>
  </dependencies>

  <objective>
  Create the SQLAlchemy model for storing PRD projects with support for
  project metadata and JSONB content storage.
  </objective>

  <requirements>
    <requirement id="1">
    Create model class `Project` in file `app/models/project.py`
    </requirement>

    <requirement id="2">
    Define enum `ProjectStatus` with values: draft, in_progress, complete
    </requirement>

    <requirement id="3">
    Project model fields:
    - id: UUID, primary key, server_default=uuid4
    - name: String(255), nullable=False
    - slug: String(100), unique=True, nullable=False
    - status: ProjectStatus enum, default=draft
    - prd_content: JSONB, nullable=True
    - created_at: DateTime, server_default=now()
    - updated_at: DateTime, onupdate=now()
    </requirement>

    <requirement id="4">
    Create Alembic migration `001_create_projects_table.py` that:
    - Creates `projects` table with all fields
    - Creates index on `slug` column
    - Creates index on `status` column
    </requirement>

    <requirement id="5">
    Export `Project` and `ProjectStatus` from `app/models/__init__.py`
    </requirement>
  </requirements>

  <test-requirements>
    <test id="1">
    Create test file: `tests/models/test_project.py`
    </test>

    <test id="2">
    Test: test_create_project_with_valid_data
    - Create Project(name="Test Project", slug="test-project")
    - Assert project.id is a valid UUID
    - Assert project.status == ProjectStatus.draft
    - Assert project.created_at is not None
    </test>

    <test id="3">
    Test: test_project_slug_uniqueness
    - Create Project(name="First", slug="unique-slug")
    - Commit to database
    - Attempt to create Project(name="Second", slug="unique-slug")
    - Assert IntegrityError is raised on commit
    </test>

    <test id="4">
    Test: test_project_prd_content_json
    - Create Project with prd_content={"features": ["a", "b"]}
    - Commit and refresh from database
    - Assert project.prd_content == {"features": ["a", "b"]}
    - Assert type is dict
    </test>

    <test id="5">
    Test: test_project_status_enum
    - Create Project with status=ProjectStatus.in_progress
    - Commit and refresh
    - Assert project.status == ProjectStatus.in_progress
    - Assert project.status.value == "in_progress"
    </test>
  </test-requirements>

  <files-to-create>
    <file>app/models/project.py</file>
    <file>app/migrations/versions/001_create_projects_table.py</file>
    <file>tests/models/test_project.py</file>
  </files-to-create>

  <verification>
    <step>Run: `alembic upgrade head` - must complete without errors</step>
    <step>Run: `pytest tests/models/test_project.py -v` - all 4 tests pass</step>
    <step>Verify: `app/models/__init__.py` exports Project and ProjectStatus</step>
  </verification>

  <exports>
    <interface name="Project" type="sqlalchemy-model">
    from uuid import UUID
    from datetime import datetime
    from enum import Enum
    from sqlalchemy.orm import Mapped
    from app.models.base import Base

    class ProjectStatus(str, Enum):
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
</task>
```

## Traceability, and the four elements that carry it (items 16 and 17)

**Every task outside Layer 0 must name where it came from.** Until item 16 a task named its
feature nowhere at all, so attribution downstream was a string match on `<name>` — which is why
`check-scope.py` could attribute nothing and why item 21's probe had to invent slugs that could
not occur by coincidence.

| Element | Value | Where it comes from |
|---|---|---|
| `<source-feature>` | the feature's slug | the feature file you were given |
| `<moscow>` | `must-have`, `should-have`, `could-have` | `index.md`'s entry for it. **Never `wont-have`** — those features never reach you (item 13) |
| `<satisfies-criteria>` | comma-separated criterion ids | the criteria this task actually implements |
| `<requirement-level>` | `P0`, `P1` or `P2` | **the highest** `priority` among those criteria |

**`<priority>` is not one of them and must not be touched.** It is an integer meaning merge order
within the layer, and it has meant that since the beginning (**P3**). The tier goes in `<moscow>`
because that name was free.

**Layer 0 tasks carry none of these**, and that is the only exemption. They create directories,
config and a test harness — they descend from the tech stack, not from a feature, and inventing a
`<source-feature>` for them would put a false attribution into item 30's coverage check.

### Carry the criteria; do not rewrite them

**Copy each `<criterion>` element whole, with its `id`, `pattern` and `priority`.** Do not
summarise, split, merge or improve the grammar. A reworded criterion is one no reviewer can match
back to the PRD, and core §1's ids exist so a task, a commit and a review can name the same
requirement and be talking about it.

**Split a criterion across two tasks by citing it from both** — `<satisfies-criteria>` is a list
and an id may appear in more than one task. What you must not do is paraphrase half of it into
each.

### Derive the tests from the criteria, and say which

Each `<test>` carries `covers="<criterion id>"`. A test citing no criterion cannot be traced back;
a criterion no test cites is the coverage gap item 30 reports.

**An `unwanted-behaviour` criterion already states its negative case**, so read the failing test
off it rather than inventing one. Inventing the failure case is what this skill did before item
33, and **P19** is the finding that says it cannot be trusted to.

### The data model is copied, never inferred

When the feature declares `<notes><data-model>`, carry it into `<context><data-model>` unchanged.
When it declares none, **omit the element** — do not infer one to fill the slot. A data model
half-read and half-invented is worse than either, because nobody can tell which half is the
author's.

## Generation Process

For each task in the layer plan:

1. **Read the task spec** from the layer plan
2. **Gather context**:
   - Relevant PRD excerpts
   - Dependencies from previous tasks (their `<exports>`)
   - Template patterns if applicable
3. **Write requirements** with exact specifications
4. **Write test requirements** with concrete test cases
5. **Define verification steps** with runnable commands
6. **Define exports** for downstream tasks

**`<meta><cwd>`, only under `monorepo`, and only when the source names a component.** Phase 1
resolved `<repo-structure>` (item 53) and passed it down:

- **`single`** — never emit `<cwd>`. One repository with one thing in it has one place to run
  commands, and a `<cwd>` there is noise that can only be wrong.
- **`monorepo`** — if the feature this task comes from declares which package, service or app it
  belongs to, emit that path as `<cwd>` and write every verification command **as if standing in
  it**: `pytest tests/test_invoices.py`, never `cd packages/billing && pytest
  tests/test_invoices.py`. A `cd` inside a command string works in one runner and nowhere else.

**Do not infer it from `<files-to-create>`.** Two files sharing a parent directory is not evidence
that the parent is where the test runner lives, and a wrong `<cwd>` fails verification in a way
that looks like broken code. No declared component means no `<cwd>`, which means the worktree
root — the behaviour every task had before the element existed.

## Layer 0 Task Format

Layer 0 (setup) tasks are different - they use shell commands instead of code generation:

```xml
<task>
  <meta>
    <id>L0-001</id>
    <name>Copy Template to Target Directory</name>
    <layer>0-setup</layer>
    <priority>1</priority>
    <estimated-files>0</estimated-files>
  </meta>

  <context>
    <prd-excerpt>
    Project type: greenfield
    Template: webapps/backends/python
    Target: /path/to/new-project
    </prd-excerpt>

    <tech-stack>
    Python 3.11, FastAPI, PostgreSQL (from template)
    </tech-stack>

    <template-source>webapps/backends/python</template-source>
    <target-directory>/path/to/new-project</target-directory>
  </context>

  <dependencies>
    <interface name="template" type="filesystem">
    Template exists at: webapps/backends/python
    Contains: Makefile, app/, frontend/, docker-compose.yml
    </interface>
  </dependencies>

  <objective>
  Copy the Python/FastAPI template to the target project directory,
  creating the foundation for the new project.
  </objective>

  <requirements>
    <requirement id="1">
    Create target directory if it doesn't exist: mkdir -p /path/to/new-project
    </requirement>
    <requirement id="2">
    Copy template contents, excluding the template's own git metadata:
    rsync -a --exclude='.git' webapps/backends/python/ /path/to/new-project/
    </requirement>
  </requirements>

  <!--
    NEVER emit a task that recursively deletes the .git directory at the target path.
    Earlier versions of this template did exactly that, intending to drop the
    TEMPLATE's git metadata after a copy. But the path is the caller's project, so it
    destroyed the target repository's history instead. Exclude .git from the copy;
    nothing then needs deleting. See finding F2.
  -->

  <test-requirements>
    <test id="1">
    Verify directory exists: test -d /path/to/new-project
    </test>
    <test id="2">
    Verify Makefile exists: test -f /path/to/new-project/Makefile
    </test>
    <test id="3">
    Verify app directory: test -d /path/to/new-project/app
    </test>
  </test-requirements>

  <files-to-create>
    <!-- Layer 0 creates directories, not individual files -->
  </files-to-create>

  <verification>
    <step>Run: ls -la /path/to/new-project - must show template files</step>
    <step>Run: test -f /path/to/new-project/Makefile && echo "OK"</step>
  </verification>

  <exports>
    <interface name="project_directory" type="path">
    /path/to/new-project
    - Contains: app/, frontend/, Makefile, docker-compose.yml
    - Ready for: initial commit, dependency installation
    </interface>
  </exports>
</task>
```

## Quality Checks Before Output

Before writing each task file, verify:

- [ ] `<source-feature>`, `<moscow>`, `<satisfies-criteria>` and `<requirement-level>` are all
      present (every layer except Layer 0)
- [ ] every id in `<satisfies-criteria>` appears in `<context><acceptance-criteria>`, and every
      criterion there is named by some `<test covers=>`
- [ ] every carried `<criterion>` is byte-identical to the source, id included
- [ ] `<requirement-level>` is the **highest** level among the criteria named, not the first
- [ ] No "TODO", "TBD", "...", or placeholders
- [ ] All file paths are complete (not "in the models folder")
- [ ] All class/function names are specified
- [ ] All fields have types specified
- [ ] Test cases have concrete values
- [ ] Verification commands are runnable
- [ ] Interface contracts have imports

## Output

Write each task as a separate XML file:
- Filename: `{task_id}-{slug}.xml` (e.g., `L1-001-project-model.xml`)
- Location: `{output_dir}/{layer}/`

**`{output_dir}` must be absolute. If it is not, stop and say so — do not resolve it yourself.**
You run in a fork, so your working directory is not the caller's, and any path you resolve here
is resolved against the wrong thing. That is finding F4: handed a relative directory, this skill
wrote an entire run's output into `skills/breakdown-generate-tasks/output/`, and the caller was
never told.

This is a backstop, not the guard. `/breakdown` resolves both paths through
`skills/breakdown/scripts/resolve-output.sh` in its Phase 1 and passes the absolute result down,
so a relative path arriving here means the caller skipped that step — which is worth reporting
rather than papering over.

After writing all tasks, output a summary:
```
Generated {N} tasks for layer {layer}:
- L1-001-project-model.xml
- L1-002-conversation-model.xml
...
```
