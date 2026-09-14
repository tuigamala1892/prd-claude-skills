# PRD artefact format

What `/prd` writes, and what `/breakdown` reads. Shared elements — identity, criteria, status,
priority — are defined in [`core.md`](core.md) and are **cited here, not restated**.

## Where it lands

```
docs/prd/{project-slug}/
  index.md
  what-next.md
  features/
    {feature-slug}.md
{project_root}/architecture.md      # project-wide, only when Phase 4 was discussed
```

The first three belong to one PRD. `architecture.md` does not: it describes the **codebase**, and
`/prd` supports several PRDs in one repository, which cannot hold several layer graphs.

---

## `index.md` — the project, and the feature index

```xml
<prd>
  <meta>
    <name>{{Project Name}}</name>
    <slug>{{project-slug}}</slug>
    <status>in-progress|complete</status>
    <created>{{YYYY-MM-DD}}</created>
    <updated>{{YYYY-MM-DD}}</updated>
  </meta>

  <overview>
    <problem>
    {{Problem statement}}
    </problem>
    <users>
    {{Target users description}}
    </users>
    <value-proposition>
    {{Core value proposition}}
    </value-proposition>
  </overview>

  <tech-stack>
    <type>greenfield|brownfield</type>
    <repo-structure>single|monorepo|multi-repo</repo-structure>
    <selected>
    {{Selected tech stack with components}}
    </selected>
    <rationale>
    {{Why this stack was chosen}}
    </rationale>
    <!-- Include for brownfield projects -->
    <integrations>
    {{Existing systems to integrate with}}
    </integrations>
    <migration-notes>
    {{Data migration and rollout considerations}}
    </migration-notes>
  </tech-stack>

  <features>
    <!-- List all features with links to detail files -->
    <feature priority="must-have" file="features/{{slug}}.md">
      <name>{{Feature Name}}</name>
      <summary>{{One-line summary}}</summary>
    </feature>
    <!-- Repeat for all features -->
  </features>

  <dependencies>
    <dependency>
      <name>{{Dependency Name}}</name>
      <version>{{Version or "any"}}</version>
      <purpose>{{What it's used for}}</purpose>
    </dependency>
    <!-- Repeat for all dependencies -->
  </dependencies>

  <!-- Optional sections - only include if documented -->
  <motivation>
  {{Motivation and use cases if included}}
  </motivation>

  <competitive-analysis>
  {{Competitive analysis if included}}
  </competitive-analysis>

  <non-functional>
  {{Non-functional requirements if included}}
  </non-functional>
</prd>
```

**Three elements here are defined in [`core.md`](core.md), not above.** `<slug>` is core §1.
`<status>` is core §3's first row — the *interview*'s progress, not any feature's. `priority=` on
each `<feature>` entry is core §4, and **this is the only place a PRD records feature priority**:
the feature file does not carry a copy.

## `what-next.md` — what the interview did not finish

**Two lists, and the file needs both.** One is *authoring gaps* — what is not yet specified. The
other is *post-PRD work* — spikes, infrastructure, design. An earlier version had a single
`<next-steps>` holding the second while the template described the first, so neither was
maintained.

```xml
<what-next>
  <meta>
    <prd-slug>{{project-slug}}</prd-slug>
    <status>in-progress|complete</status>       <!-- what /prd --resume looks for -->
    <last-updated>{{YYYY-MM-DD}}</last-updated>
    <next-command>/breakdown</next-command>
    <toolchain-version>{{plugin version}}</toolchain-version>  <!-- stamped, item 24 -->
  </meta>

  <!-- DERIVED. Never hand-maintained. See below. -->
  <authoring-gaps>
    <summary defined="34" in-progress="1" tbd="21" excluded="7" superseded="2"/>
    <gap slug="{{feature-slug}}" id="2" kind="dependency" raised="{{YYYY-MM-DD}}"/>
    <feature slug="{{feature-slug}}" definition="tbd">no criteria written</feature>
  </authoring-gaps>

  <!-- HUMAN-AUTHORED. Post-PRD work. Markdown bodies. -->
  <next-steps>
    <step kind="spike">{{what it must measure, and why that matters}}</step>
    <step kind="infrastructure">{{...}}</step>
    <step kind="data-model">{{...}}</step>
    <step kind="ux">{{...}}</step>
    <step kind="breakdown">{{...}}</step>
    <!-- A step that has already happened records that it did, and when -->
    <step kind="decision" status="done">
    Architecture: default layering taken deliberately, not asked about. {{YYYY-MM-DD}}
    </step>
  </next-steps>

  <risks>
    <risk><description>{{...}}</description><mitigation>{{...}}</mitigation></risk>
  </risks>

  <open-questions href="../../product/open-questions.md"/>   <!-- pointer, or inline -->
  <session-notes>{{context helpful for resuming}}</session-notes>
</what-next>
```

