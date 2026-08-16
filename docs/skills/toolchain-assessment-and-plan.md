# Claude Code Toolchain — Assessment and Remediation Plan

**Status:** **The pipeline works end to end, reports itself honestly, and survives interruption.** Run 6 of §5.2 test 9 passed: 18 tasks, **18 merge commits — one per task**, every worktree created by the caller via the bundled script, independent verification invoked for the first time in six runs, no repository created outside the target, and the resulting application passing 88 tests. F17, F18, F19 and F20 are resolved and behaviourally verified, alongside F1, F2 and F13. **F16 is resolved** by item 4.16 and verified by run 7 — the ledger and the merge commits correspond exactly, and the counts are finally correct. 4.4 and 4.5 are deferred to a separate plan; every other remediation item is done. **F4 is resolved** by item 4.6 and verified by test 5. **F24** — the finalizer wrote the literal string `current-HEAD` into `last-context-hash`, having no `Bash` to compute one with — is resolved; the caller stamps it now. A **CRD fixture now exists** (§5.3) but the brownfield path has still never run.
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

*Applied by item 4.2. Every identifier below is current, and every skill/agent pair agrees.*

| File | Declared model |
|---|---|
| `skills/breakdown`, `breakdown-generate-tasks` + `agents/task-generator` | `claude-opus-5` |
| `skills/crd`, `crd-investigate`, `execute`, `execute-batch`, `execute-layer`, `execute-merge` + `agents/crd-investigator` | `claude-sonnet-5` |
| `skills/breakdown-analyze-prd`, `breakdown-plan-layers`, `breakdown-review-tasks`, `crd-context-update`, `crd-impact-analysis`, `execute-verify` | `claude-haiku-4-5` |
| `agents/task-implementer`, `task-reviewer`, `crd-context-updater`, `crd-impact-analyzer`, `verification-runner`, `project-context-finalizer` | `claude-haiku-4-5` |
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

#### F20 — `execute-task/SKILL.md` has never been loaded — **RESOLVED, verified by run 6**

> **Fixed by item 4.15 (`c915422`).** `execute-batch` now creates each worktree itself and
> passes the path into the prompt; `skills/execute-task/` is deleted and its procedure lives in
> `task-implementer.md` and `skills/execute-batch/references/`. Run 6: **19 script invocations,
> 18 successful** (the extra correctly refused a duplicate branch), **zero** hand-written
> `git worktree add`, and `execute-verify` invoked **18 times** — the first time independent
> verification has ever run.


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

#### F21 — `execute-state.json` is written into the target repository, and still lies — **RESOLVED, verified by run 9**

> **Fixed by item 4.17.** `skills/execute/scripts/write-state.py` is now the only writer.
> Every countable field is derived from the ledger and git; nothing is incremented. It refuses
> to write anywhere inside `{project_path}`, and warns if the stray copy from run 8 is still
> lying there.
>
> Run against run 8's own fixture, it produced `completed, 18/18` where the hand-written file
> said `completed` at 4 of 18.
>
> **Run 9 confirms it end to end.** `write-state.py` was invoked 38 times and
> `execute-state.json` was hand-written **zero** times. The file it produced is the first
> truthful one this project has seen:
>
> ```
> schema_version   3.0
> derived_from     ledger + git; no field in this file is maintained by hand
> status           completed          tasks_completed  18 of 18
> merge_queue      18                 missing_commits  []
> layers           0-setup 4/4, 1-foundation 5/5, 2-backend 4/4, 4-integration 5/5
> ```
>
> `git status` in the target was empty, no second copy of the file appeared, and no repository
> was created outside the target. The produced application passes 88 tests.


Found by §5.2 run 8. **The ledger is right and the state file is wrong — again, in a new way.**

Run 8 passed: 18 merge commits, 18 ledger entries, all 18 recorded SHAs are merge commits, no
repository outside the target. `ledger-status.sh` was invoked 3 times. And yet:

| | |
|---|---|
| `app/execute-state.json` | **written into the target repo**, untracked — `?? execute-state.json` |
| its `status` | `completed` |
| its `tasks_completed` | **4** |
| its `tasks_remaining` | **14** |
| merges actually in git | **18** |

Two distinct defects:

1. **State leaked into the product repository.** A `Write` went to
   `{project_path}/execute-state.json` as well as the correct
   `{tasks_path}/execute-state.json`, and the two hold *different halves* of the schema — the
   target's copy has the metadata and metrics, the tasks directory's has `tasks`,
   `merge_queue`, `completed` and `layers`. Neither is complete. The stray one shows up in the
   operator's `git status`, which is exactly the pollution the ledger's self-ignoring
   `.gitignore` was designed to avoid.
2. **`status: completed` alongside `tasks_completed: 4` of 18.** This is the precise
   contradiction the run-7 follow-up was written to prevent — `status` may only be `completed`
   when `verified == expected`. The reconciliation step ran (`ledger-status.sh`, 3 calls) and
   its answer was not used. The `4` is a hand-count that stopped early.

**The pattern is now unmistakable.** Everything that became a script is correct and has stayed
correct across three runs: `preflight.sh` (invoked, and 4.13 verified by this run),
`create-worktree.sh` (34 calls), `record-task.sh` (35), `ledger-status.sh` (3). The one
artefact still assembled by hand from prose instructions has been wrong in **two consecutive
runs, in two different ways** — over-counting in run 7, under-counting and duplicated in run 8.

Prose has now failed on this specific file four times. The remedy is not a fifth rewording.

Addressed by item **4.17**.

#### F19 — `/execute` creates a git repository outside `{project_path}` — **RESOLVED, verified by run 6**

> **Fixed by items 4.14 and 4.15.** Zero `git init` invocations in run 6, and no repository at
> the workspace root. The cause was never `git init` itself: agents ran it while improvising
> around a failed worktree. Remove the need to improvise and the symptom goes with it.


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

#### F18 — the `git worktree add` command is retyped from prose, and drifts — **RESOLVED, verified by run 6**

> **Fixed by items 4.14 and 4.15.** The command exists in exactly one executable file and is
> invoked by the caller. Run 6 ran it 19 times and hand-wrote it zero times. Note the ordering:
> 4.14 bundled the script and changed nothing, because the file naming it was never read
> (F20). The script only became load-bearing once 4.15 moved the call to `execute-batch`.


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

#### F15 — guards written as skill prose are advisory, not enforced — **RESOLVED for the critical guards**

> **Fixed by item 4.13.** Every `/execute` precondition now lives in
> `skills/execute/scripts/preflight.sh`, one program whose exit status is the decision. There
> is no sentence left to weigh.
>
> **Item 4.7's third part is delivered at last.** The wrong-repository refusal existed in prose
> from 4.7 onward and never once fired; it now does, and the suite proves it by running it.
>
> The general principle stands — any prose instruction may be ignored — but the guards this
> finding named are no longer prose. Five scripts now carry what used to be description:
> `preflight.sh`, `create-worktree.sh`, `record-task.sh`, `ledger-status.sh` and
> `build-manifest.py`. Each was written because the described version demonstrably failed.


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

#### F16 — `execute-state.json` is not a truthful record — **RESOLVED, verified by run 7**

