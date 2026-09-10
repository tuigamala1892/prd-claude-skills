# Findings — every one the plan named, and what became of it

[`plugin-2.0-plan.md`](plugin-2.0-plan.md) states the findings; this file says which are closed,
which were retracted, and which nobody settled. **It exists because those states were
indistinguishable.** P9 was explicitly *retracted* — a predicted failure with no live instance —
and P13 was *closed* by measurement; both were simply absent from every index, so nothing could
tell a decision from an omission. And **P58–P68 had no definition at all**: eleven findings whose
claim existed only in commit messages.

*One correction, made while building this.* The proposal for this file cited P22 as never
settled. It is closed — item 32's rendered task summary — and the row says so. What was never
taken is the volume *projection* P22's paragraph rests on, which is a different thing from the
finding.

That is the same rule three other files in this repository already apply, to everything except the
thing the plan is organised around:

| File | Distinguishes |
|---|---|
| [`readers.md`](../../schema/readers.md) | an element with no reader, from one with a recorded reason it has none |
| [`checks.md`](../../schema/checks.md) | an assertion with an owner, from an ownerless row kept deliberately |
| [`parity.md`](../../schema/parity.md) | a settled asymmetry, from one marked `open` |
| **this file** | a finding that was closed, from one that was retracted, from one nobody answered |

---

## How to read the table

| Column | Holds |
|---|---|
| **Finding** | Its id. The plan defines each under a `**PN — claim**` heading |
| **Claim** | What was found, in a line. Not the fix |
| **Status** | `closed` · `retracted` · `open` · `superseded` |
| **Settled by** | A regression check, or the item that closed it. Required for every status |

**Most rows name a check, and that is the strongest form.** A finding guarded by a check in
`tests/test_toolchain.py` cannot quietly come back; one closed by an item is closed on the day
that item landed and nothing watches it since.

**`retracted` is not `closed`.** P9 is the reason this column has four values: it was a predicted
failure that turned out to have no live instance, and recording that as *closed* would claim a fix
that never happened — while deleting the row would lose the retraction, which the plan explicitly
kept rather than removing.

**A note on the id space.** `P0`, `P1` and `P2` are also the criterion priority levels (core §4),
so a bare grep for `P2` finds both. The findings are the ones defined by a heading; the levels
always appear as `P0|P1|P2` or inside a `priority=` attribute. `P0` is **not** a finding.

**P58–P68 had no claim heading when this file was built.** They came out of the sixth crossing
and the items that closed it, and existed only as `finding=` tags in the suite and words in
commit messages — eleven findings nobody could look up. They were **placed into the plan at
sections S, T and U** in the same phase, so the claims below are theirs rather than their checks'.
That is the remedy and the rule: a finding gets a heading in the plan and a row here, and neither
substitutes for the other.

---

## The table