**`<toolchain-version>` is written once and never updated** (item 24). `build-what-next.py`
inserts it when it is absent, from the running plugin's `plugin.json`; `list-prds.py` reads it and
says so before a resume, because a PRD authored against an older schema may want `/migrate` first.
It is **provenance, not a version tracker** — rewriting it on every derivation would make every
what-next.md look stale on every plugin release, and a file that is always stale is a check nobody
runs. `--check` never fails on it, deliberately.

**`<status>` is the same tag `index.md` carries, and that is deliberate** — `list-prds.py` reads
both and reports `DISAGREE` when they differ, because a PRD findable through one file and not the
other is a PRD that gets silently replaced. See core §3.

### `<authoring-gaps>` is derived, and that is what makes it survive

```bash
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/build-what-next.py {prd_dir}
```

**Never hand-maintained.** A PRD with twenty-one unfinished features has twenty-one entries to
keep in step with twenty-one files, and hand-maintenance of that has never once happened — the
corpus this schema was measured against listed **zero** TBD items while carrying twenty-one.
Generating it is the only version of this that stays true.

It **aggregates** rather than re-derives. Each `<gap>` row is a pointer to a feature's own
**open** `<gap>` — slug, id, kind, date, no body — so there is one place a gap is written and one
place it is corrected. A closed gap is not an authoring gap and gets no row. A `<feature>` row is
for a feature with *no open* gap that is nonetheless short of `defined`: nothing to carry, so the
shortfall is named directly.

`<summary>` counts the `<definition>` values. It is the line a person reads first and the only
number in the file that is not a pointer.

### `kind=` on a step is what routes it

| `kind` | What it is | Where it goes |
|---|---|---|
| `spike` | technical validation, with what it must measure | investigation |
| `infrastructure` | environment, pipelines, access | before the work that needs it |
| `data-model` | modelling to settle before building | before the layer that uses it |
| `ux` | design work | alongside |
| `breakdown` | ready to generate tasks from | `/breakdown` |
| `decision` | a decision taken, usually with `status="done"` | the record |

**`kind` is not there so `/breakdown` can consume a sequence.** It must not: the ordering in this
file is a second model's unvalidated inference, and `<depends-on>` plus `plan-layers` replace it.
What survives here is the *rationale* — why a spike matters, what it must measure — which is the
part no dependency graph can hold.

### Two elements that are deliberately not read

**`<risks>` is for the person resuming the work**, and nothing consumes it. Recorded so that its
absence from every consumer list reads as intent rather than as an oversight.

**`<open-questions>` may be a pointer.** A register of questions outlives any one PRD, so a
project that keeps one project-wide should link it rather than copy entries back inline. The
`href` form and an inline list are both valid; `check-references.py` validates `OQ-NNN` citations
either way.

### Migrating a prose `what-next.md` (item 12)

**`/prd`'s initialization reads `<status>` from `what-next.md` *or* `index.md`, and that dual
check stays** until every artefact is migrated. A PRD that cannot be found is a PRD that gets
overwritten — F3, which cost an interview before it was fixed.

So the marker must stay readable in **both** shapes: `<status>` sits directly under
`<what-next>` in the old file and under `<meta>` in the new one, and `list-prds.py` takes the
first `<status>` in the file either way. That is not an accident of the regex; it is the reason
the element was left where a naive reader finds it.

## `features/{feature-slug}.md` — one feature

