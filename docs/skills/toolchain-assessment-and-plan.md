# Claude Code Toolchain — Assessment and Remediation Plan

**Status:** Phase 0 complete and measured; **item 4.11 done — skills now fork**; items 4.1–4.10 proposed
**Date:** 2026-08-10
**Subject:** the `prd` / `breakdown` / `execute` / `crd` skill toolchain
**Toolchain location:** repository root of `prd-claude-skills`, packaged as a Claude Code plugin
**Intended workflow:** load with `claude --plugin-dir <checkout>`, apply and test changes against a scratch project, then commit back.

> **Phase 0 has been run.** The three items previously marked *Unverified* are now
> measured, and one result was severe enough to become a **Blocking** finding (F13):
> no skill in this toolchain had ever forked. That is now **fixed** (item 4.11) and
> verified on real skills. Items 4.1 and 4.2 changed shape as a result, and open
> questions 1–3 are resolved. See §3.5 for results and §3.6 for method.
>
> A regression suite at `tests/` enforces these findings; run it before and after any
> change to frontmatter.

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
| **Measured** | Was unverified; has since been tested. Records a result, not a test to run |

---

## 2. Current state

### 2.1 Repository topology (as of 2026-08-10)

The toolchain and its documentation now live in **one** repository, packaged as a Claude
Code plugin rather than as a `.claude/` directory to be copied into each project:

```
prd-claude-skills\           ← single git repo, main, no remote
├── .claude-plugin\
│   └── plugin.json          ← name, version, author
├── skills\      (15)
├── agents\      (8)
├── commands\    (3)
├── docs\                    ← this document
├── README.md
└── LICENSE.md
```

Loaded with `claude --plugin-dir <checkout>`; everything resolves under the
`prd-claude-skills:` namespace. Verified: 15 skills, 8 agents and 3 commands all
register, against a control run with no `--plugin-dir` that registers none.

The application repository does not exist yet. When it does, the agreed layout is:

```
test-project\                ← workspace root, NOT a git repository
├── app\.git\                ← {project_path} for /execute
└── .worktrees\              ← default {project}/../.worktrees resolves here
```

