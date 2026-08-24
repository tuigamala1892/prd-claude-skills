# Plugin 2.0 — PRD Fidelity Plan

**Status:** Proposed. Nothing here is implemented yet.
**Date:** 2026-08-17
**Subject:** what `/prd` writes, and how much of it survives into `/breakdown` and `/execute`
**Supersedes:** items **4.4** and **4.5** of [`toolchain-assessment-and-plan.md`](toolchain-assessment-and-plan.md), which are folded in below as items 12 and 18.
**Evidence base:** a sample PRD corpus of 64 feature files (~594 KB, ~165k tokens), measured rather than assumed.

---

## 1. Scope, and how this differs from the assessment

The assessment plan fixed the toolchain's *mechanics* — forking, worktrees, merges, state, path
resolution. All of that now works end to end. This plan is about **fidelity**: the assessment
never asked whether the content a PRD carries actually reaches the code.

It does not. Measured against a real corpus, `/prd` writes four kinds of content and the
pipeline consumes one of them:

| What `/prd` writes | Consumed downstream? |
|---|---|
| `<description>` | Yes — via `analysis.json` summaries |
| `<acceptance-criteria>` (up to 36 per feature) | **No** — no consumer on the PRD path (P2) |
| `<notes>` (up to 28 KB per feature) | **No** — zero consumers anywhere (P4) |
| MoSCoW priority | Extracted into `analysis.json`, then **never read** (P1) |

Three quarters of the document is written and discarded. Everything below follows from that.

Findings use the same grades as the assessment (Blocking / Correctness / Consistency /
Structural / Measured) and are numbered **P1–P17** so they do not collide with its F1–F24.

**Verification status is stated per finding.** "Static" means every file in `skills/`,
`commands/` and `agents/` was searched and the consumer does not exist. "Measured" means a
script was run against the corpus and its output is reproduced. Two items are explicitly
**unverified** and carry a probe to run rather than a fix to apply.

---

## 2. What the corpus measures

Aggregate figures only; the corpus itself stays out of version control.

| Measure | Value |
|---|---|
| Feature files | 64 |
| Feature entries in `index.md` | 62 |
| Total corpus size | ~594 KB ≈ **165k tokens** |
| Largest single feature file | 38 KB |
| `index.md` alone | 48 KB ≈ 13k tokens |
| Features carrying `<acceptance-criteria>` | 55 |
| Features carrying `<notes>` | 55 |
| Criteria in the richest feature | 36 |
| Median criteria among fully-defined features | 15 |
| Declared statuses | `defined` 34, `tbd` 21, `excluded` 7, `superseded` 2 |
| Declared priorities | must 13, should 25, could 19, wont 7 |

Two of those rows are the whole story. **`excluded` and `superseded` are not in the template's
enum** — the corpus invented them because it had to. And **64 files against 62 index entries**
is not drift: the two unindexed files are exactly the two `superseded` ones. Removing a merged
feature from the index while keeping its file as a pointer is a real convention that the
toolchain neither documents nor validates.

---

## 3. Findings

### 3.1 Correctness

**P1 — MoSCoW priority is extracted, then discarded. Won't-have features are built.**
*Verification: static, exhaustive.*
`breakdown-analyze-prd` reads the priority attribute and writes `features[].priority` into
`analysis.json`. No skill downstream of that ever reads it. `breakdown-plan-layers` does not
mention priority at all; in `breakdown-generate-tasks` and every `/execute` skill, the only
`priority` is the integer described in P3. Consequences, in order of severity:

1. Won't-have features are broken down into tasks and implemented.
2. There is no way to build an MVP — a could-have's backend precedes a must-have's frontend,
   because layer order is the only order.
3. `/execute` cannot report what tier it is building, because the tasks do not carry one.

In corpus terms: 7 features the product owner explicitly rejected would be built, and the 13
must-haves would be interleaved with 44 others.

> **Runtime confirmation still owed.** The static result is unambiguous — the consumer does not
> exist — but the user asked for a test, and a passing static grep is not a run. See item 21.

**P2 — `<acceptance-criteria>` has no consumer on the PRD path.**
*Verification: static, exhaustive.*
Across the whole toolchain, `acceptance-criteria` appears in exactly three kinds of place: the
`/prd` and `/crd` templates that *write* it; the CRD branch of `breakdown/SKILL.md`, which
reads it; and two **XML comments** — `<!-- Include feature description, acceptance criteria -->`
— in `task-format-spec.md` and `breakdown-generate-tasks`. A comment inside a template is not a
consumer. On the PRD path the criteria are never read, so `<test-requirements>` in every
generated task are invented from a summary rather than derived from the criteria that already
exist. The CRD path does this correctly, which makes the gap an inconsistency as well as a loss.