> **Fixed by item 4.16.** A task is now recorded by SHA in a ledger, appended only after the
> commit exists, and the metrics block is recomputed from git at the end of the run rather than
> incremented along the way. `elapsed_seconds` is gone — it was a field nobody measured.
>
> Two scripts, both tested against a real repository: `record-task.sh` refuses to record a
> commit that does not exist, and `ledger-status.sh` re-verifies every SHA and reports the first
> gap. Two regression guards, both verified to bite, including one that fails the build on any
> `tasks_completed += 1`.
>
> **Run 7 confirms it on a real run.** The ledger holds 18 entries for 18 distinct tasks, every
> recorded SHA is one of the 18 merge commits, and no merge is unrecorded — exact
> correspondence in both directions. `ledger-status.sh` returns
> `{"recorded":18,"verified":18,"missing":[],"first_unverified":null}`. The ledger stayed
> invisible to the target: `git status` in `app/` is empty.
>
> The numbers that were wrong are now right:
>
> | field | run 6 | run 7 | actual |
> |---|---|---|---|
> | `tasks_completed` | 23 | **18** | 18 |
> | `completed[]` entries | 19 | **18** | 18 |
> | `elapsed_seconds` | 4000 | **absent** | — |
>
> **One gap the run exposed in the fix itself**, since corrected: `/execute` wrote
> `status: completed` alongside `tasks_remaining: 2`. The guard said "do not report success
> while `missing` is non-empty", and `missing` *was* empty — every recorded commit verified.
> The shortfall was `expected - verified`, which nothing checked. `status` may now only be
> `completed` when `verified == expected` **and** `missing` is empty; they fail separately and
> are now checked separately.
>
> The shortfall itself is **item 4.9**, not F16: `manifest.json` claims 20 tasks where 18 task
> files exist, so `/breakdown` over-counted and `/execute` faithfully reported 18 of 20.


> **Run 6 sharpens it.** With everything else working, the state file is measurably wrong in a
> run that genuinely succeeded:
>
> | field | recorded | actual |
> |---|---|---|
> | `tasks_total` | 18 | 18 ✓ |
> | `tasks_completed` | **23** | 18 |
> | `completed[]` entries | **19** | 18 |
> | `elapsed_seconds` | **4000** | 10476 |
> | `merge_queue` | 18 `merged` | 18 ✓ |
>
> The parts derived from git are right; the counters the model maintains by hand are not. That
> is the whole finding in miniature, and the argument for
> [`resumable-execution-proposal.md`](resumable-execution-proposal.md): record SHAs, count by
> asking git, never by incrementing.


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

#### F3 — `/prd --resume` cannot find this PRD — **RESOLVED**

> **Fixed by item 4.3.** The half that mattered was never the `--resume` lookup: it was that
> `/prd` with no arguments began a fresh interview immediately, and Phase 8 then wrote to
> `docs/prd/[slug]/`. `/prd` now enumerates existing PRDs on entry *regardless of arguments*,
> reads the status marker from `what-next.md` **or** `index.md`, and Phase 8 refuses to write
> over an existing directory without asking.


`commands/prd.md:14` searches `docs/prd/*/what-next.md` for `<status>in-progress</status>`.
The status tag is present in `index.md`, not in `what-next.md`. Resume therefore finds nothing.

Worse, the no-arguments path starts a **new** PRD and Phase 8 writes to `docs/prd/[slug]/` —
so an unguarded session can overwrite an existing `index.md` and `what-next.md`.

#### F4 — Skill output can be written relative to the skill directory — **RESOLVED**

> **Fixed by item 4.6, and verified behaviourally by §5.2 test 5.** Both output paths are
> resolved by `skills/breakdown/scripts/resolve-output.sh` before anything is created; a relative
> `--output-dir` and any path inside a plugin are refused by exit code. The run's transcript shows
> the forked `/breakdown` context **running** the script and stopping on its status — not reasoning
> its way to the same answer, which is the distinction F15 made expensive.

`.claude/skills/breakdown-generate-tasks/output/2-backend/LAYER_SUMMARY.md` exists on disk and
contains generated tasks for an unrelated **"Voice PRD Generator"** project. The skill takes the
output directory as an input (`SKILL.md:21`), so nothing is hardcoded — but a previous
invocation resolved a relative path against the skill's own directory and wrote there.

Two consequences: generated artefacts silently pollute the toolchain repository, and the caller
has no indication their output went somewhere unexpected. Currently gitignored via
`skills/*/output/`, which contains the symptom but not the cause.

#### F5 — Model versions are stale, and no Haiku 5 exists — **RESOLVED**

> Fixed by item 4.2. No stale identifier remains, and the check that forbids them is now a
> permanent guard rather than an expected failure.


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

#### F7 — Agent models conflict with the skills that invoke them — **RESOLVED**

> Fixed by item 4.2. Both conflicting pairs now agree, and the check is a permanent guard.
> This mattered because of F6: the skill's `model:` wins, so the agent's line was the one
> silently losing.


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

#### F8 — Commands carry no frontmatter — **RESOLVED**

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
settled by item 4.1: **all three stay commands.** F8 is resolved.

#### F9 — The documented `project_path` fallback is dead — **RESOLVED**

> **Fixed by item 4.9.** `build-manifest.py` writes `prd.project_path`, and its `--verify` mode
> fails when the field is absent, so the fallback `/execute` documents can now actually fire.
>
> The finding turned out to have a second half nobody had looked for: the manifest was written
> from `layer_plan.json` rather than from the generated files, so it was wrong about *what
> exists*, not merely incomplete. See item 4.9.


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

#### F11 — Orphaned agent — **RESOLVED**

> **Fixed by item 4.10**, by wiring rather than deleting. `/execute` Step 10 now dispatches
> `project-context-finalizer` via `subagent_type`, which loads the agent definition by
> construction. A guard now fails the build on *any* unreferenced agent, so this cannot
> recur with a different file.


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

#### U1 — `allowed-tools` in a skill: grants, never restricts, and disables forking — **answered**

Three results, the third added later from an external report:

1. **`allowed-tools` does not restrict anything in a skill**, and its presence disables
   `context: fork`. Promoted to **F13**, blocking, and fixed by item 4.11.
2. **`tools:` is the correct skill key, but it does not restrict either.** A forked skill
   declaring `tools: Read, Glob, Grep` still performed a `Write` in 3/3 runs. Both comma and
   space separation parse without breaking the fork.
