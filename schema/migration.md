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

**Who makes each judgement is fixed here, and almost all of them are a person's.** Every table
below headed *"never the script's"* says what a script must not do. It does not hand the rest to
an agent. `schema-migrator` is a machine too, and a judgement a script must not make because it
would be guessed is guessed just the same by a model. This table is the whole allocation. Every
judgement named anywhere in this file is one row of it, and only two rows go to the agent:

| Judgement | Element | Made by |
|---|---|---|
| rewriting a Given/When/Then triple, or a migrated requirement's body, into one EARS sentence | `<criterion>` | agent |
| extracting a `<data-model>` from `<notes>` where no heading marks one | `<data-model>` | agent |
| assigning an EARS `pattern` | `pattern` | person |
| raising a criterion's `priority` above `P1` | `priority` | person |
| writing a `<user-story>` | `<user-story>` | person |
| declaring `<depends-on>` edges | `<depends-on>` | person |
| writing a `<gap>` or deciding its `kind` | `<gap>` | person |
| setting `<architecturally-significant>` | `<architecturally-significant>` | person |
| reclassifying `<definition>` | `<definition>` | person |
| a CRD's document-level `<meta><priority>` | `<meta><priority>` | person |
| demoting a CRD's `<workflow>` | `<workflow>` | person |
| writing a missing `<rationale>` (R7) | `<rationale>` | person |
| writing a missing `<superseded-by>` pointer (R8) | `<superseded-by>` | person |
| recording a `<review>` (R13) | `<review>` | person |

**The two agent rows are the ones that transform content already there.** The sentence is in the
triple and the data model is in the notes; the agent rewrites them and nothing is added. Every
person row writes something the file does not contain: a classification, a claim about
importance, a relationship or a decision. That is the line, not a list of hard cases. A file
with the agent's half done still has no `pattern`, so it is still `PARTIAL` and `--check` still
refuses it. That is the correct end of a run, not an unfinished one.

**An orchestrator must not restate this allocation in its own words.** A live run of
`/migrate` on sample data summarised the rules into its agents' prompts and told them to assign
`pattern`. A task prompt outranks an agent's definition, so the agents did as told, and sixteen
files came back with invented patterns. Nothing in the agent's own forbidden list
could stop it. The skill carries a prompt used as
written, and the suite holds that prompt, the agent's lists and this table to the same rows.

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

## schema-2 → schema-3: the first step nobody can finish alone

Items 33 and 34. A `<criterion>` stops being a Given/When/Then triple and becomes one EARS
sentence carrying `pattern` and `priority`.

**This is the first step that is part mechanical and part judgement**, and the split is the whole
design of it.

### The mechanical half — `migrate.py`'s

| # | Precondition | Transformation | Postcondition |
|---|---|---|---|
| R4 | a PRD feature file with any `<criterion>` lacking `priority` | every criterion lacking `priority` gains `priority="P1"`; every one lacking `derived-from` gains `derived-from="{{its id}}"` | every criterion carries both, and the id list is unchanged |
| R5 | a CRD, same condition | as R4 | as R4, except that a `complete` or `abandoned` CRD needs no `pattern` |

**`priority="P1"` is written in rather than left to the documented default, and that is not
noise.** An absent attribute and a deliberate `P1` are indistinguishable, so a partly-assigned
corpus could not be told from a finished one — and the marker is the shape. This is the
constraint the top of this file states, meeting its first real case.

**The precondition is `priority`, and it used to be `pattern`.** A pattern-less criterion stopped
being evidence that a file predates item 34 the moment R10 existed, because R10's postcondition
requires the criteria it creates to carry **no `pattern`** — a migrated requirement's EARS sentence
is a judgement nobody has made yet. Keyed on `pattern`, R4 and R5 re-fired on a schema-5 CRD, and
`detect` read it back as schema-2: the file oscillated between versions on alternate runs and
collected `derived-from="1"` on criteria a person had authored, which is a false record of
provenance in the one attribute whose whole purpose is to be a true one. Keyed on `priority` — the
attribute the transform makes **total**, for exactly this reason — the rule fires when it has work
to do and not otherwise.

**`derived-from` is what makes the rewrite reviewable.** It carries until the migration is signed
off, and it is the only way a reader can check a rewritten sentence against the triple it came
from.

