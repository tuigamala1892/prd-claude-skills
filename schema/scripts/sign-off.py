#!/usr/bin/env python3
"""Sign off a migrated artefact's classified criteria: remove `derived-from` where a `pattern` is.

Core section 2 gives a migrated criterion three states, each visible in its attributes:

    derived-from, no pattern     the migration's sentence, unread
    derived-from and pattern     classified by a person, not yet signed off
    pattern, no derived-from     signed off

`derived-from` outlives the pattern on purpose. It is how a reviewer checks the sentence against
where it came from, so it has to still be there when they look. Signing off is the moment that
check has happened, and it is ONE implementation, here, whichever path calls it:

  - a PRD feature is signed off by recording its review. `check-definition.py --record-review`
    imports `sign_off` from this file and applies it before it hashes;
  - a CRD has no <review>, so `/crd --resume` runs this script at the end of its review.

A criterion with no `pattern` keeps `derived-from` either way. Nobody has classified that
sentence, and removing the marker would hide that a migration wrote it.

USAGE

    sign-off.py <crd.md> [--dry-run]

REFUSED, exit 2, and nothing written:

  - a PRD feature file. Its sign-off is its review, and a second route to the same edit is a
    second implementation of when it happens;
  - a CRD still holding <requirements>. It has not been migrated, so it has no criteria to sign;
  - a CRD whose <workflow> is `complete` or `abandoned`. It is a record of something that already
    happened, and migration.md keeps its `derived-from` permanently.

EXIT CODES

  0  signed off, or nothing to sign off
  2  refused, or usage error
"""

import argparse
import io
import re
import sys

CRITERION_TAG = re.compile(r"<criterion\b([^>]*)>")
PAST = {"complete", "abandoned"}


def sign_off(text):
    """Return (text, signed, unclassified): the text with `derived-from` removed from every
    criterion that carries a `pattern`, how many were signed off, and the ids left unclassified."""
    signed, unclassified = [0], []

    def one(m):
        attrs = m.group(1)
        if not re.search(r'\bpattern="', attrs):
            if re.search(r'\bderived-from="', attrs):
                cid = re.search(r'\bid="([^"]*)"', attrs)
                unclassified.append(cid.group(1) if cid else "?")
            return m.group(0)
        without = re.sub(r'\s+derived-from="[^"]*"', "", attrs)
        if without != attrs:
            signed[0] += 1
        return "<criterion%s>" % without

    return CRITERION_TAG.sub(one, text), signed[0], unclassified


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", help="a CRD file")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    try:
        with io.open(args.path, encoding="utf-8", newline="") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"REFUSED  cannot read {args.path}: {e}", file=sys.stderr)
        return 2

    if re.search(r"^\s*<feature>", text, re.M):
        print(f"REFUSED  {args.path} is a PRD feature. Its sign-off is its review: "
              f"check-definition.py PRD_DIR --record-review --by NAME --feature SLUG",
              file=sys.stderr)
        return 2
    if not re.search(r"^\s*<crd>", text, re.M):
        print(f"REFUSED  {args.path} is not a CRD -- no <crd> root element", file=sys.stderr)
        return 2
    if "<requirements>" in text:
        print(f"REFUSED  {args.path} still holds <requirements>, so it has not been migrated and "
              f"has no criteria to sign off. Run migrate.py first", file=sys.stderr)
        return 2
    meta = re.search(r"<meta>(.*?)</meta>", text, re.S)
    state = re.search(r"<(workflow|status)>\s*([a-z-]+)\s*</\1>", meta.group(1) if meta else "")
    if state and state.group(2) in PAST:
        print(f"REFUSED  {args.path} is `{state.group(2)}`, a record of something that already "
              f"happened. Its derived-from stays, permanently, per migration.md", file=sys.stderr)
        return 2

    out, signed, unclassified = sign_off(text)
    if signed and not args.dry_run:
        with io.open(args.path, "w", encoding="utf-8", newline="") as f:
            f.write(out)
    verb = "would sign off" if args.dry_run else "signed off"
    print(f"{verb} {signed} criteria in {args.path}")
    if unclassified:
        print(f"  unclassified, derived-from kept: {', '.join(unclassified)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
