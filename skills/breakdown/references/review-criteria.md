# Task Review Criteria

Use this checklist to validate generated task files.

## Critical Criteria (Must Pass)

Failure on ANY critical criterion means the task must be regenerated.

### 1. Completeness

- [ ] All required XML sections present (`meta`, `context`, `dependencies`, `objective`, `requirements`, `test-requirements`, `files-to-create`, `verification`, `exports`)
  - **`test-requirements` is required unless the project declares `<testing default="none">`** in `architecture.md`. Read the declaration before failing a
    task for its absence: this criterion and `task-format-spec.md` are two of the three
    places the TDD mandate actually lives, and a project that switched TDD off would
    otherwise have every task fail here and never reach execution. Its *presence* when
    `default="none"` is not a failure — only its emptiness is.
- [ ] No empty sections
- [ ] No **unmarked** placeholder text: "TODO", "TBD", "...", "[fill in]", "etc."
  - **A `<gap>` carried from the source document is not a placeholder.** It is an author's
    declared uncertainty, with a `kind`, an `id` and a date, and it *passes* review and
    *blocks* execution — see [core §6](../../../schema/core.md#6-gaps--what-a-document-knows-it-is-missing).
    Banning marked uncertainty outright is precisely what makes invention the compliant
    answer: an author who cannot write "we have not decided this" writes something
    plausible instead, and nothing downstream can tell the difference.
  - Unmarked vagueness keeps failing exactly as it did. The distinction is whether
    somebody **declared** the gap, not whether the task admits to one.
- [ ] No "see above", "as mentioned", or references to other parts of the document

### 2. Self-Containment

- [ ] All necessary context is inline (not "see PRD" or "check docs")
- [ ] Interface contracts include all imports
- [ ] Tech stack versions specified
- [ ] No assumptions about "obvious" knowledge

### 3. Interface Contracts

- [ ] Every `<interface>` has `name` and `type` attributes
- [ ] Complete type annotations on all signatures
- [ ] Import statements included
- [ ] Return types specified
- [ ] Docstrings for functions (at minimum)

### 4. Requirements Specificity

- [ ] Each requirement has unique `id`
- [ ] Exact file paths specified (not "in the models folder")
- [ ] Exact class/function names specified
- [ ] Exact field names and types specified
- [ ] No ambiguous terms: "appropriate", "suitable", "proper", "good"

### 5. Test Requirements

- [ ] Test file path specified
- [ ] Each test has unique `id`
- [ ] Setup steps are concrete
- [ ] Assertions are specific (not "should work correctly")
- [ ] Uses concrete test values (not "some value")

### 6. Verification Steps

- [ ] All steps are runnable commands
- [ ] Expected outcome specified for each step
- [ ] Commands use correct syntax for the tech stack
- [ ] Steps are in executable order
- [ ] **Every step holds inside a git worktree.** That is where `/execute` runs them: cwd is the
      worktree root, `.git` is a *file* rather than a directory, the branch is
      `worktree-{task-id}` and never the base branch, and the other tasks of this layer are not
      merged in. A step asserting any of those otherwise fails a task that is correct — which is
      **P42**, found by a live run on `Path('.git').is_dir()`.
- [ ] **Each step asserts the task's own artefact where one would do.** `import link_shelf` is a
      claim about this task's output; `test -d .git` is a claim about somebody else's execution
      model. Flag the second wherever the first is available, and where the task genuinely
      depends on an environment property, the step must name what provides it.

### 7. File Scope

- [ ] Maximum 3 files to create (excluding test file)
- [ ] Files listed in creation order
- [ ] Full relative paths from project root

## Warning Criteria (Should Pass)

Warnings don't block, but should be noted for improvement.

### 1. Context Quality

- [ ] PRD excerpt is relevant (not entire PRD copied)
- [ ] Tech stack matches PRD specification
- [ ] Project structure reflects actual layout

### 2. Dependency Clarity

- [ ] Only necessary dependencies listed
- [ ] Dependency purpose is clear
- [ ] No unused imports in interface contracts

### 3. Objective Clarity

- [ ] 1-3 sentences (not a paragraph)
- [ ] Focuses on WHAT, not HOW
- [ ] Clear value statement

### 4. Export Completeness

- [ ] All public interfaces exported
- [ ] Interfaces usable by downstream tasks
- [ ] No internal implementation details exposed

## Review Output Format

```json
{
  "task_id": "L1-001",
  "task_name": "Create Project Model",
  "pass": false,
  "critical_issues": [
    {
      "criterion": "completeness",
      "location": "<requirements>",
      "issue": "Requirement 3 contains placeholder 'TBD'"
    }
  ],
  "warnings": [
    {
      "criterion": "context_quality",
      "location": "<context><prd-excerpt>",
      "issue": "PRD excerpt is 500+ lines, consider trimming"
    }
  ],
  "suggestions": [
    "Consider splitting into two tasks - model + migration separate"
  ]
}
```

## Review Process

1. **Parse XML**: Verify well-formed XML
2. **Check structure**: All required sections present
3. **Critical scan**: Check each critical criterion
4. **Warning scan**: Check each warning criterion
5. **Generate report**: Output JSON with findings
6. **Verdict**: `pass: true` only if 0 critical issues

## Common Issues

### Placeholder Patterns to Flag

**Inside a `<gap>` element, none of these are flagged.** The list below finds vagueness
nobody owned up to; a gap is vagueness somebody signed and dated. Scope the scan to the
task text outside `<gaps>`, or the mechanism item 29 built to make honesty possible becomes
the thing that fails review.

```
TODO
TBD
FIXME
[fill in]
[to be determined]
...
etc.
and so on
as needed
appropriate
suitable
proper
relevant
necessary (without specifics)
```

### Vague Requirement Patterns

```
"Create the appropriate model"          → Specify exact class name
"Add necessary fields"                  → List exact fields with types
"Implement proper validation"           → Specify validation rules
"Store the data"                        → Specify table/collection name
"Handle errors appropriately"           → Specify which errors, how
"Follow best practices"                 → Specify exact pattern/approach
```

### Environment-Shaped Verification Steps

Each of these fails inside a worktree, or passes for a reason unrelated to the task. The
right-hand column is the same check re-aimed at what the task actually produced.

```
"test -d .git"                          → test -f the file this task creates
"git branch --show-current = main"      → run the task's own test command
"git log --oneline | wc -l" ≥ N         → assert the behaviour the commits were for
"ls node_modules" / "ls .venv"          → run the command those install, or install it in a step
"test -f ../L1-002/out.json"            → depend on an earlier LAYER, never a sibling task
```

**The general form is the review question, not the list.** The list is what one live run
produced; the class is every assertion about the machinery around the task rather than about the
task.

### Missing Context Patterns

```
"As described in the PRD"               → Copy relevant PRD text inline
"Using the standard approach"           → Specify the approach
"Like other models in the project"      → Copy the pattern inline
"Following the existing pattern"        → Document the pattern
```