Note that the toolchain no longer needs to sit inside the workspace at all, which
removes the nested-repository concern entirely for the toolchain itself. The table
below still applies to `app\` and `.worktrees\`.

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
| Converted to Claude Code plugin layout: `skills/`, `agents/`, `commands/` moved to the repository root as git renames, `.claude-plugin/plugin.json` added | `e0256cd` |
| Frontmatter added to the three command files — see F8, which turned out to be worse than described | `e0256cd` |
| `README.md` with upstream attribution, and `LICENSE.md` (MIT) | `e0256cd`, `0747b66` |
| **Phase 0 probes run** — 45 `claude -p` runs over three iterations; see §3.5 and §3.6 | — |
| Probe harness committed under `docs/skills/probes/`, with a guard refusing to generate inside this repository | — |
| Regression suite added at `tests/` — 17 static checks tied to finding IDs, known failures marked with the item that fixes them | `973604c` |
| **Item 4.11 done** — `allowed-tools` removed from all 15 skills; forking verified on real skills. **Skills fork for the first time** | — |

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

> Findings are numbered in discovery order. **F13 is the most severe item in this
> document** and is placed first for that reason.

#### F13 — `allowed-tools` silently disables `context: fork` on every skill — **RESOLVED**

> **Fixed by item 4.11.** The `allowed-tools` line was removed from all 15 skills, and
> forking was then verified on real skills rather than assumed:
> `breakdown-analyze-prd` and `crd-impact-analysis` both report
> `toolUseResult.status == "forked"`, with their declared `claude-haiku-4-5-20251001`
> appearing in `modelUsage` alongside the session model.
>
> `crd-impact-analysis` also confirms F6 on production code: it declares
> `claude-haiku-4-5-20251001` while its agent `crd-impact-analyzer` declares
> `claude-haiku-4-5`, and the **skill's** model is the one that ran.
>
> `tests/test_toolchain.py` now guards against the key returning. The description below
> is kept because the failure mode is subtle and worth being able to recognise again.

Found by the Phase 0 probes. `allowed-tools` is a **command** frontmatter key; the
equivalent key for a skill or an agent is `tools`. Fifteen of fifteen skills use the
command key in a skill file, and its presence stops `context: fork` from taking effect —
the skill degrades to plain text injected into the calling session.

Measured, deterministically:

| Skill frontmatter | Forked |
|---|---|
| `context: fork` alone | 3/3 |
| `context: fork` + `tools: Read, Glob, Grep` | 3/3 |
| `context: fork` + `tools: Read Glob Grep` | 3/3 |
| `context: fork` + `allowed-tools: Read, Glob, Grep` | **0/3** |
| `context: fork` + `allowed-tools: Read Glob Grep` | **0/3** |

Separator makes no difference; the key **name** is the whole issue. The corroborating
evidence is that the one published plugin command that loads correctly
(`claude-md-management`) declares `allowed-tools: Read, Edit, Glob` — as a *command* —
while the one published skill that restricts tools declares `tools: Read, Glob, Grep, Bash, Edit`.

**Why this outranks everything else in §3.3.** If nothing forks, then:

- `agent:` never fires — the six delegating skills run inline, not in their declared agent (U2)
- every skill's `model:` is inert — execution stays on whatever model the caller is using (F6, F7)
- the declared tool restrictions were never in force anyway (U1)

Concretely for implementation quality: `execute-batch` spawns `task-implementer`
(`claude-haiku-4-5`), which invokes `/execute-task`. Because `execute-task` cannot fork,
its `claude-sonnet-4-6` declaration never applies. **Haiku writes the code** — not by
decision, but as a side effect of a wrong key name.

**Fix:** rename `allowed-tools:` to `tools:` in all 15 skills, or delete the line. One
line per file, and it is a precondition for items 4.1 and 4.2 meaning anything.

**Caveat — do not over-read the fix.** Renaming restores forking; it does **not** buy
tool restriction. A forked skill declaring only `tools: Read, Glob, Grep` still wrote a
file in 3/3 runs. Treat `tools:` on a skill as documentation, not as a sandbox.

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

**Resolved (Phase 0) — in two parts.**

*Precedence, once forking works:* the **skill's** `model:` wins over the **agent's**. Probed
with an agent declaring `claude-haiku-4-5` invoking a forked skill declaring
`claude-opus-5`; `modelUsage` recorded `claude-opus-5[1m]`. With only one of the two
declared, that one is used; with neither, the fork inherits the session model.

*What actually happens today:* nothing forks (F13), so neither declaration applies and
`/execute-task` runs inline inside the Haiku `task-implementer`. The ambiguity was real,
but the answer is currently masked by a more basic defect. Fix F13 first, then this
precedence rule makes the tier decision in 4.2 enforceable.

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

**Status after Phase 0.** Both conflicts are currently inert, because F13 stops the
`agent:` key firing at all. They become live the moment F13 is fixed, and at that point
the F6 precedence rule applies: the skill's `model:` wins, so the agent's declaration is
what silently loses. That makes aligning the two more important after the fix than before
it — the conflict is currently hidden, not absent.

#### F8 — Commands carry no frontmatter

`commands/prd.md`, `commands/crd.md` and `commands/crd-context.md` begin directly with a `#`
heading. There is no `---` block, therefore:

- no `description` for the command picker
- **no `model` selector** — which is why `/prd` was absent from the model upgrade list; there is
  nowhere to put one
- no `argument-hint`
- no tool restriction

**Worse than described, and now fixed.** Frontmatter-less commands load fine when they are
*project* commands under `.claude/commands/`, which is how this was originally assessed. As
**plugin** commands they do not load at all: after the move to plugin layout, `/prd`, `/crd`
and `/crd-context` silently stopped registering. Verified both ways, each against a decoy
name that correctly reported absent.

