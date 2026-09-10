#!/usr/bin/env python3
"""Migrate PRD, CRD and PROJECT.md artefacts between schema versions (plan item 41).

The rules this executes are specified in ../migration.md, which is the authority. This file is
its consumer, not a second statement of it: every rule below cites the identifier the guide
gives it, and a rule that exists here and not there is a bug in this file.

WHAT MAKES THIS SAFE TO RE-ENTER

The marker of "already migrated" is the SHAPE, never a stamp. A feature file carrying
<definition> is past schema-1; a criterion carrying `priority` is past schema-2 -- `priority` and
not `pattern`, because R10 creates criteria that are REQUIRED to lack a pattern, so only the
attribute the transform makes total still means what it used to. So re-running is safe by
construction, a partly migrated tree is safe to re-enter, and there is no side-car that can
disagree with the content. The cost is a constraint the guide states: a transformation whose
completion is not visible in the shape has to be made total until it is -- which is why criterion
`priority` is WRITTEN IN as P1 rather than left to a documented default.

THE THIRD STATE

Some steps are part mechanical and part judgement. schema-2 -> schema-3 is: the attributes are
mechanical, and rewriting a Given/When/Then into an EARS sentence and assigning its `pattern` are
not. A file that has had the mechanical half applied and not the judgements is PARTIAL -- and it
is detectable, because `priority` is present and `pattern` is not. `--check` refuses a PARTIAL
tree, which is what stops "the script ran" being mistaken for "the migration finished".

WHAT IT REFUSES TO DO

A file matching no precondition is REPORTED, never transformed. That is the whole escalation
path, and it is why exit 2 exists separately from exit 1: nothing was written for those files,
so the tree is exactly as it was found. A file that is not valid UTF-8 takes the same path, for
the same reason one step earlier -- bytes this script cannot decode are a meaning it would be
guessing at, and decoding them with a replacement character loses the original irrecoverably in
a run that would otherwise exit 0.

USAGE

    migrate.py <path> --to schema-3 [--dry-run] [--quiet]
    migrate.py <path> --to schema-3 --check      # assert postconditions, write nothing
    migrate.py <path> --detect                   # report each file's schema, write nothing

EXIT CODES

  0  every file reached the target schema and every postcondition holds
  1  a postcondition failed, or --check found a file short of the target. Nothing partly
     written survives: a file whose postconditions failed is left exactly as it was
  2  escalation -- one or more files matched no precondition, or could not be decoded as
     UTF-8. Nothing written for those, and each is named
  3  usage error
"""

import argparse
import os
import re
import sys

VERSIONS = ["schema-1", "schema-2", "schema-3", "schema-4", "schema-5", "schema-6"]

# ---------------------------------------------------------------- artefact kinds

# Which artefact a file is, decided by ROOT ELEMENT rather than by filename. R1 must not touch
# index.md or what-next.md -- their <status> is the document-level tag, which was never renamed
# and whose reader is what makes `/prd --resume` work. Deciding by filename would have been one
# convention away from breaking it.
ROOTS = (
    ("feature", re.compile(r"<\s*feature\s*>")),
    ("crd", re.compile(r"<\s*crd\s*>")),
    ("prd", re.compile(r"<\s*prd\s*>")),
    ("what-next", re.compile(r"<\s*what-next\s*>")),
    ("project-context", re.compile(r"<\s*project-context\b")),
)

META = re.compile(r"<meta>(.*?)</meta>", re.S)
FEATURE_ENTRY = re.compile(r"<feature\s+id=\"[^\"]+\"[^>]*>")
REQUIREMENTS = re.compile(r"( *)<requirements>(.*?)</requirements>\n?", re.S)
REQUIREMENT = re.compile(r"<requirement\b([^>]*)>(.*?)</requirement>", re.S)
CRITERIA_BLOCK = re.compile(r"( *)<acceptance-criteria>(.*?)( *)</acceptance-criteria>", re.S)

# Item 47. One to one, and the fourth MoSCoW value is deliberately absent: P0|P1|P2 has no "not
# building this" level, because that judgement belongs to the whole item -- which on this path is
# the document, in <meta><priority>. A `wont-have` requirement therefore has no honest target and
# is an escalation rather than a mapping. See migration.md.
MOSCOW_TO_P = {"must-have": "P0", "should-have": "P1", "could-have": "P2"}

CRITERION = re.compile(r"<criterion\b([^>]*)>", re.S)


def kind_of(text):
    for name, pat in ROOTS:
        if pat.search(text):
            return name
    return None


# Names the toolchain itself writes. Consulted for ONE question, and only after kind_of() has
# already come back None: is an absent root element expected here, or is it the whole problem?
OWNED_NAMES = {"index.md", "what-next.md", "project.md"}
OWNED_DIRS = {"features"}


