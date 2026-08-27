B = chr(92)
MUTANTS = [
    ("the enforcer returns 0 instead of refusing",
     "skills/breakdown/scripts/check-rules.py",
     "              \"exemption, deliberately.\", file=sys.stderr)\n        return 1",
     "              \"exemption, deliberately.\", file=sys.stderr)\n        return 0",
     "`<banned>` and `<task-limits>` are enforced"),

    ("judgement rules start refusing",
     "skills/breakdown/scripts/check-rules.py",
     'findings.append(Finding(kind, reason, "worktree",\n'
     '                                    f"for a model to weigh: {rule.get(\'body\') or \'\'}", '
     'False))',
     'findings.append(Finding(kind, reason, "worktree",\n'
     '                                    f"for a model to weigh: {rule.get(\'body\') or \'\'}", '
     'True))',
     "`<banned>` and `<task-limits>` are enforced"),

    ("the rule's <except> stops suppressing",
     "skills/breakdown/scripts/check-rules.py",
     "def excepted(rule, path):\n    for ex in rule.get(\"excepts\") or []:",
     "def excepted(rule, path):\n    return None\n    for ex in rule.get(\"excepts\") or []:",
     "`<banned>` and `<task-limits>` are enforced"),

    ("dotted imports stop resolving, so edge misses ordinary Python",
     "skills/breakdown/scripts/check-rules.py",
     '    if "." in target and worktree:',
     '    if False:',
     "`<banned>` and `<task-limits>` are enforced"),

    ("the same-unit guard is dropped, so a service importing itself is flagged",
     "skills/breakdown/scripts/check-rules.py",
     "                        if src.rstrip(\"/*\") and target.split(\"/\")[:2] == "
     "rel.split(\"/\")[:2]:\n                            continue",
     "                        if False:\n                            continue",
     "`<banned>` and `<task-limits>` are enforced"),

    ("scoped task-limits are ignored, so contracts/** gets the default 3",
     "skills/breakdown/scripts/check-rules.py",
     "            if any(matches(p, lim[\"match\"]) for p in declared):",
     "            if False:",
     "`<banned>` and `<task-limits>` are enforced"),

    ("task-limits stops being enforced at all",
     "skills/breakdown/scripts/check-rules.py",
     "    limits = rules.get(\"task_limits\")\n    if limits and declared:",
     "    limits = rules.get(\"task_limits\")\n    if False:",
     "`<banned>` and `<task-limits>` are enforced"),

    ("the reason is no longer reported verbatim",
     "skills/breakdown/scripts/check-rules.py",
     '        return f"  {head} [{self.kind}] {self.where}'
     + B + 'n           {self.detail}' + B + 'n           {self.reason}"',
     '        return f"  {head} [{self.kind}] {self.where}'
     + B + 'n           {self.detail}"',
     "`<banned>` and `<task-limits>` are enforced"),

    ("a change rule with no diff passes quietly instead of saying UNRESOLVED",
     "skills/breakdown/scripts/check-rules.py",
     '                findings.append(Finding(\n'
     '                    kind, reason, "diff",\n'
     '                    f"UNRESOLVED: no --base given, so the diff this rule is about was '
     'never "\n'
     '                    f"computed. The rule is NOT in force for this run", False))\n'
     '                continue',
     '                continue',
     "`<banned>` and `<task-limits>` are enforced"),

    ("content rules stop firing in review mode",
     "skills/breakdown/scripts/check-rules.py",
     'REVIEW_KINDS = ("import", "content")',
     'REVIEW_KINDS = ("import",)',
     "`<banned>` and `<task-limits>` are enforced"),

    ("review-tasks stops calling the enforcer",
     "skills/breakdown-review-tasks/SKILL.md",
     "python {skill_dir}/../breakdown/scripts/check-rules.py",
     "# review the task against the project's rules by eye",
     "`<banned>` and `<task-limits>` are enforced"),

    ("execute-verify stops calling the enforcer",
     "skills/execute-verify/SKILL.md",
     "python {skill_dir}/../breakdown/scripts/check-rules.py",
     "# check the project's rules by eye",
     "`<banned>` and `<task-limits>` are enforced"),

    ("execute-verify starts failing tasks on judgement findings",
     "skills/execute-verify/SKILL.md",
     "| `judgement` | prose for you to weigh | **report only — never fail** |",
     "| `judgement` | prose for you to weigh | fail the task |",
     "`<banned>` and `<task-limits>` are enforced"),
]
