#!/usr/bin/env python3
"""Decide which features `/breakdown` may turn into tasks, and say what it left out (items 13,
14 and 15; finding P1).

`/breakdown` filtered NOTHING. It read every feature named in the index and generated tasks for
all of them -- so a `wont-have` feature nobody intends to build, a `superseded` one that has been
absorbed into another, and a `tbd` one consisting of a name and a sentence all arrived at
`/execute` as work. That is P1, and it is three separate rules wearing one symptom.

THREE RULES, AND THEY ARE NOT THE SAME KIND OF RULE

  item 13   wont-have, excluded, superseded      EXCLUDED    correctness. No flag, no override
  item 14   below the --priority threshold       EXCLUDED    the operator's choice
  item 15   not defined enough to build          REFUSED     a defect in the PRD, and it is named

Only the middle one is a preference. Item 13 is not: a `wont-have` feature is one somebody
decided against, and offering a flag to build it anyway would make the decision advisory.
Item 15 is not either -- breaking down an underspecified feature does not produce a thin task,
it produces an INVENTED one, and TDD then locks the invention in as passing tests.

EVERY REASON IS REPORTED, NOT THE FIRST ONE THAT MATCHED

A feature is commonly excluded by more than one rule at once -- the reference fixture's
`quokka-telemetry` is `wont-have` AND carries a specification gap AND is `in-progress`. Reporting
only the first match would make the other two invisible, and would mean that fixing one reason
appears to change nothing. So each excluded feature carries the full list.

THE GAP BLOCK BEATS THE STATUS, AND THAT IS ITEM 15's REAL CONTENT

A `<definition>` is a summary; `<gaps>` is the detail. A `specification` gap refuses the feature
whatever its declared status, because it is the author saying the specification is incomplete. The
other four kinds -- dependency, decision, evidence, ownership -- WARN and do not refuse: they say
the feature is specified but not yet buildable, which is a scheduling fact rather than a
definition defect. A boolean could not have made that distinction.

USAGE

    select-features.py <prd-dir|crd-file> [--priority <tier>] [--include-tbd] [--json] [--quiet]

  --priority   must-have | should-have | could-have   (default: could-have -- all three tiers)
  --include-tbd   build features whose <definition> is `tbd` anyway. Does NOT reach a
                  specification gap, which is a statement about content rather than about status

  exit 0  at least one feature was selected
  exit 1  nothing was selected; the report says why for every feature
  exit 2  usage error, or the PRD could not be read
"""

import argparse
import datetime
import json
import os
import re
import sys

# MoSCoW, most important first. `wont-have` is in the list because it must be RECOGNISED; it is
# never selected, which is item 13 rather than a threshold.
TIERS = ["must-have", "should-have", "could-have", "wont-have"]
SELECTABLE = TIERS[:3]

# Core §6. Only the first refuses; the rest are scheduling facts, and a run halted by every open
# item is a run nobody leaves unattended.
REFUSING_GAPS = {"specification"}

FEATURE_ENTRY = re.compile(
    r'<feature\s+priority="([^"]+)"\s+file="([^"]+)"\s*>(.*?)</feature>', re.S)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def name_of(block, fallback):
    m = re.search(r"<name>\s*(.*?)\s*</name>", block, re.S)
    return " ".join(m.group(1).split()) if m else fallback


def definition_of(text):
    """`<definition>`, accepting the pre-item-45 `<status>` on read. Core §3."""
    meta = re.search(r"<meta>(.*?)</meta>", text, re.S)
    if not meta:
        return None
    for tag in ("definition", "status"):
        m = re.search(r"<%s>\s*([a-z-]+)\s*</%s>" % (tag, tag), meta.group(1))
        if m:
            return m.group(1)
    return None


GAP = re.compile(r"<gap\b([^>]*)>", re.S)
GAP_ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')
GAP_KIND = re.compile(r"[a-z]+")
GAP_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def gap_attrs_of(text):
    """Every `<gap>`'s attributes, open and closed, in document order, valid or not.

    The one gap parser in the toolchain. `check-status.py` validates these rows and
    `build-what-next.py` points at them; every other reader wants `gaps_of()`.
    """
    return [dict(GAP_ATTR.findall(attrs)) for attrs in GAP.findall(text)]


def gap_date(value):
    """A gap's `raised` or `closed` as a date, or None when it is not a real YYYY-MM-DD."""
    if not value or not GAP_DATE.fullmatch(value):
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def is_closed(attrs, today=None):
    """Whether a gap is closed -- core section 6 -- by a closure this reader can TRUST.

    `closed` must be a real date, not earlier than `raised` and not later than today. Anything
    else leaves the gap OPEN. That is deliberate and it is the safe direction: `/breakdown` never
    runs `check-status.py`, which is where a bad closure is refused, so a `closed="soon"` treated
    as closed here would open item 29's stop on a typo. A gap wrongly held open blocks a run; a
    gap wrongly read as closed waves one through.
    """
    closed = gap_date(attrs.get("closed"))
    raised = gap_date(attrs.get("raised"))
    if closed is None or raised is None:
        return False
    return raised <= closed <= (today or datetime.date.today())


def gaps_of(text, today=None):
    """The kinds of the OPEN gaps. A closed gap is kept as a record and counts toward nothing."""
    return [a["kind"] for a in gap_attrs_of(text)
            if GAP_KIND.fullmatch(a.get("kind", "")) and not is_closed(a, today)]


