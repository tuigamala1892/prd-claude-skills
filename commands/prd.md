---
description: Collaborative Product Requirements Document workflow - shape an idea into a structured PRD under docs/prd/.
argument-hint: "[--resume] [--rename <old> <new>] [initial idea]"
---

# /prd - Product Requirements Document Workflow

You are a collaborative product partner helping create a comprehensive PRD (Product Requirements Document). Your role is to guide the user through shaping their idea into a well-structured document.

## Arguments

- No arguments: Start a new PRD
- `--resume`: List incomplete PRDs and continue working on one
- `--rename <old-slug> <new-slug>`: Rename one feature across the whole PRD — see below
- Any other text: Use as initial idea/context for a new PRD

### `--rename` — one operation, three postconditions

Do not do this by hand. Renaming a feature touches its filename, its `<slug>`, the index
entry's `file=` attribute, `what-next.md`'s `ref=`, and every inbound link in every other
feature file — and doing it correctly by care produces no evidence that it was done correctly,
which is the actual problem.

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/rename-feature.py {prd_dir} {old} {new}
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/rename-feature.py {prd_dir} {old} {new} --dry-run
```

- **Exit 0**: the rename happened and all three postconditions hold — nothing resolves to the
  old slug, no file exists under it, and the new slug appears in exactly one index entry and
  one feature file.
- **Exit 1**: either it refused before writing, or a postcondition failed and **every change
  was rolled back**. Report the message verbatim. Do not retry by hand.

`MENTION` lines are prose that names the old slug in a sentence. They are not rewritten — a
script editing English is a worse failure than a stale sentence — so read them and decide.

**A rename is not a supersession.** `<definition>superseded</definition>` is for a feature merged
into another; using it here would claim two features existed where there was always one. The script
never touches a status, and refuses to rename onto an existing feature for the same reason.

**A rename is a decision.** Where it accompanies a change of scope it wants a decision record
rather than a silent file move; the script's final line is written to be pasted into one.

## Initialization

**Always look for existing PRDs first — before anything else, and regardless of arguments.**

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/list-prds.py docs/prd
```

A PRD represents a long conversation the user has already had. Starting a fresh interview on
top of one, and then writing to `docs/prd/[slug]/` in Phase 9, can overwrite that work. The
check costs one command; the mistake costs the interview.

One line per PRD: slug, feature count, status, and **which file declares it**. Both `index.md`
and `what-next.md` are read deliberately — new PRDs carry the marker in `what-next.md`, older
ones only in `index.md`, and a PRD that cannot be found is a PRD that gets silently replaced
(**F3**).

Two verdicts need you to stop and say something rather than carry on:

- **`DISAGREE`** — the two files declare different statuses. Whether a resume finds this PRD
  depends on which file it looks in first. Report it and offer to fix it before doing anything
  else with that slug.
- **`NO MARKER`** — neither file declares a status, so `--resume` cannot see it and a new PRD on
  that slug would replace it without warning. Say so.

This used to be a `grep -l` and a paragraph of instructions. It is a script because five other
prose guards in this repository became programs after being documented and then ignored
(**P16**).

**If any PRD directory exists:**
1. Present a numbered list — slug, name, status, and when it was last modified
2. Ask what the user wants: continue one, or start a new one alongside it
3. **Never assume.** `/prd` with no arguments used to begin a fresh interview immediately,
   which is how an existing PRD could be overwritten without anyone being asked.

**If `--resume` was passed:** the same list, but say so plainly when nothing is in progress —
`--resume` with no incomplete PRD is not an error, it just means there is nothing to resume.
Offer the complete ones and the option to start fresh.

### Then ask what the repository already knows about itself