def toolchain_owns(path):
    """True when this repository's own commands are what create a file at this path.

    THIS IS NOT `deciding by filename`, and the distinction is worth stating because the rule it
    sounds like is one ROOTS is careful about. That rule is about which artefact a file IS, and
    it stands untouched: R1 must not reach index.md because of its ROOT ELEMENT, never its name,
    or `/prd --resume` breaks. Nothing here selects a rule, a kind or a schema version. The name
    is asked a different question, and asked only when the root element is already known absent:
    whether that absence is ordinary.

    The two failure modes are not symmetric, and that sets the default. A file wrongly called
    the toolchain's is one escalation line an operator reads and dismisses. A file wrongly called
    prose is a PRD migrated to the current schema around a what-next.md still holding a markdown
    heading, with nothing that ever says so -- which is how this was found, on a corpus rather
    than in this suite.
    """
    name = os.path.basename(path).lower()
    parent = os.path.basename(os.path.dirname(os.path.abspath(path))).lower()
    return name in OWNED_NAMES or parent in OWNED_DIRS


def read(path):
    """Returns (text normalised to \\n, the line ending the file actually used).

    STRICT decoding, and the UnicodeDecodeError is meant to reach the caller. Reading with
    `errors="replace"` and writing the result back is not a read: every byte the decoder cannot
    place becomes U+FFFD, permanently, in a run that exits 0. A corpus authored in a Windows
    editor and saved as cp1252 is the ordinary case rather than the exotic one, and a file this
    script cannot decode is a file whose meaning it would be guessing at -- which is the
    escalation path's definition, so it takes the escalation path.

    The line ending comes back with the text because none of these rules is ABOUT line endings.
    A file that arrived CRLF has to leave CRLF: rewriting every line turns each per-file diff
    into a whole-file diff, which fails no postcondition and destroys the one mechanism the guide
    names for catching silent semantic loss. The rename invariants cannot see it either -- values
    and tag counts both survive a line-ending flip intact.

    A file mixing both endings takes the one it uses more often. It is the only answer that is
    not a guess, and a file already inconsistent with itself has no convention to preserve.
    """
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    crlf = text.count("\r\n")
    return text.replace("\r\n", "\n"), ("\r\n" if crlf > text.count("\n") - crlf else "\n")


def write(path, text, newline="\n"):
    with open(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)


# ------------------------------------------------------------------ transforms

def _meta_swap(text, old, new):
    """Rename <old> to <new>, inside <meta> only, preserving content byte for byte."""
    m = META.search(text)
    if not m:
        return text
    inner = re.sub(r"<%s>(.*?)</%s>" % (old, old), r"<%s>\1</%s>" % (new, new),
                   m.group(1), flags=re.S)
    return text[:m.start(1)] + inner + text[m.end(1):]


def _meta_has(text, tag):
    m = META.search(text)
    return bool(m and re.search(r"<%s>" % tag, m.group(1)))


def _entries_with(text, attr):
    return [e for e in FEATURE_ENTRY.findall(text) if re.search(r"\b%s=" % attr, e)]


def _criteria_attrs(text):
    return [dict(re.findall(r'([\w-]+)="([^"]*)"', a)) for a in CRITERION.findall(text)]


def _criteria_lacking(text, attr):
    return [a for a in _criteria_attrs(text) if attr not in a]


DATA_MODEL_HEADING = re.compile(r"^\s*\*\*Data model\*\*\s*:?\s*$", re.M | re.I)


def _meta_drop(text, tag):
    """Remove <tag>...</tag> from <meta>, and the newline it sat on."""
    m = META.search(text)
    if not m:
        return text
    inner = re.sub(r"\n[ \t]*<%s>.*?</%s>" % (tag, tag), "", m.group(1), flags=re.S)
    return text[:m.start(1)] + inner + text[m.end(1):]


def _split_notes(text):
    """<notes> prose becomes <data-model> plus <considerations>, keyed on a bold heading.

    The catch-all is what makes this safe: everything not under a `**Data model**` heading goes
    to <considerations> VERBATIM. A three-way split needing judgement per file was on this
    plan's critical path until §4.3 removed it; this is the two-way one that replaced it, and
    the reason it can be mechanical at all is that one side never has to be understood.
    """
    m = re.search(r"( *)<notes>(.*?)</notes>", text, re.S)
    if not m or "<considerations>" in m.group(2):
        return text
    base, body = m.group(1), m.group(2).strip("\n")
    lines = body.splitlines()
    hit = next((i for i, ln in enumerate(lines) if DATA_MODEL_HEADING.match(ln)), None)

    def block(tag, rows):
        # Blank rows at either end are an artefact of where the heading fell, not content.
        # Keeping them would make the output depend on the source's blank lines rather than
        # on its prose, and a golden comparison would then be asserting whitespace.
        while rows and not rows[0].strip():
            rows = rows[1:]
        while rows and not rows[-1].strip():
            rows = rows[:-1]
        inner = "\n".join(rows)
        return f"{base}  <{tag}>\n{inner}\n{base}  </{tag}>"

    parts = []
    if hit is None:
        parts.append(block("considerations", lines))
    else:
        end = next((j for j in range(hit + 1, len(lines))
                    if re.match(r"^\s*\*\*[^*]+\*\*\s*:?\s*$", lines[j])), len(lines))
        parts.append(block("data-model", lines[hit + 1:end]))
        rest = lines[:hit] + lines[end:]
        if any(ln.strip() for ln in rest):
            parts.append(block("considerations", rest))
    return (text[:m.start()] + f"{base}<notes>\n" + "\n".join(parts) + f"\n{base}</notes>"
            + text[m.end():])


