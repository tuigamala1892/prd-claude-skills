# Claude Code Toolchain — Assessment and Remediation Plan

**Status:** proposed, not yet implemented
**Date:** 2026-08-10
**Subject:** the `prd` / `breakdown` / `execute` / `crd` skill toolchain
**Toolchain location:** `.claude/` (separate git repository since 2026-08-10)
**Intended workflow:** copy the toolchain into a scratch project, apply and test these changes there, then bring the result back.

---

## 1. Scope and how to read this

Every finding below was verified against the files in this session — by parsing, grepping, or
running the behaviour in a scratch repository. Where something could **not** be verified, it is
labelled explicitly as unverified and carries a test to run rather than a fix to apply.

Findings are graded:

| Grade | Meaning |
|---|---|
| **Blocking** | `/execute` cannot complete, or will destroy data, in its current state |
| **Correctness** | Produces wrong or unpredictable results |
| **Consistency** | Two places disagree; behaviour depends on undocumented precedence |
| **Structural** | Works, but the design invites the above |
| **Unverified** | Suspected issue; needs a test before any change |

---

## 2. Current state

### 2.1 Repository topology (as of 2026-08-10)

```
test-project\           ← workspace root, NOT a git repository
├── .claude\.git\          ← toolchain repo   (2 commits, main, no remote)
└── docs\.git\             ← documentation repo (3 commits, main, no remote)
```

The application repository does not exist yet. When it does, the agreed layout is:

```
test-project\
├── .claude\.git\
├── docs\.git\
├── app\.git\              ← {project_path} for /execute
└── .worktrees\            ← default {project}/../.worktrees resolves here
```

Rationale: with the root not a repository, `.worktrees/` and each sub-repo sit outside every
other repository, so no repo needs to ignore another and no gitlink can form.

**Verified nested-repository behaviour** (tested in a scratch repo, not assumed):

| Situation | Outcome |
|---|---|
| Nested repo, parent does not ignore it | Parent records a **gitlink** (`160000`), git warns *"adding embedded git repository"*; a clone of the parent yields an empty directory |
| Nested repo, parent ignores the directory | Clean; child fully invisible to the parent |
| `git clean -xdf` in parent | Nested repo **survives** — git will not recurse into a directory containing `.git` |
| `git clean -xdff` in parent | Nested repo **destroyed** |

### 2.2 Work already completed

| Change | Commit |
|---|---|
| Documentation placed under version control | `docs` baseline |
| 94 bare `&` escaped so PRD files parse as XML | `docs` |
| Toolchain split into its own repository, history preserved via `git subtree split` | `.claude` |

The ampersand fix brought the PRD directory to **61 of 62 files parsing as well-formed XML**.
The single holdout is `docs/prd/test-project/what-next.md`, which is prose markdown rather
than XML — addressed by item **4.4** below.

### 2.3 Current model assignments

| File | Declared model |
|---|---|
| `commands/prd.md`, `crd.md`, `crd-context.md` | *none — no frontmatter at all* |
| `skills/breakdown`, `breakdown-generate-tasks`, `crd`, `crd-investigate`, `execute`, `execute-batch`, `execute-layer`, `execute-merge`, `execute-task` | `claude-sonnet-4-6` |
| `skills/breakdown-analyze-prd`, `breakdown-plan-layers`, `breakdown-review-tasks`, `crd-context-update`, `crd-impact-analysis`, `execute-verify` | `claude-haiku-4-5-20251001` |
| `agents/task-generator`, `crd-investigator` | `claude-sonnet-4-5` |
| `agents/task-implementer`, `task-reviewer`, `crd-context-updater`, `crd-impact-analyzer`, `verification-runner`, `project-context-finalizer` | `claude-haiku-4-5` |

---

## 3. Findings

### 3.1 Blocking

#### F1 — `/execute` cannot run against a repository with no remote

`skills/execute-task/SKILL.md:67` runs, before every task:

```bash
git pull origin main
```

With no remote configured this fails, and it is the first command of every task. **No task can
complete.** The plan is explicitly "no remote for now", so this blocks the entire pipeline
regardless of any other fix.

#### F2 — Layer 0's git initialisation is self-contradictory and destructive

Two facts that cannot both hold:

- `skills/execute/SKILL.md:95` — preflight asserts `test -d {project_path}/.git`, so `/execute`
  aborts unless the repository **already exists**.
- `skills/breakdown-generate-tasks/SKILL.md:308` — the generated Layer 0 task runs
  `rm -rf /path/to/new-project/.git (if exists)`.

