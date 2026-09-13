# Distribution and Installation — What Was Measured

**Status:** Analysis only. Nothing here is implemented. §6 is a remediation proposal.
**Date:** 2026-09-12
**Subject:** How this plugin — 15 skills, 10 agents, 3 commands — reaches a machine other than
the author's, and what breaks on each route. Measured against Claude Code 2.1.268 and the
VS Code extension 2.1.267, on Windows 11.
**Relationship to the other documents:** this is [`sdd-comparison.md`](sdd-comparison.md) **C8**
turned from a one-paragraph observation into a measurement. C8 recorded that the toolchain is
"loaded with `--plugin-dir` from a checkout, not published to a marketplace", and called the
resulting adoption ceiling real but unquantified. It is quantified here, and the answer is not
the one C8 assumed.

**Findings are numbered DP1–DP15** (distribution/packaging) so they do not collide with F, P, R,
V, C, S, A, B, E, L, U, OQ or D1–D3, all of which are in use elsewhere in `docs/skills/`.

**Verification status is stated per finding:**

- ***Measured*** — a command was run and its output is quoted or summarised here. Where a probe
  asked a model a yes/no question, a decoy name was included and had to come back absent, so the
  answer is a lookup rather than an echo of the question.
- ***External*** — from Claude Code's published documentation, not from a run here.
- ***Unmeasured*** — stated as an open question, with what it would take to close it.

**Paths in this document are placeholders.** `<checkout>` is wherever this repository is cloned;
`~` is the user's home directory. The runs behind these findings used real paths; those do not
belong in a committed file.

**What has happened since the first draft**, kept here rather than folded silently into the
findings:

| Finding | Since |
|---|---|
| DP1, DP11 | **Landed.** `marketplace.json` added, `plugin.json` filled out — commit `ee7a9fb`. |
| DP13 | **Fixed.** `setup_fixture.py` reads `meta/status` — commit `10ab174`. |
| DP5 | **Closed.** The open cell was measured; see the finding. |
| DP2 | **Corrected, and it had a fourth site.** See the finding. |
| DP15 | **Withdrawn.** It was already fixed before this document claimed it. |

---

## 1. The read gate, which decides everything else

Every route delivers the same 15 skills. They differ on one thing, and it turns out to be the
only thing that matters: **can a skill read its own bundled files?**

The skills read `references/*.md`, and read each other's `SKILL.md`, with the `Read` tool. They
also shell out to bundled scripts with `Bash`. Those two tools are gated differently, and
conflating them is what made the existing documentation wrong:

| Tool | Gated by | Consequence |
|---|---|---|
| `Bash` | the session's permission mode | scripts run wherever the plugin lives |
| `Read` | the directory allowlist | a plugin's own files are refused unless granted |

So a plugin can execute all of its scripts and still be unable to read a single one of its
reference files. That is the failure this document is about, and it is quiet: the skill stops
partway through a phase with a permission message rather than an error that names the cause.

---

## 2. The routes, compared

| Route | Usable today | Read gate | Update story | Needs a flag |
|---|---|---|---|---|
| Marketplace install, any scope | **No** — nothing to install from | **Solved** — cache is readable | `/plugin update` | none |
| `--plugin-dir` + `--add-dir` | **Yes** — the current flow | Solved by `--add-dir` | `git pull` | both, every launch |
| `--plugin-dir` alone | loads | **Breaks** mid-phase | `git pull` | one |
| Skills-directory plugin | loads | **Unsolved** | `git pull` via junction | none |
| `--plugin-dir <zip>` / `--plugin-url` | *External* | as `--plugin-dir` alone | manual | one |
| Standalone `.claude/` (not a plugin) | Yes | moot — inside the workspace | manual copy | none |

The ordering is the finding. **The route that does not exist yet is the only one that needs no
workaround**, and the route the repository documents is the only one that works today.

---

## 3. Findings

### DP1 — There is no marketplace, so there is no install. *Structural. Measured.*

