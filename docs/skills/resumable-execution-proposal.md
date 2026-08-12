# Resumable, Usage-Aware Execution — Feature Proposal

**Status:** proposed, not implemented
**Date:** 2026-08-11
**Subject:** `/execute` — safe interruption, checkpoint/resume, and subscription usage awareness
**Depends on:** finding **F16** (`execute-state.json` is not a truthful record) — see
[`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md)

> **The headline is not the usage endpoint.** The valuable property is that a run can be
> interrupted at any moment — by a usage limit, a crash, a dropped network, or Ctrl-C — and
> resumed from the last *verified* completed task with no lost or duplicated work. Usage
> awareness is one trigger for a stop that has to be safe regardless of what caused it.

---

## 1. The problem

A `/breakdown` of a modest three-feature PRD produced 18 tasks. The first full `/execute` on
that fixture ran **83 minutes**. A realistic 60-task PRD is a multi-hour proposition, and a
Claude subscription enforces a **5-hour rolling window** and a **weekly** cap.

Three things go wrong today when a long run meets a limit:

1. **The run stops wherever it happens to be**, mid-task, with no checkpoint.
2. **The retry loop makes it worse.** `execute-task` retries five times; against a limit that
   will not lift for hours, that is five guaranteed failures burning the remaining allowance.
3. **Resume is not trustworthy.** §5.2 test 9 produced an `execute-state.json` claiming
   20/20 tasks complete when git contained **one** merge commit. A `--resume` against that
   state would skip seventeen tasks that were never done — silent data loss, worse than
   crashing.

Point 3 is the one that matters. Everything else in this proposal is inert without it.

---

## 2. What is actually reachable

### 2.1 Subscription usage — an undocumented endpoint

`GET https://api.anthropic.com/api/oauth/usage`, authenticated with the OAuth bearer token in
`~/.claude/.credentials.json`, returns the subscription window state. Verified live:

```json
{
  "five_hour": { "utilization": 14.0, "resets_at": "2026-08-11T17:30:00Z",
                 "limit_dollars": null, "used_dollars": null },
  "seven_day": { "utilization": 21.0, "resets_at": "2026-08-12T22:00:00Z" },
  "limits": [
    { "kind": "session",       "group": "session", "percent": 14, "severity": "normal",
      "resets_at": "2026-08-11T17:30:00Z", "is_active": false },
    { "kind": "weekly_all",    "group": "weekly",  "percent": 21, "severity": "normal",
      "resets_at": "2026-08-12T22:00:00Z", "is_active": true },
    { "kind": "weekly_scoped", "group": "weekly",  "percent": 0,  "severity": "normal",
      "scope": { "model": { "display_name": "Fable" } }, "is_active": false }
  ]
}
```

`HTTP 200` with or without the `anthropic-beta: oauth-2025-04-20` header.

**Treat this as an internal surface.** The response also contains fields named `tangelo`,
`iguana_necktie`, `nimbus_quill`, `omelette_promotional`, `cinder_cove` and `amber_ladder` —
codenamed feature flags. There is no deprecation contract here: the path, the shape, and the
field names can change without notice.

Consume only `five_hour`, `seven_day`, and `limits[]`. Ignore everything else, including the
dollar fields, which are `null` on this plan.

### 2.2 What the documented API gives instead

The public REST API exposes remaining allowance as **response headers**
(`anthropic-ratelimit-*-remaining`, `-reset` in RFC 3339) and offers a Rate Limits API for
reading *configured* limits. Neither helps here:

- Those are **organisation API rate limits** — per-minute RPM/ITPM/OTPM token buckets. A
  different quota system from the subscription window, and healthy right up until the
  5-hour window closes.
- They arrive as headers on a response. `claude -p` does not surface response headers, so a
  skill cannot read them.

### 2.3 Fallbacks when 2.1 is unavailable

The endpoint is subscription-only and undocumented. Two independent guards cover its absence:

| Guard | Applies when | Signal |
|---|---|---|
| **Elapsed wall clock** | always | The 5-hour window is *time*-based, so `--max-runtime` is a well-matched proxy needing no API at all |
| **Accumulated cost** | always | `total_cost_usd` in each `claude -p` result JSON, summed across tasks |

Both are strictly worse than the real signal and strictly better than nothing.

---

## 3. Design

### 3.1 The checkpoint contract — the load-bearing part

**A task is complete when, and only when, a commit exists in the target repository.** Not
when a status field says so.

Each task, on success, produces exactly one commit (or merge commit), and the orchestrator
appends one line to a ledger recording:

```json
{ "task_id": "L2-001", "commit": "3b6632d…", "at": "2026-08-11T14:22:03Z",
  "verified": true, "attempts": 1 }
```

Three rules make this trustworthy:

1. **Record the SHA, never an adjective.** A status of `"completed"` cannot be checked; a SHA
   can — `git cat-file -e <sha>` either succeeds or it does not.
2. **Append after the commit, never before.** A crash between the two under-reports progress,
   which is recoverable. The reverse over-reports, which is the F16 failure.
3. **Git is the source of truth; the ledger is an index into it.** On any disagreement, git wins.

This is the same shape superpowers' `subagent-driven-development` uses, and for the same
stated reason: *"the commits it names exist in git even when your context no longer remembers
creating them."*

### 3.2 Resume

`/execute --resume` rebuilds progress from evidence rather than trusting the file:

```
for each ledger entry, oldest first:
    git cat-file -e <commit>   →  present? task is done
                               →  missing? task is NOT done, and neither is anything after it
resume at the first task without a verified commit
```

An entry whose SHA is absent means the repository was reset, rebased, or the ledger was
written optimistically. Stopping the scan there is deliberate: a later verified SHA after an
unverified gap is not evidence the gap was filled.

**Partial work from an interrupted task is preserved but never counted.** Its branch or
worktree stays for inspection; the task re-runs from its last verified base.

### 3.3 The usage guard

```
before dispatching each task:
    usage = poll()                        # fail-open, see below
    if usage is unknown:            proceed
    if five_hour.utilization >= STOP:     checkpoint and stop
    if seven_day.utilization >= STOP:     checkpoint and stop
    if either >= WARN:                    log, continue
```

Four properties, in order of importance:

- **Fail-open.** Any error — non-200, timeout, changed schema, missing credentials file,
  API-key user — is treated as *unknown* and the run **proceeds**. An undocumented endpoint
  that breaks after a Claude Code update must never halt a working pipeline.
- **Checked between tasks, never inside one.** Stopping mid-task wastes the task. Stopping
  immediately after a commit costs nothing.
- **Stop, don't retry, on a limit error.** If a task fails with a rate/usage error rather
  than a code error, the retry loop must not consume its five attempts. Distinguish the two
  and treat a limit as a stop condition.
- **Thresholds are configurable, defaults conservative.** `--stop-at-usage` defaulting to
  ~85% leaves headroom for the task in flight plus the merge.

### 3.4 The stop message

A graceful stop is only graceful if the operator knows what happened and what to do:

```
STOPPED: 5-hour usage at 87% (limit resets 17:30 UTC, in 1h 12m)

Completed: 11/20 tasks, last verified commit 3b6632d (L2-001)
Remaining: 9 tasks
Resume:    /execute docs/tasks/link-shelf --project-path ./app --resume
```

`resets_at` comes straight from the endpoint. When the stop came from the wall-clock or cost
guard instead, the same message reports that trigger and omits the reset time.

### 3.5 Where it lives — not in a skill

The guard belongs in the **orchestrator**, and the orchestrator should be a script.

- A skill cannot cleanly make an HTTP request, parse JSON, and branch on the result.
- A skill **should not read `~/.claude/.credentials.json`**. Shipping a skill that reads a
  credentials file is a materially worse thing to distribute than one that does not, whatever
  it does with the contents.
- F15 established that prose guards in skills are advisory — `/execute` reasoned past both the
  `docs/prd/` refusal and its own preflight. A threshold check written as prose would be
  ignored the same way.

This is the same conclusion as item 4.13, reached from a different direction.

---

## 4. What this does not solve

- **It does not make the limit go away.** A 60-task PRD that needs six hours will take two
  sittings. The feature makes that cost one clean pause instead of a corrupted tree.
- **It cannot stop cleanly mid-task.** If the window closes between two tool calls, that task
  is lost and re-runs. Task granularity is the resolution of the checkpoint.
- **It does not fix F14.** Worktree isolation and resumability are independent; a resumable
  run that skips isolation is still wrong.
- **It is subscription-only.** API-key users fall back to §2.3.

---

## 5. Testability

The pause/resume path can be tested **without exhausting a real limit**, which is what makes
this shippable rather than hopeful:

| # | Test | Passes when |
|---|---|---|
| 1 | `--stop-at-usage 0` on the §5.1 fixture | Stops before task 1; no commits; clear message |
| 2 | `--stop-at-usage 0` after N tasks (injected) | Stops after task N; ledger has N verified SHAs |
| 3 | `--resume` after test 2 | Starts at task N+1; does not redo 1..N |
| 4 | `--resume` with a ledger SHA hand-deleted from git | Treats that task as not done and re-runs it |
| 5 | Endpoint returns 404 / garbage / times out | Run proceeds unaffected (fail-open) |
| 6 | Kill the run mid-task, then `--resume` | Restarts the interrupted task; earlier work intact |

Tests 4, 5 and 6 are the ones worth writing first — they cover the failure modes that turn a
safety feature into a data-loss feature. Test 5 in particular must be a real test, not an
assumption: fail-open is the property most likely to regress silently.

---

## 6. Implementation order

Each step is independently useful, and the order is a dependency chain rather than a
preference:

| # | Step | Why here |
|---|---|---|
| ~~1~~ | ~~**Truthful ledger — SHA per task, appended after commit**~~ **DONE** (`f2049d2`, verified by run 7) | Fixed F16 |
| ~~2~~ | ~~**`--resume` verifies SHAs against git**~~ **DONE** — resume is now driven by `verified_tasks`, and is the default when the ledger has entries | Interruption is now survivable |
| 3 | **Wall-clock and cost guards** (`--max-runtime`, `--max-cost`) | No API dependency; works for every auth mode |
| 4 | **Limit-error detection in the retry loop** | Stops five doomed retries against a closed window |
| 5 | **Usage guard against the endpoint** | The precise signal, once stopping is already safe |
| 6 | **Stop message with `resets_at`** | Operator ergonomics |

Steps 1 and 2 deliver most of the value: after them, *any* interruption is recoverable.
Steps 3–6 change how gracefully the stop is chosen, not whether it is safe.

---

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Undocumented endpoint changes or disappears | Medium | Fail-open; guards in §2.3 cover its absence; consume only three fields |
| Ledger and git diverge | **High** | Git is authoritative; SHAs verified on every resume; never trust a status field |
| Resume duplicates work | Medium | Resume at the first *unverified* task; a task that committed is never re-run |
| Resume skips work | **High** | Scan stops at the first missing SHA rather than continuing past the gap |
| Credentials handling | Medium | Read only in the orchestrator script; never log the token; never in a skill |
| Threshold too low | Low | Configurable; a premature stop is safe and resumable — the failure is benign by design |

The two **High** rows are the same failure in opposite directions, and both are addressed by
the same rule: verify SHAs, and stop scanning at the first gap.

---

## 8. Decisions taken

### 8.1 The ledger lives in the target repository

```
{project_path}/.execute/<slug>/ledger.jsonl
{project_path}/.execute/.gitignore          # contains a single line: *
```

**Rationale — index and evidence must share a fate.** The ledger is an index into git; its
entries are meaningless anywhere else. A ledger in the tasks directory *survives* the target
repository being reset, re-cloned, or recreated, and then names SHAs that no longer exist —
F16 reappearing by another route, a record outliving its evidence. Co-located in the target,
it dies with the commits it references and cannot drift independently.

Second reason: **one task set can be executed against several targets.** `/breakdown` output
is reusable — the same 18 tasks may be run into a fresh repo after an abandoned attempt. A
tasks-directory ledger implicitly assumes one execution; a target-side ledger gives one per
target for free.

The **self-ignoring `.gitignore`** is what makes writing into the user's repository
acceptable: it keeps the directory out of `git status` and out of accidental commits *without
modifying any tracked file*. It lives in the working tree rather than under `.git/`, which
Claude Code treats as a protected path and denies agent writes to. This is the mechanism
superpowers' `sdd-workspace` script uses, for the same reasons.

Two consequences accepted knowingly:

- **`git clean -xdff` destroys it.** Acceptable — `git log` is the source of truth and the
  ledger is an index; recovery means re-deriving from commit messages.
- **Regenerating tasks can stale it.** If `/breakdown` re-runs and task IDs shift, the ledger
  references IDs that no longer mean the same thing. Record a `manifest` hash in the ledger
  header so resume detects the mismatch rather than acting on it.

### 8.2 `--resume` is the default when a ledger exists

A bare `/execute` with a ledger present resumes from the last verified task rather than
prompting. Prompting cannot work for the unattended overnight runs this feature exists to
support — and after §8.1, resuming is the safe default: verification is against git, so a
resume with nothing verified simply starts from the beginning.

`--reset` remains the explicit way to discard progress and start fresh, and should say how
many verified tasks it is about to abandon before doing so.

### 8.3 The threshold defaults to 85% and is overrideable

`--stop-at-usage <percent>`, defaulting to `85`. The right value depends on what a single task
costs relative to the window, which the §5.1 fixture can measure — treat 85 as a starting
point to be tuned, not a finding. A premature stop is safe and resumable by design, so erring
low costs little.

### 8.4 `/breakdown` gets the same guard, on weaker evidence

Test 6 in §5.2 ran 67 minutes — long enough to meet a window. `/breakdown` has no commits to
verify against, but it is not checkpoint-less: it already writes per-layer `.done` markers
alongside the generated task files. That is the same principle in weaker form — **verify the
artifact exists** rather than trust a status field — with files as the evidence instead of
commits.

Two known gaps, which is why this is lower priority than the `/execute` work:

- The checkpoint granularity is a whole layer, so an interrupted layer is re-generated.
- Existing `.done` resumption cannot distinguish *resumed deliberately* from *inherited
  someone else's partial run*. This is not hypothetical: it silently contaminated §5.2 test 6,
  which resumed from test 5's markers and generated only three of four layers while reporting
  success.

## 9. Open questions

1. **Should the ledger header record a manifest hash?** §8.1 argues yes — it is the only way
   resume can detect that the task set was regenerated underneath it. Cheap to add; the
   question is whether a mismatch should warn or refuse.
2. **What locks a target against two concurrent runs?** Target-side ledgers make a lock file a
   natural companion, but nothing currently prevents two `/execute` invocations against one
   repository.
