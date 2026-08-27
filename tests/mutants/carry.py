"""Mutants for group 5b -- items 16, 17, 30, 19 and 20.

The two worth singling out:

`<priority> is overloaded with MoSCoW` is P3 arriving as a mutant. The whole reason item 16's
elements have the names they do is that `<priority>` already means merge order within the layer;
a check that only asserted "the tier is somewhere in <meta>" would pass on the overload.

`the shortfall is a count, not a name` is item 59's third assertion in miniature. A coverage check
reporting "1 feature has no task" passes any test that a check naming the WRONG feature would also
pass, so the mutant keeps the count correct and removes only the name.
"""

MUTANTS = [
    # ------------------------------------------------------------------ items 16, 17
    ("the task format stops declaring <moscow>, so the tier has nowhere to travel",
     "skills/breakdown/references/task-format-spec.md",
     "  <moscow>must-have</moscow>                          <!-- item 16: that feature's tier -->\n",
     "",
     "a task names the feature and criteria it came from"),

    ("<priority> is overloaded with MoSCoW, which is P3 exactly",
     "skills/breakdown/references/task-format-spec.md",
     "  <priority>1</priority>              <!-- Execution order within layer (1 = first) -->\n"
     "  <estimated-files>2</estimated-files> <!-- Number of files to create/modify -->\n"
     "  <cwd>packages/billing</cwd>         <!-- Optional; where commands run. See below -->\n\n"
     "  <source-feature>",
     "  <priority>must-have</priority>      <!-- Execution order within layer (1 = first) -->\n"
     "  <estimated-files>2</estimated-files> <!-- Number of files to create/modify -->\n"
     "  <cwd>packages/billing</cwd>         <!-- Optional; where commands run. See below -->\n\n"
     "  <source-feature>",
     "a task names the feature and criteria it came from"),

    ("the criteria go back to being excerpted as prose, which is how P2 happens",
     "skills/breakdown/references/task-format-spec.md",
     "  <acceptance-criteria>\n    <criterion id=\"4\" pattern=\"event-driven\" priority=\"P0\">",
     "  <criteria-summary>\n    <criterion id=\"4\" pattern=\"event-driven\" priority=\"P0\">",
     "a task names the feature and criteria it came from"),

    ("the generator may rewrite a criterion instead of copying it",
     "skills/breakdown-generate-tasks/SKILL.md",
     "**Copy each `<criterion>` element whole, with its `id`, `pattern` and `priority`.**",
     "**Summarise each criterion into the task's own words.**",
     "a task names the feature and criteria it came from"),

    ("build-manifest drops the traceability, so every downstream reader attributes nothing",
     "skills/breakdown/scripts/build-manifest.py",
     "        entry.update(traceability(path))",
     "        pass",
     "the analysis predicts size and certainty"),

    # ------------------------------------------------------------------ item 30
    ("the coverage shortfall becomes a count, losing the name that makes it falsifiable",
     "skills/breakdown/scripts/check-coverage.py",
     '"uncovered_features": [{"slug": r["slug"], "tier": r["tier"]} for r in uncovered],',
     '"uncovered_features": [{"slug": "a feature", "tier": r["tier"]} for r in uncovered],',
     "the task set is checked against the document"),

    ("item 13's runtime backstop stops firing, so wont-have work is built",
     "skills/breakdown/scripts/check-coverage.py",
     '            if any("item 13" in r for r in why):',
     '            if False:',
     "the task set is checked against the document"),

    ("a task citing a criterion that does not exist is no longer reported",
     "skills/breakdown/scripts/check-coverage.py",
     "        for cid in sorted(got - known, key=lambda x: (len(x), x)):",
     "        for cid in sorted(set() - known, key=lambda x: (len(x), x)):",
     "the task set is checked against the document"),

    # ------------------------------------------------------------------ items 19, 20
    ("the tier summary is not derived, so <requirement-level> has no reader at all",
     "skills/execute/scripts/write-state.py",
     '        "tiers": tier_summary(tasks),',
     '        "tiers": {},',
     "/execute reports the tier it built"),

    ("tasks with no tier stop being counted, so a partial report looks complete",
     "skills/execute/scripts/write-state.py",
     '    if unattributed:\n        summary["unattributed"] = unattributed',
     '    if False:\n        summary["unattributed"] = unattributed',
     "/execute reports the tier it built"),

    ("preflight stops refusing won't-have work, and item 20 protects nothing",
     "skills/execute/scripts/preflight.sh",
     'wont=$(grep -rl "<moscow>wont-have</moscow>" "$tasks_abs" 2>/dev/null | sort)',
     'wont=""',
     "/execute reports the tier it built"),
]
