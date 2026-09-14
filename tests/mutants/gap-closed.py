"""Gap closure: `closed` on <gap>, and only an open gap counts.

Core section 6 gained `closed` and `closed-by`. Every reader of <gap> now goes through one parser,
which trusts a closure only when it is a real date between `raised` and today; check-status.py
validates closures and reports the CRD `ready` rule (P70); closed gaps are never carried; and /prd
and /crd are where a person writes `closed`. The mutants take each of those apart one at a time --
including the ways a closure could open a gate early, which is the direction that matters.
"""

STATUS = "skills/breakdown/scripts/check-status.py"
SELECT = "skills/breakdown/scripts/select-features.py"
GATE = "skills/breakdown/scripts/check-gate.py"
WHAT_NEXT = "schema/scripts/build-what-next.py"
CORE = "schema/core.md"
CRD_FORMAT = "skills/crd/references/crd-format.md"

SCHEMA = "a resolved gap is closed rather than deleted, and the bar counts open gaps only"
READY_ANCHOR = "`/crd` cannot silently replace a CRD, and `ready` cannot outrank its gaps"
P70 = "a ready CRD carrying a specification gap is a contradiction the script reports"
SHAPE = "a closed gap is well-formed or refused, and its remainder takes a new id"
COUNT = "a closed gap counts toward nothing"
AGES = "gap ages count open gaps, and the gaps closed since a date can be listed"
CARRY = "a closed gap is never carried into the analysis or a task"
PRODUCE = "a person closes a gap in /prd and in /crd, and the challenger is handed the closures"
PARITY = "parity between the paths is a table with probes, and the probes resolve"

