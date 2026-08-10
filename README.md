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
```

## Use

During development, load the plugin from a checkout:

```bash
claude --plugin-dir /path/to/prd-claude-skills
```

The skills, agents and commands then resolve without copying anything into the
target project.

## Status

**This toolchain is under repair and is not currently expected to run end to end.**
See [`docs/skills/toolchain-assessment-and-plan.md`](docs/skills/toolchain-assessment-and-plan.md)
for the full assessment. The findings that matter most before relying on it:

- **All 15 skills declare both `context: fork` and `allowed-tools`.** `allowed-tools`
  is not a recognised skill key, and its presence stops `context: fork` from taking
  effect — verified at 0/6 forked with it versus 9/9 without, across repeated runs.
  Consequence: no skill forks, so `agent:` never fires and each skill's `model:`
  declaration is inert. Everything runs inline on the caller's model.
- **`/execute` cannot run against a repository with no remote.** `execute-task` runs
  `git pull origin main` as the first command of every task.
- **The generated Layer 0 task runs `rm -rf {output-dir}/.git`.** That destroys git
  history at whatever path is passed in.

Model identifiers in the frontmatter (`claude-sonnet-4-6`, `claude-sonnet-4-5`) are
also stale, and the `<what-next.md>` template that `/prd --resume` greps for does not
match what `/prd` actually writes.

## Attribution and licensing

Derived from [vinzenz/prd-breakdown-execute](https://github.com/vinzenz/prd-breakdown-execute).

That repository's README states its licence as MIT, but it carries **no `LICENSE`
file** and GitHub reports no detected licence for it. This repository therefore does
not yet ship a `LICENSE` of its own — adding one means deciding how to represent both
the upstream grant and any local copyright, which is a call for the maintainer rather
than something to assume.
