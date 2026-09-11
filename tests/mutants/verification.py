"""Mutants for items 68-71 -- what verifying the implementation against the plan found.

**Three of the four fixes are prose in a shipped artefact**, which is exactly the class this
repository has watched pass while doing nothing five times: a check that asserts a phrase is
satisfied by the phrase, not by the mechanism. So the mutants here break the CLAIM rather than
the wording wherever they can -- a flag that is cited but not registered, a caller that runs a
script and is not listed, a count that disagrees with the script that produces it.

The last mutant breaks the check's own control. Item 71 derives its landed-item set from the
ledger, and a parse that silently returns nothing would make the check pass over its whole
subject in silence -- which is the failure mode group 8b named and this round is where it gets
tested rather than asserted.
"""

MUTANTS = [
    # ---------------------------------------------------------------- item 68
    ("the feature template loses <review>, so /prd writes a shape the bar cannot satisfy",
     "schema/prd-format.md",
     '    <!-- required by the BAR on a `defined` feature, optional in the schema. Core §7 -->\n'
     '    <review by="{{who read it}}" at="{{YYYY-MM-DD}}" sha="{{first 12 hex}}"/>\n',
     "",
     "producer on the authoring path"),

    ("/prd stops naming the producer, and the element goes back to having none",
     "commands/prd.md",
     "    --record-review --by {name} [--feature {slug}]",
     "    --by {name} [--feature {slug}]",
     "producer on the authoring path"),

    ("/prd cites a flag check-definition.py does not register",
     "skills/breakdown/scripts/check-definition.py",
     '    ap.add_argument("--record-review", action="store_true",',
     '    ap.add_argument("--write-review", action="store_true",',
     "producer on the authoring path"),

    ("the instruction denying there is anywhere to record a review comes back",
     "commands/prd.md",
     "**`defined` needs both halves**: the mechanical tests passing *and* a review recorded. Report a",
     "Where the PRD carries no place to record that review, say so plainly.\n\n"
     "**`defined` needs both halves**: the mechanical tests passing *and* a review recorded. Report a",
     "producer on the authoring path"),

    # ---------------------------------------------------------------- item 69
    ('task-integrity.py loses the row it never had until this item',
     'schema/checks.md',
     '| A task file is the one this run was dispatched with, or the run stops | `task-integrity.py` | `skills/execute/SKILL.md` · `skills/execute-layer/SKILL.md` | n/a | Reads a task file against the ledger that dispatched it | 63, 67 |\n',
     '',
     'every file that runs an owning script'),

    ('resolve-layers.py loses its row, so the layer refusal owns nothing',
     'schema/checks.md',
     '| Which layers this run executes, derived from the plan rather than recited | `resolve-layers.py` | `skills/execute/SKILL.md` | n/a | Reads the layer plan | 66 |\n',
     '',
     'every file that runs an owning script'),

    ("the CRD caller group 8b wired in is dropped from the column again",
     "schema/checks.md",
     "`schema/decision-record.md` · `skills/crd/references/crd-format.md` · `skills/breakdown/scripts/check-gate.py`",
     "`schema/decision-record.md`",
     "every file that runs an owning script"),

    ("the gate stops being listed as a caller of the coverage check it runs",
     "schema/checks.md",
     "| `check-coverage.py` | `skills/breakdown/SKILL.md` · `skills/breakdown/scripts/check-gate.py` |",
     "| `check-coverage.py` | `skills/breakdown/SKILL.md` |",
     "every file that runs an owning script"),

    # ---------------------------------------------------------------- item 70
    ("a documented command goes back to a path relative to the plugin",
     "skills/crd/references/crd-format.md",
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-references.py docs/crd/<slug>.md",
     "python skills/breakdown/scripts/check-references.py docs/crd/<slug>.md",
     "documented invocation names the plugin root"),

    ("the migration guide's own invocation loses the plugin root",
     "schema/migration.md",
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-definition.py docs/prd/<slug>",
     "python skills/breakdown/scripts/check-definition.py docs/prd/<slug>",
     "documented invocation names the plugin root"),

    # ---------------------------------------------------------------- item 71
    ("a script tells an operator that a landed item is still pending",
     "skills/breakdown/scripts/check-scope.py",
     "    ATTRIBUTION IS ITEM 16's, AND IT LANDED IN GROUP 5d.",
     "    ATTRIBUTION IS ITEM 16's, AND IT HAS NOT LANDED.",
     "no shipped artefact describes a state"),

    ("the registry's stated count stops agreeing with the script that produces it",
     "schema/readers.md",
     "Three filters take it to **seven**",
     "Three filters take it to **six**",
     "no shipped artefact describes a state"),

    ("a sibling registry drops back a schema version, which is where this finding started",
     "schema/parity.md",
     '<parity schema="schema-6"/>',
     '<parity schema="schema-5"/>',
     "no shipped artefact describes a state"),

    # ------------------------------------------------- the check's own control
    ("item 71's landed set parses to nothing, so it would pass over its whole subject",
     "tests/test_toolchain.py",
     '        if line.startswith("| **") and ("Landed" in line or "Done" in line):',
     '        if line.startswith("| ***") and ("Landed" in line or "Done" in line):',
     "no shipped artefact describes a state"),
]
