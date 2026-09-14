# Checks — one assertion, one owner, one exit code

[`core.md`](core.md) defines the elements. This file is the other side of item 23's rule: **every
assertion the toolchain makes about an artefact names the script that makes it, and the callers
that run it.**

It exists because item 6 had accumulated eleven assertions in one prose list, and items 22, 39, 40
and 42 each claimed some of the same ground — *"no reference anywhere to a slug that has no file"*
was owned by four of them at once. This repository's idiom is one script, one job, one exit code,
and item 6 was the first thing to depart from it.

**Item 6 is the *caller*, not the container.** `/prd`'s validation phase invokes the five scripts
its column names and reports their combined output. Each is independently runnable, independently
testable, and owns its assertion — so *"which script says a slug has no file"* has one answer.

```xml
<checks schema="schema-6"/>
```

---

## How to read the table

| Column | Holds |
|---|---|
| **Assertion** | What must be true, not which element spells it |
| **Owner** | The one script that decides it. `—` where nothing decides it yet |
| **Invoked by** | Every file that runs it -- a skill, a command, a reference, or another script. A script nobody calls is not an assertion, it is a file |
| **Paths** | Which of `/prd` and `/crd` this assertion reaches: `both`, `prd-only`, `crd-only`, or `n/a` where it never reads a requirements document at all |
| **Why, where they differ** | Required for every value except `both`. What decided it |
| **Item** | Where the assertion was specified |

### The `Paths` column, and why it is not the same claim as `parity.md`

[`parity.md`](parity.md) measures **capability** parity — is the element documented on both paths
— and its probe is a string in a format reference. This column measures **enforcement** parity —
does the assertion about that element *run* on both paths. They are different questions, and the
distance between them is where four defects lived: `<gaps>` and
`<architecturally-significant>` are both recorded there as `both`, and the checks over them
reached one path each until items 77 and P58/P60.

**`n/a` is a real verdict and it is the largest group.** Eleven of these assertions read a task
file, a manifest, a worktree or the project's own `architecture.md`. Forcing a PRD/CRD answer
onto `check-layering.py` would invent an asymmetry on an axis that does not exist there, and a
column that reports differences that mean nothing is measuring the wrong thing — the mistake
`parity.md` names about spelling, one level up.

**Every `both` row is checked by RUNNING it, against a good CRD and a broken one**
(`check-enforcement.py`). A declaration alone would be a documentation ratchet: it catches the
row nobody wrote down and nothing about whether the code reaches. This repository has recorded
nine false passes; a column asserting reach without probing it would be the tenth.

**Every owner and every caller is checked by running it**, and **in both directions since item
69**: the script must exist, each caller named must cite it by name, and — the half that was
missing — every file that *runs* an owner must appear in its column. The forward direction alone
could not see a script wired into a new caller, which is how `check-references.py` reached a CRD
for a whole phase with this table saying otherwise. A caller is a line that runs it, not a line
that mentions it; half the repository names these scripts in a docstring.

**A row with no owner is kept, not deleted.** An assertion this plan has specified and not yet
built is a fact about the project; the defect this file exists to prevent is one nobody wrote
down. Those rows were what Phase 6 was.

**There are none today, and the last one shows what the rule bought.** Item 22 was the last of
Phase 6's, and its row names `check-artefacts.py`. The `PROJECT.md` size row was written ownerless
at item 79, because filling in the `Paths` column produced it: `check-prd-size.py` is `prd-only`
for a good reason, and asking *why* surfaced that the unbounded input on the CRD path is a
different document that nothing measured. It was written down on the day it was found rather than
on the day somebody remembered it, and item 86 built it — **with the reachability measured first**,
because a row kept for a year is also a row that might turn out not to be worth building. The
count is a state, not a rule: the next assertion somebody specifies and does not build belongs
here the same day.

---

## The table