So the preflight demands a repository, and the first task deletes it. Additionally
`skills/breakdown/SKILL.md:100,244` describes a `git init` Layer 0 task that can never usefully
run, because the preflight already required the repository to exist.

The `rm -rf` is the serious part: whatever `{project_path}` points at loses its git history.

### 3.2 Correctness

#### F3 — `/prd --resume` cannot find this PRD

`commands/prd.md:14` searches `docs/prd/*/what-next.md` for `<status>in-progress</status>`.
The status tag is present in `index.md`, not in `what-next.md`. Resume therefore finds nothing.

Worse, the no-arguments path starts a **new** PRD and Phase 8 writes to `docs/prd/[slug]/` —
so an unguarded session can overwrite an existing `index.md` and `what-next.md`.

#### F4 — Skill output can be written relative to the skill directory

`.claude/skills/breakdown-generate-tasks/output/2-backend/LAYER_SUMMARY.md` exists on disk and
contains generated tasks for an unrelated **"Voice PRD Generator"** project. The skill takes the
output directory as an input (`SKILL.md:21`), so nothing is hardcoded — but a previous
invocation resolved a relative path against the skill's own directory and wrote there.

Two consequences: generated artefacts silently pollute the toolchain repository, and the caller
has no indication their output went somewhere unexpected. Currently gitignored via
`skills/*/output/`, which contains the symptom but not the cause.

#### F5 — Model versions are stale, and no Haiku 5 exists

Current model identifiers:

| Tier | Current identifier | Note |
|---|---|---|
| Opus | `claude-opus-5` | |
| Sonnet | `claude-sonnet-5` | |
| Haiku | `claude-haiku-4-5` (full form `claude-haiku-4-5-20251001`) | **There is no Haiku 5** |

`claude-sonnet-4-6` and `claude-sonnet-4-5` are both superseded. Because these are Claude Code
frontmatter selectors rather than API calls, none of the API-level breaking changes
(`budget_tokens`, sampling parameters, assistant prefill) apply — this is a string change only.

### 3.3 Consistency

#### F6 — Two declarations govern the implementation model, precedence unknown

`skills/execute-batch/SKILL.md:68` spawns:

```
Task(subagent_type: "task-implementer", prompt: "Execute /execute-task --task-file ...")
```

- `agents/task-implementer.md` declares `model: claude-haiku-4-5`
- `skills/execute-task/SKILL.md` declares `model: claude-sonnet-4-6`

Nothing in the tree resolves which wins. **You cannot currently tell which model writes your
code.** This is the single most consequential ambiguity in the toolchain, because implementation
quality gates everything downstream.

Note this is a question about *ambiguity*, not about tier. Haiku is a defensible choice here —
the architecture is deliberately built for a cheap implementer: self-contained XML task specs,
TDD, an independent verifier, and a retry loop. The risk is concentrated in specific layers
(see item 4.2).

#### F7 — Agent models conflict with the skills that invoke them

Six skills delegate via an `agent:` key. Two disagree outright with the agent's own declaration:

| Skill | Skill model | Agent | Agent model | |
|---|---|---|---|---|
| `breakdown-generate-tasks` | `claude-sonnet-4-6` | `task-generator` | `claude-sonnet-4-5` | **conflict** |
| `crd-investigate` | `claude-sonnet-4-6` | `crd-investigator` | `claude-sonnet-4-5` | **conflict** |
| `breakdown-review-tasks` | `claude-haiku-4-5-20251001` | `task-reviewer` | `claude-haiku-4-5` | same model, two spellings |
| `crd-impact-analysis` | `claude-haiku-4-5-20251001` | `crd-impact-analyzer` | `claude-haiku-4-5` | same model, two spellings |
| `crd-context-update` | `claude-haiku-4-5-20251001` | `crd-context-updater` | `claude-haiku-4-5` | same model, two spellings |
| `execute-verify` | `claude-haiku-4-5-20251001` | `verification-runner` | `claude-haiku-4-5` | same model, two spellings |

Any model upgrade that touches only skills leaves the agents behind.

#### F8 — Commands carry no frontmatter

`commands/prd.md`, `commands/crd.md` and `commands/crd-context.md` begin directly with a `#`
heading. There is no `---` block, therefore:

- no `description` for the command picker
- **no `model` selector** — which is why `/prd` was absent from the model upgrade list; there is
  nowhere to put one
- no `argument-hint`
- no tool restriction

#### F9 — The documented `project_path` fallback is dead

`skills/execute/SKILL.md:77-79` resolves the project path as:

1. `--project-path` argument
2. `manifest.prd.project_path`
3. error