def _wrap_what_next_meta(text):
    """R9 (items 11, 12): lift <status> and <last-updated> into a <meta> block.

    Only what is DERIVABLE FROM THE FILE. <prd-slug>, <next-command> and <toolchain-version>
    are not in it -- the first is the directory's, the second is a choice, the third is item
    24's stamp -- so the step is PARTIAL until a person or `schema-migrator` supplies them.

    <status> stays the first <status> in the file, inside <meta> or not. That is not an accident
    of `list-prds.py`'s regex; it is the reason the element is placed where a naive reader finds
    it, and it is what keeps F3's dual check working across a partly migrated tree (item 12).
    """
    if re.search(r"<meta>.*?<status>", text, re.S):
        return text
    m = re.search(r"( *)<status>.*?</status>(\s*\n *<last-updated>.*?</last-updated>)?", text,
                  re.S)
    if not m:
        return text
    base = m.group(1)
    inner = "\n".join(f"{base}  {ln.strip()}" for ln in m.group(0).strip().splitlines()
                       if ln.strip())
    return text[:m.start()] + f"{base}<meta>\n{inner}\n{base}</meta>" + text[m.end():]


def _requirements_to_criteria(text):
    """R10 (items 46, 47): every <requirement> becomes a <criterion>, and the list is removed.

    The two id spaces merge here, so the migrated requirements are RENUMBERED to continue after
    the highest existing criterion id -- never the other way round. An existing criterion id may
    already be cited from a commit message or a task file, and `id` exists precisely so such a
    citation still resolves; a requirement id was only ever local to a list that is ceasing to
    exist. `derived-from="requirement-N"` keeps the other half readable, and it is prefixed
    rather than bare because after this step a bare `3` is ambiguous between the two former
    spaces.

    No `pattern` is assigned and no sentence is rewritten. A requirement body is prose someone
    wrote to be read, not an EARS sentence waiting to be extracted -- the same boundary R4 and R5
    draw, arriving through a different door.
    """
    block = REQUIREMENTS.search(text)
    if not block:
        return text
    entries = REQUIREMENT.findall(block.group(2))
    if not entries:
        return text[:block.start()] + text[block.end():]

    ids = [int(i) for i in criterion_ids(text) if i and i.isdigit()]
    nxt = (max(ids) + 1) if ids else 1

    criteria = CRITERIA_BLOCK.search(text)
    indent = (criteria.group(1) if criteria else block.group(1)) + "  "

    rendered = []
    for attrs, body in entries:
        old = re.search(r'id="([^"]*)"', attrs)
        moscow = re.search(r'priority="([^"]*)"', attrs)
        priority = MOSCOW_TO_P.get(moscow.group(1) if moscow else "", "P1")
        derived = ' derived-from="requirement-%s"' % old.group(1) if old else ""
        prose = " ".join(body.split())
        rendered.append('%s<criterion id="%d" priority="%s"%s>\n%s  %s\n%s</criterion>'
                        % (indent, nxt, priority, derived, indent, prose, indent))
        nxt += 1
    added = "\n".join(rendered)

    if not criteria:
        base = block.group(1)
        return (text[:block.start()]
                + "%s<acceptance-criteria>\n%s\n%s</acceptance-criteria>\n" % (base, added, base)
                + text[block.end():])

    text = (text[:criteria.end(2)].rstrip("\n") + "\n" + added + "\n" + text[criteria.start(3):])
    block = REQUIREMENTS.search(text)
    return text[:block.start()] + text[block.end():]


def crd_problems(text):
    """Escalations about a CRD itself rather than about a transformation (item 47).

    A `wont-have` requirement cannot be placed. Sending it to P2 would make it buildable by
    default, since `--requirement-level` defaults to P2; dropping it would delete something a
    person wrote down. Both are decisions about the change rather than about its format, so the
    file is named and nothing is written -- the escalation path that already exists, used for the
    reason it exists.
    """
    problems = []
    for attrs, _body in REQUIREMENT.findall(text):
        moscow = re.search(r'priority="([^"]*)"', attrs)
        if moscow and moscow.group(1) not in MOSCOW_TO_P:
            rid = re.search(r'id="([^"]*)"', attrs)
            problems.append(
                "R10: requirement %s is `%s`, which has no P0|P1|P2 equivalent. P2 would make it "
                "buildable by default and dropping it would delete a decision -- neither is a "
                "formatting change, so the tier belongs on <meta><priority> and this requirement "
                "needs a person" % (rid.group(1) if rid else "?", moscow.group(1)))
    return problems


