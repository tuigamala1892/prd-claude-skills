#!/usr/bin/env python3
"""Is each feature's `<definition>` label honest about its own content? (item 3, §4.2)

A PRD is edited over weeks. The label is written once, at the moment a feature is drafted, and
the content moves under it -- so the features `/prd` did not touch this session are exactly the
ones whose labels have gone stale (item 7). Nothing has ever checked one against the other.

A CEILING, NOT A VALUE -- AND THE DIRECTION IS THE WHOLE DESIGN

The first version of this rule derived a *value* and compared it to the declared one. Re-run
against a later corpus it contradicted an author: a feature held at `in-progress` whose content
supported `defined`, for reasons the file cannot express -- a review not yet done, a boundary
expected to move. Deriving a value calls that a defect. Deriving a CEILING calls it fine.

So: report where declared EXCEEDS what the content supports; stay silent where it sits below.
Nothing is ever promoted by this script, because the absence of evidence is not evidence.

WHAT THE CEILING IS BUILT FROM (§4.2's `Required content` column, and nothing else)

  0 criteria                                          ceiling `tbd`
  >=1 criterion                                       ceiling `in-progress`
  ... plus `<user-story>` and no specification gap    ceiling `defined`

`excluded` and `superseded` are off the ladder -- they are definition states about a feature
nobody is building, not degrees of completeness -- so each is checked against the element §4.2
pairs it with instead.

THE BYTE COUNTS ARE GONE, AND THAT IS AN IMPROVEMENT RATHER THAN A SIMPLIFICATION

Item 3's measured rule tested for "a data-model / dependency / relationship marker in the notes"
and for ">=1000 bytes of notes". Both were proxies for elements that did not exist yet: at
schema-4 the marker became `<data-model>` and the dependency became `<depends-on>`, and a proxy
kept alongside the thing it stood for is a second answer to one question. The byte thresholds
went with them -- a small feature that is completely specified is not `tbd`, and on the reference
fixture the count rule said it was.

WHERE THE AMBIGUOUS BAND WENT

Item 3's rule was three-valued: agree / ambiguous / contradicted, where `ambiguous` meant *the
counters cannot see this one*. The ladder above is deterministic and has no ambiguous band -- but
the question it could not answer has not gone away, it has moved to `check-definition.py`, which
has the eight tests for it (item 40). This script asks whether the label is CONTRADICTED by the
file's own structure; that one asks whether the feature is actually well defined. Two questions,
two exit codes, one each.

WHAT ELSE IS HERE, AND WHY IT IS NOT A SECOND SCRIPT

`<gaps>` well-formedness and gap age. A gap is the one element that can bar `defined` outright
(core §6), so the check that reads it for the ceiling is the check that already has it parsed.
Age is REPORTED and never judged: a gap raised months ago is a different object from one raised
yesterday, and only the date shows it.

USAGE

    check-status.py <prd-dir|crd-file> [--today YYYY-MM-DD] [--closed-since YYYY-MM-DD]
                    [--strict] [--quiet] [--json]

  --today    the date gap ages are measured from. Defaults to the system date; passing it is
             what makes an age assertion reproducible
  --closed-since
             list the gaps closed on or after this date, with the criteria that closed them --
             what a review of the fill is checked against (core 6)
  --strict   exit non-zero on escalations too, not only on contradictions

A gap carrying a trusted `closed` date is CLOSED: validated, counted, and never aged. Only open
gaps reach the ceiling, the CRD `ready` rule and the `AGE` lines.

EXIT CODES

  0  no declared status exceeds its ceiling (escalations may have been reported)
  1  at least one contradiction
  2  usage error, or the PRD could not be read
"""

import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# The rules for reading a feature file live in ONE place. Re-deriving "what does this file
# declare" here would give the toolchain two answers to that question, and the interesting
# failures are exactly the ones where they disagree (check-coverage.py makes the same import).
_spec = importlib.util.spec_from_file_location(
    "select_features", os.path.join(_HERE, "select-features.py"))
_sel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sel)

# The ladder, lowest first. `excluded` and `superseded` are deliberately absent: they are not
# degrees of definition, so comparing them with `<` would be comparing unlike things.
LADDER = ["tbd", "in-progress", "defined"]
OFF_LADDER = {"excluded", "superseded"}

GAP_KINDS = {"specification", "dependency", "decision", "ownership", "evidence"}

