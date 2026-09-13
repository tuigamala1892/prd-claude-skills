#!/usr/bin/env python3
"""The well-defined bar, as far as a script can carry it (item 40, finding P26).

Section 4.2 says what `defined` means in a sentence. Item 40 is that sentence as EIGHT tests
applied one at a time, split by what a script can settle and what needs a reader. This is the
first half. The second half is `agents/prd-criteria-author.md` in `review-definition` mode, and
the split is not a convenience -- a test that needs judgement, run by a script, produces a
confident wrong answer, which is worse than no answer.

AND THE GATE HAS A SECOND HALF, WHICH UNTIL SCHEMA-6 HAD NOWHERE TO LIVE

The bar is *the mechanical tests pass AND a review has been recorded*. For four phases only the
first half existed, so a feature labelled `defined` and one labelled `defined` after somebody read
it were the same file. `<review by= at= sha=>` (core section 3) is the second half, and this script
is its reader:

    reviewed      sha matches the file's content with the <review> element removed
    STALE         sha differs -- reviewed, then edited
    not reviewed  the element is absent

Both failing states are REPORTED, never refused, and only `--strict` turns them into an exit
code. Section 4.2's own principle is that a wrong label signals wrong content, so a gate that
blocks the label invites relabelling rather than fixing -- which is the failure it exists to
prevent, committed deliberately.

`--record-review --by NAME` writes the element. The hash rule lives here, in the reader, so that
producing a record and checking one cannot drift apart -- an agent computing a digest by hand is
the kind of thing that is right four times and wrong on the fifth.

**Recording a review is also the migration's sign-off** (core section 2). Before hashing, it removes
`derived-from` from every criterion that carries a `pattern`. A criterion with no pattern keeps
the attribute, because nobody has classified that sentence yet.

THE EIGHT TESTS, AND WHERE EACH ONE LANDS

  1  scope states what the feature owns AND what it does not          judgement
  2  each distinct failure mode has its own criterion                 HERE, via `pattern`
  3  strike out criteria that exist only to serve another feature     judgement
  4  a data model, including what is deliberately absent              HERE, presence only
  5  external dependencies as providers with roles, not brand names   HERE, presence only
  6  cited decision records are DISCHARGED, not merely cited          split, see below
  7  a relationships list in BOTH directions                          HERE
  8  a <user-story> naming an actor, a capability and a benefit       HERE, shape only

Test 6's citation half already has an owner: `check-references.py` resolves every `ADR-NNN` and
reports a citation of a superseded record. Whether the record's obligations appear as criteria is
judgement, so this script asserts neither and names both -- a rule stated in two programs is a
rule that will be changed in one of them.

TEST 7 IS THE ONE WORTH RUNNING FIRST

Its inbound half is the one that gets skipped and the one that catches contract gaps. The
mechanism is a grep rather than an element: `<depends-on>` records this feature's OUTBOUND edges,
and there is deliberately no `<relationships>` element for the inbound ones, because a second
structured list of the same relationships would be two producers for one idea. So the inbound
edges are found by grepping this feature's slug and display name across the PRD, and every
mention from a file that declares no `<depends-on>` back is reported as an edge to triage.

On the reference corpus that is 93 one-way edges to look at rather than 231 documents to read.
**When it finds a gap, the fix belongs in the OWNING feature** -- weakening the consumer's claim
to match an under-specified owner loses a requirement that had a reason.

TEST 8 HAS ONE CHEAP SCREEN AND NO MORE

A user story degrades into "As a user, I want X, so that I can X", and the tautology is
catchable: the "so that" clause must not merely restate the "I want" clause. That is crude, it
catches only the worst case, and it is worth having because the worst case is the common one.
Everything beyond it -- is this a real benefit, is this the right actor -- is judgement.

THE GATE REPORTS; THE LABEL IS THE AUTHOR'S TO SET

A feature cannot be *labelled* `defined` until the mechanical tests pass and a review has been
recorded. This script is the first half of that sentence and it reports rather than refuses,
because 4.2's own principle is that a wrong status usually signals wrong CONTENT, and a gate that
blocks the label invites relabelling rather than fixing. Never lower a `<definition>` to silence
a line printed here.

WHAT THE BAR DELIBERATELY DOES NOT TOUCH

Priority. Definition completeness and MoSCoW are orthogonal -- a could-have can be fully defined
and a must-have can be a sketch. A feature is never promoted because it is well written, nor
elaborated only as far as its priority seems to justify.

USAGE

    check-definition.py <prd-dir> [--feature SLUG] [--all] [--strict] [--quiet] [--json]
    check-definition.py <prd-dir> --record-review --by NAME [--feature SLUG]

  --feature  check one feature by slug, for the per-feature loop in `/prd`
  --all      apply the bar to every feature, not only the ones declared `defined`. The bar is a
             gate on that label, so by default a `tbd` feature failing it is not a finding
  --strict   exit non-zero on the one-way edges, and on a missing or stale review
  --record-review --by NAME
             record a review on every `defined` feature (or one, with --feature) and exit

EXIT CODES

  0  every feature the bar applies to passes the mechanical tests
  1  at least one does not -- reported by feature and by test
  2  usage error, or the PRD could not be read
"""

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))

