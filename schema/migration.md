# Migrating artefacts between schema versions

Every schema change in this plan implies rewriting artefacts that already exist. **This file is
the specification for that rewrite, and it has a consumer** — `schema/scripts/migrate.py` for
the mechanical rules and [`schema-migrator`](../agents/schema-migrator.md) for the ones that need
judgement. It is not prose for a person to follow carefully; it is subject to the same discipline
as every other producer/consumer pair here.

**Read [`core.md`](core.md) first.** It defines the elements; this file defines how they move.

---

## What a migration is allowed to be

Three properties, and they are the reason this is a script and an agent rather than a careful
afternoon.

**Idempotent and resumable.** A 65-file migration will be interrupted. Re-running must be safe,
and the marker of *already migrated* must live in the file rather than in a side-car that can
drift from it.

> **The marker is the shape, not a stamp.** A file carrying `<definition>` is migrated; a file
> carrying `<status>` is not. Nothing is added to record the fact. A version stamp beside the
> content would be a second source of truth about the same file, free to disagree with it — the
> defect this plan spends most of its items removing, reintroduced by the tool meant to apply
> them.
>
> **The corollary is a constraint on what a transformation may be.** If completion is not visible
> in the shape, the transformation must be made **total** so that it becomes visible. Item 34's
> criterion `priority` is the case: *unassigned* and *deliberately absent* look identical, so the
> migration assigns `P1` to every criterion that lacks one rather than leaving the default
> implicit. A partial transformation with an invisible completion state cannot be resumed, and
> `migrate.py` refuses to define one.

**Per file, reviewed as a diff. Never a bulk pass.** This is item 33's rule generalised: silent
semantic loss across dozens of files is the failure mode, and only a diff catches it. The script
writes one file at a time and prints one summary line per file.

**Versioned, and the version is selected by the artefact rather than by the tool.** An artefact
stamped by an older toolchain selects the *right* migration, not the newest one. Until item 24
stamps `toolchain_version`, the shape does the selecting: `migrate.py --detect` reports which
schema a file is in, and refuses rather than guessing when the answer is not one of them.

---

## The shape of every rule

Each transformation is stated four ways, and the order matters — the precondition is what makes a
partly migrated tree safe to re-enter.

| Part | Answers | Checkable without judgement? |
|---|---|---|
| **Precondition** | may this rule run on this file at all | yes |
| **Transformation** | a rule over the *old* shape — never an example of the new one | yes |
| **Postcondition** | what must be true afterwards | **yes, and it is run** |
| **Escalation** | what to do when no precondition matches | — |

**Escalation is always the same: stop and report this file.** Never transform it anyway. A file
that matches no precondition is a file the migration does not understand, and a tool that guesses
at those is how 550 criteria lose their meaning quietly.

**A rule stated as an example of the new shape is not a rule.** *"`<criterion>` becomes an EARS
sentence"* tells an agent what to aim at and nothing about what to do with the seventeen criteria
that are already sentences. Rules here are written over what is there.

---

## schema-1 → schema-2: the rename

Purely mechanical. Three tags, values unchanged. `migrate.py` performs all of it and no agent is
involved.

| # | Precondition | Transformation | Postcondition |
|---|---|---|---|
| R1 | a PRD feature file whose `<meta>` contains `<status>` | `<status>` → `<definition>`, content preserved byte for byte | exactly one `<definition>` in `<meta>`; no `<status>` in `<meta>` |
| R2 | a CRD whose `<meta>` contains `<status>` | `<status>` → `<workflow>` | exactly one `<workflow>` in `<meta>` |
| R3 | a `PROJECT.md` `<feature>` element carrying `status=` | `status=` → `built=`, value preserved | every `<feature>` in `<features>` carries `built=` |

**R1 does not touch `index.md` or `what-next.md`.** Their `<status>` is the document-level tag,
which was not renamed. This is the rule most likely to be applied too widely, and applying it too
widely breaks `--resume` — so the precondition names the *feature file*, and `migrate.py` decides
by root element rather than by filename.

**Invariants across all three**, asserted after every file:

- **No value changes.** The set of values in the file before and after is identical. A rename
  that alters a value is not a rename.
- **Nothing else moves.** Byte-for-byte, the only differences are the tag names the rules name.
- **Element count is preserved.** One `<status>` in becomes one `<definition>` out.