**Sign-off is not this file's step, and nothing here performs it.** It happens in two steps, both
a person's, per [core §2](core.md#2-acceptance-criteria). In `/prd --resume`,
`prd-criteria-author` proposes a `pattern` for each migrated sentence, and the person accepts or
corrects each one while `derived-from` stays. Recording the feature's review then removes
`derived-from` from every classified criterion. That is why the fixtures from schema-3 onward
carry both attributes: they are classified and not yet signed off. `/migrate` never dispatches
that agent. A proposal nobody is present to accept is the unattended judgement this file forbids,
however it is labelled. **A CRD signs off in `/crd --resume`.** The person classifies the same way,
and also supplies what R10 leaves on the document: `<meta><priority>`, and any `<gap>` a CRD from
before item 48 never recorded. `schema/scripts/sign-off.py` then does the edit a PRD's review does,
from the same code.

**R4 and R5 are vacuously satisfied by an artefact with no criteria**, and that is correct rather
than convenient. A feature carrying zero criteria is `excluded` or `superseded`; requiring at
least one would turn a rule about criteria into a rule about features and escalate a legitimate
file.

### The judgement half — never the script's

| Judgement | Why a machine must not |
|---|---|
| rewriting the triple into one EARS sentence | the mechanical part is large and the loss is concentrated in the few criteria that were never event-shaped. A count cannot find those |
| assigning `pattern` | a pattern derived by the heuristics it exists to replace is circular |
| raising `priority` above `P1` | `P1` is the safe default; anything else is a claim about importance |

### PARTIAL: the third state, and why it has a name

A file with the mechanical half applied and the judgements outstanding is **`PARTIAL`**, and it is
detectable from its shape alone: `priority` present, `pattern` absent.

- `migrate.py` reports it per file and exits **0** — the half it could do, it did.
- **`--check` refuses the tree**, exit 1. *"The script ran"* and *"the migration finished"* are
  different claims, and this is the difference.
- A `defined` feature carrying pattern-less criteria is a contradiction; a `tbd` one is just
  unfinished. That distinction belongs to item 3's derivation, not here.

**Naming the state is what stops the boundary being crossed in either direction.** A script that
stopped at it entirely would leave the mechanical work undone across 550 criteria; one that
crossed it would invent the judgement it was written to protect. Neither failure announces
itself, which is why the state is reported rather than inferred.

## schema-3 → schema-4: the rest of the feature template

Items 1, 2, 5, 27, 29 and 35. `<user-story>`, `<depends-on>`, `<gaps>`,
`<architecturally-significant>`, the `<notes>` split, and the removal of the duplicated
`<priority>`. **Mixed, like the step before it**, and for the same reason: some of it is a
transformation of what is there, and the rest is content nothing in the file implies.

### The mechanical half — `migrate.py`'s

| # | Precondition | Transformation | Postcondition |
|---|---|---|---|
| R6 | a PRD feature file with `<meta><priority>`, or a `<notes>` not yet split, or a `defined` feature with no `<user-story>` | `<priority>` is deleted from `<meta>`; `<notes>` prose is split into `<data-model>` and `<considerations>` | no `<priority>` in `<meta>`; `<notes>` contains `<considerations>`; a `defined` feature has a `<user-story>` |

**`<priority>` is deleted only after the index entry is confirmed to carry it.** The index is the
survivor of the pair, so removing the copy before checking the original would lose the fact
rather than deduplicate it.

**The `<notes>` split keys on a bold `**Data model**` heading, and everything else goes to
`<considerations>` verbatim.** That is what makes it mechanical at all: one side of a two-way
split never has to be understood. A three-way split — data model, relationships, considerations —
was on this plan's critical path until `<depends-on>` took the relationships, and it needed a
judgement per file.

**A feature with no `<notes>` gains none.** The rule transforms prose that exists; it is not an
instruction to write some.

### The judgement half — never the script's

