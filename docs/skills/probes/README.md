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

## OQ1, measured separately (2026-08-24)

Open question 1 of [`../plugin-2.0-plan.md`](../plugin-2.0-plan.md) — *can a command
invoke a script bundled in its plugin?* — was answered by a one-off spike rather than
by the harness above, because it needs a **plugin loaded with `--plugin-dir`** rather
than skills dropped into a project.

| Question | Answer as measured |
|---|---|
| Can a command invoke a bundled script? | **Yes**, via `${CLAUDE_PLUGIN_ROOT}` |
| Who expands `${CLAUDE_PLUGIN_ROOT}`? | **The harness**, before the model sees the command |
| Is `CLAUDE_PLUGIN_ROOT` set in the script's environment? | **No** — unset in the spawned shell |
| Does a bare relative path work? | No. `sh: scripts/probe.sh: No such file or directory` — cwd is the project |
| Can the model find the script unaided? | Only by brute force — 8 tool calls including `find /` |

**The mechanism, which is the part worth keeping.** The spike's script recorded `$0`,
`pwd` and `$CLAUDE_PLUGIN_ROOT` into a marker file. It ran with an absolute plugin path
in `$0` while `CLAUDE_PLUGIN_ROOT` was **unset** in its environment — so the variable is
not exported to the shell. The session transcript settles where it went: the *user-role*
message already contained the fully-resolved absolute path, so substitution happens at
command-expansion time and the model simply ran what it was handed.

That distinction is the actionable half. **Text substitution inside a command body works;
a script reading `$CLAUDE_PLUGIN_ROOT` from its own environment gets nothing.** Pass the
path as an argument if a script needs it.

The no-path control is the reason not to rely on the model finding things: it succeeded,
but only after globbing the working directory (nothing — the plugin is outside it),
searching `~/.claude`, running `find /` across the filesystem, reading the plugin config,
and finally guessing candidate base directories. It worked because the script had a unique
name on a machine where the path was guessable. It is not a mechanism.

### Reproducing it

```bash
# a plugin with .claude-plugin/plugin.json, commands/probe-root.md, scripts/probe.sh
# where the command body contains, literally:
#     sh "${CLAUDE_PLUGIN_ROOT}/scripts/probe.sh" root
cd <some-empty-project-dir>
claude -p "/probe-root" --plugin-dir <plugin-dir> \
       --allowedTools Bash --permission-mode acceptEdits --output-format json
```

Grade on the marker file the script writes, not on what the model says it did. Check
`permission_denials` in the JSON result is empty before believing a negative — a denied
`Bash` is what made run 1 of §5.2 unreadable for a day.

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
