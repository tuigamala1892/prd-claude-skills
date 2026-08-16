#!/usr/bin/env python3
"""Validate PROJECT.md's embedded <project-context> block, and optionally repair it.

`project-context-finalizer` rewrites this file after every CRD run, and on its first ever
execution it produced:

    ?tag=python&status=archived

A bare `&` is not valid XML. The block stopped parsing, which silently breaks every consumer:
`crd-impact-analysis` reads `<api-registry>` and `<schema-registry>` from it, and the finalizer
itself has to parse the file to update it next time. The run reported success.

This is the same defect the project opened with -- 94 bare ampersands escaped so the PRD
directory would parse -- reintroduced by a component whose whole job is writing XML. Telling
an agent to escape ampersands is a prose instruction; checking afterwards is not.

Usage:
    check-project-md.py <project-path>               # validate; exit 1 if malformed
    check-project-md.py <project-path> --fix         # escape bare ampersands, then validate
    check-project-md.py <project-path> --stamp-hash  # write HEAD into <last-context-hash>
    check-project-md.py <project-path> --status      # is the context stale? exit 3 if so

`--fix` only escapes `&` that does not already begin an entity. It does not attempt to repair
unbalanced tags or anything else structural -- if the block is broken in some other way, that
is a defect to look at rather than paper over.

WHY --stamp-hash EXISTS

`project-context-finalizer` was told to write `<last-context-hash>{current git HEAD}</...>`
while declaring `tools: Read Write Glob`. With no Bash it cannot run `git rev-parse`, so on the
one CRD run that has ever happened it wrote the literal string `current-HEAD`, replacing a
perfectly good hash. Every consumer then fails: `git diff current-HEAD..HEAD` is
`fatal: ambiguous argument`, and both update paths treat an invalid hash as "fall back to full
investigation" -- so every future update silently takes the most expensive route available.

Asking a component for a value it has no way to compute is the F20 shape. The agent produces
content and the caller owns git, which is the division everywhere else here; the hash is git's
business, so the caller stamps it with this.

WHAT THE HASH MEANS, AND WHY THAT REMOVES AN OFF-BY-ONE

It records **the commit whose code this context describes** -- not the commit that carries the
context. Those can never be the same one: PROJECT.md is written first and committed second, so
a hash naming its own commit is unobtainable in principle. Recording HEAD at stamp time, before
the PROJECT.md commit, is therefore exactly right rather than one short.

Staleness follows from that: the context is stale when commits since the recorded hash touched
**anything other than PROJECT.md**. The one commit that is always in between is the PROJECT.md
write itself, and a documentation commit does not make the documentation out of date. Comparing
the hash to HEAD directly -- which is what every consumer used to do -- reports "STALE"
immediately after a successful update, every single time.
"""

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

BLOCK = re.compile(r"<project-context.*?</project-context>", re.S)
BARE_AMP = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)")
HASH_EL = re.compile(r"(<last-context-hash>)(.*?)(</last-context-hash>)", re.S)
SHA = re.compile(r"^[0-9a-f]{7,40}$")


