# Gap Closure — Plan

**Status:** built on branch `gap-closed`; see §12 for where it departed from this plan
**Date:** 2026-09-14
**Subject:** a `closed` date on `<gap>`, an optional `closed-by`, and every reader counting only
open gaps, on both paths. Released as plugin **2.1.0**
**Relates to:** [core §6](../../schema/core.md#6-gaps--what-a-document-knows-it-is-missing) ·
item 29 (gaps), item 48 (gaps on the CRD path), item 40 (`<review>`), item 76 (the no-version
precedent) · [`checks.md`](../../schema/checks.md) · [`parity.md`](../../schema/parity.md)

> **This is not a new capability. It supplies a mechanism for a rule the schema already states.**
> Core §6 already says *"a resolved gap is annotated, not deleted"*, in the body. But every
> script that reads gaps counts every `<gap>` whatever its body says. So an author who follows
> the rule can never reach `defined` or `ready`, and the only way through is to delete the gap,
> which breaks the rule. `closed` is what makes the rule possible to follow.

Line references are to `main` at `49d6fcc`.

---

## 1. Decisions

Every point below was agreed. They are listed here so the rest of the plan can cite them.

| # | Decision |
|---|---|
| D1 | `<gap>` gains **`closed`**, a `YYYY-MM-DD` date, beside `raised` |
| D2 | A gap with `closed` is **closed**. A gap without it is **open**. There is no third state |
| D3 | **No partial closure.** If only part of a gap is resolved, close it and raise a new gap, with a new id, for the rest. The new gap's body cites the old id |
| D4 | **No reopening.** If a closure turns out wrong, raise a new gap citing the old one. `raised` and `closed` never change once written |
| D5 | **Only open gaps count**, in every check, gate, report and derived list |
| D6 | A closed `specification` gap **does not** bar `defined`, and **does not** bar a CRD's `ready`. One rule, two subjects, as §6 already treats them |
| D7 | **Closed gaps are not carried forward**: not into `analysis.json`, not into a task's `<context>`. `/breakdown` still *reads* every gap, because selection and the gate need them |
| D8 | An optional **`closed-by`** names the criterion ids that closed the gap. It is recorded **on the gap only**, never mirrored onto `<criterion>` |
| D9 | The body still says **how** the gap was resolved. `closed-by` covers only the case where criteria resolved it |
| D10 | **No schema version.** Precedent is item 76 (core §8); the reasoning is in §8 below |
| D11 | Released as **2.1.0**: a feature, not a fix |

---

## 2. Why the existing rule cannot be followed

[core.md:411-413](../../schema/core.md#L411-L413): *"A resolved gap is annotated, not deleted…
Say what resolved it and when, in the body, and leave it in place."*

Every gap reader goes by the tag and ignores the body:

| Site | What it does with an annotated, resolved gap |
|---|---|
| [`select-features.py:90-91`](../../skills/breakdown/scripts/select-features.py#L90-L91) `gaps_of()` | returns its `kind`. Everything below that imports it inherits this |
| [`check-status.py:130`](../../skills/breakdown/scripts/check-status.py#L130) | a `specification` gap caps a PRD feature below `defined`. **PRD only**, see §2.1 |
| [`select-features.py:114`](../../skills/breakdown/scripts/select-features.py#L114) | item 15 refuses the feature |
| [`check-gate.py:160`](../../skills/breakdown/scripts/check-gate.py#L160) | assertion 3 blocks a feature that has tasks, on both paths |
| [`check-coverage.py:143`](../../skills/breakdown/scripts/check-coverage.py#L143) | passes the gap to `judge()` |
| [`check-status.py:193-240`](../../skills/breakdown/scripts/check-status.py#L193-L240) `check_gaps()` | prints an `AGE` line and counts it in *"N gaps open"* |
| [`build-what-next.py:61,97`](../../schema/scripts/build-what-next.py#L61) | lists it in `<authoring-gaps>` |
| [`breakdown-analyze-prd`](../../skills/breakdown-analyze-prd/SKILL.md#L248-L252) | copies it into `analysis.json` verbatim |
| [`task-format-spec.md:237`](../../skills/breakdown/references/task-format-spec.md#L237) | carries it into the task's `<context>`, *"unchanged"* |

The last row is the dangerous one. An implementer handed a resolved `decision` gap has been told
to stop.

### 2.1 Found while planning: nothing checks the CRD `ready` rule

**Core §6 overstates what is enforced.** [core.md:388-393](../../schema/core.md#L388-L393) says
the CRD *"now has the same one-way mechanical test `<definition>` has"*. No script runs it.
`check-status.py`'s CRD branch
([lines 280-284](../../skills/breakdown/scripts/check-status.py#L280-L284)) validates gap shape
and ages, and passes `[]` as the escalation list. No script in `schema/` or `skills/` compares
`<workflow>` against gaps. What exists:

- prose telling the model to demote the CRD
  ([`commands/crd.md:139, 308`](../../commands/crd.md#L308));
- a suite check that the sentence *exists*
  ([`test_toolchain.py:6218`](../../tests/test_toolchain.py#L6218));
- the downstream effect: `select-features.py` refuses any `specification` gap whatever the
  workflow says, and `check-gate.py` blocks it. So a `ready` CRD carrying one is still stopped at
  `/breakdown`, but it is never reported as the contradiction §6 calls it.

This is the pattern of the same element being on both paths while the check runs on one. **This
plan closes it**, because D6 needs something on the CRD path to test: `check-status.py`'s CRD
branch gains a CONTRADICTION for `<workflow>ready</workflow>` together with an **open**
`specification` gap, mirroring line 130. Without that, check C6 would be asserting on prose. The
merge message names this finding separately from the `closed` feature.

**The rule in [`decision-record.md:91-93`](../../schema/decision-record.md#L91-L93) is the same
one**: *"Resolved questions are annotated in place, never deleted… it is the same rule `<gaps>`
follows."* That rule stays true after this change, and the sentence needs no edit.

---

## 3. The schema change

### 3.1 The element

```xml
<gaps>
  <gap id="3" kind="specification" raised="2026-08-18" closed="2026-09-02" closed-by="7 8">
  Retention period for archived links is unspecified.

  Closed by criteria 7 and 8: 90 days, then purged; a restore inside the window is a P1.
  </gap>
  <gap id="4" kind="decision" raised="2026-09-02">
  Whether a restore after purge is offered at all. Remainder of gap 3.
  </gap>
</gaps>
```

Gap 4 is D3 in practice: part of gap 3 was answered, so gap 3 closed and gap 4 holds the rest.

### 3.2 The attribute table in core §6 gains two rows

| Part | Required | Holds |
|---|---|---|
| `closed` | No | `YYYY-MM-DD`. Present means closed. Not earlier than `raised`, not later than today |
| `closed-by` | No | Space-separated criterion ids **in the same document**. Only on a closed gap. Each must resolve |

### 3.3 The rules each check enforces

| Rule | Mechanical? | Where |
|---|---|---|
| `closed` is a real ISO date | yes | `check_gaps()` |
| `closed` is not earlier than `raised` | yes | `check_gaps()` |
| `closed` is not later than `--today` | yes | `check_gaps()`. **This is the one that matters most.** A future date would open a gate that should still be shut |
| `closed-by` appears only on a gap that has `closed` | yes | `check_gaps()` |
| every `closed-by` id resolves to a `<criterion id=>` in the same document | yes | `check_gaps()`, which already has the document text |
| gap ids stay unique **across open and closed gaps** | yes, already | `check_gaps()` checks every `<gap>`. D3's new gap therefore cannot reuse the old id. Add a control that proves this |
| no partial closure (D3) | **no** | prose in §6. One file cannot tell a partial closure from a full one |
| no reopening (D4) | **no** | prose in §6. Detecting a deleted `closed` needs history, and history is out of scope (§11) |
| the body says how the gap was resolved (D9) | **no** | prose in §6 |

`raised` has no "not later than today" check, and this plan does not add one. That asymmetry is
deliberate: a future `raised` blocks too early, which is safe; a future `closed` unblocks too
early, which is not.

### 3.4 Wording that changes

- **core §6**: rewrite *"A resolved gap is annotated, not deleted"* around `closed`. Add D3, D4 and
  D6. The two statements of the bar become *"must not carry an **open** `specification` gap"*.
- **[`crd-format.md:283-311, 394, 432-435`](../../skills/crd/references/crd-format.md#L283)**: the
  same rewording, and a closed gap in the example.
- **[`prd-format.md:170-172, 253-257, 297`](../../schema/prd-format.md#L170)**: `<authoring-gaps>`
  points at **open** gaps only.
- **`CLAUDE.md`, Important Notes**: one line saying a gap can be closed and that only open gaps
  count.

**Two suite anchors match this wording and will break when it changes.** Update them in the
same commit as the wording:
[`test_toolchain.py:6218`](../../tests/test_toolchain.py#L6218) (`ready must not carry a <gap
kind="specification">`) and the core assertion three lines below it (`CRD marked ready must not
carry a specification gap`). Change the regexes to require **open**. Then add the word **open**
to the mutant set (§9), so that a later rewording which drops it is caught.

The item-29 check at [`test_toolchain.py:5405-5445`](../../tests/test_toolchain.py#L5405) reads
kinds from the `### The five kinds` table only. New rows in the attribute table do not reach it,
but confirm that by running the suite rather than assuming it.

---

## 4. Readers: only open gaps count

**Change the parser once.** Every script row in §2 goes through `gaps_of()` or through one of two
regexes, so the edit is small if it is made in the right place.

| Site | Change |
|---|---|
| `select-features.py` `gaps_of()` | returns the kinds of **open** gaps only. It gains a sibling, `gap_attrs_of()`, which returns every gap's attributes, open and closed, for the two callers that need closed ones |
| `check-status.py` `GAP` / `gap_rows()` | switches to `gap_attrs_of()`, so there is one gap regex in the toolchain rather than two |
| `check-status.py` `check_gaps()` | validates every gap (the §3.3 rules) and adds **open gaps only** to `ages` |
| `check-status.py` `report()` | the summary gains closed gaps: *"N gaps open, M closed, oldest open gap D days"*. The JSON rows gain `closed` and `closed_by` fields |
| `check-status.py` new `--closed-since DATE` | lists gaps closed on or after that date. It is the data feed for §6.1, so no command has to read the file by eye |
| `check-status.py:130`, the `defined` ceiling | unchanged code: `gaps_of()` is now open-only, which is D6 |
| `check-status.py` CRD branch, lines 280-284 | **new** (§2.1): `<workflow>ready</workflow>` with an open `specification` gap → CONTRADICTION. Reads `<workflow>` the way `migrate.py` does, and accepts the old `<status>` spelling on read, per core §3 |
| `check-gate.py` `blocking_gaps()` | unchanged code, for the same reason. It still validates `kind` on closed gaps too: a misspelt kind is still a defect |
| `check-coverage.py` | unchanged code, same reason |
| `build-what-next.py` `GAP` | open gaps only. A feature whose gaps are **all** closed and whose definition is `tbd` or `in-progress` becomes a `<feature>` row, exactly as if it had declared none (line 106) |
| [`tests/fixture/run_5_3.py:224`](../../tests/fixture/run_5_3.py#L224) | a third copy of the regex. Its count is compared with `AGE` lines, so it must count open gaps only, or it will disagree the first time a fixture carries a closed gap. Import `gaps_of()` instead of copying it |

**No other reader exists.** The `gap` hits in `write-state.py`, `ledger-status.sh` and
`state-schema.md` are about gaps in the verification ledger, not `<gap>`. Nothing in `execute-*`
reads `<gaps>`. `build-manifest.py` does not carry gaps either, so `MANIFEST_SCHEMA_VERSION` and
`READER_SCHEMA` do not move.

**`check-readers.py` audits elements, not attributes.** `closed` and `closed-by` will not appear
in its measurement, and `readers.md` needs no row. That is a limit of the audit this plan accepts;
it does not work around it.

---

## 5. Carrying forward

D7, at the two places a gap leaves the source document:

1. **[`breakdown-analyze-prd/SKILL.md:248-263`](../../skills/breakdown-analyze-prd/SKILL.md#L248)**:
   *"Copy each feature's **open** `<gap>` entries out verbatim… A closed gap is not copied: it is
   the record of a question already answered, and its answer is in the criteria."*
2. **[`task-format-spec.md:237-252`](../../skills/breakdown/references/task-format-spec.md#L237)**:
   *"Carry the source document's **open** `<gaps>`…"* and one sentence on why: a closed gap in a
   task file is an instruction to stop that nobody means.

Also:

- **[`breakdown/SKILL.md:381, 404-418`](../../skills/breakdown/SKILL.md#L381)**: the report line
  counts open gaps and adds *"M closed, not carried"*, so that a PRD with ten closed gaps does not
  look as though it declared none.
- **`review-criteria.md`** needs no change. It scopes its placeholder scan around `<gaps>`, and a
  task that carries no closed gaps loses nothing.

**Size is where D7 pays off.** A task file is written for a small-context implementer, and every
closed gap left out is context that implementer never has to read.

---

## 6. Producers: who writes `closed`

A reader with no producer is P46's shape, and it is the defect this project has found most often.
Two commands and one agent write `closed`. Without them the attribute is only ever written by hand.

### 6.1 `/prd` (and `--resume`)

In [`commands/prd.md`](../../commands/prd.md#L250), Phase 3: when a feature is resumed with open
gaps, **walk each one, by id and kind, before proposing new criteria.** For each, the person says
one of three things:

- **still open**: leave it as it is;
- **resolved**: write `closed` (today's date), write `closed-by` if criteria resolved it, and add a
  line to the body saying how;
- **partly resolved**: close it and raise the remainder as a new gap (D3).

A command never writes `closed` on its own judgement. That is the same boundary
[`migration.md:53`](../../schema/migration.md#L53) draws for writing a gap: **person**.

**The review works from the gap (the second rationale).** Before the challenger's review, run
`check-status.py --closed-since <the feature's <review at=> date>`. Hand the challenger each gap
closed since the last review, with its body and `closed-by`. A feature with no `<review>` hands
over every closed gap. The review was already going stale: `<review sha=>` covers the whole file,
so closing a gap marks the review STALE in `check-definition.py`. What was missing was anything
telling the reviewer what to check the new criteria against.

### 6.2 `/crd` (and `--resume`)

[`commands/crd.md:294-308`](../../commands/crd.md#L294),
[`skills/crd/SKILL.md:145`](../../skills/crd/SKILL.md#L145): the same walk, in the same words.
Phase 8 ([`crd.md:371-390`](../../commands/crd.md#L371)) already reports `AGE` lines from
`check-status.py`, and that is unchanged: `AGE` is now open gaps only.

**A CRD has no `<review>`, so it has no review date.** At `/crd --resume`'s review the challenger
gets **every** closed gap in the CRD. A CRD is one document about one change, so the list stays
short. This is a real difference between the paths, and §7 records it.

### 6.3 `prd-criteria-author`

In [`agents/prd-criteria-author.md`](../../agents/prd-criteria-author.md#L135), review mode: when
handed closed gaps, check each against the criteria named in `closed-by`, or against the body when
`closed-by` is absent. Report a closure whose criteria do not answer the gap's question as a
finding. **It proposes; it never removes `closed`.** D4 applies: the fix for a wrong closure is a
new gap.

### 6.4 Gaps already annotated under the old rule

**No migration step, and nothing that searches the body for resolution words.** Recognising
"resolved" in free text is a judgement, of the same kind as `pattern`, and a machine must not make
it. The route is the walk in §6.1 and §6.2. At the next resume, every open gap is put to a person
by id, oldest first, from the `AGE` listing that already exists, and the person closes the ones
already resolved. The only hand edit this needs is the one the walk performs.

---

## 7. Parity

Both paths get every change. The CRD has had `<gaps>` since item 48, and `check-status.py` and
`check-gate.py` already read CRDs. Two rows in [`parity.md`](../../schema/parity.md#L48):

| Capability | PRD | CRD | Status | Note |
|---|---|---|---|---|
| Uncertainty recorded as gaps (existing row) | … | … | both | note gains: *"closed gaps are kept, counted separately, and never carried"* |
| A closed gap is reviewed against its fill (new) | `commands/prd.md` — gaps closed since `<review at=>` | `commands/crd.md` — every closed gap | both, **different trigger** | settled: a CRD has no `<review>`, so it has no date to compare against |

**`checks.md` row 100** (`check-status.py`) gains *"`closed` and `closed-by` well-formed"* and
*"a `ready` CRD carries no open `specification` gap"* (§2.1). Its caller list already names both
commands, and both also become callers of `--closed-since`.

---

## 8. Why no schema version (D10)

**Core §8 measured this question for item 76, and every part of that answer applies here.**

- **The shape is unchanged for every existing artefact.** `closed` is optional, so no current file
  becomes invalid. `check-artefacts.py` hands `<gap>` to `check-status.py`
  ([`check-artefacts.py:25`](../../schema/scripts/check-artefacts.py#L25)), and `check_gaps()` never
  closes a gap's attribute set.
- **Detection is keyed on shape** ([`migration.md:532`](../../schema/migration.md#L532)). A
  schema-7 file with no closed gap would be byte-identical to a schema-6 file, so `migrate.py`
  could not tell the two apart.
- **A version would cost a frozen fixture and a migration step whose transform is the identity.**
  `SCHEMAS.json` warns that exactly this is what makes people abandon versioned fixtures.

**Where this case differs from item 76, and why that is still acceptable.** An older reader
ignoring `<architecturally-significant>` loses nothing. An older reader (2.0.3) ignoring `closed`
**treats a closed gap as open**. The effect is that it over-blocks: selection refuses, the gate
blocks, `defined` is capped, and a `ready` CRD reads as a contradiction. That is the safe
direction: a run is stopped, never waved through. The fix is `/plugin update`. The 2.1.0 merge
subject says so (§10).

**Do not add a closed gap to the reference fixture.** `tests/fixture/prd/schema-6` is current and
unfrozen. It is also the *target* of the schema-5 → schema-6 golden comparison
([`test_toolchain.py:3875-3900`](../../tests/test_toolchain.py#L3875)), which strips only
`review, notes, data-model, acceptance-criteria`. A closed gap written into schema-6 would appear
nowhere in the migrated schema-5 output, and the comparison would fail. Every check in §9 builds
its own workspace, as the existing gap checks at
[`test_toolchain.py:11469`](../../tests/test_toolchain.py#L11469) already do.

---

## 9. Checks and mutants

Every check drives the script with a document it writes itself; none asserts on prose alone, except
C10. New mutants go in `tests/mutants/gap-closed.py`.

| # | Check | Control (must still fail) | Mutant that must be caught |
|---|---|---|---|
| C1 | `closed="2026-13-40"` and `closed="soon"` → CONTRADICTION | a valid `closed` passes | skip date validation for `closed` |
| C2 | `closed` earlier than `raised` → CONTRADICTION | equal dates pass | drop the ordering test |
| C3 | `closed` later than `--today` → CONTRADICTION | `closed` equal to `--today` passes | drop the future test |
| C4 | `closed-by` without `closed` → CONTRADICTION; `closed-by="99"` with no criterion 99 → CONTRADICTION | `closed-by="1"` resolving passes | skip id resolution |
| C5 | a feature with a **closed** `specification` gap reaches the `defined` ceiling | the same feature with the gap **open** is capped | `gaps_of()` returns closed gaps again |
| C6 | `check-status.py` on a `ready` CRD with a **closed** `specification` gap exits 0 | the same CRD with the gap **open** exits 1 with CONTRADICTION; a `draft` CRD with it open exits 0 | (a) delete the new CRD `ready` test, which is §2.1's gap reopened; (b) `gaps_of()` returns closed gaps. **Both C5 and C6 must fail under (b)**, or one path is satisfying the check alone |
| C7 | `select-features.py` does not refuse a closed `specification` gap; `check-gate.py` assertion 3 does not block a closed `decision` gap, **for a PRD directory and for a CRD file** | open gaps still refuse and block on both | `check-gate.py` bypasses `gaps_of()` with its own regex |
| C8 | `build-what-next.py` lists no closed gap, and a feature with only closed gaps and `in-progress` becomes a `<feature>` row | an open gap is still listed | `GAP` matches closed gaps |
| C9 | `AGE` lines and *"N gaps open"* count open gaps only; the summary names M closed; `--closed-since` lists exactly the gaps closed on or after the date | a gap closed the day before is excluded | `ages` appends closed gaps |
| C10 | `breakdown-analyze-prd` and `task-format-spec.md` both say closed gaps are **not carried**, asserted inside their gaps sections, as a sentence with that shape | — | delete *"open"* from the carry sentence in `task-format-spec.md` |
| C11 | a new gap reusing a closed gap's id → CONTRADICTION | distinct ids pass | exclude closed gaps from the `seen` map |
| C12 | core §6's attribute table declares `closed` and `closed-by`, and both bar statements say **open** | — | drop *open* from the core `ready` sentence |

**Before launching the round:** check that every mutant's anchor text appears exactly once. A
mutant whose anchor is missing reports MISSED, which reads exactly like a check that failed to
fire. Then `git add -A`, and run the round **in the background, from Git Bash**. Expect every
mutant to be caught. Any MISSED result is investigated, never re-anchored until it goes green.

**Suite before and after**, from Git Bash (PowerShell has no `sh`, and four checks fail falsely
there).

---

## 10. Work order and release

One branch, **`gap-closed`**, off `main`. One commit per step, and the suite is green at the end of
each.

| Step | Commit | Contents |
|---|---|---|
| 1 | *Schema: a gap can be closed, and only an open gap counts.* | core §6, `crd-format.md`, `prd-format.md`, `parity.md`, `checks.md`, `CLAUDE.md`; the two suite anchors from §3.4; C12 |
| 2a | *A ready CRD with a specification gap is a contradiction, as core §6 always said.* | §2.1 only: the CRD branch of `check-status.py`, with C6's open-gap half. **Before `closed` exists**, so the finding lands and is watched failing on its own |
| 2b | *One gap parser, and it counts open gaps.* | §4: `select-features.py`, `check-status.py` (validation, report, `--closed-since`), `build-what-next.py`, `run_5_3.py`; C1–C9, C11 |
| 3 | *A closed gap is not carried.* | §5: `breakdown-analyze-prd`, `task-format-spec.md`, `breakdown/SKILL.md`; C10 |
| 4 | *A person closes a gap, and the review checks the fill.* | §6: `commands/prd.md`, `commands/crd.md`, `skills/crd/SKILL.md`, `agents/prd-criteria-author.md` |
| 5 | *(mutants)* | `tests/mutants/gap-closed.py`, a background round, and any fixes it forces |
| 6 | **Live run** (no commit unless it finds something) | see below |
| 7 | *Plugin 2.1.0: closed gaps reach an installed copy.* | `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, `version` → `2.1.0`. **Both files, and nothing else in this commit**, as 2.0.1–2.0.3 did |
| 8 | merge `--no-ff` into `main` | subject: *Merge gap-closed: a gap can be closed and only an open gap counts; closed gaps are never carried; a ready CRD's specification gap is checked, 2.1.0.* Body: *a 2.0.3 install reads a closed gap as open and over-blocks; `/plugin update`.* Then push `main` to `origin` |

**The live run is not optional.** Green checks have missed contradicting instructions before; only
a run found them. Use sample data in the fixture directory under `%TEMP%`, outside the repository,
and headless with `--plugin-dir`, `--add-dir` and `bypassPermissions`:

1. `/prd --resume` on a feature holding an open `specification` gap. Answer it as *resolved*, then
   separately as *partly resolved*. Confirm `closed`, `closed-by` and the remainder gap were
   written as §3.1 shows, and that the challenger was handed the closed gap.
2. `/crd --resume` on a `draft` CRD with an open `specification` gap. Close it and confirm the CRD
   can become `ready`.
3. `/breakdown` on both. Confirm `analysis.json` and every task's `<context>` hold **no** closed
   gap, and that the report line names the closed count.
4. Point a **2.0.3** install at the same artefacts, and confirm that it over-blocks rather than
   crashing or passing. This confirms the §8 claim by measurement rather than by argument.

**Why the version must move.** An installed plugin is cached at
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
([`distribution-and-install-analysis.md:140`](distribution-and-install-analysis.md#L140)).
Whether `/plugin update` re-fetches an **unchanged** version has not been measured, and every
release so far has bumped both manifests for exactly that reason (*"reaches an installed copy"*).
Bump regardless.

**Why 2.1.0 and not 2.0.4.** 2.0.1 to 2.0.3 each fixed a defect. This release adds a schema
capability and changes what every gap reader returns, and a 2.0.3 install reads the new artefacts
differently. That is a minor release. There is no changelog file; the merge subject is the release
note, as it has been for every 2.0.x release.

---

## 11. Out of scope

- **Mirroring `closed-by` onto `<criterion>`.** D8. The reverse lookup can be derived from the gap
  side whenever something needs it; a second copy would drift.
- **`closed-by` naming anything other than criteria**, such as an ADR, another document's criteria,
  or the new gap in D3. The body covers these, and nothing reads them.
- **Enforcing D3 or D4 mechanically.** Both need history rather than one file. A later check could
  compare a gap's attributes against `git log -p`, but nothing here requires it.
- **A "not later than today" check on `raised`.** See the asymmetry note in §3.3.
- **A migration step for gaps annotated under the old rule.** §6.4.

---

## 12. Outcome

Built as the plan describes, on branch `gap-closed`. The suite went from 175 checks to 183, all
passing, and `tests/mutants/gap-closed.py` caught 31 of 31. This section records only where the
build departed from the plan, and what a live run showed that the checks could not.

### Where the build departed from the plan

- **A closure a reader cannot trust is no closure.** D2 said a `closed` attribute that is present
  means closed. The readers go further: `select-features.is_closed()` counts a gap as closed only
  when `closed` is a real date between `raised` and today. Anything else stays open. `/breakdown`
  never runs `check-status.py`, so if presence were enough, `closed="soon"` would open the gate.
- **The gate does not validate `kind` on closed gaps.** §4 said it would. It reads open gaps only,
  and `check-status.py` still validates every gap.
- **The CRD challenger got a mode of its own, `review-closures`.** §6.3 said the review mode. A CRD
  has no `review-definition`, so the closed-gap check is a section that both modes share.
- **`/breakdown` became a caller of `check-status.py`.** Its report takes the closed count from
  `--json`, because `analysis.json` carries open gaps only. The caller-registry check caught the
  missing `checks.md` entry.
- **Two findings got ids.** §2.1's unchecked `ready` rule is **P70**. **P71** was found by the
  first mutation round, which scored 28/29: `mutate.py`'s `failing_checks()` dropped a failing
  check printed on the line directly below another. It could only produce false MISSED results.

### What the live run showed

The run used headless `claude -p` against a workspace under `%TEMP%`.

| Step | Result |
|---|---|
| `/prd --resume` on a feature with three open gaps | one gap closed, one partly resolved and closed with the rest raised as gap 4 citing it, one left open; `<authoring-gaps>` rebuilt to the two open gaps |
| `/crd --resume` on a `draft` CRD | the `specification` gap closed; the challenger dispatched in `review-closures` with `check-status.py`'s list; `ready` only because the answers authorised it |
| `/breakdown` on both | `analysis.json` and every task held open gaps only; the report counted the closed ones; `tag-links` refused for its open gap, not its closed ones |
| 2.0.3's scripts on the same files | 4 gaps open where 2 are; the CRD refused under item 15 and 2 blocking gaps at the gate where there is 1. That is over-blocking, the safe direction, and neither a crash nor a pass |

It found two defects, both fixed with a check or a mutant:

- The model wrote `closed-by="8,9"`. The walk tables showed a placeholder rather than the
  separator, and the refusal said the criteria did not exist when both did. The tables now show
  `closed-by="5 6"`, and the refusal names the separator.
- `breakdown-analyze-prd` mentioned `check-status.py` without a path, and a fork guessed
  `schema/scripts/`. That analyzer runs no scripts, so the sentence now names none.

**Not exercised by the run:** the `--closed-since` hand-off in `/prd`'s `review-definition`.
`/prd` offers that step only for a feature about to be labelled `defined`, and `tag-links` stayed
`in-progress`, correctly. The hand-off is covered by check and mutant only.

**Reported by the runs and not verified or fixed here.** None of these is part of this change.

- `/breakdown` Phase 1 step 11 runs `check-references.py` on a CRD without `--project-path`, which
  the run says resolves `PROJECT.md` against the CRD's directory.
- Phase 2's *"if analysis.json exists, skip"* has no staleness test. On a changed CRD it would have
  dropped the two new criteria.
- The PRD run wrote `analysis.json`'s `gaps` as `{open, closed_count}` rather than the documented
  list. No script reads the field.