**What must not be migrated mechanically: nothing.** Recorded explicitly, because it is the only
migration in this file of which that is true, and a reader who meets schema-3's table first
should know that the empty case exists.

---

## schema-2 → schema-3: where the judgement lives

Not yet written — schema-3 arrives with items 1, 2, 5, 33, 34 and 35. What is settled now is the
**boundary**, because the boundary is what stops an agent guessing.

**Mechanical, and `migrate.py`'s to perform:**

| Transformation | Rule over the old shape | Item |
|---|---|---|
| `<priority>` deleted from a feature's `<meta>` | only after the index entry is confirmed to carry it | 1 |
| `<notes>` prose split | a bold `**Data model**` heading opens `<data-model>`; **everything else goes to `<considerations>` verbatim** | 2 |
| `<phases>` removed, `phase=` dropped from criteria | a `phase="2"` becomes a `<gap>` only where the file states a reason; otherwise it is dropped and the drop is reported | 5 |
| criterion `priority` assigned | **`P1` to every criterion lacking one** — total, so completion is visible | 34 |
| `<affected-apis>` → `<affected-contracts kind="api">` | one contract element per api element | 57 |

**Judgement, and never mechanical:**

| Judgement | Why a machine must not | Item |
|---|---|---|
| assigning a criterion's EARS `pattern` | a pattern derived by the heuristics it is meant to replace is circular | 33 |
| raising a criterion's `priority` above `P1` | `P1` is the safe default; anything else is a claim about importance | 34 |
| setting `<architecturally-significant>` | not derivable from any structural property — that is the point of the flag | 35 |
| rewriting a Given/When/Then into EARS | the mechanical part is large and the loss is concentrated in the few criteria that were never event-shaped | 33 |

**The guide's job here is to stop an agent guessing, not to help it.** Where a judgement is
required and the agent is not confident, the answer is the escalation: stop and report this file.

**Criterion count in equals criterion count out**, and every migrated criterion carries
`derived-from="{{old id}}"` until the migration is signed off. That is the invariant that makes
the EARS rewrite reviewable at all.

---

## The CRD path

Seven items in §5 J change artefacts that are already written. A migration scoped to PRDs would
leave every existing CRD and `PROJECT.md` behind.

| Artefact | Transformation | Item |
|---|---|---|
| `docs/crd/{slug}.md` | `<meta><status>` → `<workflow>` | 45 |
| | `<requirements>` retired; each becomes an EARS criterion in the single list | 46, 33 |
| | requirement `priority` MoSCoW → `P0\|P1\|P2` on the criterion | 47 |
| | `<meta>` gains a document-level MoSCoW `<priority>` | 47 |
| | deferred criteria become `<gap kind="specification">` | 48 |
| | `<affected-apis>` → `<affected-contracts kind="api">` | 57 |
| `PROJECT.md` | `<feature status=>` → `built=` | 45 |
| | registries stay at root; **none is added or removed by migration** | 25 |

**Two CRD-specific rules.**

**A CRD whose `<workflow>` is `complete` or `abandoned` is migrated but not re-reviewed.** It is a
record of something that already happened. Rewriting its criteria into EARS is a formatting
change, not a re-specification, and treating it as one invites an agent to improve a record of
the past.

**`<affected-apis>` is accepted on read for a full release after the migration.** A CRD is often
authored in one place and broken down in another; a hard cutover strands the ones in flight. This
is the same policy core §3 states for the three renamed status tags, and it is one policy rather
than three by design.

---

## Running it

```bash
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --to schema-2
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --to schema-2 --dry-run
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --detect
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --to schema-2 --check
```

`<path>` is a file or a directory; a directory is walked and each file decided on its own.

| Exit | Means |
|---|---|
| **0** | every file is now in the target schema, and every postcondition holds |
| **1** | a postcondition failed. **The file was restored**; nothing partly written survives |
| **2** | escalation — one or more files matched no precondition. Nothing was written for those, and each is named |
| **3** | usage error |

**`--check` writes nothing** and asserts the postconditions against files as they are. It is what
makes *"the migration ran"* a different claim from *"the migration finished"*, and it is what the
regression suite calls.

**Re-running is safe and is expected.** A file already in the target schema is reported
`ALREADY` and left untouched, which is the same answer whether it was migrated a second ago or a
release ago — because the marker is the shape.
