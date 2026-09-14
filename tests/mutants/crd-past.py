"""A finished CRD finishes its migration: R5, R10 and the validator exempt a record of the past.

The defect had three sites, and fixing one moved the refusal to the next: R5 demanded patterns,
R10 demanded patterns and a tier, and check-artefacts.py demanded the tier. Each is mutated back
separately. The last mutant widens the exemption to every CRD, which is the opposite mistake.
"""

MIGRATE = "schema/scripts/migrate.py"
CHECK = "a finished CRD completes its migration without anyone re-specifying it -- by running it"

MUTANTS = [
    ("R5 demands patterns of a finished CRD again",
     MIGRATE,
     '               and (_is_past(t) or not _criteria_lacking(t, "pattern"))),',
     '               and not _criteria_lacking(t, "pattern")),',
     CHECK),

    ("R10 demands patterns and a tier of a finished CRD again",
     MIGRATE,
     '               and (_is_past(t) or (not _criteria_lacking(t, "pattern")\n'
     '                                    and _meta_has(t, "priority")))),',
     '               and not _criteria_lacking(t, "pattern")\n'
     '               and _meta_has(t, "priority")),',
     CHECK),

    ("the validator demands a finished CRD's tier again",
     "schema/scripts/check-artefacts.py",
     '        if not (el(inner, "priority") or "").strip() and not _mig._is_past(text):',
     '        if not (el(inner, "priority") or "").strip():',
     CHECK),

    ("`abandoned` stops counting as a record of the past",
     MIGRATE,
     '    return bool(state and state.group(2) in ("complete", "abandoned"))',
     '    return bool(state and state.group(2) in ("complete",))',
     CHECK),

    ("every CRD is treated as a record of the past",
     MIGRATE,
     '    return bool(state and state.group(2) in ("complete", "abandoned"))',
     "    return True",
     CHECK),
]
