"""Mutants for the residue -- items 10, 24, 32 and 38 (group 5e).

Seventeen mutants. Eleven break a PROGRAM and six break a DOCUMENT, and the eleven are the ones
that say whether these checks read behaviour or read prose about behaviour.

Three are worth naming in advance, because each is a mutant that leaves the check's most obvious
assertion TRUE:

  - the compatibility reader refuses a NEWER MINOR. Additive minors running is what let item 16
    add four traceability fields without breaking a reader written against 1.0, and a check that
    only tested the refusal direction would call this an improvement.
  - the stamp is REWRITTEN on every derivation. It is still present, still correct-looking, and
    provenance has quietly become a version tracker that makes every PRD read as stale.
  - the design-track switch gates the CHECKING rather than the STOPPING. The gate still exists,
    still passes, still reports nothing -- which is exactly the failure item 38 says the report
    half is there to prevent.
"""

MUTANTS = [
    # ---------------------------------------------------------------- item 32
    ("the rendered summary stops being written, so review means opening every task",
     "skills/breakdown/scripts/build-manifest.py",
     '    summary_path = os.path.join(tasks_path, SUMMARY_NAME)\n'
     '    with open(summary_path, "w", encoding="utf-8", newline="\\n") as f:\n'
     '        f.write(render_summary(inventory, by_layer, prd.get("slug")))',
     '    summary_path = os.path.join(tasks_path, SUMMARY_NAME)',
     "the task set is reviewable without opening every task"),

    ("--verify stops comparing the summary, so a hand-edited one is accepted",
     "skills/breakdown/scripts/build-manifest.py",
     '        elif open(summary_path, encoding="utf-8").read() != wanted:',
     '        elif False:',
     "the task set is reviewable without opening every task"),

    ("the summary loses the objective, leaving a row that says nothing about the work",
     "skills/breakdown/scripts/build-manifest.py",
     '    el = root.find("objective")',
     '    el = root.find("objective-was")',
     "the task set is reviewable without opening every task"),

    # ------------------------------------------------- item 24, the compatibility half
    ("a major this reader has never seen becomes a warning instead of a refusal",
     "skills/execute/scripts/check-compatibility.py",
     '        refuse.append(f"manifest schema_version {schema_version} is {direction} MAJOR than "',
     '        warn.append(f"manifest schema_version {schema_version} is {direction} MAJOR than "',
     "the manifest's version stamps finally have a reader"),

    ("a newer MINOR is refused, so additive fields stop being additive",
     "skills/execute/scripts/check-compatibility.py",
     "    elif got[1] > reader[1]:\n        warn.append(",
     "    elif got[1] > reader[1]:\n        refuse.append(",
     "the manifest's version stamps finally have a reader"),

    ("provenance starts deciding compatibility, so every patch release is a migration",
     "skills/execute/scripts/check-compatibility.py",
     '        notes.append(f"produced by toolchain {produced_by}; this one is {running}. That is "',
     '        refuse.append(f"produced by toolchain {produced_by}; this one is {running}. That is "',
     "the manifest's version stamps finally have a reader"),

    ("a manifest with no schema_version is downgraded to a note nobody acts on",
     "skills/execute/scripts/check-compatibility.py",
     '        warn.append(f"the manifest declares no schema_version, so it was written before the "',
     '        refuse.append(f"the manifest declares no schema_version, so it was written before the "',
     "the manifest's version stamps finally have a reader"),

    ("/execute stops running the compatibility check and only describes it",
     "skills/execute/SKILL.md",
     "python {skill_dir}/scripts/check-compatibility.py {tasks_path}",
     "the compatibility check is described below",
     "the manifest's version stamps finally have a reader"),

    # ------------------------------------------------------ item 24, the stamp half
    ("the stamp is rewritten on every derivation, turning provenance into a version tracker",
     "schema/scripts/build-what-next.py",
     "    if STAMP.search(text):\n        return text",
     "    text = STAMP.sub('', text)",
     "what-next.md records what wrote it, once, and something reads it"),

    ("the stamp stops being written at all",
     "schema/scripts/build-what-next.py",
     "        f.write(touch(stamp(text)))",
     "        f.write(touch(text))",
     "what-next.md records what wrote it, once, and something reads it"),

    ("the stamp loses its reader, so the element goes back to being stored rather than read",
     "skills/breakdown/scripts/list-prds.py",
     '            print(f"\\n{prd[\'slug\']}: written by toolchain {stamp}; this one is {running}. "',
     '            _unused = (f"\\n{prd[\'slug\']}: written by toolchain {stamp}; this one is {running}. "',
     "what-next.md records what wrote it, once, and something reads it"),

    # ---------------------------------------------------------------- item 38
    ('the switch gates the CHECKING rather than the STOPPING, so `off` reports nothing',
     'skills/breakdown/scripts/check-gate.py',
     '    gaps, gap_err = blocking_gaps(args.document, built)',
     '    gaps, gap_err = ([], None) if not track["enabled"] else blocking_gaps(args.document, built)',
     'the gate asserts three things by name'),

    ("a `decision` gap stops blocking, so an undecided question builds in silence",
     "skills/breakdown/scripts/check-gate.py",
     'BLOCKING_GAPS = {"specification", "dependency", "decision"}',
     'BLOCKING_GAPS = {"specification", "dependency"}',
     "the gate asserts three things by name"),

    ("significance stops being scoped to what was built, so the gate reports the whole PRD",
     "skills/breakdown/scripts/check-gate.py",
     "    if built:\n        undriven = [ln for ln in undriven if any(f\"{slug}.md\" in ln for slug in built)]",
     "    if False:\n        undriven = [ln for ln in undriven if any(f\"{slug}.md\" in ln for slug in built)]",
     "the gate asserts three things by name"),

    ("the gate stops caring what the coverage check returned",
     "skills/breakdown/scripts/check-gate.py",
     "    if cov_code != 0:\n        findings.append((\"coverage\", cov_out))",
     "    if False:\n        findings.append((\"coverage\", cov_out))",
     "the gate asserts three things by name"),

    ("an unset design-track switch is defaulted to off instead of refused",
     "skills/breakdown/scripts/check-architecture.py",
     '    if raw not in ("true", "false"):',
     '    if raw not in ("true", "false", ""):',
     "`<design-track>` has a host artefact"),

    # ---------------------------------------------------------------- item 10
    ("/prd stops saying to write feature files one at a time",
     "commands/prd.md",
     "**Write `features/{slug}.md` one file at a time, and do not assemble the set in a single "
     "message\nbefore writing any of it.**",
     "**Write the feature files.**",
     "`/prd` writes features one at a time"),

    ("the bound on what a later EDIT loads disappears, and the blob comes back",
     "commands/prd.md",
     "- **When editing later, re-read only the feature being edited**, plus its index entry and "
     "the\n  neighbours its `<depends-on>` names",
     "- **When editing later, load the PRD**, including its index entry and the\n  neighbours "
     "its `<depends-on>` names",
     "`/prd` writes features one at a time"),
]
