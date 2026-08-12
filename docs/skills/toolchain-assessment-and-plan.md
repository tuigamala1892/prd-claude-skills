# Claude Code Toolchain — Assessment and Remediation Plan

**Status:** Five end-to-end runs, and run 5 found the thing underneath all of it: **`execute-task/SKILL.md` has never once been loaded.** Task agents are dispatched with a *prompt* that says "using the /execute-task skill", which is text, not an invocation — so the file describing worktree creation, TDD and verification has never been read by anything, in any run (**F20**). The agent that does the work, `task-implementer.md`, is written on the assumption that its worktree already exists. That is why no fix aimed at the worktree command has ever changed the outcome. Previously: F1/F2/F13 fixed; F14 **withdrawn** (a harness artefact); **F17 fixed and verified** — synchronous dispatch restored the orchestration chain, and run 4 produced 18 task agents and one commit per task where run 3 produced one commit for all twenty. The fix exposed the next layer: **F18** (the `git worktree add` command is retyped from prose and drifts — 6 of 6 attempts dropped `-b`, making them always fatal) and **F19, blocking and destructive** (on failure the agents improvise upward and `git init` a repository *outside* `{project_path}`, swallowing the docs tree and recording the real project as a gitlink). F15 and F16 stand. Items 4.13 and 4.14 open
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
> Items **4.7** and **4.8** have since been completed too, so F1, F2 and F13 are resolved and
> confirmed under a real run. **The pipeline has been run end to end three times (§5.2), and
> the third run is the one to read.** `/execute` produced a working application with 91
> passing tests in 17 minutes — as a single commit for twenty tasks, with no worktrees, no
> branches and no merges, because the forked orchestrators dispatch their children in the
> background and then return immediately (**F17**). Add to that: documented guards are ignored
> (F15) and the state file invents its own numbers (F16).
>
> **Two lessons generalise past these findings, both learned the hard way here.** A negative
> result from an end-to-end run is only as trustworthy as the harness's permissions — run 1
> was misread for a day because subagents had been denied `Bash`. And a forked skill's parent
> transcript records almost nothing, because the work happens in `<sid>/subagents/`; capturing
> only the parent yields a file with zero tool calls in it, which reads as "nothing ran". The
> harness now captures both. Check the subagent transcripts before writing up any §5.2 failure
> as a toolchain defect.
>
> A regression suite at `tests/` enforces every one of these fixes; run it before and
> after any change to skill frontmatter or git commands.

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
| **Item 4.8 done** — remote operations guarded; branch name parameterised as `--base-branch`, defaulting to repository HEAD | — |
| **Item 4.7 done** — Layer 0 no longer deletes the target's `.git` or contradicts the preflight. The wrong-repository guard was added but **does not work in practice** — see F15 | — |
| §5.1 fixture built at `tests/fixture/`, §5.2 sequence run end to end | `3972064`, `a623d83` |
| **First full `/execute` ever run** — completed in 83 min; surfaced F15 and F16, and F14 which was later withdrawn | — |

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

> Findings are numbered in discovery order, and listed here worst first rather than in
> numeric order.
>
> **F13 remains the most severe thing this assessment found** — no skill in the toolchain had
> ever forked, so no declared model or agent had ever applied — but it is fixed, so **F17
> leads the open findings**.
>
> The path from one to the other is worth following, because the first two steps were both
> wrong and both convincing. F13's fix made skills fork for the first time. Run 1 appeared to
> show that forking had destroyed worktree isolation (F14) — a tidy story, and false: the
> harness had denied subagents `Bash`. Run 2, with permissions granted, showed isolation
> working perfectly in layer 2 and absent in layers 0–1, which read as a per-layer defect.
> Run 3 was the first to complete, and found the actual cause: a forked skill dispatches its
> child in the background, says it is waiting, and returns immediately — because ending its
> turn *is* its return (F17). Three runs, three stories, and only the last one survives.

#### F20 — `execute-task/SKILL.md` has never been loaded; the task agent assumes a worktree it never gets

Found by §5.2 run 5. **Blocking, and it supersedes the diagnosis behind F18, F19 and item
4.14.** Everything below follows from one measurement:

| | |
|---|---|
| Task agents dispatched in run 5 | 19 |
| That invoked the `execute-task` skill | **0** |
| Skills actually invoked in the run | `execute-batch` ×17, `execute-merge` ×14, `execute-layer` ×4 |

`execute-batch` dispatches each task through the **Agent** tool with a prompt that opens:

> *"You are executing task L1-004 using the /execute-task skill. Execute the following
> command: `/execute-task --task-file …`"*

Inside an agent prompt, `/execute-task` is **text**. It is not a command, it does not resolve,
and nothing loads the skill. The other three skills are invoked properly because their callers
use the `Skill` tool; this one is described rather than invoked. Every task agent has therefore
been implementing tasks straight from the task XML, with no procedure at all.

