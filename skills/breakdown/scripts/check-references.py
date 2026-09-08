#!/usr/bin/env python3
"""Validate the references that leave the PRD (plan item 39, finding P24).

A PRD cites artefacts the toolchain cannot see: architecture decision records, an
open-questions register, and -- from the other direction -- decision records that name the
features they drive. Measured against the sample corpus: 19 distinct decision records over 136
mentions, 22 distinct questions over 44, none of them validated. A feature whose scope was
settled by a record that no longer exists is broken down without it, and nothing says so.

AND THE SAME RULE ON THE CRD PATH, WHICH NEVER HAD IT

A CRD carries three references of its own and, until this, **nothing followed any of them**:
`<project-ref>` names the `PROJECT.md` the change is against and was `Required` in every CRD;
`<prd-ref>` is the only structured link from a change back to the PRD that produced the feature;
and each `<feature-ref id=>` names a feature in `PROJECT.md`. All three were `open` rows in
`readers.md` -- a producer with no consumer, three times, which is P2's shape on the CRD path.

`check-references.py <crd-file> --project-path <path>` resolves them. It is the same program
rather than a second one, because the rule is the same rule: a reference that names something
must resolve to it, or be reported by name.

**`<project-ref>` is CHECKED against the project the run resolved, never used to resolve it.**
Letting a document choose which `PROJECT.md` a run reads would hand a file authority over where
the run points; comparing them instead catches the case that matters -- a CRD describing a
change to one project being executed against another.

WHAT IS CHECKED

  ADR-NNN citations   resolve to a record in the decision directory
                      a citation of a *superseded* record is reported with its successor
  OQ-NNN citations    resolve to an entry in the open-questions register
                      a citation of a *resolved* question is reported with what resolved it
  **Drives:** links   in each decision record, resolve to a file that exists
                      (the record's template and conventions: schema/decision-record.md)
  P-NNN citations     resolve to a <principle id=> in architecture.md's <principles> section
  significant features are named by some record's **Drives:**, or the absence is reported
  unflagged features that LOOK significant are reported as candidates, and never flagged

A FLAG WITH TWO DIRECTIONS, AND A THIRD READING THAT IS NEITHER

Item 35's flag is a declared judgement, so this script reads it both ways round: a flagged feature
no record drives is STALE, and an unflagged feature matching the published ASR heuristics is a
CANDIDATE. A candidate is not a defect and never affects the exit code, including under
--strict -- the heuristics are a screen for a conversation, and a screen that can fail a build is
a heuristic that has been promoted to a rule behind everyone's back.

Two of the six `because` values are screened, because only two are structural: a quality
attribute named in the feature's own text, and cross-cutting reach measured as the number of
other documents that name this feature. `first-of-a-kind`, `risk` and `constraint` are judgements
with no signal in the file, and guessing them would produce a candidate list nobody reads.

A FLAG THAT REPORTS, NEVER REFUSES (item 35)

`<architecturally-significant>` is a declared judgement -- not derivable from any structural
property, which is the whole reason it is a flag. So a flagged feature that no decision record
drives is STALE, not DANGLING: it may be a decision nobody has written yet, or a feature that
genuinely needs none. The script says which features are in that state and stops there.

Without this the flag would have had no reader until item 38's gate, and an element nobody reads
is the defect this plan exists to remove.

PRINCIPLES WERE THE DEFERRED TENTH (item 39, closed by items 28 and 37)

This script originally checked 180 of the corpus's 190 references and said so: a principle had
nowhere to live until item 28 gave `architecture.md` its `<principles>` section, so there was
nothing for a citation to resolve against, and validating one would have asserted a file that
did not exist. That section now exists, so the remaining 10 are checked here -- and the
exclusion is removed rather than left quietly in force.

**`P-NNN`, and the hyphen is load-bearing.** `P0`, `P1` and `P2` without one are item 34's
criterion priorities and appear throughout a PRD; matching those would report a dangling
principle on every prioritised criterion in the corpus.

WHAT IS NOT CHECKED, AND WHY

Nothing, now. The heading is kept so the next thing to be deferred is written down here rather
than skipped in silence: a validator quietly passing over a class of input is worse than one
that says what it passes over.

The register itself is never written. It is human-maintained and outlives any one PRD; this
script reports and never repairs (plan item 39).

USAGE

    check-references.py <prd-dir> [--adr-dir DIR] [--questions FILE]
                        [--architecture FILE] [--strict] [--quiet]

  <prd-dir>      directory holding index.md, what-next.md and features/
  --adr-dir      decision records. Default: discovered, see DISCOVERY below
  --questions    the open-questions register, a single markdown file
  --architecture architecture.md. Default: discovered by walking up from <prd-dir>
  --strict       exit non-zero on warnings too, not just on dangling references
  --quiet        print the summary line only

DISCOVERY

`--adr-dir` and `--questions` default to the corpus project's layout, tried in order and
relative to <prd-dir>: ../../architecture/decisions, ../../../architecture/decisions,
../../docs/architecture/decisions. The register is looked for as open-questions.md beside the
decision directory and one level above it. A citation with nowhere to resolve *against* is an
error naming the flag to pass -- silently passing because the directory was not found is how a
validator becomes decorative.

EXIT CODES

  0  no dangling references (warnings may have been reported)
  1  at least one dangling reference, or a citation with no register to check against
  2  usage error
"""