But `skills/breakdown/SKILL.md:175` specifies the manifest as containing PRD slug and name,
generation timestamp, layer completion status, and task inventory. **`project_path` is not
among them**, so step 2 can never fire and `--project-path` is effectively mandatory on every
invocation.

The safe half of this: there is no `cwd` fallback, so `/execute` cannot silently target the
workspace root.

### 3.4 Structural

#### F10 — No toolchain version is recorded in generated artefacts

`manifest.json` records no version of the tooling that produced it, and `what-next.md` has no
version marker either. Since `/prd --resume` greps `what-next.md` for a structure the skill
defines, a future skill version reading an older artefact fails silently rather than detecting
an incompatibility.

This matters more now that the toolchain is a separate, independently versioned repository
intended for reuse across projects.

#### F11 — Orphaned agent

`agents/project-context-finalizer.md` (219 lines) is referenced by nothing in `.claude/`.
Either wire it into `/execute`'s completion phase or delete it.

#### F12 — Worktree default depends on `{project_path}`'s parent

`skills/execute/SKILL.md:35` defaults `--worktree-dir` to `{project}/../.worktrees`. This is
correct for the agreed topology, but silently wrong if `{project_path}` is ever nested inside a
repository — worktrees would materialise inside that repository's working tree, one full
checkout per task.

### 3.5 Unverified — test before changing

#### U1 — `allowed-tools` format and whether it is honoured

Every skill declares tools space-separated, e.g. `allowed-tools: Read Glob Grep`.

Evidence gathered: across **82 published skills** in the local plugin cache, `allowed-tools`
appears **zero times**. That establishes the key is rarely used; it does *not* establish that
space separation is invalid. No change should be made until tested.

**Test:** create a scratch skill with `allowed-tools: Read` whose body attempts a `Write`. If
the write succeeds, the restriction is not being honoured in this form.

#### U2 — Whether the `agent:` key is honoured

Six skills declare `agent:`. Across the same 82 published skills, `agent:` appears **zero
times** (one uses `agents:`, plural). If the key is ignored, all six delegations are silently
running inline rather than in the declared subagent — which would also explain why the model
precedence in F6 is unclear.

**Test:** invoke a skill declaring `agent:` and confirm from the transcript whether a subagent
is actually spawned.

#### U3 — Skill name resolution across scopes

If a plugin-provided skill and a project skill share a name, the precedence between project
`.claude/skills/`, user `~/.claude/skills/`, and plugin scopes is not established. Not currently
a problem — becomes one as soon as a second source is in play. Prefixed names side-step it.

---

## 4. Remediation plan

Ordered so that blocking items and tests come first, and so that nothing later depends on an
unverified assumption.

### Phase 0 — Establish facts (do first)

| # | Action |
|---|---|
| 0.1 | Run test **U1** (`allowed-tools` honoured?) |
| 0.2 | Run test **U2** (`agent:` honoured?) |
| 0.3 | Determine model precedence for **F6**: does a skill's `model:` override the spawning agent's when the agent invokes the skill? |

Phase 0 outcomes determine the shape of 4.1 and 4.2. Do not start those until it is complete.

### 4.1 Frontmatter and command→skill conversion

**Addresses F8, U1**

Convert `commands/prd.md`, `crd.md` and `crd-context.md` to skills that retain slash
invocation. This is not a blanket "commands are deprecated" migration — the local plugin cache
shows commands and skills coexisting (15 command files alongside 82 skills). It applies to these
three specifically **because they currently have no frontmatter and therefore no model
selector**.

Evidence for the mechanism: 12 of the 82 published skills declare a `command:` key, e.g.
`command: /hub:board`, making a skill directly slash-invocable.

Target frontmatter:

```yaml
---
name: prd
description: <one line; this is what the model matches on for invocation>
command: /prd
argument-hint: "[--resume] [idea]"
model: claude-opus-5
---
```

Notes:

- Published skills overwhelmingly use **short aliases** — `model: opus`, `model: sonnet`,
  `model: inherit` — rather than pinned identifiers. Aliases track the current tier and never
  need another migration. Pin only where reproducibility genuinely matters.
- Apply the `allowed-tools` format decision from test 0.1 across all skills at the same time.

### 4.2 Model assignments across skills *and* agents

**Addresses F5, F6, F7**

Apply as one change so skills and agents cannot drift apart again.

