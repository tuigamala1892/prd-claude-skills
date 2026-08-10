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

## Status

**All three blocking defects are fixed, but the pipeline has not yet been run end to
end.** Treat it as repaired-but-unproven rather than working. See
[`docs/skills/toolchain-assessment-and-plan.md`](docs/skills/toolchain-assessment-and-plan.md)
for the full assessment.

Fixed:

- ~~All 15 skills declare `allowed-tools`, which stops `context: fork` working.~~
  **Fixed** (4.11). That key is a *command* key; in a skill it restricted nothing and
  silently disabled forking, so for the life of this toolchain no skill forked,
  `agent:` never fired, and no skill's `model:` applied. One line per file fixed all
  three.
- ~~`/execute` cannot run against a repository with no remote.~~ **Fixed** (4.8).
  Remote operations are now conditional on a remote existing, and the branch name is a
  parameter defaulting to the repository's HEAD rather than a hardcoded `main`.
- ~~The generated Layer 0 task deletes the target's `.git`.~~ **Fixed** (4.7). The
  template now excludes `.git` from the copy instead of deleting it at the
  destination, Layer 0 no longer contradicts the preflight by running `git init`, and
  `/execute` refuses to target a docs tree or the toolchain itself.

Still outstanding: model identifiers in the frontmatter (`claude-sonnet-4-6`,
`claude-sonnet-4-5`) are stale (4.2), and the `what-next.md` template that
`/prd --resume` greps for does not match what `/prd` writes (4.3, 4.4).

`tests/test_toolchain.py` guards every one of the fixes above against regression.

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