# One reader for "what does this feature file declare" -- see check-status.py's note.
_spec = importlib.util.spec_from_file_location(
    "select_features", os.path.join(_HERE, "select-features.py"))
_sel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sel)

# Core 2's six patterns. The failure-path ones are what test 2 counts: a feature whose criteria
# are entirely `event-driven` has said what happens when things go right and nothing else.
PATTERNS = {"ubiquitous", "event-driven", "state-driven", "optional-feature",
            "unwanted-behaviour", "complex"}
FAILURE_PATTERNS = {"unwanted-behaviour"}

CRITERION = re.compile(r"<criterion\b([^>]*)>(.*?)</criterion>", re.S)
ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')
USER_STORY = re.compile(r"<user-story>\s*(.*?)\s*</user-story>", re.S)
DATA_MODEL = re.compile(r"<data-model>\s*(.*?)\s*</data-model>", re.S)
DEPENDS_ON = re.compile(r'<depends-on\b[^>]*\bslug="([^"]*)"[^>]*>')
DEPENDENCY = re.compile(r"<dependency>(.*?)</dependency>", re.S)
PURPOSE = re.compile(r"<purpose>\s*(.*?)\s*</purpose>", re.S)
DEP_NAME = re.compile(r"<name>\s*(.*?)\s*</name>", re.S)

STORY_SHAPE = re.compile(r"\bas\s+(?:a|an|the)?\s*(.+?)[,.]\s*i\s+want\s+(.+?)[,.]\s*so\s+that\s+"
                         r"(.+)$", re.S | re.I)

# Words carried by both halves of every user story ever written. Stripping them is what stops
# the tautology screen firing on "I want a token, so that I can get a token for the session".
STOPWORDS = {"a", "an", "the", "to", "of", "for", "and", "or", "in", "on", "at", "by", "with",
             "that", "this", "it", "its", "is", "be", "can", "i", "my", "we", "our", "so",
             "them", "they", "as", "want", "from", "into", "without", "when", "each", "every"}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS}


def criteria_of(text):
    rows = []
    for attrs, body in CRITERION.findall(text):
        row = dict(ATTR.findall(attrs))
        row["text"] = " ".join(body.split())
        rows.append(row)
    return rows


def test_2(text, crits, fail):
    """Each distinct failure mode has its own criterion. Mechanical via `pattern`."""
    missing = [c.get("id", "?") for c in crits if c.get("pattern") not in PATTERNS]
    if missing:
        fail("2", f"criteria {', '.join(missing)} carry no recognised `pattern`, so nothing can "
                  f"count the shapes this feature covers")
    if not any(c.get("pattern") in FAILURE_PATTERNS for c in crits):
        fail("2", "no criterion has pattern=\"unwanted-behaviour\" -- the feature says what "
                  "happens when things go right and nothing else")


