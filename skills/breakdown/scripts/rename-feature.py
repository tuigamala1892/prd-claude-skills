#!/usr/bin/env python3
"""Rename a feature slug across a PRD, and prove the rename finished (plan item 42, P27).

The rename that prompted this was done correctly, by hand, across 20 references in 8 files --
and produced no evidence of that fact. That is the actual defect. A refactor that is right by
care and unverifiable by construction is one distraction away from being wrong and silent.

So the edits are the easy half. The postconditions are the point, and they are asserted after
the writes rather than assumed by them:

  1. no reference anywhere resolves to the old slug
  2. no file exists under the old slug
  3. the new slug appears in exactly one index entry and one feature file

Assert those three and a residue becomes impossible rather than merely unlikely.

WHAT IS REWRITTEN

  features/<old>.md            the file itself
  <slug>old</slug>             in that file's <meta>
  file="features/<old>.md"     the index entry
  ref="features/<old>.md"      what-next.md entries
  ](features/<old>.md)         inbound markdown links in every other file
  ](<old>.md)                  the same link written relative to features/

WHAT IS ONLY REPORTED

Bare prose mentions of the old slug -- "as decided for save-link" -- are printed with file and
line and are NOT rewritten. They are not references, they do not resolve, and a script editing
English is a worse failure than a stale sentence. They are shown because a rename that leaves
them is half-done in a way the operator should choose to accept.

WHAT THIS IS NOT

A rename is **not** a supersession. `<status>superseded</status>` is for a feature merged into
another, and using it here would claim two features existed where there was always one. This
script never touches a status.

A rename IS a decision, and where it accompanies a change of scope it wants a decision record
(item 36) rather than a silent file move. The summary line printed at the end is written to be
pasted into one.

USAGE

    rename-feature.py <prd-dir> <old-slug> <new-slug> [--dry-run] [--quiet]

EXIT CODES

  0  renamed, and all three postconditions hold
  1  refused before writing, or a postcondition failed after writing
  2  usage error
"""

import argparse
import os
import re
import sys

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def markdown_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                yield os.path.join(dirpath, name)


def reference_patterns(old, new):
    """(compiled pattern, replacement) for every shape a reference takes.

    Deliberately narrow. Each one matches a slug in a position where it *resolves* to
    something -- a path, an attribute, an element -- and never a slug sitting in a sentence.
    """
    o, n = re.escape(old), new
    return [
        (re.compile(r"features/%s\.md" % o), "features/%s.md" % n),
        (re.compile(r"<slug>\s*%s\s*</slug>" % o), "<slug>%s</slug>" % n),
        (re.compile(r"\]\(\s*%s\.md\s*\)" % o), "](%s.md)" % n),
        (re.compile(r'"\s*%s\.md\s*"' % o), '"%s.md"' % n),
    ]


