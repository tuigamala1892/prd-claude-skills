#!/usr/bin/env python3
"""Does this artefact match the schema it claims to be in? (plan item 22, finding P10)

P10 is a general failure with a specific symptom: **the spec said XML, the run produced markdown,
and nothing noticed for weeks.** A producer/consumer mismatch should fail at the boundary, not
degrade silently three skills later. This is that boundary check, and it runs in three places --
at the end of `/prd`, at the *start* of `/breakdown`, and over every fixture in the suite.

WHAT IT OWNS, AND THE LINE IS DRAWN NARROWLY ON PURPOSE

**Shape.** Is this a well-formed artefact of its kind: the right root element, the elements its
kind requires, and values from the enums the schema declares. Nothing else.

Everything about *relationships between documents* -- a slug that resolves, an index that
reconciles, a feature that has a task -- belongs to the scripts that already own those questions,
and everything editorial -- is this well defined, is the label honest -- belongs to
`check-definition.py` and `check-status.py`. `checks.md` is the table; consult it before adding a
rule here, because the reason this script exists at all is that item 6 had eleven assertions and
four other items claimed the same ground.

Named explicitly, because a validator that quietly passes over a class of input is worse than one
that says what it passes over. **NOT checked here:**

  criterion id uniqueness           `check-definition.py`
  `<gap>` id / kind / raised        `check-status.py`
  `<priority>` residue in <meta>    `check-rename.py`
  a slug that resolves to nothing   `check-rename.py`
  ADR / OQ citations                `check-references.py`
  PROJECT.md's block parses         `check-project-md.py`

WELL-FORMEDNESS COMES FIRST

A feature, CRD, index or what-next file is one XML document, and every other rule here reads it
with a regex. A regex does not notice that the document does not parse: an element name written
in prose -- `split <data-model> from <offers>` -- left a feature unparseable, and this script
passed it, because each pattern still found what it looked for. Whether a reader downstream
fails loudly or reads half the file depends on the reader.

So an artefact is parsed before anything else is asked of it, and one that does not parse gets
that as its only problem. The shape rules are not run on it: the one that did fire in that case
reported `<notes> holds ['offers']`, which names a symptom and sends the author to the wrong
edit. A `PROJECT.md` is prose around one `<project-context>` block, and that block's parse is
`check-project-md.py`'s -- two owners for one assertion is what `checks.md` prevents.

THE VERSION IS DETECTED, NEVER DECLARED

An artefact carries no `schema_version`, deliberately: **the marker is the shape** (item 41). A
stamp can drift from a hand-edited file and a shape cannot, and a 2.0.1 toolchain writes schema-4
and schema-5 artefacts alike -- so `migrate.py --detect` is the one owner of *what shape is this*,
and this script imports it rather than deriving a second answer.

That is a departure from item 22 as written, which asked for artefacts to *declare* a version. It
was written before item 41 settled the question in the other direction, and two answers to *"which
schema is this file in"* is exactly the defect this file exists to catch.

**Each artefact is judged against its OWN version, never the current one.** A schema-1 fixture is
not broken for lacking `<user-story>`; it is a schema-1 fixture. Item 23 asks for exactly this,
and it is what makes the frozen fixtures testable rather than merely stored.

USAGE

    check-artefacts.py <path> [--schema VERSION] [--strict] [--quiet] [--json]

  <path>      a file, or a directory walked for .md artefacts
  --schema    judge everything against this version instead of the detected one
  --strict    exit non-zero on warnings too

EXIT CODES

  0  every artefact matches its schema (warnings may have been reported)
  1  at least one does not
  2  usage error, or nothing that looks like an artefact was found
"""

import argparse
import importlib.util
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.parsers.expat import ErrorString

_HERE = os.path.dirname(os.path.abspath(__file__))

# One owner for "what kind of artefact is this, and what shape is it in".
_spec = importlib.util.spec_from_file_location("migrate", os.path.join(_HERE, "migrate.py"))
_mig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mig)

