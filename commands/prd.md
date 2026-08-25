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

**A rename is not a supersession.** `<status>superseded</status>` is for a feature merged into
another; using it here would claim two features existed where there was always one. The script
never touches a status, and refuses to rename onto an existing feature for the same reason.

**A rename is a decision.** Where it accompanies a change of scope it wants a decision record
rather than a silent file move; the script's final line is written to be pasted into one.

## Initialization

**Always look for existing PRDs first — before anything else, and regardless of arguments.**

```bash
ls -d docs/prd/*/ 2>/dev/null
```

A PRD represents a long conversation the user has already had. Starting a fresh interview on
top of one, and then writing to `docs/prd/[slug]/` in Phase 8, can overwrite that work. The
check costs one command; the mistake costs the interview.

For each directory found, read the status marker from **either** file:

```bash
grep -l "<status>in-progress</status>" docs/prd/*/what-next.md docs/prd/*/index.md 2>/dev/null
```

Both locations are checked deliberately. New PRDs carry the marker in `what-next.md`, but
artefacts written before that template settled carry it only in `index.md`, and a PRD that
cannot be found is a PRD that gets silently replaced.

**If any PRD directory exists:**
1. Present a numbered list — slug, name, status, and when it was last modified
2. Ask what the user wants: continue one, or start a new one alongside it
3. **Never assume.** `/prd` with no arguments used to begin a fresh interview immediately,
   which is how an existing PRD could be overwritten without anyone being asked.

**If `--resume` was passed:** the same list, but say so plainly when nothing is in progress —
`--resume` with no incomplete PRD is not an error, it just means there is nothing to resume.
Offer the complete ones and the option to start fresh.

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

**For Greenfield:**
- Ask about any tech preferences or constraints
- Present 2-3 stack options with pros/cons based on the features discussed

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

If "now": Write Given/When/Then acceptance criteria together.
If "later": Mark as TBD in what-next.md

### Phase 4: Dependencies

Ask: *"What external services, APIs, or libraries will this project depend on?"*

For each dependency capture:
- Name
- Version requirements (if known)
- Purpose/usage

### Phase 5: Optional Sections

For each optional section, ask if they want to include it:

**Motivation & Use Cases:**
*"Would you like to document the motivation and use cases? This helps communicate 'why' to stakeholders. (Skip if not needed)"*

**Competitive Analysis:**
*"Would you like to include competitive analysis? We'd document similar products and how yours differs. (Skip if not needed)"*

**Non-functional Requirements:**
*"Are there specific performance, security, or scalability requirements we should document?"*
- Only include if they mention specific concerns

### Phase 6: Validation

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

### Phase 7: Interactive Review

Present a summary of each section:
*"Let me summarize what we've captured. Tell me if anything needs revision:"*

Go through each section briefly. Ask: *"Would you like to revise anything?"*

If yes, make revisions interactively.

### Phase 8: Output

Create the folder structure and files:

```
docs/prd/[project-slug]/
  index.md
  what-next.md
  features/
    [feature-slug].md (one per feature with detailed specs)
```

**Check before writing, every time:**

```bash
test -e docs/prd/[project-slug]/index.md && echo EXISTS
```

If anything is already there, **stop and ask** — naming the files that would be replaced and
offering a different slug. Do not overwrite `index.md`, `what-next.md` or anything under
`features/` on the strength of having reached this phase.

Two different situations end up here, and only one of them is safe:

- **Resuming a PRD** you loaded in Initialization: writing back is the point. Proceed.
- **A new PRD that happens to collide** with an existing slug: two projects with similar names
  produce the same slug, and the second silently destroys the first. Ask.

If the interview was long, say what is about to be replaced *before* replacing it. A PRD is an
hour of someone's thinking; a slug collision should never be the reason it disappears.

## Output Formats

### index.md (Main PRD)

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

### what-next.md

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
  </next-steps>

  <session-notes>
    <!-- Any context helpful for resuming -->
    {{Notes about decisions made, alternatives considered, etc.}}
  </session-notes>
</what-next>
```

### features/[feature-slug].md

```xml
<feature>
  <meta>
    <name>{{Feature Name}}</name>
    <slug>{{feature-slug}}</slug>
    <priority>must-have|should-have|could-have</priority>
    <status>defined|tbd|in-progress</status>
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