**So `execute-task/SKILL.md` is dead code.** Its worktree creation, its TDD sequence, its
verification hand-off, its commit format, its retry handling — none of it has ever executed, in
any of the five runs. Item 4.8's `git fetch` guard and item 4.14's script live in that file too,
which is why neither changed anything.

**And the agent that does run assumes the missing step already happened.**
`agents/task-implementer.md` opens with *"You work in an isolated git worktree"* — stated as a
fact about its environment, not a task — and its worked example says:

```
2. Change to worktree:
   cd ../.worktrees/L1-001/
```

`cd` into a worktree, not `git worktree add`. The agent expects to be *placed* in one. Nothing
places it there. So it does the only thing it can: works where it stands, in the main tree.

**They are not duplicates, which is the part that makes this fixable.** The two files are the
toolchain's standard skill/agent split — *procedure* and *persona* — and their section headings
show it plainly:

| `execute-task/SKILL.md` (procedure) | `task-implementer.md` (persona) |
|---|---|
| Input Arguments | Core Principles |
| Execution Flow — worktree, TDD, commit, verify | What You Must NEVER Do |
| Constraints, Error Recovery | Quality Standards, Example Workflow |

One is a runbook, the other a character brief. Six other skills bind the two halves with an
`agent:` line in frontmatter — `execute-verify` → `verification-runner`,
`crd-investigate` → `crd-investigator`, and four more. **`execute-task` is the only one of the
seven that omits `agent:`**, so its halves were never joined, and `execute-batch` reaches past
it to the agent with `subagent_type: "task-implementer"` — the only use of `subagent_type` in
the toolchain.

**Why this one pair broke and the other six did not** is worth recording, because it is a
design limit rather than an oversight. Every other pair is invoked *once*, by one caller, so a
`Skill` call suffices. `execute-task` must run *N times in parallel*, and a `Skill` invocation
cannot fan out — parallel dispatch requires the Agent tool, and the Agent tool takes an
**agent**, not a skill. The pattern has no way to express "run this skill N times in parallel",
so the author reached for the only thing that could, and the skill was stranded.

The consequence is that only the persona half is guaranteed to load. Anything that must be read
has to live in the agent definition.

**This re-reads the earlier findings rather than replacing them:**

- **F18** (the `-b` flag never survived) is a true observation with the wrong cause attached.
  The agents were not paraphrasing an instruction badly — they had never seen one, and were
  improvising `git worktree add` from general knowledge. Improvisation is why `-b` was missing.
- **F19** recurred in run 5 despite 4.14's guards, for the same reason: the guards are in a
  file nobody reads. One `git init` at the workspace root, one stray repository again.
- **F6's model precedence is moot on this path.** `execute-task` declares
  `claude-sonnet-4-6`; the work has always run on `task-implementer`'s `claude-haiku-4-5`,
  because the skill never loads to contest it.

**One task did get a worktree** — `L4-002`, hand-rolled with `git worktree add .worktrees/L4-002
-b L4-002` from the workspace root, and merged as `b979869`. Improvisation occasionally lands.
That is not isolation, it is luck.

**The fix is the one item 4.12 option 1 already described**, now on much firmer ground: the
worktree must be created *before* the agent is dispatched, by the caller, and its path passed
in — which is exactly the world `task-implementer.md` is already written for. Nothing needs to
be persuaded to call a script; `execute-batch` creates the worktree, then hands over. See item
**4.15**.

#### F19 — `/execute` creates a git repository outside `{project_path}`

Found by §5.2 run 4. **Blocking, and the first finding in this document that damages
something outside the target directory.**

When `git worktree add` failed (F18), task agents did not stop. They improvised upward: `cd`
to the workspace root and try again there. Something in that sequence ran `git init`, and the
result is a repository at the workspace root — the one place §2.1 states must *not* be a
repository, because that is the whole reason the topology was chosen.

What it contains:

```
$ git -C <workspace-root> log --oneline
4628944 Merge L2-004: Export router from app/api package
2c5ef51 Merge L2-002: GET /links endpoint with tag filtering
3bd2225 Add comprehensive tests for GET /links endpoint
eed0151 Initial commit

$ git -C <workspace-root> ls-files -s app
160000 abf60608dc585701fdf5817b9d95868dbd9ddc01 0    app
```

Three things are wrong at once:

1. **A repository exists where the design forbids one.** Created at 09:34 during the run;
   `setup_fixture.py` only ever initialises `app/`.
2. **`app/` is recorded as a gitlink** (mode `160000`). This is precisely the failure the
   §2.1 table documents: cloning the outer repository yields an **empty** `app/`. The real
   project has been swallowed by reference.
3. **39 files under `docs/` were committed into it** — the PRD and the generated task tree,
   which live in a different repository entirely and are no business of `/execute`'s.

Merges then happened *in the stray repository* rather than in the target, which is why run 4
shows `Merge L2-002` and `Merge L2-004` commits that are absent from `app/`'s history.

The preflight already refuses to *target* a docs tree or the toolchain (item 4.7). It has no
opinion about the target's **parent**, because nothing anticipated an agent walking upward
after a failure. Prose guards constrain where `/execute` is pointed; nothing constrains where
it wanders.