def test_4(text, fail):
    """A data model, including what is deliberately absent. Presence only."""
    m = DATA_MODEL.search(text)
    if not m or not m.group(1).strip():
        fail("4", "<notes><data-model> is absent or empty -- the entities this feature owns are "
                  "wherever the reader guesses they are")


def test_7(slug, name, text, mentions, feature_slugs, fail, edges):
    """Relationships in both directions: declared outbound, grepped inbound."""
    declared_out = set(DEPENDS_ON.findall(text))
    for target in sorted(declared_out):
        if target not in feature_slugs:
            fail("7", f"<depends-on slug=\"{target}\"> names a feature that does not exist")

    for other_slug, rel, line in mentions:
        edges.append(f"{rel}:{line}: {other_slug} names `{slug}` and declares no "
                     f"<depends-on slug=\"{slug}\"> -- read it as a claim on this feature")


def test_8(text, fail):
    """A story naming an actor, a capability and a benefit -- shape, then the tautology screen."""
    m = USER_STORY.search(text)
    if not m or not m.group(1).strip():
        fail("8", "<user-story> is absent")
        return
    story = " ".join(m.group(1).split())
    shape = STORY_SHAPE.match(story)
    if not shape:
        fail("8", f"<user-story> is not in three parts (As a ..., I want ..., so that ...): "
                  f"{story[:70]}")
        return
    want, benefit = words(shape.group(2)), words(shape.group(3))
    if benefit and benefit <= want:
        fail("8", f"the `so that` clause restates the `I want` clause and names no benefit: "
                  f"so that {shape.group(3)[:60]}")


def test_5(prd_dir, fail_prd):
    """External dependencies as providers with ROLES. Presence of the role is the mechanical
    half; whether it is a role rather than a brand name is judgement."""
    index = read(os.path.join(prd_dir, "index.md"))
    for block in DEPENDENCY.findall(index):
        purpose = PURPOSE.search(block)
        if not purpose or not purpose.group(1).strip():
            name = DEP_NAME.search(block)
            fail_prd("5", f"dependency `{(name.group(1) if name else '?').strip()}` names "
                          f"no <purpose> -- a brand name with no role does not say what it gates")


def mentions_of(slug, name, files, owner_rel):
    """Every other feature file that names this feature without declaring an edge to it.

    Three things are deliberately not inbound edges. A mention inside the feature's own file.
    A file that already declares `<depends-on slug=...>` back -- that edge is recorded, which is
    the whole point of the element. And `index.md` / `what-next.md`, which name every feature by
    construction, so treating their mentions as claims would report the entire corpus.
    """
    hits = []
    needles = [n for n in {slug, name} if n]
    declared = re.compile(r'<depends-on\b[^>]*\bslug="%s"' % re.escape(slug))
    for rel, other_slug, text in files:
        if rel == owner_rel or other_slug is None or declared.search(text):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if any(re.search(r"\b" + re.escape(n) + r"\b", line, re.I) for n in needles):
                hits.append((other_slug, rel, i))
                break
    return hits


REVIEW = re.compile(r"[ \t]*<review\b[^>]*/>[ \t]*\n?")


def content_sha(text):
    """The feature's content hash: sha256 over the file WITHOUT its <review> element.

    Excluding the element is what makes the record self-consistent -- hashing the whole file
    would mean writing the review changed the file the review describes, so every review would
    be stale the moment it was recorded.

    No canonicalisation, deliberately. A reflow invalidates a review, because the alternative is
    a canonicaliser deciding which edits are cosmetic, and that decision is the judgement the
    reviewer was there to make. Twelve hex is git's readability trade, not a security one.
    """
    return hashlib.sha256(REVIEW.sub("", text).encode("utf-8")).hexdigest()[:12]