MUTANTS = [
    # --- P70: the CRD ready rule ------------------------------------------------------------------
    ("the CRD ready rule is not run, which is P70 reopened",
     STATUS,
     '        if workflow_of(text) == "ready" and "specification" in _sel.gaps_of(text, today):',
     "        if False:",
     P70),

    ("an unmigrated <status>ready</status> escapes the ready rule",
     STATUS,
     '    m = re.search(r"<(workflow|status)>\\s*([a-z-]+)\\s*</\\1>", meta.group(1))',
     '    m = re.search(r"<(workflow)>\\s*([a-z-]+)\\s*</\\1>", meta.group(1))',
     P70),

    # --- the one parser ---------------------------------------------------------------------------
    ("gaps_of() counts closed gaps again",
     SELECT,
     '            if GAP_KIND.fullmatch(a.get("kind", "")) and not is_closed(a, today)]',
     '            if GAP_KIND.fullmatch(a.get("kind", ""))]',
     COUNT),

    ("any closure is trusted, a future or unreal one included",
     SELECT,
     "    return raised <= closed <= (today or datetime.date.today())",
     "    return True",
     COUNT),

    ("a closed=\"soon\" is trusted because only presence is tested",
     SELECT,
     "    if closed is None or raised is None:\n        return False",
     '    if "closed" in attrs:\n        return True\n    if closed is None or raised is None:\n'
     "        return False",
     COUNT),

    ("the gate reads the gaps with its own regex instead of gaps_of()",
     GATE,
     '        for kind in sorted(set(row["gaps"]) & BLOCKING_GAPS):',
     '        own = open(document if not os.path.isdir(document) else os.path.join(document, '
     'row["file"]), encoding="utf-8").read()\n'
     "        for kind in sorted(set(re.findall(r'<gap\\b[^>]*\\bkind=\"([a-z]+)\"', own)) "
     "& BLOCKING_GAPS):",
     COUNT),

    ("<authoring-gaps> lists closed gaps",
     WHAT_NEXT,
     "        gaps = [a for a in _sel.gap_attrs_of(text) if not _sel.is_closed(a)]",
     "        gaps = _sel.gap_attrs_of(text)",
     COUNT),

    # --- check-status.py: ages, the closed count, --closed-since ----------------------------------
    ("closed gaps are aged as open",
     STATUS,
     "        if _sel.is_closed(attrs, today):",
     "        if False:",
     AGES),

    ("--closed-since excludes the gaps closed on the day itself",
     STATUS,
     "    listed = [c for c in closed if since is None or _sel.gap_date(c[5]) >= since]",
     "    listed = [c for c in closed if since is None or _sel.gap_date(c[5]) > since]",
     AGES),

    ("the summary no longer counts closed gaps",
     STATUS,
     '{len(ages)} gaps open, {len(closed)} closed{oldest}")',
     '{len(ages)} gaps open{oldest}")',
     AGES),

    # --- check-status.py: closure well-formedness -------------------------------------------------
    ("an unreal closed date is accepted",
     STATUS,
     "        if d is None:\n            bad.append(f\"{where} has closed={closed!r}, which is not",
     "        if False:\n            bad.append(f\"{where} has closed={closed!r}, which is not",
     SHAPE),

    ("a gap closed before it was raised is accepted",
     STATUS,
     "            if raised and d < raised:",
     "            if False:",
     SHAPE),

    ("a closure dated in the future is accepted",
     STATUS,
     "            if d > today:",
     "            if False:",
     SHAPE),

    ("closed-by on an open gap is accepted",
     STATUS,
     "        if closed is None:\n            bad.append(f\"{where} has closed-by={by!r}",
     "        if False:\n            bad.append(f\"{where} has closed-by={by!r}",
     SHAPE),

    ("closed-by naming a criterion that does not exist is accepted",
     STATUS,
     "        if missing:",
     "        if False:",
     SHAPE),

    ("a remainder may reuse the closed gap's id",
     STATUS,
     "        elif gid in seen:",
     '        elif gid in seen and "closed" not in rows[seen[gid] - 1]:',
     SHAPE),

    # --- carrying ---------------------------------------------------------------------------------
    ("the task format carries closed gaps",
     "skills/breakdown/references/task-format-spec.md",
     "**Carry the source document's open `<gaps>` into `<context>`, unchanged.**",
     "**Carry the source document's `<gaps>` into `<context>`, unchanged.**",
     CARRY),

    ("the analyzer copies closed gaps",
     "skills/breakdown-analyze-prd/SKILL.md",
     "**A closed gap is not copied.**",
     "**A closed gap is copied like any other.**",
     CARRY),

    ("/breakdown's report drops the closed count",
     "skills/breakdown/SKILL.md",
     ", 3 closed, not carried",
     "",
     CARRY),

    # --- the schema text --------------------------------------------------------------------------
    ("core section 6 drops `closed-by` from its attribute table",
     CORE,
     "| `closed-by` | No |",
     "| `closed_by` | No |",
     SCHEMA),

    ("core section 6's defined bar counts closed gaps",
     CORE,
     "**A `defined` artefact must not carry an open `specification` gap.**",
     "**A `defined` artefact must not carry a `specification` gap.**",
     SCHEMA),

    ("core section 6's ready bar counts closed gaps",
     CORE,
     "must not carry an open specification gap",
     "must not carry a specification gap",
     READY_ANCHOR),

    ("crd-format.md's ready rule counts closed gaps",
     CRD_FORMAT,
     'must not carry an open `<gap kind="specification">`',
     'must not carry a `<gap kind="specification">`',
     READY_ANCHOR),

    # --- the producers ----------------------------------------------------------------------------
    ("/prd's walk loses the partly-resolved answer",
     "commands/prd.md",
     "| partly resolved | close it as above",
     "| half done | close it as above",
     PRODUCE),

    ("/crd's walk loses the partly-resolved answer",
     "commands/crd.md",
     "| partly resolved | close it as above",
     "| half done | close it as above",
     PRODUCE),

    ("/prd's review is not handed the closures",
     "commands/prd.md",
     "           the gaps closed since its last review>,",
     "           >,",
     PRODUCE),

    ("/crd's closure review dispatches the wrong mode",
     "commands/crd.md",
     "mode: review-closures; the CRD file path",
     "mode: sign-off; the CRD file path",
     PRODUCE),

    ("the challenger may propose removing `closed`",
     "agents/prd-criteria-author.md",
     "**Never propose removing `closed`, and never propose reopening a gap.**",
     "**Propose removing `closed` where a closure was wrong.**",
     PRODUCE),

    # --- P71: found by this round ----------------------------------------------------------------
    ("the harness's failure parser crosses a line again",
     "tests/mutate.py",
     'r"^  FAIL[ \\t]+(.*?)[ \\t]{2,}"',
     'r"^  FAIL\\s+(.*?)\\s{2,}"',
     "the mutation harness sees every failing check, adjacent ones included"),

    ("parity.md cites a closure-review probe the CRD path does not have",
     "schema/parity.md",
     "`commands/crd.md :: review-closures`",
     "`commands/crd.md :: review-closures-by-date`",
     PARITY),
]