CRITERION = re.compile(r"<criterion\b", re.S)
USER_STORY = re.compile(r"<user-story>\s*(.*?)\s*</user-story>", re.S)
RATIONALE = re.compile(r"<rationale>\s*(.*?)\s*</rationale>", re.S)
SUPERSEDED_BY = re.compile(r'<superseded-by\b[^>]*\bslug="([^"]*)"')
CRITERION_ID = re.compile(r'<criterion\b[^>]*\bid="([^"]*)"')
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# *What document is this* has ONE answer in this toolchain, and it is `migrate.py`'s ROOTS --
# the same table `check-artefacts.py` reads. A second root regex here would be a second answer,
# which is the defect `checks.md` exists to prevent and the reason this dispatch is safe at all.
_mspec = importlib.util.spec_from_file_location(
    "migrate", os.path.join(_HERE, os.pardir, os.pardir, os.pardir,
                            "schema", "scripts", "migrate.py"))
_mig = importlib.util.module_from_spec(_mspec)
_mspec.loader.exec_module(_mig)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def ceiling(text):
    """The highest `<definition>` this file's own structure supports, and why.

    Returns (ceiling, reason). The reason is what makes a report actionable: `declared defined,
    ceiling in-progress` says nothing a person can act on; naming the absent element does.
    """
    criteria = len(CRITERION.findall(text))
    if criteria == 0:
        return "tbd", "no <criterion> is written"

    story = USER_STORY.search(text)
    if not story or not story.group(1).strip():
        return "in-progress", "<user-story> is absent, and `defined` requires one"

    if "specification" in _sel.gaps_of(text):
        return ("in-progress",
                'it carries a <gap kind="specification"> -- claiming to be fully specified '
                "while declaring the specification incomplete is a contradiction (core 6)")

    return "defined", f"{criteria} criteria, a user story, and no specification gap"


def workflow_of(text):
    """A CRD's `<workflow>`, accepting the pre-item-45 `<status>` on read. Core section 3.

    The backreference is what stops `<workflow>x</status>` being read as either.
    """
    meta = re.search(r"<meta>(.*?)</meta>", text, re.S)
    if not meta:
        return None
    m = re.search(r"<(workflow|status)>\s*([a-z-]+)\s*</\1>", meta.group(1))
    return m.group(2) if m else None


def gap_rows(text):
    """Every `<gap>` with its attributes, in document order, whether or not they are valid.

    Parsed by `select-features.py`, which every other gap reader also uses: two regexes for one
    element is two answers to *what does this file declare*.
    """
    return _sel.gap_attrs_of(text)


def criterion_ids(text):
    """The `<criterion id=>` values a `closed-by` may name."""
    return set(CRITERION_ID.findall(text))


def check_feature(row, prd_dir, indexed_slugs):
    """Contradictions and escalations for one feature. Neither list stops the other."""
    bad, soft = [], []
    rel = row["file"]
    declared = row["definition"]

    if row["missing"]:
        # Not a contradiction here. A dangling index entry is `check-rename.py`'s assertion, and
        # a label cannot contradict content that does not exist.
        soft.append(f"{rel}: not read -- the index names a file that does not exist "
                    f"(check-rename.py owns that)")
        return bad, soft, []

    text = read(os.path.join(prd_dir, rel.replace("/", os.sep)))

    if declared is None:
        bad.append(f"{rel}: declares no <definition>, so nothing states how far it is defined")
        return bad, soft, gap_rows(text)

    if declared in OFF_LADDER:
        # Not compared with the ladder. §4.2 pairs each with the element that records the
        # decision, and a file recording a decision nobody can reconstruct is the defect.
        if declared == "excluded" and not RATIONALE.search(text):
            bad.append(f"{rel}: `excluded` with no <rationale> -- the file records that this is "
                       f"not being built and not why")
        if declared == "superseded":
            if not SUPERSEDED_BY.search(text):
                bad.append(f"{rel}: `superseded` with no <superseded-by> -- nothing names the "
                           f"feature that absorbed it")
            if row["slug"] in indexed_slugs:
                bad.append(f"{rel}: `superseded` and still in index.md -- the template removes "
                           f"it from the index, and leaving it there offers it for breakdown")
        return bad, soft, gap_rows(text)

    if declared not in LADDER:
        bad.append(f"{rel}: <definition>{declared}</definition> is not one of "
                   f"{'|'.join(LADDER + sorted(OFF_LADDER))}")
        return bad, soft, gap_rows(text)

    top, why = ceiling(text)
    if LADDER.index(declared) > LADDER.index(top):
        bad.append(f"{rel}: declared `{declared}`, ceiling `{top}`, because {why}")
    elif LADDER.index(declared) < LADDER.index(top):
        # Silent by design at the default level. The author may be holding it lower on purpose,
        # and this script never overturns that -- so it is an observation, not a finding.
        soft.append(f"{rel}: declared `{declared}`, content supports `{top}` ({why})")

    return bad, soft, gap_rows(text)