`description` and `argument-hint` have been added to all three (`e0256cd`), restoring them.
The remaining part of F8 — whether these should become skills with `model:` selectors — is
still open under item 4.1.

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

### 3.5 Measured — Phase 0 results

The original suspicion behind U1 and U2 was "the key is probably ignored". Both turned out
to be wrong in a more useful way: the keys are not ignored, they are *the wrong keys*, and
one of them does active harm.

#### U1 — `allowed-tools`: not honoured, and actively harmful — **answered**

Two separate results:

1. **`allowed-tools` is a command key, not a skill key.** In a skill it does not restrict
   anything, and its presence disables `context: fork`. Promoted to **F13**, blocking.
2. **`tools:` is the correct skill key, but it does not restrict either.** A forked skill
   declaring `tools: Read, Glob, Grep` still performed a `Write` in 3/3 runs. Both comma and
   space separation parse without breaking the fork.

Practical consequence: there is **no working per-skill tool sandbox** to standardise on.
Item 4.1 should drop the tool-restriction goal rather than restate it in a different spelling.

#### U2 — `agent:` is honoured, but only together with `context: fork` — **answered**

`agent:` alone does nothing. `agent:` + `context: fork` genuinely forks into the declared
agent: the probe agent carried a private instruction the skill body never mentioned
(`MARKER-AGENT-7734`), and that instruction appeared in the output only in the forked run.
The agent's declared model ran in that fork.

So the original worry — "six skills are silently running inline" — is **correct in effect
but wrong in cause**. All six do declare `context: fork`; they fail because they also declare
`allowed-tools` (F13). Fixing F13 activates all six as designed.

Detection note for future testing: `isSidechain` stays `false` for forked skill execution, so
it is useless as a signal. Fork is visible as `toolUseResult.status == "forked"` on the `Skill`
tool result, and models actually used are visible in the `modelUsage` map of
`claude -p --output-format json`. Forked and subagent work never reaches the parent transcript.

#### U3 — Skill name resolution across scopes — **partly answered**

Plugin-provided skills, agents and commands are namespaced by plugin name — they register as
`prd-claude-skills:breakdown`, `prd-claude-skills:task-generator`, and so on. That side-steps
collisions with project or user scopes for anything coming from this plugin.

Still untested: precedence when a project `.claude/skills/` skill and a plugin skill share a
bare name. Not currently reachable, since the toolchain no longer installs into `.claude/`.

### 3.6 How Phase 0 was measured

45 runs of `claude -p --output-format json` against throwaway probe skills in a scratch
project, in three iterations:

| Iteration | Runs | Purpose |
|---|---|---|
| 1 | 16 | U1/U2/F6 **without** `context: fork` — established that unforked skills are plain text injection, so no execution-governing key can apply |
| 2 | 14 | Same questions **with** `context: fork` — the configuration the toolchain actually uses. Produced the F6 precedence answer |
| 3 | 15 | Reproducibility of the fork-breaking result: 5 frontmatter variants × 3 repetitions |

Design points worth preserving if these are ever re-run — harness behaviour changes between
Claude Code versions, so these answers have a shelf life:

- **Every probe carried a unique token in its body.** Without it, a skill that produced no
  output is indistinguishable from a skill that was never loaded, and the whole result is
  unfalsifiable.
- **Every question had a control arm** differing only in the key under test.
- **Availability checks used decoy names.** Asking a model "is X available" invites an echo;
  including names that do not exist proves the answer is a real lookup.
- **Model identity came from `modelUsage`, never from self-report.**

**The harness is committed under [`probes/`](probes/)** so these questions can be re-asked
cheaply. Frontmatter handling is harness behaviour rather than documented API, so the answers
above have a shelf life and should be re-measured on a newer Claude Code rather than assumed.

The harness generates into a temp directory and **refuses to run with a `--workdir` inside this
repository** — F4 is precisely "generated output leaked into the toolchain tree", and the first
version of that guard had an off-by-one that let it write here anyway. The raw results are not
committed: roughly 2.3 MB of transcripts across 375 files, only meaningful next to the Claude
Code build that produced them.