def review_of(text):
    """(state, attrs) where state is `reviewed`, `stale` or `absent`."""
    m = re.search(r"<review\b([^>]*)/>", text)
    if not m:
        return "absent", {}
    attrs = dict(re.findall(r'\b([a-z-]+)="([^"]*)"', m.group(1)))
    return ("reviewed" if attrs.get("sha") == content_sha(text) else "stale"), attrs


CRITERION_TAG = re.compile(r"<criterion\b([^>]*)>")


def sign_off(text):
    """Remove `derived-from` from every criterion that carries a `pattern`; return (text, n).

    Recording a review IS the sign-off (core section 2). A migrated criterion keeps `derived-from`
    after a person assigns its pattern, so the reviewer can still check the sentence against where
    it came from. The review is the moment that check has happened. A criterion with NO pattern
    keeps the attribute: nobody has classified it, so it is still the migration's sentence and
    not yet anyone's.
    """
    count = [0]

    def one(m):
        attrs = m.group(1)
        if not re.search(r'\bpattern="', attrs):
            return m.group(0)
        signed = re.sub(r'\s+derived-from="[^"]*"', "", attrs)
        if signed != attrs:
            count[0] += 1
        return "<criterion%s>" % signed

    return CRITERION_TAG.sub(one, text), count[0]