3. **`allowed-tools` *is* honoured — as a permission grant, and only on direct invocation.**
   [anthropics/claude-code#67198](https://github.com/anthropics/claude-code/issues/67198)
   reports that the listed tools are pre-approved when a user types `/skill-name`, but **not**
   when the model reaches the same skill through the `Skill` tool, where every command still
   prompts. Closed as a duplicate, so it is a known issue rather than a fix.

The three fit together: the key grants permissions rather than restricting them, that grant
only fires on the direct path, and on any path it costs forking. My original heading —
*"not honoured"* — was too strong, and this correction is why: it is honoured, for a purpose
opposite to the one the toolchain appeared to intend.

**What this means for item 4.11**, which deleted the key from all 15 skills:

- For the twelve skills reached through the `Skill` tool, the grant never fired anyway. Pure
  gain: they now fork, and lost nothing.
- For `/execute`, `/prd` and the other directly-invoked entry points, the deletion **did**
  give up a real permission pre-approval, in exchange for forking. That is the right trade —
  a toolchain whose declared models and agents never apply is worse than one that prompts —
  but it is a trade, not a free win, and it was not visible when 4.11 was written.
- The durable place for those grants is the operator's `settings.json` `permissions.allow`,
  not skill frontmatter: it works on both invocation paths and does not interact with forking.
  §5.2 sidesteps the question by running under `bypassPermissions`, which is why no run has
  ever surfaced it.

Practical consequence, unchanged: there is **no working per-skill tool sandbox** to
standardise on. Item 4.1 should drop the tool-restriction goal rather than restate it in a
different spelling.

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

### 3.7 Resume, verified by accident

Run 10 is the most useful result in this document, and none of it was planned.

The run stopped at **11 of 18** tasks with `API Error: Response stalled mid-stream` — an
infrastructure failure, not a toolchain defect. It was then finished by resuming twice, and
the ledger records the whole thing:

| Session | Tasks added | Ended by |
|---|---|---|
| Original run | `L0-001` … `L2-002` (11) | API stall |
| First resume | `L2-003` … `L4-004` (6) | 4-hour timeout, after the machine slept overnight |
| Second resume | `L4-005` (1), in 9 minutes | **completed** |

Final state: **18 ledger entries, 18 distinct task ids, zero duplicates, every entry
`attempts=1`.** The state file says `completed`, 18 of 18, `missing: []`; `git status` in the
target is clean; there is no repository outside it; and the produced application passes 88
tests.

**Not one task was redone.** Each resume read the ledger, verified each SHA against git, and
started at the first task without one.

Three things this validates that nothing else could:

1. **`--resume` works on a real interruption**, not a constructed one. The synthetic test in
   4.16 proved the arithmetic; this proves the behaviour under an unplanned failure with
   partial state on disk.
2. **The record survived a nine-hour suspension.** The machine slept from 23:24 to 08:13 with
   the process suspended mid-run; on waking it merged the task it had been holding and carried
   on. Nothing had to be reconciled by hand.
3. **The harness graded the interruption honestly.** Both improvements made that morning
   earned their place immediately: a killed run reported `INCONCLUSIVE` rather than `FAIL`,
   and the new ledger-based criterion described the state precisely — *"17 of 18 tasks
   completed; state file agrees, record is consistent and resumable."*

Worth stating what would have happened a week earlier. `execute-state.json` was the only
progress record, and in run 8 it claimed `completed` at 4 of 18 while git held 18 merges. A
resume trusting it would have skipped fourteen tasks that were never done — or redone eleven
that were. Both were live failure modes, and this run would have exposed neither, because
before F16 nothing checked.

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

### 4.1 Frontmatter and command→skill conversion -- **DONE**

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

**Decision taken: `/crd-context` stays a command too, so all three do, and this item is
closed.** It was left open on the reasoning that it is "closer to batch work than to an
interview". Reading the file settles it the other way.

`commands/crd-context.md` is a **thin router**. Both paths that cost anything delegate to
skills that already fork and already carry their own selector:

| Path | Delegates to | | |
|---|---|---|---|
| `--full`, or no `PROJECT.md` | `/crd-investigate` | `context: fork` | `model: claude-sonnet-5` |
| context stale | `/crd-context-update` | `context: fork` | `model: claude-haiku-4-5` |

What the command does itself is validate the path, read `last-context-hash`, compare it with
`git rev-parse HEAD`, and — for `--diff` — run `git diff <hash>..HEAD --name-only` and
categorise the result.

So converting would buy a `model:` selector on a hash comparison, while costing the one thing
`--check` and `--diff` exist for: printing status **in the user's context**. A forked skill
returns a summary to its caller instead. That is the same argument that kept `/prd` and `/crd`
as commands, and it applies here with more force rather than less, because there is no
expensive reasoning to isolate in the first place.

The general form is worth keeping: **fork to isolate expensive reasoning, not to obtain a
`model:` selector.** Where the expensive reasoning has already been delegated to a forked
skill, the caller has nothing left to isolate.

Two things deliberately not done, so they do not read as loose ends:

- **Model aliases are not adopted here.** The note below prefers `model: opus` over pinned
  identifiers, and for most repositories that is right. This one pins deliberately: the fork
  and model rules it depends on were established by measurement against specific models in
  Phase 0 (§3.5), so a pinned identifier is the reproducible choice. The regression suite
  accepts both forms and rejects stale ones, which is the property that actually matters.
- **`/crd-context` has no guard script**, unlike `/execute` (`preflight.sh`) and `/breakdown`
  (`resolve-output.sh`). It does validate its `--project` path before acting, but that
  validation is prose, and F15 is what prose validation is worth. That is a separate and
  smaller item than this one, and worth raising only if the brownfield path gets real use.

Notes:

- Published skills overwhelmingly use **short aliases** — `model: opus`, `model: sonnet`,
  `model: inherit` — rather than pinned identifiers. Aliases track the current tier and never
  need another migration. Pin only where reproducibility genuinely matters.
- The former instruction to "apply the `allowed-tools` format decision across all skills" is
  superseded: there is no valid format. See item **4.11**.

### 4.2 Model assignments across skills *and* agents — **DONE**

**Addresses F5, F6, F7.**

> **Completed.** 16 declarations changed in one pass, so skills and agents could not drift
> apart in the doing of it. Every stale identifier is gone (`claude-sonnet-4-6`,
> `claude-sonnet-4-5`), Haiku-tier has one spelling (`claude-haiku-4-5`, not the dated alias),
> and both skill/agent pairs that named different models now agree —
> `breakdown-generate-tasks`/`task-generator` on Opus 5, `crd-investigate`/`crd-investigator`
> on Sonnet 5.
>
> **The `task-implementer` question answered itself.** The plan agonised over it because
> `execute-task`'s `model:` would override the agent's — but 4.15 deleted that skill, so the
> agent's declaration is now the only one, and it governs directly. What was an emergent
> default is now an explicit choice: `claude-haiku-4-5`, declared in one place, with nothing
> silently overriding it. Runs 6–9 produced 88 passing tests on that tier.
>
> **The suite is fully green for the first time**: 31 passed, 0 failed, **0 known**. Both
> `expect_fail="4.2"` markers were removed, converting those checks into permanent guards — one
> forbidding stale identifiers, one requiring a skill and its agent to agree.

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

### 4.3 Resume detection — **DONE**

**Addresses F3.**

> **Completed**, all three parts.
>
> **What the finding got right and wrong.** F3 led on `--resume` searching `what-next.md` for a
> marker that lived in `index.md`. That is no longer true for new PRDs — `commands/prd.md`
> already specifies `what-next.md` with `<status>`, and §5.2 test 2 confirmed a fresh `/prd`
> writes it as valid XML. The lookup is now dual anyway, because artefacts written before that
> template settled still carry the marker only in `index.md`, and a PRD that cannot be found is
> a PRD that gets silently replaced.
>
> **The live danger was the second paragraph of the finding**, and §5.2 test 3 confirmed it:
> `/prd` with no arguments opened a fresh interview with a PRD already present. Two guards
> now stand between that and data loss — an unconditional enumeration on entry, and a
> `test -e` in Phase 8 that stops and asks rather than trusting that Initialization was
> careful. The second matters because slug collisions arrive from a different direction:
> two similarly-named projects produce the same slug, and the second would destroy the first.
>
> **Verified behaviourally by §5.2 test 3**, which is the only thing that could — the static
> guard checks wording, and F15 is the standing reminder that wording is not behaviour. The
> re-run reported **FIXED**: an existing PRD detected in 15 seconds, named with its status and
> last-modified date, `index.md` byte-identical afterwards, and no interview started. Test 2
> re-ran at 130s to confirm the new lookup does not disturb the fresh path.
>
> **4.4 is deferred and nothing here waits on it.** Part 2 was designed to work without it;
> deferring 4.4 only means the dual lookup stays permanent rather than being simplified.

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

### 4.6 Absolute output path guard -- **DONE**

**Addresses F4**

> **Completed.** `skills/breakdown/scripts/resolve-output.sh` does all three parts, and does
> them as a program rather than as prose -- which §3.1 had already insisted on for this exact
> item: *"the same doubt applies to every other prose guard in the toolchain, including 4.6's
> proposed absolute-path check."*
>
> Like `preflight.sh`, it **resolves as well as refuses**: running it is the cheapest way to
> obtain the two paths, so calling it is in the caller's interest rather than a hoop.
>
> ```
> resolve-output.sh <tasks-dir> [target-dir]
>   -> tasks_dir=<absolute>
>      target_dir=<absolute>
> ```
>
> 1. **`--output-dir`/`--project-path` must be absolute.** Refused otherwise, quoting the path
>    it would have resolved to, so the caller can see exactly what was ambiguous.
> 2. **Neither path may resolve inside a Claude Code plugin.** That is F4 directly, and it is
>    pointless as well as wrong: `preflight.sh` already refuses a plugin as an `/execute`
>    target, so tasks generated there could never be run.
> 3. **Both resolved paths are echoed before anything is written**, and `breakdown/SKILL.md`
>    now uses `{tasks_dir}` throughout instead of the literal `docs/tasks/{slug}` -- resolution
>    is worthless if the relative string is used afterwards anyway, so the regression check
>    fails if any survives.
>
> The stray `skills/breakdown-generate-tasks/output/` tree is already gone; the check that no
> generated output is committed under `skills/` remains as a separate permanent guard.
>
> **Asymmetry, deliberately.** The tasks directory *may* be relative -- `docs/tasks/<slug>` is
> the documented default -- and is resolved here against the caller's working directory. The
> target may not. They differ in whether a wrong answer is recoverable: mis-resolving the tasks
> directory produces files in a visible place, whereas `--output-dir` names where an entire
> codebase is built and where `/execute` later creates and merges branches.
>
> **A second F4 was found inside the fix.** The first version resolved
> `C:\Users\Lee\AppData\Local\Temp\nope\app` to **`/tmp/nope/app`** -- silently, with exit 0. `dirname` and
> `basename` treat a backslash as an ordinary character and MSYS mangles what is left. The
> guard against writing to a directory nobody named was itself naming the wrong directory.
> Fixed by normalising separators and replacing `dirname`/`basename` with parameter expansion;
> paths are now emitted in the host's own form (`pwd -W` where it exists), because `/c/tmp/x`
> cannot be opened by the Python and Write-tool consumers downstream.
>
> **The first version of the regression check did not catch it**, because it asserted that a
> `target_dir=` line was *present* rather than what it *said*. That is the §5.2 test 9 mistake
> in miniature: a weak assertion converts an unexamined failure into a green tick. It now
> compares the resolved value against the path supplied, and fails when the normalisation is
> reverted.
>
> **Verified by reverting it, eight ways**: script deleted; `breakdown` not calling it;
> `breakdown` calling it and then using `docs/tasks/{slug}` anyway; the sub-skill backstop
> weakened; `is_absolute` always true, so a relative target sails through; the plugin
> containment check disabled; resolution made a no-op; and separator normalisation removed.

<details><summary>Original proposal</summary>

In `breakdown` and `breakdown-generate-tasks`:

1. Require `--output-dir` to be an absolute path; reject relative paths with a clear error.
2. Refuse to write anywhere under the toolchain's own directory.
3. Echo the resolved absolute output path before writing, so a wrong target is visible
   immediately.

Then delete the stray `skills/breakdown-generate-tasks/output/` tree, which is currently only
gitignored.

</details>

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

### 4.9 Manifest completeness — **DONE**

> **Now measured, not suspected.** `manifest.json` for the §5.1 fixture declares
> `summary.total_tasks: 20` while 18 task XML files exist (`L0-001`–`L0-004`, `L1-001`–`L1-005`,
> `L2-001`–`L2-004`, `L4-001`–`L4-005`; layer 3 is empty because the fixture PRD has no
> frontend). `/execute` correctly reported 18 of 20 — the over-count originates in
> `/breakdown`.

**Addresses F9.**

> **Completed.** `skills/breakdown/scripts/build-manifest.py` builds the manifest from the
> task files on disk and verifies it, and `/breakdown` Phase 5 calls it instead of writing the
> inventory by hand.
>
> **The over-count was the smaller half.** The manifest was written from `layer_plan.json` — the
> *plan* — and never reconciled with generation. On the fixture the plan called for six Layer 0
> tasks; generation produced four, renaming all of them. The manifest kept the plan's version,
> so it was not merely over-counting: **every Layer 0 path it named pointed at a file that did
> not exist.** The other three layers matched only because generation happened to follow the
> plan one-for-one there.
>
> | | plan / old manifest | on disk |
> |---|---|---|
> | Layer 0 | 6 tasks | **4** |
> | Total | 20 | **18** |
> | Layer 0 paths resolving | 0 of 6 | 4 of 4 |
>
> The task files are the deliverable, so the task files are the source of truth. A plan revised
> during generation is the plan working, not failing — but the manifest has to follow.
>
> Also delivered: `prd.project_path` (F9 proper) and `toolchain_version` from `plugin.json`
> (a down-payment on item **4.5**). `--verify` fails on a missing `project_path`, on a count
> mismatch, and on any inventory entry naming a file that is not there.
>
> Tested against the fixture: the broken manifest was flagged with the six bad paths and the
> count mismatch; the rebuild produced 18 tasks with correct per-layer counts, real task names
> read from the XML, and preserved metadata; re-verification is clean.

### 4.10 Orphaned agent — **DONE**

**Addresses F11.** Wired in, not deleted.

> **The choice turned on which description was better.** `/execute` Step 10 already carried a
> six-step summary of the same job, so this was **two descriptions of one job with nothing
> deciding which ran** — precisely F20's shape, caught before it could cost a run. The agent's
> version is the better one: 219 lines covering idempotent handling of entries that already
> exist, file tracking, skip conditions and quality checks, none of which the summary had.
>
> Step 10 now dispatches it by `subagent_type`, which loads the agent definition by
> construction — the same mechanism 4.15 used to fix F20. The inline procedure is gone, so
> there is one description again.
>
> **The division of labour is forced by the agent's own frontmatter.** It declares
> `tools: Read Write Glob` and has no `Bash`, so it edits `PROJECT.md` and cannot commit it.
> `/execute` commits afterwards — and only if the agent reports it changed something, since
> the agent returns `{"skipped": true, ...}` when there are no exports to add and an empty
> commit would claim a context update that never happened. Agent produces content, caller owns
> git: the same split as `execute-batch` and the worktree.
>
> Completed task ids are taken from the **ledger**, not a running total.
>
> **This path has never run.** `PROJECT.md` is CRD-only and every §5.2 run has been greenfield,
> so neither the old inline version nor this one has been exercised. Specified but unproven,
> and stated as such in the skill itself. **The whole CRD half of the toolchain is in that
> position** — `/crd`, `/crd-context` and their four skills have no fixture at all.

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

### 4.12 Consolidate git ownership under forked orchestration -- **DONE**

> **Structural half completed.** `skills/execute-merge/scripts/merge-task.sh` performs the whole
> merge sequence as one program: resolve the base branch from the repository, assert the target
> is the repository root, assert the base branch has no uncommitted tracked changes, assert the
> worktree is on its own branch, clean, and at least one commit ahead, merge `--no-ff`, record
> the merge commit in the ledger, and only then remove the worktree and delete the branch.
>
> `execute-merge/SKILL.md` went from 345 lines to 183, and no longer contains a single runnable
> git command. That was the point. It was the **last git sequence in the toolchain still
> described rather than executed** -- twelve commands across ten prose steps -- and every other
> one became a script because the described version demonstrably failed: six agents retyped
> `git worktree add` and not one kept `-b` (F18); a run walked up out of the target, ran
> `git init`, and merged into the repository it had just created (F19). The merge is the step
> that decides whether a task counts as complete, which makes it the last place to leave to
> improvisation.
>
> **Two behaviour changes, both deliberate.**
>
> - **Record before cleanup**, which reverses the old step order. A crash between merge and
>   record under-reports progress, and a resume recovers from that. Cleaning up first would put
>   a failure mode -- a worktree that will not remove -- between the commit and the record of
>   it, so a merged task could go unrecorded and be done twice. Cleanup failures are now
>   warnings: tidying cannot decide whether work counts.
> - **Uncommitted changes are refused, not committed.** The old step 3 auto-committed whatever
>   it found in the worktree under a merge-agent byline. Committing work you did not write, to
>   get past a state you did not expect, is the improvisation that produced F19.
>
> **A latent gap closed on the way.** The old step 8 already used `{prd_slug}` to name the
> ledger, but `--prd-slug` was declared by nothing and passed by nobody -- `/execute` did not
> send it to `/execute-layer`, which did not send it to `/execute-merge`. It is now declared and
> threaded at all three levels, the same way `--base-branch` is.
>
> **What option 1 turned out to mean.** The item asks for git operations to move to "the
> non-forked orchestrator". There is no such thing here: `/execute` declares `context: fork`
> too, so every level of the chain forks. The achievable and actually valuable reading is
> **one owner per git operation, and that owner is a program** -- `create-worktree.sh` for
> creation (4.15), `merge-task.sh` for merging and cleanup, `record-task.sh` for the ledger.
> The merge queue itself still lives in `execute-layer`, which is correct: sequencing is a
> decision, and decisions are what the forked skills are for.
>
> **Verified by reverting it, ten ways**: script deleted; `execute-merge` not calling it;
> `execute-merge` spelling out `git merge` again; the ledger record removed; cleanup moved
> before the record; a conflict treated as success; and `--prd-slug` dropped from each of the
> four places it is declared or passed.
>
> One of those ten did not bite at first, and the reason is worth keeping: the check asserted
> `"--prd-slug" in layer`, which was satisfied by the invocation line alone, so deleting the
> *declaration* slipped past. Declaring and passing are separate failures and are now asserted
> separately. That is the same weak-assertion shape as §5.2 test 9's original criterion.
>
> The behavioural half of the acceptance test -- `git log --merges` showing one merge per task
> -- was already met by runs 6 through 10. **The script itself has now run inside a real
> `/execute`**: the §5.3 step 4 re-run invoked it 3 times, one per task, produced 3 merge
> commits, and contains no hand-written `git worktree add` or `git merge --no-ff` in any of
> its 18 transcripts. The conflict path is still exercised only by the regression suite --
> no run has produced one, which is what sequential merging is for.

<details><summary>Original proposal</summary>

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

</details>

### 4.13 Make the critical guards executable rather than advisory — **DONE**

**Addresses F15.** Option 2 was chosen, as anticipated.

> **Completed.** `skills/execute/scripts/preflight.sh` performs every precondition and
> **resolves the base branch**, printing it on stdout. That second half is deliberate: a guard
> that only says no is a hoop, and hoops stop being jumped through. Running this one is the
> cheapest way to get the base branch, so calling it is in the caller's interest.
>
> Exit 0 means proceed and here is your branch; non-zero means stderr begins `REFUSED:` and
> `/execute` stops. Thirteen paths tested: two accepted, eleven refused — no `manifest.json`,
> no `layer_plan.json`, a missing target, a target containing `docs/prd/`, a target containing
> `.claude-plugin/plugin.json`, a target inside the tasks directory, a target that is not a
> repository, a target that is a *subdirectory* of one, a nonexistent base branch, and a
> detached HEAD. It creates nothing, and in particular never runs `git init`.
>
> **Verified by run 8**: `preflight.sh` was invoked, and the run proceeded on the base branch
> it resolved.
>
> **The regression check was rewritten as the item asked.** It used to assert the guard *text*
> appeared in `SKILL.md` — which F15 showed is worth nothing, since the text was present,
> correct and ignored. It now builds real repositories in a temp directory and *runs* the
> guard against them. Proof it is worth having: disabling the `docs/prd` refusal inside the
> script, while leaving every word of the surrounding documentation intact, now fails the
> suite. The old check would have passed.

<details><summary>Original proposal</summary>

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

</details>

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
> **Verified by run 6**: 18 merge commits for 18 tasks, one worktree per task created by the
> caller, independent verification running for the first time, and 88 passing tests in the
> produced application.

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

### 4.16 Record completion as a SHA; derive counts from git, and resume from it — **DONE**

**Addresses F16.** Step 1 of
[`resumable-execution-proposal.md`](resumable-execution-proposal.md), and the precondition for
its `--resume`.

> **Completed.** Two bundled scripts:
>
> - `skills/execute-merge/scripts/record-task.sh` — appends
>   `{task_id, commit, at, attempts, verified}` to `{project_path}/.execute/<slug>/ledger.jsonl`
>   **after** verifying the commit exists with `git cat-file -e`. Refuses otherwise. The ledger
>   sits behind a self-ignoring `.gitignore`, so it never appears in the target's `git status`
>   and never touches a tracked file.
> - `skills/execute/scripts/ledger-status.sh` — re-verifies every recorded SHA and reports
>   `{recorded, verified, missing, first_unverified}`. Stops counting at the first gap, because
>   a later verified SHA is not evidence that an earlier missing one was done.
>
> `execute-merge` records before touching any counter; `/execute` recomputes `metrics` from the
> script's output before reporting, and must not report success while `missing` is non-empty.
> The hand-increments are gone, as is `elapsed_seconds`.
>
> Tested against a real repository: three tasks recorded and derived correctly; a non-existent
> commit refused with the ledger unchanged; and — the case that defines the finding — after a
> `git reset` the ledger claims 3 while only 1 verifies, naming `L1-002` as the restart point.
>
> **Resume now runs off it (proposal step 2).** `ledger-status.sh` also reports
> `verified_tasks`, and `/execute` skips exactly those, re-running everything else — including
> anything `execute-state.json` calls completed. Resuming is the **default** when the ledger has
> verified entries, because an unattended run has nobody to answer a prompt. `--reset` discards
> the record only: it never deletes commits, branches or worktrees.
>
> Tested on a scratch repository: a run interrupted after 3 of 5 tasks resumes by skipping
> exactly those 3; and when the repository is rewound *after* recording, the ledger claims 3
> while git confirms 2, so `L1-003` is reported vanished and the resume restarts there rather
> than skipping it. That second case is the silent-data-loss scenario the old state-file resume
> would have walked straight into.
>
> **Verified by run 7** — see F16. Ledger and merge commits correspond exactly, in both
> directions, and the state file's counts are finally correct.
>
> **Ledger location** follows §8.1 of the proposal: it lives with the commits it indexes so the
> two share a fate. A ledger in the tasks directory would survive a reset target and go on
> describing work that no longer exists — F16 by another route.

### 4.17 Write `execute-state.json` from a script — **DONE**

**Addresses F21.** Option 1 chosen: derive the whole file.

> **Completed.** `write-state.py` reads the ledger, re-verifies each SHA with `git cat-file -e`,
> and writes the complete file: per-task status with its commit, per-layer progress, the merge
> queue, `completed`, `missing_commits`, and a metrics block computed with `len()`. `status` is
> `completed` only when every task in the manifest has a commit that exists and nothing is
> missing or abandoned. It carries forward only the two facts that cannot be derived — which
> tasks were abandoned and which failed — and takes those as arguments rather than accumulating
> them.
>
> Tested: 18/18 on run 8's real fixture (against the hand-written 4/18); a rewound repository
> reported `in_progress 2/3` with `missing: ["L1-003"]` and that task back to `pending`;
> `--abandoned` carried through to `tasks_abandoned`; and a tasks path inside the target
> refused with exit 1, writing nothing.
>
> **Two further defects found while wiring it in**, both in `execute-layer`, both caught by the
> new regression guard rather than by reading:
>
> - the ready-queue read completion and *dependency satisfaction* from
>   `state["completed"]` — the field that has been wrong in four runs. Over-reporting there
>   would let a task start before the dependency it builds on had landed. It now reads
>   `verified_tasks` from the ledger.
> - `add_to_merge_queue` appended to `state["merge_queue"]` by hand. The queue is now derived;
>   an entry in it means a merge commit exists.
>
> The guard flags *mutations* of the state file's fields, not reads, and was verified to fail
> both on a reintroduced hand-write and on removing the script's pollution refusal.
>
> **Verified by run 9**: 38 invocations, zero hand-writes, and a state file that finally
> agrees with git.

Two defects, one cause: the file is assembled by hand. Options, in the order I would try them:

1. *(recommended)* **Derive the whole file.** A `write-state.sh` that takes the tasks path,
   project path and slug, reads the ledger and the manifest, and writes the complete
   `execute-state.json` — every field computed, none incremented, one fixed location. This is
   what worked for the manifest (4.9), the worktree (4.14), the ledger (4.16) and the preflight
   (4.13), and it fixes both halves of F21 at once: a script cannot write the file to a
   second location by accident, and cannot count to 4 when git says 18.
2. **Delete it.** The ledger already carries what resume needs, and `/execute` reports from
   `ledger-status.sh`. The state file's remaining consumers are the §5.2 harness and human
   curiosity. Simpler, but loses per-task retry history and the merge queue, which are
   genuinely useful for diagnosing a stalled run.

Whichever is chosen, `{project_path}` must never be written to except for commits, branches,
worktrees, and the self-ignoring `.execute/` ledger directory.

**Acceptance:** a run after which `git status` in the target is clean, and the state file's
counts equal `ledger-status.sh`'s.

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
| 2 | `/prd` on a fresh directory | **PASS** — PRD written, `what-next.md` valid XML with `<status>`. Re-run after 4.3 (130s): the new unconditional lookup does not disturb the fresh path. No `<toolchain-version>`: item 4.5 deferred |
| 3 | `/prd` again with no arguments | **FIXED** (was KNOWN/4.3) — detects the existing PRD in **15s** and leaves it untouched, naming it, its status and its last-modified date, then offering to extend it or start a new one alongside. `index.md` byte-identical afterwards. Marker removed; now a permanent guard |
| 4 | `/prd --resume` | **PASS** — found the existing PRD |
| 5 | `/breakdown` with a relative `--output-dir` | **FIXED** (was KNOWN/4.6) — refused in **63s**, `./relative-out` never created, nothing written to the toolchain tree. The transcript shows `resolve-output.sh` actually invoked, twice, in the forked context: the refusal is an exit code, not a judgement. Marker removed; now a permanent guard |
| 6 | `/breakdown` with an absolute `--output-dir` | **PASS** — 29 files generated in 67 min; nothing written into the toolchain tree |
| 7 | `/execute` against a repo with **no remote** | **PASS** — full plan produced, base branch resolved from HEAD. F1 fix confirmed under a real run |
| 8 | `/execute` against a path containing `docs/prd/` | **FAIL** — not refused → **F15** |
| 9 | Full `/execute` run on the fixture | **Run 1 VOID** — 83 min, reported success while 19 of 20 tasks bypassed isolation, but `--permission-mode acceptEdits` denied subagents `Bash`, so it measured the harness → **F14 withdrawn**. **Run 2 INCONCLUSIVE** — killed by the 90-minute timeout at 15/18 tasks; layer 2 isolated correctly (4 worktrees, 4 merges), layers 0–1 not at all. **Run 3 FAIL** — the first to complete: 20 tasks, **1 commit**, 0 worktrees, 0 branches, 0 merges, in 17 min → **F17**. `.git` intact and root commit preserved throughout (F2); state file fabricated its elapsed time (F16). **Run 4 FAIL** — the dispatch fix verified (18 task agents, one commit per task), but 0 of 6 `git worktree add` attempts included `-b` so all failed → **F18**, and the agents then `git init`-ed a repository at the workspace root containing the docs tree and a gitlink to `app/` → **F19**. **Run 5 FAIL** — 4.14's script invoked **0** times across 19 task agents, because not one of them ever loaded `execute-task` at all: it is *described* in an Agent prompt, not invoked → **F20**. **Run 6 PASS (2h 55m)** — 18 tasks, **18 merge commits**, 19 script invocations and 0 hand-written ones, `execute-verify` invoked 18 times, no repository outside the target, `.git` intact, and the produced application passes 88 tests. The first end-to-end success in six attempts. **Run 7 PASS (2h 36m)** — repeated it, and verified the ledger: 18 entries, exact correspondence with the 18 merge commits, `tasks_completed` 18 (was 23), no invented `elapsed_seconds` → **F16 resolved**. Exposed one gap in the fix, since closed: `status: completed` was written alongside `tasks_remaining: 2`. **Run 8 PASS (2h 22m)** — third consecutive pass; `preflight.sh` invoked (**4.13 verified**), ledger exact again at 18/18, no stray repository. Exposed **F21**: `execute-state.json` was written into the *target* repo as well, and its metrics said `completed` at 4 of 18 while git held 18 merges. **Run 10: interrupted at 11/18 by an API stall, then completed across two resumes with no task redone — see §3.7.** **Run 9 PASS (1h 59m)** — fourth consecutive pass and the first with a *truthful* state file: `write-state.py` invoked 38 times, hand-written 0 times, `18 of 18`, `git status` clean, 88 tests passing → **F21 resolved** |
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

### 5.3 CRD fixture — **RUN END TO END**

Every finding this document records came from running the greenfield path against §5.1. The
CRD half — `/crd`, `/crd-context`, `/crd-investigate`, `/crd-impact-analysis`,
`/crd-context-update`, and `project-context-finalizer` — has had **static checks only**. Item
4.10 wired an agent into a code path that has never executed.

> **Built at [`tests/fixture/setup_crd_fixture.py`](../../tests/fixture/setup_crd_fixture.py).**
> A working FastAPI application: 17 files, **5 commits**, no remote, 8 passing tests, and no
> `PROJECT.md`.
>
> **The differences from §5.1 are the point.** Greenfield starts from an empty repository;
> brownfield starts from code that already works, has history, and has a test asserting the
> behaviour a careless change would break.
>
> Choices that matter, in the same spirit as §5.1:
>
> - **It passes its own tests on a fresh build**, and the setup script says so. A brownfield
>   fixture with a broken baseline cannot tell you whether a change request broke anything.
> - **Five commits, not one.** `/crd-investigate` may reasonably read git log, and a single
>   "Initial commit" is not a brownfield project.
> - **Delete is destructive and tested.** The change request asks for archiving *alongside*
>   delete, so `test_delete_is_permanent` is the trap: a change that removes it did more than
>   it was asked to.
> - **Tags are a join table**, so impact analysis has to reason about `link_tags` rather than
>   a column.
> - **`app/api/__init__.py` re-exports the routers**, so any new endpoint edits a shared file
>   that two modules import — where unisolated parallel work shows up first.
> - **No `PROJECT.md`.** Producing it is `/crd-context`'s job and the first thing to test.
> - **The change request is prose**, deliberately unstructured. Handing `/crd` something
>   already structured would test nothing.
>
> `--verify` mirrors §5.1's F2 guard and is tested negatively: removing `app/.git` makes it
> exit 1. The static suite validates the fixture definition — that every commit places a file,
> that no commit index is out of range, and that each trap is still present — so drift fails
> in seconds rather than partway through a CRD run.

**Step 1 has now run — the first execution of any CRD skill.** It passed cleanly.

`/crd-context --project app/` invoked `crd-investigate` through the `Skill` tool (so not an
F20 case) and wrote a 202-line `PROJECT.md`. The embedded block validates:

```
<project-context version="1.0">   parses
  <meta>              3 entries, last-context-hash 59e7829412d6 == actual HEAD
  <features>          5
  <api-registry>      5   /health, /links, /links, /links/{link_id}, /links/{link_id}/tags
  <schema-registry>   3   Link, Tag, link_tags
```

Every endpoint and model is right, including the join table, and the description of
`delete-link` reads *"Intentionally has no archive/soft-delete alternative yet"* — the exact
state the change request asks to change. The target was not otherwise touched: five commits
intact, root commit reachable, `git status` showing only the new file.

**A correction worth recording, because it nearly became a finding.** On first look I read
`PROJECT.md` as "markdown, not the XML the consumers grep for" and started writing it up as a
producer/consumer mismatch. That was wrong: `crd-investigate` specifies markdown *wrapping* a
`<project-context>` XML block, so a root-level parse failure is the expected result, not a
defect. I had checked the output against my assumption before checking the spec. The lesson is
the same one this document keeps recording, pointed the other way — a plausible failure story
is not evidence, and the cheap check (read the spec) comes first.

**One open question, not a defect yet.** `PROJECT.md` is left untracked (`?? PROJECT.md`).
Whether `/crd-context` should commit it is undecided; `/execute` Step 10 does commit its
updates, so the two halves may disagree. Step 4 will settle it.

**Step 2 also passed**, and more convincingly than step 1 because it had to reason rather
than describe. `/crd` produced a 222-line CRD at `app/docs/crd/archive-links.md` with every
specified section — `meta`, `context`, `change-request`, `assumptions`, `impact-analysis`,
`requirements`, `acceptance-criteria` — typed `feature-add` rather than `modify`.

The judgements that matter:

- **It caught the buried constraint.** The change request mentions keeping delete once, in a
  casual aside in the last paragraph. The CRD makes it a *must-have*: *"`DELETE /links/{link_id}`
  behavior is unchanged: immediate, unconditional hard delete."* Missing this would have been
  the expensive failure, and it is exactly where a skimming reader drops a requirement.
- **It reasoned about the join table**, not just the model: *"Archiving and restoring a link
  never touches its tags — a restored link has exactly the same tags."*
- **`breaking-changes`: none**, which is correct — delete is untouched and the new `status`
  parameter defaults to `active`.
- Affected files: `link.py`, `schemas.py`, `api/links.py`, and both test files. Five, and right.

**Two defects found — both in the fixture, neither in the toolchain.**

1. The fixture created `<workdir>/docs/crd/`. `/crd` writes to `{project_path}/docs/crd/{slug}.md`,
   which is what its own spec says. The empty directory made a correct write look like a wrong
   one. Removed.
2. The `app/api/__init__.py` "shared file" trap was **mis-designed**. It assumed a new endpoint
   must edit the re-export; in fact the new routes go into the *existing* `links.py` router,
   which is already exported, so `__init__.py` correctly does not change. The CRD was right and
   the trap was wrong. Kept as realistic structure, no longer described as a trap.

**A note on method, since this is now a pattern.** Three times in this sequence I read an
output as a defect before reading the specification it was written against — the markdown/XML
question in step 1, the CRD's location, and the `__init__.py` omission. All three were mine.
The toolchain has earned scepticism over twenty findings, but scepticism applied before the
cheap check is just noise, and it produces exactly the kind of confident wrong story that F14
cost this project a day to unwind.

**Step 3 passed on every criterion the skill sets for itself.** `/breakdown` produced **3
tasks** where the greenfield PRD produced 18 — *"CRDs typically produce fewer tasks"* — with
**no Layer 0**, as *"CRDs are always brownfield"* requires:

```
1-foundation/L1-001-add-archived-at-column.xml
2-backend/L2-001-archive-restore-endpoints-and-status-filter.xml
4-integration/L4-001-archive-acceptance-tests.xml
```

The tasks **modify existing code** rather than creating it — `app/models/link.py`,
`app/api/links.py`, `app/schemas.py`, `tests/test_links.py`, all files that already exist —
which is the brownfield behaviour nothing greenfield could test. Item 4.9's work shows up
too: `manifest.json` records `total_tasks: 3` matching the files on disk, per-layer counts,
`toolchain_version: 2.0.0`, and `prd.project_path`.

#### F22 — the F21 guard forbids the brownfield layout

Found by step 3, before it could cost a run. **`/execute` could not have started.**

`/crd` and `/breakdown` write *into* the project — `app/docs/crd/{slug}.md` and
`app/docs/tasks/{slug}/` — so a change request and its tasks travel with the code they change.
That is deliberate and it is what both skills' specs say.

`write-state.py`'s F21 guard refused whenever the tasks path sat anywhere inside the project:

```
REFUSED: tasks path .../app/docs/tasks/archive-links is inside the target project .../app
```

The guard was written against the greenfield topology, where the tasks tree lives outside the
target, and I generalised from one layout to a rule. **F21 was never about that.** The actual
mistake was a *second* copy of `execute-state.json` at the target's **root**, alongside the
correct one — so the guard now refuses exactly that, and permits the tasks directory to sit
inside the project.

Verified against all three layouts: brownfield (tasks inside the project) writes; the project
root refuses; greenfield still writes. `preflight.sh` was already correct here — it *notes*
that the tasks directory is inside the target rather than refusing.

**Step 4 passed, and the trap held.** Three tasks, three merge commits, ledger 3/3 verified,
state file `completed`. The application went from **8 passing tests to 21** — and
`test_delete_is_permanent` is one of them. The CRD made preserving hard delete a must-have,
`/breakdown` carried it into a task, and the implementation honoured it. That is the whole
chain working on the requirement most likely to be dropped.

`project-context-finalizer` ran for the first time ever (item 4.10 wired it in; nothing had
executed it). It committed `ab91256 docs: Update PROJECT.md with features from archive-links`
and genuinely updated the registries — 5 features → 7, 5 endpoints → 7 with
`POST /links/{link_id}/archive` and `/restore`, 3 schema entries → 4 with `archived_at`
recorded.

**F22's fix held**: `execute-state.json` was written into the tasks directory *inside* the
project, which is the layout that would have been refused an hour earlier.

**Step 4 was re-run after F23, F24 and item 4.12 landed, and passed again — 794s, $3.12**
(against 1034s and $4.27 first time; the merge being one script call rather than ten prose
steps is the likely difference). Driven this time by
[`tests/fixture/run_5_3.py`](../../tests/fixture/run_5_3.py), because a sequence driven by
hand is not a sequence that can be re-run: the prompts lived in a terminal history and the
pass criteria in someone's head.

The app was reset to `e7ab199` — step 4's exact starting state, 8 passing tests, no ledger —
so this is a genuine re-execution rather than a resume. The criteria were checked against that
reset state first and correctly reported `0 of 3 tasks verified`; a check that cannot fail
proves nothing, which is what §5.2 test 9 taught.

**Verified against git and the transcripts, not the summary:**

| | |
|---|---|
| 3 merge commits, one per task | `L1-001`, `L2-001`, `L4-001`, ledger 3/3 verified, nothing missing |
| Application tests | 8 → **21 passing**, and `test_delete_is_permanent` is still among them — the trap held a second time |
| `merge-task.sh` | invoked **3 times** — its first execution inside a real `/execute` |
| `create-worktree.sh` | 3 times |
| Hand-written `git worktree add` / `git merge --no-ff` | **none, anywhere** in 18 transcripts |
| `record-task.sh` | 0 *direct* calls, and 3 ledger entries — it now runs from inside `merge-task.sh`, which is the consolidation working |
| **F23** | `PROJECT.md` parses: `meta 3, features 7, api-registry 7, schema-registry 4`. No bare ampersand this time |
| **F24** | `<last-context-hash>50d15fb…</last-context-hash>` — a real SHA, and exactly `HEAD^` |
| Containment | no stray repository at the workspace root; the toolchain tree untouched |

The stamped hash being `HEAD^` is the fix working rather than the bug persisting: `50d15fb` is
the last *merge* commit, and `903235f` — the commit carrying `PROJECT.md` — is the one after
it. `--status` accordingly reports `changed=0, stale=no`. It also proves the ordering: had the
stamp run after the commit it would have recorded `903235f`.

The finalizer genuinely updated the registries again — 5 → 7 features, 5 → 7 endpoints with
`/links/{link_id}/archive` and `/restore`, 3 → 4 schema entries.

#### F23 — the finalizer writes unescaped XML and corrupts the file it maintains — **RESOLVED, verified by the step 4 re-run**

Found by step 4. `project-context-finalizer`, on its first execution, wrote:

```xml
<description>… ?tag=python&status=archived returns only archived links …</description>
```

A bare `&` is not valid XML. The `<project-context>` block stopped parsing, which silently
breaks every consumer — `crd-impact-analysis` reads `<api-registry>` from it, and the
finalizer itself must parse the file to update it next time. **The run reported success.**

Verified precisely: the block parsed after step 1, fails after step 4, contains exactly one
bare ampersand, and escaping that one character makes it parse again. Nothing else is wrong
with it.

This is the defect this project *opened* with — 94 bare ampersands escaped so the PRD
directory would parse — reintroduced by the one component whose job is writing XML.

Fixed two ways, because one of them is prose:

- `agents/project-context-finalizer.md` now states the escaping rule with the exact failing
  example, and says the caller validates afterwards.
- `skills/execute/scripts/check-project-md.py` parses the block, escapes bare ampersands with
  `--fix`, and refuses if it is malformed for any other reason. Step 10 runs it **before
  committing**, and a non-zero exit blocks the commit. Tested on the real corruption, on the
  repair, and on a greenfield project with no `PROJECT.md` (not an error).

#### F24 — the finalizer writes a placeholder into `last-context-hash` — **RESOLVED, verified by the step 4 re-run**

*This was recorded above as "one cosmetic issue not worth a finding: off by exactly one
commit". Reading the artefact instead of reasoning about it gives a different answer.* The
`PROJECT.md` the step-4 run actually committed contains:

```xml
<last-context-hash>current-HEAD</last-context-hash>
```

The literal placeholder, not a hash — and it **replaced a valid one**. The commit before it
recorded `59e7829…`; the finalizer's commit (`ab91256`, which touched `PROJECT.md` and nothing
else) overwrote that with `current-HEAD`.

