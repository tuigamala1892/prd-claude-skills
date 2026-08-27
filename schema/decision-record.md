# The decision record

**Adopted as-is from a project that already had nineteen of them and a settled house style, not
designed here.** That matters: the conventions below are load-bearing because they were already
regular in a real corpus, so the checks read a convention that exists rather than asking for a
migration. `**Status:**` and `**Date:**` were already regular bolded fields; links to features
and to other records were already ordinary markdown.

**Where records live is the project's choice.** The plugin ships this as a default reference;
`architecture.md`'s `<rules>` may point at a project's own template. Shipping ours as
unoverridable would be a sixth vendored opinion — and this one came from a project rather than
from the plugin, which rather makes the point.

---

## When you are writing one, and when you are not

| Kind | Test | Home | Enforced? |
|---|---|---|---|
| **Decision** | has rejected alternatives to record | a record, this template | no — it is a record |
| **Principle** | a rule, with no alternatives weighed | `<principles>` in `architecture.md` | no — it is guidance |
| **Constraint** | the toolchain must obey it | `<rules>` in `architecture.md` | **yes — exit code** |
| **Advisory** | stated, checked, not decidable by comparison | `<rule kind="judgement">` | reports, never refuses |

**No rejected alternatives means it is not a decision record — it is a principle.** That is the
whole test, and it is the one most often failed: a record with a single option and a paragraph of
justification is a principle that has been given the wrong home, and it will be read as though
something was weighed.

---

## The template

```markdown
# ADR-{{NNN}}: {{a claim, not a topic}}

**Status:** Accepted
**Date:** {{YYYY-MM-DD}}
**Drives:** [{{Feature Name}}](../../prd/{{slug}}/features/{{feature-slug}}.md), [{{Another}}](...)

## Context

{{What exists today, with links.}}

**{{One bolded lead-in per pressure}}.** {{What has accumulated against it.}}

## The Problem
{{Optional. Where the context does not make the problem obvious on its own.}}

## Options Considered

### {{Option A}}
**Pros:** {{where they exist}}
**Cons:** {{...}}
**Verdict:** {{rejected, and on what grounds}}

### {{Option B}}
...

## Decision

**{{A single bolded sentence.}}** {{Then the mechanics: what is actually being changed.}}

## Scope Boundary
{{Optional. What this decision deliberately does not settle.}}

## Rationale

{{Prose. Not a summary of the Cons -- why this option, in terms someone who disagreed would
recognise.}}

## Consequences

{{What changes in index.md or in a feature file, concretely enough to act on.}}
```

**Titles state a claim, not a topic.** *"ADR-007: Contexts communicate by event, never by call"*
tells a reader what was decided; *"ADR-007: Inter-context communication"* makes them open the
file to find out.

---

## The three conventions that come with it

**`Status: Accepted` on every current record, and supersession amends rather than rewrites.** A
superseded record keeps its decision exactly as written and gains a status line naming its
successor. This is the same principle as a `superseded` feature keeping its file — the record of
what was decided, and why, outlives the decision itself.

**Resolved questions are annotated in place, never deleted.** A heading naming what resolved them
and when. An `OQ-NNN` may have been cited from a commit or a review, and deleting the entry turns
those citations into nothing. This is also the answer to a question item 29 leaves open, and it
is the same rule `<gaps>` follows.

**`**Drives:**` is a declared field, not an inference from the Context links.** Those links are
load-bearing by accident: they are there because the author happened to reference the feature, and
they will drift. A declared field is the difference between a check that holds and one that
erodes — and it is what lets `check-references.py` assert something real about item 35's
architecturally-significant features.

Each link resolves to a feature file by its slug, which is [core §1](core.md#1-identity)'s
identifier — stable, global, and a filename. That is why a rename is a script with
postconditions rather than an edit: it has to carry every `**Drives:**` link pointing at the
feature along with the five other places the slug appears.

---

## Off by default

```xml
<design-track enabled="false" adr-dir="../../architecture/decisions"/>
```

The design track is opt-in, and `adr-dir` points **outside** the PRD deliberately. Decision
records outlive the PRD that prompted them, which is why a project keeps them in a project-wide
directory and why `architecture.md` cites them by pointer rather than absorbing them.

With `enabled="false"` the gate between `/breakdown` and `/execute` prints its report and
returns. With it enabled, it asks for confirmation. **The report is the valuable half** — the
confirmation only matters if somebody is there, and the assertions are worth running either way.

---

## What reads this

| Reader | Reads |
|---|---|
| [`check-references.py`](../skills/breakdown/scripts/check-references.py) | `**Status:**` for supersession; `**Drives:**` links resolve; a significant feature no record drives |
| `/prd` Phase 4 | where a rename or a scope change wants a record rather than a silent edit |
| item 38's gate | every architecturally-significant feature is named, or explicitly needs no decision |

The first is shipped and runs today. The third is not built yet, and saying so here is cheaper
than letting a reader assume it is.