**P4 — `<notes>` has no consumer anywhere.**
*Verification: static, exhaustive.*
Zero reads. Meanwhile `breakdown-analyze-prd` is instructed to **infer** data models and
relationships from feature descriptions. In the corpus, 28 of the 34 defined features state
their data model and their dependencies explicitly in `<notes>` — entity names, field lists,
relationship semantics, and warnings about modelling traps. The toolchain re-derives, by
inference on a small model, what the document already says.

**P5 — The first step of `/breakdown` does not fit in its model's context.**
*Verification: measured.*
`breakdown/SKILL.md` Phase 2 says: *"Invoke the `breakdown-analyze-prd` skill with the full PRD
content."* For this corpus that is **~165k tokens**, sent in one prompt to a skill declaring
`model: claude-haiku-4-5` (200k window). It nominally fits and practically cannot work: it
leaves ~35k for a structured extraction of 64 features, against an explicit instruction not to
"truncate or summarize features". There is no chunking, no per-feature pass, and no size check.
This is graded **Blocking** for any PRD of realistic size — it is the first thing `/breakdown`
does.

### 3.2 Consistency

**P6 — The `<status>` enum cannot express what real use needs.**
*Verification: measured.*
Template allows `defined|tbd|in-progress`. The corpus uses `defined`, `tbd`, `excluded` (7) and
`superseded` (2), and uses `in-progress` **zero** times. Two of the four values in use are
undefined by the template; the one value the template offers beyond the obvious pair is unused.

**P7 — `<status>` has no definitions, and nothing checks it.**
*Verification: measured — see item 3.*
Three enum values, no statement of what any of them means, no derivation, no guard. A status is
whatever was true when the file was written, and nothing notices when that stops being true.

**P8 — Priority is stored twice.**
*Verification: measured.*
`priority=` on the index entry, and `<priority>` in the feature file. Across the 62 shared
entries the two agree — but the file set does not: 64 files, 62 entries. The two `superseded`
files still declare `should-have` for a feature that no longer exists in the plan.

**P13 — Excluded features carry an undocumented `<rationale>` element.**
*Verification: measured — present in exactly the 7 `excluded` files and nowhere else.*
The corpus needed somewhere to record *why* something was rejected and invented a slot for it.
It is a good idea that the template should adopt, not an error.

**P14 — Excluded and superseded features keep a stale priority.**
A won't-have that carries `should-have`, or a merged-away feature that still claims a tier, is
a contradiction the schema permits.

### 3.3 Structural

**P3 — `priority` means two unrelated things.**
On a feature it is MoSCoW. On a task it is *"Execution order within layer (1 = first)"*, an
integer 1–99 (`task-format-spec.md` line 24), also used as a merge-queue ordinal. **Any fix that
"carries priority onto the task" must not use the element name `priority`** — it is taken, by a
field `/execute` depends on for merge sequencing. This is the single most likely way to
implement items 14–16 wrongly.