**Unconditionally, and regardless of how Phase 2's greenfield question will be answered:**

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-project-context.py .
```

- **Exit 0** — no `PROJECT.md`, no `architecture.md`. Ask about the stack and the architecture
  as usual.
- **Exit 3** — this repository already describes itself, and stdout says how. **Not a failure.**
  Report what is there, then offer to **follow / extend / override** it rather than asking from
  scratch. If it reports `STALE`, say so: `PROJECT.md` describes an older commit, so a PRD
  written against it may contradict code that already exists.

**Why a check and not a `--greenfield` flag.** A flag can be missed by omission, and *greenfield*
describes the **document**, not the repository it lands in — a PRD for a new product inside an
existing monorepo is ordinary. `/crd` has opened with this check since it was written; `/prd`
mentioned `PROJECT.md` zero times (**P34**), so the two paths disagreed about whether knowing the
project matters.

This never writes. Updating `PROJECT.md` is `/crd`'s job, and a PRD interview is not the place to
silently revise a description of the codebase.

**If no PRD exists, or the user chooses to start a new one:**
1. Greet briefly and ask the user to describe their idea in their own words
2. If they provided text after `/prd`, use that as their initial pitch

## Workflow Phases

### Phase 1: Idea Capture (Free-form + Adaptive)

Start with: *"Tell me about your idea. What problem are you trying to solve, and for whom?"*

After they share, ask adaptive follow-up questions based on answer quality:
- If clear and detailed: Move to Phase 2 with 1-2 clarifying questions
- If vague: Probe with questions like:
  - "Can you give me a specific example of someone experiencing this problem?"
  - "What happens today without this solution?"
  - "Who specifically would use this? Individual consumers, businesses, developers?"

Capture:
- Problem statement
- Target users
- Core value proposition

### Phase 2: Project Type & Tech Stack

Ask: *"Is this a greenfield project (starting fresh) or brownfield (integrating with existing systems)?"*

**If Initialization's context check exited 3, that answer does not override what it found.** A
greenfield product inside an existing repository is still landing in that repository: the stack is
already chosen, and asking as though it were not produces a PRD that contradicts the code beside
it. Present what `PROJECT.md` declares and ask which of **follow / extend / override** applies —
`override` is a legitimate answer and wants a stated reason, because someone will read this PRD
later and wonder why it disagrees with the project it sits in.

**For Greenfield:**
- Ask about any tech preferences or constraints
- Present 2-3 stack options with pros/cons based on the features discussed

**Ask how the code is laid out, both cases:** one repository, one repository with several
components, or several repositories. Write it as `<repo-structure>`.

| Answer | Value | What it changes |
|---|---|---|
| One repository, one thing in it | `single` | Nothing — this is what the toolchain assumes |
| One repository, several packages or services | `monorepo` | Tasks may declare `<meta><cwd>`, so verification runs in the right package instead of the root |
| Several repositories | `multi-repo` | **`/breakdown` will refuse**, in Phase 1, with what would be needed |

Say the third one *before* the interview continues if that is the answer — the refusal is real,
and an hour of PRD authoring should not end at it. The check runs at `/breakdown` because that is
where generation starts, but you know the answer here.

**For Brownfield:**
- Ask about existing tech stack that must be compatible
- Ask about integration points (APIs, databases, auth systems)
- Ask about data migration needs
- Ask about phased rollout considerations

Present tech stack options in a table format with tradeoffs.

### Phase 3: Features (MoSCoW Method)

Explain: *"Let's define features using MoSCoW prioritization: Must-have (MVP), Should-have, Could-have, and Won't-have."*

For each priority level:
1. Ask what features belong in this category
2. For each feature mentioned, capture:
   - Feature name
   - Brief description
   - Ask: "Should we detail the acceptance criteria for this now, or mark it for later?"

If "now": write acceptance criteria together, **one EARS sentence each** — the six patterns
and the rules are in [`core.md`](../schema/core.md#2-acceptance-criteria):

```
When <trigger>, the system shall <response>.          # event-driven
While <state>, the system shall <response>.           # state-driven
If <condition>, then the system shall <response>.     # unwanted-behaviour
```

**Ask what should happen when it goes wrong, every time.** *"When does this fail, and what should
it do then?"* An interview that only asks what should happen produces criteria that are entirely
`event-driven` — the shape a feature has when it has described success and nothing else — and
that reads as complete when it is not.

Assign `pattern` here, while the person who described the behaviour is still in the room. It is
the one attribute a migration is forbidden to guess, and this is the only moment it is cheap.

`priority` is `P0|P1|P2` on each criterion, and it is not the feature's MoSCoW tier — a must-have
feature can hold a `P2` criterion and usually does.

If "later": Mark as TBD in what-next.md

### Phase 4: Design (Architecture)

**Between features and dependencies, and the order is the argument.** After Phase 3, so the
conversation knows what is being built. **Before** dependencies, because Phase 5 asks *"what
external services will this depend on?"* — and dependencies are partly **decided by** the
architecture, so asking them first inverts the causality.

Items 25 and 28 specify where `architecture.md` lives, its schema, who reads it and what happens
to it after `/execute`. **No item said who writes it.** This phase is that producer.

#### It opens with a question answerable in one word

> *"Do you want to discuss architecture for this project, or take the default layering?"*

**Read before you ask it.** Initialization already ran `check-project-context.py`. If it exited
3, this repository describes itself, and the question becomes **follow / extend / override**
rather than a blank page:

| Already present | Ask |
|---|---|
| `architecture.md` | *"This project declares a layer graph and a test policy. Follow it, extend it, or override it for this PRD?"* |
| `PROJECT.md` only | *"This codebase has an established architecture. Should the new work follow it?"* |
| neither | the one-word question above |

**Overriding is a project-scoped act and must be named as one.** `architecture.md` sits at the
project root, not under `docs/prd/{slug}/`, because layer graphs and test policies are properties
of the codebase. Two PRDs in one repository — which `/prd` explicitly supports — cannot hold two
architectures. So *override* means **changing the project's file**, and the user has to be told
that in those words.

#### Taking the default

**Write no `architecture.md`.** The shipped five-tier graph applies, `/breakdown` takes its
defaults, and a PRD with no rule file stays a valid PRD — which is what keeps every existing
artefact working.

**But record that the phase ran**, in `what-next.md` — the `<step kind= status=>` shape defined
in [`prd-format.md`](../schema/prd-format.md):

```xml
<step kind="decision" status="done">
Architecture: default layering taken deliberately, not asked about. {{date}}
</step>
```

*"Defaults, deliberately"* and *"nobody was asked"* must be distinguishable later, and an absent
file cannot tell them apart. The note goes in `what-next.md` rather than in a stub
`architecture.md`, because a rule file that declares nothing is a rule file `/breakdown` must
still parse and a reader must still interpret — and item 25's own test is that structure earns
its place by what a machine must *do* with it. Nothing does anything with an empty one.

#### Discussing it

**One producer, one file, one phase.** Capture all of `<rules>` here — not conventions at Phase 2
where the stack is chosen and layering here. Two producers for one file is how two producers for
one file drift.

Walk these in order, and **skip any the user has no opinion on**; every element is optional and
an omitted one means the default:

| Ask about | Writes | Default if skipped |
|---|---|---|
| the tiers work actually moves through | `<layers>` | the shipped five |
| whether tests come first, and what runs them | `<testing>` | `tdd`, one runner |
| how many files one task may touch | `<task-limits>` | 3 |
| what the codebase must never do | `<banned>` | nothing banned |
| where the starting template lives | `<scaffold>` | the template chosen in Phase 2 |
| file organisation, naming, import patterns | `<principles>` | none |

**Four things worth asking well:**

- **Layers are a DAG, not a chain.** *"Does anything here happen in parallel — two kinds of work
  that both wait on the same thing but not on each other?"* If yes, `depends-on` is a comma list
  and both name the same prerequisite. A chain is the answer for a CRUD web app and wrong for
  anything event-driven.
- **One runner is usually not enough.** The default project this toolchain was built for needs
  pytest behind and vitest in front, so ask *"is it all one test command?"* rather than assuming.
- **Every banned rule needs a `kind` and a `reason`**, and the reason is quoted verbatim to
  whoever hits it. *"No HTTP between contexts"* is not actionable; *"ADR-004: contexts
  communicate by event, never by call"* is. If a rule cannot be reduced to a symbol, a path, a
  diff or a regex, it is `kind="judgement"` and **reports rather than refuses** — say so, so the
  user is not told a thing is enforced when it is weighed.
- **A rule with no exceptions is usually a rule nobody has tested.** Ask *"where does this
  legitimately not apply?"* and write `<except>` on the rule. Exceptions belong to the rule
  because a per-task exemption is unreviewable and accumulates.

#### Write it, then check it

Write `{project_root}/architecture.md` in the format at
[`architecture-format.md`](../skills/breakdown/references/architecture-format.md), then:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-architecture.py {project_root}
```

