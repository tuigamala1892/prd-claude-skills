# Schema core — the elements both paths share

`/prd` and `/crd` produce different documents about different things. They do not produce
different *criteria*, different *statuses*, or different *identifiers* — but until this file
existed they each wrote their own definition of all three, and a definition written twice is a
definition that will disagree with itself.

**This file is the single definition. Every other schema reference cites it and none restates
it.** Where a format document needs to show a shared element it shows an *example*; the legal
attributes, the legal values and the meaning live here.

```xml
<schema-core version="schema-2"/>
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
| priority vocabularies | [4](#4-priority) | `/prd`, `/crd` | `/breakdown`'s `--priority` |
| `<scope>`, `<confidence>` | [5](#5-scope-and-confidence) | `crd-impact-analysis` | *(none yet — item 49)* |

The empty cell in the last row is stated rather than hidden. `<scope>` and `<confidence>` are
required fields on the CRD path with no consumer anywhere in the toolchain; they are in this
file because item 49 gives them one on **both** paths, and putting them here first is what stops
the PRD path inventing a second pair.

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
  <criterion id="1">
    <given>{{Initial context}}</given>
    <when>{{Action taken}}</when>
    <then>{{Expected outcome}}</then>
  </criterion>
</acceptance-criteria>
```

| Part | Required | Holds |
|---|---|---|
| `id` | Yes | Integer, unique within `<acceptance-criteria>` |
| `<given>` | Yes | The state the system is in before the action |
| `<when>` | Yes | One action, by one actor |
| `<then>` | Yes | One observable outcome |

**One criterion, one behaviour.** A `<then>` joined by *and* is two criteria that have not been
separated yet, and it reaches `/breakdown` as one test requirement covering two things.

**Identical on both paths.** A PRD feature file and a CRD carry the same element with the same
meaning, which is what lets `breakdown-generate-tasks` read either without a branch.

> **This element is scheduled for replacement.** Item 33 adopts EARS — a single sentence with
> `pattern` and `priority` attributes — in place of the Given/When/Then triple. It is recorded
> here rather than in a footnote because *this file* is where that change lands: one definition,
> one migration, both paths at once. That is the whole reason the core is extracted before the
> items that rewrite it.

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

**MoSCoW — `must-have`, `should-have`, `could-have`, `wont-have`.** One vocabulary, two homes:

| Where | On | Selects |
|---|---|---|
| PRD | `priority=` on the **`index.md` feature entry** | which features are in scope |
| CRD | `priority=` on each `<requirement>` | which requirements are in scope |

**On the PRD path the index owns it, and the feature file does not carry it.** Priority is a
judgement *across* features — a ranking has no meaning inside the thing being ranked — so it
lives where the comparison is made. A copy in the feature file is the duplication item 1 removes.

`/breakdown --priority <threshold>` filters on this, and `wont-have` is skipped unconditionally.

> **A second vocabulary arrives at items 34 and 47**: `P0|P1|P2` on individual criteria, on both
> paths. It is deliberately not MoSCoW, so that no report line or flag is ambiguous about which
> level it means. When it lands, the CRD's requirement-level MoSCoW migrates to it, and MoSCoW
> survives only where it is a judgement across whole items.

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

Both are required on the CRD path today. **Neither has a reader**, which is recorded here as a
defect rather than as a schema.

---

## Who cites this file

| Document | Cites it for |
|---|---|
| [`prd-format.md`](prd-format.md) | identity, criteria, status, priority |
| [`crd-format.md`](../skills/crd/references/crd-format.md) | identity, criteria, status, priority, scope, confidence |
| [`project-format.md`](../skills/crd/references/project-format.md) | status |
| [`task-format-spec.md`](../skills/breakdown/references/task-format-spec.md) | identity, criteria |
| [`breakdown/SKILL.md`](../skills/breakdown/SKILL.md) | criteria, status, priority — it is the reader both paths share |
| [`commands/prd.md`](../commands/prd.md) | via `prd-format.md` |
| [`commands/crd.md`](../commands/crd.md) | via `crd-format.md` |
| [`crd/SKILL.md`](../skills/crd/SKILL.md) | via `crd-format.md` |

**Adding an element here means adding a row above.** An element in the core that nothing cites
is not shared — it is stored.
