# Model and Effort Tiering — Proposal

**Status:** proposed; nothing implemented, nothing measured in a live run
**Date:** 2026-09-10
**Subject:** the `effort:` frontmatter key across `skills/` and `agents/`, and two model
reassignments on the breakdown path
**Relates to:** **C7** ([`sdd-comparison.md`](sdd-comparison.md)) · item 18 and item 27
([`plugin-2.0-plan.md`](plugin-2.0-plan.md)) · **F6** and **F13**
([`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md))

> **The headline is not the new key.** Two structural facts came out of looking for it, and both
> outlive any level this proposal picks. First, **`effort:` does not exist on Haiku** — so the
> dial is absent from exactly the half of the toolchain where tiering was the cost decision, and
> on those six skills the key parses, is stored, and is then dropped with no warning. Second,
> **six of ten agents have inert `model:` declarations**, shadowed by the skill that forks them;
> `effort:` inherits the same shadowing. The levels chosen below are the least durable part of
> this document.

---

## 1. What `effort:` is

### 1.1 Provenance of everything in this section

Read by static string extraction from the shipped CLI binary — `~/.local/bin/claude.exe`,
**v2.1.267** — on 2026-09-10. **Nothing here was observed in a live run.** Every claim in §1 is
"the parser is written this way", not "this was seen to happen". §6 lists what that leaves open.

### 1.2 Where it is accepted

The skill frontmatter schema extends the same base object commands use, and that base declares:

```
effort: "Thinking effort for the model: `low`, `medium`, `high`, `max`, or an integer."
```

The agent schema carries its own copy (`"Reasoning effort level for this agent. Either a named
level or an integer"`). So `commands/*.md`, `skills/*/SKILL.md` and `agents/*.md` all accept it.

Values parsed: `low | medium | high | xhigh | max`, plus the aliases `med` → `medium` and
`ultracode` → `xhigh`, plus any integer. **The description string above omits `xhigh`**; the
level list (`["low","medium","high","xhigh","max"]`) includes it. The hint is stale, not the
parser — but see **E3**.

Unlike `allowed-tools` (**F13**), `effort` sits in the shared base schema and does **not**
disable `context: fork`.

### 1.3 The default is `high`

`nQe(model) = catalog.default_effort ?? "high"`, and the string coercion also falls back to
`"high"`. No `default_effort` values are compiled into the binary — the field arrives on the
fetched model catalog.

**Consequence: `effort: high` is a no-op declaration.** Only `low`/`medium` and `xhigh`/`max`
change anything. This proposal therefore never writes `high`.

### 1.4 Haiku has no effort dial

```js
function Ak(e){ let t=Bse(e,"effort"); if(t!==void 0) return t;
  let r=uo(e);
  if(r.includes("claude-3-")||r==="claude-opus-4-0"||r==="claude-opus-4-1"
     ||r==="claude-sonnet-4-0"||r==="claude-sonnet-4-5"||r==="claude-haiku-4-5") return !1;
  if(ut(process.env.CLAUDE_CODE_ALWAYS_ENABLE_EFFORT)) return !0;
  ...
```

`claude-haiku-4-5` is excluded by name, and the exclusion is checked **before**
`CLAUDE_CODE_ALWAYS_ENABLE_EFFORT` — so that escape hatch cannot reach it either. Only a model
catalog capability row (`Bse`) could, and the bundled API reference independently states effort
errors on Haiku 4.5. Two sources, same answer.

Downstream, `zfe(model, effort)` returns `undefined` when the model has no dial, and downgrades
`max` → `high` and `xhigh` → `high` on models lacking those levels. **All three are silent.**

### 1.5 Precedence

Highest wins:

| Rank | Source |
|---|---|
| 1 | `CLAUDE_CODE_EFFORT_LEVEL` (environment) |
| 2 | the **skill's** declared `effort` — `skill.effort ?? agent.effort`, then written onto the agent config |
| 3 | the **agent's** declared `effort` |
| 4 | the model's `default_effort`, else `high` |

Then clamped by `maxEffortLevel` in settings and by any organisation per-model cap; lowest wins.

Rank 2 over rank 3 is the same shape as the `model:` rule in **F6** — the skill wins, and the
agent's declaration is the one silently ignored.

For an inline (non-forked) skill or command, the value is pushed as a `{kind: "effort"}` context
layer over the main loop, scoped to the invocation rather than the session.

---

## 2. Why this lands awkwardly on this repository

Current declarations, all fifteen skills and ten agents:

| Model | Skills | Agents | Effort available? |
|---|---|---|---|
| `claude-opus-5` | breakdown, breakdown-generate-tasks | task-generator | yes |
| `claude-sonnet-5` | crd, crd-investigate, execute, execute-layer, execute-batch, execute-merge, migrate | crd-investigator, prd-criteria-author, schema-migrator | yes |
| `claude-haiku-4-5` | breakdown-analyze-prd, breakdown-plan-layers, breakdown-review-tasks, crd-context-update, crd-impact-analysis, execute-verify | crd-context-updater, crd-impact-analyzer, project-context-finalizer, task-implementer, task-reviewer, verification-runner | **no** |

**No skill, agent or command declares `effort:` today.** Six of fifteen skills and six of ten
agents cannot use it at all.

And of those ten agents, only four have a *live* model declaration — the other six are `agent:`
fork targets whose model and effort are both shadowed by the calling skill:

| Agent | Reached via | Declaration |
|---|---|---|
| task-generator, task-reviewer, crd-context-updater, crd-impact-analyzer, crd-investigator, verification-runner | forked from breakdown-generate-tasks, breakdown-review-tasks, crd-context-update, crd-impact-analysis, crd-investigate, execute-verify | **inert** |
| task-implementer, prd-criteria-author, project-context-finalizer, schema-migrator | dispatched directly via the Task tool | live |

---

## 3. The proposal

Arrows are steps on `low → medium → high → xhigh → max`, relative to the `high` default.

| Entity | Kind | Current model | Current effort | Target model | Target effort | vs default |
|---|---|---|---|---|---|---|
| [`breakdown-analyze-prd`](../../skills/breakdown-analyze-prd/SKILL.md) | skill | `claude-haiku-4-5` | — | `claude-sonnet-5` | — | — |
| [`breakdown-review-tasks`](../../skills/breakdown-review-tasks/SKILL.md) | skill | `claude-haiku-4-5` | — | `claude-sonnet-5` | — | — |
| [`task-reviewer`](../../agents/task-reviewer.md) | agent | `claude-haiku-4-5` | — | `claude-sonnet-5` | — | — |
| [`crd-investigate`](../../skills/crd-investigate/SKILL.md) | skill | `claude-sonnet-5` | — | `claude-sonnet-5` | `xhigh` | ⬆️ |
| [`execute-layer`](../../skills/execute-layer/SKILL.md) | skill | `claude-sonnet-5` | — | `claude-sonnet-5` | `medium` | ⬇️ |
| [`execute-batch`](../../skills/execute-batch/SKILL.md) | skill | `claude-sonnet-5` | — | `claude-sonnet-5` | `medium` | ⬇️ |
| [`execute-merge`](../../skills/execute-merge/SKILL.md) | skill | `claude-sonnet-5` | — | `claude-sonnet-5` | `low` | ⬇️⬇️ |

Rows whose target effort is `—` stay undeclared and land on the `high` default; the change there
is model only.

### 3.1 Row rationale

**`breakdown-analyze-prd` — model.** This is **C7**, and the only row with a measurement behind
it: the corpus is 64 feature files at ~594 KB ≈ 165k tokens against a 200k window, graded
Blocking. [`sdd-comparison.md` §7](sdd-comparison.md) states the position — "the assignment
should either change model or refuse". **Contingent**: item 18's per-feature split makes Haiku
defensible again, and if 18 lands first this row should be withdrawn rather than applied.

**`breakdown-review-tasks` — model.** The reviewer sits a tier below the generator it gates
(`task-generator` is `claude-opus-5`).
[`review-criteria.md`](../../skills/breakdown/references/review-criteria.md) is 220 lines of
structured rubric; criteria 1, 1b, 2 and 7 are presence-and-count checks with named patterns to
flag, which is genuinely Haiku-shaped work and a real argument for the status quo. Criterion 4
(Requirements Specificity) and the warning criteria Context Quality and Objective Clarity are
not — they are judgement, and a small model fails them by *passing* things it should flag. Since
`pass: true` requires zero critical issues, under-flagging criterion 4 is silent. **Unmeasured**
— see **E6**, which is the experiment that should decide this row.

**`task-reviewer` — model, for consistency only.** Strictly a no-op on today's paths: the skill
forks into it, so the skill's model wins. Changing it anyway because leaving it on Haiku makes
the file state the opposite of what executes — the divergence **F6** already catalogues.

**`crd-investigate` — `xhigh`.** One shot, output is `PROJECT.md`, and every brownfield path
downstream reads it. The clearest case in the repository for spending more.

**`execute-merge` — `low`.** 190 lines, sequential, one well-defined merge per invocation.

**`execute-layer` / `execute-batch` — `medium`, not `low`.** Lower effort consolidates tool
calls and shortens preamble. `execute-batch` is 521 lines with a mandatory red/green cycle;
`low` is where a step gets skipped quietly. `medium` is the defensible step-down. See **E5**.

---

## 4. What is assumed

Every item here is load-bearing and none is measured.

| # | Assumption | If wrong |
|---|---|---|
| A-a | The fetched model catalog does not set `default_effort` for `claude-opus-5` / `claude-sonnet-5`, so the default really is `high` | the `—` rows stop being no-ops and the arrows are miscounted |
| A-b | The catalog's `Bse(model,"effort")` row does not re-enable effort on `claude-haiku-4-5` | the six Haiku skills gain a dial and §2's conclusion softens |
| A-c | The precedence table in §1.5 describes runtime behaviour, not just parse order | a declared effort may never reach the API |
| A-d | `effort` shadowing follows `model` shadowing for `agent:` fork targets (the code reads that way; **F6** measured it only for `model`) | the six inert agents are not inert for effort, and levels must be set in two places |
| A-e | The CLI's own level descriptions describe the actual behavioural difference | every level choice in §3 is arbitrary |
| A-f | No `CLAUDE_CODE_EFFORT_LEVEL` is set in the environments this toolchain runs in | rank 1 overrides all of §3 and the whole proposal is inert |

---

## 5. What is deliberately not proposed

- **`breakdown-plan-layers` stays on Haiku.** [`plugin-2.0-plan.md`](plugin-2.0-plan.md) argues
  the fixed layer graph exists *because* the model is small — "a strong prior that stops it
  inventing a bad decomposition". Haiku and the guardrail are a pair. **Item 27**, which removes
  the fixed graph, is what would force the model question; it should not be reopened before then.
- **`task-implementer` stays on Haiku.** Its model is live and it writes the code, so it is the
  obvious candidate — but [`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md)
  already concluded "Haiku is a defensible choice here" on the grounds that the task XML is
  specified tightly enough. Not reopened on no new evidence.
- **`execute` and `migrate` keep the default.** Both are plausible step-downs; both are places
  where a silent wrong answer corrupts state (`execute-state.json`; a migrated artefact). Not a
  trade to make unmeasured.
- **No level is proposed for `prd-criteria-author`, `project-context-finalizer` or
  `schema-migrator`.** All three have live declarations and all three are plausible, but none has
  been read. See **E8**.

---

## 6. What is left to answer

| # | Question | How to settle it |
|---|---|---|
| **E1** | Does a forked skill's declared `effort` reach the API at all? | A hook payload carries `effort: {level}` (built by the CLI alongside `session_id` / `permission_mode`). Register a hook, run one forked skill with `effort: low`, read the level. Settles A-c. |
| **E2** | Does the skill's `effort` override the agent's, as §1.5 claims? | Same harness: skill `low`, agent `max`, observe which arrives. Settles A-d. |
| **E3** | Is `xhigh` accepted in frontmatter, given the schema hint omits it? | Declare it on one sonnet-5 skill and read the hook payload. A validation warning would show at load. |
| **E4** | Does `effort:` on a Haiku skill warn, or fail silently? | Predicted silent. If so it is the same failure class as **F6**/**F13** and needs the §7 guard. |
| **E5** | Do the down-steps skip procedural steps? | Run `execute-batch` at `medium` against a fixture and assert the red/green cycle still produces a failing test before a passing one. The row most likely to regress. |
| **E6** | **Are criterion 4 and the warning criteria gradeable by Haiku?** The real question behind the `breakdown-review-tasks` row. | Build a small eval: N generated tasks seeded with known criterion-4 defects, review at Haiku and at Sonnet 5, compare flag rates. If Haiku catches them, withdraw the row — the rubric split is unnecessary. |
| **E7** | Does item 18 land before this? | If yes, withdraw the `breakdown-analyze-prd` row; C7's own resolution says Haiku becomes defensible once analysis is per-feature. |
| **E8** | Should the four live-declaration agents move? | Read `task-implementer`, `prd-criteria-author`, `project-context-finalizer`, `schema-migrator` and assess each. Separate pass. |
| **E9** | What does this cost? | Nothing here is budgeted. Three down-steps save; `xhigh` on crd-investigate and two Haiku→Sonnet moves spend. Net direction unknown — and C7's complaint, "a cost decision dressed as an architecture", applies to this document too until it is measured. |
| **E10** | Is `CLAUDE_CODE_EFFORT_LEVEL` set anywhere in CI or the local harness? | One `env` check. Settles A-f. |

**E6 and E9 are the two that should gate implementation.** E6 decides the most consequential row;
E9 is the measurement whose absence this repository has already named as a defect once.

---

## 7. The guard this needs

`effort` fails the way **F6** and **F13** fail: accepted, ignored, silent. The regression suite
already enforces the absence of `allowed-tools`; the matching assertion here is that **no skill or
agent declares `effort:` alongside a model on the exclusion list** (`claude-3-*`,
`claude-opus-4-0`, `claude-opus-4-1`, `claude-sonnet-4-0`, `claude-sonnet-4-5`,
`claude-haiku-4-5`).

Without it, a later `model:` change from `claude-sonnet-5` to `claude-haiku-4-5` turns the effort
off with nothing to say so — which is precisely how this repository acquired **F6** and **F13**.

Per [`schema/checks.md`](../../schema/checks.md) the assertion needs one owning script and every
caller listed. Per the mutation convention it is not finished until it has been watched failing.
