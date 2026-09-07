"""Mutants for schema-6 -- item 40's gate gets its second half.

The element being guarded is a RECORD, and the difference between a record and a claim is the
hash. So most of these break the hash rather than the element: a review that survives an edit, a
review that is stale the moment it is written, a reader that reports staleness and then passes it
anyway. Each of those leaves a `<review>` in the file and means nothing.

Two are worth reading twice.

  * `content_sha` hashing the whole file INCLUDING the review element is the version somebody
    writes first. It is self-defeating -- writing the review changes the file the review
    describes, so every review is stale on arrival -- and it looks completely reasonable.
  * R13 inventing a placeholder review is the migration doing the reviewer's job. The schema
    would be satisfied, the gate would pass, and nobody would have read anything.
"""

MUTANTS = [
    # ------------------------------------------------------------------ the hash rule
    ("the hash covers the review element too, so every review is stale on arrival",
     "skills/breakdown/scripts/check-definition.py",
     'return hashlib.sha256(REVIEW.sub("", text).encode("utf-8")).hexdigest()[:12]',
     'return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]',
     "the `defined` gate has both halves, and a stale review is not a review"),

    ("the review is a date and a name with nothing to check it against",
     "skills/breakdown/scripts/check-definition.py",
     'return ("reviewed" if attrs.get("sha") == content_sha(text) else "stale"), attrs',
     'return "reviewed", attrs',
     "the `defined` gate has both halves, and a stale review is not a review"),

    ("a stale review is reported and then passed by --strict anyway",
     "skills/breakdown/scripts/check-definition.py",
     "    return 1 if (args.strict and (edges or reviews)) else 0",
     "    return 1 if (args.strict and edges) else 0",
     "the `defined` gate has both halves, and a stale review is not a review"),

    ("a missing review stops being reported at all",
     "skills/breakdown/scripts/check-definition.py",
     '        if state == "absent":\n            reviews.append((r["file"], "no review recorded',
     '        if False:\n            reviews.append((r["file"], "no review recorded',
     "the `defined` gate has both halves, and a stale review is not a review"),

    ("the recorder signs the review itself, which is the adjective the element replaced",
     "skills/breakdown/scripts/check-definition.py",
     '        if not args.by:\n            print("REFUSED  --record-review needs --by NAME.',
     '        if False:\n            print("REFUSED  --record-review needs --by NAME.',
     "the `defined` gate has both halves, and a stale review is not a review"),

    # ------------------------------------------------------------------ the migration step
    ("the migration invents a review, and the gate passes without anybody reading anything",
     "schema/scripts/migrate.py",
     '    ("R13", "schema-6", "feature",\n'
     '     lambda t: _is_defined(t) and "<review" not in t,\n'
     "     lambda t: t,",
     '    ("R13", "schema-6", "feature",\n'
     '     lambda t: _is_defined(t) and "<review" not in t,\n'
     '     lambda t: t.replace("</meta>", \'  <review by="migrate" at="1970-01-01" sha="0"/>\\n</meta>\'),',
     "schema-6 migrates the half it can and reports the half nobody can"),

    ("an unreviewed tree is called finished, which is what PARTIAL exists to prevent",
     "schema/scripts/migrate.py",
     '     lambda t: not _is_defined(t) or "<review" in t),',
     "     lambda t: True),",
     "schema-6 migrates the half it can and reports the half nobody can"),

    ("the document status keeps a value nothing can classify",
     "schema/scripts/migrate.py",
     '    return DOC_STATUS.sub("<status>in-progress</status>", text, count=1)',
     "    return text",
     "schema-6 migrates the half it can and reports the half nobody can"),

    ("the status resolves toward `complete`, asserting an interview nobody finished",
     "schema/scripts/migrate.py",
     '    return DOC_STATUS.sub("<status>in-progress</status>", text, count=1)',
     '    return DOC_STATUS.sub("<status>complete</status>", text, count=1)',
     "schema-6 migrates the half it can and reports the half nobody can"),

    # ------------------------------------------------------------------ and the fixture itself
    ("the reference fixture stops passing the bar it is the reference for",
     "tests/fixture/prd/schema-6/link-shelf/features/list-links.md",
     '    <criterion id="4" pattern="unwanted-behaviour" priority="P0">',
     '    <criterion id="4" pattern="event-driven" priority="P0">',
     "the `defined` gate has both halves, and a stale review is not a review"),
]
