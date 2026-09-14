# Schema core — the elements both paths share

`/prd` and `/crd` produce different documents about different things. They do not produce
different *criteria*, different *statuses*, or different *identifiers* — but until this file
existed they each wrote their own definition of all three, and a definition written twice is a
definition that will disagree with itself.

**This file is the single definition. Every other schema reference cites it and none restates
it.** Where a format document needs to show a shared element it shows an *example*; the legal
attributes, the legal values and the meaning live here.

```xml
<schema-core version="schema-6"/>
```

The version above is the artefact schema the toolchain currently writes. It is the same string
`tests/fixture/prd/SCHEMAS.json` names as `current`, and the two are checked against each other —
a core that has moved on from its fixtures is a migration nobody has rehearsed.

---

## Why a core, and what it is not

Three producers restated the criterion shape before this file existed: `commands/prd.md`'s
feature template, `commands/crd.md`'s Phase 6 template, and
[`crd-format.md`](../skills/crd/references/crd-format.md). They had already drifted. The CRD
format marks `<scope>` and `<confidence>` **required**; the command that writes CRDs emits
neither. Nothing was wrong with either author — there were two documents, and only one of them
got the change.

**Its counterpart is [`parity.md`](parity.md)**, which records every capability one path has and
the other does not, with a probe for each. This file is what the two paths share; that one is the
distance between them, and neither is readable without the other.

**It is not a container for everything schema-shaped.** An element belongs here when **both
paths use it**. A PRD's `<user-story>` and a CRD's `<impact-analysis>` are each one path's own,
and moving them here would turn a shared definition into a directory.

**Every element here names its readers.** An element with no reader is the defect this plan was
written to remove, and the surest way to grow one is to define it somewhere nobody has to look.

---

## The shared elements