def _definition(text):
    """A feature's definition completeness, in EITHER spelling.

    Core section 3: a reader that finds <status> where it expects <definition> treats it as that
    element and carries on, because a hard cutover strands the artefacts that are only old. This
    reader did not, and the consequence was not a missed read -- it was a MISROUTED one. An
    `excluded` feature still carrying the old tag slipped past the convention check on the way in
    and was caught on the way out, after R1 had renamed the tag for it; and on the way out, a gap
    the artefact arrived with is indistinguishable from a gap the migration created. One is a
    sentence nobody has written yet and the other is a bug in this file, so telling them apart is
    the whole point of routing them to different exit codes.
    """
    m = META.search(text)
    if not m:
        return None
    d = re.search(r"<(definition|status)>\s*([a-z-]+)\s*</\1>", m.group(1))
    return d.group(2) if d else None


def convention_problems(text, path=None, index_slugs=None):
    """R7 and R8 (item 4): the conventions a corpus invented, as rules a postcondition can hold.

    These transform NOTHING. A migration cannot invent a rationale for a decision it was not
    present for -- what it can do is refuse to finish while one is missing, which turns "somebody
    will notice" into an exit code at the moment the file is being touched anyway.

    `index_slugs` is the set of slugs index.md still points at. R8's third clause needs it and
    is skipped when the index was not read, rather than passing silently: a check that cannot
    run says so at its caller.
    """
    problems = []
    definition = _definition(text)
    # The TAG THE FILE ACTUALLY USES, so the message quotes something greppable. These lines
    # named <definition> unconditionally, which was harmless while only migrated files could
    # reach them and became misleading the moment the dual read let an unmigrated one through:
    # an operator told their file says <definition>excluded</definition> will not find that
    # string in a file that says <status>excluded</status>.
    tag = "status" if re.search(r"<status>\s*[a-z-]+\s*</status>", META.search(text).group(1)) \
        else "definition"

    if definition == "excluded":
        body = re.search(r"<rationale>(.*?)</rationale>", text, re.S)
        if not body or not body.group(1).strip():
            problems.append(f"R7: <{tag}>excluded</{tag}> with no <rationale>. A "
                            "feature nobody will build is a decision, and a decision nobody "
                            "can reconstruct is a gap in the record")

    if definition == "superseded":
        successor = re.search(r'<superseded-by\s+slug="([^"]*)"', text)
        if not successor or not successor.group(1).strip():
            problems.append(f"R8: <{tag}>superseded</{tag}> with no "
                            "<superseded-by slug=>. Without the pointer the feature is merely "
                            "missing, and nothing says what absorbed it")
        elif path:
            sibling = os.path.join(os.path.dirname(path), successor.group(1) + ".md")
            if not os.path.isfile(sibling):
                problems.append(f"R8: <superseded-by slug=\"{successor.group(1)}\"> names a "
                                f"feature that does not exist")
        slug = re.search(r"<slug>\s*([a-z0-9-]+)\s*</slug>", text)
        if index_slugs is not None and slug and slug.group(1) in index_slugs:
            problems.append(f"R8: {slug.group(1)} is superseded and index.md still points at "
                            f"it. A merged feature leaves the planning view; leaving the entry "
                            f"makes the feature count wrong and gives --priority something to "
                            f"select that nobody intends to build")
    return problems


