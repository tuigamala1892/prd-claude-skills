# `architecture.md` Format Specification

The project's **prescriptive** architecture artefact: what the toolchain must obey when it plans
layers, generates tasks, reviews them and verifies them.

Plan items 25, 28 and 37. Findings P11, P17, P18, P35.

---

## Why this file exists

Five architectural opinions were vendored into the plugin and no project could override any of
them (P18): the five-tier layer graph, mandatory TDD, three files per task, the template enum, and
verification as shell commands. Disagreeing with one meant forking the plugin.

This file is the channel. It is **optional** — a project with no `architecture.md` gets exactly
the behaviour the toolchain has always had, and every artefact written before this file existed
keeps working. What changes is that the defaults are now *defaults* rather than laws.

## Where it lives, and why not somewhere else

`{project_root}/architecture.md`, beside `PROJECT.md`.

**Project root, not `docs/prd/{slug}/`.** `/prd` explicitly supports several PRDs in one
repository — it globs `docs/prd/*/` and offers to start a new one alongside an existing one. A
layer graph, a test policy, a task limit and a banned pattern are properties of the **codebase**,
not of a document about it. Per-PRD would let two PRDs state two architectures for one repository.

**Not `what-next.md`.** That file is transient by design — a status marker and a session to-do
list, consumed and then stale. An architectural constraint is durable and is read *every time*
tasks are generated.

## Its relationship to PROJECT.md

The two files share a schema and differ in direction:

| | `architecture.md` | `PROJECT.md` |
|---|---|---|
| Direction | **prescriptive** — what must be true | **descriptive** — what is true |
| Written by | `/prd`'s Design phase (item 51), by hand | `crd-investigate`, `project-context-finalizer` |
| Derived from | a conversation | the code |
| Lifetime | authored before code exists | rewritten after every run |

Registries are **root children in both**, with the same element names and the same content
model, so item 26's seeding of `PROJECT.md` from `architecture.md` is a subtree **copy** rather
than a transform. The registry elements themselves are defined once, in
[`../../crd/references/project-format.md`](../../crd/references/project-format.md); this file
does not restate them.

---

## Structure

Markdown for a human, with one machine-readable block, exactly as `PROJECT.md` is laid out.

````markdown
# Architecture: {name}

## Overview
{prose a human reads; the toolchain never parses this}

## Machine-Readable Section
<architecture version="1.0">
  <rules>...</rules>
  <principles>...</principles>
  <api-registry>...</api-registry>
  <schema-registry>...</schema-registry>
</architecture>
````

### Root element

```xml
<architecture version="1.0">
  <rules>...</rules>            <!-- optional; what the toolchain OBEYS -->
  <principles>...</principles>  <!-- optional; what a reader is TOLD -->
  <api-registry/>               <!-- optional; any number of registries -->
  <schema-registry/>
  <event-registry/>
  <command-registry/>
  <service-registry/>
  <screen-registry/>
</architecture>
```

