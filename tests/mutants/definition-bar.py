"""Mutants for the definition bar -- items 58, 3, 6, 7, 40 and 8 (group 5d).

Fifteen mutants, and the split matters more than the count. Four break a DOCUMENT and eleven
break a PROGRAM: a document check can be satisfied by a sentence, so the eleven are the ones that
say whether these checks read behaviour or read prose about behaviour.

Two of them are the ones worth having. The ceiling mutant makes `check-status.py` report a
feature declared BELOW what its content supports -- which is the failure mode the first version
of item 3's rule actually had on a real corpus, and a check that only ever tested the loud
direction would pass it. And the inbound-edge mutant silences test 7's half that gets skipped,
which is the half that catches contract gaps.
"""

MUTANTS = [
    # ---------------------------------------------------------------- item 58
    ("two assertions are given the same owner, so `which script says so` has two answers",
     "schema/checks.md",
     "| Index ↔ `features/` reconcile; no reference to a slug that has no file | `check-rename.py` |",
     "| Index ↔ `features/` reconcile; no reference to a slug that has no file | `check-status.py` |",
     "every assertion has one owning script"),

    ('a row claims a caller that never names the script',
     'schema/checks.md',
     "| The mechanical half of the well-defined bar, and the criterion-priority spread | `check-definition.py` | `commands/prd.md` · `schema/migration.md` | prd-only | The bar is about a PRD feature's `<definition>` ladder, and [core](core.md) section 3 makes a CRD's `<workflow>` a process position rather than a degree of definition | 40, 34 |",
     "| The mechanical half of the well-defined bar, and the criterion-priority spread | `check-definition.py` | `commands/crd.md` · `schema/migration.md` | prd-only | The bar is about a PRD feature's `<definition>` ladder, and [core](core.md) section 3 makes a CRD's `<workflow>` a process position rather than a degree of definition | 40, 34 |",
     'every assertion has one owning script'),

    # ----------------------------------------------------------------- item 3
    ("the ceiling becomes a value: a feature held BELOW what its content supports is a defect",
     "skills/breakdown/scripts/check-status.py",
     "        soft.append(f\"{rel}: declared `{declared}`, content supports `{top}` ({why})\")",
     "        bad.append(f\"{rel}: declared `{declared}`, content supports `{top}` ({why})\")",
     "declared definition is checked against its own content"),

    ("`defined` stops being barred by a specification gap",
     "skills/breakdown/scripts/check-status.py",
     '    if "specification" in _sel.gaps_of(text):',
     '    if False and "specification" in _sel.gaps_of(text):',
     "declared definition is checked against its own content"),

    ("any word is accepted as a gap kind, so the enum is decoration",
     "skills/breakdown/scripts/check-status.py",
     "        if kind not in GAP_KINDS:",
     "        if kind is None:",
     "declared definition is checked against its own content"),

    ("gap age stops being reported, so an item raised in January reads like one raised today",
     "skills/breakdown/scripts/check-status.py",
     '            print(f"  AGE            {rel}: gap {gid} ({kind}) raised {raised}, '
     '{days} days ago")',
     '            pass',
     "declared definition is checked against its own content"),

    # ---------------------------------------------------------------- item 40
    ("every pattern counts as a failure path, so test 2 passes a corpus of happy paths",
     "skills/breakdown/scripts/check-definition.py",
     'FAILURE_PATTERNS = {"unwanted-behaviour"}',
     'FAILURE_PATTERNS = set(PATTERNS)',
     "each mechanical test of the well-defined bar fires"),

    ("test 4 stops looking for a data model",
     "skills/breakdown/scripts/check-definition.py",
     '    m = DATA_MODEL.search(text)\n    if not m or not m.group(1).strip():',
     '    m = DATA_MODEL.search(text)\n    if False:',
     "each mechanical test of the well-defined bar fires"),

    ("a dependency with a name and no role passes test 5",
     "skills/breakdown/scripts/check-definition.py",
     "        if not purpose or not purpose.group(1).strip():",
     "        if purpose is None and False:",
     "each mechanical test of the well-defined bar fires"),

    ("test 7's INBOUND half goes silent -- the half that gets skipped, and catches contract gaps",
     "skills/breakdown/scripts/check-definition.py",
     '        edges.append(f"{rel}:{line}: {other_slug} names `{slug}` and declares no "',
     '        _unused = (f"{rel}:{line}: {other_slug} names `{slug}` and declares no "',
     "each mechanical test of the well-defined bar fires"),

    ("the tautology screen stops firing, so `so that I can X` passes test 8",
     "skills/breakdown/scripts/check-definition.py",
     "    if benefit and benefit <= want:",
     "    if benefit and False:",
     "each mechanical test of the well-defined bar fires"),

    # -------------------------------------------------------------- items 6/42
    ("an unindexed feature file stops being an orphan, so a rename residue is invisible",
     "skills/breakdown/scripts/check-rename.py",
     '        if slug not in indexed and _sel.definition_of(text) != "superseded":',
     '        if slug not in indexed and _sel.definition_of(text) is None:',
     "the index, the feature directory and every reference reconcile"),

    ("a <priority> left behind in a feature file stops being residue",
     "skills/breakdown/scripts/check-rename.py",
     "        if meta and PRIORITY_EL.search(meta.group(1)):",
     "        if meta and PRIORITY_EL.search(meta.group(1)) and False:",
     "the index, the feature directory and every reference reconcile"),

    # ---------------------------------------------------------------- items 6/7
    ("/prd's validation phase stops RUNNING the status check and only discusses it",
     "commands/prd.md",
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-status.py {prd_dir}\n"
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-rename.py {prd_dir}\n"
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-references.py {prd_dir}\n"
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-definition.py {prd_dir}\n"
     "```\n\nPass `{prd_dir}` as an argument.",
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-rename.py {prd_dir}\n"
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-references.py {prd_dir}\n"
     "python ${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-definition.py {prd_dir}\n"
     "```\n\nThe status check is described above. Pass `{prd_dir}` as an argument.",
     "/prd calls the checks rather than restating them"),

    ("--resume re-runs the checks only over what this session touched",
     "commands/prd.md",
     "**Then re-run Phase 7's checks across the whole PRD before resuming anything.** Not over "
     "the\nfeatures this session is about to touch — over **all** of them:",
     "**Then re-run Phase 7's checks over the features you are about to edit.**",
     "/prd calls the checks rather than restating them"),

    # ----------------------------------------------------------------- item 8
    ("the challenger is given a writing tool, so it can close the loop it must leave open",
     "agents/prd-criteria-author.md",
     "tools: Read Glob Grep",
     "tools: Read Write Edit Glob Grep",
     "the criteria challenger proposes, never writes"),

    ("the review dispatch disappears, leaving the judgement half of the bar with no runner",
     "commands/prd.md",
     '  subagent_type: "prd-criteria-author",\n'
     '  prompt: <mode: review-definition; the feature file path; its index entry; its neighbours;',
     '  subagent_type: "some-other-agent",\n'
     '  prompt: <mode: review-definition; the feature file path; its index entry; its neighbours;',
     "the criteria challenger proposes, never writes"),
]