---

## 4. Remediation plan

Ordered so that blocking items and tests come first, and so that nothing later depends on an
unverified assumption.

### Phase 0 — Establish facts — **COMPLETE**

| # | Question | Answer |
|---|---|---|
| 0.1 | Is `allowed-tools` honoured? | **No.** Wrong key for a skill, and it disables `context: fork` → **F13** |
| 0.2 | Is `agent:` honoured? | **Yes, but only with `context: fork`** — which F13 currently prevents |
| 0.3 | Model precedence, skill vs agent | **The skill's `model:` wins.** Currently moot: nothing forks |

The single most important consequence was that **item 4.11 had to precede 4.1 and 4.2**,
since until skills forked every `model:` and `agent:` edit was a no-op. 4.11 is now done,
so those items change real behaviour and should be applied with that in mind.

### 4.1 Frontmatter and command→skill conversion

**Addresses F8** *(revised after Phase 0)*

Partly done. `description` and `argument-hint` are now present on all three command files, so
they register as plugin commands again. What remains is the question of whether they should be
**skills** rather than commands.

The original argument was "they have no frontmatter and therefore nowhere to put a `model:`".
That is now a live consideration rather than a hypothetical, because Phase 0 established that a
skill's `model:` genuinely takes effect — provided the skill also forks and does not carry
`allowed-tools`. A command has no equivalent lever.

So the case for converting is: `/prd` is the longest, most judgement-heavy interaction in the
toolchain, and as a command it will always run on whatever model the user happens to be using.
The case against is that these three are interactive, user-facing entry points, and forking
them into a separate context is not obviously desirable — a forked skill returns a summary to
the caller rather than conducting a conversation in it.

**Decision taken: `/prd` and `/crd` stay commands.** An interview that reports a summary back
to the caller is not the same thing as an interview, and forking is the price of a `model:`
selector. Both therefore run on whatever model the user is already using — which is the correct
trade for an interactive entry point, but should be a conscious one.

Still to decide: `/crd-context`, which is closer to batch work than to an interview and so may
be worth converting on the opposite reasoning.

Notes:

- Published skills overwhelmingly use **short aliases** — `model: opus`, `model: sonnet`,
  `model: inherit` — rather than pinned identifiers. Aliases track the current tier and never
  need another migration. Pin only where reproducibility genuinely matters.
- The former instruction to "apply the `allowed-tools` format decision across all skills" is
  superseded: there is no valid format. See item **4.11**.

### 4.2 Model assignments across skills *and* agents

**Addresses F5, F6, F7** *(unblocked — 4.11 is done)*

**These rows now change real behaviour.** Before 4.11 they were string edits with no
runtime effect. Skills fork today, so every `model:` here selects the model that
actually runs — verified live on `crd-impact-analysis`, whose declared
`claude-haiku-4-5-20251001` appeared in `modelUsage`.

Phase 0 also settles *how* to apply it: the skill's `model:` beats the agent's. Where a skill
and its agent disagree, the agent's line is the one that silently loses, so the alignment below
is not cosmetic.

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

**`task-implementer` deserves a separate decision.** Phase 0.3 settled the mechanism: once
`execute-task` forks, its own `model:` governs, overriding the `task-implementer` agent. So the
tier is chosen in the skill, and the agent's declaration is documentation at best.

Note what this means for the status quo. Today the emergent answer is *Haiku*, because
`execute-task` cannot fork and simply inherits the agent it was spawned into. Anyone who read
`model: claude-sonnet-4-6` in `execute-task` and assumed Sonnet was writing the code has been
wrong for the life of this toolchain. Make the choice explicit rather than emergent.

Haiku is defensible for mechanical layers (enums, configuration, scaffolding, CRUD). It is
riskier for:

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

### 4.11 Remove `allowed-tools` from all 15 skills — **DONE**

**Addresses F13, and unblocks 4.1 and 4.2**