Addressed by item **4.14**, and this is the strongest argument yet for **4.13**: a guard that
only exists as prose cannot stop an improvisation it never contemplated.

#### F18 — the `git worktree add` command is retyped from prose, and drifts

Found by §5.2 run 4, and the direct cause of F19.

`execute-task/SKILL.md:76` documents the command correctly:

```bash
git worktree add -b worktree-{task_id} {worktree_dir}/{task_id} {base_branch}
```

Not one agent ran it. Across the whole run:

| | |
|---|---|
| Task agents dispatched | 18 |
| Agents that attempted `git worktree add` | **6** |
| Attempts including the `-b` flag | **0** |
| Attempts run from the wrong directory | 5 of 6 |
| Attempts that succeeded | **0** |

What they ran instead:

```
git worktree add ".worktrees/L4-001" main
fatal: 'main' is already used by worktree at '.../app'
```

Dropping `-b worktree-{task_id}` changes the meaning entirely. With `-b`, git creates a *new*
branch and checks it out into the new worktree. Without it, git tries to check out the
*existing* `main` — which is already checked out in the primary worktree, so git refuses. **The
paraphrase is not merely different, it is unconditionally fatal.** Every attempt failed
identically, which is why no run has ever produced a worktree this way.

Twelve of the eighteen agents never attempted a worktree at all, and five of the six that did
ran from the workspace root rather than `{project_path}`. Three distinct drifts — a dropped
flag, a wrong directory, a skipped step — from one paragraph of prose.

This is **F15 in its purest form**. The instruction is correct, unambiguous, and in the right
file. It is also a shell command written in a document, which a model retypes from
understanding rather than copies verbatim, and understanding does not preserve `-b`.

Addressed by item **4.14**: a command this load-bearing should be a script the skill invokes,
not a line the skill describes.

#### ~~F14 — worktree isolation is not happening~~ — **WITHDRAWN**

> **This finding was wrong, and wrong in a way worth recording rather than deleting.** The
> observation was real; the diagnosis was not. It is left in place, struck through, because
> the mistake is instructive and because item 4.12 and open question 1 were both written on
> top of it.

**What was observed.** §5.2 test 9, the first full `/execute` ever run, reported complete
success — `status: completed`, 20/20 tasks, 0 failed, 0 abandoned — while git contained one
merge commit and one branch. Nineteen of twenty tasks wrote directly into the main working
tree, which the orchestrator swept up in a commit titled *"Pre-merge baseline: commit working
tree state from prior tasks"*, leaving duplicate implementations (`api/links.py` beside
`app/api/links.py`, `main.py` beside `app/main.py`).

**What it was attributed to.** Item 4.11. The argument was that `execute-layer` and
`execute-batch` had only ever worked by mutating the caller's context inline, so making them
fork severed the worktree→merge flow. It was coherent, it matched a risk recorded when 4.11
landed, and it was wrong.

**What actually caused it.** The harness ran `/execute` with `--permission-mode acceptEdits`.
That grants file edits but **not `Bash`**, and the subagents said so in plain language:

> *"I need permission to create a git worktree."*

They could not run `git worktree add`, so they fell back to the only thing left available to
them — editing files in place — and the orchestrator committed the result. The toolchain
behaved correctly given what it was permitted to do. §5.2 test 9 was measuring its own
permission mode.

**The counter-evidence.** Re-running test 9 under `bypassPermissions`, on the unmodified
forked `main` configuration, produces worktrees. Taken from the fixture while that run was
still in flight:

```
$ git -C app log --oneline
aba78b7 Merge worktree-L2-001: POST /links endpoint - Create new link
...
$ git -C app worktree list
.../app                 aba78b7 [main]
.../.worktrees/L2-002   aba78b7 [worktree-L2-002]
```

A worktree created, a branch per task, a real merge commit. Forked orchestration and worktree
isolation are not in conflict — which is exactly what F14 claimed they were.

**Experiment B is void for the same reason.** The un-forked-orchestrator branch
(`experiment/unfork-orchestrators`) ran under the same permission mode, so it measured the
same artefact and settles nothing either way.

**What survives.** The clean run does bypass worktrees for layers 0 and 1 while using them
correctly for layer 2. That observation held up and is now recorded as **F17** below — a real
defect, but a different and narrower one than F14 described, with a different cause.

#### F17 — a forked skill cannot await background work — **FIXED, verified by run 4**

> **Resolved by item 4.12 step one** (commit `d278c05`): `execute-batch` now dispatches with
> `run_in_background: false`, and the polling step is gone. Run 4 confirms it behaviourally —
> **18 task agents for 18 task files**, all 18 dispatched synchronously, 55 subagent
> transcripts against run 3's 4, and 17 commits at roughly one per task against run 3's single
> commit for all twenty. The chain that collapsed now runs end to end.
>
> Two regression guards hold the fix (`tests/test_toolchain.py`, both tagged F17), and both
> were verified to fail when the old pattern is reintroduced.
>
> The description below is retained because it explains what was wrong and why three runs
> disagreed. **What it did not fix is isolation** — see F18 and F19, which the fix exposed.


