"""Item 44 -- the schema core, and the two checks that guard it.

Both checks went green the first time they ran, which by this repository's standard means
nothing at all. Six mutants: four against the citation graph, two putting an artefact template
back where it came from.

The via-row mutant (M4) is the one worth having. The first version of that check asserted only
the first hop -- that `commands/prd.md` links `prd-format.md` -- and would have passed happily
while `prd-format.md` had stopped citing the core. Breaking the second hop is what showed it.
"""

CORE = "schema/core.md"

MUTANTS = [
    ("the core's version drifts from the fixture registry",
     CORE,
     '<schema-core version="schema-6"/>',
     '<schema-core version="schema-5"/>',
     "the schema core is one definition"),

    ('a link out of the core dangles',
     'schema/core.md',
     '| [`prd-format.md`](prd-format.md) | identity, criteria, status, priority, significance |',
     '| [`prd-format.md`](prd-formats.md) | identity, criteria, status, priority, significance |',
     'the schema core is one definition'),

    ("a directly-citing document stops citing the core",
     "skills/breakdown/references/task-format-spec.md",
     "[core §2](../../../schema/core.md#2-acceptance-criteria)",
     "the acceptance criteria section",
     "the schema core is one definition"),

    ("the chain's second hop breaks: prd-format.md stops citing the core",
     "schema/prd-format.md",
     "priority — are defined in [`core.md`](core.md) and are **cited here, not restated**.",
     "priority — are defined below.",
     "the schema core is one definition"),

    ("a feature template comes back into the command that writes it",
     "commands/prd.md",
     "## Output Formats\n",
     "## Output Formats\n\n```xml\n<feature>\n  <meta>\n    <slug>{{slug}}</slug>\n"
     "  </meta>\n</feature>\n```\n",
     "no artefact template lives in a command file"),

    ("the CRD skill grows its own copy of the document shape again",
     "skills/crd/SKILL.md",
     "### Phase 8: Completion\n",
     "```xml\n<crd>\n  <meta>\n    <slug>{slug}</slug>\n  </meta>\n</crd>\n```\n\n"
     "### Phase 8: Completion\n",
     "no artefact template lives in a command file"),
]