| Judgement | Why a machine must not |
|---|---|
| writing a `<user-story>` | new content, not a transformation. Nothing in the file implies the benefit clause, which is the half that matters |
| declaring `<depends-on>` edges | a markdown link and a dependency are not the same thing, and that ambiguity is the defect item 27 exists to fix. Deriving edges from links puts the guess back |
| deciding a `<gap>`'s `kind` | the difference between a blocked dependency and an undecided question is what the gap is *for* |
| setting `<architecturally-significant>` | not derivable from any structural property — that is the point of the flag |
| extracting a `<data-model>` where no heading marks one | the heading convention is what makes the split mechanical; without it, the boundary is a judgement |
| reclassifying `<definition>` | item 4. A `specification` gap bars `defined`, and applying that is a decision about the feature, not about its format |

**`<user-story>` is required for `defined`, not for `tbd`.** A feature acquires one on promotion,
so the migration owes stories only for the features already at `defined`. R6 asks exactly that,
in its precondition and its postcondition alike. **For five schema versions it asked every
feature.** The prose here said `defined` and the rule's code said everyone, so a `tbd` feature
stayed `PARTIAL` on R6 for good. It was owed a story nobody could write, because a story arrives
when a feature is promoted.

---

## schema-4 → schema-5: the CRD path takes the parity changes

Items 46, 47 and 48. `<requirements>` is retired into the criteria list, requirement-level MoSCoW
becomes `P0|P1|P2`, `<meta>` gains a document-level MoSCoW, and `<gaps>` arrives. **Mixed**, and
this is the first step whose mechanical half can *move* content rather than only relabel it — a
`<requirement>` becomes a `<criterion>`, which is a transformation, while the EARS sentence it
ought to be is not.

**This step touches CRDs only.** PRD features, `PROJECT.md` and `what-next.md` are unchanged and
are named as unchanged rather than left to fall through — *"no rule matched"* and *"no rule was
needed"* are different answers and only the first is an escalation.

### The mechanical half — `migrate.py`'s

**It is R10, not R7.** R7 and R8 are item 4's conventions — `excluded` needs a `<rationale>`,
`superseded` needs a pointer — which are rules about an artefact rather than steps in a version,
and R9 is `what-next.md`'s half of schema-4. The identifiers are a flat space across this guide
and its executor, so a number is never reused.

| # | Precondition | Transformation | Postcondition |
|---|---|---|---|
| R10 | a CRD with a `<requirements>` element | each `<requirement>` becomes a `<criterion>` appended to `<acceptance-criteria>`, renumbered to continue after the highest existing criterion id, carrying `derived-from="requirement-N"` and its MoSCoW mapped to `P0\|P1\|P2`; `<requirements>` is removed | no `<requirements>`; every migrated criterion has a `priority` and a `derived-from`; **no `pattern`**. The step is finished when every criterion has a `pattern` and `<meta>` has a `<priority>`, **except on a `complete` or `abandoned` CRD, which needs neither** |

**The ids merge, so they have to be renumbered, and that is the only lossy-looking part of the
step.** Requirement 1 and criterion 1 were two different things in two id spaces, and after item
46 there is one space. Renumbering the *requirements* rather than the criteria is deliberate:
existing criterion ids may already be cited from a commit message or a task file, and the whole
purpose of `id` is that such a citation still resolves. `derived-from="requirement-3"` is what
keeps the other half of the history readable — and it is prefixed rather than bare because after
this step a bare `3` would be ambiguous between the two former spaces.

**The MoSCoW map is one to one, and the fourth value has no target.**

| Was | Becomes |
|---|---|
| `must-have` | `P0` |
| `should-have` | `P1` |
| `could-have` | `P2` |
| `wont-have` | **the file is not placed; the migration stops and names it** |

`P0|P1|P2` has no *"not building this"* value by design — that judgement belongs to the whole
item, which on this path is the document. `P2` would make a declined requirement buildable, since
`--requirement-level` defaults to `P2`; dropping it would delete something a person wrote. Both
are decisions about the change rather than about its format, so this is an escalation. It uses
machinery that already exists: `--check` refuses the tree and the file is named, exactly as an
unplaceable artefact is.

### The judgement half — never the script's