This finding was first written as *"worktree isolation is applied per layer, not per task"*,
drawn from a single truncated run. A third run — the first to complete — showed the layer
pattern was a symptom, and found the cause. The heading and framing are corrected here;
the earlier observation is preserved below because it remains true of that run.

**The mechanism.** `execute-batch` dispatches each task with `run_in_background: true` and
then, per Step 5 of its own instructions, is supposed to "use TaskOutput to wait for each".
A forked skill has no way to do that. **Ending its turn *is* its return.** There is no
suspended state to resume into, so the intent to wait resolves as an immediate return with
the work still outstanding.

Both intermediate levels did exactly this. Their final returns, verbatim:

> **execute-layer:** *"The execute-batch skill has started L0-001 in the background… I'm
> waiting for the background task agent to complete and notify me before proceeding to the
> next batch."*

> **execute-batch:** *"Task agent for L0-001 is now running in the background. Waiting for
> completion notification before collecting results and updating state."*

Neither called `TaskOutput`. Both returned that text as their summary and terminated.

**What the parent then does is the damaging part.** `/execute` received a child that had
plainly not finished, and compensated by implementing all twenty tasks itself — 40 `Write`
calls, 15 `PowerShell` calls, **zero** `git worktree`, `git branch` or `git merge` commands —
and committed the lot as one commit:

```
ffbe2fb feat: implement Link Shelf API (all layers 0-4)
897fef9 Initial commit
```

Two commits in the repository. Twenty tasks. No branches, no worktrees, no merges.

**The orphaned agent is the corroboration.** The one task that was dispatched, `L0-001`, ran
to completion — 23 `Bash` calls, 8 `Write`s — and its completion notification was delivered to
the *top-level session*, because the fork that spawned it no longer existed to receive it. The
orchestrator's own closing summary describes it as *"a stray result from a background agent
that was spawned early on but superseded"*. Work was done, and thrown away, in a run that
reported total success. (That task never ran `git worktree add` either, so even the one task
that went down the documented path skipped isolation — F15 again.)

**Why the three runs disagreed.** This is stochastic in *degree*, not in kind. Run 2 got layer
2 right — 4 worktrees, 4 branches, 4 merges — and layers 0–1 wrong. Run 3 got nothing right
and collapsed to a single inline commit in 17 minutes. The architecture works when a level
happens to dispatch synchronously and fails when it happens to dispatch in the background, and
nothing in the toolchain forces the former.

**What run 2 showed, preserved.** Layers 0, 1 and 2 completed before that run was killed:

| Layer | Tasks | Worktrees | Branches | Merge commits |
|---|---|---|---|---|
| 0-setup | 4 | **0** | **0** | **0** |
| 1-foundation | 5 | **0** | **0** | **0** |
| 2-backend | 4 | 4 | 4 | 4 |

That layer 2 is textbook is the useful part: the worktree machinery is correct and does work.
It is the dispatch-and-wait step above it that fails.

**Severity.** Blocking. The toolchain's entire claim is isolated parallel execution with a
commit per task; run 3 delivered a single commit for twenty tasks while reporting
`status: completed`, 20/20. Note that it *did* produce a working application with 91 passing
tests in 17 minutes — the output was fine, the architecture was simply not used. A toolchain
that silently degrades to "one agent writes everything" is not obviously worse software, but
it is not the thing being tested, and it cannot be resumed, parallelised, or audited per task.

**Two related facts from the same run:**

- `execute-state.json` recorded `status: completed`, 20/20 tasks, and
  `elapsed_seconds: 3600` — the run took **1053 seconds**. The elapsed figure is invented.
  It also counts 20 tasks where only 18 task files exist. **F16**, at its worst so far.
- The `/breakdown`-generated manifest claims 20 tasks against 18 XML files, which is item
  **4.9** rather than a new finding.

**The fix is now specific**, which it was not under either earlier framing: sub-skills must
dispatch children **synchronously** and not rely on background notifications, or the
non-forked parent must own the dispatch loop outright. See item **4.12**.

#### F15 — guards written as skill prose are advisory, not enforced

Found by §5.2 test 8. `/execute` was pointed at a path containing `docs/prd/` — the exact
case item 4.7 added a refusal for — and did not refuse. It produced a full execution plan and
reasoned past the missing repository as well:

> *"The project path is not yet a git repository — which is expected since this is a
> greenfield project where L0-002 initializes git."*

Two separate guards ignored in one run: the `docs/prd/` refusal, and the preflight's
`test -d {project_path}/.git`. Both are written as prose instructions, and a capable model
treated them as context to be weighed rather than conditions to be met.

Test 9 is a second instance, though not the one originally claimed. That citation was
withdrawn with F14 — those subagents were denied `Bash`, so skipping the worktree flow was
compliance with their permissions rather than disregard of an instruction. The clean re-run
restores the point on better evidence: with `Bash` available, layers 0 and 1 still skipped the
documented worktree procedure while layer 2 followed it (**F17**). A prose *procedure* is as
negotiable as a prose *guard*.