import argparse
import os
import re
import sys

ADR_CITATION = re.compile(r"\bADR-(\d{1,4})\b")
OQ_CITATION = re.compile(r"\bOQ-(\d{1,4})\b")
# `**Status:** Superseded by ADR-014` -- item 36's convention, already regular in the corpus.
STATUS_FIELD = re.compile(r"^\s*\*\*Status:\*\*\s*(.+?)\s*$", re.M)
DRIVES_FIELD = re.compile(r"^\s*\*\*Drives:\*\*\s*(.+?)\s*$", re.M)
# Item 35. `criteria=` is optional and not read here -- which criteria carry the
# significance is for a person reading the record, not for this check.
SIGNIFICANT = re.compile(r"<architecturally-significant\b([^>]*)>")
# Core section 8's enum. Named here because this is the script that decides it: a `because`
# outside the set claims a design step is warranted in a kind nothing downstream can act on.
SIGNIFICANCE_KINDS = {"quality-attribute", "risk", "first-of-a-kind", "cross-cutting",
                      "external-dependency", "constraint"}
SLUG_EL = re.compile(r"<slug>\s*([a-z0-9-]+)\s*</slug>")

# The published ASR heuristics, reduced to the two that leave a mark in the file. Matched
# case-insensitively on whole words -- `secure` must not fire on `security-blanket`, and a
# substring match on "audit" fires on every "auditory".
QUALITY_WORDS = re.compile(
    r"\b(latency|throughput|performance|availability|uptime|scalab\w*|secur\w*|encrypt\w*|"
    r"authenticat\w*|authoris\w*|authoriz\w*|password\w*|credential\w*|complian\w*|audit|"
    r"audited|retention|concurren\w*|"
    r"idempotent|failover|backpressure|rate.limit\w*)\b", re.I)
# Reach: how many OTHER documents name this feature. Three is where a change stops being local.
CROSS_CUTTING_AT = 3
MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
# An id in a filename: `ADR-007-title.md`, `007-title.md`, `adr007.md`.
FILENAME_ID = re.compile(r"^(?:adr[-_]?)?(\d{1,4})\b", re.I)
RESOLVED_HEADING = re.compile(r"^#{1,6}\s*(.*\bOQ-(\d{1,4})\b.*)$", re.M)
# The hyphen separates a principle from item 34's criterion priorities (P0, P1, P2).
PRINCIPLE_CITATION = re.compile(r"\bP-(\d{1,4})\b")
PRINCIPLES_BLOCK = re.compile(r"<principles[\s>].*?</principles>", re.S)
PRINCIPLE_ID = re.compile(r"""<principle\b[^>]*\bid=["']([^"']+)["']""", re.I)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def markdown_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                yield os.path.join(dirpath, name)