def record_review(path, by):
    """Sign off, then write or replace a <review> in the feature's <meta>.

    Returns (the line written, criteria signed off), or None when there is no </meta>. The sign-off
    comes BEFORE the hash, because the review describes the file as signed off. The other order
    would leave every freshly recorded review STALE.
    """
    text = read(path)
    stripped, signed = sign_off(REVIEW.sub("", text))
    line = '  <review by="%s" at="%s" sha="%s"/>\n' % (
        by, time.strftime("%Y-%m-%d"), content_sha(stripped))
    m = re.search(r"([ \t]*)</meta>", stripped)
    if not m:
        return None
    out = stripped[:m.start()] + line.replace("  ", m.group(1) + "  ", 1) + stripped[m.start():]
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    return line.strip(), signed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir", metavar="prd-dir")
    ap.add_argument("--feature", default=None, help="check one feature by slug")
    ap.add_argument("--all", action="store_true",
                    help="apply the bar to every feature, not only those declared `defined`")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record-review", action="store_true",
                    help="record a review on the `defined` features and exit")
    ap.add_argument("--by", default=None, help="who reviewed it -- required by --record-review")
    args = ap.parse_args()

    prd_dir = args.prd_dir
    if not os.path.isdir(prd_dir):
        print(f"REFUSED  not a directory: {prd_dir}", file=sys.stderr)
        return 2

    rows, err = _sel.features_of_prd(prd_dir)
    if err:
        print(f"REFUSED  {err}", file=sys.stderr)
        return 2

    if args.record_review:
        if not args.by:
            print("REFUSED  --record-review needs --by NAME. A review is somebody's, and a "
                  "record with no name is the adjective this element replaced", file=sys.stderr)
            return 2
        wrote = 0
        for r in rows:
            if args.feature and r["slug"] != args.feature:
                continue
            if r["definition"] != "defined":
                continue
            path = os.path.join(prd_dir, r["file"].replace("/", os.sep))
            if not os.path.isfile(path):
                continue
            result = record_review(path, args.by)
            if result is None:
                print(f"REFUSED  {r['file']} has no </meta> to record a review in",
                      file=sys.stderr)
                return 2
            line, signed = result
            wrote += 1
            if not args.quiet:
                tail = f"; signed off {signed} migrated criteria" if signed else ""
                print(f"  recorded  {r['file']}: {line}{tail}")
        print(f"recorded {wrote} review(s) as `{args.by}`")
        return 0

    feature_slugs = {r["slug"] for r in rows}
    corpus = []
    for r in rows:
        path = os.path.join(prd_dir, r["file"].replace("/", os.sep))
        corpus.append((r["file"], r["slug"], read(path) if os.path.isfile(path) else ""))
    for extra in ("index.md", "what-next.md"):
        p = os.path.join(prd_dir, extra)
        if os.path.isfile(p):
            corpus.append((extra, None, read(p)))

    findings, edges, reviews = [], [], []
    # Item 34, reported as a distribution rather than as a rule. A corpus where
    # everything is P0 carries no information, and neither does one where nothing
    # is set -- and no threshold between those two is defensible, so this counts
    # and says nothing about what the count should be.
    tally = collections.Counter()

    def fail_prd(test, message):
        findings.append(("index.md", test, message))

    test_5(prd_dir, fail_prd)

    applied = 0
    for r in rows:
        if args.feature and r["slug"] != args.feature:
            continue
        if r["missing"]:
            findings.append((r["file"], "-", "the index names this file and it does not exist"))
            continue
        if not args.all and r["definition"] != "defined":
            continue
        applied += 1
        text = read(os.path.join(prd_dir, r["file"].replace("/", os.sep)))
        crits = criteria_of(text)

        def fail(test, message, rel=r["file"]):
            findings.append((rel, test, message))

        seen = {}
        for c in crits:
            cid = c.get("id")
            if cid is None:
                fail("-", "a <criterion> carries no id, so nothing downstream can name it")
            elif cid in seen:
                fail("-", f"criterion id {cid} is used twice -- an id must resolve to one "
                          f"criterion for a task to satisfy it")
            else:
                seen[cid] = True

        state, attrs = review_of(text)
        if state == "absent":
            reviews.append((r["file"], "no review recorded -- the bar is `the mechanical tests "
                                       "pass AND a review has been recorded`, and this is the "
                                       "second half"))
        elif state == "stale":
            reviews.append((r["file"], f"the review by {attrs.get('by') or '?'} on "
                                       f"{attrs.get('at') or '?'} is STALE: the file has changed "
                                       f"since it was recorded"))

        test_2(text, crits, fail)
        test_4(text, fail)
        test_7(r["slug"], r["name"], text,
               mentions_of(r["slug"], r["name"], corpus, r["file"]), feature_slugs, fail, edges)
        test_8(text, fail)

        unset = [c.get("id", "?") for c in crits if not c.get("priority")]
        if unset and len(unset) == len(crits):
            fail("-", f"no criterion carries a `priority` -- a feature where nothing is "
                      f"prioritised carries no more information than one where everything is P0")
        for c in crits:
            tally[c.get("priority") or "unset"] += 1

    if args.feature and applied == 0 and not any(f[0].endswith(f"{args.feature}.md")
                                                 for f in findings):
        print(f"REFUSED  no feature `{args.feature}` in {prd_dir}, or it is not `defined` "
              f"(--all applies the bar anyway)", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"applied_to": applied,
                          "findings": [{"file": f, "test": t, "message": m}
                                       for f, t, m in findings],
                          "reviews": [{"file": f, "message": m} for f, m in reviews],
                          "edges": edges}, indent=2))
    elif not args.quiet:
        for rel, test, message in findings:
            print(f"  BAR t{test}  {rel}: {message}")
        for rel, message in reviews:
            print(f"  REVIEW    {rel}: {message}")
        for line in edges:
            print(f"  EDGE      {line}")

    spread = ", ".join(f"{k} {v}" for k, v in sorted(tally.items())) or "no criteria"
    print(f"the bar applied to {applied} features: {len(findings)} mechanical failures, "
          f"{applied - len(reviews)} of {applied} reviewed, {len(edges)} one-way edges to "
          f"triage; criterion priority: {spread}")

    if findings:
        return 1
    return 1 if (args.strict and (edges or reviews)) else 0


if __name__ == "__main__":
    sys.exit(main())