Two consequences worth stating plainly:

- **Item 4.7's third part is not delivered.** The wrong-repository guard exists in the text
  and does not work. The regression suite checks the text is present, which is now known to
  be insufficient.
- **The same doubt applies to every other prose guard in the toolchain**, including 4.6's
  proposed absolute-path check. Writing more emphatic prose is not a fix.

Addressed by item **4.13**.

#### F16 — `execute-state.json` is not a truthful record

> A fix is designed in [`resumable-execution-proposal.md`](resumable-execution-proposal.md):
> record a commit SHA per task, appended *after* the commit, and have `--resume` verify each
> SHA against git rather than trusting a status field. That proposal also covers stopping
> cleanly on a subscription usage limit — but the truthful ledger is its prerequisite, not the
> other way round.

Found by §5.2 test 9. The state file claimed 20/20 tasks completed with zero failures while
git contained a single merge commit, and it listed two task IDs — `L0-005` and `L0-006` —
that have no corresponding generated task file.

This matters beyond tidiness: `--resume` trusts this file, so a resumed run would skip work
that was never done, and the completion report shown to the operator is not evidence of
anything. Any future check on `/execute` must read the repository, not the state file.

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

#### F1 — `/execute` cannot run against a repository with no remote — **RESOLVED**

> **Fixed by item 4.8.** Remote operations in `execute-task` and `execute-merge` are now
> conditional on `git remote get-url origin` succeeding. The branch name is no longer
> hardcoded either: `--base-branch` is threaded through `execute` → `execute-layer` →
> `execute-batch` → `execute-task`/`execute-merge`, defaulting to the repository's own
> HEAD. Two regression checks guard both halves.

`skills/execute-task/SKILL.md:67` runs, before every task:

```bash
git pull origin main
```

With no remote configured this fails, and it is the first command of every task. **No task can
complete.** The plan is explicitly "no remote for now", so this blocks the entire pipeline
regardless of any other fix.

#### F2 — Layer 0's git initialisation is self-contradictory and destructive — **RESOLVED**

> **Fixed by item 4.7.** The template now excludes `.git` from the copy rather than
> deleting it at the destination, so there is no destructive step to get wrong. Layer 0's
> `git init` task became "commit the template files", matching the preflight that already
> required the repository to exist. `/execute` additionally refuses to target a tree
> containing `docs/prd/`, a Claude Code plugin, or the tasks directory itself.

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

### 4.7 Layer 0 git contradictions — **DONE**

**Addresses F2**

> **Completed.** All three parts. The intent behind the original line was to drop the
> *template's* git metadata after copying, but the path it was given is the *caller's*
> project — so excluding `.git` from the copy achieves the intent with nothing to delete.
> That is the safer shape: a step that cannot be misdirected beats a step that must be
> given the right target.

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

### 4.8 `git pull origin main` guard — **DONE**

**Addresses F1**

> **Completed**, including the branch-name half. `--base-branch` is now a documented
> parameter defaulting to the repository's HEAD.
>
> Worth recording: after the change looked complete by grep, the regression suite's new
> hardcoded-branch check still failed, pointing at four `git checkout main` lines in
> `execute-merge/references/merge-strategy.md` that the sweep had missed. The suite
> earned its keep on its first real use.

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

### 4.12 Consolidate git ownership under forked orchestration — *step one done; structural half open*

**Addresses F17 — step one DONE (`d278c05`), and it worked.** `execute-batch` now dispatches
with `run_in_background: false`; the `TaskOutput` polling step is deleted; the single-message
rule is promoted from formatting preference to the mechanism that produces parallelism; and
two regression guards hold it. Run 4 verified it behaviourally: 18 task agents, one commit per
task, against run 3's single commit for twenty tasks.

**What remains of 4.12 is the structural half.** The dispatch fix restored the chain but not
isolation, because git operations are still performed by whichever agent happens to run them,
from whichever directory it happens to be in — which is how F18 and F19 arose. Option 1 below
is the answer to that, and it is no longer optional: it is the only version of this item that
puts `git worktree add` and the merge queue in one place with one owner.

`execute-layer` and `execute-batch` fork, so they cannot drive the worktree flow by mutating
the caller's context. Two ways to arrange this:

1. *(recommended)* **Move worktree creation and merging out of the forked skills.** Have the
   fork return a structured result — task id, branch, worktree path, verification outcome —
   and let the non-forked orchestrator perform `git worktree add` and the merge queue.
   Forking is then a way to isolate *reasoning*, and git operations stay in one place with
   one owner.
2. **Stop `execute-layer`/`execute-batch` forking**, by dropping `context: fork` from those
   two specifically. Cheapest to do, but it gives up per-skill `model:` on exactly the
   skills that orchestrate the expensive work, and re-creates the coupling that made this
   fragile.

