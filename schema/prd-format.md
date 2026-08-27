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

```xml
<what-next>
  <status>in-progress|complete</status>
  <last-updated>{{YYYY-MM-DD}}</last-updated>

  <tbd-items>
    <!-- Items marked "for later" during the session -->
    <item section="features" ref="features/auth.md">
      Define acceptance criteria for password reset flow
    </item>
    <!-- More TBD items -->
  </tbd-items>

  <next-steps>
    <!-- What to work on next when resuming -->
    <step>Complete acceptance criteria for authentication features</step>
    <step>Review tech stack decision with team</step>
    <!-- A step that has already happened records that it did, and when -->
    <step kind="decision" status="done">
    Architecture: default layering taken deliberately, not asked about. {{YYYY-MM-DD}}
    </step>
  </next-steps>

  <session-notes>
    <!-- Any context helpful for resuming -->
    {{Notes about decisions made, alternatives considered, etc.}}
  </session-notes>
</what-next>
```

**`<status>` is the same tag `index.md` carries, and that is deliberate** — `list-prds.py` reads
both and reports `DISAGREE` when they differ, because a PRD findable through one file and not the
other is a PRD that gets silently replaced. See core §3.

**`<step>` takes two optional attributes, and the pair is one shape, not two.** `kind` says what
sort of step it was; `status="done"` says it already happened. A step with neither is future work,
which is the common case and why both are optional.

`/prd`'s Phase 4 is the producer that needs them: when the architecture conversation is *declined*
it writes no `architecture.md`, and *"defaults taken deliberately"* must stay distinguishable from
*"nobody was asked"*. An absent file cannot tell those apart; a `kind="decision" status="done"`
step can. This is the only mechanism recording that a phase ran and chose nothing.

## `features/{feature-slug}.md` — one feature

```xml
<feature>
  <meta>
    <name>{{Feature Name}}</name>
    <slug>{{feature-slug}}</slug>
    <priority>must-have|should-have|could-have</priority>
    <definition>defined|tbd|in-progress</definition>
  </meta>

  <description>
  {{Detailed feature description}}
  </description>

  <acceptance-criteria>
    <criterion id="1">
      <given>{{Initial context}}</given>
      <when>{{Action taken}}</when>
      <then>{{Expected outcome}}</then>
    </criterion>
    <!-- More criteria -->
  </acceptance-criteria>

  <notes>
  {{Any additional notes, edge cases, or considerations}}
  </notes>
</feature>
```

**`<acceptance-criteria>` is core §2 and is identical to the CRD's.** One criterion, one
behaviour; `id` is stable and citable. Nothing about it is PRD-specific, which is exactly why it
is not defined here.

**`<definition>` is core §3's second row** — how completely this feature is *defined*, never how
much of it is built. It was called `<status>` until item 45; a feature file that still says
`<status>` is read as `<definition>` and rewritten by item 41's migration, never refused.

**`<priority>` in `<meta>` duplicates the index entry, and the index is the one that counts.**
Two writers for one fact, with nothing keeping them in step and no check that they agree. Item 1
removes it from here; until then, a reader that must choose reads `index.md`.

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