def check_closure(where, attrs, today, bad, criteria):
    """Core section 6's closure rules that one file can show. Reports; decides nothing.

    Whether a gap COUNTS as closed is `select-features.is_closed()`, the one definition every
    reader shares -- so a closure refused here is also a closure every reader treats as open.
    """
    closed = attrs.get("closed")
    by = attrs.get("closed-by")

    if closed is not None:
        d = _sel.gap_date(closed)
        raised = _sel.gap_date(attrs.get("raised"))
        if d is None:
            bad.append(f"{where} has closed={closed!r}, which is not a real YYYY-MM-DD date -- "
                       f"every reader holds the gap OPEN until it is")
        else:
            if raised and d < raised:
                bad.append(f"{where} has closed={closed}, before raised={attrs['raised']} -- a "
                           f"gap cannot be answered before it was asked")
            if d > today:
                bad.append(f"{where} has closed={closed}, after {today} -- a closure dated in "
                           f"the future would open a gate early, so every reader holds the gap "
                           f"OPEN")

    if by is not None:
        ids = by.split()
        if closed is None:
            bad.append(f"{where} has closed-by={by!r} and no closed -- an open gap has not been "
                       f"resolved by anything")
        if not ids:
            bad.append(f"{where} has an empty closed-by -- name the criteria, or omit it")
        missing = [i for i in ids if i not in criteria]
        if missing:
            bad.append(f"{where} has closed-by naming criteria {' '.join(missing)}, which this "
                       f"document does not define (core 6)")


def check_gaps(rel, rows, today, bad, ages, closed=None, criteria=()):
    """Validate every gap, and age the OPEN ones. A trusted closure goes to `closed` instead.

    Ids are unique across open and closed gaps alike, which is what makes *close it and raise the
    rest as a new gap* enforceable: the remainder cannot reuse the closed gap's id.
    """
    seen = {}
    for i, attrs in enumerate(rows, start=1):
        where = f"{rel}: <gap> {i}"
        gid = attrs.get("id")
        kind = attrs.get("kind")
        raised = attrs.get("raised")

        if not gid:
            bad.append(f"{where} has no id -- nothing can cite it from a commit or a review")
        elif gid in seen:
            bad.append(f"{where} repeats id {gid}, already used by gap {seen[gid]}")
        else:
            seen[gid] = i

        if kind not in GAP_KINDS:
            bad.append(f"{where} has kind={kind!r}, which is not one of "
                       f"{'|'.join(sorted(GAP_KINDS))} (core 6)")

        check_closure(where, attrs, today, bad, criteria)

        if not raised or not ISO_DATE.match(raised):
            bad.append(f"{where} has raised={raised!r} -- without a date an open item and a "
                       f"stale one look identical")
            continue
        try:
            d = datetime.date.fromisoformat(raised)
        except ValueError:
            bad.append(f"{where} has raised={raised!r}, which is not a real date")
            continue
        if _sel.is_closed(attrs, today):
            if closed is not None:
                shut = _sel.gap_date(attrs["closed"])
                closed.append(((shut - d).days, rel, gid or "?", kind or "?", raised,
                               attrs["closed"], attrs.get("closed-by", "")))
            continue
        ages.append((max((today - d).days, 0), rel, gid or "?", kind or "?", raised))