```xml
<feature>
  <meta>
    <name>{{Feature Name}}</name>
    <slug>{{feature-slug}}</slug>
    <!-- priority is NOT here. It lives on the index entry -- core §4 -->
    <definition>tbd|in-progress|defined|excluded|superseded</definition>
    <!-- required by the BAR on a `defined` feature, optional in the schema. Core §7 -->
    <review by="{{who read it}}" at="{{YYYY-MM-DD}}" sha="{{first 12 hex}}"/>
    <!-- optional; a judgement, never derived. See below -->
    <architecturally-significant
        because="quality-attribute|risk|first-of-a-kind|cross-cutting|external-dependency|constraint"
        criteria="3,7"/>
  </meta>

  <user-story>
  As a {{actor}}, I want {{capability}}, so that {{benefit}}.
  </user-story>

  <description>
  {{Detailed feature description}}
  </description>

  <!-- zero or more; the edges plan-layers orders by -->
  <depends-on slug="{{other-feature}}" kind="data|runtime|reference"/>

  <acceptance-criteria>
    <criterion id="1" pattern="event-driven" priority="P0">
      When {{trigger}}, the system shall {{response}}.
    </criterion>
    <criterion id="2" pattern="unwanted-behaviour" priority="P1">
      If {{condition}}, then the system shall {{response}}.
    </criterion>
    <!-- More criteria -->
  </acceptance-criteria>

  <gaps>
    <gap id="1" kind="dependency" raised="{{YYYY-MM-DD}}">
    {{What is not known, in markdown. Core §6}}
    </gap>
  </gaps>

  <notes>
    <data-model>
    {{Entities and fields. READ by analyze-prd -- see below}}
    </data-model>
    <considerations>
    {{Everything else. Deliberately unread}}
    </considerations>
  </notes>

  <!-- required when definition is `excluded` -->
  <rationale>{{why this feature is not being built}}</rationale>
  <!-- required when definition is `superseded` -->
  <superseded-by slug="{{the feature that absorbed it}}"/>
</feature>
```

**`<acceptance-criteria>` is core §2 and is identical to the CRD's.** One EARS sentence per
criterion, one behaviour; `id` is stable and citable; `pattern` is assigned by a person and
`priority` defaults to `P1`. Nothing about it is PRD-specific, which is exactly why it is not
defined here.

**The second criterion above is not filler.** A feature whose criteria are all `event-driven` has
said what happens when things go right and nothing else, and the template showing only that shape
is how a corpus ends up with no `unwanted-behaviour` criteria in it at all.

**`<definition>` is core §3's second row** — how completely this feature is *defined*, never how
much of it is built. `excluded` and `superseded` are how a feature that is *not being built*
stays in the PRD as a record instead of vanishing from it, and each is paired with the element
that says why: no `<rationale>` on an `excluded` feature, and no successor on a `superseded` one,
means the file records a decision nobody can reconstruct.

**`<review>` is core §7**, and it is the half of the `defined` gate a script cannot supply.
Optional in the schema and **required by the bar**: a `tbd` or `in-progress` feature has nothing to
review yet, so an element required everywhere would put a false record on every unfinished file.
`sha` is what separates *reviewed* from *reviewed, then edited*, which is why nothing writes the
element by hand — `check-definition.py --record-review --by NAME` computes the hash and writes it,
and `commands/prd.md` Phase 7 is where `/prd` runs it.

**`<gaps>` is core §6**, and it goes between `</acceptance-criteria>` and `<notes>` — stated,
because a migration needs somewhere definite to put it. A resolved gap is **closed**, never
deleted: `closed="YYYY-MM-DD"`, `closed-by` naming the criteria that resolved it, and a line in
the body saying how. Only open gaps count toward anything.

**`<priority>` is gone from `<meta>`.** It duplicated the index entry with nothing keeping the two
in step and no check that they agreed. Core §4 has the argument: a ranking has no meaning inside
the thing being ranked.

### `<user-story>` — intent, before its elaboration

**Required for `defined`; optional for `tbd`.** A feature acquires one on promotion, so early
authoring stays cheap and the bar applies where it matters.

**A separate element, not part of `<description>`.** The description is about *scope* — what is
in, what is out, and who holds each excluded part. Intent and elaboration are different jobs, and
one element serving two of them serves neither. The story comes first because the description
elaborates it.

**Prose with a three-part convention, not parsed attributes.** No consumer needs to *understand*
a user story. Locate it, check its shape, leave it in prose.

**The actor may be a consuming feature, not only a person.** Reference-data features often have
no human user, and forcing one produces *"As a system, I want…"* — the degenerate case that
teaches people to stop taking the field seriously. *"As **Best Value Engine**, I want price bands
per venue, so that I can compare offers without re-deriving them"* is a better story **and** it
forces a reference-data feature to name who consumes it. The features least able to state a human
benefit are exactly the ones whose consumers are least clear.

### `<depends-on>` — the edges, not the order

```xml
<depends-on slug="save-link" kind="data"/>
```

| `kind` | Means |
|---|---|
| `data` | this feature reads or writes something the other one defines |
| `runtime` | this feature calls the other one, or needs it running |
| `reference` | this feature mentions the other one; no build-order consequence |

