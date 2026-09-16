"""Mutants for letter-suffixed criterion ids -- `7a` is one id, never a relative of `7`.

Core section 1 permits a suffix because a project that cites `7a` may not renumber it. Every
reader already compared ids as strings, so the suffix worked by accident. The ways back: any one
site reads an id by its leading integer, which makes `7a` a copy of `7` -- a false duplicate, a
closure that resolves to nothing, a criterion covered by a task that never named it -- or the
migration numbers a new id beside a surviving suffix.
"""

CHECK = "a letter-suffixed criterion id is one id to every reader and the migration -- by running it"

LETTERS = "abcdefghijklmnopqrstuvwxyz"

MUTANTS = [
    ("the migration counts only bare integers again, so a new 2 sits beside 2a",
     "schema/scripts/migrate.py",
     'ids = [int(m.group()) for m in (re.match(r"\\d+", i or "") for i in criterion_ids(text)) if m]',
     "ids = [int(i) for i in criterion_ids(text) if i and i.isdigit()]",
     CHECK),

    ("the bar's uniqueness test reads 3a as 3",
     "skills/breakdown/scripts/check-definition.py",
     'cid = c.get("id")',
     f'cid = (c.get("id") or "").rstrip("{LETTERS}") or None',
     CHECK),

    ("closed-by resolves against ids truncated to their integer",
     "skills/breakdown/scripts/check-status.py",
     "CRITERION_ID = re.compile(r'<criterion\\b[^>]*\\bid=\"([^\"]*)\"')",
     "CRITERION_ID = re.compile(r'<criterion\\b[^>]*\\bid=\"(\\d+)[^\"]*\"')",
     CHECK),

    ("coverage reads a feature's criterion ids by their integer",
     "skills/breakdown/scripts/check-coverage.py",
     "cid = re.search(r'id=\"([^\"]*)\"', attrs)",
     "cid = re.search(r'id=\"(\\d+)[^\"]*\"', attrs)",
     CHECK),

    ("the manifest strips the suffix from a task's satisfies-criteria",
     "skills/breakdown/scripts/build-manifest.py",
     'ids = [x.strip() for x in crit.split(",") if x.strip()]',
     f'ids = [x.strip().rstrip("{LETTERS}") for x in crit.split(",") if x.strip()]',
     CHECK),
]