def _index_slugs(root):
    """Slugs index.md still points at, or None when there is no index to read."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if "index.md" in filenames:
            try:
                text, _eol = read(os.path.join(dirpath, "index.md"))
            except UnicodeDecodeError:
                # None is the documented "there was no index to read", and R8's third clause is
                # skipped rather than guessed. Nothing is lost by being quiet here: the walk
                # reaches this same file and escalates it by name, so the run stops regardless.
                return None
            return {m for m in re.findall(r'file="features/([a-z0-9-]+)\.md"', text)}
    return None


def _stamp_criteria(text):
    """Add priority="P1" and derived-from="{id}" to every criterion lacking them.

    TOTAL, deliberately. An absent `priority` and a deliberate P1 are indistinguishable, so a
    partly-assigned corpus could not be told from a finished one -- and a transformation whose
    completion is invisible cannot be resumed. See migration.md.
    """
    def one(m):
        attrs = m.group(1)
        cid = re.search(r'id="([^"]*)"', attrs)
        add = ""
        if not re.search(r'\bpriority=', attrs):
            add += ' priority="P1"'
        if cid and not re.search(r'\bderived-from=', attrs):
            add += ' derived-from="%s"' % cid.group(1)
        return "<criterion%s%s>" % (attrs.rstrip(), add)
    return CRITERION.sub(one, text)


# ------------------------------------------------------------------------ rules
#
# (id, target version, artefact kind, precondition over the OLD shape, transform, postcondition)
#
# `applies` and `done` together are the file's own record of where it is, which is why nothing
# needs stamping. A step whose `done` cannot be satisfied by the transform alone is PARTIAL --
# see PARTIAL_OF below.

RULES = [
    ("R1", "schema-2", "feature",
     lambda t: _meta_has(t, "status"),
     lambda t: _meta_swap(t, "status", "definition"),
     lambda t: _meta_has(t, "definition") and not _meta_has(t, "status")),

    ("R2", "schema-2", "crd",
     lambda t: _meta_has(t, "status"),
     lambda t: _meta_swap(t, "status", "workflow"),
     lambda t: _meta_has(t, "workflow") and not _meta_has(t, "status")),

    ("R3", "schema-2", "project-context",
     lambda t: bool(_entries_with(t, "status")),
     lambda t: FEATURE_ENTRY.sub(lambda m: re.sub(r"\bstatus=", "built=", m.group(0)), t),
     lambda t: not _entries_with(t, "status")
               and len(_entries_with(t, "built")) == len(FEATURE_ENTRY.findall(t))),

    # R4 is the mixed one. The transform does the attributes; `pattern` and the sentence are
    # judgements the guide forbids a machine to make, so `done` is not reachable from here.
    # `done` is VACUOUSLY true for an artefact with no criteria, and that is correct rather
    # than convenient: a feature carrying zero criteria is `excluded` or `superseded`, which
    # the schema allows outright. Requiring at least one would have made a legitimate artefact
    # unplaceable and escalated it -- turning a rule about criteria into a rule about features.
    ("R4", "schema-3", "feature",
     lambda t: bool(_criteria_lacking(t, "priority")),
     _stamp_criteria,
     lambda t: not _criteria_lacking(t, "pattern") and not _criteria_lacking(t, "priority")),

    ("R5", "schema-3", "crd",
     lambda t: bool(_criteria_lacking(t, "priority")),
     _stamp_criteria,
     lambda t: not _criteria_lacking(t, "pattern") and not _criteria_lacking(t, "priority")),

    # R6 is mixed for the same reason R4 is: the two mechanical halves are here, and
    # <user-story>, <depends-on>, <gaps> and <architecturally-significant> are content a
    # machine has nothing to derive from. `done` requires the story, which is what a person or
    # `schema-migrator` supplies.
    # R9 is what-next.md's half of schema-4 (items 11 and 12). Mechanical: the <meta> wrap.
    # Judgement: <prd-slug> and <next-command>, `kind=` on each step, and rehoming <tbd-items>
    # entries into the feature files' own <gaps> -- which is why the entries are LEFT IN PLACE
    # rather than dropped. A migration that deleted them would lose the only record of what an
    # interview did not finish.
    ("R9", "schema-4", "what-next",
     lambda t: not re.search(r"<meta>.*?<status>", t, re.S),
     _wrap_what_next_meta,
     lambda t: bool(re.search(r"<meta>.*?<status>", t, re.S))
               and "<prd-slug>" in t and "<tbd-items>" not in t),

    # R10 is mixed for the same reason R4 and R5 are, and it is the first rule that MOVES
    # content rather than relabelling it. The move is mechanical; the EARS sentence, the
    # `pattern`, <meta><priority> and <gaps> are not. `done` names all of them, so a CRD that has
    # only had the move applied reports PARTIAL rather than MIGRATED.
    ("R10", "schema-5", "crd",
     lambda t: "<requirements>" in t,
     _requirements_to_criteria,
     lambda t: "<requirements>" not in t
               and not _criteria_lacking(t, "priority")
               and not _criteria_lacking(t, "pattern")
               and _meta_has(t, "priority")),

    # R11 and R12 are schema-6's mechanical half: a DOCUMENT status outside its own enum.
    # core section 3 gives `<status>` in index.md and what-next.md the values `in-progress` and
    # `complete`; nothing had ever validated the value, and the fixture carried `defined` in both
    # files at once -- so F3's DISAGREE check passed while /prd --resume, which finds unfinished
    # PRDs by this tag, could classify neither.
    #
    # The mapping is to `in-progress`, the WEAKER claim, and that is the whole judgement here: a
    # machine resolving toward `complete` would assert that an interview finished which nobody
    # finished. Resolving toward protection is the same rule the layer-graph spike settled.
    ("R11", "schema-6", "prd",
     lambda t: _bad_doc_status(t),
     lambda t: _fix_doc_status(t),
     lambda t: not _bad_doc_status(t)),

    ("R12", "schema-6", "what-next",
     lambda t: _bad_doc_status(t),
     lambda t: _fix_doc_status(t),
     lambda t: not _bad_doc_status(t)),

    # R13 has NO mechanical half, and it is the first rule of which that is true. Item 40's gate
    # is `the mechanical tests pass AND a review has been recorded`; a review is a person having
    # read the feature, and there is nothing in the file to derive one from. So the transform is
    # the identity, every `defined` feature reports PARTIAL, and `--check` refuses the tree until
    # somebody runs `check-definition.py --record-review`.
    #
    # The alternative was a transform that writes a placeholder review with no reviewer. That is
    # a record of nothing, and this repository's own rule is that a ledger records SHAs rather
    # than adjectives -- an unsigned review is the adjective.
    ("R13", "schema-6", "feature",
     lambda t: _is_defined(t) and "<review" not in t,
     lambda t: t,
     lambda t: not _is_defined(t) or "<review" in t),

    ("R6", "schema-4", "feature",
     lambda t: _meta_has(t, "priority") or ("<notes>" in t and "<considerations>" not in t)
               or "<user-story>" not in t,
     lambda t: _split_notes(_meta_drop(t, "priority")),
     lambda t: not _meta_has(t, "priority")
               and ("<notes>" not in t or "<considerations>" in t)
               and "<user-story>" in t),
]

DOC_STATUS = re.compile(r"<status>\s*([^<]*?)\s*</status>")
DOC_STATUS_VALUES = ("in-progress", "complete")


def _bad_doc_status(text):
    m = DOC_STATUS.search(text)
    return bool(m) and m.group(1) not in DOC_STATUS_VALUES


def _fix_doc_status(text):
    return DOC_STATUS.sub("<status>in-progress</status>", text, count=1)


def _is_defined(text):
    return bool(re.search(r"<definition>\s*defined\s*</definition>", text))


# Rules whose transform cannot reach their own postcondition, and what the mechanical half DOES
# reach. Named rather than inferred: "the transform did not finish" and "the transform is broken"
# are different answers and only one of them is a defect.
PARTIAL_OF = {
    # `priority` alone, and NOT `derived-from`. Priority is the total one -- written in rather
    # than left to the documented default precisely so that a partly-assigned corpus can be told
    # from a finished one -- so it is the honest marker of "the mechanical half landed".
    # `derived-from` is neither total nor permanent: an authored criterion never had one (core
    # section 2 makes it migration-only) and a migrated one LOSES it at sign-off, so requiring it
    # here would call a signed-off file unfinished and an authored one half-migrated.
    "R4": lambda t: not _criteria_lacking(t, "priority"),
    "R5": lambda t: not _criteria_lacking(t, "priority"),
    "R6": lambda t: not _meta_has(t, "priority")
                    and ("<notes>" not in t or "<considerations>" in t),
    "R9": lambda t: bool(re.search(r"<meta>.*?<status>", t, re.S)),
    "R10": lambda t: "<requirements>" not in t and not _criteria_lacking(t, "priority"),
    # R13's mechanical half is EMPTY, so it is complete the moment the rule is reached. Stated as
    # a constant rather than left out: "there was nothing mechanical to do" and "the mechanical
    # part failed" are different answers, and only the second is a defect.
    "R13": lambda t: True,
}

# Artefacts a step does not change. Named rather than defaulted: "no rule matched" and "no rule
# was needed" are different answers, and only the first is an escalation.
UNCHANGED = {
    "schema-6": {"project-context", "crd"},
    "schema-2": {"prd", "what-next"},
    "schema-3": {"prd", "what-next", "project-context"},
    "schema-4": {"prd", "project-context", "crd"},
    "schema-5": {"prd", "project-context", "what-next", "feature"},
}


# ----------------------------------------------------------------- invariants

VALUE = re.compile(r">\s*([^<>\s][^<>]*?)\s*<|=\"([^\"]*)\"")


def values(text):
    """Every element body and attribute value, sorted.

    A rename must leave this IDENTICAL. Asserting only the tag names would not have noticed a
    transform that changed a value on the way past.
    """
    return sorted(v for body, attr in VALUE.findall(text) for v in (body or attr,) if v.strip())


def tag_counts(text):
    return len(re.findall(r"<[A-Za-z][\w-]*", text))


def criterion_ids(text):
    return [a.get("id") for a in _criteria_attrs(text)]


# --------------------------------------------------------------------- driving

def artefacts(path):
    if os.path.isfile(path):
        yield path
        return
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                yield os.path.join(dirpath, name)


def rules_for(kind, version):
    return [r for r in RULES if r[1] == version and r[2] == kind]


def detect(text, kind):
    """The highest version whose step is complete for this artefact, or None if unplaceable."""
    reached = VERSIONS[0]
    for version in VERSIONS[1:]:
        if kind in UNCHANGED.get(version, ()):
            reached = version
            continue
        governing = rules_for(kind, version)
        if not governing:
            reached = version
            continue
        if all(r[5](text) for r in governing):
            reached = version
        elif any(r[3](text) for r in governing) or any(
                rid in PARTIAL_OF and PARTIAL_OF[rid](text) for rid, *_ in governing):
            break
        else:
            return None
    return reached


def steps_to(kind, current, target):
    lo, hi = VERSIONS.index(current), VERSIONS.index(target)
    return [(v, rules_for(kind, v)) for v in VERSIONS[lo + 1:hi + 1]]


def apply_steps(text, kind, current, target):
    """Returns (new text, [rule ids to report], [problems], verdict).

    The reported ids are what the skill hands `schema-migrator` as the outstanding work, so a
    rule left PARTIAL by an EARLIER pass belongs in that list even though this pass did not run
    its transform. Reporting only what ran made a resumed migration say `judgements outstanding
    ()`, which is the one thing the operator resuming it needs to know.
    """
    applied, outstanding, problems, partial = [], [], [], False
    for version, rules in steps_to(kind, current, target):
        if kind in UNCHANGED.get(version, ()):
            continue
        for rid, _v, _k, precond, transform, done in rules:
            if done(text):
                continue
            if not precond(text):
                # A precondition that no longer matches is not automatically an unplaceable
                # file: for R9 and R10 it goes false the MOMENT their mechanical half lands
                # (<meta><status> now exists; <requirements> is gone) while `done` stays false
                # pending the judgements. On a second pass such a rule was neither skippable nor
                # applicable, and a file sitting in exactly the state it was supposed to be in
                # was reported FAILED -- which broke the first property this migration claims,
                # that a partly migrated tree is safe to re-enter. detect() has always consulted
                # PARTIAL_OF at this same fork; this is application catching up with detection.
                if rid in PARTIAL_OF and PARTIAL_OF[rid](text):
                    partial = True
                    outstanding.append(rid)
                else:
                    problems.append(f"{rid}: no precondition matched at {version}")
                continue
            before = text
            text = transform(text)
            applied.append(rid)
            # Every id that resolved before the step must still resolve after it, in place.
            # Equality was the rule until R10, which APPENDS migrated requirements as criteria;
            # a prefix check is strictly stronger for every rule that adds none, and is the
            # actual property worth holding -- `id` exists so a citation survives.
            was = criterion_ids(before)
            if criterion_ids(text)[:len(was)] != was:
                problems.append(f"{rid}: an existing criterion id changed -- a citation that "
                                f"resolved before this step must resolve after it")
            if not done(text):
                if rid in PARTIAL_OF and PARTIAL_OF[rid](text):
                    partial = True
                else:
                    problems.append(f"{rid}: postcondition does not hold after transforming")
    report = applied + [r for r in outstanding if r not in applied]
    return text, report, problems, ("PARTIAL" if partial else "MIGRATED")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("--to", dest="target")
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"usage: no such path: {args.path}", file=sys.stderr)
        return 3
    if not args.detect:
        if not args.target:
            print("usage: --to <schema> is required unless --detect", file=sys.stderr)
            return 3
        if args.target not in VERSIONS:
            print(f"usage: unknown schema {args.target}. Known: {VERSIONS}", file=sys.stderr)
            return 3

    escalations, failures, short, skipped = [], [], [], []
    found = {}
    migrated = already = partial = 0
    root = args.path if os.path.isdir(args.path) else (os.path.dirname(args.path) or ".")
    index_slugs = _index_slugs(root)

    for path in artefacts(args.path):
        rel = os.path.relpath(path, root)
        try:
            text, eol = read(path)
        except UnicodeDecodeError as e:
            # Exit 2's guarantee, one layer below the one it was written for: nothing was
            # written for this file, and it is named. Replacing the bytes it could not decode
            # and carrying on is the only failure here that loses content irrecoverably.
            escalations.append(
                f"{rel}: not valid UTF-8 ({e.reason}, byte {e.start}) -- cannot be read without "
                f"guessing at what those bytes meant. NOT WRITTEN")
            continue
        kind = kind_of(text)

        if kind is None:
            # `Does this file have a root element?` answers whether a README is an artefact,
            # which is what it was added for, and silently answers a second question nobody
            # asked it: whether a what-next.md holding `# What Next` is one. A /prd run that
            # went off-script and never wrote the skeleton produces exactly that, and the file
            # is an artefact of the PRD in every sense except the one being tested.
            #
            # So the absent root is not the whole question. `SHOULD this file have had one` is,
            # and only the NAME answers it -- see toolchain_owns().
            if toolchain_owns(path):
                escalations.append(
                    f"{rel}: no artefact root element, in a file the toolchain writes -- it "
                    f"should be an artefact and is not. Nothing here can be migrated; the "
                    f"skeleton has to be authored or regenerated. NOT WRITTEN")
            else:
                skipped.append(f"{rel}: no artefact root element -- not an artefact; left alone")
            continue

        current = detect(text, kind)
        if current is None:
            escalations.append(
                f"{rel}: a <{kind}> in no recognised schema -- no migration can be selected")
            continue

        if args.detect:
            found[current] = found.get(current, 0) + 1
            if not args.quiet:
                print(f"  {current:<10} {kind:<16} {rel}")
            continue

        # R7/R8 are asserted on EVERY feature file the run sees, before anything else decides
        # what to do with it. They are rules about the artefact rather than about a
        # transformation, so attaching them to a step would have let an already-migrated tree
        # violate them in silence -- which is what the first version of this did.
        if kind == "feature":
            broken = convention_problems(text, path, index_slugs)
            if broken:
                # ESCALATION, not a failure. R7 and R8 transform nothing, so they cannot fail the
                # way a transformation does: what is missing is a sentence a person has to write,
                # and exit 1 carries `a defect in the rule, not in the artefact` along with
                # `never work around it by editing a file by hand`. Both are exactly backwards
                # here. The guide had already settled the identical question one rule along --
                # a `wont-have` requirement escalates `using machinery that already exists` --
                # because it too is a decision about the feature rather than about its format.
                escalations.append(
                    f"{rel}: " + "; ".join(broken)
                    + " -- NOT WRITTEN. A person supplies this; the migration cannot")
                continue

        # Asserted before the steps rather than inside R10, so that `detect` stays honest: a CRD
        # holding a `wont-have` requirement IS a valid schema-4 artefact, it just cannot be
        # carried to schema-5 by a machine. Making R10's precondition exclude it would have made
        # detect() call the file unplaceable, which is a different and wrong answer.
        if kind == "crd" and VERSIONS.index(args.target) >= VERSIONS.index("schema-5"):
            broken = crd_problems(text)
            if broken:
                escalations.append(f"{rel}: " + "; ".join(broken) + " -- NOT WRITTEN")
                continue

        if VERSIONS.index(current) >= VERSIONS.index(args.target):
            already += 1
            if not args.quiet:
                print(f"  {'ALREADY':<10} {rel}")
            continue

        new, applied, problems, verdict = apply_steps(text, kind, current, args.target)

        if kind == "feature":
            problems = problems + convention_problems(new, path, index_slugs)

        # Invariants that hold across every step, checked before anything is kept.
        if verdict == "MIGRATED" and not problems:
            if values(new) != values(text) and not applied_adds_values(applied):
                problems.append("values changed; a rename that alters a value is not a rename")

        if problems:
            failures.append(f"{rel}: " + "; ".join(problems) + " -- RESTORED")
            continue

        if not args.check and not args.dry_run:
            write(path, new, eol)
        if verdict == "PARTIAL":
            partial += 1
            short.append(f"{rel}: mechanically migrated; judgements outstanding "
                         f"({', '.join(applied)}) -- a person or `schema-migrator` finishes it")
        else:
            migrated += 1
        if not args.quiet:
            verb = verdict if not (args.dry_run or args.check) else "WOULD " + verdict[:4]
            print(f"  {verb:<10} {rel}  [{', '.join(applied) or '-'}]")

    if args.detect:
        for line in skipped:
            print(f"  SKIPPED    {line}")
        for line in escalations:
            print(f"  ESCALATE   {line}", file=sys.stderr)
        if not args.quiet:
            # The skill's Phase 1 asks for these five numbers, and until now nothing produced
            # them: a run ends with a summary line and --detect ended with the last row. An
            # agent told to state a total it was never given counts the listing by eye, and on
            # a sixty-six line one it reported sixty features where there were sixty-five --
            # every other fact in the report correct, which is what makes the invented number
            # hard to see. This is item 51's defect in this repository's own skill: an element
            # with no producer.
            #
            # DERIVED from the same rows that were printed, never counted a second way. A
            # summary that can disagree with the listing beneath it is the same defect again,
            # one layer down and harder to catch.
            total = sum(found.values())
            print(f"\n{total} artefact{'' if total == 1 else 's'} under {args.path}, "
                  f"{len(escalations)} escalated, "
                  f"{len(skipped)} not artefact{'' if len(skipped) == 1 else 's'}")
            if found:
                # In VERSIONS order rather than by count: `how many are already current` is the
                # number Phase 1 leads with, and it is the last column when the order is the
                # schema's own.
                print("    " + "     ".join(f"{v}  {found[v]}"
                                            for v in VERSIONS if v in found))
        return 2 if escalations else 0

    if not args.quiet:
        print(f"\n{migrated} migrated, {partial} partial, {already} already in {args.target}, "
              f"{len(escalations)} escalated, {len(failures)} failed, "
              f"{len(skipped)} not artefacts")

    # Named rather than merely counted. A file this tool has no claim on is uninteresting
    # exactly until it is a feature file whose root element somebody broke, and a count cannot
    # tell those apart -- so the operator gets the list and can.
    for line in skipped:
        print(f"  SKIPPED    {line}")
    for line in short:
        print(f"  PARTIAL    {line}", file=sys.stderr)
    for line in failures:
        print(f"  FAILED     {line}", file=sys.stderr)
    for line in escalations:
        print(f"  ESCALATE   {line}", file=sys.stderr)

    if failures:
        return 1
    # --check asks a different question from a run: not "can this be migrated" but "is it".
    # A file the run WOULD transform, and a PARTIAL one, are both short of the target.
    if args.check and (migrated or partial):
        print(f"\nCHECK FAILED: {migrated + partial} file(s) are not yet in {args.target}",
              file=sys.stderr)
        return 1
    if escalations:
        return 2
    if partial:
        return 0
    return 0


def applied_adds_values(applied):
    """True when a step legitimately introduces new attribute values.

    R4/R5 add `priority` and `derived-from`; R6 removes a duplicated <priority> and re-nests
    note prose; R10 maps MoSCoW onto P0|P1|P2, which replaces one value with another by design;
    R11/R12 map a document `<status>` outside its own enum onto `in-progress`, which is the same
    act one artefact along. So the rename invariant -- values identical before and after -- does
    not hold for them and must not be asserted. Stated per rule rather than switched off globally,
    because the invariant is the only thing standing between a rename and an edit for R1-R3.

    R13 is deliberately NOT here: it changes nothing at all, so the invariant holds for it and
    exempting it would hide a transform that had started doing something.
    """
    return any(rid in ("R4", "R5", "R6", "R9", "R10", "R11", "R12") for rid in applied)


if __name__ == "__main__":
    sys.exit(main())