| Component | Current | Proposed |
|---|---|---|
| `breakdown` | `claude-sonnet-4-6` | `claude-opus-5` |
| `breakdown-generate-tasks` | `claude-sonnet-4-6` | `claude-opus-5` |
| `agents/task-generator` | `claude-sonnet-4-5` | `claude-opus-5` — must match the skill |
| `crd`, `crd-investigate`, `execute`, `execute-batch`, `execute-layer`, `execute-merge`, `execute-task` | `claude-sonnet-4-6` | `claude-sonnet-5` |
| `agents/crd-investigator` | `claude-sonnet-4-5` | `claude-sonnet-5` — must match the skill |
| All Haiku-tier skills | `claude-haiku-4-5-20251001` | `claude-haiku-4-5` — alias, one spelling |
| All Haiku-tier agents | `claude-haiku-4-5` | unchanged |

Rationale for Opus on task generation: task quality gates everything `/execute` does, and a
defective task file costs far more than the token difference.

**`task-implementer` deserves a separate decision.** Whatever Phase 0.3 establishes about
precedence, make the choice explicit rather than emergent. Haiku is defensible for mechanical
layers (enums, configuration, scaffolding, CRUD). It is riskier for:

- the data-model layer — multi-level single-table inheritance (`Place → Lodging → Hotel`, see
  ADR-001) is exactly where a wrong discriminator map produces code that compiles, passes a
  shallow test, and is silently wrong
- the Discovery Search pipeline

Note also that the verifier is itself Haiku and only runs the commands the task XML specifies —
so a weak `<verification>` block is checked weakly. Consider per-layer model tiering rather than
one global choice, and treat retry economics as part of the calculation: enough failed
verify→retry cycles cost more than a stronger model would have.

### 4.3 Resume detection

**Addresses F3**

Three changes to the converted `prd` skill:

1. **Detect an existing PRD without `--resume`.** Glob `docs/prd/*/` on entry regardless of
   arguments. If a PRD directory exists, present it and ask before starting a new one.
2. **Look in the right place.** Accept the status marker from either `what-next.md` or
   `index.md`, so existing PRDs authored before the template change are still found.
3. **Guard the write path.** Phase 8 writes to `docs/prd/[slug]/`; refuse to overwrite an
   existing `index.md` or `what-next.md` without explicit confirmation.

Item 4.4 makes `what-next.md` carry the status marker natively, so (2) can be simplified once
existing artefacts are migrated.

### 4.4 `what-next.md` template with toolchain-version header

**Addresses F3, F10, and the last XML parse failure**

The current file is prose markdown and diverges from the skill's Phase 8 specification, which
calls for `<status>`, `<tbd-items>`, `<next-steps>` and `<session-notes>`. The divergence
produced a **better** artefact — task-generation order, spikes, infrastructure, data model and
risks are all content the template lacks — so the fix is a hybrid, not a conversion back.

Making it XML also brings the PRD directory to 62/62 parsing.

```xml
<what-next>
  <meta>
    <prd-slug>test-project</prd-slug>
    <status>in-progress</status>          <!-- what /prd --resume greps for -->
    <last-updated>2026-08-10</last-updated>
    <next-command>/breakdown</next-command>
    <toolchain-version>2.0.0</toolchain-version>   <!-- see 4.5 -->
  </meta>

  <tbd-items>
    <item id="1" blocking="true">...</item>
  </tbd-items>

  <next-steps>
    <!-- markdown prose preserved verbatim: task-generation order, spikes,
         infrastructure, data model, UX wireframes -->
  </next-steps>

  <risks>...</risks>
  <session-notes>...</session-notes>
</what-next>
```

### 4.5 Toolchain version stamping

**Addresses F10**

1. Introduce a version for the toolchain repository (a `VERSION` file or a git tag).
2. Have `/prd` write `<toolchain-version>` into `what-next.md`.
3. Have `/breakdown` write `toolchain_version` into `manifest.json`.
4. On resume or on `/execute`, compare the recorded version against the running toolchain and
   warn — or refuse — on a known-incompatible mismatch.

This is what makes independent versioning safe. Without it, a toolchain upgrade silently
misreads artefacts produced by an earlier version, in any project.

### 4.6 Absolute output path guard

**Addresses F4**

In `breakdown` and `breakdown-generate-tasks`:

1. Require `--output-dir` to be an absolute path; reject relative paths with a clear error.
2. Refuse to write anywhere under the toolchain's own directory.
3. Echo the resolved absolute output path before writing, so a wrong target is visible
   immediately.

Then delete the stray `skills/breakdown-generate-tasks/output/` tree, which is currently only
gitignored.

### 4.7 Layer 0 git contradictions

**Addresses F2**

1. **Remove `rm -rf {output-dir}/.git` from the Layer 0 template** (`breakdown-generate-tasks`
   line 308). Removing template `.git` is only meaningful when scaffolding from a cloned
   template; it must never run against a caller-supplied path.