**P9 — Nothing reconciles the index against the feature directory.**
Orphans, dangling links and priority mismatches are all silently possible. The corpus's two
orphans are legitimate (P6's `superseded` convention); the check must therefore *understand*
that convention rather than flag every orphan.

**P10 — `what-next.md` is prose markdown where the spec says XML.**
*(This is assessment finding F3/F10; carried forward as item 12.)* The divergence produced a
**better** artefact — the prose version carries task-generation order, spikes, infrastructure,
data-model work, UX gaps and a risk table, none of which the XML template has a slot for. The
skill's own note on this is the right diagnosis: its "next steps" are all *post-PRD activities*,
while the template assumes *authoring gaps*. Both are real and they are not the same list.

**P11 — `index.md` has grown sections the template does not define.**
The corpus's index carries a large `<architecture>` block (data model, hierarchy, relationships)
and cross-references documents outside the PRD directory — ADRs and an open-questions register.
The template defines neither, and neither has a reader (P17). The block was not authored against
a spec; it was invented mid-invocation when the author needed somewhere to constrain
architecture and found no slot. That makes it the third instance of the same pattern, alongside
`<rationale>` (P13) and prose phasing (P12): **where the template is silent, the model invents
structure, and the invention is usually right.** Treat these as requirements discovered by use,
not as deviations to be corrected.

**P17 — The greenfield path has no architecture channel, in either direction.**
*Verification: static, exhaustive.* This is the finding P11 was a symptom of.

*Nothing accepts architecture as an input.* The layer graph in `layer-definitions.md` is a
fixed, hardcoded five-tier DAG — setup → foundation → backend → frontend → integration — with no
override, and nothing in a PRD can influence it. `breakdown-analyze-prd` is explicitly
instructed **"Do NOT ... include your own opinions about architecture"**, and infers data models,
endpoints and components instead. So `/breakdown`'s pre-baked tiering is the entire answer, and
an authored architectural constraint has nowhere to enter.

*Nothing records architecture as an output either.* `/execute` dispatches
`project-context-finalizer` only after `test -f {project_path}/PROJECT.md` — **if it exists**.
A greenfield project has no PROJECT.md, so the finalizer never runs, so one is never created.
A greenfield project can therefore run the entire pipeline and end with no architecture record
at all; the first `/crd` against it then pays for a full `crd-investigate` to rediscover
architecture the PRD had already stated.

*The brownfield path, by contrast, is well served.* PROJECT.md carries `## Architecture` — tech
stack, component structure, key patterns — plus machine-readable schema and API registries;
`crd-investigate` produces it, and `/breakdown` loads it for CRD input. The asymmetry is the
finding: **the toolchain has an architecture artefact, and greenfield is the only path that
cannot reach it.** Note the direction of flow differs — PROJECT.md is *descriptive*, discovered
from code, whereas a PRD-time constraint is *prescriptive*. Same shape, opposite direction.

**P12 — Intra-feature phasing exists in prose, with no slot for it.**
Seven features already split themselves into "phase 1 / phase 2" in prose, with real semantics:
a phase 2 that depends on external access, criteria mapped to specific phases, and an open
question about whether a phase 2 should exist at all. `/breakdown` cannot see any of it, so it
would build both phases at once or neither.

**P15 — Tasks have no link back to the feature they came from.**
`<meta>` carries id, name, layer, priority, estimated-files. Nothing identifies the source
feature, so coverage cannot be reported, criteria cannot be traced, and a failed task cannot be
attributed to a requirement.

**P16 — `/prd`'s guards are prose, in a repository that has learned better.**
Items 4.6, 4.12, 4.13, 4.14 and 4.17 all converted prose instructions into programs, each time
because the prose guard was documented and ignored. `/prd` is now the largest remaining
concentration of prose guards: the pre-write existence check, the consistency checks, and the
status marker are all instructions to a model rather than exit codes.

---

## 4. Two design decisions that resolve most of the above

### 4.1 Ownership rule: the index owns *planning*, the file owns *definition*

> **Priority lives in `index.md`. Status lives in the feature file. Neither is duplicated.**

This settles P8 by choosing, not by synchronising. The reasoning is not aesthetic:

- Priority is a **portfolio decision** — a feature's place relative to others. It belongs where
  the others are visible. Re-prioritising is then one edit to one file, not 64.
- Status is a **property of the file's own content** — how completely this feature is specified.
  It is derivable from the file and from nothing else (item 3), which is only true if it lives
  there.
- `analyze-prd` already reads the index entry, so the priority is on the path it already walks.
- It fixes P14 for free: removing a superseded feature from the index removes its priority,
  because the priority was never in the file. A stale tier becomes unrepresentable.

**Change:** delete `<priority>` from the feature template. Keep `priority=` on the index entry.

### 4.2 Status records definition completeness, not build progress

The five values, defined — and the definitions go **in the template**, where the writer sees them:

| Status | Meaning | Required content |
|---|---|---|
| `tbd` | No criteria written. A name and an intent. | — |
| `in-progress` | Criteria exist, but some scope is carried by the description alone. | ≥1 criterion |
| `defined` | Criteria cover the edge cases; notes carry the data model and relationships. | criteria + structured notes |
| `excluded` | Won't-have. Deliberately not built. | `<rationale>` (adopts P13) |
| `superseded` | Merged into another feature; file retained as a pointer. | successor link; **removed from `index.md`** |

**The tag records how completely the feature is *defined*, not how far it is *built*.** This must
be said explicitly, because `in-progress` reads as build progress to every developer who sees
it, and because `/execute` has its own `in-progress` meaning exactly that.

Two consequences worth stating plainly:

- `excluded` and `superseded` are **definition states, not priorities**. `excluded` pairs with
  `priority="wont-have"` in the index; `superseded` has no index entry at all.
- The corpus's zero uses of `in-progress` are a symptom, not a preference. Under these
  definitions, several features currently labelled `tbd` — thin criteria, real scope in the
  description — are `in-progress`. The migration in item 4 will reclassify them.

---

## 5. Remediation items

### A. Schema — `/prd` templates

**1. Feature template: remove `<priority>`, extend `<status>`, add the missing slots.**

```xml
<feature>
  <meta>
    <name>{{Feature Name}}</name>
    <slug>{{feature-slug}}</slug>
    <!-- priority is NOT here: it lives on the index entry (§4.1) -->
    <status>tbd|in-progress|defined|excluded|superseded</status>
    <!-- status = how completely this feature is DEFINED, not how far it is BUILT -->
  </meta>

  <description>...</description>

  <phases>                                  <!-- optional; item 5 -->
    <phase id="1" name="...">...</phase>
  </phases>

  <acceptance-criteria>
    <criterion id="1" phase="1">            <!-- phase optional -->
      <given/><when/><then/>
    </criterion>
  </acceptance-criteria>

  <notes>
    <data-model>...</data-model>            <!-- item 2 -->
    <relationships>...</relationships>
    <considerations>...</considerations>
  </notes>

  <rationale>...</rationale>                <!-- required when status=excluded -->
  <superseded-by slug="..."/>               <!-- required when status=superseded -->
</feature>
```

**2. Give `<notes>` an internal shape.**
The corpus already writes notes in three recurring kinds — data model, dependencies and
relationships, and free considerations — signalled with bold markdown headings. Promoting those
to elements is what makes P4 fixable: `analyze-prd` can then *read* `<data-model>` instead of
inferring one. Free markdown stays legal inside each element; the corpus proves markdown-in-XML
is comfortable. **Migration must not be lossy** — unrecognised note content goes to
`<considerations>` verbatim, never dropped.

**3. Status derivation, as a script — and it is feasible.**
*Measured, with the caveat below.* A probe deriving each feature's status from its own content:

```
64 feature files
  defined    -> defined     34   OK
  excluded   -> excluded     7   OK
  superseded -> superseded   2   OK
  tbd        -> tbd         20   OK
  tbd        -> ambiguous    1   escalate
agree=63  ambiguous=1  contradicted=0
```

The rule, in order:

| Test | Verdict |
|---|---|
| 0 criteria + `<rationale>` | `excluded` |
| 0 criteria + successor link | `superseded` |
| 0 criteria, neither | **error** — no criteria and no reason |
| Notes carry a data-model / dependency / relationship marker | `defined` |
| ≥3 criteria and ≥1000 bytes of notes | `defined` |
| ≤2 criteria, or <400 bytes of notes | `tbd` |
| anything else | **ambiguous → escalate** |

The structured-notes marker was the decisive signal: present in 28 of 34 `defined` files and in
**none** of the other 30. Zero false positives.

> **Read this honestly.** The rule was tuned on the same corpus it was scored against, so 63/64
> is an in-sample figure and not evidence it generalises. What does generalise is the shape:
> **zero contradictions and a one-file escalation band.** The design is safe because it refuses
> rather than guesses — an ambiguous file is escalated to the model, never silently relabelled.

And the escalation band is not a defect: **"criteria exist but scope is carried by the
description alone" is precisely what a counter cannot see.** The ambiguous band *is*
`in-progress`. The third status exists exactly where the deterministic rule must stop, which is
why the check is three-valued by construction rather than by concession.

**4. Migrate the corpus conventions into the templates, then reclassify.**
`excluded` + `<rationale>`, `superseded` + pointer + index removal, structured notes. Then re-derive
every status: expect a cohort of `tbd` files to become `in-progress`, and expect the two orphans
to validate as legitimate rather than flag.

**5. Phasing within a feature.**
Optional `<phases>` with `phase=` on criteria. Deliberately minimal: a phase is a **named subset
of the acceptance criteria**, not a second priority axis and not a schedule. `/breakdown` gains
`--phase <n>` (item 15) and, absent it, builds phase 1 only where phases are declared — because
seven corpus features describe a phase 2 that depends on access or decisions that do not exist
yet, and building it would be wrong, not early.

### B. `/prd` — the command

**6. Phase 6 becomes a real consistency check, run by script.**
Today Phase 6 asks the model four prose questions about the tech stack. It gains, as exit codes:

- derive status for **every** feature; report each mismatch as `declared X, derived Y, because Z`
- reconcile index against `features/` — orphans that are not `superseded`, dangling entries,
  and any feature file still carrying a `<priority>`
- criterion `id` uniqueness within a feature; `phase` references that exist in `<phases>`
- `excluded` without `<rationale>`; `superseded` without a successor or still present in the index

Mismatches are **reported, not auto-corrected**. A wrong status is often a signal that the
*content* is wrong, and silently relabelling hides that.

**7. `--resume` re-runs the check across all features, before resuming.**
This is the point of item 6. A PRD is edited over weeks; the features `/prd` did not touch this
session are exactly the ones whose labels have gone stale. Stamping only what it touched is how
the label drifts from the content in the first place.

**8. A criteria-authoring sub-agent — worth building, with a specific persona.**
*Recommended: yes.* Not a second author with the same voice — a **challenger**. The corpus makes
the case: the best-defined features carry negative cases, abstention behaviour and
irreversibility warnings, and those are precisely what an author who just wrote the happy path
does not think to add. A same-persona agent would deepen the bias; an adversarial one corrects it.

- `agents/prd-criteria-author.md`, `context: fork` — 64 features must not accumulate in one context.
- Input: one feature file, plus the index entry and the named related features. Output: proposed
  criteria only, never a rewritten file.
- Persona: a QA lead trying to find the case the author missed — edge cases, empty and error
  states, the negative assertion, the thing that must *not* happen.
- It also proposes the `<data-model>` note, since `defined` requires it (§4.2).

> **Keep it opt-in, per feature.** Run unattended across 21 `tbd` features it would produce
> plausible criteria that nobody has agreed to, and a `defined` status derived from them would be
> *true* and *worthless*. The user accepts or rejects each set. This is the one item where
> automation must not close the loop.

**9. Make `/prd`'s prose guards executable (P16).**
The Phase 8 pre-write existence check, the status marker, and item 6's checks all become scripts.

> **Unverified mechanism — probe before committing to it.** Every bundled script in this
> repository is invoked from a *skill*, via `{skill_dir}`. **No command invokes one today**, and
> nothing uses `${CLAUDE_PLUGIN_ROOT}`. Since item 4.1 deliberately kept all three entry points
> as commands, the path a command uses to reach a bundled script is unestablished. Probe it in
> `docs/skills/probes/` first. If a command cannot reliably locate one, the fallback is a thin
> `prd-check` skill that the command invokes — not prose.

**10. Feature files are read per feature, never as one blob.**
`/prd` writing 64 files in one context is the same P5 problem at the authoring end.

### C. `what-next.md`

**11. Design: XML skeleton, markdown bodies, derived TBD list.**
This subsumes assessment item 4.4 and answers the skill's own critique — that its "next steps"
were post-PRD activities while the template expected authoring gaps. **They are two different
lists and the file needs both.**

```xml
<what-next>
  <meta>
    <prd-slug>...</prd-slug>
    <status>in-progress|complete</status>   <!-- what /prd --resume greps for -->
    <last-updated>YYYY-MM-DD</last-updated>
    <next-command>/breakdown</next-command>
    <toolchain-version>2.0.0</toolchain-version>
  </meta>

  <!-- DERIVED by item 6. Never hand-maintained. -->
  <authoring-gaps>
    <summary defined="34" in-progress="0" tbd="21" excluded="7" superseded="2"/>
    <gap slug="..." status="tbd" blocking="true">Missing acceptance criteria</gap>
  </authoring-gaps>

  <!-- HUMAN-AUTHORED. Post-PRD work. Markdown bodies. -->
  <next-steps>
    <step kind="breakdown">...ordered task-generation sequence...</step>
    <step kind="spike">...technical validation, with what it must measure...</step>
    <step kind="infrastructure">...</step>
    <step kind="data-model">...</step>
    <step kind="ux">...</step>
  </next-steps>

  <risks>
    <risk><description>...</description><mitigation>...</mitigation></risk>
  </risks>

  <open-questions href="../../product/open-questions.md"/>  <!-- pointer or inline -->
  <session-notes>...</session-notes>
</what-next>
```

Three things this gets right that neither the current template nor the corpus file does:

- **`<authoring-gaps>` is derived.** The corpus file lists no TBD items at all — with 21 of them,
  hand-maintenance was never going to happen. Generating it is what makes it survive.
- **`kind=` on steps** preserves the prose file's real value (the ordered breakdown sequence, the
  spikes and what they must measure) in a form `/breakdown` could later consume.