def prose_mentions(root, slug, skip=()):
    """Whole-word occurrences left over after the references are gone."""
    word = re.compile(r"(?<![\w/-])%s(?![\w-])" % re.escape(slug))
    out = []
    for path in markdown_files(root):
        if path in skip:
            continue
        for i, line in enumerate(read(path).splitlines(), 1):
            if word.search(line):
                out.append((os.path.relpath(path, root), i, line.strip()[:90]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir")
    ap.add_argument("old_slug")
    ap.add_argument("new_slug")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    prd_dir = os.path.abspath(args.prd_dir)
    old, new = args.old_slug, args.new_slug

    # ---- refuse before writing anything -------------------------------------------------
    if not os.path.isdir(prd_dir):
        print(f"REFUSED: no such PRD directory: {prd_dir}", file=sys.stderr)
        return 2
    if not SLUG.match(new):
        print(f"REFUSED: {new!r} is not a slug (lowercase, digits, single hyphens)",
              file=sys.stderr)
        return 1
    if old == new:
        print("REFUSED: the old and new slugs are the same", file=sys.stderr)
        return 1

    old_file = os.path.join(prd_dir, "features", f"{old}.md")
    new_file = os.path.join(prd_dir, "features", f"{new}.md")
    if not os.path.isfile(old_file):
        print(f"REFUSED: no feature file at features/{old}.md", file=sys.stderr)
        return 1
    if os.path.exists(new_file):
        print(f"REFUSED: features/{new}.md already exists -- a rename must not merge two "
              f"features. That is a supersession, and it is a different operation.",
              file=sys.stderr)
        return 1

    patterns = reference_patterns(old, new)
    planned = []
    for path in markdown_files(prd_dir):
        text = read(path)
        hits = sum(len(p.findall(text)) for p, _ in patterns)
        if hits:
            planned.append((path, hits))

    total = sum(h for _, h in planned)
    if args.dry_run:
        for path, hits in planned:
            print(f"  would rewrite {hits:>3}  {os.path.relpath(path, prd_dir)}")
        print(f"{total} reference(s) in {len(planned)} file(s); "
              f"features/{old}.md -> features/{new}.md")
        return 0

    # ---- write, keeping enough to undo it ------------------------------------------------
    #
    # The first version of this script asserted the postconditions and reported the failure,
    # having already renamed the file and rewritten four others. That is a half-done rename
    # plus a message -- worse than not starting, because the operator now has to work out how
    # far it got. Item 41 requires per-file atomicity across 64 files; learning it here, on
    # 8, is the entire reason this item is a rehearsal.
    original = {path: read(path) for path, _ in planned}

    for path, _ in planned:
        text = original[path]
        for pattern, replacement in patterns:
            text = pattern.sub(replacement, text)
        write(path, text)

    os.rename(old_file, new_file)
    # The rewrite pass ran before the move, so a reference inside the file itself is already
    # correct; re-read from its new name for the assertions below.

    # ---- postconditions, asserted rather than assumed -----------------------------------
    failures = []

    left = []
    for path in markdown_files(prd_dir):
        text = read(path)
        for pattern, _ in patterns:
            if pattern.search(text):
                left.append(os.path.relpath(path, prd_dir))
                break
    if left:
        failures.append(f"references to {old} still resolve in: {', '.join(sorted(set(left)))}")

    if os.path.exists(old_file):
        failures.append(f"features/{old}.md still exists")

    index = os.path.join(prd_dir, "index.md")
    if os.path.isfile(index):
        entries = len(re.findall(r'file="features/%s\.md"' % re.escape(new), read(index)))
        if entries != 1:
            failures.append(f"the new slug appears in {entries} index entries, expected 1")
    files = [p for p in markdown_files(prd_dir)
             if re.search(r"<slug>\s*%s\s*</slug>" % re.escape(new), read(p))]
    if len(files) != 1:
        failures.append(f"<slug>{new}</slug> appears in {len(files)} files, expected 1")

    residue = prose_mentions(prd_dir, old)

    if not args.quiet:
        for rel, line, text in residue:
            print(f"  MENTION   {rel}:{line}: {text}")

    if failures:
        for f in failures:
            print(f"  POSTCONDITION FAILED  {f}", file=sys.stderr)

        # Undo, then say so. A failed rename must leave the PRD as it was found: the operator
        # is being told the operation did not happen, and that has to be true.
        if os.path.exists(new_file) and not os.path.exists(old_file):
            os.rename(new_file, old_file)
        for path, text in original.items():
            write(path, text)

        undone = (os.path.isfile(old_file) and not os.path.exists(new_file)
                  and all(read(p) == t for p, t in original.items()))
        if undone:
            print(f"REFUSED: the rename did not finish. {len(failures)} postcondition(s) "
                  f"failed and every change was rolled back; the PRD is as you left it.",
                  file=sys.stderr)
            return 1

        # The rollback is itself asserted, because an unverified undo is the same class of
        # claim as the unverified rename this script exists to replace.
        print("ROLLBACK INCOMPLETE -- the PRD is in a mixed state. Files that should be "
              f"restored: features/{old}.md and {len(original)} rewritten file(s).",
              file=sys.stderr)
        return 1

    print(f"renamed {old} -> {new}: {total} reference(s) in {len(planned)} file(s), "
          f"3/3 postconditions hold, {len(residue)} prose mention(s) left for you")
    if residue:
        print(f"  ({len(residue)} mention(s) above are prose, not references. Nothing resolves "
              f"to {old} any more.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
