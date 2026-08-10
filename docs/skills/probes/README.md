# Phase 0 probe harness

The measurements behind §3.5 and finding **F13** of
[`../toolchain-assessment-and-plan.md`](../toolchain-assessment-and-plan.md).

These answers are specific to a Claude Code version. Frontmatter handling is
harness behaviour, not documented API, so **re-run these before trusting the
conclusions on a newer Claude Code** rather than assuming they still hold.

## What it establishes

| Question | Answer as measured |
|---|---|
| Is `allowed-tools` honoured on a skill? | No. It is a *command* key. In a skill it restricts nothing **and disables `context: fork`** |
| Does `tools:` restrict a skill? | No. A fork declaring only `Read, Glob, Grep` still wrote a file, 3/3 |
| Is `agent:` honoured? | Only together with `context: fork` |
| Skill `model:` vs agent `model:` | The **skill's** wins |

## Running it

Requires the `claude` CLI on PATH and Python 3.9+. About 45 runs total, a few
minutes wall clock.

```bash
python build_probes.py --iteration 1     # generate probe project + run plan
python run_probes.py   --iteration 1     # execute
python grade_probes.py --iteration 1     # grade and print the table
```

Repeat for `--iteration 2` and `--iteration 3`. Add `--salt <anything>` to
`run_probes.py` when re-running, since session ids are derived deterministically
and the CLI refuses to reuse one.

Everything is generated under `--workdir`, which defaults to a directory in the
system temp dir. `build_probes.py` **refuses to generate inside this repository** —
finding F4 is precisely "generated output leaked into the toolchain tree".

## The three iterations

| Iteration | Runs | Purpose |
|---|---|---|
| 1 | 16 | Everything **without** `context: fork`. Establishes that an unforked skill is text injected into the caller, so no execution-governing key can apply. Iteration 1 alone is misleading — it makes every key look inert |
| 2 | 14 | The same questions **with** `context: fork` — the configuration the toolchain actually uses. Source of the F6 precedence answer |
| 3 | 15 | Reproducibility of the fork-breaking result: 5 frontmatter variants × 3 repetitions |

## Design points worth preserving

Each of these exists because its absence produced, or would have produced, a wrong
conclusion:

- **Unique `SKILLTOKEN` in every probe body.** Without it, "no file was written" is
  indistinguishable from "the skill was never loaded", and the result is
  unfalsifiable.
- **A control arm per question**, differing only in the key under test. Iteration 1's
  flat results were only interpretable because the controls were equally flat.
- **Decoy names in availability checks.** Asking a model "is X available" invites an
  echo of the question; including names that do not exist proves it is a real lookup.
  This is what caught the commands silently failing to register.
- **Model identity from `modelUsage`, never self-report.** Models misreport their own
  identity.
- **`isSidechain` is not a fork signal** — it stays `false` for forked skill
  execution. Use `toolUseResult.status == "forked"`.
- **One project copy per run.** The control arm writes the same filename across
  several evals, so shared state lets one run's output be mistaken for another's.

## What is not committed

The raw results — roughly 2.3 MB of transcripts across 375 files — are not kept.
The conclusions are recorded in the assessment, and the transcripts are only
meaningful next to the Claude Code build that produced them. Re-running is cheap.