- **`<open-questions>` may be a pointer.** The corpus moved its questions to a project-wide
  register; the template must permit that instead of forcing them back inline.

Markdown stays inside the elements. The goal is a parseable skeleton, not the loss of prose depth.

**12. Migrate the existing prose file, and keep the marker readable in both.**
`/prd`'s initialization greps `<status>in-progress</status>` from `what-next.md` *or* `index.md`.
Keep the dual check until every artefact is migrated — a PRD that cannot be found is a PRD that
gets overwritten.

### D. `/breakdown`

**13. Skip `wont-have`, `excluded` and `superseded` unconditionally.**
Correctness, not preference. No flag, no override.

**14. Add `--priority <threshold>`, mirroring `--layer`.**
`must-have` = must only; `should-have` = must+should; `could-have` = all three. **Default
`could-have`** — that preserves today's behaviour minus item 13, so the flag adds capability
without silently changing what an existing invocation builds.

> **A filtered set is not automatically a buildable set.** 9 of the corpus's 13 must-have
> features reference lower-tier features, 49 times in total. Resolve open question 4 before
> building this item — the flag is easy, but what it should do about a must-have that points at
> a could-have is not.

**15. Refuse to break down features that are not defined enough — loudly.**
A `tbd` feature has a name and roughly one criterion. Breaking it down does not produce a thin
task; it produces an **invented** one, and TDD then locks the invention in as passing tests.
Skip `tbd` unless `--include-tbd`. In the corpus this would skip 21 features — **including 5
must-haves**, which is exactly the point: the report must name them, because "5 must-have
features are not defined enough to break down" is the single most useful sentence `/breakdown`
could say about that PRD. Silent omission would be worse than the current behaviour.