2. **Resolve the init-versus-preflight contradiction.** Either:
   - *(recommended)* drop the `git init` task and document that `{project_path}` must be an
     existing repository, matching what the preflight already enforces; or
   - allow `/execute` to create the repository when absent, and relax the preflight accordingly.

   Do not leave both behaviours declared.
3. **Add a guard against operating on the wrong repository.** Refuse if `{project_path}`
   contains `docs/prd/` or is the toolchain repository. Cheap insurance against a mistyped
   argument destroying the wrong `.git`.

### 4.8 `git pull origin main` guard

**Addresses F1**

In `execute-task`, replace the unconditional pull with a conditional:

```bash
git remote get-url origin >/dev/null 2>&1 && git pull origin main || true
```

Also confirm the branch name is not hardcoded elsewhere — `execute-merge` refers to `main` in
several places (`SKILL.md:57,83,84`). Derive it from the repository's actual HEAD, or make it a
documented parameter.

### 4.9 Manifest completeness

**Addresses F9**

Add to `breakdown`'s `manifest.json` specification:

- `prd.project_path` — so `/execute`'s documented fallback actually works
- `toolchain_version` — per item 4.5

### 4.10 Orphaned agent

**Addresses F11**

Decide `agents/project-context-finalizer.md`: wire it into `/execute`'s completion phase, or
delete it. Leaving 219 unreferenced lines in a reusable toolchain is a maintenance liability.

---

## 5. Test plan

Run in a scratch project, not against `test-project`.

### 5.1 Fixture

A minimal PRD with two or three features — enough to exercise layer planning without a 60-file
generation cycle on every iteration.

### 5.2 Sequence

| # | Test | Passes when |
|---|---|---|
| 1 | Phase 0 probes (U1, U2, F6 precedence) | Behaviour of `allowed-tools`, `agent:` and model precedence is documented |
| 2 | `/prd` on a fresh directory | PRD written; `what-next.md` is valid XML with `<status>` and `<toolchain-version>` |
| 3 | `/prd` again with no arguments | Existing PRD detected and offered; nothing overwritten |
| 4 | `/prd --resume` | Finds the PRD via `what-next.md` |
| 5 | `/breakdown` with a relative `--output-dir` | Rejected with a clear error |
| 6 | `/breakdown` with an absolute `--output-dir` | Tasks land there; nothing written into the toolchain tree; manifest carries `project_path` and `toolchain_version` |
| 7 | `/execute` against a repo with **no remote** | Runs; no `git pull` failure |
| 8 | `/execute` against a path containing `docs/prd/` | Refused |
| 9 | Full `/execute` run on the fixture | Tasks implement, verify and merge; no `.git` deleted anywhere |
| 10 | Artefact version mismatch | Toolchain warns rather than misreading |

### 5.3 Regression check against this project

Before adopting: run the updated `/prd --resume` against a **copy** of
`docs/prd/test-project/` and confirm it detects the existing PRD. Then migrate the real
`what-next.md` to the new template and confirm 62/62 XML parsing:

```python
import xml.etree.ElementTree as ET, glob
files = sorted(glob.glob('docs/prd/test-project/**/*.md', recursive=True))
bad = [p for p in files if not _parses(p)]
```

---

## 6. Summary table

| # | Item | Grade | Files |
|---|---|---|---|
| 4.1 | Command→skill conversion, frontmatter | Consistency | `commands/*.md` → `skills/` |
| 4.2 | Model assignments, skills and agents | Correctness | all skills, all agents |
| 4.3 | Resume detection and overwrite guard | Correctness | `prd` |
| 4.4 | `what-next.md` template | Correctness | `prd`, existing artefacts |
| 4.5 | Toolchain version stamping | Structural | `prd`, `breakdown`, `execute` |
| 4.6 | Absolute output path guard | Correctness | `breakdown`, `breakdown-generate-tasks` |
| 4.7 | Layer 0 git contradictions | **Blocking** | `breakdown-generate-tasks`, `execute` |
| 4.8 | `git pull origin main` guard | **Blocking** | `execute-task`, `execute-merge` |
| 4.9 | Manifest completeness | Consistency | `breakdown` |
| 4.10 | Orphaned agent | Structural | `agents/project-context-finalizer.md` |

---

## 7. Open questions

1. **Model precedence** (F6) — blocks the `task-implementer` tier decision.
2. **`allowed-tools`** (U1) — blocks the frontmatter standardisation.
3. **`agent:` honoured** (U2) — if not, six skills are not running as designed.
4. **Per-layer model tiering** — worth it, or one global implementation model?
5. **Branch naming** — derive from HEAD, or keep `main` as a documented requirement?