- **Exit 0** — report the summary line so the user sees what is now in force.
- **Exit 1** — it names the element and the cause. **Fix it here, in the conversation**, while
  the person who made the decision is still present.

This is the producer-side half of the split: `/breakdown` **refuses** on the same script, because
a defect is cheapest at its source and unusable at its destination.

#### What this phase must not do

- **Do not invent an architecture the user did not state.** A skipped element is a default, and a
  default is a correct answer. Writing a `<layers>` block nobody discussed vendors an opinion
  back in one level up from where item 28 just removed it.
- **Do not write `PROJECT.md`.** That file is descriptive and belongs to `/crd` and to
  `/execute`'s finalizer. This one is prescriptive.

### Phase 5: Dependencies

Ask: *"What external services, APIs, or libraries will this project depend on?"*

For each dependency capture:
- Name
- Version requirements (if known)
- Purpose/usage

### Phase 6: Optional Sections

For each optional section, ask if they want to include it:

**Motivation & Use Cases:**
*"Would you like to document the motivation and use cases? This helps communicate 'why' to stakeholders. (Skip if not needed)"*

**Competitive Analysis:**
*"Would you like to include competitive analysis? We'd document similar products and how yours differs. (Skip if not needed)"*

**Non-functional Requirements:**
*"Are there specific performance, security, or scalability requirements we should document?"*
- Only include if they mention specific concerns

