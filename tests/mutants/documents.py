"""Mutants for item 72 -- the top-level documents catch up with the repository.

These four checks guard PROSE, which is the class this repository has watched pass while doing
nothing more often than any other. So every mutant here restores a real historical state rather
than inventing a plausible one: `execute-task` in the model table and the file tree is what
ARCHITECTURE.md actually said for nine phases, `allowed-tools` in the frontmatter example is what
it actually taught, the one-flag load command is what README.md actually gave, and "None of this
is built" is what target-state-data-flow.md actually claimed after the plan closed.

If a mutant here survives, the check was decorative and the document goes stale again silently --
which is exactly how it got into this state the first time.
"""

MUTANTS = [
    # ------------------------------------------------- the layout, both directions
    ("ARCHITECTURE.md lists a skill that does not exist, as it did for nine phases",
     "ARCHITECTURE.md",
     "├── execute-verify/               independent verification",
     "├── execute-task/                 code implementation\n"
     "├── execute-verify/               independent verification",
     "describe the one on disk"),

    ("ARCHITECTURE.md drops a skill that does exist, which is the quieter direction",
     "ARCHITECTURE.md",
     "└── migrate/                      artefact schema migration (item 41)",
     "",
     "describe the one on disk"),

    ("ARCHITECTURE.md stops mentioning schema/, item 44's whole artefact",
     "ARCHITECTURE.md",
     "schema/                           the single definition both paths cite (item 44)",
     "sch3ma/                           the single definition both paths cite (item 44)",
     "describe the one on disk"),

    ("CLAUDE.md drops the agent it omitted through two phases",
     "CLAUDE.md",
     "├── prd-criteria-author.md    # Proposes criteria; reviews a definition (items 8, 40)\n",
     "",
     "describe the one on disk"),

    ("README.md's skill count goes stale again, which is how it was found",
     "README.md",
     "skills/<name>/SKILL.md       15 skills, most with references/ and scripts/",
     "skills/<name>/SKILL.md       14 skills, most with references/ and scripts/",
     "describe the one on disk"),

    ("README.md's agent count goes stale",
     "README.md",
     "agents/*.md                  10 subagent definitions",
     "agents/*.md                  8 subagent definitions",
     "describe the one on disk"),

    # ------------------------------------------------- the frontmatter example and the model table
    ("the fork example teaches allowed-tools again, which is the key that disables the fork",
     "ARCHITECTURE.md",
     "name: execute-batch\ncontext: fork\nmodel: claude-sonnet-5\n",
     "name: execute-batch\ncontext: fork\nmodel: claude-sonnet-5\nallowed-tools:\n  - Read\n",
     "frontmatter example is one a skill"),

    ("the model table disagrees with the frontmatter, as it did for every row",
     "ARCHITECTURE.md",
     "| `breakdown-generate-tasks` | `claude-opus-5` |",
     "| `breakdown-generate-tasks` | `claude-sonnet-5` |",
     "frontmatter example is one a skill"),

    ("the model table names a component that has not existed since item 4.15",
     "ARCHITECTURE.md",
     "| `execute-verify` | `claude-haiku-4-5` |",
     "| `execute-task` | `claude-haiku-4-5` |",
     "frontmatter example is one a skill"),

    # ------------------------------------------------- the load command
    ("README.md gives the one-flag load command again, and /breakdown stops in Phase 1",
     "README.md",
     "claude --plugin-dir /path/to/prd-claude-skills --add-dir /path/to/prd-claude-skills",
     "claude --plugin-dir /path/to/prd-claude-skills",
     "way to load the plugin"),

    ("CLAUDE.md loses --add-dir from its own measured instruction",
     "CLAUDE.md",
     "`claude --plugin-dir <checkout> --add-dir <checkout>`",
     "`claude --plugin-dir <checkout>`",
     "way to load the plugin"),

    # ------------------------------------------------- the target-state status
    ("target-state-data-flow.md claims again that none of it is built",
     "docs/skills/target-state-data-flow.md",
     "**Status:** **Reached.** Written 2026-08-25 as a target",
     "**Status:** Target state. **None of this is built.** Written 2026-08-25 as a target",
     "target state says whether"),

    ("the status says nothing either way, which is the half a reader still needs",
     "docs/skills/target-state-data-flow.md",
     "**Status:** **Reached.** Written 2026-08-25 as a target",
     "**Status:** Written 2026-08-25 as a target",
     "target state says whether"),

    # ------------------------------------------------- the checks' own controls
    # NOT a mutant on the block-scoping itself, and the reason is recorded rather than hidden.
    # `return blocks[0]` -> `return text` SURVIVES: unscoped, the whole of ARCHITECTURE.md still
    # satisfies every assertion, because nothing outside the tree happens to look like a
    # directory entry. The scoping is defensive rather than load-bearing on today's content, and
    # a mutant that cannot fail proves nothing about it. What CAN be shown is that the section is
    # located at all -- if the heading lookup breaks, the check has no subject.
    ("the layout check cannot find the section it reads, so it has no subject",
     "tests/test_toolchain.py",
     '                          (os.path.join(REPO, "CLAUDE.md"), "## Key Directories")):',
     '                          (os.path.join(REPO, "CLAUDE.md"), "## Keye Directories")):',
     "describe the one on disk"),

    ("the model table parse returns nothing, so the check would pass over its whole subject",
     "tests/test_toolchain.py",
     '        m = re.match(r"\\|\\s*`?/?([a-z0-9-]+)`?[^|]*\\|\\s*`?([a-z0-9.*()-]+)`?[^|]*\\|", line)',
     '        m = re.match(r"\\|\\s*ZZZ([a-z0-9-]+)\\s*\\|\\s*([a-z0-9.-]+)\\s*\\|", line)',
     "frontmatter example is one a skill"),
]