| Judgement | Why a machine must not |
|---|---|
| the EARS sentence and `pattern` for a migrated requirement | the same rule as R4 and R5, arriving through a different door. A requirement body is prose someone wrote to be read, not a sentence with a trigger and a response waiting to be extracted, and a `pattern` inferred by the heuristics it exists to replace is circular |
| `<meta><priority>` | the document's MoSCoW is **new content**. Nothing in the file implies it, and the obvious derivation — take the highest requirement priority — conflates the two levels item 47 just separated |
| `<gaps>` | there is nothing to transform. A CRD written before item 48 recorded its deferrals nowhere, so the absence of a gap is not evidence there were none. This is the one place the migration can only leave a hole and say so |
| demoting `<workflow>` from `ready` to `draft` | a consequence of the judgement above. Once a `specification` gap is written in, `ready` becomes a contradiction — but the gap has to be written by someone who knows what was deferred |

**A CRD whose `<workflow>` is `complete` or `abandoned` is migrated but not re-reviewed**, per the
rule already stated below. Its requirements still become criteria — that is a formatting change —
but nobody is asked to supply the EARS sentences, the gaps or the document tier for a change that
already happened. **So R5 and R10 do not wait for them.** For four schema versions both did: their
completion tests asked every CRD for patterns and a tier. Every finished CRD stayed `PARTIAL` for
good, and `--check` could never pass a corpus that held one. `check-artefacts.py` exempts the
same files from the `<meta><priority>` it otherwise requires, using `migrate.py`'s definition of
a record of the past rather than a second one. The `derived-from` attributes stay in place permanently on those files, because
sign-off is a thing that happens to work in flight.

---

## schema-5 → schema-6: the review the gate always required

