---
name: crd
description: Orchestrates Change Request Document workflow. Manages context, captures changes, analyzes impact, and generates CRD files.
context: fork
model: claude-sonnet-5
user-invocable: true
---

# CRD Orchestration Skill

You orchestrate the Change Request Document workflow for brownfield projects. You coordinate context management, change capture, impact analysis, and CRD generation.

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--project <path>` | **Yes** | Path to target project |
| Description text | No | Initial change description |
| `--list` | No | List existing CRDs |
| `--status <slug>` | No | Check CRD status |

## Orchestration Flow

### Phase 1: Validation

1. Parse arguments, extract `--project` path
2. Verify path exists and is a git repository:
   ```bash
   git -C {project_path} rev-parse --git-dir
   ```
3. If invalid, report error and exit

### Phase 2: Context Management

Check for PROJECT.md at `{project_path}/PROJECT.md`:

**If exists:**

**Staleness is decided by the script, not by comparing the hash to HEAD:**

```bash
python {execute_skill_dir}/scripts/check-project-md.py {project_path} --status
```

| Exit | Meaning |
|------|---------|
| 0 | `stale=no` — the context is current; do nothing |
| 3 | `stale=yes` — it lists what changed; update the context |
| 1 | The recorded hash is unusable; a full re-investigation is the only option |

**Do not compare `last-context-hash` to `git rev-parse HEAD` yourself.** They are *supposed* to
differ by one commit: the hash records the commit whose code the context describes, and
PROJECT.md is written first and committed second, so the commit carrying the context is always
one ahead of the code it describes. A direct comparison therefore reports STALE immediately
after every successful update — and a `--full` re-investigation is the most expensive operation
in the CRD half of the toolchain. The script ignores changes to `PROJECT.md` itself, which is
exactly the difference.

Only on exit 3, invoke the context update:
```
/crd-context-update --project {project_path}
```

**If not exists:**
```
/crd-investigate --project {project_path} --depth medium
```

**Then measure it, on every one of the three ways in** — already current, updated, or freshly
investigated:

```bash
python {breakdown_skill_dir}/scripts/check-project-size.py {project_path}
```

`PROJECT.md` is generated from the codebase rather than written by a person, so it scales with
the code, and it is read whole because — unlike a PRD — there is nothing in it to split into one
prompt per feature (**P69**). **Exit 1** names its size against the budget and which sections
carry it. Stop and report it rather than reading it anyway: a file past the budget is read
truncated, and no consumer downstream can tell a truncated read from a complete one.

**It goes here rather than in the `If exists` branch above**, and the difference is not
cosmetic. The staleness check can send this phase through `/crd-context-update`, which **adds**
features and registry entries and removes none — so a measurement taken before that branch is a
measurement of a file that no longer exists by the time Phase 3 reads it. One invocation after
every branch covers all three.

### Phase 3: Handle List/Status Flags

**If `--list`:**
```bash
find {project_path}/docs/crd -name "*.md" -type f 2>/dev/null
```
Parse and display CRDs, then exit. **Show `<meta><priority>` as a column** — a change request's
MoSCoW tier (item 47). `--list` is the CRD path's only survey view, and a survey that cannot show
tiers is the reason the tier lives on the document at all.

**If `--status <slug>`:**
Read `{project_path}/docs/crd/{slug}.md`, extract `<meta><workflow>` — accepting `<status>`
from a CRD written before item 45 — display, exit.

### Phase 4: Change Capture

If description provided, use it. Otherwise prompt user.

Classify change type based on keywords:
- "add", "create", "new" → `feature-add`
- "change", "update", "modify" → `feature-modify`
- "remove", "delete", "drop" → `feature-remove`
- "refactor", "restructure" → `refactor`

Confirm type with user.

Capture:
- Summary (1-2 sentences)
- Motivation
- **`<meta><priority>`** — MoSCoW, for the change request as a whole. This is the document's only
  MoSCoW value; criterion priorities in Phase 6 are `P0|P1|P2` (item 47)

### Phase 5: Impact Analysis

Invoke impact analysis skill:
```
/crd-impact-analysis --project {project_path} --type {change_type} --description "{description}"
```

Present results to user for confirmation.

### Phase 6: Requirements

**Capture one list, not two.** There is no `<requirements>` element — item 46 retired it, because
an EARS criterion *is* a requirement and the split existed only to work around Given/When/Then
being a scenario format. Asking for requirements and then criteria for each gets the same content
twice under two ids.

Interactively capture criteria:
- `id`
- One EARS sentence, per [`core.md`](../../schema/core.md#2-acceptance-criteria)
- `pattern` — yours to assign, with the person who described the behaviour present
- `priority` — `P0`, `P1` or `P2`. **Write it in even when it is the `P1` default**, or
  *unassigned* and *deliberately P1* become indistinguishable

Ask for the unwanted case explicitly, or every criterion comes back `event-driven`.

**Then ask what is still open**, and record each as a `<gap>` with a `kind` and a `raised` date
(item 48). A deferred criterion is `kind="specification"` and bars `<workflow>ready</workflow>`;
core [§6](../../schema/core.md#6-gaps--what-a-document-knows-it-is-missing) has the other four
and says which block and which only warn.

### Phase 7: Generate CRD

Create directory if needed:
```bash
mkdir -p {project_path}/docs/crd
```

**Then check what would be lost, before writing** (item 48):
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-writable.py {project_path}/docs/crd/{slug}.md
```
Exit 1 is a refusal: show the user what would be replaced and stop. `--resume` is the only way
past and the caller has to state it. This path was documented as stateless and had F3's hole
exactly; it had simply not been caught by it yet.

Write the CRD at `{project_path}/docs/crd/{slug}.md` **against
[`references/crd-format.md`](references/crd-format.md)**, which defines every section, and which
cites [`core.md`](../../schema/core.md) for the elements shared with the PRD path.

The template is not repeated here. It was, and this file plus `commands/crd.md` plus
`crd-format.md` were three copies of one document shape that had already diverged over
`<scope>`, `<confidence>` and `<affected-contracts>`.

`<impact-analysis>` is written from what `/crd-impact-analysis` returned, verbatim where it is
structured. It is the only section this phase does not author, and `<scope>` and `<confidence>`
come with it — both are required, and neither is yours to invent if the analysis omitted them.

### Phase 8: Completion

Report success with next steps:
- Path to generated CRD
- **Every open `<gap>`, by id and kind.** Not a count, and not "some things are TBD" — a gap
  reported vaguely is one nobody returns to
- Command to run /breakdown
- Command to run /execute

## Sub-Skills Used

| Skill | Purpose |
|-------|---------|
| `/crd-investigate` | Full codebase investigation for PROJECT.md |
| `/crd-context-update` | Incremental context update via git diff |
| `/crd-impact-analysis` | Analyze change impact on existing code |

## Error Handling

| Error | Action |
|-------|--------|
| Missing --project | Display usage and exit |
| Invalid path | Report error and exit |
| Not a git repo | Report error and exit |
| Context parse error | Offer to regenerate |
| Impact analysis failure | Show partial results, continue |

## State Management

CRD workflow is stateless per invocation. All state is stored in:
- `PROJECT.md` - Context with hash
- `docs/crd/*.md` - CRD documents

No execute-state.json style tracking needed for CRD creation.
