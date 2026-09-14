# Parity — where the two paths differ, and why

[`core.md`](core.md) is the elements `/prd` and `/crd` **share**. This file is the other half:
every capability one path has and the other does not, with a verdict and a reason.

**It exists because the distance between two paths is invisible until something measures it.**
Five of the asymmetries this plan resolved existed because nobody had read the two paths side by
side — the plan itself was PRD-only for forty-three items. A paragraph describing the difference
goes stale the week after it is written; a table with probes cannot, because the probes are run.

```xml
<parity schema="schema-6"/>
```

---

## How to read the table

| Column | Holds |
|---|---|
| **Capability** | What a path can do, not which element it spells it with |
| **PRD** / **CRD** | `file :: string` — the evidence that path has it, or `—` for absent |
| **Verdict** | `both`, `prd-only` or `crd-only` |
| **Settled** | `yes` where the asymmetry is deliberate, `open` where nobody has decided |
| **Why** | Required for every asymmetric row. What decided it, or what is undecided |

**Every non-`—` cell is checked by running it**: the file must exist and the string must be in
it. That is what stops this table describing a toolchain that has moved on — a resolved row whose
evidence has been deleted fails, and so does an `—` whose counterpart has quietly appeared.

**`open` is a legitimate verdict and is not a failure.** The regression suite lists the open rows
rather than refusing them. An asymmetry nobody has examined is a fact about this project; the
defect the file exists to prevent is one nobody has *written down*.

**Verdicts are about capability, not spelling.** `<scope>` is an element in a CRD and a field in
`analysis.json` on the PRD path, and the row says `both` because both paths predict change size.
A row that tracked element names would report a difference that means nothing.

---

## The table

| Capability | PRD | CRD | Verdict | Settled | Why |
|---|---|---|---|---|---|
| Acceptance criteria, in EARS | `schema/prd-format.md :: <acceptance-criteria>` | `skills/crd/references/crd-format.md :: <acceptance-criteria>` | both | — | items 33, 46 |
| Requirement-level priority | `schema/prd-format.md :: priority="P0"` | `skills/crd/references/crd-format.md :: priority="P0"` | both | — | items 34, 47 — one vocabulary, `P0\|P1\|P2` |
| Whole-item MoSCoW | `schema/prd-format.md :: must-have` | `skills/crd/references/crd-format.md :: <priority>should-have</priority>` | both | — | item 47. The PRD's lives in the index, the CRD's in `<meta>`, because a change request is its own planning unit |
| Uncertainty recorded as gaps | `schema/prd-format.md :: <gaps>` | `skills/crd/references/crd-format.md :: <gaps>` | both | — | items 29, 48. A resolved gap is closed rather than deleted, on both paths: closed gaps are kept, counted separately, and never carried |
| Analysis confidence | `skills/breakdown-analyze-prd/SKILL.md :: confidence` | `skills/crd/references/crd-format.md :: <confidence>` | both | — | item 49. The CRD declares it; the PRD path's analyser emits it per feature |
| Change size predicted | `skills/breakdown-analyze-prd/SKILL.md :: scope` | `skills/crd/references/crd-format.md :: <scope>` | both | — | item 49. Nothing is written back to the PRD — the prediction lives in `analysis.json` |
| That prediction has a reader | `skills/breakdown/SKILL.md :: check-scope.py` | `skills/breakdown/SKILL.md :: check-scope.py` | both | — | item 49. One reader, both paths |
| Resume of an interrupted interview | `commands/prd.md :: --resume` | `commands/crd.md :: --resume` | both | — | item 48 |
| Pre-write overwrite guard | `commands/prd.md :: check-writable.py` | `commands/crd.md :: check-writable.py` | both | — | F3, item 9, then item 48. One script, generalised to take a file |
| Layer set derived from content | `skills/breakdown/SKILL.md :: check-scope.py` | `skills/crd/references/crd-format.md :: <impact-analysis>` | both | — | item 31 |
| Impact against existing code | — | `skills/crd/references/crd-format.md :: <impact-analysis>` | crd-only | yes | A greenfield PRD has nothing to have an impact on. The counterpart is `architecture-format.md`, which is a *design*, not an assessment |
| Deferral beyond a single document | `schema/prd-format.md :: what-next.md` | — | prd-only | yes | Item 48 considered and rejected a `what-next` per CRD. A CRD is one document about one change; the deferral belongs in its own `<gaps>` and the next command in `<meta>` |
| An intent statement per item | `schema/prd-format.md :: <user-story>` | `skills/crd/references/crd-format.md :: <motivation>` | both | — | Different elements, one capability. A feature says who wants it and why; a change request says why it is being made |
| Declared dependency edges | `schema/prd-format.md :: <depends-on` | — | prd-only | yes | **Settled 2026-09-08 (V7): deliberate.** `<depends-on>` exists so `plan-layers` can order *items within one document*; a CRD **is** one item, so there is no set to order. Ordering between separate CRDs is a different capability, and **nothing in the toolchain consumes it** — no multi-CRD workflow exists to read it. Adding the element would be a producer with no reader, which is the defect item 27 itself refused: an ordering nothing derives from is a second model's unvalidated inference |
| A data model channel, in the document | `schema/prd-format.md :: <data-model>` | `skills/crd/references/crd-format.md :: kind="schema"` | both | yes | **Settled 2026-09-08 (V7): the row was reading the spelling.** `<contract kind="schema" ref="User">` is the CRD's channel and item 57 generalised it; an *added* entity is a contract naming a ref that does not exist yet. It has readers — `crd-impact-analysis`, `check-artefacts.py` |
| That channel reaching a task | `skills/breakdown/references/task-format-spec.md :: <data-model>` | `skills/breakdown-generate-tasks/SKILL.md :: affected-contracts` | both | yes | **Closed by item 75.** V7 found this as the residual after the row above turned out to be reading the spelling: the task format defined `<data-model>` as *the feature's own*, `analyze-prd` did not mention a CRD at all, and `generate-tasks` carried `architecture.md`'s registry rather than the document's contracts. One element now has two producers, and the CRD's `kind="schema"` entries reach the task that touches them |
| Architectural significance flag | `schema/core.md :: architecturally-significant` | `skills/crd/references/crd-format.md :: architecturally-significant` | both | yes | **Closed by item 76.** Defined once in core §8 and cited by both format references; `check_crd()` gained the same assertions the PRD screen makes, plus the enum. V7 first called this a reader with no producer — it was neither: `main()`'s CRD branch returns before the significance screen, so the element had no reader here either, and the two had to arrive together |

---

## Adding a row

**When you give one path something the other lacks, add the row in the same commit.** That is the
whole discipline. The table is cheap to extend and expensive to reconstruct — the twelve rows this
started from took a read of two commands, three sub-skills, four agents and both format
references, and half of what it found had been true for months.

A row leaves the table only when the capability leaves the toolchain. **A resolved asymmetry stays,
with `both` and the item that resolved it**, because *"these are the same now"* is a fact worth
being able to check, and a row that disappears on resolution takes its evidence with it.