def report(bad, soft, ages, counted, noun, as_json, quiet, strict, closed=(), since=None):
    """One reporting path for both document shapes, so the two cannot drift apart.

    `ages` is the OPEN gaps and `closed` the closed ones; `oldest` measures open gaps only. The
    closed gaps are listed only when `since` asks for them -- that list is what `/prd` hands the
    challenger, the gaps closed since a feature's last review -- and counted always, so a document
    whose gaps were all resolved does not read as one that never declared any.
    """
    listed = [c for c in closed if since is None or _sel.gap_date(c[5]) >= since]
    if as_json:
        print(json.dumps({noun: counted, "contradictions": bad, "escalations": soft,
                          "gaps": [{"days": d, "file": f, "id": i, "kind": k, "raised": r}
                                   for d, f, i, k, r in ages],
                          "closed": [{"days_open": d, "file": f, "id": i, "kind": k, "raised": r,
                                      "closed": c, "closed_by": b.split()}
                                     for d, f, i, k, r, c, b in listed]}, indent=2))
    elif not quiet:
        for line in bad:
            print(f"  CONTRADICTION  {line}")
        for line in soft:
            print(f"  ESCALATE       {line}")
        for days, rel, gid, kind, raised in sorted(ages, reverse=True):
            print(f"  AGE            {rel}: gap {gid} ({kind}) raised {raised}, {days} days ago")
    if since is not None and not as_json:
        for days, rel, gid, kind, raised, shut, by in sorted(listed, key=lambda c: c[5]):
            by = f", by criteria {by}" if by else ""
            print(f"  CLOSED         {rel}: gap {gid} ({kind}) raised {raised}, closed {shut} "
                  f"after {days} days{by}")

    oldest = f", oldest gap {max(a[0] for a in ages)} days" if ages else ""
    print(f"{counted} {noun} checked: {len(bad)} contradictions, "
          f"{len(soft)} escalated, {len(ages)} gaps open, {len(closed)} closed{oldest}")

    if bad:
        return 1
    return 1 if (strict and soft) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir", metavar="prd-dir|crd-file")
    ap.add_argument("--today", default=None,
                    help="date gap ages are measured from (YYYY-MM-DD)")
    ap.add_argument("--closed-since", default=None,
                    help="list the gaps closed on or after this date (YYYY-MM-DD)")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    since = None
    if args.closed_since is not None:
        since = _sel.gap_date(args.closed_since)
        if since is None:
            print(f"REFUSED  --closed-since {args.closed_since} is not a real YYYY-MM-DD date",
                  file=sys.stderr)
            return 2

    prd_dir = args.prd_dir
    if not os.path.exists(prd_dir):
        print(f"REFUSED  no such path: {prd_dir}", file=sys.stderr)
        return 2
    if not os.path.isdir(prd_dir) and _mig.kind_of(read(prd_dir)) != "crd":
        # A file that is not a CRD is REFUSED rather than checked and found to have no gaps.
        # `0 gaps open` over an arbitrary file is the silence this whole class is made of: it
        # reads as an assertion that passed and is an assertion that never ran.
        print(f"REFUSED  not a PRD directory, and not a CRD: {prd_dir}", file=sys.stderr)
        return 2

    if args.today:
        if not ISO_DATE.match(args.today):
            print(f"REFUSED  --today {args.today} is not YYYY-MM-DD", file=sys.stderr)
            return 2
        today = datetime.date.fromisoformat(args.today)
    else:
        today = datetime.date.today()

    # A CRD is one file and carries no <definition>, so the ladder above has nothing to compare
    # -- core section 3 makes <workflow> a process position rather than a degree of definition.
    # The `<gaps>` half is the same assertion on both paths, and `check_gaps()` was already
    # path-agnostic, so this is a dispatch rather than a second copy of core section 6's enum.
    if not os.path.isdir(prd_dir):
        bad, ages, closed = [], [], []
        text = read(prd_dir)
        rel = os.path.basename(prd_dir)
        # Core section 6's rule for <workflow>, which is <definition>'s with one word changed. The
        # prose called it mechanical from item 48 and nothing ran it: this branch validated the
        # gaps and never compared them with the workflow (P70). One way only, as the ladder is --
        # a `draft` CRD with no gap is never promoted.
        if workflow_of(text) == "ready" and "specification" in _sel.gaps_of(text, today):
            bad.append(f'{rel}: <workflow>ready</workflow> while carrying an open '
                       f'<gap kind="specification"> -- ready for implementation and the '
                       f'specification is incomplete cannot both be true (core 6). It is `draft` '
                       f'until the gap is closed')
        check_gaps(rel, gap_rows(text), today, bad, ages, closed, criterion_ids(text))
        return report(bad, [], ages, 1, "change request(s)",
                      args.json, args.quiet, args.strict, closed, since)

    rows, err = _sel.features_of_prd(prd_dir)
    if err:
        print(f"REFUSED  {err}", file=sys.stderr)
        return 2

    indexed = {r["slug"] for r in rows}

    # A `superseded` feature has no index entry (§4.2), so the index alone cannot enumerate the
    # feature set. Walking features/ is what makes the off-ladder rules reachable at all.
    fdir = os.path.join(prd_dir, "features")
    if os.path.isdir(fdir):
        for name in sorted(os.listdir(fdir)):
            if not name.endswith(".md"):
                continue
            slug = os.path.splitext(name)[0]
            if slug in indexed:
                continue
            text = read(os.path.join(fdir, name))
            rows.append({"slug": slug, "name": _sel.name_of(text, slug), "tier": None,
                         "file": f"features/{name}", "definition": _sel.definition_of(text),
                         "gaps": _sel.gaps_of(text), "missing": False})

    bad, soft, ages, closed = [], [], [], []
    for row in rows:
        b, s, gaps = check_feature(row, prd_dir, indexed)
        bad.extend(b)
        soft.extend(s)
        if not row["missing"]:
            # A `closed-by` names criteria in the SAME document, so each feature resolves
            # against its own file and never against a neighbour's ids.
            ids = criterion_ids(read(os.path.join(prd_dir, row["file"].replace("/", os.sep))))
            check_gaps(row["file"], gaps, today, bad, ages, closed, ids)

    return report(bad, soft, ages, len(rows), "features",
                  args.json, args.quiet, args.strict, closed, since)


if __name__ == "__main__":
    sys.exit(main())