def judge(tier, definition, gaps, threshold, include_tbd):
    """Every reason this feature is out, and every reason it is merely worrying.

    Returns (excluded_reasons, warnings). A feature is built when the first list is empty.
    """
    out, warn = [], []

    # ---- item 13. Correctness, and deliberately not overridable.
    if tier == "wont-have":
        out.append("item 13: `wont-have` -- somebody decided against building this")
    if definition == "excluded":
        out.append("item 13: `<definition>excluded</definition>` -- see its `<rationale>`")
    if definition == "superseded":
        out.append("item 13: `<definition>superseded</definition>` -- see `<superseded-by>`")

    # ---- item 14. The operator's threshold, and the only rule here that is a preference.
    if tier in SELECTABLE and TIERS.index(tier) > TIERS.index(threshold):
        out.append(f"item 14: `{tier}` is below the `--priority {threshold}` threshold")

    # ---- item 15. A defect in the PRD, so it is named rather than quietly dropped.
    refusing = sorted(set(gaps) & REFUSING_GAPS)
    for kind in refusing:
        out.append(f"item 15: carries a `<gap kind=\"{kind}\">` -- the author says the "
                   f"specification is incomplete")
    if definition == "tbd" and not include_tbd:
        out.append("item 15: `<definition>tbd</definition>` -- a name and roughly one criterion. "
                   "Breaking it down invents the rest, and TDD locks the invention in "
                   "(`--include-tbd` overrides)")

    for kind in sorted(set(gaps) - REFUSING_GAPS):
        warn.append(f"carries a `<gap kind=\"{kind}\">` -- specified, but not yet buildable")

    return out, warn


def features_of_prd(prd_dir):
    index = os.path.join(prd_dir, "index.md")
    if not os.path.isfile(index):
        return None, f"no index.md in {prd_dir}"
    rows = []
    for tier, rel, block in FEATURE_ENTRY.findall(read(index)):
        slug = os.path.splitext(os.path.basename(rel))[0]
        path = os.path.join(prd_dir, rel.replace("/", os.sep))
        text = read(path) if os.path.isfile(path) else ""
        rows.append({
            "slug": slug,
            "name": name_of(block, slug),
            "tier": tier,
            "file": rel,
            "definition": definition_of(text),
            "gaps": gaps_of(text),
            "missing": not os.path.isfile(path),
        })
    if not rows:
        return None, f"{index} names no features"
    return rows, None


def features_of_crd(path):
    """A CRD is one item, so the 'set' has one row. Item 47 is what gives it a tier at all."""
    text = read(path)
    meta = re.search(r"<meta>(.*?)</meta>", text, re.S)
    tier = None
    if meta:
        m = re.search(r"<priority>\s*([a-z-]+)\s*</priority>", meta.group(1))
        tier = m.group(1) if m else None
    slug = re.search(r"<slug>\s*([a-z0-9-]+)\s*</slug>", text)
    return [{
        "slug": slug.group(1) if slug else os.path.splitext(os.path.basename(path))[0],
        "name": name_of(text, "change request"),
        "tier": tier or "must-have",
        "file": os.path.basename(path),
        "definition": None,
        "gaps": gaps_of(text),
        "missing": False,
        "tier_declared": tier is not None,
    }], None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", metavar="prd-dir|crd-file")
    ap.add_argument("--priority", default="could-have", choices=SELECTABLE,
                    help="lowest tier to build (default: could-have -- all three)")
    ap.add_argument("--include-tbd", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"usage: no such path: {args.path}", file=sys.stderr)
        return 2

    if os.path.isdir(args.path):
        rows, err = features_of_prd(args.path)
    else:
        rows, err = features_of_crd(args.path)
    if err:
        print(f"cannot select: {err}", file=sys.stderr)
        return 2

    selected, dropped = [], []
    for row in rows:
        out, warn = judge(row["tier"], row["definition"], row["gaps"],
                          args.priority, args.include_tbd)
        if row["missing"]:
            out.append(f"the index points at {row['file']}, which does not exist")
        row["reasons"], row["warnings"] = out, warn
        (dropped if out else selected).append(row)

    # The sentence item 15 exists to make sayable. A must-have that cannot be built is the single
    # most useful thing this command can report about a PRD, and it is called out separately
    # BECAUSE it would otherwise be one line among twenty and read as routine.
    undefined_musts = [r for r in dropped if r["tier"] == "must-have"
                       and any("item 15" in x for x in r["reasons"])]

    if args.json:
        print(json.dumps({
            "threshold": args.priority,
            "include_tbd": args.include_tbd,
            "selected": [r["slug"] for r in selected],
            "dropped": [{"slug": r["slug"], "tier": r["tier"], "reasons": r["reasons"]}
                        for r in dropped],
            "warnings": {r["slug"]: r["warnings"] for r in selected + dropped if r["warnings"]},
            "undefined_must_haves": [r["slug"] for r in undefined_musts],
        }, indent=2))
    elif not args.quiet:
        print(f"selected {len(selected)} of {len(rows)} feature(s)  "
              f"[--priority {args.priority}"
              f"{', --include-tbd' if args.include_tbd else ''}]")
        for r in selected:
            print(f"  BUILD    {r['slug']:<24} {r['tier']}")
            for w in r["warnings"]:
                print(f"      warn  {w}")
        for r in dropped:
            print(f"  SKIP     {r['slug']:<24} {r['tier']}")
            for reason in r["reasons"]:
                print(f"      {reason}")
            for w in r["warnings"]:
                print(f"      warn  {w}")

    if undefined_musts:
        print(f"\n{len(undefined_musts)} must-have feature(s) are not defined enough to break "
              f"down: {', '.join(r['slug'] for r in undefined_musts)}", file=sys.stderr)
        print("Report this before anything else. A silently omitted must-have is worse than the "
              "unfiltered behaviour this replaced.", file=sys.stderr)

    if not selected:
        print(f"\nnothing to build: all {len(rows)} feature(s) were skipped", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