`.claude-plugin/plugin.json` exists and is valid. `.claude-plugin/marketplace.json` does not, and
nothing in the repository or in `docs/` refers to one. Without it,
`/plugin marketplace add <owner>/<repo>` has nothing to read, so no `/plugin install` path exists
at any scope. A single repository may serve as both marketplace and plugin via a relative
`"source": "./"` entry (*External*), so this is a file to add, not a restructuring.

### DP2 — `--add-dir` gates `Read`, not the scripts. The documented reason is wrong. *Correctness. Measured.*

**Four sites, not the three the first draft named.** [`README.md`](../../README.md) §Use,
`CLAUDE.md`, the P50 check in `tests/test_toolchain.py`, and — found later, while fixing DP13 —
the guidance [`setup_fixture.py`](../../tests/fixture/setup_fixture.py#L184) *prints to the
operator at the start of every §5.2 run*, which is the one a person actually reads before a
measured run. All four stated that without `--add-dir` the skills cannot *run*
`resolve-output.sh`, `check-references.py` or `build-manifest.py`. Four runs, varying one thing at
a time:

| Flags | Permission mode | A bundled script via `Bash` |
|---|---|---|
| `--plugin-dir` + `--add-dir` | `bypassPermissions` | ran, exit 0 |
| `--plugin-dir` only | `bypassPermissions` | ran, exit 0 |
| `--plugin-dir` only | default | denied — "requires approval" |
| `--plugin-dir` + `--add-dir` | default | denied — "requires approval" |

`--add-dir` made no difference in either direction; the permission mode decided it. The same pair
of runs against the `Read` tool inverted cleanly: `<checkout>/schema/core.md` was refused without
`--add-dir` and returned with it.

**The advice is right and the explanation is wrong.** Both flags are needed. The reason is the
reference files the skills read, not the scripts they shell out to.

P50's *assertion* was never the wrong part and is unchanged: every line that gives
`--plugin-dir` must also give `--add-dir`. Only its stated reason moved. All four sites now say
so, and each says that `Bash` is gated by the permission mode rather than the directory
allowlist, so a reader who meets any one of them meets the whole distinction.

### DP3 — An installed plugin's cache is readable. A skills-directory plugin's is not. *Measured.*

Identical conditions throughout — unrelated working directory, no flags, default permissions:

| Delivery | `Read` of the plugin's own file |
|---|---|
| `--plugin-dir`, no `--add-dir` | refused |
| skills-directory (`~/.claude/skills/<name>/`) | refused |
| marketplace install (`~/.claude/plugins/cache/…`) | **OK** |

The skills-directory result came from a real `/breakdown` run rather than a synthetic probe: the
plugin was junctioned into `~/.claude/skills/`, loaded as `<name>@skills-dir`, and **six bundled
scripts ran clean** — `check-artefacts.py`, `check-architecture.py`, `check-repo-structure.py`,
`check-references.py`, `check-prd-size.py`, `select-features.py`. The run then stopped on a
refused `Read` of a sub-skill's own `SKILL.md`.

**The mechanism is not established.** The candidates are that the managed cache is granted
because Claude Code owns it, or that the grant follows `enabledPlugins` registration, which the
junctioned plugin never had. The outcome is measured; the cause is not.

### DP4 — Install scope does not affect the read gate. *Measured.*

`--scope project` installs into the **same** shared cache as user scope —
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` — and writes only an `enabledPlugins`
entry into the project's `.claude/settings.json`. Nothing but `.claude/` appeared in the project.
A read probe from that project returned OK and the plugin loaded.

Scope selects which settings file records the enablement, not where the files live. Project scope
is therefore the better default for a team: the enablement is version-controlled. One documented
caveat (*External*): a plugin that only the project's settings enable, from an external source,
does not auto-install — Claude Code reports it as not installed and prints the
`claude plugin install` command to run.

### DP5 — A third-party marketplace's cache is readable too. *Measured, with one cell open.*

A local marketplace was stood up (`.claude-plugin/marketplace.json`, source type `directory`)
carrying a probe plugin whose only content was a reference file holding a random token. Installed,
it landed at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, and the probe returned
the token **verbatim** — chosen randomly so a plausible-sounding answer could not fake it.

The catalog's source type only decides where the *catalog* lives; the plugin is copied into the
cache regardless, and the cache is what carries the read access.

| Marketplace source | Owner | Cache readable |
|---|---|---|
| `github` | Anthropic | OK — `superpowers` 6.3.0 |
| `directory` | third party | OK — the probe |
| `git` / `https` | third party | **OK** — see below |

The last row was open in the first draft and could not be closed locally: `marketplace add`
rejects a `file://` URL with *"Invalid marketplace source format. Try: owner/repo,
https://..., or ./path"*, so it needed a real remote. **It is now closed.** With this
repository's own `marketplace.json` pushed to a branch and added as
`https://github.com/<owner>/<repo>.git#<branch>`, Claude Code recorded it as `"source": "git"`,
cloned it, installed to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` with a
`gitCommitSha`, and both `schema/core.md` and `skills/breakdown/references/layer-definitions.md`
read **OK** under default permissions with no flags.

All three rows now pass. The grant tracks the cache, and neither the marketplace's owner nor its
source type changes that.

### DP6 — Relative reference citations do not lift the gate. *Measured, with a control.*

Every installed plugin surveyed cites its reference files by bare relative path — `superpowers`
(5 files), `chrome-devtools-mcp` (7), `claude-md-management` (3), `skill-creator` (1) — with zero
absolute paths and zero `${CLAUDE_PLUGIN_ROOT}` among them. This toolchain instead builds an
absolute `{skill_dir}/…` path. The hypothesis was that the relative form is what makes the
ecosystem's plugins readable, and that adopting it would fix `--plugin-dir` and skills-dir too.

It is false. A probe plugin citing `references/probe.md` exactly as `superpowers` does:

| Run | `--add-dir` | Result |
|---|---|---|
| test | no | `FAILED … you haven't granted it yet` |
| control | yes | the token |

A relative citation resolves to an absolute path inside the plugin and is permission-checked like
any other. It is an authoring convention, not a permission bypass — `superpowers` works because
its files sit in the granted cache. **No citation change fixes any route.**

Incidental and useful: a bare relative reference path resolves against the **skill's own**
directory, `skills/<name>/references/…`, not the plugin root. This repository's layout already
matches, so switching citation style would resolve correctly and buy nothing.

### DP7 — `--plugin-dir` copies nothing and registers nothing. *Measured.*

After eight sessions launched with `--plugin-dir` from a scratch workspace: no `.claude/`
directory in the workspace, no entry in `installed_plugins.json` or `known_marketplaces.json`,
and zero occurrences of the plugin's name in `plugin-catalog-cache.json`. It is a live view of the
checkout, per session, with no footprint. That is a real advantage for the author — one clone,
`git pull`, every workspace current — and a total barrier for anyone else.

### DP8 — Nothing loads the plugin implicitly. *Measured.*

Two candidate conveniences, both absent. A session started **inside** the plugin's own repository
with no flag reported the skills absent, so there is no workspace-root auto-detection. And no
settings file enables it: `enabledPlugins` lists only marketplace-installed plugins, and the
project's `.claude/settings.local.json` carries permissions, `additionalDirectories` and a hook,
with no plugin keys. Availability comes from the flag and nothing else.

### DP9 — Path formats are forgiving except for one quiet failure. *Measured.*

| Launched from | Form | Loads |
|---|---|---|
| PowerShell | backslash, quoted | yes |
| PowerShell | forward slash, quoted | yes |
| PowerShell | absolute path containing a space, quoted | yes |
| Git Bash | backslash, quoted | yes |
| Git Bash | backslash, **unquoted** | **no — and silently** |
| Git Bash | forward slash | yes |
| Git Bash | MSYS `/c/…` | yes |
| either | relative | yes |

Only the unquoted-backslash case fails, and it fails invisibly: the shell strips the separators
before Claude Code sees the argument, and the session starts **exit 0, no warning**, with the
plugin simply absent.

Documentation should use **forward slashes in double quotes**. Single and double quotes behave
identically in PowerShell and Git Bash for a path with no `$` in it, but `cmd.exe` does not treat
the apostrophe as a quote character at all — a single-quoted path containing a space split into
two arguments with the quote marks left in the value. Double quotes are the only style that
survives all three shells.

### DP10 — The VS Code extension cannot pass the flags. *Measured.*

The installed extension (2.1.267) contributes 16 configuration keys, none for plugin directories
or CLI arguments. The nearest levers are `claudeCode.environmentVariables`, which takes
environment variables only, and `claudeCode.claudeProcessWrapper`, a wrapper executable that could
inject flags. So the `--plugin-dir` route is terminal-only in practice, and a wrapper shim is the
only way to reach the extension — which is itself an argument for a route that needs no flags.

### DP11 — `plugin.json` is valid but thin. *Consistency. Measured.*

It declares `name`, `description`, `version` 2.0.0, `author` and `keywords`, and
`tests/test_toolchain.py` already guards the first three. Only `name` is required (*External*).
Absent: `license`, `repository`, `homepage`, `displayName` — all informational, and all of them
what a marketplace listing shows a stranger. `claude plugin validate` warns about a missing plugin
`author` and a missing marketplace `description`, so the tooling will ask for some of this anyway.

### DP12 — `resolve-output.sh` refuses a relative `--output-dir`. *Measured. Incidental.*

Encountered while driving a real `/breakdown`: the script requires an absolute path and declines
to guess between the caller's working directory and its own. The refusal is correct and the
message explains itself, but a first-time user types a relative path, so it belongs in whatever
install documentation is written.

### DP13 — ~~The fixture cannot be built from clean.~~ **Fixed** (`10ab174`). *Blocking. Measured. Unrelated to distribution.*

`python tests/fixture/setup_fixture.py --clean` refuses:

> fixture PRD is invalid: what-next.md has no `<status>in-progress</status>` — /prd --resume greps
> for exactly that (F3)

The fixture is correct: the current schema fixture's `what-next.md` carries exactly that element,
inside `<meta>`. [`setup_fixture.py:127`](../../tests/fixture/setup_fixture.py#L127) reads
`wn.findtext("status")`, which searches only direct children of `<what-next>`. It needs
`meta/status`. `git log -L` on that line shows it arrived with the fixture's first commit and had
never been edited — so this broke when the fixture moved the element into `<meta>` at schema-4,
and stayed invisible because the built fixture persists in `%TEMP%` across runs and nothing
rebuilt from clean.

**Fixed in `10ab174`, and it was not the one-word fix it looked like.** Two sibling readers
already accepted both positions — `test_toolchain.py:2374` as `meta/status or status`,
`run_5_2.py:161` as `status or meta/status`, the former's message even spelling out "under
`<meta>` or directly under `<what-next>`". This was the only site reading one position, and the
wrong one; it now matches its siblings rather than merely moving to the current position.
Verified three ways: provoked (value changed to `complete`, exit 1 with the check's own named
message, so it is still live rather than permissive), enumerated (both positions accepted,
element-absent and wrong-value both rejected), and built (`--clean` completes, exit 0).

### DP14 — There are no installation instructions, which is currently correct. *Measured.*

`README.md` §Use documents the two-flag developer flow and nothing else. No install section exists
anywhere in the repository. Given DP1 that is honest rather than an omission — there is no
installed path to document — but it becomes the gap the moment a marketplace exists, and per DP3
the instructions will need more than an install command on at least two of the routes.

### DP15 — ~~`README.md` §Status understates the suite by a factor of five.~~ **Withdrawn. It was already fixed.**

The claim was that §Status said **31 checks** against **163** `@check` functions. Both numbers
were real when read and neither was current when written. Commit `b94e9e8`, *"Four derived counts
in README.md, outside the carve-out that keeps three"*, had already replaced the count with
"every check verified to fail when its fix is reverted" — the numberless form this finding was
about to propose. The suite now reports **170**, and `@check` now counts 170 too, so the second
number had moved as well.

**The error was a failure to reconcile, not a failure to measure.** Both counts were read early
in the session; five commits landed in the repository between that reading and this document
being written, and nothing re-read the file. A count measured against a tree that has since moved
is a ghost, and this is the finding that proves the rule rather than an exception to it. It is
recorded rather than deleted because a withdrawn finding is the only evidence the finding was ever
checked — the convention `tests/fixture/prd/SCHEMAS.json` uses for its wrong predictions.

---

## 4. Method note — one invalid result, and what caught it

The DP6 probe was run twice. The first fixture placed `references/` at the **plugin root**; both
arms failed, which reads as a clean negative. It was not one: the control failed with
`File does not exist` rather than a permission refusal, and that is what exposed both that the
bare path resolves against the skill's directory and that the fixture had put the file somewhere
the skill would never look.

**A negative result with a failing control measures nothing.** Both arms are reported in DP6 for
that reason, and the positive control is the only thing separating "the gate refused it" from "my
fixture was wrong".

The same discipline was needed earlier. The skills-directory `/breakdown` run's own summary
reported `READS_REFUSED=NONE`. Its nine session transcripts contained the refusal. **The
self-report was wrong, and the finding in DP3 comes from the transcripts.**

---

## 5. What is not measured

1. ~~**A `git`-sourced third-party marketplace** (DP5).~~ **Closed.** Measured by pushing this
   repository's own `marketplace.json` to a branch and installing from it over GitHub. It was the
   load-bearing inference behind §6 and it held.
2. **Whether `additionalDirectories` in settings supplies a permanent read grant.** `--add-dir` is
   measured to lift the refusal; its settings equivalent is untested. This matters only if the
   skills-directory route is to be documented rather than dropped.
3. **Why the managed cache is readable and `~/.claude/skills/` is not** (DP3). The outcome is
   solid; a mechanism would tell us whether the cache grant is safe to rely on.
4. **`--plugin-dir` with a `.zip`, and `--plugin-url`.** Documented (*External*), never run here.

---

## 6. Remediation, in dependency order

1. ~~**Add `.claude-plugin/marketplace.json`**~~ — **done, `ee7a9fb`.** This repository serves as
   its own marketplace via `"source": "./"`, modelled on `superpowers` 6.3.0, which ships exactly
   that beside its own `plugin.json`. Per DP3–DP5 this is the fix for the read gate, not merely a
   distribution mechanism. `claude plugin validate` passes with no warnings.
2. ~~**Close §5 item 1**~~ — **done.** Pushed to a branch, added over GitHub, installed, read.
3. ~~**Correct DP2's explanation**~~ — **done**, in all **four** sites, one more than this
   document originally named. Both flags stay; the reason changes from the scripts to the reads,
   and each site now also states that `Bash` is gated by the permission mode.
4. **Write the install section.** Leading with the marketplace, and carrying the `cmd.exe`-safe
   quoting convention from DP9 and the absolute-path requirement from DP12. The only item still
   open.
5. ~~**Fill in `plugin.json`**~~ — **done, `ee7a9fb`.** `license`, `repository`, `homepage`,
   `displayName`.
6. ~~**Fix `setup_fixture.py:127`**~~ — **done, `10ab174`**, and see DP13 for why it was not the
   one-word fix it appeared to be.
7. ~~**Delete or recompute the `31 checks` claim**~~ — **withdrawn.** Already done in `b94e9e8`
   before this document claimed otherwise. See DP15.

**Still open:** item 4, plus §5 items 2, 3 and 4 — none of which block an install.