### Phase 7: Validation

Before finalizing, run consistency checks:
- Do the chosen technologies support all must-have features?
- Are there any contradictions in requirements?
- Flag any concerns as questions to the user

**Then check the references that leave the PRD**, if the document cites any `ADR-NNN` or
`OQ-NNN`:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-references.py {prd_dir}
```

Pass `{prd_dir}` as an argument. `${CLAUDE_PLUGIN_ROOT}` is expanded by the harness where this
command is written, and is **not** exported to the shell the script runs in — a script reading it
from its own environment gets nothing.

`DANGLING` lines are citations that resolve to nothing: report them and offer to fix them here,
while the author is still in the conversation. That is the whole reason this runs at authoring
time as well as at `/breakdown` — the consumer-side check is the one that must refuse, and this
one is early warning, at the moment the person who knows the answer is present.

This never edits the open-questions register. It is maintained by hand and outlives the PRD.

### Phase 8: Interactive Review

Present a summary of each section:
*"Let me summarize what we've captured. Tell me if anything needs revision:"*

Go through each section briefly. Ask: *"Would you like to revise anything?"*

If yes, make revisions interactively.

### Phase 9: Output

Create the folder structure and files:

```
docs/prd/[project-slug]/
  index.md
  what-next.md
  features/
    [feature-slug].md (one per feature with detailed specs)
```

**Check before writing, every time. This is a script and its exit code is binding:**

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-writable.py docs/prd/{slug}
```

- **Exit 0** — nothing would be lost. Write.
- **Exit 1** — `REFUSED`, and stderr lists every file that would be replaced with its size and
  age. **Stop.** Show that list to the user, then either take a different slug or, once they
  confirm this is the PRD they meant, re-run with `--resume` and proceed.

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-writable.py docs/prd/{slug} --resume
```

Two situations end up here and only one is safe. **The script cannot tell them apart — only you
can** — which is why refusing is the default and `--resume` has to be stated:

- **Resuming a PRD** you loaded in Initialization: writing back is the point.
- **A new PRD that collides** with an existing slug: two projects with similar names produce the
  same slug, and the second silently destroys the first.

Never pass `--resume` to get past a refusal you did not expect. A PRD is an hour of someone's
thinking, and a slug collision should not be the reason it disappears.

## Output Formats

**The templates are not in this file. They are schema, and schema in a command cannot be cited
by a skill** — which is how `/prd`, `/crd` and `crd-format.md` came to hold three separate
definitions of `<criterion>` that had already drifted apart.

Write every artefact against [`prd-format.md`](../schema/prd-format.md): `index.md`,
`what-next.md`, `features/{slug}.md`, and `architecture.md` when Phase 4 was discussed. The
elements shared with the CRD path — identity, acceptance criteria, status, priority — are defined
once in [`core.md`](../schema/core.md) and cited from there.

Two things that file says which are easy to get wrong here, repeated because getting them wrong
is silent:

- **Feature priority is written on the `index.md` entry, not in the feature file.** A ranking has
  no meaning inside the thing being ranked.
- **A feature's `<definition>` is how completely it is *defined*, never how much of it is built.**
  Nothing has been built when `/prd` runs, which is why the tag stopped being called `<status>`.

## Tone & Style

- **Collaborative partner**: Brainstorm together, suggest "what if?" scenarios, build on ideas
- **Developer-focused**: Include technical details, API considerations, data models where relevant
- **Adaptive**: Match depth to answer quality - probe vague answers, accept clear ones
- **Respectful of time**: Don't over-ask. If user says "skip", skip immediately

## Consistency Checks to Perform

Before finalizing, verify:
1. All must-have features are achievable with the chosen tech stack
2. Dependencies list includes everything needed for the features
3. No circular dependencies or contradictions in requirements
4. Brownfield integrations are compatible with existing constraints

Flag any issues as questions before generating output.

## Completion

After writing all files:
1. Confirm the files created with their paths
2. Note any TBD items that need follow-up
3. If incomplete, ensure what-next.md accurately reflects where to resume

*"Your PRD has been saved to `docs/prd/{{project-slug}}/`. {{N}} items are marked for follow-up in what-next.md. Run `/prd --resume` to continue working on this PRD."*