**Every child is optional.** A file declaring only `<layers>` is valid; so is one declaring only
a `<command-registry>`. What is *not* valid is a file that is present and unparseable — see
[Refusals](#refusals).

### `<rules>` versus `<principles>` — the distinction is enforcement (item 37)

| Kind | Test | Home | Enforced? |
|---|---|---|---|
| **Decision** | has rejected alternatives to record | a decision record, outside this file | no — it is a record |
| **Principle** | a rule, with no alternatives weighed | `<principles>` here | no — it is guidance |
| **Constraint** | the toolchain must obey it | `<rules>` here | **yes — exit code** |
| **Advisory** | stated and checked, not decidable by comparison | `<rule kind="judgement">` | reports, never refuses |

Both sections live in this one file — a separate `PRINCIPLES.md` would make three files
describing one project — and they are distinct *within* it. `<rules>` is what a script obeys;
`<principles>` is what a reader is told. Something written as a principle when it needed to be a
constraint gets weighed rather than obeyed, while the operator believes it is in force. That is
P16's failure mode, and keeping the two sections separate is what makes it visible.

**Registries are not in `<rules>`.** A registry is an inventory the toolchain *reads*, not a
constraint it *obeys*, and nesting them would make item 26's seeding a transform instead of a
copy. They sit beside `<rules>` as root children, at the level `PROJECT.md` already uses them.

---

## `<rules>`

### `<layers>` — the layer graph, which stops being hardcoded

```xml
<layers>
  <layer id="0" name="setup"       depends-on=""/>
  <layer id="1" name="foundation"  depends-on="0"/>
  <layer id="2" name="backend"     depends-on="1"/>
  <layer id="3" name="frontend"    depends-on="2"/>
  <layer id="4" name="integration" depends-on="2,3"/>
</layers>
```

| Attribute | Required | Description |
|---|---|---|
| `id` | Yes | Unique within the block. Used in `depends-on` and in the task id prefix `L{id}-` |
| `name` | Yes | Layer name. The directory is `{id}-{name}`, matching the existing convention |
| `depends-on` | Yes | **Comma-separated list** of layer ids. Empty means no dependencies |
| `applies-to` | No | On the `<layers>` element, not the `<layer>`. See below |

**`depends-on` is a comma list and the result is a DAG, not a chain.** An event-driven graph fans
contracts out to producers and consumers independently and then converges; a single-valued
attribute cannot express that, and the fan-out is the whole point of the architecture:

```xml
<layers>
  <layer id="1" name="contracts"      depends-on=""/>
  <layer id="2" name="infrastructure" depends-on="1"/>
  <layer id="3" name="producers"      depends-on="1,2"/>
  <layer id="4" name="consumers"      depends-on="1,2"/>   <!-- sibling of producers -->
  <layer id="5" name="projections"    depends-on="1,2"/>
  <layer id="6" name="orchestration"  depends-on="3,4"/>
  <layer id="7" name="integration"    depends-on="3,4,5,6"/>
</layers>
```

**`applies-to` instantiates the graph once per matching directory.** Microservices and
multi-platform mobile need the same tiers repeated per unit, and flattening them is not merely
inconvenient — one global graph orders *every* service's data layer before *any* service's API,
destroying the independent deployability the architecture was chosen for.

```xml
<layers>                             <!-- shared, unscoped -->
  <layer id="1" name="contracts"    depends-on=""/>
  <layer id="9" name="gateway"      depends-on="1"/>
  <layer id="10" name="integration" depends-on="1,9"/>
</layers>
<layers applies-to="services/*/">    <!-- instantiated per service -->
  <layer id="1" name="data"  depends-on=""/>
  <layer id="2" name="logic" depends-on="1"/>
  <layer id="3" name="api"   depends-on="2"/>
</layers>
```

Layer ids are scoped to their block, so the two `id="1"`s above do not collide. A scoped layer's
directory is `{unit}/{id}-{name}`. A project with a single unscoped block never meets this
feature.

**Read by** `breakdown-plan-layers`, which uses this graph in place of
[`layer-definitions.md`](layer-definitions.md) when the file is present. That reference becomes
the **default graph**, not the graph.

**A tier with no work in it is not a tier** (item 31). Declaring a layer does not create it: the
derivation drops any layer to which no task was assigned. Declaring `frontend` in a project that
turns out to have no frontend costs nothing.

### `<testing>` — policy and runner, scoped

```xml
<testing default="tdd" runner="pytest">
  <policy match="web/**"       kind="component"    runner="vitest"/>
  <policy match="e2e/**"       kind="end-to-end"   runner="playwright"/>
  <policy match="contracts/**" kind="schema-compatibility"/>
</testing>
```

| Attribute | Required | Description |
|---|---|---|
| `default` | Yes | `tdd` or `none`. `tdd` is the shipped behaviour |
| `runner` | No | Default test runner |
| `policy match` | Yes | Path glob the policy applies to |
| `policy kind` | Yes | Free text naming the kind of test. Carried into the task, not interpreted |
| `policy runner` | No | Overrides the default runner for matching paths |

**One runner is never enough, and the default case proves it.** The monolithic SPA this toolchain
was built for needs pytest behind and vitest in front. A single `runner` attribute could not
describe the shipped default, which is why the scoped form exists rather than being an
accommodation for exotic projects.

**`default` has three readers, and all three must change together.** The TDD mandate does not
live in `tdd-workflow.md`, which only describes Red/Green/Refactor — it is imposed upstream by
`task-format-spec.md` marking `<test-requirements>` a required section and by `review-criteria.md`
making it critical twice. A project declaring `default="none"` would otherwise have every task
fail batch review at `/breakdown` and never reach `execute-batch` at all:

| Reader | What it reads `default` for |
|---|---|
| `breakdown-generate-tasks` | whether to emit `<test-requirements>` |
| `breakdown-review-tasks` | whether to *require* it |
| `execute-batch` | whether to run the red/green cycle |

`tdd` is right for most projects and wrong for a spike. The toolchain should be able to say which
it is running.

### `<task-limits>` — the file cap, scoped

```xml
<task-limits default="3">
  <limit match="contracts/**" max-files="5"/>
</task-limits>
```

| Attribute | Required | Description |
|---|---|---|
| `default` | Yes | Positive integer. `3` is the shipped behaviour |
| `limit match` | Yes | Path glob |
| `limit max-files` | Yes | Positive integer for matching paths |

Three files is right for a UI change and wrong for adding an event type, where the schema, the
producer, the consumer, the projection and the test are one change. Enforced where the limit
already lives: `task-format-spec.md` and `review-criteria.md` become readers of this element
instead of hardcoding `3` (item 56).

### `<repo-structure>`

```xml
<repo-structure>single|monorepo|multi-repo</repo-structure>
```

Defined by item 53; `multi-repo` is refused at `/breakdown` with the reason. **When this element
is present here it is authoritative**, because repository layout is a property of the codebase
rather than of a document about it — a PRD's own `<repo-structure>` is the fallback for a project
with no `architecture.md`. `check-repo-structure.py` reads this file first.

### `<banned>` — five kinds, and the kind decides whether it can refuse

Every rule carries a **required `kind`** and a **required `reason`**. One element name was
covering four unrelated detection mechanisms, which is why *"is it an exit code?"* had no single
answer.

| `kind` | Required attributes | Detected by | Refuses? | Fires in |
|---|---|---|---|---|
| `import` | `match`, `symbol` | forbidden symbol × path glob | **yes** | review *and* verify |
| `edge` | `from`, `to` | dependency graph — a module under X importing from Y | **yes** | verify |
| `change` | `path`, `action` | **the diff against the base branch** | **yes** | verify |
| `content` | `match`, `pattern` | regex over file contents at a path | **yes** | review *and* verify |
| `judgement` | element body | a model reading the code | **no — reports** | verify |

```xml
<banned>
  <rule kind="import" match="contexts/**" symbol="httpx|requests|grpc"
        reason="ADR-004: contexts communicate by event, never by call">
    <except match="contexts/*/adapters/outbound/**"
            reason="third-party APIs are called over HTTP by definition"/>
  </rule>

  <rule kind="change" path="contracts/**" action="modify"
        reason="published events are immutable; add a version, never edit"/>

  <rule kind="content" match="services/*/src/**" pattern="(postgres|mysql|mongodb)://"
        reason="ADR-002: no shared datastore across services"/>

  <rule kind="edge" from="services/*/" to="services/*/"
        reason="ADR-002: services are independently deployable; call by contract, not by import"/>

  <rule kind="judgement" reason="ADR-011: consumers must tolerate replay">
    handler with side effects that are not idempotent
  </rule>
</banned>
```

**`change` is a property of the diff, not of the code.** *"Modifying a published event schema in
place"* is not a pattern anything can match in a file — it is a property of what changed, and
`/execute` already holds both the base branch and the worktree. `action` is `modify`, `delete` or
`rename`.

**`judgement` is a prose guard and is labelled as one.** Prose guards get weighed rather than
obeyed, so these report and never block a merge. A rule that reports is useful; a rule that claims
to enforce and does not is what P16 is about.

**`reason` is mandatory on every rule, and is reported verbatim.** *"Banned: HTTP client to
another context's service — ADR-004: contexts communicate by event, never by call"* tells an
implementer what to do instead. A bare rule number does not.

**Exceptions belong to the rule, never to the task.** `<except match= reason=>` is reviewed once,
lives here where a reader can see it, and applies consistently. A per-task exemption is
unreviewable, accumulates, and would let a component pre-authorise its own violation — which makes
the check advisory with extra steps. A genuine one-off is answered by editing the rule, which is
deliberately the slow route: if the rule truly should not apply to that case, editing it is the
correct change; if it should apply, the task is wrong.

**Two rules that look like bans usually are not.** *"Writes outside the working directory"* and
*"a network call with no offline fallback"* are runtime properties asserted by a test, and belong
in `<testing>`. Moving them out is most of why the `judgement` class is smaller than it looks.

### `<scaffold>` — the template stops being an enum

```xml
<scaffold template="python" path="webapps/backends/python"/>
<scaffold template="none"/>
```

`template` names a template and is **not** a closed set; `path` locates it and is required unless
`template` is `none`. The three names in
[`layer0-templates.md`](layer0-templates.md) become the ones the toolchain ships with rather than
the ones it permits.

---

## `<principles>`

```xml
<principles>
  <principle id="P-001">
  Prefer deleting code to configuring it. Markdown, including links, exactly as elsewhere.
  </principle>
</principles>
```

| Attribute | Required | Description |
|---|---|---|
| `id` | Yes | Unique within the file. This is what a PRD citation resolves against |

**Non-enforced by construction.** Nothing here produces an exit code, and a principle that needs
one is a constraint written in the wrong section.

**Read by** `check-references.py`, which resolves a PRD's principle citations against these ids —
the 10 of the corpus's 190 references item 39 deferred for want of anywhere to resolve them — and
by `breakdown-generate-tasks`, which carries a cited principle into the task's `<context>` as
guidance.

---

## Registries

Any number, any of the names below, as **root children beside `<rules>`**. The element content is
defined in [`project-format.md`](../../crd/references/project-format.md) and is identical here.

| Registry | Records | Natural to |
|---|---|---|
| `<api-registry>` | method, path, request, response | REST |
| `<schema-registry>` | model, table, fields | relational |
| `<event-registry>` | event, version, payload, producers, consumers | event-driven |
| `<command-registry>` | subcommand, flags, exit codes, output format | CLI |
| `<service-registry>` | service, owns, contracts, deployable unit | microservices |
| `<screen-registry>` | screen, route, view-model | mobile / SPA |

**The set is open because the pair was CRUD-shaped.** API-plus-schema is the right pair for a
REST-and-relational project and the wrong pair for four of the five patterns this schema was
tested against. Fixing the layer graph while leaving the registries fixed would re-vendor the same
class of opinion one level down.

**Each registry needs a reader, or this is P4 in a new file.** `breakdown-analyze-prd` loads them
as it loads a feature's `<data-model>` — a registry *is* a data model at project scope — and
`breakdown-generate-tasks` carries the entries a task touches into its `<context>`.
`crd-impact-analysis` reports against them as `<affected-contracts>` (item 57).

---

## Refusals

`check-architecture.py` is run by `/breakdown` Phase 1 and by `/prd`'s Design phase.

**Absent is fine and means defaults. Present-and-broken stops the run**, because a silently
ignored rule file is worse than no rule file at all: the operator believes the rule is in force.

| Condition | Result |
|---|---|
| No `architecture.md` | exit 0, defaults apply |
| No `<architecture>` block in it | **exit 1** |
| Not well-formed XML | **exit 1**, with the bare-`&` hint |
| `<layers>` contains a cycle | **exit 1**, naming the cycle |
| `depends-on` names an unknown layer id | **exit 1** |
| Duplicate layer id within a block | **exit 1** |
| A layer unreachable from any root | **exit 1** |
| `<rule>` with no `kind`, or an unknown `kind` | **exit 1** |
| `<rule>` with no `reason` | **exit 1** |
| `<rule>` missing an attribute its `kind` requires | **exit 1** |
| `<testing default>` not `tdd` or `none` | **exit 1** |
| `max-files` or `task-limits default` not a positive integer | **exit 1** |
| `<scaffold>` with a template but no path | **exit 1** |
| `<principle>` with no `id`, or a duplicate id | **exit 1** |

## Version History

| Version | Changes |
|---|---|
| 1.0 | Initial specification. Plan items 25, 28, 37 |