**16. Carry the feature through to the task — under names that are free.**
In `task-format-spec.md` `<meta>`, **not** as `<priority>` (P3):

```xml
<meta>
  <id>L2-003</id>
  <priority>1</priority>                    <!-- UNCHANGED: integer, merge order -->
  <source-feature>{{feature-slug}}</source-feature>   <!-- P15 -->
  <moscow>must-have</moscow>                          <!-- P1 -->
  <feature-phase>1</feature-phase>                    <!-- P12, optional -->
</meta>
```

**17. Carry the criteria and the data model, structurally.**
`<prd-excerpt>` as free prose is how P2 and P4 happen. Add to the task format:

- `<acceptance-criteria>` — the source criteria, **verbatim with their original ids**, so a task
  cites `criterion 7` and coverage is reportable
- the feature's `<data-model>` note carried into `<context>` rather than re-inferred
- `<test-requirements>` **derived from** the criteria, with each test naming the criterion it covers

This is where the pipeline stops discarding the document.

**18. Fix P5: analyse per feature, not per corpus.**
Two stages: an index-level pass (~13k tokens — tech stack, feature list, priorities,
architecture) and a per-feature pass fanned out one file at a time, each writing its own
fragment. `generate-tasks` receives only the feature files for its batch. Add a hard **size
check with a refusal**, in the idiom of `resolve-output.sh`: if a single prompt would exceed a
threshold, refuse with `REFUSED:` rather than silently truncating. Re-examine
`model: claude-haiku-4-5` on `analyze-prd` once the per-feature split lands — the split may
make haiku adequate; without it, no model choice rescues the design.

