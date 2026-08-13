# prd-claude-skills

A Claude Code plugin for taking a product idea through to merged code: capture
requirements, break them into self-contained implementation tasks, execute those
tasks in parallel git worktrees, and handle change requests against the result.

## Workflows

| Command | Purpose |
|---|---|
| `/prd` | Interview-driven Product Requirements Document, written to `docs/prd/<slug>/` |
| `/breakdown` | Turn a PRD into layered, self-contained XML task files plus a manifest |
| `/execute` | Run the tasks layer by layer — parallel worktrees, TDD, independent verification, sequential merge |
| `/crd` | Change Request Document workflow for changes against an existing codebase |
| `/crd-context` | Build and incrementally maintain `PROJECT.md` codebase context |

`/execute` is hierarchical: `execute` → `execute-layer` → `execute-batch` →
`execute-task` → `execute-verify`, with `execute-merge` draining a sequential
merge queue so parallel tasks cannot conflict on merge.

## Layout

```
.claude-plugin/plugin.json   plugin manifest (name, version, author)
skills/<name>/SKILL.md       15 skills, some with references/
agents/*.md                  8 subagent definitions
commands/*.md                3 slash commands
docs/skills/                 assessment and remediation notes
docs/skills/probes/          harness that measured the frontmatter behaviour
tests/                       regression suite
```

## Tests

```bash
python tests/test_toolchain.py              # static checks, fast and offline
python tests/test_toolchain.py --behaviour  # + plugin-load check (needs `claude`)
```

Standard library only. Checks encoding a fix that has not landed yet are marked with
the remediation item that will fix them; they report as known and do not break the
build, but fail the run once they start passing, so the marker gets removed and the
check becomes a permanent guard. See [`tests/README.md`](tests/README.md).

## Use

During development, load the plugin from a checkout:

```bash
claude --plugin-dir /path/to/prd-claude-skills
```

The skills, agents and commands then resolve without copying anything into the
target project.

## Running unattended

`/execute` runs for hours and spawns one subagent per task. Every one of those
subagents needs `Bash` — a task that cannot run `git` cannot create its worktree, and
will quietly do the work in the main tree instead. That failure is silent and it cost
this project five end-to-end runs to diagnose, so it is worth setting up properly.

**Do not put the grants in skill frontmatter.** `allowed-tools:` in a `SKILL.md` looks
like the right home and is not:

- it pre-approves tools only when a user types `/skill-name` directly, not when the
  model reaches the skill through the `Skill` tool
  ([#67198](https://github.com/anthropics/claude-code/issues/67198)), and most of this
  toolchain's skills are reached the second way;
- it is reported not to grant `Bash` reliably even then
  ([#14956](https://github.com/anthropics/claude-code/issues/14956), open since
  December 2025, whose own workaround is the global allow list);
- and its presence silently disables `context: fork`, which is finding **F13** — the
  most severe defect this repository has found.

Put them in `settings.json` `permissions.allow` instead. It works on both invocation
paths and does not interact with forking:

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(git:*)",          // worktrees, branches, merges - the whole pipeline
      "Bash(python:*)",       // bundled scripts and project test runs
      "Bash(sh:*)",           // create-worktree.sh, record-task.sh
      "Bash(pytest:*)",       // whatever your tasks' <verification> actually runs
      "Bash(ls:*)", "Bash(cat:*)", "Bash(find:*)", "Bash(grep:*)", "Bash(test:*)"
    ]
  }
}
```

On Windows the agents also reach for `PowerShell`; add it if you see prompts.

That list is taken from a real 18-task run rather than guessed — its subagents made 645
`Bash` calls, of which the largest groups were `python` (177), `git rev-parse` (57),
`git status` (26), `git branch` (21), `git worktree` (17) and `git merge` (13), plus
`sh` (32) for the bundled scripts.

Two honest caveats. The exact pattern syntax is worth confirming with `/permissions` in
your own setup — and the §5.2 harness runs under `--permission-mode bypassPermissions`,
so this narrower path is *not* covered by any test here. If a run produces commits
directly on your base branch with no `worktree-*` branches, permissions are the first
thing to check.

## Status

**The pipeline works end to end, and reports itself honestly.** Runs 6 through 9 of the
§5.2 suite all passed on the reference fixture: 18 tasks, **18 merge commits — one per
task**, every worktree created by the caller, independent verification running per task,
and the produced application passing 88 of its own tests. Run 9 added the last piece —
`execute-state.json` is now generated from the ledger and git, and agreed with both for
the first time. See
[`docs/skills/toolchain-assessment-and-plan.md`](docs/skills/toolchain-assessment-and-plan.md)
for the full assessment, including the four runs before those that did not.

Fixed and verified under a real run:

- ~~All 15 skills declare `allowed-tools`, which stops `context: fork` working.~~
  **Fixed** (4.11, F13). That key is a *command* key; in a skill it restricted nothing
  and silently disabled forking, so for the life of this toolchain no skill forked,
  `agent:` never fired, and no skill's `model:` applied.
- ~~`/execute` cannot run against a repository with no remote.~~ **Fixed** (4.8, F1).
- ~~The generated Layer 0 task deletes the target's `.git`.~~ **Fixed** (4.7, F2).
- ~~Forked skills dispatched work in the background and returned before it finished.~~
  **Fixed** (4.12, F17). A fork ends when its turn ends, so "dispatch and wait" returned
  immediately with the work outstanding and the parent re-implemented everything inline.
- ~~`execute-task/SKILL.md` was never loaded at all.~~ **Fixed** (4.15, F20). It was
  *named* in an agent prompt, where a slash command is inert text. The worktree is now
  created by the caller and its path passed in.
- ~~`execute-state.json` invented its own numbers.~~ **Fixed** (4.16, F16). Completion is
  recorded as a commit SHA and verified with `git cat-file -e`; counts are derived from
  git, never incremented. `--resume` skips only tasks whose commits still exist.
- ~~`manifest.json` was written from the plan, not from the generated files.~~ **Fixed**
  (4.9, F9), along with the `prd.project_path` fallback that could never fire.

Still outstanding: prose guards are advisory rather than enforced (4.13, **F15**), model
identifiers in the frontmatter are stale (4.2), and the `what-next.md` template that
`/prd --resume` greps for does not match what `/prd` writes (4.3, 4.4).

`tests/test_toolchain.py` guards every fix above against regression — 28 checks, each
verified to fail when its fix is reverted.

## Attribution and licensing

Derived from [vinzenz/prd-breakdown-execute](https://github.com/vinzenz/prd-breakdown-execute),
created January 2026.

Licensed under the MIT Licence — see [`LICENSE.md`](LICENSE.md), which carries both the
upstream copyright and the copyright on modifications made here.

One caveat is recorded in that file and repeated here because it is easy to miss: the
upstream repository declares MIT in the body of its `README.md` but ships no `LICENSE`
file, and GitHub reports no detected licence for it. The upstream copyright line is
therefore reconstructed from that stated licence, the owner's public name and the
repository's creation year, not copied from an upstream notice.