| Element | Section | Written by | Read by |
|---|---|---|---|
| `<slug>`, `id=` | [1](#1-identity) | `/prd`, `/crd` | `rename-feature.py`, `list-prds.py`, `check-references.py`, `/breakdown` |
| `<acceptance-criteria>` / `<criterion>` | [2](#2-acceptance-criteria) | `/prd`, `/crd` | `breakdown-generate-tasks`, as `<test-requirements>` |
| status vocabularies | [3](#3-status) | `/prd`, `/crd`, `crd-investigate` | `list-prds.py`, `/breakdown`, `/crd` |
| priority vocabularies | [4](#4-priority) | `/prd`, `/crd` | `/breakdown`'s `--priority` and `--requirement-level` |
| `<scope>`, `<confidence>` | [5](#5-scope-and-confidence) | `crd-impact-analysis`, `breakdown-analyze-prd` | `check-scope.py`, `/breakdown`'s report |
| `<gaps>` / `<gap>` | [6](#6-gaps--what-a-document-knows-it-is-missing) | `/prd`, `/crd` | `breakdown-analyze-prd`, `breakdown-review-tasks`, `/breakdown`'s report |
| `<architecturally-significant>` | [8](#8-architecturally-significant--a-judgement-declared) | `/prd`, `/crd` | `check-references.py`, `check-gate.py`, `/breakdown`'s report |

That last row was an empty cell until item 49, and it was stated rather than hidden: `<scope>`
and `<confidence>` were required fields on the CRD path with **no consumer anywhere in the
toolchain**. They were put in this file before they had one, which is what stopped the PRD path
inventing a second pair — and item 49 then gave them producers and readers on both paths rather
than only on the one that already declared them.

---

## 1. Identity

Two identifier kinds, and the distinction is load-bearing.

**`<slug>` — stable, global, and a filename.** Lowercase, hyphen-separated, unique within its
document set. A feature slug is its filename under `features/`, its `file=` attribute in
`index.md`, its `ref=` in `what-next.md`, and the target of every inbound link. That is five
places, which is why renaming one is a script with postconditions (`rename-feature.py`) rather
than an edit.

**`id=` — stable, local, and never a filename.** An integer, unique within its parent element,
and *not* reused when a sibling is deleted. Criteria and requirements carry one. Its job is
citation: a commit message, a review comment or a task file naming criterion 3 of a feature must
still mean the same criterion a month later.

**Neither is a version.** A reworded criterion keeps its `id`; a criterion replaced by a
different requirement gets a new one. The test is whether a reader who cited it would now be
misled.

---

## 2. Acceptance criteria

```xml
<acceptance-criteria>
  <criterion id="1" pattern="event-driven" priority="P0">
    When a user submits a link, the system shall store it and return the stored record.
  </criterion>
</acceptance-criteria>
```

**A criterion is one sentence in EARS form.** Not a Given/When/Then triple — that is a *scenario*
format, and a scenario cannot state a requirement, which is why the CRD path needed a second
list to hold requirements at all.

**That second list is gone, and this one holds both.** An EARS criterion *is* a requirement —
*"When the user toggles the theme, the system shall persist the preference"* states an obligation,
not a scenario — so at item 46 the CRD's `<requirements>` was retired and its entries became
criteria here. One list, one id space, on both paths. The question that used to be unanswerable —
*which criteria discharge requirement 3?* — is not answered but dissolved: there is no requirement
3 that is not itself a criterion.

| Part | Required | Holds |
|---|---|---|
| `id` | Yes | Integer, unique within `<acceptance-criteria>`; core §1 |
| `pattern` | Yes for `defined` | One of the six EARS patterns, below |
| `priority` | Yes | `P0`, `P1` or `P2`; core §4 |
| body | Yes | One sentence, containing the word **shall** |
| `derived-from` | Migration only | Where this criterion came from, until sign-off: a criterion id, or `requirement-N` where a CRD `<requirement>` became one at item 46 |

### The six patterns

| `pattern` | Shape | Reads |
|---|---|---|
| `ubiquitous` | The system shall … | always true, no trigger |
| `state-driven` | While ‹state›, the system shall … | true for as long as a state holds |
| `event-driven` | When ‹trigger›, the system shall … | in response to something happening |
| `optional-feature` | Where ‹feature is included›, the system shall … | true only in some configurations |
| `unwanted-behaviour` | If ‹condition›, then the system shall … | the error and abuse cases |
| `complex` | a combination of the above | last resort, and a smell |

**`pattern` is what makes "covers the edge cases" mechanical.** Counting patterns across a
feature answers a question that no keyword heuristic could: a feature whose criteria are entirely
`event-driven` has stated what happens when things go right and nothing else. That single fact is
the signal item 3's derivation was missing, and it is the reason the taxonomy is an attribute
rather than a report.

**`pattern` is assigned by a person, never derived.** A pattern inferred by the same heuristics
it exists to replace is circular. This is why a migration must not assign it — see
[`migration.md`](migration.md). An agent may **propose** one; a person who accepts the proposal
has assigned it, exactly as an author accepts a drafted criterion in `/prd`. What no agent does is
write it unaccepted.

**A migrated criterion passes through three states, and each one is visible in its attributes:**

| Attributes | State | Reached by |
|---|---|---|
| `derived-from`, no `pattern` | the migration's sentence, unread | `/migrate` |
| `derived-from` and `pattern` | classified, not yet signed off | a person accepting or assigning a `pattern` in `/prd --resume` or `/crd --resume` |
| `pattern`, no `derived-from` | signed off | a PRD feature: recording its `<review>`. A CRD: `sign-off.py`, after `/crd --resume`'s review |

**A CRD has no `<review>`, so it signs off by script.** `schema/scripts/sign-off.py` is the one
implementation of the edit, and `check-definition.py` imports it. It refuses a `complete` or
`abandoned` CRD, whose `derived-from` stays permanently as a record of the past.

**The review is the sign-off.** `derived-from` outlives the pattern on purpose. It is how a
reviewer checks the sentence against where it came from, so it has to still be there when they
look. `check-definition.py --record-review` removes it from every criterion carrying a `pattern`,
in the same write that records the review. A criterion with no `pattern` keeps `derived-from`
through a review, because nobody has classified it yet. A `tbd` feature is never reviewed, so its
criteria keep `derived-from` until it is promoted. That is the true state of them, not a gap.

**One criterion, one behaviour.** A body joined by *and* is two criteria that have not been
separated yet, and it reaches `/breakdown` as one test requirement covering two things.

**Identical on both paths.** A PRD feature file and a CRD carry the same element with the same
meaning, which is what lets `breakdown-generate-tasks` read either without a branch.

### Reading a criterion written before EARS

**Accepted on read; never written** — the same policy as §3. A `<criterion>` containing
`<given>`, `<when>` and `<then>` is a schema-2 criterion: read the three parts as one requirement
and treat it as having no `pattern`.

**A criterion with no `pattern` is not an error, and this is deliberate.** It is precisely how a
feature that has been migrated mechanically but not yet re-read is distinguishable from one that
has — see `migration.md`'s `PARTIAL` state. A `defined` feature carrying pattern-less criteria is
a contradiction; a `tbd` one is just unfinished.

---

## 3. Status

**Four things used to be spelled `status`, and no two of them meant the same thing.** Three now
have names of their own. The fourth kept the word, which is the point of the rename rather than
an exception to it: after item 45, `<status>` means exactly one thing.

| Tag | Lives in | Records | Values |
|---|---|---|---|
| `<status>` | `index.md`, `what-next.md` | how far the **interview** got | `in-progress`, `complete` |
| `<definition>` | a PRD feature file's `<meta>` | how completely the feature is **defined** | `tbd`, `in-progress`, `defined` |
| `<workflow>` | a CRD's `<meta>` | where the change is in the **process** | `draft`, `ready`, `in-progress`, `complete`, `abandoned` |
| `built=` | `PROJECT.md`'s `<feature>` | how much **exists in code** | `complete`, `partial`, `planned` |

Three of the four still carry `in-progress` or `complete`, with three different meanings — which
is why the *tags* had to differ. A shared value set across distinct tags is ordinary; a shared
tag across distinct value sets is a script reading the right name from the wrong file and getting
a plausible answer.

**A fifth is not in the table, deliberately.** `what-next.md`'s `<step status="done">` records
whether one recorded step has happened. It is PRD-only, so it is defined in
[`prd-format.md`](prd-format.md) rather than here — but it is named, because *"four things are
called status"* would have been the wrong count and this file is where someone comes to get that
count right. It is also the reason the rename stopped at three: `<step>`'s attribute cannot
collide with a document's element.

**Definition completeness is not build progress.** A feature whose criteria are fully written is
`<definition>defined` whether or not a line of it exists; a feature that is half-built is still
`defined`. The second row records what the *document* says, and the fourth records what the
*code* says. Naming them differently is what stops one being read for the other.

**Why the first row keeps the word.** It is the only one of the four with a shipped reader —
`list-prds.py` takes the first `<status>` in `index.md` and in `what-next.md` and reports
`DISAGREE` when they differ. It is also the tag that makes `--resume` work at all. Renaming it
would have cost a migration and a behaviour change to buy nothing, because once its three
namesakes are gone it is no longer ambiguous.

**`<definition>` extends to `excluded` and `superseded` at items 1 and 4.** Those values exist in
authored PRDs today and not in the template; adding them is a change to the *value set*, which is
a different act from renaming the tag, and doing both at once would make one migration
indistinguishable from the other in a diff.

### Reading an artefact written before the rename

**Accepted on read; never written.** A reader that finds `<status>` where it expects
`<definition>`, `<workflow>` or `built=` treats it as that element and carries on. A producer
writes only the new name.

This is the rule item 57 already set for `<affected-apis>`, stated once here so that three
renames share one policy rather than inventing three. The reason is the same in both cases: a
document is often authored in one place and read in another, and a hard cutover strands whatever
is in flight. Item 41's migration rewrites them; until it has run everywhere, refusing would
break artefacts that are not wrong, only old.

**One exception, and it is the first row.** `<status>` in `index.md` and `what-next.md` was never
renamed, so there is nothing to accept — a `<definition>` at document level is not an old
artefact, it is a mistake.

---

## 4. Priority

**Two levels, in two vocabularies, deliberately.** No flag, report line or conversation should
ever be ambiguous about which one it means.

| Level | Where | Vocabulary | Selects |
|---|---|---|---|
| Whole item | PRD: `priority=` on the `index.md` feature entry · CRD: `<priority>` in `<meta>` | MoSCoW: `must-have` · `should-have` · `could-have` · `wont-have` | which features, or which change requests, are in scope |
| Requirement | `priority=` on each `<criterion>`, both paths | `P0` · `P1` · `P2` | which criteria within them are built |

**On the PRD path the index owns the feature level, and the feature file does not carry a copy.**
Priority is a judgement *across* features — a ranking has no meaning inside the thing being
ranked — so it lives where the comparison is made.

**On the CRD path the document carries it, and that is the same rule rather than an exception.**
A change request is the planning unit *and* the thing being planned, and there is no index for it
to live in — `/crd --list` is the survey view, derived by scanning. §4.1's actual test is
*"anything finer than the planning unit belongs where the thing itself is"*, and here the two
coincide.

`/breakdown --priority <threshold>` filters the first; `--requirement-level <P0|P1|P2>` filters
the second, and is applied **after** it. `wont-have` is skipped unconditionally.

### Why the second level exists

A must-have feature that depends on a could-have one used to make `--priority must-have` an
**open** set: closing it pulled in the whole dependency, tier boundary and all. Criterion-level
priority changes what closure costs — the must-have pulls in *that feature's `P0` criteria*, not
the entire feature. "What does this filter actually build" becomes a computation rather than a
guess.

### The default is `P1`, and it is written down rather than implied

An unassigned criterion is `P1`. **The migration writes it in rather than leaving it to the
default**, which looks like noise and is not: *unassigned* and *deliberately P1* are
indistinguishable when the attribute is absent, so a partly-assigned corpus cannot be told from a
finished one. See `migration.md` — a transformation whose completion is invisible in the shape
cannot be resumed.

A corpus where everything is `P0` says nothing, and neither does one where nothing is set.

### What is still MoSCoW, and where

MoSCoW survives **only where the judgement is across whole items**. On the PRD path that is the
feature, in the index; on the CRD path it is the document, in `<meta>`. Below that level there is
one vocabulary, `P0|P1|P2`, on both paths.

**Landed at item 47, and it removed a vocabulary rather than adding one.** The CRD used to carry
requirement-level priority in MoSCoW, so a toolchain reading both paths had two vocabularies for
one concept — exactly what item 29 refused when it retired `<needs-clarification>` rather than run
it beside `<gaps>`. Existing CRD requirement priorities migrate under item 41, one to one:

| Was | Becomes |
|---|---|
| `must-have` | `P0` |
| `should-have` | `P1` |
| `could-have` | `P2` |
| `wont-have` | **nothing — the migration stops and names the file** |

**The fourth row is the interesting one, and it is an escalation rather than a mapping.**
`P0|P1|P2` has no *"we are not building this"* value, deliberately: that judgement belongs to the
whole item, and on this path the whole item is the document. So a `wont-have` requirement has no
honest target. Sending it to `P2` would make it buildable by default — `--requirement-level`
defaults to `P2` — and dropping it would delete something a person wrote down. Both are decisions
about the change, not about its format, so the migration refuses the file and says why. See
[`migration.md`](migration.md).

The consequence worth naming: **`/breakdown --priority <threshold>` now means something on the CRD
path**, where it previously had nothing to read. A could-have change request can be declined.

---

## 5. Scope and confidence

```xml
<scope>small</scope>           <!-- small: 1-3 files | medium: 4-8 | large: 9+ -->
<confidence>high</confidence>  <!-- high | medium | low -->
```

**`<scope>` is a prediction, and a prediction is only useful beside an observation.** It is a
cross-check, never a routing input: a declared `small` against a generated 14 tasks flags a
change that was under-analysed or a generator that ran away. Nothing selects a layer set from it
— that is derived from content instead.

**`<confidence>` grades a whole analysis**, not a specific unknown. Ambiguous matches and
incomplete context lower it. A specific unknown is a different thing and gets its own element at
item 29.

### Who produces each, on each path (item 49)

| | Predicted by | Observed by | Compared by |
|---|---|---|---|
| CRD | `crd-impact-analysis`, into the CRD | `build-manifest.py`, into `manifest.json` | `check-scope.py` |
| PRD | `breakdown-analyze-prd`, **per feature**, into `analysis.json` | `build-manifest.py` | `check-scope.py`, per feature |

**Nothing is written back to the PRD.** The prediction lives in `analysis.json` and the
observation in `manifest.json` — an earlier design derived `<scope>` from the task count *after*
breakdown, which is not a prediction to disagree with, and which would have had `/breakdown`
mutating the PRD, something nothing else in this toolchain does and §4.1 has no rule for.

**The comparison fires on gross disagreement only, and that is the whole tolerance.** A size
estimate from a model is soft; it is tolerable precisely *because* it routes nothing. `small`
against `medium` says nothing worth a line of output. `small` against `large` says one of the two
is wrong, which is the only case worth an operator's attention.

**The bands are counted in files, and the observation is counted in tasks.** That conversion is
why the comparison is band-to-band rather than number-to-number, and why only non-adjacent bands
disagree. A task creates at most three files, so the two units do not line up and pretending they
do would produce a check that fires constantly and is therefore ignored.

---

## 6. Gaps — what a document knows it is missing

```xml
<gaps>
  <gap id="3" kind="specification" raised="2026-08-18">
  Retention period for archived links is unspecified.
  </gap>
</gaps>
```

| Part | Required | Holds |
|---|---|---|
| `id` | Yes | Integer, unique within `<gaps>`; core §1 — citable from a commit or a review |
| `kind` | Yes | One of the five below |
| `raised` | Yes | `YYYY-MM-DD`. Without it an open item and a stale one look identical |
| body | Yes | Markdown, including links, exactly as elsewhere |

**Uncertainty is recorded, not banned.** A toolchain that forbids `TBD` outright makes invention
the compliant answer — the author writes something plausible because writing nothing fails
review. A marked gap **passes review and blocks execution**; unmarked vagueness keeps failing
review exactly as it did.

### The five kinds, and what each blocks

| `kind` | Blocks `defined`? | Blocks execution? |
|---|---|---|
| `specification` | **yes** — it bars `defined` outright | yes |
| `dependency` | no | yes, until the dependency is named and available |
| `decision` | no | yes — an undecided question built anyway is an invented one |
| `ownership` | no | **warn** — the boundary may move under the task |
| `evidence` | no | **warn** |

**Three of the five warn rather than stop**, and that is the answer to the objection that killed
an earlier design: an overnight run should be halted by a genuine unknown, not by every open
item. A boolean `blocking=` could not make that distinction; `kind` can, and it also says *what
sort of not-knowing this is*, which a boolean never could.

**A `defined` artefact must not carry a `specification` gap.** That is a contradiction — claiming
to be fully specified while declaring the specification incomplete — and it is the one rule here
a script can enforce without judgement. It runs one way only: the absence of a gap proves
nothing, so nothing is ever promoted *to* `defined` by this rule.

**The same rule, one word different, is what `<workflow>` was missing.** A CRD marked `ready`
must not carry a `specification` gap — *ready for implementation* and *the specification is
incomplete* cannot both be true. Before item 48 the CRD had no `<gaps>` at all, so `draft` versus
`ready` rested entirely on the author's say-so; it now has the same one-way mechanical test
`<definition>` has, and for the same reason. §3's second row and third row are checked by one
rule with two names for its subject.

**One element, not two.** `<confidence>` (§5) grades a whole analysis; a `<gap>` marks one
specific unresolved point. They feed the same gate and the same report line, and neither is a
substitute for the other — but a second element meaning *"something here is unknown"* would be
the drift this file exists to prevent.

### Where a gap is resolved

**In the interview, wherever possible.** `/prd`'s phases and `/crd`'s change capture are better
resolution mechanisms than anything downstream, because a human is answering. A gap is for what
the interview *failed* to resolve — never a licence to stop asking.

**A deferred criterion is a gap, not an absence.** This is the CRD path's most common case and the
reason item 48 exists: *"we'll define that later"* used to leave nothing behind at all, so a CRD
that had deferred half its behaviour was indistinguishable from one that had none. It is now a
`<gap kind="specification">`, which bars `ready` and blocks execution.

**A resolved gap is annotated, not deleted.** The `id` may already have been cited from a commit
message or a review, and a deleted gap turns those citations into nothing. Say what resolved it
and when, in the body, and leave it in place.
---

## 7. `<review>` — the half of the `defined` gate that is not mechanical

**Item 40's bar is two halves: the mechanical tests pass, *and* a review has been recorded.**
`check-definition.py` is the whole of the first half. Until schema-6 the second had nowhere to
live, so a feature labelled `defined` and a feature labelled `defined` *after somebody read it*
were the same file — and the gate silently had one working half.

```xml
<meta>
  <slug>save-link</slug>
  <definition>defined</definition>
  <review by="lee" at="2026-09-07" sha="8f21c4a90b3e"/>
</meta>
```

| Attribute | |
|---|---|
| `by` | who reviewed it. A name, not a role — a review is somebody's |
| `at` | the date they did, `YYYY-MM-DD` |
| `sha` | the first 12 hex of sha256 over **this file with the `<review>` element removed** |

**`sha` is what makes it a record rather than a claim.** Without it, a review element says a
review happened once, and the file it describes can be rewritten underneath it — which is the
same defect as a ledger that records adjectives instead of commits. With it, a reader can tell
three states apart:

| | |
|---|---|
| **reviewed** | `sha` matches the file's current content |
| **stale** | `sha` differs — this was reviewed, and then edited |
| **not reviewed** | the element is absent |

**A stale review is reported exactly as an absent one**, and reported rather than refused: §4.2's
principle is that a wrong label usually signals wrong *content*, so a gate that blocks the label
invites relabelling instead of fixing. `--strict` is where it becomes an exit code.

**Any edit invalidates it, including a reflow**, and that is deliberate rather than a limitation.
The alternative is a canonicaliser deciding which edits are cosmetic — which is a judgement, and
judgement is the thing a reviewer was there to supply. Re-recording a review is one command.

**The element is optional in the schema and required by the bar.** A `tbd` or `in-progress`
feature has nothing to review yet, so a schema that required it everywhere would put a false
record on every unfinished file. The obligation belongs to the label, not to the tag.

**Nothing writes it automatically.** `check-definition.py --record-review` computes the hash and
writes the element when a person asks for it; no migration produces one, and
[`migration.md`](migration.md) records that as the reason the schema-5 → schema-6 step reports
`PARTIAL` on every `defined` feature it meets.

---

## 8. `<architecturally-significant>` — a judgement, declared

```xml
<meta>
  <slug>archive-links</slug>
  <architecturally-significant
      because="quality-attribute|risk|first-of-a-kind|cross-cutting|external-dependency|constraint"
      criteria="3,7"/>
</meta>
```

| Attribute | Required | |
|---|---|---|
| `because` | Yes | Which kind of significance. One of the six above |
| `criteria` | No | The criterion ids that carry it, comma-separated, no spaces |

**It cannot be derived, and that is why it is declared.** Not every non-functional requirement is
architecturally significant and some functional ones are, so no structural property of the file —
not a `<non-functional>` section, not a count, not a pattern — answers the question. A machine
that inferred it would be inventing the judgement a design step exists to act on.

**It exists to make a design step affordable.** Without it a design pass runs across every item in
the document rather than the handful that warrant one, which is the cost that stops anyone running
one at all.

**It sits in `<meta>`** because significance is a property of the item's *nature*, not of its
place in a plan.

### Both paths, and the CRD's was the last to arrive (item 76)

The PRD had this from item 35. The CRD did not, while **`check-references.py` read it and
`check-gate.py` ran that script for a CRD** — a live reader scanning for an element the format
never defined, which is P46's shape and the defect item 68 fixed for `<review>` on the other path.

**A refactor CRD is the document item 35 was written for.** *"Replace the session store"* is
architecturally significant in a way that *"add a column"* is not, and until item 76 a change
request had no way to say which it was.

**It did not need a schema version, and that was measured rather than assumed.** The element is
optional, so no existing CRD becomes invalid; `check-artefacts.py` closes a child set only where
the schema says *exactly these* — `<notes>` — and `<meta>` has never been closed, so a CRD
carrying it validates against schema-6 unchanged. A version would have bought a frozen fixture and
a migration step whose transform is the identity, against `SCHEMAS.json`'s own warning that
maintaining the same project twice is what makes people abandon versioned fixtures.

---

## Who cites this file

| Document | Cites it for |
|---|---|
| [`prd-format.md`](prd-format.md) | identity, criteria, status, priority, significance |
| [`migration.md`](migration.md) | every element it moves between versions |
| [`decision-record.md`](decision-record.md) | identity — a record's `**Drives:**` resolves to a feature |
| [`checks.md`](checks.md) | status, criteria, gaps — it names the script that decides each |
| [`readers.md`](readers.md) | every element it defines, and whether anything reads it |
| [`crd-format.md`](../skills/crd/references/crd-format.md) | identity, criteria, status, priority, scope, confidence, significance |
| [`project-format.md`](../skills/crd/references/project-format.md) | status |
| [`task-format-spec.md`](../skills/breakdown/references/task-format-spec.md) | identity, criteria |
| [`breakdown/SKILL.md`](../skills/breakdown/SKILL.md) | criteria, status, priority — it is the reader both paths share |
| [`commands/prd.md`](../commands/prd.md) | via `prd-format.md` |
| [`commands/crd.md`](../commands/crd.md) | via `crd-format.md` |
| [`crd/SKILL.md`](../skills/crd/SKILL.md) | via `crd-format.md` |

**Adding an element here means adding a row above.** An element in the core that nothing cites
is not shared — it is stored.

**And it means the element needs a reader.** [`readers.md`](readers.md) is where that is
enforced: every element any schema document defines must be named by some script, skill, command
or agent, or appear there with a verdict and a reason. `check-readers.py` runs it, and the rule
is this plan's closing argument — *P2 and P4 were both invisible to a suite that reads the files,
because the failure is an absent consumer rather than a wrong string.*