| Assertion | Owner | Invoked by | Paths | Why, where they differ | Item |
|---|---|---|---|---|---|
| An existing PRD is found before a new one is written | `list-prds.py` | `commands/prd.md` | prd-only | Its findings need two files: `DISAGREE` compares `index.md` with `what-next.md` and `WROTE IT` reads the latter's stamp. A CRD is one file with neither, and the overwrite it screens for is guarded on both paths by `check-writable.py` | 9 |
| Nothing is silently overwritten | `check-writable.py` | `commands/prd.md` · `commands/crd.md` · `skills/crd/SKILL.md` | both | — | 9, 48 |
| The repository already describes itself, and the interview reads it first | `check-project-context.py` | `commands/prd.md` | prd-only | Asks whether the repository describes itself before a greenfield interview starts. `/crd` requires a `PROJECT.md` outright, so the row below is the same question with a different answer available | 52 |
| `PROJECT.md` parses; at least one `*-registry` | `check-project-md.py` | `skills/crd/SKILL.md` · `skills/execute/SKILL.md` · `commands/crd-context.md` | crd-only | A greenfield PRD has no existing codebase to have described. Counterpart of the row above | 26 |
| Output paths resolve — the tasks directory from the document's location, never a working directory — and are not inside a plugin | `resolve-output.sh` | `skills/breakdown/SKILL.md` · `skills/breakdown-generate-tasks/SKILL.md` | n/a | Resolves where output goes. It reads the document's path, never its content | P75 |
| A resumed run's artefacts were built from the documents it is given now, or the run refuses | `check-resume.py` | `skills/breakdown/SKILL.md` | both | — | P73 |
| One repository, or refuse early and say what is missing | `check-repo-structure.py` | `skills/breakdown/SKILL.md` | both | — | 53 |
| The PRD fits the model's context, per prompt rather than per corpus | `check-prd-size.py` | `skills/breakdown/SKILL.md` | prd-only | A PRD is a corpus fanned into one prompt per feature, and this guard is what makes that split honest. A CRD is one authored document read whole -- one prompt, nothing to split. **Measured 2026-09-09**: the unbounded input on the CRD path is `PROJECT.md`, which scales with the codebase rather than with an author, and that is the row below rather than this script's job | 18 |
| `PROJECT.md` fits the prompt it is about to be sent in | `check-project-size.py` | `commands/crd.md` · `commands/crd-context.md` · `skills/crd/SKILL.md` · `skills/breakdown/SKILL.md` | crd-only | A PRD has `check-prd-size.py`; this is the same assertion about the other path's unbounded input, and it is a different document. `PROJECT.md` is generated from a codebase — one `<feature>` per feature, one entry per registry item, and a markdown half carrying the component tree — so it scales with the code and not with an author, and unlike a PRD it is read whole because there is nothing in it to split. Reachability was measured before it was built (**P69**): `crd-investigate`'s own error table already carries *Very large codebase → limit scope, note truncation*, and `project-context-finalizer` appends after every `/execute` and never compacts | 18, 86 |
| Which features may be built, and every reason each one may not | `select-features.py` | `skills/breakdown/SKILL.md` | both | — | 13, 14, 15 |
| The predicted change size has a reader | `check-scope.py` | `skills/breakdown/SKILL.md` | n/a | Reads `analysis.json` and the generated task set. The document's shape was resolved upstream | 49 |
| `<rules>` parses; `<layers>` acyclic and reachable | `check-architecture.py` | `skills/breakdown/SKILL.md` · `commands/prd.md` | n/a | Reads the project's `architecture.md`, not a requirements document | 28, 31 |
| `<banned>` and `<task-limits>` are enforced against real files | `check-rules.py` | `skills/breakdown-review-tasks/SKILL.md` · `skills/execute-verify/SKILL.md` | n/a | Reads task files against a worktree | 56 |
| Every task file parses, before any reader reports a symptom of one that does not | `check-task-xml.py` | `skills/breakdown/SKILL.md` · `skills/breakdown-review-tasks/SKILL.md` · `skills/execute/SKILL.md` | n/a | Reads task files. Three readers deferred this to each other and to an item that was never assigned | 80 |
| The manifest matches the files on disk, and the review summary is current | `build-manifest.py` | `skills/breakdown/SKILL.md` | n/a | Reads the task directory | 60, 32 |
| Every in-scope feature and criterion has a task, named where it does not | `check-coverage.py` | `skills/breakdown/SKILL.md` · `skills/breakdown/scripts/check-gate.py` | both | — | 30 |
| `ADR-NNN` / `OQ-NNN` / principle citations resolve; significance read in both directions | `check-references.py` | `commands/prd.md` · `skills/breakdown/SKILL.md` · `schema/decision-record.md` · `skills/crd/references/crd-format.md` · `skills/breakdown/scripts/check-gate.py` | both | — | 39, 35 |
| No task depends on an interface a later layer exports | `check-layering.py` | `skills/breakdown/SKILL.md` | n/a | Reads task XML and the layer plan | 73 |
| The emitted layer order is the declared graph's, minus what was dropped | `check-layer-order.py` | `skills/breakdown/SKILL.md` | n/a | Reads the emitted layer set against the declared graph | 74 |
| Coverage, significance and blocking gaps, before `/execute` may run | `check-gate.py` | `skills/breakdown/SKILL.md` | both | — | 38 |
| This toolchain can read this manifest, or refuses to guess | `check-compatibility.py` | `skills/execute/SKILL.md` | n/a | Reads `manifest.json` | 24 |
| Declared `<definition>` ≤ the ceiling its content supports, and a `ready` CRD carries no open `specification` gap; `<gaps>` well-formed — `closed` and `closed-by` included — and open gaps aged | `check-status.py` | `commands/prd.md` · `commands/crd.md` · `skills/breakdown/SKILL.md` | both | — | 3 |
| Index ↔ `features/` reconcile; no reference to a slug that has no file | `check-rename.py` | `commands/prd.md` | prd-only | Reconciles `index.md` against `features/`. A CRD has neither, so there is no pair to reconcile | 6, 42 |
| The mechanical half of the well-defined bar, and the criterion-priority spread | `check-definition.py` | `commands/prd.md` · `schema/migration.md` | prd-only | The bar is about a PRD feature's `<definition>` ladder, and [core](core.md) section 3 makes a CRD's `<workflow>` a process position rather than a degree of definition | 40, 34 |
| A rename finishes across every reference, or rolls back | `rename-feature.py` | `commands/prd.md` | prd-only | Renames a feature across an index, a feature file and every citation. A CRD is one document and its slug is its filename | 42 |
| An artefact moves exactly one schema version forward, or escalates | `migrate.py` | `skills/migrate/SKILL.md` · `agents/schema-migrator.md` · `schema/migration.md` · `commands/prd.md` · `commands/crd.md` | both | — | 41 |
| `what-next.md` is derived from the PRD, never hand-maintained, and stamped once | `build-what-next.py` | `schema/prd-format.md` · `commands/prd.md` | prd-only | `parity.md` settles deferral beyond a single document as prd-only: a CRD is one document about one change, and its deferral belongs in its own `<gaps>` | 11, 12, 24 |
| Every artefact is the shape its schema version describes | `check-artefacts.py` | `commands/prd.md` · `skills/breakdown/SKILL.md` · `skills/migrate/SKILL.md` | both | — | 22 |
| A task file is the one this run was dispatched with, or the run stops | `task-integrity.py` | `skills/execute/SKILL.md` · `skills/execute-layer/SKILL.md` | n/a | Reads a task file against the ledger that dispatched it | 63, 67 |
| Which layers this run executes, derived from the plan rather than recited | `resolve-layers.py` | `skills/execute/SKILL.md` | n/a | Reads the layer plan | 66 |
| Every element the schema defines has a reader, or a recorded reason it has none | `check-readers.py` | `tests/test_toolchain.py` | n/a | Audits the schema's elements against their readers | 23 |
| Every assertion reaches the paths its row claims, probed by running it | `check-enforcement.py` | `tests/test_toolchain.py` | n/a | Audits this table against the toolchain. `parity.md` measures whether an element is on both paths; this measures whether the check over it *runs* on both, which is the distance six live findings lived in | 79 |