Whichever is chosen, the acceptance test is not "the run reports success". It is
`git log --merges` in the target repository showing one merge per task, and no duplicate
implementations at the project root — both now asserted by §5.2 test 9, **run with `Bash`
actually available to subagents and long enough to finish**. Asserting on a run that was not
permitted to create a worktree, or was killed before it could, measures nothing. F17 is the
concrete target: every layer must look like layer 2 did.

### 4.13 Make the critical guards executable rather than advisory

**Addresses F15**

The `docs/prd/`, toolchain-repository and detached-HEAD guards are prose, and F15 shows prose
is negotiable. Options, in increasing order of reliability:

1. Express each guard as a **single shell command whose exit status is the decision**, phrased
   so there is nothing to interpret: `test -d {p}/docs/prd && exit 1`. Better than prose, still
   dependent on the model choosing to run it.
2. Put the preconditions in a **script the skill invokes** — one `preflight.sh` that exits
   non-zero — so the check is a program, not an instruction.
3. Accept that a skill cannot police its own target and move the guard **outward**, to whatever
   wraps `/execute`.

Option 2 is the smallest change that actually changes the guarantee. Note the regression suite
currently checks only that the guard *text* exists (`F2` check in `tests/test_toolchain.py`);
that check should assert the mechanism, not the wording, once one is chosen.

### 4.14 Make worktree creation a script, and refuse to operate outside the target — **DONE**

**Addresses F18 and F19. Blocking.**

> **Completed.** `skills/execute-task/scripts/create-worktree.sh` is now the single place the
> command exists; `execute-task` Step 2 invokes it, `execute-merge` asserts its toplevel before
> merging, the duplicate command in `merge-strategy.md` is replaced by a pointer, and
> `/execute`'s "git not initialised" advice no longer reads as an instruction to run `git init`.
> The script was tested against all six paths — two parallel worktrees created, and refusals
> for a non-repository (without initialising one), a subdirectory of a repository, a
> pre-existing branch, and a missing base branch.
>
> Two regression guards added, both verified to fail when the old pattern is reintroduced:
> no `git worktree add` in any instruction `.md`, and no `git init` outside backticks. Suite:
> 22 passed, 0 failed, 2 known.
>
> **Run 5 says it is inert.** The script was invoked **zero** times, because the file telling
> anyone to invoke it — `execute-task/SKILL.md` — has never been loaded (**F20**). Five
> hand-written `git worktree add` commands ran instead, and one `git init` re-created the stray
> repository at the workspace root. Nothing here is *wrong*; it simply sits in a document that
> is not in the execution path. It becomes live the moment item **4.15** lands, and the script
> itself is tested and correct.

Two halves, both narrow, both mechanical. Neither is a rewrite of the architecture — 4.12
option 1 is that — but together they remove the failure that has cost four runs.

**1. Bundle the worktree command as a script.** F18 shows a shell command in prose gets
retyped from understanding, and understanding does not preserve `-b`. Ship a script and have
`execute-task` invoke it:

```bash
# skills/execute-task/scripts/create-worktree.sh <task-id> <worktree-dir> <base-branch>
set -euo pipefail
cd "$PROJECT_PATH"                      # never inherited from the caller's cwd
git rev-parse --git-dir >/dev/null      # fail loudly if this is not a repository
git worktree add -b "worktree-$1" "$2/$1" "$3"
```

The point is not that a script is tidier. It is that `-b` cannot be dropped from a file that
is executed rather than read, and the working directory cannot drift. This is the same reason
superpowers bundles its worktree and workspace setup as scripts rather than describing them.

**2. Refuse to operate outside `{project_path}`.** F19's damage came from agents walking
*upward* after a failure. The preflight constrains where `/execute` is pointed; nothing
constrains where it wanders. Add, as a precondition on every git-mutating step:

```bash
test "$(git rev-parse --show-toplevel)" = "$PROJECT_PATH" || exit 1
```

and state plainly in `execute-task` that a failed worktree creation is a **task failure to be
reported**, not a problem to be worked around. The retry loop exists for this; improvisation
does not need to.

A `git init` anywhere other than `{project_path}` should be treated the way item 4.7 treats
deleting `.git` — as something the toolchain never does.

**Acceptance:** run 4's fixture, replayed, produces a worktree per task and *no* repository at
the workspace root. The regression suite cannot check the second half statically, which is
what item **4.13** is for.

### 4.15 Create the worktree before dispatch, and invoke skills rather than describing them — **DONE**

> **Completed (option A).** `execute-batch` now creates each worktree via the script *before*
> spawning anything, and passes `{worktree_path}` into the agent prompt — the arrangement
> `task-implementer.md` was always written for. `skills/execute-task/` is deleted; its
> procedural content moved to the agent (worktree framing, the commit step it never had, a
> result schema that actually carries `commit_hash`), its two reference files moved to
> `skills/execute-batch/references/` and are named in the dispatch prompt, and the script moved
> to `skills/execute-batch/scripts/`. Independent verification is now invoked by `execute-batch`
> through the `Skill` tool, because a dispatched agent has no `Skill` tool at all.
>
> Two defects fixed in passing: the agent had **no commit step**, while `execute-batch` parsed
> `commit_hash` from its result; and the two result schemas disagreed (`status: success` vs
> `verified`, no `branch`/`worktree_path`).
>
> Two regression guards added, both verified to bite. One is a tripwire rather than a proof: a
> skill *named in a prompt* is textually identical to a skill *invoked from a skill*, so no
> static rule separates them in general.
>
> **Not yet verified behaviourally** — that needs run 6.