**Root cause, and it is structural.** `agents/project-context-finalizer.md` declares
`tools: Read Write Glob` — no `Bash` — while its Step 5 template asked for
`<last-context-hash>{current git HEAD}</last-context-hash>`. It cannot run `git rev-parse`, and
never could. Asked for a value it had no way to compute, it wrote the placeholder. That is the
**F20 shape**: a component instructed to do something it structurally cannot.

**Measured consequence, not inferred.** `git diff current-HEAD..HEAD` is
`fatal: ambiguous argument`. Both update paths already have a rule for that —
`crd-context-updater`: *"Invalid last-context-hash → Fall back to full investigation"* — so
every subsequent context update silently takes the most expensive operation in the CRD half of
the toolchain, forever, and reports nothing amiss. The "always in the direction of looks
slightly stale" reading was wrong twice over: the field is not off by one, it is not a hash.

**The off-by-one is real too, and separate.** `59e7829…` is exactly the parent of `e7ab199`,
the commit that recorded it. That is unavoidable rather than a bug: PROJECT.md is written
first and committed second, so a hash naming its own commit cannot exist.

Fixed by giving the field a definition under which the off-by-one disappears rather than
needing correction. **It records the commit whose *code* the context describes**, so `HEAD` at
stamp time — before the PROJECT.md commit — is exactly right. Staleness then means *commits
since that hash touching anything other than `PROJECT.md`*, because the one commit always in
between is the context write itself, and a documentation commit does not make the
documentation out of date.