**Item 40's bar is two halves — the mechanical tests pass *and* a review has been recorded — and
for four phases the second half had nowhere to live.** `<review by= at= sha=>` in a feature's
`<meta>` is that place ([core §7](core.md#7-review--the-half-of-the-defined-gate-that-is-not-mechanical)),
and this step is the first whose feature half is **entirely** a person's.

### The mechanical half — `migrate.py`'s

| Rule | Artefact | What it does |
|---|---|---|
| **R11** | `index.md` | a document `<status>` outside `in-progress\|complete` becomes `in-progress` |
| **R12** | `what-next.md` | the same, in the file that has to agree with it |

**Why `in-progress` and not `complete`.** It is the weaker claim, and a machine choosing the
stronger one would assert that an interview finished which nobody finished. The same rule settled
the layer-graph spike: where the evidence does not decide, resolve toward protection.

**This is the second rule that changes a value rather than a tag**, after R10's MoSCoW mapping,
and it is exempted from the rename invariant by name — `applied_adds_values` lists the rules
allowed to move a value, because that invariant is the only thing standing between a rename and
an edit for R1–R3.

### The judgement half — never the script's

**R13 has no mechanical half at all, and it is the first rule of which that is true.** A review
is a person having read the feature; there is nothing in the file to derive one from. So the
transform is the identity, every `defined` feature reports `PARTIAL`, and `--check` refuses the
tree until somebody records the reviews:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-definition.py docs/prd/<slug> \n    --record-review --by <name>
```

**The rejected alternative was a placeholder** — a `<review>` with no reviewer, written by the
migration so the shape would be present. That is a record of nothing, and this repository's rule
is that a ledger records SHAs rather than adjectives. An unsigned review is the adjective.

**A migration invalidates the reviews it rewrites**, and that is correct rather than unfortunate.
`sha` covers the file with the review element removed, so any later step that rewrites a feature
leaves its review `STALE` — which is the true statement: somebody read a document that has since
changed. Re-reviewing is one command, and the alternative is a hash that survives edits, which is
a record of nothing again.

## The conventions, and what they make checkable

Item 4. `excluded` and `superseded` were conventions an authoring corpus invented because the
schema had nowhere to record *"we decided not to build this"*. They are schema now, and each is
paired with the element that says **why** — which is what turns a convention into something a
postcondition can hold.

| # | Precondition | Transformation | Postcondition |
|---|---|---|---|
| R7 | a feature whose `<definition>` is `excluded` | none — this is a rule, not a rewrite | it carries a non-empty `<rationale>` |
| R8 | a feature whose `<definition>` is `superseded` | none | it carries `<superseded-by slug=>`, the slug resolves to a feature that exists, and **no `index.md` entry points at this feature** |

**R7 and R8 transform nothing, and that is deliberate.** A migration cannot invent a rationale
for a decision it was not present for. What it can do is **refuse to finish** while one is
missing, which turns *"somebody will notice"* into an exit code at the moment the file is being
touched anyway.

**The exit code is 2, and for a while it was 1.** That was the wrong half of the interface: exit
1 means a rule broke its own postcondition, and it is paired everywhere with *"a defect in the
rule, not in the artefact"* and *"never work around it by editing a file by hand."* Both are
exactly backwards for a missing rationale — the artefact is what is incomplete, and a person
writing the sentence is the fix rather than a way past the check. This guide had already settled
the identical question one rule along: a `wont-have` requirement escalates *"using machinery that
already exists"*, because it too is a decision about the change rather than about its format. The
same reasoning reaches the same code here, and the reported line says which of the three kinds of
exit 2 it is.

**The routing depended on a dual read that was not implemented, which is why this was found late.**
Core §3 says a reader finding `<status>` where it expects `<definition>` treats it as that element.
`migrate.py` read only the new spelling, so an `excluded` feature that had not been renamed yet
slipped past the check on the way in and was caught on the way out, after R1 had renamed the tag
for it — and on the way out, a gap the artefact **arrived with** is indistinguishable from a gap
the migration **created**. An unimplemented compatibility read looks like a missing read and was
in fact a misrouting.

**Index removal is the half that is easy to forget.** A superseded feature stays on disk as a
record and leaves the index, because the index is the *planning* view and a merged feature is no
longer a unit of planning. Leaving the entry there makes the feature count wrong and gives
`--priority` something to select that nobody intends to build.

**Reclassifying `<definition>` is a judgement, and the rule it will follow is a ceiling.**
Item 3 builds the derivation; the constraint it inherits is recorded here so it implements rather
than invents:

> Derive **at most** what the content supports. Report where the declared status **exceeds** the
> ceiling; stay silent where it sits below. A feature an author has held at `in-progress` for
> reasons the file cannot express is never contradicted upward — and a `<gap kind="specification">`
> against a `defined` feature is reported as the contradiction it is, not escalated.

A derivation that reports a *value* can contradict an author. One that reports a *ceiling*
cannot, and that is the whole reason the check is three-valued by construction rather than by
concession.

---

## The CRD path

Seven items in §5 J change artefacts that are already written. A migration scoped to PRDs would
leave every existing CRD and `PROJECT.md` behind.

| Artefact | Transformation | Item | Version |
|---|---|---|---|
| `docs/crd/{slug}.md` | `<meta><status>` → `<workflow>` | 45 | schema-2 |
| | Given/When/Then criteria become EARS | 33 | schema-3 |
| | `<requirements>` retired; each becomes a criterion in the single list | 46 | **schema-5** |
| | requirement `priority` MoSCoW → `P0\|P1\|P2` on the criterion | 47 | **schema-5** |
| | `<meta>` gains a document-level MoSCoW `<priority>` | 47 | **schema-5** |
| | deferred criteria become `<gap kind="specification">` | 48 | **schema-5** |
| | `<review by= at= sha=>` records that a feature was read | 40 | **schema-6** |
| | a document `<status>` outside its own enum becomes `in-progress` | 22 | **schema-6** |
| | `<affected-apis>` → `<affected-contracts kind="api">` | 57 | *accepted on read; not a step* |
| `PROJECT.md` | `<feature status=>` → `built=` | 45 | schema-2 |
| | registries stay at root; **none is added or removed by migration** | 25 | — |

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
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --detect
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --to schema-4 --dry-run
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --to schema-4
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py <path> --to schema-4 --check
```

`<path>` is a file or a directory; a directory is walked and **each file decided on its own** —
including which schema it starts from, so a tree holding artefacts of three vintages migrates in
one pass and each one takes only the steps it needs.

**The walk takes every `.md` file, and most corpora hold some that are not artefacts.** A file
carrying none of the five root elements is reported `SKIPPED` and changes no exit code. It was an
escalation once, which meant a single `README.md` beside `docs/prd/` halted the migration before
it began — and worse, gave the operator no way to tell that harmless case from a `<feature>` in
no recognised schema, since both arrived as exit 2 under the same word.

**But an absent root element is only half the question, and the first version of this rule asked
only that half.** *"Does this file have a root element"* decides whether a README is an artefact.
It also silently decides that a `what-next.md` holding nothing but `# What Next` is not one — and
that file is an artefact of the PRD in every sense except the one being tested. A `/prd` run that
went off-script and never wrote the skeleton produces exactly it, which is how this was found: on
a corpus, not in the suite, and only because `SKIPPED` files are named.

So the question is **should this file have had a root element**, and the only thing that answers
it is the name. `index.md`, `what-next.md`, `PROJECT.md` and every `.md` directly under a
`features/` directory are names this toolchain writes; one of those carrying no root **escalates**,
because it should be an artefact and is not. Anything else carrying no root is prose somebody put
beside the corpus, and stays `SKIPPED` — still named, because a count cannot be read.

**This does not reopen *"deciding by filename"*.** That rule governs which artefact a file IS, and
it stands: R1 reaches a feature file by its ROOT ELEMENT and never by its name, or `/prd --resume`
breaks. The name is consulted for a different question, asked only once the root is known absent,
and nothing downstream reads the answer. The two failure modes also settle the default between
them: a file wrongly called the toolchain's is one line an operator dismisses, and a file wrongly
called prose is a corpus migrated to the current schema around a markdown heading, with nothing
that ever says so.

| Exit | Means |
|---|---|
| **0** | every file reached the target, or reached `PARTIAL` and the half the script may do is done |
| **1** | a postcondition failed, or `--check` found a file short of the target. Nothing partly written survives |
| **2** | escalation — a file matched no precondition, could not be decoded as UTF-8, is **missing something only a person can write** (R7, R8), or is a file the toolchain writes that carries no artefact root at all. Nothing was written for those, and each is named |
| **3** | usage error |

| Per-file verdict | Means |
|---|---|
| `MIGRATED` | every step reached its postcondition |
| `PARTIAL` | the mechanical half is done and judgements are outstanding — `--check` will refuse |
| `ALREADY` | the file is at or beyond the target |
| `UNCHANGED` | the target's steps do not touch this kind of artefact |
| `ESCALATE` | the file matched no precondition, could not be decoded, or is missing what only a person can write. **Nothing was written** |
| `SKIPPED` | the file carries no artefact root element **and is not one the toolchain writes**. It is not an artefact, it stops nothing, and it is listed rather than dropped |

**`--check` writes nothing** and asserts the postconditions against files as they are. It is what
makes *"the migration ran"* a different claim from *"the migration finished"*, and it is what the
regression suite calls. A `PARTIAL` tree fails it, deliberately.

**`--detect` reports where each file already is**, and escalates rather than guessing when the
answer is not one of the known versions. It is how an artefact selects the right migration rather
than the newest one.

**It also counts its own listing**, in a totals line naming the path scanned, the number of
artefacts found per schema, and how many escalated or were not artefacts. That is not a
convenience: the skill's Phase 1 requires those totals to be stated before anything is migrated,
and for four phases nothing produced them, so the only way to obey the instruction was to count
the rows by eye. A sixty-six line listing was duly reported as sixty. An element with no producer
is the defect this plan spends most of its items removing, and it had one in its own skill.

The totals are **derived from the rows that were printed**, never counted a second way. A summary
that can disagree with the listing beneath it is the same defect one layer down, and harder to
see, because a printed number reads as a counted one.

**Item 24's stamp does not replace this, and the earlier version of this paragraph said it would.**
`<toolchain-version>` records what *produced* a file; the migration needs to know what *shape* the
file is in, and those are different questions — a 2.0.1 toolchain writes schema-4 and schema-5
artefacts alike. The shape is also self-correcting where a stamp is not: a hand-edited file has the
shape it has, whatever the stamp still claims. So detection stays keyed on the shape, and the stamp
is what `list-prds.py` reports before a resume.

**What the migration will not silently normalise.** A file keeps the line endings it arrived
with, and a file that is not valid UTF-8 is escalated rather than decoded with replacement
characters. Neither is a rule about the schema, and both were once done quietly: the first turns
every per-file diff into a whole-file one, which costs nothing a postcondition can see and
everything the review depends on, and the second is the only failure here that destroys content
in a run that reports success.

**Re-running is safe and is expected.** A file already in the target schema is reported `ALREADY`
and left untouched, which is the same answer whether it was migrated a second ago or a release
ago — because the marker is the shape.