| Finding | Claim | Status | Settled by |
|---|---|---|---|
| **P1** | MoSCoW priority is extracted, then discarded. Won't-have features are built | closed | `the P1 fixture reads as a product, not as a test` |
| **P2** | `<acceptance-criteria>` has no consumer on the PRD path | closed | items 16, 17, 30 — *the pipeline stops discarding the document*. Criteria reach the task and `check-coverage.py` reads them. **Residue:** the plan's own note at §3 still says *runtime confirmation still owed … see item 21*, and item 21's run addressed P1. Whether it settles this one is unrecorded |
| **P3** | `priority` means two unrelated things | closed | item 34 — a criterion's `priority` is `P0\|P1\|P2`, deliberately not MoSCoW, so no flag or report line is ambiguous about which level it means |
| **P4** | `<notes>` has no consumer anywhere | closed | `` `<considerations>` is unread by design, and says so `` |
| **P5** | The first step of `/breakdown` does not fit in its model's context | closed | `an oversized PRD is refused before a prompt is built` |
| **P6** | The `<status>` enum cannot express what real use needs | closed | item 45 and [core](../../schema/core.md) §3 — four things were called `status`; three were renamed, and each enum is now validated separately |
| **P7** | `<status>` has no definitions, and nothing checks it | closed | item 3 — `check-status.py`, which derives a ceiling from a feature's own content and reports where the declared value exceeds it |
| **P8** | Priority is stored twice | closed | `the feature template carries intent, significance, and no second priority` |
| **P9** | Nothing reconciles the index against the feature directory | retracted | **No live instance.** Read first as a dropped must-have, then as rename residue; it was neither — the sample was refreshed by overwriting the folder without clearing it, so the file was a leftover from a previous copy. A predicted failure again, and `check-rename.py` guards it |
| **P10** | `what-next.md` is prose markdown where the spec says XML | closed | `every artefact is the shape its own schema version describes -- by running it` |
| **P11** | `index.md` has grown sections the template does not define | closed | `feature dependencies are declared edges, and ordering is derived from them` |
| **P12** | Intra-feature phasing exists in prose, with no slot for it | closed | `what-next.md's gap list is derived, and staleness is an exit code -- by running it` |
| **P13** | Excluded features carry an undocumented `<rationale>` element | closed | item 3 — `check-status.py` requires `<rationale>` on an `excluded` feature, so the element the corpus invented is now specified and asserted |
| **P14** | Excluded and superseded features keep a stale priority | closed | item 5 — `<priority>` is gone from the feature file entirely; the index entry is the only place it lives, so it cannot go stale in two places |
| **P15** | Tasks have no link back to the feature they came from | closed | ``a task names the feature and criteria it came from, and `<priority>` is left alone`` |
| **P16** | `/prd`'s guards are prose, in a repository that has learned better | closed | `` `/prd`'s overwrite guard is an exit code, not a paragraph `` |
| **P17** | The greenfield path has no architecture channel, in either direction | closed | `architecture.md has a producer, and it runs before dependencies` |
| **P18** | The toolchain's architectural opinions are vendored into the plugin, and no project can override them | closed | `a rule file that cannot be obeyed stops the run -- by running the guard` |
| **P19** | On the PRD path, ambiguity has no channel — and the design actively suppresses it | closed | `uncertainty has a channel that survives the handoff, and review lets it through` |
| **P20** | Nothing reconciles the task set against the PRD | closed | `the task set is checked against the document it came from -- by running it` |
| **P21** | There is no path for a change too small to be worth the ceremony | closed | items 31 and 49 — the layer set derives from content with no threshold, and `<scope>`/`<confidence>` give the small change somewhere to say it is small |
| **P22** | Self-containment makes the task set harder to review than the PRD it came from | closed | `the task set is reviewable without opening every task -- by running it` |
| **P23** | The criterion format cannot express most of what a requirement needs to say | closed | `a criterion is one EARS sentence with a pattern and a priority` |
| **P24** | The PRD cites three artefact classes the toolchain cannot see | closed | `dangling ADR / OQ citations are refused, and named` |
| **P25** | There is no design step, and no way to say which requirements would need one | closed | `the gate asserts three things by name, and the switch decides only whether it stops` |
| **P26** | Nothing checks that a feature discharges what other features expect of it | closed | `a feature's declared definition is checked against its own content -- by running it` |
| **P27** | There is no rename operation, and a slug lives in five places | closed | `a rename finishes, or leaves the PRD exactly as it was` |
| **P28** | One version where two are needed, and the one schema version there is, is wrong | closed | `exactly one PRD schema is current, and each has its fixture` |
| **P29** | `status` means three unrelated things, and two of the vocabularies overlap | closed | `three status vocabularies, three distinct names -- and the fourth keeps the word` |
| **P30** | The two paths define overlapping schemas independently, and neither cites the other | closed | `the schema core is one definition that both paths cite -- and its citations resolve` |
| **P31** | CRD requirements and acceptance criteria are unlinked, and the criteria carry no priority | closed | `a CRD carries one list, not two -- and the migration moves it, by running it` |
| **P32** | The CRD path has no deferral mechanism and no resume | closed | `` `/crd` cannot silently replace a CRD, and `ready` cannot outrank its gaps -- by running it `` |
| **P33** | Layer selection is derived on one path, hardcoded on the other, and wrong on both | closed | `the layer set is derived from content, not taken as a list` |
| **P34** | `/prd` does not know what project it is writing into | closed | `` `/prd` asks what the repository knows before asking the user `` |
| **P35** | `<rules>` has the right bones and three CRUD-shaped leaves | closed | `PROJECT.md requires a registry, not the REST pair -- by running the guard` |
| **P36** | The execution model assumes one repository, and says so nowhere until it fails | closed | `multi-repo is refused in Phase 1, with what would be needed` |
| **P37** | The ledger reports a merge and implies a build | closed | `the ledger records what was verified, not that it was` |
| **P38** | `execute-layer` maintains a file that is rebuilt from git on every write | closed | item 60 — `execute-layer` stopped maintaining a file that is rebuilt from git on every write |
| **P39** | `plan-layers` forbade the derivation it performs | closed | `the layer set is derived, and nothing instructs otherwise` |
| **P40** | `task-format-spec.md` required a layer its own constraints could not express | closed | `the task schema admits every layer the layer graph can produce` |
| **P41** | `/execute` may rewrite the acceptance criteria it is being judged against | closed | `a task file edited mid-run is a stop with a diff -- by running it` |
| **P42** | the generator does not know the execution model | closed | `the generator is told where its verification commands will run` |
| **P43** | `<source-feature>` is single-valued, and an integration task spans features | closed | `a task names every feature it descends from, and the manifest carries all of them` |
| **P44** | `/execute` iterates a layer list that stopped being true three items ago | closed | `the layer set is the plan's, not a list in /execute's prose -- by running it` |
| **P45** | the task-file guard protects a dispatch, and a run is not a dispatch | closed | `a snapshot that replaces another says what changed between them -- by running it` |
| **P46** | `<review>` has a reader, a fixture and a migration rule, and no producer | closed | `the review the gate requires has a producer on the authoring path -- by running it` |
| **P47** | the assertion registry drifted, in the one direction nothing checks | closed | `every file that runs an owning script is listed as its caller -- by running it` |
| **P48** | two documented commands use a path that cannot resolve | closed | `a documented invocation names the plugin root, never a bare relative path` |
| **P49** | three shipped artefacts describe a state the toolchain has left | closed | `no shipped artefact describes a state the toolchain has left -- by running it` |
| **P50** | the documents that onboard a reader describe a smaller project than exists | closed | `the documents that describe the layout describe the one on disk -- by reading both` |
| **P51** | a wrong layer graph produces an unbuildable task set, and nothing mechanical notices | closed | `no task depends on a layer that runs after it -- by running it on both controls` |
| **P52** | `breakdown-plan-layers` resequenced the declared graph, which its own spec forbids | closed | `a declared layer order is obeyed, not improved on -- by running it on both controls` |
| **P53** | a CRD declares a schema change and no task ever sees it | closed | `a CRD's schema contracts have a route into the task that implements them` |
| **P54** | the significance flag exists on one path and is unsayable on the other | closed | `a CRD can declare architectural significance, and something reads it -- by running it` |
| **P55** | item 29's execution stop was unreachable on the CRD path | closed | `the gate's assertions reach a CRD, not only a PRD directory -- by running it` |
| **P56** | a CRD's architectural significance never reached the gate, and item 76 built half of it | closed | item 77 — the CRD branch reported significance under `NOTE` while the gate filtered for `STALE`, so the screen fired and nothing downstream acted |
| **P57** | a live run wrote scratch files into the toolchain checkout | closed | `a live run writes nothing into the toolchain, and every harness proves it` |
| **P58** | a CRD's `<gaps>` were never validated, and a typo defeats item 29 there | closed | `a CRD's <gaps> are validated by the script that owns the assertion -- by running it` |
| **P59** | the gate reports a pass it has not established, in two ways | closed | ``the gate never reports `blocked OK` for an assertion it could not make -- by running it`` |
| **P60** | item 35's third direction has never seen a CRD | closed | `the significance-candidate screen reaches a CRD, not only a PRD -- by running it` |
| **P61** | capability parity is recorded and enforcement parity is not | closed | ``every assertion says which paths it reaches, and each `both` is probed by running it`` |
| **P62** | `/breakdown` names its document placeholder for one of the two shapes | closed | `a skill that takes either document does not name its placeholder for one of them` |
| **P63** | both `PROJECT.md` producers omit a required attribute, and the validator has no branch for it | closed | `a feature declares its build state, and an unplaceable file still says why -- by running it` |
| **P64** | nothing asserts a task file is well-formed XML, and three readers hide it in turn | closed | `a task file parses, and every reader that cannot read one says so -- by running it` |
| **P65** | item 49's only reader could not see its input, and reported that as agreement | closed | `the analysis fields a check reads are named where the analysis is written -- by running it` |
| **P66** | the manifest does not carry what `/execute` documents reading | closed | `the manifest carries what /execute reads, and its reader knows what its producer writes` |
| **P67** | a format table that can be followed to the wrong answer | closed | `a PROJECT.md feature carries the elements the format marks required -- by running it` |
| **P68** | the findings have no registry, and the plan is organised around them | closed | `every finding the plan names has a status, and a closed one names where it was settled` |
| **P69** | the CRD path's unbounded input is generated from a codebase, and nothing measures it | closed | `PROJECT.md fits the prompt it is about to be sent in -- by running it` |

---

## Adding a row

**A finding gets a row on the day it is named, not on the day it is closed.** An open row with a
reason is a fact about the project; a finding nobody wrote down is the thing this file exists to
prevent — which is exactly what happened to P58–P68, eleven times in two days.

**Give it a claim heading in the plan too.** The check name is a serviceable stand-in and it is
not the same thing: a check says what is guarded, a claim says what was wrong.