def discover_adr_dir(prd_dir):
    for rel in ("../../architecture/decisions",
                "../../../architecture/decisions",
                "../../docs/architecture/decisions"):
        cand = os.path.normpath(os.path.join(prd_dir, rel))
        if os.path.isdir(cand):
            return cand
    return None


def discover_questions(prd_dir, adr_dir):
    roots = [prd_dir, os.path.join(prd_dir, "..", "..")]
    if adr_dir:
        roots = [adr_dir, os.path.join(adr_dir, ".."), os.path.join(adr_dir, "..", "..")] + roots
    for root in roots:
        cand = os.path.normpath(os.path.join(root, "open-questions.md"))
        if os.path.isfile(cand):
            return cand
    return None


def index_records(adr_dir):
    """id -> {path, status, superseded_by, drives}. Ids come from the filename, then a heading."""
    records = {}
    for path in markdown_files(adr_dir):
        text = read(path)
        m = FILENAME_ID.match(os.path.basename(path))
        rid = m.group(1) if m else None
        if rid is None:
            head = ADR_CITATION.search(text[:400])
            rid = head.group(1) if head else None
        if rid is None:
            continue
        status_m = STATUS_FIELD.search(text)
        status = status_m.group(1) if status_m else ""
        successor = None
        if "supersed" in status.lower():
            after = ADR_CITATION.search(status)
            successor = after.group(0) if after else None
        drives = []
        for line in DRIVES_FIELD.findall(text):
            drives += [target for _, target in MD_LINK.findall(line)]
        key = rid.lstrip("0") or "0"
        records[key] = {"path": path, "status": status,
                        "superseded_by": successor, "drives": drives}
    return records


def index_questions(path):
    """id -> resolution text, or None when the entry is still open."""
    text = read(path)
    questions = {}
    for heading, qid in RESOLVED_HEADING.findall(text):
        key = qid.lstrip("0") or "0"
        # Item 36's convention: a resolved question is annotated in place, in its heading.
        resolved = re.search(r"\bresolved\b(.*)$", heading, re.I)
        questions[key] = resolved.group(0).strip() if resolved else None
    for qid in OQ_CITATION.findall(text):
        questions.setdefault(qid.lstrip("0") or "0", None)
    return questions