VERSIONS = _mig.VERSIONS


def at_least(version, floor):
    return VERSIONS.index(version) >= VERSIONS.index(floor)


# --------------------------------------------------------------------- the enums
#
# Every value set the schema declares, in one place. A value not in its set is the failure P10
# is the general form of: a producer writing something a consumer will read as absent.

DEFINITION = {"tbd", "in-progress", "defined", "excluded", "superseded"}
DOC_STATUS = {"in-progress", "complete"}
WORKFLOW = {"draft", "ready", "in-progress", "complete", "abandoned"}
PATTERN = {"ubiquitous", "event-driven", "state-driven", "optional-feature",
           "unwanted-behaviour", "complex"}
CRIT_PRIORITY = {"P0", "P1", "P2"}
MOSCOW = {"must-have", "should-have", "could-have", "wont-have"}
DEPENDS_KIND = {"data", "runtime", "reference"}
SIGNIFICANCE = {"quality-attribute", "risk", "first-of-a-kind", "cross-cutting",
                "external-dependency", "constraint"}
STEP_KIND = {"spike", "infrastructure", "data-model", "ux", "breakdown", "decision"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CRD_TYPE = {"feature-add", "feature-modify", "feature-remove", "refactor"}
PROJECT_TYPE = {"greenfield", "brownfield"}

META = re.compile(r"<meta>(.*?)</meta>", re.S)
ATTRS = re.compile(r'(\w[\w-]*)="([^"]*)"')


def el(text, tag):
    m = re.search(r"<%s>\s*(.*?)\s*</%s>" % (tag, tag), text, re.S)
    return m.group(1) if m else None


def tags(text, tag):
    """Every occurrence of `<tag ...>` as an attribute dict."""
    return [dict(ATTRS.findall(a)) for a in re.findall(r"<%s\b([^>]*)>" % tag, text)]


def enum(problems, where, value, allowed, label):
    if value is None:
        return
    if value not in allowed:
        problems.append(f"{where}: {label} is {value!r}, not one of "
                        f"{'|'.join(sorted(allowed))}")


# ------------------------------------------------------------------- per kind

def check_feature(text, version, problems, warnings):
    meta = META.search(text)
    if not meta:
        problems.append("no <meta> block")
        return
    inner = meta.group(1)

    for tag in ("name", "slug"):
        if not (el(inner, tag) or "").strip():
            problems.append(f"<meta> has no <{tag}>")
    slug = (el(inner, "slug") or "").strip()
    if slug and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        problems.append(f"<slug>{slug}</slug> is not a slug -- lowercase, digits and hyphens")

    # Item 45 renamed <status> to <definition>. Accepted on READ for a full release and never
    # written, which is core 3's policy for all three renames -- so an old spelling is a warning
    # with a migration to point at, not a refusal that strands a document in flight.
    definition = el(inner, "definition")
    if definition is None:
        legacy = el(inner, "status")
        if legacy is None:
            problems.append("<meta> declares neither <definition> nor the pre-item-45 <status>")
        else:
            # Gated on what THIS TOOLCHAIN writes, not on the artefact's own version. Gating it
            # on the artefact was unreachable code: `<status>` is the shape schema-2's rename
            # keys on, so a file spelling it that way always detects as schema-1 and the
            # `at_least(version, "schema-2")` branch could never run. The mutation round found
            # it by making the branch a refusal and watching nothing change.
            if at_least(current_schema(), "schema-2"):
                warnings.append(f"<meta> still spells it <status>{legacy}</status>; "
                                f"<definition> is the name since item 45. Accepted on read")
            definition = legacy
    enum(problems, "<meta>", (definition or "").strip() or None, DEFINITION, "<definition>")

    if not (el(text, "description") or "").strip():
        problems.append("no <description>")

    for i, c in enumerate(tags(text, "criterion"), start=1):
        where = f"<criterion> {i}" + (f" (id {c['id']})" if "id" in c else "")
        if "id" not in c:
            problems.append(f"{where} has no id, so nothing downstream can name it")
        if at_least(version, "schema-3"):
            if "pattern" not in c:
                problems.append(f"{where} declares no pattern -- assigned by a person, and a "
                                f"migration is forbidden to guess it")
            enum(problems, where, c.get("pattern"), PATTERN, "pattern")
            enum(problems, where, c.get("priority"), CRIT_PRIORITY, "priority")

    for d in tags(text, "depends-on"):
        if "slug" not in d:
            problems.append("<depends-on> names no slug")
        if "kind" not in d:
            problems.append(f"<depends-on slug=\"{d.get('slug', '?')}\"> declares no kind -- "
                            f"without it a dependency is indistinguishable from a `see also`")
        enum(problems, f"<depends-on slug=\"{d.get('slug', '?')}\">", d.get("kind"),
             DEPENDS_KIND, "kind")

    for s in tags(text, "architecturally-significant"):
        enum(problems, "<architecturally-significant>", s.get("because"), SIGNIFICANCE, "because")

    if at_least(version, "schema-4"):
        notes = re.search(r"<notes>(.*?)</notes>", text, re.S)
        if notes:
            children = set(re.findall(r"<([a-z-]+)>", notes.group(1)))
            unknown = children - {"data-model", "considerations"}
            if unknown:
                problems.append(f"<notes> holds {sorted(unknown)}; item 2 split it into exactly "
                                f"<data-model> (read) and <considerations> (unread by design)")

    if re.search(r"<phases>", text):
        problems.append("<phases> was retired at item 5. Phasing is priority plus gaps, and a "
                        "third axis forces an author to demote something important to say it "
                        "is stuck")


def check_prd(text, version, problems, warnings):
    meta = META.search(text)
    if not meta:
        problems.append("no <meta> block")
        return
    inner = meta.group(1)
    for tag in ("name", "slug"):
        if not (el(inner, tag) or "").strip():
            problems.append(f"<meta> has no <{tag}>")

    # Core 3's FIRST row, and the one tag the rename left alone. It has a shipped reader --
    # `list-prds.py` decides what `--resume` can see from it -- so a value outside the enum is a
    # PRD that cannot be found rather than a cosmetic slip.
    status = (el(inner, "status") or "").strip() or None
    if status is None:
        problems.append("<meta> has no <status>, so `/prd --resume` cannot see this PRD and a "
                        "new PRD on this slug would replace it without warning")
    enum(problems, "index.md <meta>", status, DOC_STATUS, "<status>")

    # `<updated>` has a producer -- touch-artefact.py, run when an index entry changes -- and a
    # reader in list-prds.py, which takes the later of this and what-next.md's date. `<created>`
    # deliberately has neither and is declared in readers.md: a birth date cannot go stale.
    updated = (el(inner, "updated") or "").strip() or None
    if updated is None:
        problems.append("<meta> has no <updated>; `list-prds.py` reports when a PRD was last "
                        "worked on and falls back to mtime, which does not survive a clone. "
                        "Run touch-artefact.py to write it")
    elif not ISO_DATE.match(updated):
        problems.append(f"<updated> is {updated!r}, not YYYY-MM-DD. A date nothing can parse is "
                        f"read as no date at all")

    enum(problems, "<tech-stack>", (el(text, "type") or "").strip() or None,
         PROJECT_TYPE, "<type>")

    entries = tags(text, "feature")
    if not entries:
        problems.append("<features> names no feature")
    for e in entries:
        if "file" not in e:
            problems.append(f"a <feature> entry has no file= attribute")
        enum(problems, f"<feature file=\"{e.get('file', '?')}\">", e.get("priority"),
             MOSCOW, "priority")


def check_what_next(text, version, problems, warnings):
    meta = META.search(text)
    if not meta:
        if at_least(version, "schema-4"):
            problems.append("no <meta> block -- item 12 gave this file a parseable skeleton")
        return
    inner = meta.group(1)
    status = (el(inner, "status") or "").strip() or None
    if status is None:
        problems.append("<meta> has no <status>; `list-prds.py` reads both files and reports "
                        "DISAGREE, and it cannot report on a file that declares nothing")
    enum(problems, "what-next.md <meta>", status, DOC_STATUS, "<status>")

    # <last-updated> has a producer -- build-what-next.py writes it whenever it rewrites the
    # file -- so a file that carries no date, or one that is not a date, is a file something
    # wrote by hand and got wrong. Checked here rather than in the builder because the builder
    # FIXES it: a producer that also reports on its own output is a check nobody can fail.
    updated = (el(inner, "last-updated") or "").strip() or None
    if updated is None:
        if at_least(version, "schema-4"):
            problems.append("<meta> has no <last-updated>; `list-prds.py` reports when a PRD "
                            "was last written and falls back to mtime, which does not survive a "
                            "clone. Run build-what-next.py to write it")
    elif not ISO_DATE.match(updated):
        problems.append(f"<last-updated> is {updated!r}, not YYYY-MM-DD. A date nothing can "
                        f"parse is read as no date at all")

    for i, s in enumerate(tags(text, "step"), start=1):
        enum(problems, f"<step> {i}", s.get("kind"), STEP_KIND, "kind")
        if s.get("status") not in (None, "done"):
            problems.append(f"<step> {i}: status is {s['status']!r}; the only value is `done`")


def check_crd(text, version, problems, warnings):
    meta = META.search(text)
    if not meta:
        problems.append("no <meta> block")
        return
    inner = meta.group(1)
    for tag in ("name", "slug"):
        if not (el(inner, tag) or "").strip():
            problems.append(f"<meta> has no <{tag}>")
    enum(problems, "<meta>", (el(inner, "type") or "").strip() or None, CRD_TYPE, "<type>")

    workflow = el(inner, "workflow")
    if workflow is None:
        legacy = el(inner, "status")
        if legacy is None:
            problems.append("<meta> declares neither <workflow> nor the pre-item-45 <status>")
        else:
            warnings.append(f"<meta> still spells it <status>{legacy}</status>; <workflow> is "
                            f"the name since item 45. Accepted on read")
            workflow = legacy
    enum(problems, "<meta>", (workflow or "").strip() or None, WORKFLOW, "<workflow>")

    if at_least(version, "schema-5"):
        # A record of the past is never asked for its tier (migration.md), so its absence is the
        # true state rather than a malformed one. One definition of `past`, migrate.py's: a second
        # would let the validator and --check disagree about the same file.
        if not (el(inner, "priority") or "").strip() and not _mig._is_past(text):
            problems.append("<meta> has no <priority> -- item 47 gave the document a MoSCoW tier, "
                            "and `--priority` has nothing to threshold against without it")
        enum(problems, "<meta>", (el(inner, "priority") or "").strip() or None,
             MOSCOW, "<priority>")
        if re.search(r"<requirements>", text):
            problems.append("<requirements> was retired at item 46. Its entries are criteria, in "
                            "one list with one id space")

    for i, c in enumerate(tags(text, "criterion"), start=1):
        where = f"<criterion> {i}" + (f" (id {c['id']})" if "id" in c else "")
        if "id" not in c:
            problems.append(f"{where} has no id")
        if at_least(version, "schema-3"):
            enum(problems, where, c.get("pattern"), PATTERN, "pattern")
            enum(problems, where, c.get("priority"), CRIT_PRIORITY, "priority")

    if re.search(r"<affected-apis>", text):
        warnings.append("<affected-apis> is item 57's old spelling of "
                        "<affected-contracts kind=\"api\">. Accepted on read for one release")


def check_project_context(text, version, problems, warnings):
    if not re.search(r"<[a-z-]+-registry\b", text):
        problems.append("no <*-registry> element -- a PROJECT.md with no registry describes "
                        "nothing a consumer can look anything up in")
    # The attribute dicts do not carry children, so the blocks are matched separately and zipped
    # by position. A `<feature>` that is self-closing or empty still yields a block, so the two
    # lists stay in step.
    blocks = re.findall(r"<feature\b[^>]*(?:/>|>(.*?)</feature>)", text, re.S)

    for i, f in enumerate(tags(text, "feature")):
        # `id` first, because every message below names the feature with it. The old message
        # reached for `f.get('name')` -- an ATTRIBUTE that project-format.md does not define;
        # `name` is a child element there. A validator modelling the wrong shape in its own
        # error text is how the wrong shape looks reasonable to the next producer (P63).
        where = f"<feature id=\"{f.get('id', '?')}\">"
        if "id" not in f:
            problems.append("a <feature> has no `id`, so nothing can refer to it")
        if "built" in f:
            enum(problems, where, f.get("built"), {"complete", "partial", "planned"}, "built")
        elif "status" in f:
            warnings.append(f"{where} still spells it `status={f['status']}`; `built=` is the "
                            f"name since item 45. Accepted on read")
        else:
            # The branch that was missing. Two spellings were handled and `neither` was not,
            # so a feature with no build state at all passed every reader: `check-project-md.py`
            # calls the file valid, and only version detection objects -- with a message about
            # schemas rather than about this.
            # One line per feature, and the rationale is NOT repeated: a PROJECT.md describing
            # forty features would otherwise print forty copies of the same paragraph, which is
            # the other way to make a finding unreadable.
            problems.append(f"{where} declares neither `built=` nor the pre-item-45 `status=` "
                            f"-- required by project-format.md, values in core section 3")

        # P67, item 81's residue. `name` and `files` are Required and are ELEMENTS -- identity
        # and state are attributes, content is a child. The crossing wrote `name` as an
        # attribute on 7 features out of 7, and nothing noticed because nothing parses either
        # form mechanically: `<files>` is read by an instruction, and a model reading the XML
        # finds a name written either way.
        inner = blocks[i] if i < len(blocks) else ""
        for tag in ("name", "files"):
            if el(inner or "", tag) is not None:
                continue
            if tag in f:
                # Naming the mistake rather than the absence. `<name> is missing` sends an
                # author to add one beside the attribute they already wrote; this is one edit.
                problems.append(f"{where} writes `{tag}` as an ATTRIBUTE. project-format.md "
                                f"marks it required and written as an ELEMENT -- identity and "
                                f"state are attributes, content is a child")
            else:
                problems.append(f"{where} has no <{tag}> -- required by project-format.md")


CHECKERS = {
    "feature": check_feature,
    "prd": check_prd,
    "what-next": check_what_next,
    "crd": check_crd,
    "project-context": check_project_context,
}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def not_well_formed(text, kind):
    """The parse error for an artefact that is not one XML document, or None when it is."""
    if kind == "project-context":
        return None
    try:
        ET.fromstring(text)
        return None
    except ET.ParseError as e:
        line, col = e.position
        lines = text.splitlines()
        at = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        # ElementTree reports where it NOTICED, which for a stray tag in prose is the closing
        # tag that no longer matches -- usually some lines below the text to fix.
        return (f"is not well-formed XML ({ErrorString(e.code)}, noticed at line {line}, column {col + 1}: "
                f"{at[:60]!r}). No other rule was checked. An element name written in prose "
                f"must be escaped as `&lt;name&gt;`, and a bare `&` as `&amp;`; a stray tag "
                f"sits on that line or above it")


def current_schema():
    """The version the toolchain writes, declared by the core rather than by a fixture.

    `core.md` carries `<schema-core version=...>` and the suite asserts it equals SCHEMAS.json's
    `current`. A shipped script reading a test fixture to find out what it writes would be the
    wrong direction entirely.
    """
    m = re.search(r'<schema-core\s+version="([^"]+)"', read(os.path.join(_HERE, os.pardir,
                                                                       "core.md")))
    return m.group(1) if m and m.group(1) in VERSIONS else VERSIONS[-1]


def artefact_files(path):
    if os.path.isfile(path):
        return [path]
    out = []
    for dirpath, dirnames, names in os.walk(path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for n in sorted(names):
            if n.lower().endswith(".md"):
                out.append(os.path.join(dirpath, n))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("--schema", default=None, choices=VERSIONS)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"REFUSED  no such path: {args.path}", file=sys.stderr)
        return 2

    current = current_schema()
    rows, checked = [], 0
    for path in artefact_files(args.path):
        text = read(path)
        kind = _mig.kind_of(text)
        if kind is None:
            continue
        checked += 1
        version = args.schema or _mig.detect(text, kind)
        problems, warnings = [], []
        malformed = not_well_formed(text, kind)
        if malformed:
            rows.append({"path": path, "kind": kind, "version": version or "no version",
                         "problems": [malformed], "warnings": []})
            continue
        if version is None:
            # migrate.py's own escalation, and it is not this script's to route around: a file
            # matching no known shape is a file whose meaning would be guessed at.
            problems.append("matches no known schema version. `migrate.py --detect` escalates "
                            "rather than guessing, and so does this")
            version = VERSIONS[-1]
            # BUT the escalation is not the whole answer, and on its own it is a wrong one.
            # `Unplaceable` and `missing a required field` are frequently the same file: a
            # version is detected from shape, so an artefact that has lost a required element
            # loses its version with it. The operator then reads *no known schema version*, runs
            # `/migrate`, and is correctly told no migration can be selected -- a remedy named
            # by the only message they got, which cannot apply (P63).
            #
            # So: escalate AND diagnose. Judged against the current schema, said out loud,
            # because judging it against a version nobody could determine is the guess this
            # script refuses to make.
            before = len(problems)
            CHECKERS[kind](text, current, problems, warnings)
            if len(problems) > before:
                problems.insert(before, f"judged against {current} to say why, since no version "
                                        f"could be determined:")
        else:
            CHECKERS[kind](text, version, problems, warnings)
            # An artefact BELOW the current schema is not invalid -- it is old, and it is judged
            # by its own rules above. Saying so is the point: shape detection means a file that
            # loses an element quietly detects as an earlier version and is then held to laxer
            # rules, and the only way that reads as a defect is if somebody says which version
            # it landed on.
            if not args.schema and at_least(current, version) and version != current:
                warnings.append(f"is at {version}; this toolchain writes {current}. "
                                f"Run `/migrate` -- it is judged by {version}'s rules here")
        rows.append({"path": path, "kind": kind, "version": version,
                     "problems": problems, "warnings": warnings})

    if not checked:
        print(f"REFUSED  nothing under {args.path} has an artefact root element "
              f"({', '.join(k for k, _ in _mig.ROOTS)})", file=sys.stderr)
        return 2

    bad = sum(len(r["problems"]) for r in rows)
    warn = sum(len(r["warnings"]) for r in rows)

    if args.json:
        print(json.dumps({"checked": checked, "problems": bad, "warnings": warn,
                          "artefacts": rows}, indent=2))
    elif not args.quiet:
        for r in rows:
            rel = os.path.relpath(r["path"], args.path if os.path.isdir(args.path) else ".")
            for p in r["problems"]:
                print(f"  INVALID  {rel} [{r['kind']}, {r['version']}]: {p}")
            for w in r["warnings"]:
                print(f"  OLD      {rel} [{r['kind']}, {r['version']}]: {w}")

    versions = sorted({r["version"] for r in rows})
    print(f"{checked} artefact(s) checked against {', '.join(versions)}: "
          f"{bad} invalid, {warn} written in an older spelling")

    if bad:
        return 1
    return 1 if (args.strict and warn) else 0


if __name__ == "__main__":
    sys.exit(main())