**Addresses F20. Blocking, and it is the precondition for 4.8, 4.13 and 4.14 having any
effect at all** — all three edited a file that is not in the execution path.

**1. `execute-batch` creates the worktree, then dispatches into it.** Before spawning the task
agent, call the script and pass the resulting path:

```bash
worktree_path=$(sh {execute_task_skill_dir}/scripts/create-worktree.sh                   {project_path} {task_id} {worktree_dir} {base_branch})
```

Then hand `{worktree_path}` to the agent in its prompt. This is the world
`agents/task-implementer.md` is *already* written for — it says "change to worktree", not
"create one" — so the agent needs no change. If the script fails, the task fails before any
agent is spawned, which is both cheaper and louder than discovering it afterwards.

This is item **4.12 option 1** applied to the one link that most needs it. Git operations move
to the caller; the agent gets an isolated directory and a specification, which is all it ever
wanted.

**2. Stop describing skills in prompts as though that invoked them.** `/execute-task …` inside
an Agent prompt is text. Either the caller invokes the `Skill` tool explicitly, or — better
here — the instructions the agent needs live in the **agent definition**, which is loaded by
construction. Prefer the second: it removes a step that can be skipped.

**3. Decide what `execute-task/SKILL.md` is for.** It currently duplicates
`task-implementer.md` and loses the race by never loading. Either fold the parts worth keeping
into the agent definition and delete the skill, or make it genuinely invoked. Two documents
describing one job, with no mechanism ensuring the right one runs, is how five runs produced
five different behaviours.

**Acceptance:** a run in which every task agent begins inside `{worktree_dir}/{task_id}`, one
`worktree-*` branch exists per task, and no `git worktree add` or `git init` appears in any
subagent transcript at all.

---

## 5. Test plan

Run in a scratch project, not against `test-project`.

### 5.1 Fixture — **DONE**

A minimal PRD with two or three features — enough to exercise layer planning without a 60-file
generation cycle on every iteration.

> **Built at [`tests/fixture/`](../../tests/fixture/).** `Link Shelf`: three features, two
> models, three endpoints, no frontend, no auth. `setup_fixture.py` materialises a workspace
> outside this repository — refusing to build inside it, since `/execute` creates branches and
> removes worktrees in its target.
>
> Choices that matter: SQLite so nothing external must be running; no template path so Layer 0
> creates directories rather than copying a tree; the target repository pre-created **with no
> remote**, which is exactly the configuration F1 could not survive; and tags as a join table
> rather than a string column, so the data-model layer is not trivial.
>
> `--verify` makes **F2 falsifiable**. It records the target repository's root commit at build
> time and checks it is still reachable afterwards, so reinitialising the repository is caught
> as well as deleting it. The negative case is tested: removing `app/.git` makes `--verify`
> exit 1. The suite also validates the fixture PRD statically, so drift fails fast rather than
> during an end-to-end run.

### 5.2 Sequence — **RUN**

Executed against the §5.1 fixture by [`tests/fixture/run_5_2.py`](../../tests/fixture/run_5_2.py),
which captures each run's result JSON and transcript.

| # | Test | Result |
|---|---|---|
| 1 | ~~Phase 0 probes (U1, U2, F6 precedence)~~ | **Done** — see §3.5 |
| 2 | `/prd` on a fresh directory | **PASS** — PRD written, `what-next.md` valid XML with `<status>`. No `<toolchain-version>`: item 4.5 not done |
| 3 | `/prd` again with no arguments | **KNOWN/4.3** — opened a fresh interview with a PRD already present. Confirms F3 |
| 4 | `/prd --resume` | **PASS** — found the existing PRD |
| 5 | `/breakdown` with a relative `--output-dir` | **KNOWN/4.6** — not rejected, and worse: generated Layer 0 tasks with the relative-derived path baked in, then timed out |
| 6 | `/breakdown` with an absolute `--output-dir` | **PASS** — 29 files generated in 67 min; nothing written into the toolchain tree |
| 7 | `/execute` against a repo with **no remote** | **PASS** — full plan produced, base branch resolved from HEAD. F1 fix confirmed under a real run |
| 8 | `/execute` against a path containing `docs/prd/` | **FAIL** — not refused → **F15** |
| 9 | Full `/execute` run on the fixture | **Run 1 VOID** — 83 min, reported success while 19 of 20 tasks bypassed isolation, but `--permission-mode acceptEdits` denied subagents `Bash`, so it measured the harness → **F14 withdrawn**. **Run 2 INCONCLUSIVE** — killed by the 90-minute timeout at 15/18 tasks; layer 2 isolated correctly (4 worktrees, 4 merges), layers 0–1 not at all. **Run 3 FAIL** — the first to complete: 20 tasks, **1 commit**, 0 worktrees, 0 branches, 0 merges, in 17 min → **F17**. `.git` intact and root commit preserved throughout (F2); state file fabricated its elapsed time (F16). **Run 4 FAIL** — the dispatch fix verified (18 task agents, one commit per task), but 0 of 6 `git worktree add` attempts included `-b` so all failed → **F18**, and the agents then `git init`-ed a repository at the workspace root containing the docs tree and a gitlink to `app/` → **F19**. **Run 5 FAIL** — 4.14's script invoked **0** times across 19 task agents, because not one of them ever loaded `execute-task` at all: it is *described* in an Agent prompt, not invoked → **F20**. One task got a hand-rolled worktree and merged; the rest wrote to the main tree, and one `git init` re-created the stray repository |
| 10 | Artefact version mismatch | Not run — depends on item 4.5 |