### E. `/execute`

**19. Report the tier being built.**
Carry `<moscow>` into `execute-state.json` per task; group the final report by tier. Requires
item 16 and nothing else.

**20. Refuse won't-have tasks at execution time.**
Defence in depth, as an exit code, matching item 4.13's principle that guards must be executable.
A task carrying `<moscow>wont-have</moscow>` reaching `/execute` means item 13 failed, and it
should stop there rather than be built.

### F. Cross-cutting

**21. The runtime test P1 still owes.**
Minimal PRD: 4 features, one per tier, each with 2 criteria. Run `/breakdown`. Assert
task count and that no task derives from the won't-have. Run before and after items 13–16 — the
"before" run is what converts P1 from static to measured. Keep it small deliberately: P5 means a
realistic PRD would fail for an unrelated reason and confound the result.

**22. One artefact schema check, shared by producer and consumer.**
P10 is a general failure: the spec says XML, the run produced markdown, and nothing noticed for
weeks. A single `check-artefacts.py` validating `index.md`, `what-next.md` and every feature file
against the declared schema, invoked in three places:

- at the end of `/prd` — before claiming the PRD is written
- at the **start** of `/breakdown` — refusing on mismatch, in the `resolve-output.sh` idiom
- in `tests/test_toolchain.py`, against a fixture

A producer/consumer mismatch should fail at the boundary, not silently degrade three skills later.

**23. Extend the regression suite.**
New checks in the existing `@check(name, finding=...)` style: no `<priority>` in the feature
template (item 1); the status enum in the template matches the one the derivation script
implements; task-format-spec declares `source-feature` and `moscow`; `<acceptance-criteria>` has
a non-comment consumer on the PRD path; the derivation script scores 0 contradictions against a
committed fixture.

That last one matters most. **P2 and P4 were both invisible to a test suite that reads the
files, because the failure is an absent consumer rather than a wrong string.** A check that a
producer has a reader is the general form of this whole plan.

**24. Toolchain version stamping — the residue of item 4.5.**
Mostly delivered: `plugin.json` declares `2.0.0` and `build-manifest.py` writes
`toolchain_version` into the manifest. What remains:

- `/prd` writes `<toolchain-version>` into `what-next.md` (item 11's `<meta>`)
- `/execute` compares the manifest's recorded version against the running plugin and warns on a
  mismatch, refusing on a known-incompatible one

The schema changes in this plan are exactly the kind of break that makes this worth finishing:
an artefact written by 2.0 and read by 2.1 must not be misread silently.

### G. Architecture

**25. Give architecture an artefact, and make it the greenfield counterpart of PROJECT.md.**
*Addresses P11, P17.*

Architecture divides cleanly by scope, and the two halves belong in different places:

- **Feature-local** — the entities, fields and relationships a single feature owns. Home:
  `<notes><data-model>` and `<relationships>` (item 2). Most of the corpus's index block is
  this, and it only ended up in the index because the feature file had no structured slot.
- **Cross-cutting** — inheritance strategy, bounded-context rules, ownership conventions,
  patterns no single feature owns. Home: a **new artefact**.

**Not `what-next.md`.** That file is transient by design — a status marker, a to-do list, and
session notes, consumed and then stale. An architectural constraint is durable and must be read
*every time* `/breakdown` generates tasks, not once when someone resumes. Putting a durable
constraint in a transient file is the same category error as §4.1's priority-in-the-feature-file:
right content, wrong lifetime. A `<step kind="architecture">` also mixes *decisions already made*
in with *work not yet done*, which is the one distinction `<next-steps>` exists to draw.

**Recommended shape:** `docs/prd/{slug}/architecture.md`, written in the **same schema as
PROJECT.md's `## Architecture` section plus its schema registry**, for three reasons: there is
then one architecture format rather than two; `/breakdown` already knows how to load that shape
for CRDs, so the greenfield reader is a small change rather than a new one; and it lets item 26
close the P17 loop — after `/execute`, the finalizer seeds PROJECT.md from it instead of being
skipped, so a greenfield project ends with the architecture record it currently never gets.

ADRs stay where the corpus already puts them: outside the PRD, holding the rationale and the
history. `architecture.md` holds the *binding constraints* and may cite an ADR by pointer. The
distinction that matters is not prose-versus-XML but **whether the toolchain has to read it** —
a constraint that binds task generation must be machine-readable and local; a rationale that
explains it to a human need be neither.

**Then give it a reader**, or this becomes P11 again in a new file: `analyze-prd` must load it,
its "no opinions about architecture" instruction must be narrowed to *"do not invent
architecture; do apply what `architecture.md` states"*, and `generate-tasks` must carry the
binding constraints into `<context>`.

**26. Fix P17's output half: seed PROJECT.md on greenfield.**
Replace `/execute`'s `test -f PROJECT.md` gate with: if it exists, update it; if it does not and
the run came from a PRD, create it from `architecture.md` plus the task exports. The current
condition means PROJECT.md is only ever updated where it already exists, which no greenfield run
can satisfy.

**27. Capture feature dependencies structurally, and let ordering be derived.**
*Addresses P1's residue, open question 4, and the ordering duplication described below.*

`what-next.md`'s task-generation order in the corpus was **deduced by the model during `/prd`**,
not authored by a human. That reframes it: it is not an authority to defer to, it is a *second
model's unvalidated inference* — produced with more context than `/breakdown` has, but with no
dependency graph, no validation, and no awareness that `breakdown-plan-layers` exists to do
exactly this job. Two producers of the same artefact, out of band, neither aware of the other.

So `/breakdown` should **not** consume the sequence. But the sequence is evidence of something
real: while writing the features, the model noticed dependencies it had nowhere to record, and
emitted an ordering because ordering was the only expressible form of that knowledge. **The
durable artefact is the dependencies, not the order.**

Capture them where they are noticed:

```xml
<depends-on slug="{{feature-slug}}" kind="data|runtime|reference"/>
```

This is the fourth instance of P11's pattern, and it pays for itself three times over: it
disambiguates the 49 cross-tier references that are currently plain markdown links indistinguishable
from "see also"; it makes open question 4 answerable — whether a `--priority` filter yields a
closed set becomes a computation rather than a guess; and it gives `plan-layers` real input, so
the ordering is derived once, by the component that owns ordering, from evidence rather than
from recollection.

`<next-steps>` then keeps the *rationale* — why a spike matters, what it must measure — and
drops the sequence.

---

## 6. Summary

| # | Item | Addresses | Grade |
|---|---|---|---|
| 1 | Feature template: drop `<priority>`, extend `<status>` | P6, P8, P13 | Consistency |
| 2 | Structure `<notes>` | P4 | Correctness |
| 3 | Status derivation script | P7 | Consistency |
| 4 | Migrate corpus conventions, reclassify | P6, P14 | Consistency |
| 5 | `<phases>` within a feature | P12 | Structural |
| 6 | Phase 6 becomes an executable consistency check | P7, P9, P16 | Consistency |
| 7 | `--resume` re-checks all features | P7 | Consistency |
| 8 | Criteria-challenger sub-agent | P2 | Structural |
| 9 | `/prd` prose guards → scripts | P16 | Structural |
| 10 | Per-feature authoring | P5 | Structural |
| 11 | `what-next.md` hybrid design | P10 | Structural |
| 12 | Migrate `what-next.md`, keep dual marker | P10 | Structural |
| 13 | Skip won't-have / excluded / superseded | **P1** | **Correctness** |
| 14 | `--priority <threshold>` | **P1** | **Correctness** |
| 15 | Refuse `tbd`, and name what was skipped | P1, P2 | Correctness |
| 16 | `source-feature` + `moscow` on tasks | P1, P3, P15 | Correctness |
| 17 | Carry criteria and data model into tasks | **P2, P4** | **Correctness** |
| 18 | Per-feature analysis + size refusal | **P5** | **Blocking** |
| 19 | `/execute` reports tier | P1 | Correctness |
| 20 | `/execute` refuses won't-have | P1 | Correctness |
| 21 | Runtime test for P1 | P1 | — |
| 22 | Shared artefact schema check | P10, P11 | Structural |
| 23 | Regression checks | all | — |
| 24 | Finish version stamping | (4.5) | Structural |
| 25 | `architecture.md`, in PROJECT.md's schema, with a reader | **P11, P17** | **Correctness** |
| 26 | Seed PROJECT.md on greenfield | **P17** | **Correctness** |
| 27 | `<depends-on>`; derive ordering rather than authoring it | P1, P11 | Structural |

**Suggested order.** 21 first — measure P1 before changing it. Then 18, since nothing else can be
tested end to end on a realistic PRD until analysis fits in context. Then the schema block
(1–5, 25, 27) and its migration, because 13–17 depend on the shapes it defines — and because 27
is what makes item 14 decidable. Then the `/breakdown` and `/execute` items, which are small
once the schema carries the data. 22 and 23 last, to hold the result in place.

---

## 7. Open questions

1. **Can a command invoke a bundled script?** Blocks item 9 and shapes 3, 6 and 22. Probe first.
2. **Resolved — see items 25 and 26.** *(Was: where does the index's `<architecture>` block
   belong?)* Feature-local architecture goes to `<notes><data-model>`; cross-cutting
   architecture goes to a new `architecture.md` sharing PROJECT.md's schema. The residual
   question is narrower: **should `architecture.md` and PROJECT.md be one file from the
   outset**, rather than two that converge after `/execute`? One file is simpler and removes a
   migration, but it means writing a *descriptive* artefact prescriptively, before any code
   exists — and `crd-context-update` compares PROJECT.md against a git hash it would not yet
   have. Two files with a defined seeding step is the safer default; one file is worth
   revisiting if the seeding proves lossy.
3. **Resolved — see item 27.** *(Was: should `/breakdown` consume the task-generation order?)*
   No. The order was model-deduced during `/prd`, not human-authored, so consuming it means
   preferring one model's unvalidated inference to another's — while duplicating
   `breakdown-plan-layers`. Capture `<depends-on>` instead and derive the order. The residual
   question: **is `kind="data|runtime|reference"` the right axis?** It is the minimum that
   separates "needs this to exist first" from "mentions this", which is what items 14 and 27
   require; whether layer assignment needs a finer distinction will not be knowable until
   `plan-layers` consumes it.
4. **Does `--priority must-have` produce a coherent build?** *Measured, and the answer is
   probably no.* Filtering yields a buildable slice only if must-haves are closed under their
   dependencies. In the corpus, **9 of the 13 must-have features carry cross-tier references —
   49 of them in total** — to should-, could- and won't-have features.

   The measurement counts *references* (inter-feature links), which are not all build
   dependencies; some are "see also". But the ratio is high enough that item 14 cannot assume a
   filtered set is coherent. Three options, in increasing cost: filter and report the dangling
   references; filter with dependency closure, pulling in lower-tier features a must-have needs
   (which quietly rebuilds the tier boundary); or treat the reference graph as the real
   ordering and let MoSCoW select roots rather than members. **This needs deciding before item
   14 is built, not after** — and distinguishing a genuine dependency from a cross-reference is
   itself work the schema does not currently support, since both are plain markdown links.