Three changes:

- **`check-project-md.py --stamp-hash`** writes the real `git rev-parse HEAD` into the field.
  `/execute` Step 10 runs it **before** committing — a stamp applied afterwards is never
  committed. That step's commit and validate blocks were also in the wrong order in the
  document, which mattered more once stamping joined them.
- **The finalizer no longer touches the field.** Its template says to copy the existing element
  through unchanged, and says why: the caller has git and it does not. Agent produces content,
  caller owns git — the same division as the commit itself.
- **`--status` replaces hash-versus-HEAD comparison** in `/crd`, `/crd-context --check` and
  `--diff`, and `crd-context-updater` excludes `PROJECT.md` from the diff it analyses. Exit 0
  current, 3 stale with the changed files listed, 1 when the recorded hash is not a commit in
  the repository.

**Verified by reverting it, seven ways**, including against the real corrupted artefact: the
script deleted; the finalizer told to fill the field from a placeholder again; `--stamp-hash`
dropped from the command; stamping moved after the commit; an unusable hash accepted;
`PROJECT.md` counted as a code change again (the off-by-one returning); and `--stamp-hash`
writing a placeholder instead of `HEAD`.

Two of those seven initially passed, because the check asserted `"--stamp-hash" in ex` — which
was satisfied by the *paragraph explaining the flag* rather than by the command running it. It
now matches the invocation line and its position relative to the commit. That is the third time
in this project a substring check has passed while the mechanism it names was absent; the
pattern is always the same, and so is the fix: **assert the command, not the prose about it.**

