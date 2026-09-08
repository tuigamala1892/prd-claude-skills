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

    <!-- One per feature this task descends from. Repeatable -- see Traceability below. -->
    <source-feature slug="save-link" moscow="must-have"
                    satisfies-criteria="1,4" requirement-level="P0"/>
  </meta>

  <context>
    <acceptance-criteria>
    <!-- The source feature's criteria, VERBATIM, with their original ids. Copy the element. -->
    <!-- Wrap each feature's criteria in <from-feature slug=> when the task has more than -->
    <!-- one <source-feature>; omit the wrapper when it has one. Ids repeat across features. -->
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

**Every task outside Layer 0 must name where it came from — and every feature it came from.**
Until item 16 a task named its feature nowhere at all, so attribution downstream was a string
match on `<name>`; until item 65 it could name only one, and a task covering two had to lie.

One `<source-feature>` per feature, each carrying that feature's own values:

| Attribute | Value | Where it comes from |
|---|---|---|
| `slug` | the feature's slug | the feature file you were given |
| `moscow` | `must-have`, `should-have`, `could-have` | `index.md`'s entry for **that** feature. **Never `wont-have`** — those features never reach you (item 13) |
| `satisfies-criteria` | comma-separated criterion ids | the criteria of **that** feature this task implements |
| `requirement-level` | `P0`, `P1` or `P2` | **the highest** `priority` among **that feature's** cited criteria |

```xml
<source-feature slug="save-link"  moscow="must-have"   satisfies-criteria="1"   requirement-level="P0"/>
<source-feature slug="tag-links"  moscow="should-have" satisfies-criteria="1,3" requirement-level="P1"/>
```

**Name every feature the task actually covers, and never narrow to the closest one.** An
integration task that exercises three features belongs to three features. Three live runs met this
case and produced three different workarounds — an invented `feature#id` notation, a task split to
suit the schema, and a silent narrowing to one feature (**P43**). The last is the worst, because
nothing downstream can tell it from a task that genuinely covers one: the coverage report, the
scope cross-check, `tasks-summary.md` and the gate all believe it, so dropping that feature from
scope silently takes the only end-to-end assertion of the others with it.

**Do not split a task to avoid naming two features.** Splitting is a decision about the work;
this element is a description of it. If the work is one task, say so and name both.

**`<priority>` is not one of them and must not be touched.** It is an integer meaning merge order
within the layer, and it has meant that since the beginning (**P3**). The tier goes in `<moscow>`
because that name was free.

**Layer 0 tasks carry none of these**, and that is the only exemption. They create directories,
config and a test harness — they descend from the tech stack, not from a feature, and inventing a
`<source-feature>` for them would put a false attribution into item 30's coverage check.

### Group the criteria by feature when there is more than one

Criterion ids are **per feature**: `save-link` criterion 1 and `tag-links` criterion 1 are two
different requirements with the same name. A task descending from more than one feature therefore
wraps each feature's carried criteria:

```xml
<acceptance-criteria>
  <from-feature slug="save-link">
    <criterion id="1" pattern="event-driven" priority="P0">...</criterion>
  </from-feature>
  <from-feature slug="tag-links">
    <criterion id="1" pattern="state-driven" priority="P1">...</criterion>
  </from-feature>
</acceptance-criteria>
```

- **Required when the task names more than one `<source-feature>`**, omitted when it names one.
- `<test covers=>` takes a matching `from-feature` attribute under the same rule:
  `<test id="2" covers="1" from-feature="tag-links">`.
- **The `<criterion>` element inside is still copied byte-for-byte.** That is why the
  qualification is a wrapper rather than a `feature#id` spelling inside the id — a run invented
  that, and it edits the copy item 17 requires to be verbatim.

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

**On the CRD path the source is `<contract kind="schema">`, and every word above still holds
(item 75).** A CRD has no features; it declares its schema changes in
`<impact-analysis><affected-contracts>`, and `analyze-prd` reads them into `data_models` marked
declared. Carry into `<context><data-model>` the entries **this task touches** — the same
*touches* rule the registry entries take, and for the same reason: a task that gets the whole
document's model back is a task nobody can size.

**Omit the element when the task touches none**, exactly as on the PRD path. And **do not infer
one from `<affected-files>`** — a filename is evidence that something changed, not a statement of
what the model is, and a model half-read and half-guessed is the failure this rule exists to
prevent.

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

## Where your verification commands will run

**Every `<verification>` step you write runs inside a git worktree of the target repository, and
until now nothing told you so.** The concrete failure was a step asserting
`pathlib.Path('.git').is_dir()`: false in a worktree, where `.git` is a *file*, so a correct
implementation failed verification for a reason with nothing to do with the task. That is **P42**,
and the class is every environment-shaped assertion invented here rather than measured.

The execution context, stated once. `execute-batch` creates the worktree before the implementing
agent exists, and every step runs there:

```text
cwd       the worktree root -- {worktree-dir}/{task-id} -- or <meta><cwd>, when the task declares one
.git      a FILE, the gitlink pointing back at the primary repository; never a directory
branch    `worktree-{task-id}`, created with -b by create-worktree.sh; never the base branch
tree      the base branch's content, freshly checked out: no build output, no installed
          dependencies, no untracked leftovers -- unless a step of this task creates them
siblings  the other tasks of this layer run at the same time in worktrees of their own and are
          NOT visible here; only layers already merged into the base branch are
```

`test -d .git`, `git branch --show-current` compared against `main`, `ls node_modules`, and any
path reaching into another task's output are each **false for a task that is otherwise perfect**.

### Assert the artefact, not the environment

**This is the durable half.** The five facts above can go out of date; the preference below cannot,
because it is about what a verification step is *for*. A step exists to decide whether this task
did its job, and every claim about the surrounding machinery is a claim you did not measure.

| Prefer | Over | Why |
|---|---|---|
| `python -c "import link_shelf"` | `test -d .git` | the first is a claim about this task's own output; the second is a claim about somebody else's execution model |
| `pytest tests/test_store.py -v` | `git log --oneline \| wc -l` | the tests are the criteria; the commit count is whatever the implementer's TDD cycle happened to produce |
| `test -f src/store.py` | `test "$(git branch --show-current)" = main` | the file is what the task promised; the branch name is decided three skills away and is never `main` here |

**A step you cannot phrase as a claim about a file this task creates, a command this task makes
runnable, or a behaviour one of its criteria names, is a step you should not write.** Where the
task genuinely needs an environment property -- a service on a port, a migration already applied
-- name in the same step what provides it, so a reviewer can tell a real dependency from a guess.

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

- [ ] a `<source-feature>` for **every** feature this task covers, each carrying `slug`,
      `moscow`, `satisfies-criteria` and `requirement-level` (every layer except Layer 0)
- [ ] every id in a `satisfies-criteria` appears among **that feature's** carried criteria, and
      every criterion carried is named by some `<test covers=>`
- [ ] more than one `<source-feature>` ⇒ every criterion is inside a `<from-feature slug=>` and
      every `<test>` carries `from-feature`
- [ ] every carried `<criterion>` is byte-identical to the source, id included
- [ ] `<requirement-level>` is the **highest** level among the criteria named, not the first
- [ ] No "TODO", "TBD", "...", or placeholders
- [ ] All file paths are complete (not "in the models folder")
- [ ] All class/function names are specified
- [ ] All fields have types specified
- [ ] Test cases have concrete values
- [ ] Verification commands are runnable
- [ ] Every verification step holds **inside the worktree**: none asserts `.git` is a
      directory, none names a branch, none reads output from another task in this layer
- [ ] Each step asserts this task's own artefact wherever one would do
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