> **Completed.** One line deleted per skill, 15 deletions, no other change. Verified
> behaviourally on two read-only skills (`breakdown-analyze-prd`, `crd-impact-analysis`),
> both of which now fork and run on their declared model. The two F13 regression checks
> have been promoted from expected-failure to permanent guards; the suite is now
> 13 pass / 4 known.
>
> The predicted fallout — skills that relied on mutating the caller's conversation state
> now returning a summary instead — has **not** been exercised. Both verified skills are
> leaf analysis skills. `execute-batch` and `execute-layer` orchestrate other skills and
> are the ones most likely to behave differently; neither can be tested without a real
> `/execute` run. **That is the outstanding risk from this item**, and it is best
> discovered on the item 5.1 fixture rather than on real work.

1. In every `skills/*/SKILL.md`, delete the `allowed-tools:` line. Renaming it to `tools:`
   is equally safe for forking, but is misleading: it restricts nothing (§3.5, U1). Deleting
   is the honest option.
2. Leave `tools:` on the **agent** files as they are — that is the correct key there.
3. Re-verify forking rather than assuming: invoke a skill and confirm
   `toolUseResult.status == "forked"` on the `Skill` tool result. `isSidechain` is not a
   valid signal.
4. Only then apply 4.2's model assignments, and expect real behaviour change — six skills
   will start running in their declared agents for the first time, on their declared models.

Expect this to surface latent issues rather than none: code that has only ever run inline in
the caller's context will now run in a fork that returns a summary. Any skill that relied on
mutating the caller's conversation state will change behaviour. `execute-batch` and
`execute-layer`, which orchestrate other skills, are the most likely to be affected.

---

## 5. Test plan

Run in a scratch project, not against `test-project`.

### 5.1 Fixture

A minimal PRD with two or three features — enough to exercise layer planning without a 60-file
generation cycle on every iteration.

### 5.2 Sequence

| # | Test | Passes when |
|---|---|---|
| 1 | ~~Phase 0 probes (U1, U2, F6 precedence)~~ | **Done** — see §3.5 |
| 1a | After 4.11, invoke each of the 15 skills | `toolUseResult.status == "forked"` on every one |
| 1b | After 4.11, invoke the six skills declaring `agent:` | `modelUsage` shows the declared model, not just the session model |
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
| ~~4.11~~ | ~~Remove `allowed-tools` — restores forking~~ **DONE** | ~~Blocking~~ | all 15 `skills/*/SKILL.md` |
| 4.1 | Command→skill conversion, frontmatter *(frontmatter done)* | Consistency | `commands/*.md` |
| 4.2 | Model assignments, skills and agents *(gated on 4.11)* | Correctness | all skills, all agents |
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

Resolved by Phase 0, kept for the record:

| | Question | Outcome |
|---|---|---|
| ~~1~~ | Model precedence (F6) | **Answered** — the skill's `model:` wins over the agent's |
| ~~2~~ | `allowed-tools` (U1) | **Answered** — wrong key, restricts nothing, breaks forking → F13 / item 4.11 |
| ~~3~~ | `agent:` honoured (U2) | **Answered** — yes, but only with `context: fork` |

Decided since:

| | Question | Decision |
|---|---|---|
| ~~4~~ | Should `/prd` and `/crd` become skills? | **No — they stay commands.** See 4.1 |
| ~~5~~ | Should the probe harness be committed? | **Yes** — [`probes/`](probes/) |

Still open:

1. **Per-layer model tiering** — worth it, or one global implementation model? Now a real
   decision rather than a hypothetical, since 4.11 makes `model:` take effect.
2. **Branch naming** — derive from HEAD, or keep `main` as a documented requirement?
3. **Should `/crd-context` become a skill?** Unlike `/prd` and `/crd` it is closer to batch work
   than to an interview, so the reasoning that kept those two as commands may invert here.
4. **Is any tool sandboxing available at all?** `tools:` on a skill does not restrict. If real
   confinement is wanted for `task-implementer`, it will have to come from somewhere other than
   skill frontmatter.