---

**All four steps have now run.** The brownfield path works end to end, and found two defects
doing so (**F22**, **F23**) — the first defects from a half of the toolchain that had only
ever had static checks. **F24** came later, from reading the `PROJECT.md` that run left
behind rather than the report of it.

| # | Step | Result |
|---|---|---|
| 1 | `/crd-context` on `app/` | **PASS** — see below |
| 2 | `/crd` on the change request | **PASS** — see below |
| 3 | `/breakdown` on the CRD | **PASS** — and it found **F22** |
| 4 | `/execute` | **PASS** — the trap held; found **F23** |

Step 4 is the one that matters: it is the first execution of `project-context-finalizer`, and
the first time the toolchain modifies code it did not write.

---

## 6. Summary table

| # | Item | Grade | Files |
|---|---|---|---|
| ~~4.11~~ | ~~Remove `allowed-tools` — restores forking~~ **DONE** | ~~Blocking~~ | all 15 `skills/*/SKILL.md` |
| ~~4.1~~ | ~~Command→skill conversion, frontmatter~~ **DONE** -- F8 resolved; all three entry points stay commands | ~~Consistency~~ | `commands/*.md` |
| ~~4.2~~ | ~~Model assignments, skills and agents~~ **DONE** — F5, F6, F7 resolved; suite fully green | ~~Correctness~~ | all skills, all agents |
| ~~4.3~~ | ~~Resume detection and overwrite guard~~ **DONE** — F3 resolved | ~~Correctness~~ | `prd` |
| 4.4 | `what-next.md` template | Correctness | `prd`, existing artefacts |
| 4.5 | Toolchain version stamping | Structural | `prd`, `breakdown`, `execute` |
| ~~4.6~~ | ~~Absolute output path guard~~ **DONE** — F4 resolved, verified by §5.2 test 5 | ~~Correctness~~ | `breakdown`, `breakdown-generate-tasks` |
| ~~4.7~~ | ~~Layer 0 git contradictions~~ **DONE** (guard part ineffective, see 4.13) | ~~Blocking~~ | `breakdown-generate-tasks`, `breakdown`, `execute` |
| ~~4.12 step one~~ | ~~Synchronous dispatch~~ **DONE `d278c05`** — F17 fixed, verified by run 4 | ~~Blocking~~ | `execute-batch` |
| ~~4.15~~ | ~~Create the worktree before dispatch~~ **DONE `c915422`** — F20 resolved, verified by run 6 | ~~Blocking~~ | `execute-batch`, `task-implementer` |
| ~~4.14~~ | ~~Worktree creation as a script~~ **DONE `b6a0a86`** — inert until 4.15 landed, then load-bearing | ~~Blocking~~ | `execute-batch/scripts/` |
| ~~4.16~~ | ~~Record completion as a SHA; derive counts from git~~ **DONE** — F16 fixed, run pending | ~~Correctness~~ | `execute-merge`, `execute`, `scripts/` |
| ~~4.17~~ | ~~Write `execute-state.json` from a script~~ **DONE** — F21 resolved, verified by run 9 | ~~Correctness~~ | `execute/scripts/`, `execute-batch`, `execute-merge`, `execute-layer` |
| ~~4.12~~ | ~~Consolidate git ownership~~ **DONE** -- the merge is a script; no git command left in `execute-merge` | ~~Structural~~ | `execute-merge`, `execute-layer`, `execute` |
| ~~4.13~~ | ~~Make critical guards executable~~ **DONE** — F15 resolved; the check now runs the guard | ~~Correctness~~ | `execute/scripts/`, `tests/test_toolchain.py` |
| ~~4.8~~ | ~~`git pull origin main` guard~~ **DONE** | ~~Blocking~~ | `execute-task`, `execute-merge`, `execute`, `execute-layer`, `execute-batch` |
| ~~4.9~~ | ~~Manifest completeness~~ **DONE** — built from task files, not the plan; F9 resolved | ~~Consistency~~ | `breakdown`, `breakdown/scripts/` |
| ~~4.10~~ | ~~Orphaned agent~~ **DONE** — wired into Step 10; F11 resolved, guard added | ~~Structural~~ | `execute`, `agents/project-context-finalizer.md` |

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
| ~~4~~ | Should `/prd`, `/crd` or `/crd-context` become skills? | **No — all three stay commands.** Fork to isolate expensive reasoning, not to obtain a `model:`. See 4.1 |
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
