"""Item 45 -- three renames, a frozen fixture, and the registry that says which is current.

The three checks here guard different failure modes, and only one of them is about wording:

  * the vocabulary check reads core §3's table AS DATA -- four rows, four distinct tags, and
    at least one shared value, because a shared value across distinct tags is what made
    reading the wrong tag return a plausible answer rather than an error;
  * the frozen-hash check is the first enforcement item 43's rule 2 has ever had;
  * the hardcoded-version check exists because item 45 created the second schema version, and
    every path still naming `schema-1` would have gone on measuring the superseded copy.
"""

CORE = "schema/core.md"
SUITE_FIXTURE = "tests/fixture/prd/schema-1/link-shelf/index.md"

MUTANTS = [
    ("two vocabularies share a tag again",
     CORE,
     "| `<workflow>` | a CRD's `<meta>` | where the change is in the **process** |",
     "| `<status>` | a CRD's `<meta>` | where the change is in the **process** |",
     "three status vocabularies, three distinct names"),

    ("the document-level tag is renamed too, so no row keeps the word",
     CORE,
     "| `<status>` | `index.md`, `what-next.md` | how far the **interview** got |",
     "| `<interview>` | `index.md`, `what-next.md` | how far the **interview** got |",
     "three status vocabularies, three distinct names"),

    ("core §3 stops recording the overlap that made the collision dangerous",
     CORE,
     "**defined** | `tbd`, `in-progress`, `defined` |",
     "**defined** | `tbd`, `partly-specified`, `defined` |",
     "three status vocabularies, three distinct names"),

    ("the rename reaches the prose but not the template",
     "schema/prd-format.md",
     "    <definition>defined|tbd|in-progress</definition>",
     "    <status>defined|tbd|in-progress</status>",
     "three status vocabularies, three distinct names"),

    # ONE of four entries, deliberately. The first version of this assertion used any() and
    # the other three satisfied it while this one carried the old attribute.
    ("one PROJECT.md entry of four keeps the old attribute",
     "skills/crd/references/project-format.md",
     '  <feature id="auth" built="complete">',
     '  <feature id="auth" status="complete">',
     "three status vocabularies, three distinct names"),

    ("the backward-read policy is dropped, so each reader decides for itself",
     CORE,
     "**Accepted on read; never written.**",
     "**Readers should do something sensible.**",
     "three status vocabularies, three distinct names"),

    ("a frozen fixture is edited",
     SUITE_FIXTURE,
     "<slug>link-shelf</slug>",
     "<slug>link-shelf-v2</slug>",
     "a frozen fixture is frozen"),

    ("the frozen digest is blanked, so rule 2 becomes a comment again",
     "tests/fixture/prd/SCHEMAS.json",
     '"frozen_sha256": "f8d4e3bd31a6cc8b1aada39f2f475a3cdc5c8f9a53978e1b6da797949d8b122f"',
     '"frozen_sha256": ""',
     "a frozen fixture is frozen"),

    ("the probe goes back to naming a version directly",
     "tests/probe-p1.py",
     'FIXTURE = os.path.join(REPO, "tests", "fixture", "prd", _SCHEMA, "staff-service")',
     'FIXTURE = os.path.join(REPO, "tests", "fixture", "prd", "schema-1", "staff-service")',
     "nothing hardcodes a schema fixture version"),

    ("the core's declared version drifts from the registry after the bump",
     CORE,
     '<schema-core version="schema-2"/>',
     '<schema-core version="schema-1"/>',
     "the schema core is one definition"),
]
