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
<checks schema="schema-5"/>
```

---

## How to read the table

| Column | Holds |
|---|---|
| **Assertion** | What must be true, not which element spells it |
| **Owner** | The one script that decides it. `—` where nothing decides it yet |
| **Invoked by** | Every document that runs it. A script nobody calls is not an assertion, it is a file |
| **Item** | Where the assertion was specified |

**Every owner and every caller is checked by running it**: the script must exist, and each caller
named must cite it by name. That is what stops this table describing a toolchain that has moved on.

**A row with no owner is kept, not deleted.** An assertion this plan has specified and not yet
built is a fact about the project; the defect this file exists to prevent is one nobody wrote
down. Those rows were what Phase 6 was.

**There are none left, and that is a state rather than an achievement to protect.** Item 22 was
the last one; its row now names `check-artefacts.py`. The next assertion somebody specifies and
does not build belongs here as an ownerless row on the day it is specified, not on the day
somebody remembers it.

---

## The table

| Assertion | Owner | Invoked by | Item |
|---|---|---|---|
| An existing PRD is found before a new one is written | `list-prds.py` | `commands/prd.md` | 9 |
| Nothing is silently overwritten | `check-writable.py` | `commands/prd.md` · `commands/crd.md` · `skills/crd/SKILL.md` | 9, 48 |
| The repository already describes itself, and the interview reads it first | `check-project-context.py` | `commands/prd.md` | 52 |
| `PROJECT.md` parses; at least one `*-registry` | `check-project-md.py` | `skills/crd/SKILL.md` · `skills/execute/SKILL.md` · `commands/crd-context.md` | 26 |
| Output paths resolve, and are not inside a plugin | `resolve-output.sh` | `skills/breakdown/SKILL.md` · `skills/breakdown-generate-tasks/SKILL.md` | — |
| One repository, or refuse early and say what is missing | `check-repo-structure.py` | `skills/breakdown/SKILL.md` | 53 |
| The PRD fits the model's context, per prompt rather than per corpus | `check-prd-size.py` | `skills/breakdown/SKILL.md` | 18 |
| Which features may be built, and every reason each one may not | `select-features.py` | `skills/breakdown/SKILL.md` | 13, 14, 15 |
| The predicted change size has a reader | `check-scope.py` | `skills/breakdown/SKILL.md` | 49 |
| `<rules>` parses; `<layers>` acyclic and reachable | `check-architecture.py` | `skills/breakdown/SKILL.md` · `commands/prd.md` | 28, 31 |
| `<banned>` and `<task-limits>` are enforced against real files | `check-rules.py` | `skills/breakdown-review-tasks/SKILL.md` · `skills/execute-verify/SKILL.md` | 56 |
| The manifest matches the files on disk, and the review summary is current | `build-manifest.py` | `skills/breakdown/SKILL.md` | 60, 32 |
| Every in-scope feature and criterion has a task, named where it does not | `check-coverage.py` | `skills/breakdown/SKILL.md` | 30 |
| `ADR-NNN` / `OQ-NNN` / principle citations resolve; significance read in both directions | `check-references.py` | `commands/prd.md` · `skills/breakdown/SKILL.md` · `schema/decision-record.md` | 39, 35 |
| Coverage, significance and blocking gaps, before `/execute` may run | `check-gate.py` | `skills/breakdown/SKILL.md` | 38 |
| This toolchain can read this manifest, or refuses to guess | `check-compatibility.py` | `skills/execute/SKILL.md` | 24 |
| Declared `<definition>` ≤ the ceiling its content supports; `<gaps>` well-formed, and aged | `check-status.py` | `commands/prd.md` | 3 |
| Index ↔ `features/` reconcile; no reference to a slug that has no file | `check-rename.py` | `commands/prd.md` | 6, 42 |
| The mechanical half of the well-defined bar, and the criterion-priority spread | `check-definition.py` | `commands/prd.md` | 40, 34 |
| A rename finishes across every reference, or rolls back | `rename-feature.py` | `commands/prd.md` | 42 |
| An artefact moves exactly one schema version forward, or escalates | `migrate.py` | `skills/migrate/SKILL.md` · `agents/schema-migrator.md` · `schema/migration.md` | 41 |
| `what-next.md` is derived from the PRD, never hand-maintained, and stamped once | `build-what-next.py` | `schema/prd-format.md` | 11, 12, 24 |
| Every artefact is the shape its schema version describes | `check-artefacts.py` | `commands/prd.md` · `skills/breakdown/SKILL.md` | 22 |
| Every element the schema defines has a reader, or a recorded reason it has none | `check-readers.py` | `tests/test_toolchain.py` | 23 |

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