def git(project, *args):
    """Run git in the project, returning stripped stdout, or None if it failed."""
    try:
        p = subprocess.run(["git", "-C", project, *args], capture_output=True,
                           text=True, timeout=60)
    except Exception:
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def main():
    argv = [a for a in sys.argv[1:]]
    fix = "--fix" in argv
    stamp = "--stamp-hash" in argv
    status = "--status" in argv
    unknown = [a for a in argv
               if a.startswith("--") and a not in ("--fix", "--stamp-hash", "--status")]
    argv = [a for a in argv if not a.startswith("--")]
    if len(argv) != 1 or unknown:
        print("usage: check-project-md.py <project-path> [--fix] [--stamp-hash] [--status]",
              file=sys.stderr)
        return 2

    path = os.path.join(os.path.abspath(argv[0]), "PROJECT.md")
    if not os.path.isfile(path):
        # Not an error: greenfield projects have no PROJECT.md and never will.
        print(f"no PROJECT.md at {path} -- nothing to validate")
        return 0

    text = open(path, encoding="utf-8").read()
    m = BLOCK.search(text)
    if not m:
        print(f"REFUSED: {path} has no <project-context> block. Every CRD skill reads that "
              f"block; without it the file is decoration.", file=sys.stderr)
        return 1

    block = m.group(0)
    bare = BARE_AMP.findall(block)

    if fix and bare:
        repaired = BARE_AMP.sub("&amp;", block)
        try:
            ET.fromstring(repaired)
        except ET.ParseError as e:
            print(f"REFUSED: escaping ampersands did not make it parse ({e}). Something else "
                  f"is wrong; look at it rather than repairing blindly.", file=sys.stderr)
            return 1
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text[:m.start()] + repaired + text[m.end():])
        print(f"escaped {len(bare)} bare ampersand(s) in {path}")
        block = repaired

    try:
        root = ET.fromstring(block)
    except ET.ParseError as e:
        print(f"REFUSED: <project-context> in {path} is not well-formed: {e}", file=sys.stderr)
        if bare:
            print(f"  {len(bare)} bare ampersand(s) found, e.g. {bare[0]!r} -- "
                  f"re-run with --fix", file=sys.stderr)
        return 1

    sections = [c.tag for c in root]
    missing = [s for s in ("meta", "features", "api-registry", "schema-registry")
               if s not in sections]
    if missing:
        print(f"REFUSED: {path} is missing {', '.join(missing)} -- consumers read these",
              file=sys.stderr)
        return 1

    print(f"PROJECT.md valid: " + ", ".join(
        f"{c.tag} {len(list(c))}" for c in root))

    project = os.path.abspath(argv[0])

    if stamp:
        head = git(project, "rev-parse", "HEAD")
        if not head:
            print(f"REFUSED: cannot read HEAD in {project}; not a git repository?",
                  file=sys.stderr)
            return 1
        text = open(path, encoding="utf-8").read()
        if HASH_EL.search(text):
            text, n = HASH_EL.subn(lambda m: m.group(1) + head + m.group(3), text, count=1)
        elif "</meta>" in text:
            # The finalizer can drop the element entirely. Put it back rather than leaving
            # the file without the one field every update path depends on.
            text, n = text.replace(
                "</meta>",
                f"  <last-context-hash>{head}</last-context-hash>\n  </meta>", 1), 1
        else:
            print(f"REFUSED: {path} has no <meta> block to stamp the hash into",
                  file=sys.stderr)
            return 1
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"stamped last-context-hash = {head}")

    if status:
        text = open(path, encoding="utf-8").read()
        m2 = HASH_EL.search(text)
        recorded = (m2.group(2).strip() if m2 else "")
        head = git(project, "rev-parse", "HEAD")
        if not head:
            print(f"REFUSED: cannot read HEAD in {project}", file=sys.stderr)
            return 1
        if not SHA.match(recorded) or git(project, "cat-file", "-e", recorded + "^{commit}") is None:
            print(f"UNUSABLE: last-context-hash is {recorded!r}, which is not a commit in this "
                  f"repository. Re-generate with a full investigation.", file=sys.stderr)
            return 1

        changed = git(project, "diff", "--name-only", f"{recorded}..HEAD") or ""
        files = [f for f in changed.splitlines() if f.strip()]
        # PROJECT.md is excluded on purpose: it is *this* context, and the commit carrying it
        # is always one ahead of the code it describes. Counting it would report stale
        # immediately after every successful update.
        code = [f for f in files if os.path.basename(f) != "PROJECT.md"]
        print(f"hash={recorded}")
        print(f"head={head}")
        print(f"changed={len(code)}")
        print("stale=" + ("yes" if code else "no"))
        if code:
            for f in code[:10]:
                print(f"  {f}")
            if len(code) > 10:
                print(f"  ... and {len(code) - 10} more")
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
