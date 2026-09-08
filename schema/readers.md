# Readers — the elements nothing consumes, and why

[`core.md`](core.md) defines the shared elements and [`checks.md`](checks.md) names the script
that decides each assertion. This file is the third side of the same rule, and the one the plan
calls its closing argument: **every element has a named reader, and every reader a named
producer.**

It holds only the **exceptions**. A reader is not declared here — it is *found*, by
[`check-readers.py`](scripts/check-readers.py), which looks for the element in every script,
skill, command and agent. A declared reader is a claim; a found one is a measurement, and the
difference is the whole point. What cannot be found has to be written down here, with a verdict
and a reason.

```xml
<readers schema="schema-6"/>
```

---

## Why this file is the exception list and not the registry

The obvious design is one row per element naming its reader: 128 rows, hand-maintained. It would
be wrong within a month, and every row would be a claim rather than an observation — which is the
failure this rule exists to catch, rebuilt as a maintenance chore.

So the script measures, and this file records only what the measurement cannot explain. On the
current corpus that is **ten of 128 elements**, all of them prose no machine should read.

**There are no `open` rows left, and that is recent.** Three CRD elements sat here as
*a producer with no consumer* from item 23's audit until group 8b: `<project-ref>` — `Required`
in every CRD and read by nothing — with `<prd-ref>` and `<feature-ref>`. They now resolve, in
`check-references.py`, under the rule item 39 already applied to the PRD path: **a reference that
names something must resolve to it, or be reported by name.** The verdict stays defined below,
because a schema that grows an element faster than it grows a consumer will need it again.

## The three verdicts

| Verdict | Means | Fails the check? |
|---|---|---|
| `unread by design` | prose a human reads. Structure would be cost with no consumer | no |
| `externally maintained` | produced and consumed outside the toolchain | no |
| `open` | a producer with no consumer, and nobody has decided what to do | **no — it is listed** |

**`open` is a legitimate verdict**, exactly as it is in [`parity.md`](parity.md). An element
nobody has examined is a fact about this project; the defect this file exists to prevent is one
nobody has *written down*. The suite lists the open rows rather than refusing them, and `--strict`
is there for anyone who wants the stricter reading.

**What is not a verdict is silence.** An element with no reader and no row fails the check, which
is the only rule here with teeth and the reason the file is worth having.

---

## The exceptions

| Element | Verdict | Why |
|---|---|---|
| `overview` | unread by design | The PRD's narrative wrapper. Its children are the story a person reads before any of the structure below it |
| `problem` | unread by design | Prose. What a machine needs from it — scope, criteria, priority — is carried by elements that have readers |
| `value-proposition` | unread by design | Prose, and deliberately not a field. A value proposition compressed into something parseable stops being one |
| `competitive-analysis` | unread by design | Optional, and for stakeholders rather than for the toolchain. `/prd` offers it and nothing downstream wants it |
| `non-functional` | unread by design | Prose. Its machine-readable counterpart is item 35's `<architecturally-significant>`, which is a declared judgement with two readers |
| `integrations` | unread by design | Brownfield prose. `PROJECT.md`'s registries are what a consumer looks things up in |
| `migration-notes` | unread by design | Notes for the person doing the migration. `schema/migration.md` is what the toolchain executes |
| `mitigation` | unread by design | Inside `<risk>`. The risk is recorded for a human to act on; a mitigation nobody wrote down is the defect, not one nothing parses |
| `created` | unread by design | A date, for a person. Provenance the toolchain acts on is `<toolchain-version>` (item 24), which has a producer and a reader |
| `change-request` | unread by design | A wrapper: `<summary>` and `<motivation>` carry the content, and `<motivation>` is named by the parity table as the CRD's counterpart to `<user-story>` |

---

## What the check cannot see, stated because a validator that passes over a class of input in silence is worse than one that says so

**It keys on the element NAME, not on the pair of artefact and name.** `<summary>` appears in
`index.md`, in `what-next.md` and in a CRD; a script reading any one of them credits all three.
Two elements sharing a name therefore share a verdict, and the three `open` rows this file
carried until group 8b were triaged by hand for exactly that reason. Keying on the pair would be more precise and would
produce mostly false results, because the reader search is textual and a script naming
`<summary>` does not say whose.

**An instruction reader is weaker evidence than a script reader**, and the summary line reports
the two separately for that reason. A skill naming an element is a model being told to read it,
which is real consumption and is how this repository's own audit was done — but it is prose, and
prose about a mechanism outlives the mechanism.

**The reverse direction is a report, not a rule.** *Every element a component reads must have a
named producer* is the other half of item 23, and run naively it produces **32 candidates of
which 29 are usage-string placeholders**: an element name and a CLI argument are the same token,
so `check-coverage.py <prd-dir> <tasks-dir>` reads as two undefined elements.

Three filters take it to **seven**, and they are stated rather than tuned: docstrings are dropped
(that is where usage lives), shell scripts are skipped entirely (a shell script parses no XML),
and a name the same file declares as an argument is an argument. What survives on this corpus is
three **retired spellings a migration must still recognise** — `<affected-apis>`, `<phases>` and
`<tbd-items>`, correctly read and correctly undefined — three placeholders in comments, and one
element that is neither.

**That seventh is `<requirement-level>`, and it is undefined here for a reason worth stating.**
It is live, not retired: item 16 puts it on a task and `write-state.py` reads it. No *schema*
document defines it because a **task is not a versioned artefact** — `SCHEMAS.json` records that
decision under `_items_16_17`, and `migrate.py` recognises five roots of which a task is none.
So the element is defined in [`task-format-spec.md`](../skills/breakdown/references/task-format-spec.md),
which this script does not scan, and the report is right to name it and right not to fail on it.
The count above is asserted against the script's own output rather than written down, because a
figure in prose is exactly what went stale here once already.

It stays a report because **a filter tuned against one corpus is a heuristic rather than a rule**,
and a heuristic that can fail a build has been promoted behind everyone's back. The same argument
as `check-references.py`'s significance screen, reached independently.

## Who cites this file

| Document | Cites it for |
|---|---|
| [`checks.md`](checks.md) | the assertion, and the script that owns it |
| [`core.md`](core.md) | the rule an element in the core is added under |
