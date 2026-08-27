---
name: breakdown-review-tasks
description: Review generated tasks for quality and completeness. Called by /breakdown skill after task generation.
context: fork
agent: task-reviewer
model: claude-haiku-4-5
---

# Task Review

You are reviewing task files for quality and completeness.

## Input

| The caller provides | Always? |
|---|---|
| a path to the generated task files | yes |
| the layer name | yes |
| `{tasks_dir}/architecture.json` | **only when the project declares an `architecture.md`** |

## Review Criteria

### Critical (Must Pass)

Failure on ANY critical criterion means the task FAILS.

#### 1. Completeness
- All required XML sections present
- No empty sections
- No **unmarked** placeholder text: "TODO", "TBD", "...", "[fill in]", "etc."
  A `<gap>` carried from the PRD or CRD is not a placeholder — it is declared uncertainty,
  and it passes review while blocking execution. Marked and unmarked are different things,
  and banning both is what makes invention the compliant answer (item 29).

#### 2. Self-Containment
- All context is inline (no "see PRD" or "check docs")
- Interface contracts include imports
- Tech stack versions specified

#### 3. Interface Contracts
- Every `<interface>` has `name` and `type` attributes
- Complete type annotations
- Import statements included
- Return types specified

#### 4. Requirements Specificity
- Each requirement has unique `id`
- Exact file paths (not "in the models folder")
- Exact class/function names
- Exact field names and types
- No ambiguous terms: "appropriate", "suitable", "proper"

#### 5. Test Requirements
- Test file path specified
- Each test has unique `id`
- Setup steps are concrete
- Assertions are specific
- Concrete test values (not "some value")

#### 6. Verification Steps
- All steps are runnable commands
- Expected outcome for each step
- Commands use correct syntax

#### 7. File Scope
- At most `<task-limits>` files (excluding test), **defaulting to 3**. Checked mechanically by `check-rules.py`, not counted by eye
- Full relative paths from project root

### Warning (Note but Don't Fail)

#### 1. Context Quality
- PRD excerpt is focused (not entire PRD)
- Project structure is accurate

#### 2. Export Completeness
- All public interfaces exported
- Usable by downstream tasks

### 8. Project Rules (Critical, and mechanical)

**Run the enforcer; do not judge these by eye.** When the caller passed `architecture.json`,
for each generated task:

```bash
python {skill_dir}/../breakdown/scripts/check-rules.py \
    --rules {tasks_dir}/architecture.json --mode review --task {task_file}
```

- **Exit 0** — nothing refused. Any `REPORT` lines are `judgement` rules: include them in the
  review output as warnings, never as critical issues.
- **Exit 1** — every `REFUSED` line is a **critical issue**. Copy the rule's `reason` into the
  issue verbatim: it says what to do instead, and a rule number does not.
- **Exit 2** — the rules file could not be read. Stop and report it; do not review as though the
  project declared nothing.

**Only `import` and `content` fire here, and that is the point.** A task saying *"call the
billing service over HTTP"* under a rule banning cross-context calls is wrong **before anybody
writes a line**, and catching it costs nothing because no code exists yet. `edge` and `change`
cannot fire at review — there is no dependency graph and no diff until something is implemented
— so `execute-verify` is where those land.

`<task-limits>` is enforced by the same run. It replaces the hardcoded 3 in criterion 7: the
limit is `<task-limits default=>` with any scoped `<limit match= max-files=>` applied, and three
is the shipped default rather than a law.

**There is no per-task exemption, deliberately.** If a rule should not apply to a task, the rule
is edited — a component that can exempt itself makes the check advisory with extra steps.

## Review Process

For each task file in the directory:

1. **Parse XML**: Verify well-formed
2. **Check structure**: All required sections present
3. **Critical scan**: Check each critical criterion
4. **Warning scan**: Note any warnings
5. **Record result**: Pass/Fail with details

## Output Format

Write review results to `{layer}_review.json`:

```json
{
  "layer": "1-foundation",
  "reviewed_at": "2024-01-15T10:30:00Z",
  "summary": {
    "total": 5,
    "passed": 4,
    "failed": 1
  },
  "results": [
    {
      "task_id": "L1-001",
      "task_file": "L1-001-project-model.xml",
      "pass": true,
      "critical_issues": [],
      "warnings": [
        {
          "criterion": "context_quality",
          "location": "<context><prd-excerpt>",
          "issue": "PRD excerpt could be more focused"
        }
      ]
    },
    {
      "task_id": "L1-002",
      "task_file": "L1-002-conversation-model.xml",
      "pass": false,
      "critical_issues": [
        {
          "criterion": "completeness",
          "location": "<requirements><requirement id=\"3\">",
          "issue": "Contains placeholder 'TBD' for field type"
        },
        {
          "criterion": "test_requirements",
          "location": "<test-requirements><test id=\"2\">",
          "issue": "Missing concrete assertion value"
        }
      ],
      "warnings": []
    }
  ],
  "verdict": "FAILED",
  "action_required": "Fix L1-002: Remove placeholder, add concrete test values"
}
```

## Failure Patterns to Detect

### Placeholders
```
TODO
TBD
FIXME
[fill in]
[to be determined]
...
etc.
```

### Vague Requirements
```
"Create the appropriate model"
"Add necessary fields"
"Implement proper validation"
"Handle errors appropriately"
"Follow best practices"
```

### Missing Context
```
"As described in the PRD"
"Using the standard approach"
"Like other models"
"Following the existing pattern"
```

### Incomplete Interfaces
```
def some_function():  # Missing return type
    ...

class Model:  # Missing type annotations
    field = Column(...)  # Old SQLAlchemy style
```

## Review Output

After reviewing all tasks:

1. Write `{layer}_review.json` to the layer directory
2. Print summary to console:

```
Review Results for 1-foundation:
================================
Total tasks: 5
Passed: 4
Failed: 1

FAILED:
- L1-002: Contains placeholder 'TBD', missing test assertion

Action required before proceeding.
```

## Verdict Rules

- `PASSED`: All tasks pass all critical criteria
- `FAILED`: Any task fails any critical criterion

The layer can only proceed (create `.done`) if verdict is `PASSED`.
