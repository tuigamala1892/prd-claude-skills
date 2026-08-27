---
name: migrate
description: Migrate PRD, CRD and PROJECT.md artefacts to a newer schema version. Use when a schema item has landed and existing documents are still in the previous shape.
context: fork
model: claude-sonnet-5
---

# /migrate - Artefact schema migration

You bring existing artefacts up to the current schema. The rules are specified in
[`schema/migration.md`](../../schema/migration.md), which is the authority — you orchestrate, and
you do not decide what a transformation is.

## Arguments

- `<path>`: file or directory to migrate (required)
- `--to <schema>`: target schema version (default: whatever `SCHEMAS.json` calls `current`)
- `--dry-run`: report what would change, write nothing

## Phase 1 — Find out where everything is, before changing anything

```bash
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py {path} --detect
```

One line per artefact: the schema it is in, what kind it is, and its path. **Exit 2 means one or
more files could not be placed** — report those first, by name, and do not migrate anything until
the person you are working with has seen them. A file the migration cannot place is a file whose
meaning would be guessed at.

Say the totals plainly: *"N files, M already current, K in schema-1, J that could not be
placed."* A migration that starts without that sentence is one nobody can tell is finished.

## Phase 2 — The mechanical rules, per file

```bash
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py {path} --to {target} --dry-run
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py {path} --to {target}
```

The script performs every transformation the guide calls mechanical, checks its own
postconditions, and restores any file whose postconditions fail.

| Exit | What it means | What you do |
|---|---|---|
| 0 | every file is in the target schema | continue to Phase 3 |
| 1 | a postcondition failed; **that file was restored** | **stop.** Report it verbatim. This is a defect in the rule, not in the artefact |
| 2 | one or more files matched no precondition | **stop.** Report each by name |

**Never work around exit 1 or 2 by editing a file by hand.** Both mean the specification and the
artefact disagree, and the resolution is a decision about the schema, not an edit.

## Phase 3 — The judgements, one file at a time

Only where the target schema requires them. The guide names them exhaustively, and for
`schema-2` the list is **empty** — that migration is a rename and nothing else.

Where they exist, dispatch **one agent per file**. Per file, never per directory: the guide's
reason is that silent semantic loss across many files is the failure mode and only a diff catches
it.

```
Task(
  subagent_type: "schema-migrator",
  prompt: <the file path, the target schema, and the rule ids the script reported>,
  run_in_background: false,
  description: "Migrate {file} to {target}"
)
```

Everything the agent needs must be in that prompt. It cannot load this skill, and naming one
here does nothing.

Collect what each returns. The part worth keeping is **what it changed that the script did
not** — everything else is reconstructable from the diff.

## Phase 4 — Say what finished, not what ran

```bash
python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/migrate.py {path} --to {target} --check
```

`--check` writes nothing and asserts the postconditions against the tree as it now stands. Report
its exit code. *"The migration ran"* and *"the migration finished"* are different claims, and
this is the only one of the two you are in a position to make.

Report, in this order: files migrated, files already current, **files escalated and why**, and
the `--check` result. The escalations are the half a reader most needs, so they are never the
half that gets summarised away.