Two results deserve emphasis because they are the opposite of what the summary line said.

**Test 9 first reported PASS.** The criterion was "more than zero commits merged", which a
run satisfies while doing almost nothing correctly. Tightening it to require merge commits
proportional to task count re-graded the same run to FAIL. A weak assertion is worse than no
assertion: it converts an unexamined failure into a green tick.

**Tests 7 and 8 also first reported PASS**, having actually failed at input validation before
reaching the behaviour under test — `/execute` errored because `/breakdown` had not yet run,
and the checker read "an error occurred" as "the guard refused correctly". Test 6 separately
inherited test 5's output, because `/breakdown` resumes from `.done` markers and both tests
share `docs/tasks/<slug>/`.

**Test 9's FAIL was also wrong**, and cost the most. Re-graded from PASS to FAIL on a
tightened criterion, it was written up as blocking finding F14 and drove a whole remediation
item — when the actual cause was that the harness ran the toolchain under a permission mode
denying subagents `Bash`. The subagents said so explicitly in their transcripts, which nobody
read before drawing the conclusion. **Check the transcripts for permission denials before
attributing an end-to-end failure to the code.**

Every one of those was a fault in the harness, not the toolchain. They are recorded because
the same shapes will recur: assert that a test reached the thing it claims to test, isolate
shared state between runs, and never accept "something happened" as evidence of success.

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
| ~~4.7~~ | ~~Layer 0 git contradictions~~ **DONE** (guard part ineffective, see 4.13) | ~~Blocking~~ | `breakdown-generate-tasks`, `breakdown`, `execute` |
| ~~4.12 step one~~ | ~~Synchronous dispatch~~ **DONE `d278c05`** — F17 fixed, verified by run 4 | ~~Blocking~~ | `execute-batch` |
| **4.15** | **Create the worktree before dispatch; invoke skills rather than describing them** | **Blocking** | `execute-batch`, `task-implementer`, `execute-task` |
| ~~4.14~~ | ~~Worktree creation as a script~~ **DONE but inert until 4.15** — the file it lives in is never loaded | ~~Blocking~~ | `execute-task`, `scripts/` |
| **4.12** | **Consolidate git ownership under forked orchestration** *(structural half)* | **Blocking** | `execute-layer`, `execute-batch`, `execute-task` |
| **4.13** | **Make critical guards executable rather than advisory** | **Correctness** | `execute`, `tests/test_toolchain.py` |
| ~~4.8~~ | ~~`git pull origin main` guard~~ **DONE** | ~~Blocking~~ | `execute-task`, `execute-merge`, `execute`, `execute-layer`, `execute-batch` |
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

1. **How should forked skills orchestrate git?** Raised by F14 and outliving its withdrawal.
   Forked orchestration and worktrees demonstrably coexist, so this is no longer urgent — but
   *which layer owns `git worktree add` and the merge queue* is still unanswered, and the
   one-commit-per-task contract the resume ledger needs depends on the answer.
2. **Can a skill enforce anything about its own target?** F15 says prose cannot. If the answer
   is "no", guards belong outside the skill entirely, and item 4.6's proposed absolute-path
   check needs rethinking before it is written rather than after.
3. **Per-layer model tiering** — worth it, or one global implementation model? Now a real
   decision rather than a hypothetical, since 4.11 makes `model:` take effect.
4. **Branch naming** — derive from HEAD, or keep `main` as a documented requirement?
5. **Should `/crd-context` become a skill?** Unlike `/prd` and `/crd` it is closer to batch work
   than to an interview, so the reasoning that kept those two as commands may invert here.
6. **Is any tool sandboxing available at all?** `tools:` on a skill does not restrict. If real
   confinement is wanted for `task-implementer`, it will have to come from somewhere other than
   skill frontmatter.
7. **What is `/execute`'s completion report worth?** F16 shows it can report 20/20 success
   against one merge commit. Until that is fixed, no automated check should trust it, and
   neither should an operator.