def cite(text, pattern):
    """(key, as-written, line) per citation. The key matches; the as-written form is reported.

    ADR-007 and ADR-7 are the same record and a report that renames one to the other sends a
    reader looking for a string that is not in the file.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in pattern.finditer(line):
            out.append((m.group(1).lstrip("0") or "0", m.group(0), i))
    return out


def discover_architecture(prd_dir):
    """architecture.md at the project root -- walk up from the PRD, stopping at the repo root."""
    cur = prd_dir
    for _ in range(6):
        candidate = os.path.join(cur, "architecture.md")
        if os.path.isfile(candidate):
            return candidate
        if os.path.isdir(os.path.join(cur, ".git")):
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def index_principles(path):
    """Map a matchable key -> the principle id as declared.

    A file may declare `id="P-001"` while a feature cites `P-1`; both name the same principle and
    a reader would not hesitate between them, so the numeric part is a key too. Leading zeros are
    stripped for MATCHING only -- what gets reported is the citation as written, because sending
    someone to look for a string that is not in their file is its own defect. This script did
    exactly that with ADR-007 before it was fixed.
    """
    text = read(path)
    block = PRINCIPLES_BLOCK.search(text)
    if not block:
        return {}
    out = {}
    for pid in PRINCIPLE_ID.findall(block.group(0)):
        out[pid] = pid
        m = re.search(r"(\d+)", pid)
        if m:
            out[str(int(m.group(1)))] = pid
    return out


PROJECT_REF = re.compile(r"<project-ref>\s*(.*?)\s*</project-ref>", re.S)
PRD_REF = re.compile(r"<prd-ref>\s*(.*?)\s*</prd-ref>", re.S)
FEATURE_REF = re.compile(r'<feature-ref\b[^>]*\bid="([^"]+)"')
PROJECT_FEATURE = re.compile(r'<feature\b[^>]*\bid="([^"]+)"')


def check_crd(crd_path, project_path):
    """Resolve a CRD's own references. Returns (errors, warnings, counted)."""
    errors, warnings, counted = [], [], 0
    text = read(crd_path)
    rel = os.path.basename(crd_path)
    here = os.path.dirname(os.path.abspath(crd_path))

    def resolve(target):
        """A ref is relative to the project when one was given, else to the CRD."""
        if os.path.isabs(target):
            return target
        for base in ([project_path] if project_path else []) + [here]:
            candidate = os.path.normpath(os.path.join(base, target))
            if os.path.exists(candidate):
                return candidate
        return os.path.normpath(os.path.join(project_path or here, target))

    project_md = None
    m = PROJECT_REF.search(text)
    if not m:
        errors.append(f"{rel}: no <project-ref>. It is required, and a change with no named "
                      f"target is one nothing can place")
    else:
        counted += 1
        project_md = resolve(m.group(1))
        if not os.path.isfile(project_md):
            errors.append(f"{rel}: <project-ref>{m.group(1)}</project-ref> does not exist")
        elif project_path:
            # The comparison that makes the element worth having: a CRD naming a different
            # PROJECT.md from the one the run is using is a change about another codebase.
            expected = os.path.normpath(os.path.join(project_path, "PROJECT.md"))
            if os.path.normcase(os.path.abspath(project_md)) != os.path.normcase(
                    os.path.abspath(expected)):
                errors.append(f"{rel}: <project-ref> names {m.group(1)}, and this run is "
                              f"against {expected}. One of the two is about another project")

    m = PRD_REF.search(text)
    if m and m.group(1):
        counted += 1
        prd = resolve(m.group(1))
        if not os.path.exists(prd):
            errors.append(f"{rel}: <prd-ref>{m.group(1)}</prd-ref> does not exist -- the only "
                          f"structured link from this change back to the PRD that produced it")

    refs = FEATURE_REF.findall(text)
    known = None
    if project_md and os.path.isfile(project_md):
        known = set(PROJECT_FEATURE.findall(read(project_md)))
    for fid in refs:
        counted += 1
        if known is None:
            errors.append(f"{rel}: <feature-ref id=\"{fid}\"> and no PROJECT.md was resolved, "
                          f"so nothing can say whether that feature exists")
        elif fid not in known:
            errors.append(f"{rel}: <feature-ref id=\"{fid}\"> resolves to no <feature id=> in "
                          f"{os.path.basename(project_md)}")
    if not refs:
        warnings.append(f"{rel}: <related-features> names no feature. `which features does this "
                        f"change touch` is then answered by prose")

    # Item 76: significance, on this path too. The screen further down iterates a PRD *directory*
    # and `main()`'s CRD branch returns before reaching it, so a CRD's flag was read by nothing.
    # The element and its reader had to arrive together -- adding the element alone would have
    # been a producer with no consumer, which is the defect item 76 was written to fix, inverted.
    #
    # Same two assertions as the PRD path, plus the enum: a `because` nobody can name is not a
    # significance, one outside core section 8's set names a kind nothing acts on, and a flag no
    # decision record drives is a WARNING rather than a refusal -- the flag is a judgement and
    # its absence proves nothing.
    for attrs in SIGNIFICANT.findall(text):
        counted += 1
        because = re.search(r'because="([^"]*)"', attrs)
        if not because or not because.group(1).strip():
            errors.append(f"{rel}: <architecturally-significant> names no `because`, so it says "
                          f"a design step is warranted without saying which kind")
        elif because.group(1) not in SIGNIFICANCE_KINDS:
            errors.append(f"{rel}: <architecturally-significant because=\"{because.group(1)}\"> "
                          f"is not one of {'|'.join(sorted(SIGNIFICANCE_KINDS))} (core section 8)")
        else:
            warnings.append(f"{rel}: is architecturally significant ({because.group(1)}). A "
                            f"change of this shape is what a design step is for")
    return errors, warnings, counted


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir", metavar="prd-dir|crd-file")
    ap.add_argument("--project-path", help="the project a CRD is against; enables the "
                                           "<project-ref> comparison")
    ap.add_argument("--adr-dir")
    ap.add_argument("--questions")
    ap.add_argument("--architecture")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    prd_dir = os.path.abspath(args.prd_dir)

    # A CRD is one file, so it takes the CRD branch. Its references are different references and
    # the same rule.
    if os.path.isfile(prd_dir):
        project_path = os.path.abspath(args.project_path) if args.project_path else None
        errors, warnings, counted = check_crd(prd_dir, project_path)
        if not args.quiet:
            for line in errors:
                print(f"  DANGLING  {line}", file=sys.stderr)
            for line in warnings:
                print(f"  NOTE      {line}")
            print(f"{counted} reference(s) checked in {os.path.basename(prd_dir)}: "
                  f"{len(errors)} dangling, {len(warnings)} note(s)")
        if not args.project_path:
            print("  NOTE      no --project-path, so <project-ref> was resolved and not "
                  "compared against the project this run is for")
        return 1 if errors else 0

    if not os.path.isdir(prd_dir):
        print(f"REFUSED: no such PRD directory or CRD file: {prd_dir}", file=sys.stderr)
        return 2

    adr_dir = os.path.abspath(args.adr_dir) if args.adr_dir else discover_adr_dir(prd_dir)
    q_path = os.path.abspath(args.questions) if args.questions else discover_questions(
        prd_dir, adr_dir)

    arch_path = (os.path.abspath(args.architecture) if args.architecture
                 else discover_architecture(prd_dir))

    records = index_records(adr_dir) if adr_dir and os.path.isdir(adr_dir) else None
    questions = index_questions(q_path) if q_path and os.path.isfile(q_path) else None
    principles = (index_principles(arch_path)
                  if arch_path and os.path.isfile(arch_path) else None)

    errors, warnings, counted = [], [], 0

    for path in markdown_files(prd_dir):
        rel = os.path.relpath(path, prd_dir)
        text = read(path)

        for rid, written, line in cite(text, ADR_CITATION):
            counted += 1
            if records is None:
                errors.append(f"{rel}:{line}: cites {written} and no decision directory was "
                              f"found -- pass --adr-dir")
            elif rid not in records:
                errors.append(f"{rel}:{line}: {written} does not exist in "
                              f"{os.path.relpath(adr_dir, prd_dir)}")
            elif records[rid]["superseded_by"]:
                warnings.append(f"{rel}:{line}: {written} is superseded by "
                                f"{records[rid]['superseded_by']}")
            elif "supersed" in records[rid]["status"].lower():
                warnings.append(f"{rel}:{line}: {written} is superseded and names no successor")

        for pid, written, line in cite(text, PRINCIPLE_CITATION):
            counted += 1
            if principles is None:
                errors.append(f"{rel}:{line}: cites {written} and no architecture.md was found "
                              f"-- pass --architecture")
            elif not principles:
                errors.append(f"{rel}:{line}: cites {written} but "
                              f"{os.path.basename(arch_path)} declares no <principles> section")
            elif pid not in principles and written not in principles:
                errors.append(f"{rel}:{line}: {written} is not a principle in "
                              f"{os.path.basename(arch_path)}")

        for qid, written, line in cite(text, OQ_CITATION):
            counted += 1
            if questions is None:
                errors.append(f"{rel}:{line}: cites {written} and no open-questions register was "
                              f"found -- pass --questions")
            elif qid not in questions:
                errors.append(f"{rel}:{line}: {written} is not in "
                              f"{os.path.basename(q_path)}")
            elif questions[qid]:
                warnings.append(f"{rel}:{line}: {written} is already {questions[qid]}")

    # The other direction: a record naming a feature that is not there any more.
    if records:
        for rid in sorted(records, key=lambda k: int(k)):
            rec = records[rid]
            for target in rec["drives"]:
                counted += 1
                if re.match(r"^[a-z]+://|^#", target):
                    continue
                resolved = os.path.normpath(
                    os.path.join(os.path.dirname(rec["path"]), target.split("#")[0]))
                if not os.path.exists(resolved):
                    errors.append(f"{os.path.basename(rec['path'])}: **Drives:** "
                                  f"{target} does not exist")

    # Item 35's direction: a feature declaring itself architecturally significant, and no
    # record driving it. Reported, never refused -- see the docstring.
    driven = set()
    if records:
        for rec in records.values():
            for target in rec["drives"]:
                driven.add(os.path.basename(target.split("#")[0]))

    for path_ in markdown_files(prd_dir):
        rel = os.path.relpath(path_, prd_dir)
        for attrs in SIGNIFICANT.findall(read(path_)):
            counted += 1
            because = re.search(r'because="([^"]*)"', attrs)
            if not because or not because.group(1).strip():
                errors.append(f"{rel}: <architecturally-significant> names no `because`, so it "
                              f"records that something matters and not what kind of thing it is")
            elif records is None:
                warnings.append(f"{rel}: is architecturally significant and no decision "
                                f"directory was found -- pass --adr-dir")
            elif os.path.basename(path_) not in driven:
                warnings.append(f"{rel}: is architecturally significant ({because.group(1)}) "
                                f"and no decision record names it in **Drives:**")

    # Item 35's third direction: a feature nobody has flagged that the heuristics say is a
    # candidate. Reported, never applied -- significance cannot be derived, which is the whole
    # reason it is a declared flag, so this screens for a conversation and stops there.
    candidates = []
    features_dir = os.path.join(prd_dir, "features")
    if os.path.isdir(features_dir):
        docs = {os.path.relpath(p, prd_dir): read(p) for p in markdown_files(prd_dir)}
        for rel in sorted(docs):
            if not rel.replace(os.sep, "/").startswith("features/"):
                continue
            text = docs[rel]
            if SIGNIFICANT.search(text):
                continue
            slug_m = SLUG_EL.search(text)
            slug = slug_m.group(1) if slug_m else os.path.splitext(os.path.basename(rel))[0]
            reasons = []
            hit = QUALITY_WORDS.search(text)
            if hit:
                reasons.append(f"quality-attribute (names `{hit.group(1).lower()}`)")
            # index.md and what-next.md name every feature by construction, so counting them
            # would hand every feature two free edges and make the threshold meaningless.
            reach = sum(1 for other, body in docs.items()
                        if other != rel
                        and os.path.basename(other) not in ("index.md", "what-next.md")
                        and re.search(r"\b" + re.escape(slug) + r"\b", body))
            if reach >= CROSS_CUTTING_AT:
                reasons.append(f"cross-cutting (named by {reach} other documents)")
            if reasons:
                candidates.append(f"{rel}: {', '.join(reasons)} -- and it declares no "
                                  f"<architecturally-significant>")

    if not args.quiet:
        for line in errors:
            print(f"  DANGLING  {line}")
        for line in warnings:
            print(f"  STALE     {line}")
        for line in candidates:
            print(f"  CANDIDATE {line}")

    where = os.path.relpath(adr_dir, prd_dir) if adr_dir else "not found"
    print(f"{counted} references checked against {where}: "
          f"{len(errors)} dangling, {len(warnings)} stale, "
          f"{len(candidates)} significance candidates")

    if errors:
        return 1
    return 1 if (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
