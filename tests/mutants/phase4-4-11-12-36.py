"""Items 4, 11, 12 and 36 -- the conventions, what-next.md, the dual read, the decision record.

Three of the four checks RUN something: the migration's convention rules, the what-next deriver,
and `list-prds.py`. That is deliberate. Item 4's rules transform nothing, so their entire value
is an exit code; item 11's block is worthless unless staleness is detectable; item 12 is about a
finder that has to keep working across a half-migrated tree.

The mutants that matter look like tidying again. Deleting a superseded feature's index entry
requirement looks like leniency; copying a gap's body into the derived block looks like
helpfulness; dropping the dual read looks like finishing a migration.
"""

MIGRATE = "schema/scripts/migrate.py"
BUILDER = "schema/scripts/build-what-next.py"
PRD_FMT = "schema/prd-format.md"
GUIDE = "schema/migration.md"
RECORD = "schema/decision-record.md"
LIST = "skills/breakdown/scripts/list-prds.py"

MUTANTS = [
    # ---- item 4: the conventions ------------------------------------------------------------
    ("an excluded feature no longer needs a rationale",
     MIGRATE,
     '    if definition == "excluded":',
     "    if False:",
     "a feature that will not be built says why"),

    ("an empty rationale counts as a rationale",
     MIGRATE,
     "        if not body or not body.group(1).strip():",
     "        if not body:",
     "a feature that will not be built says why"),

    ("a superseded feature may name a successor that does not exist",
     MIGRATE,
     "            if not os.path.isfile(sibling):",
     "            if False:",
     "a feature that will not be built says why"),

    ("a superseded feature may stay in the index",
     MIGRATE,
     "        if index_slugs is not None and slug and slug.group(1) in index_slugs:",
     "        if False:",
     "a feature that will not be built says why"),

    ("the conventions are checked only on files the migration transforms",
     MIGRATE,
     "        if kind == \"feature\":\n            broken = convention_problems(text, path, index_slugs)",
     "        if False:\n            broken = convention_problems(text, path, index_slugs)",
     "a feature that will not be built says why"),

    ("a refused file is written anyway instead of left alone",
     MIGRATE,
     '                failures.append(f"{rel}: " + "; ".join(broken) + " -- NOT WRITTEN")',
     '                failures.append(f"{rel}: " + "; ".join(broken) + " -- rewritten")',
     "a feature that will not be built says why"),

    ("the guide stops recording that reclassification derives a ceiling",
     GUIDE,
     "**Reclassifying `<definition>` is a judgement, and the rule it will follow is a ceiling.**",
     "**Reclassifying `<definition>` is a judgement.**",
     "a feature that will not be built says why"),

    # ---- item 11: the derived block ---------------------------------------------------------
    ("the deriver stops noticing that a feature grew a gap",
     BUILDER,
     "    if existing and existing.group(0) == wanted:",
     "    if existing:",
     "what-next.md's gap list is derived"),

    ("the derived block copies each gap's body instead of pointing at it",
     BUILDER,
     "            rows.append(f'{indent}  <gap slug=\"{slug}\" id=\"{a.get(\"id\", \"\")}\" '\n"
     "                        f'kind=\"{a.get(\"kind\", \"\")}\" raised=\"{a.get(\"raised\", \"\")}\"/>')",
     "            body = re.sub(r'<[^>]+>', ' ', attrs)\n"
     "            rows.append(f'{indent}  <gap slug=\"{slug}\" id=\"{a.get(\"id\", \"\")}\" '\n"
     "                        f'kind=\"{a.get(\"kind\", \"\")}\">Who owns the URL parser</gap>')",
     "what-next.md's gap list is derived"),

    ("the summary miscounts by ignoring a feature's declared definition",
     BUILDER,
     '        counts[definition] = counts.get(definition, 0) + 1',
     '        counts[definition] = counts.get(definition, 0)',
     "what-next.md's gap list is derived"),

    ("--check reports stale as success",
     BUILDER,
     "        print(f\"STALE: what-next.md's <authoring-gaps> {where}. Run without --check to \"\n"
     "              f\"rebuild it.\", file=sys.stderr)\n        return 1",
     "        print(f\"STALE: what-next.md's <authoring-gaps> {where}. Run without --check to \"\n"
     "              f\"rebuild it.\", file=sys.stderr)\n        return 0",
     "what-next.md's gap list is derived"),

    ("the template stops saying the block is never hand-maintained",
     PRD_FMT,
     "**Never hand-maintained.** A PRD with twenty-one unfinished features",
     "**Keep it up to date.** A PRD with twenty-one unfinished features",
     "what-next.md's gap list is derived"),

    # ---- item 12: the dual read -------------------------------------------------------------
    # This mutant also trips `/prd`'s overwrite-guard check, which runs the same script, so the
    # harness reports that as an orphan. It is a second check firing rather than a MISSED being
    # misattributed -- which is exactly the ambiguity the orphan warning exists to surface, and
    # is worth leaving visible rather than silencing.
    ("the finder stops seeing a status nested under <meta>",
     LIST,
     'STATUS = re.compile(r"<status>\\s*([a-z-]+)\\s*</status>", re.I)',
     'STATUS = re.compile(r"^  <status>\\s*([a-z-]+)\\s*</status>", re.I | re.M)',
     "the resume marker is readable in both shapes"),

    # ---- item 36: the decision record --------------------------------------------------------
    ("the test for whether it is a decision at all is deleted",
     RECORD,
     "**No rejected alternatives means it is not a decision record — it is a principle.**",
     "**Write one whenever a choice was made.**",
     "the decision record has a template"),

    ("an option no longer records what it was rejected on",
     RECORD,
     "**Verdict:** {{rejected, and on what grounds}}",
     "{{rejected}}",
     "the decision record has a template"),

    ("the Drives field is dropped from the template",
     RECORD,
     "**Drives:** [{{Feature Name}}](../../prd/{{slug}}/features/{{feature-slug}}.md), [{{Another}}](...)",
     "{{features this drives, in the Context links above}}",
     "the decision record has a template"),

    ("the design track ships on by default",
     RECORD,
     '<design-track enabled="false" adr-dir="../../architecture/decisions"/>',
     '<design-track adr-dir="../../architecture/decisions"/>',
     "the decision record has a template"),

    ("titles go back to naming a topic",
     RECORD,
     "**Titles state a claim, not a topic.**",
     "**Give it a title.**",
     "the decision record has a template"),

    ("the record names no reader, so nothing keeps its conventions honest",
     RECORD,
     "| [`check-references.py`](../skills/breakdown/scripts/check-references.py) | `**Status:**`"
     " for supersession; `**Drives:**` links resolve; a significant feature no record drives |",
     "| a person | the conventions above |",
     "the decision record has a template"),
]