**Captured where they are noticed, which is during the interview.** While writing features an
author notices dependencies and has nowhere to record them, so they come out as an *ordering* in
`what-next.md` instead — a second model's unvalidated inference, produced with no dependency
graph and no awareness that layer planning exists to do exactly this job.

**The durable artefact is the dependencies, not the order.** `breakdown-plan-layers` derives the
ordering from these edges, once, in the component that owns ordering. `<next-steps>` keeps the
*rationale* — why a spike matters, what it must measure — and drops the sequence.

**`kind` is what makes a link different from a dependency.** A plain markdown link to another
feature is indistinguishable from *"see also"*; that ambiguity is the defect this element exists
to remove, and it is why `reference` is a value rather than an absence.

### `<notes>` — two elements, one of them deliberately unread

**`<data-model>` is read.** `analyze-prd` takes entities and fields from it and stops inferring
them. Locating it is not enough — a consumer must *understand* it — which is the test for whether
something earns an element.

**`<considerations>` is unread by design, and the template says so.** It is the catch-all that
makes migration safe and prose survivable: unrecognised note content goes here **verbatim, never
dropped**. Marking it explicitly unread is what distinguishes *unread by design* from *unread by
oversight*.

**There is no `<relationships>` element.** Outbound edges are `<depends-on>` above, in
machine-readable form; inbound ones are found by grepping this feature's slug across the PRD.
Relationship *prose* stays in the notes. A second structured list of the same relationships would
be two producers for one idea.

### `<architecturally-significant>` — core §8

**Defined in [core §8](core.md#8-architecturally-significant--a-judgement-declared), and identical
to the CRD's since item 76.** The `because` enum, the optional `criteria` list, and the argument
for why it is declared rather than derived all live there. Nothing about it is PRD-specific, which
is exactly why it is not defined here.

On this path it is item 35, and what it buys is a design step over the handful of features that
warrant one instead of over every feature in the PRD.

### There is no `<phases>` element, and that is a decision

Phasing is **priority plus gaps**, and between them nothing is left for a third axis to carry:

| Saying | Element | Also carries |
|---|---|---|
| less important | `priority="P2"` on a criterion | a rank |
| blocked | `<gap kind="dependency\|decision">` | *why*, and *since when* |

The case that looked like it needed a third axis — **a criterion that is essential but blocked** —
is handled better by the pair: the criterion keeps its `P0` because it matters, and the gap blocks
execution because it cannot proceed. A phase would have forced an author to *demote* something
important in order to say it was stuck.

What is genuinely lost is naming a coherent increment, because priority ranks and does not group.
That is recovered from the filter instead: `--requirement-level P0` **produces** the increment, so
the grouping is a query result rather than a fourth thing to maintain.

## `architecture.md` — the project rule file

Not under `docs/prd/{slug}/`: it describes the **codebase**, and `/prd` supports several PRDs in
one repository. Full element reference in
[`architecture-format.md`](../skills/breakdown/references/architecture-format.md).

```markdown
# Architecture: {{Project Name}}

## Overview
{{prose a human reads; the toolchain never parses this}}

## Machine-Readable Section
<architecture version="1.0">
  <rules>
    <layers>
      <layer id="1" name="foundation" depends-on=""/>
      <layer id="2" name="backend"    depends-on="1"/>
      <layer id="3" name="frontend"   depends-on="2"/>
      <layer id="4" name="integration" depends-on="2,3"/>
    </layers>
    <testing default="tdd" runner="pytest">
      <policy match="web/**" kind="component" runner="vitest"/>
    </testing>
    <task-limits default="3"/>
    <repo-structure>single</repo-structure>
    <banned>
      <rule kind="import" match="core/**" symbol="requests|httpx"
            reason="ADR-002: core must be usable as a library">
        <except match="core/adapters/**" reason="adapters exist to call out"/>
      </rule>
    </banned>
    <scaffold template="python" path="webapps/backends/python"/>
  </rules>
  <principles>
    <principle id="P-001">{{a rule with no alternatives weighed}}</principle>
  </principles>
  <api-registry/>
  <schema-registry/>
</architecture>
```

**`<rules>` is obeyed; `<principles>` is read.** Something written as a principle when it needed
to be a constraint gets weighed rather than enforced, while the author believes it is in force.

**Registries may be any set the architecture needs** — `<event-registry>`, `<command-registry>`,
`<service-registry>`, `<screen-registry>` — not only the REST-and-relational pair. Leave them
empty at PRD time: they are filled from the code after `/execute`.