---

## What is deliberately not in it

**The judgement half of the bar.** Four of item 40's eight tests cannot be settled by a script —
whether the scope names what the feature does *not* own, whether a criterion exists only to serve
a neighbour, whether a cited decision record is discharged rather than merely cited, whether a
benefit is a real benefit. They belong to
[`prd-criteria-author.md`](../agents/prd-criteria-author.md) in `review-definition` mode. A test
that needs judgement, run by a script, produces a confident wrong answer.

**The execution mechanics.** `preflight.sh`, `create-worktree.sh`, `merge-task.sh`,
`record-task.sh`, `classify-failure.sh`, `write-state.py` and `ledger-status.sh` *do* things
rather than decide whether something is true. Listing them here would turn a table of assertions
into a table of scripts, and the distinction is the whole point of the file.

**The elements themselves.** [`readers.md`](readers.md) is the companion to this table: this one
says which script decides each assertion, that one says which element has a reader and which
deliberately has none. A row here without a reader there is a check nobody consumes; an element
there without a row here is an assertion nobody owns.

**Anything a check emits as a report rather than an exit code.** `check-status.py`'s escalations,
`check-definition.py`'s one-way edges and `check-rename.py`'s retired pointers are all findings
that a person triages. They are documented in each script's own header, where the person reading
the output is looking.