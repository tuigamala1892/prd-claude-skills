"""Mutants for item 65 -- a task may name every feature it descends from.

Four checks, and three of them run code, so most of these break scripts rather than sentences.
The shape of the round follows the shape of the item: a producer that must write every edge, a
compatibility shim that must not guess, and consumers that must read the list rather than the
first of it.

Three deserve a note.

  * `source_feature` written for a multi-edge task is the shim REINTRODUCING the defect it
    exists to smooth over: a 1.2 reader would see one slug and believe it, which is exactly
    run 3's silent narrowing wearing the compatibility layer's clothes.
  * The relaxed consumer is the fix the plan explicitly forbids -- pooling criterion ids across
    features makes the report pass and leaves the task set as unattributable as it was.
  * The last two break the OTHER half of two prose assertions, because a check that only
    requires a sentence passes on a file that has lost the thing the sentence is about.
"""

MUTANTS = [
    # ------------------------------------------------------------------ the producer
    ("only the first <source-feature> is read, which is run 3's silent narrowing in code",
     "skills/breakdown/scripts/build-manifest.py",
     '    for el in meta.findall("source-feature"):',
     '    for el in meta.findall("source-feature")[:1]:',
     "a task names every feature it descends from"),

    ("the singular key is written for a multi-feature task, so a 1.2 reader believes one slug",
     "skills/breakdown/scripts/build-manifest.py",
     "    if len(edges) == 1:\n        out[\"source_feature\"] = edges[0][\"slug\"]",
     "    if edges:\n        out[\"source_feature\"] = edges[0][\"slug\"]",
     "a task names every feature it descends from"),

    ("the effective tier becomes the first edge's rather than the strongest",
     "skills/breakdown/scripts/build-manifest.py",
     '    tier = _strongest([e.get("moscow") for e in edges], TIERS)',
     '    tier = edges[0].get("moscow")',
     "a task names every feature it descends from"),

    ("the pre-item-65 shape stops being read, stranding every task set generated before today",
     "skills/breakdown/scripts/build-manifest.py",
     '        slug = (el.get("slug") or " ".join((el.text or "").split() if el.text else "")).strip()',
     '        slug = (el.get("slug") or "").strip()',
     "a task names every feature it descends from"),

    ("the manifest shape changes and its version does not",
     "skills/breakdown/scripts/build-manifest.py",
     'MANIFEST_SCHEMA_VERSION = "1.3"',
     'MANIFEST_SCHEMA_VERSION = "1.2"',
     "a task names every feature it descends from"),

    ("the reviewable summary shows one feature for a task that walks three",
     "skills/breakdown/scripts/build-manifest.py",
     '        origin = "<br>".join(x["slug"] for x in edges) or "—"',
     '        origin = (edges[0]["slug"] if edges else "—")',
     "a task names every feature it descends from"),

    # ------------------------------------------------------------------ the consumers
    ("coverage attributes a task to the first feature it names and no others",
     "skills/breakdown/scripts/check-coverage.py",
     "        for edge in edges_of(task):",
     "        for edge in edges_of(task)[:1]:",
     "coverage and scope attribute a task to every feature it names"),

    ("criterion ids are pooled across features -- the relaxed consumer the plan forbids",
     "skills/breakdown/scripts/check-coverage.py",
     "        got = cited.get(slug, set())",
     "        got = set().union(*cited.values()) if cited else set()",
     "coverage and scope attribute a task to every feature it names"),

    ("the scope cross-check counts a task under one of the features it names",
     "skills/breakdown/scripts/check-scope.py",
     "        for edge in edges:\n            per_feature[edge[\"slug\"]] = "
     "per_feature.get(edge[\"slug\"], 0) + 1",
     "        for edge in edges[:1]:\n            per_feature[edge[\"slug\"]] = "
     "per_feature.get(edge[\"slug\"], 0) + 1",
     "coverage and scope attribute a task to every feature it names"),

    # ------------------------------------------------------------------ the raw-text guards
    ("preflight goes back to matching only the retired element form",
     "skills/execute/scripts/preflight.sh",
     "wont=$(grep -rlE '<moscow>wont-have</moscow>|moscow=\"wont-have\"' \"$tasks_abs\" 2>/dev/null | sort)",
     "wont=$(grep -rl '<moscow>wont-have</moscow>' \"$tasks_abs\" 2>/dev/null | sort)",
     "the wont-have refusal and the gate read the per-edge shape"),

    ("the gate stops seeing the slugs /breakdown now writes",
     "skills/breakdown/scripts/check-gate.py",
     "SOURCE_FEATURE = re.compile(\n"
     "    r'<source-feature\\b[^>]*\\bslug=\"([a-z0-9-]+)\"'\n"
     "    r'|<source-feature>\\s*([a-z0-9-]+)\\s*</source-feature>')",
     "SOURCE_FEATURE = re.compile(\n"
     "    r'<source-feature>\\s*([a-z0-9-]+)\\s*</source-feature>()')",
     "the wont-have refusal and the gate read the per-edge shape"),

    # ------------------------------------------------------------------ the instructions
    ("the spec's only multi-feature example goes, leaving the shape with no worked case",
     "skills/breakdown/references/task-format-spec.md",
     '  <source-feature slug="tag-links"  moscow="should-have" satisfies-criteria="1,3" requirement-level="P1"/>\n',
     "",
     "the schema, the generator and the reviewer all say a task may name several features"),

    ("an example edge loses its own criteria, so ids stop being per feature",
     "skills/breakdown/references/task-format-spec.md",
     '<source-feature slug="save-link" moscow="must-have"\n                  satisfies-criteria="1,4,7" requirement-level="P0"/>',
     '<source-feature slug="save-link" moscow="must-have" requirement-level="P0"/>',
     "the schema, the generator and the reviewer all say a task may name several features"),

    ("the generator stops being told to name every feature the task covers",
     "skills/breakdown-generate-tasks/SKILL.md",
     "**Name every feature the task actually covers, and never narrow to the closest one.**",
     "**Name the feature the task is mainly about.**",
     "the schema, the generator and the reviewer all say a task may name several features"),

    ("review stops asking for the grouping, so two features' criterion 1 arrive as one id",
     "skills/breakdown/references/review-criteria.md",
     "- [ ] **More than one `<source-feature>` means the carried criteria are grouped.** Every\n"
     "      `<criterion>` sits inside a `<from-feature slug=>` matching one of them, and every `<test>`\n"
     "      carries `from-feature`. Criterion ids repeat across features, so an ungrouped `1` names two\n"
     "      requirements at once.\n",
     "",
     "the schema, the generator and the reviewer all say a task may name several features"),

    # Two mutants, because the promise has two halves and the first version of this round broke
    # only the lead sentence -- leaving `is still accepted by every reader` two lines below, which
    # the check matched. A rule stated across two sentences needs the whole paragraph removing.
    ("the compatibility promise goes unstated, and a corpus of old task files has no rule",
     "skills/breakdown/references/task-format-spec.md",
     "**The old shape is read and never written.** One `<source-feature>slug</source-feature>` with\n"
     "sibling `<moscow>`, `<satisfies-criteria>` and `<requirement-level>` elements is still accepted by\n"
     "every reader, and the siblings still fill in an attribute the new form omits — that is what makes\n"
     "a half-migrated task readable rather than an error. New tasks carry the attribute form. This is\n"
     "item 45's rule, and it applies here for the same reason: a corpus of task files does not migrate\n"
     "itself, and a reader that refuses the old shape strands every task set generated before today.\n",
     "**The shape above is what to write.**\n",
     "the schema, the generator and the reviewer all say a task may name several features"),

    ("the promise keeps its `read` half and loses its `never written` half",
     "skills/breakdown/references/task-format-spec.md",
     "**The old shape is read and never written.**",
     "**The old shape still parses.**",
     "the schema, the generator and the reviewer all say a task may name several features"),
]
