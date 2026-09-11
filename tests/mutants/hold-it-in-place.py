"""Mutants for Phase 6 -- items 22 and 23.

Fourteen mutants against two scripts whose whole job is to notice absence. That makes them the
hardest checks in this suite to test honestly: a check on a script that reports *nothing missing*
passes just as well when the script has stopped looking.

Three are the ones worth naming:

  - the defining document counts as a reader. Every element then reads itself, the audit reports
    a clean 128 of 128, and it is a function that returns True. It is the single most likely
    "simplification" anybody would make to this script.
  - `open` starts failing the run. The verdict still exists, the rows are still there, and a
    legitimate `we have not decided` becomes a red build that somebody turns off.
  - the artefact version is taken as the CURRENT schema rather than detected. Every frozen
    fixture is then reported for elements its version never had, which reads as the fixtures
    being broken rather than the checker.
"""

MUTANTS = [
    # ---------------------------------------------------------------- item 22
    ("the <definition> value stops being checked against its enum",
     "schema/scripts/check-artefacts.py",
     '    enum(problems, "<meta>", (definition or "").strip() or None, DEFINITION, "<definition>")',
     '    _ = definition',
     "every artefact is the shape its own schema version describes"),

    ("a feature's criteria stop being checked for pattern and priority at all",
     "schema/scripts/check-artefacts.py",
     '            problems.append(f"{where} has no id, so nothing downstream can name it")\n'
     '        if at_least(version, "schema-3"):',
     '            problems.append(f"{where} has no id, so nothing downstream can name it")\n'
     '        if False:',
     "every artefact is the shape its own schema version describes"),

    ("the document-level <status> enum goes unchecked, and the live defect goes quiet",
     "schema/scripts/check-artefacts.py",
     '    enum(problems, "index.md <meta>", status, DOC_STATUS, "<status>")',
     '    _ = status',
     "every artefact is the shape its own schema version describes"),

    ("every artefact is judged by the CURRENT schema instead of its own",
     "schema/scripts/check-artefacts.py",
     "        version = args.schema or _mig.detect(text, kind)",
     "        version = args.schema or current",
     "every artefact is the shape its own schema version describes"),

    ("a retired <phases> element stops being refused",
     "schema/scripts/check-artefacts.py",
     '    if re.search(r"<phases>", text):',
     '    if False:',
     "every artefact is the shape its own schema version describes"),

    ('the pre-rename spelling is REFUSED, stranding every artefact written before item 45',
     'schema/scripts/check-artefacts.py',
     '            if at_least(current_schema(), "schema-2"):\n                warnings.append(f"<meta> still spells it <status>{legacy}</status>; "\n                                f"<definition> is the name since item 45. Accepted on read")',
     '            if at_least(current_schema(), "schema-2"):\n                problems.append(f"<meta> still spells it <status>{legacy}</status>; "\n                                f"<definition> is the name since item 45. Accepted on read")',
     'every artefact is the shape its own schema version describes'),

    ("/breakdown stops running the artefact check on its input",
     "skills/breakdown/SKILL.md",
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/check-artefacts.py {input_path_or_prd_dir}",
     "the artefact check is described below",
     "every artefact is the shape its own schema version describes"),

    ("/prd stops running the artefact check on what it just wrote",
     "commands/prd.md",
     "python ${CLAUDE_PLUGIN_ROOT}/schema/scripts/check-artefacts.py docs/prd/{slug}",
     "the artefact check is described above",
     "every artefact is the shape its own schema version describes"),

    # ---------------------------------------------------------------- item 23
    ("the defining document counts as a reader, so every element reads itself",
     "schema/scripts/check-readers.py",
     "            if rel in SCHEMA_DOCS or rel == READERS_DOC:\n                continue",
     "            if rel == READERS_DOC:\n                continue",
     "every element the schema defines has a reader, or a written reason"),

    ("an element with no reader and no row becomes a note nobody acts on",
     "schema/scripts/check-readers.py",
     '            problems.append(f"<{tag}> is defined in {\', \'.join(sorted(defined[tag]))} and "',
     '            notes.append(f"<{tag}> is defined in {\', \'.join(sorted(defined[tag]))} and "',
     "every element the schema defines has a reader, or a written reason"),

    ("`open` starts failing the run, so `we have not decided` becomes a red build",
     "schema/scripts/check-readers.py",
     '        elif verdict == "open":\n            opens.append(f"<{tag}>: {why}")',
     '        elif verdict == "open":\n            problems.append(f"<{tag}>: {why}")',
     "every element the schema defines has a reader, or a written reason"),

    ("readers.md may declare elements the schema no longer defines",
     "schema/scripts/check-readers.py",
     "        if tag not in defined:\n            problems.append(f\"{READERS_DOC} declares <{tag}>,",
     "        if False:\n            problems.append(f\"{READERS_DOC} declares <{tag}>,",
     "every element the schema defines has a reader, or a written reason"),

    ("the plan and the suite count as readers, so writing about an element makes it read",
     "schema/scripts/check-readers.py",
     '            if rel.startswith("docs/") or rel.startswith("tests/"):\n                continue',
     '            if False:\n                continue',
     "every element the schema defines has a reader, or a written reason"),

    # ------------------------------------------------- item 23, the enum consistency
    ("one reader's definition enum loses a value the other still derives",
     "schema/scripts/check-artefacts.py",
     'DEFINITION = {"tbd", "in-progress", "defined", "excluded", "superseded"}',
     'DEFINITION = {"tbd", "in-progress", "defined", "excluded"}',
     "the definition enum is one set, wherever it is implemented"),
]
