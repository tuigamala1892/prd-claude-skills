"""Mutants for the instruction that prose inside an artefact is XML text.

The ways back: core loses the rule, its example stops demonstrating it, or a command's writing
step stops pointing at it.
"""

CHECK = "both writing steps say prose in an artefact is XML text, and core's example parses"

MUTANTS = [
    ("core's escaped example is written unescaped, so it no longer parses",
     "schema/core.md",
     "Write *split `&lt;data-model&gt;` from `&lt;offers&gt;`* instead",
     "Write *split `<data-model>` from `&lt;offers&gt;`* instead",
     CHECK),

    ("core no longer says backticks do not escape",
     "schema/core.md",
     "**Markdown backticks are not an escape.**",
     "**Markdown backticks are an escape.**",
     CHECK),

    ("/prd's writing step stops pointing at core section 9",
     "commands/prd.md",
     "([core §9](../schema/core.md#9-text-inside-an-artefact-is-xml-text)). An unescaped one leaves\n  the file",
     "(see the core). An unescaped one leaves\n  the file",
     CHECK),

    ("/crd's pointer drops the ampersand",
     "commands/crd.md",
     "`&lt;offers&gt;` and a bare ampersand `&amp;`",
     "`&lt;offers&gt;` and a bare ampersand",
     CHECK),
]
