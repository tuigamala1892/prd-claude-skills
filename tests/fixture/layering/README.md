# Layering fixtures — item 43's third arm

**These are the artefacts of open question 7's experiment**, kept because the answer was
LOAD-BEARING and the decision table says that outcome buys a third fixture arm. They are the
input to `check-layering.py`'s regression check.

**Generator output, not hand-built, and that is the point.** A fixture written by hand to match
the checker validates the code against itself — the defect
[`a-fixture-must-not-agree-with-the-reader`](../prd/SCHEMAS.json) exists to prevent, and the same
one item 21 hit when its probe PRD explained the experiment to the model under test. Every task
file here came out of a real `/breakdown` run on the `schema-6` `link-shelf` PRD, on 2026-09-08.

| Directory | The run that produced it | What it is for |
|---|---|---|
| `sound/` | no `architecture.md`; the shipped default graph | The **negative control**. 10 tasks, `0-setup → 1-foundation → 2-backend → 4-integration`, and **zero** forward references. A check that fires here is wrong |
| `inverted/` | an `architecture.md` declaring the five default layer names with the dependency direction reversed | The **positive control**. 14 tasks and **16** forward references — `L3-*` backend endpoints importing `Link`, `get_db` and `db_session` from `4-foundation`, which the declared graph runs *after* them |
| `inverted-halted/` | the same inverted graph, second run | No tasks at all. `plan-layers` silently reordered the declared graph and `generate-tasks` refused to proceed. Kept because it is the evidence for **P52** and for the finding that the two runs disagree |

## Why `inverted/` is trustworthy despite its provenance

Its `architecture.md` prose *told* the model the direction was inverted, which contaminated it as
a measurement of how the toolchain reacts — that is why `inverted-halted/` exists, and why the
verdict rests on the pair rather than on this arm alone.

**It is not contaminated as a fixture for `check-layering.py`.** What the check reads is the task
set's own dependency structure: task `L3-003` names an interface that task `L4-002` exports, and
the declared graph puts layer 4 after layer 3. That relation is a fact about the files, whatever
the run was told. The prose affected *how the toolchain behaved*, not *whether these 16 edges
point backwards*.

## What must stay true of them

**Do not regenerate these to make a check pass.** They are frozen evidence of one measurement. If
`check-layering.py` stops firing on `inverted/`, the check has broken, not the fixture — the same
rule `SCHEMAS.json` states for a superseded schema version.

The counts are asserted by the suite rather than written here alone: `sound/` must yield 0 and
`inverted/` must yield at least one, because a positive control that has drifted to zero is a
check with no subject and would pass in silence.
