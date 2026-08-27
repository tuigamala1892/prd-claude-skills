"""Mutants for the CRD parity pass -- items 46, 47 and 48 (schema-5).

Six mutants, one per claim the three new checks make. Each names the check that must fail, so a
check that fires for the wrong reason reads as an orphan rather than as a pass.

The two `migrate.py` mutants are the ones worth having. Everything else here breaks a document,
and a document check can be satisfied by a sentence; those two break BEHAVIOUR, and a check that
survives them is a check that was reading prose about a program rather than running it.
"""

MUTANTS = [
    # ---------------------------------------------------------------- item 46
    ("crd-format's document structure puts <requirements> back",
     "skills/crd/references/crd-format.md",
     "  <impact-analysis>...</impact-analysis>\n  <acceptance-criteria>...</acceptance-criteria>",
     "  <impact-analysis>...</impact-analysis>\n  <requirements>...</requirements>\n"
     "  <acceptance-criteria>...</acceptance-criteria>",
     "a CRD carries one list, not two"),

    ("the migration renumbers from 1, colliding with the criteria that were there",
     "schema/scripts/migrate.py",
     "    nxt = (max(ids) + 1) if ids else 1",
     "    nxt = 1",
     "a CRD carries one list, not two"),

    ("a migrated requirement gets a bare derived-from, ambiguous across the merged spaces",
     "schema/scripts/migrate.py",
     "        derived = ' derived-from=\"requirement-%s\"' % old.group(1) if old else \"\"",
     "        derived = ' derived-from=\"%s\"' % old.group(1) if old else \"\"",
     "a CRD carries one list, not two"),

    # ---------------------------------------------------------------- item 47
    ("core gives `wont-have` a P-level instead of leaving it unmappable",
     "schema/core.md",
     "| `wont-have` | **nothing — the migration stops and names the file** |",
     "| `wont-have` | `P2` |",
     "requirement priority is P0|P1|P2 on both paths"),

    ("the migration maps `wont-have` to P2 rather than escalating",
     "schema/scripts/migrate.py",
     'MOSCOW_TO_P = {"must-have": "P0", "should-have": "P1", "could-have": "P2"}',
     'MOSCOW_TO_P = {"must-have": "P0", "should-have": "P1", "could-have": "P2",\n'
     '               "wont-have": "P2"}',
     "requirement priority is P0|P1|P2 on both paths"),

    # ---------------------------------------------------------------- item 48
    ("/crd stops running the overwrite guard, which is F3 exactly",
     "commands/crd.md",
     "check-writable.py {project_path}/docs/crd/{slug}.md\n```\n\n- **Exit 0**",
     "test -e {project_path}/docs/crd/{slug}.md && echo EXISTS\n```\n\n- **Exit 0**",
     "cannot silently replace a CRD"),

    ("the guard stops refusing a single file, so only PRD directories are protected",
     "skills/breakdown/scripts/check-writable.py",
     "    if os.path.isfile(target):\n        return [target]",
     "    if os.path.isfile(target):\n        return []",
     "cannot silently replace a CRD"),
]
