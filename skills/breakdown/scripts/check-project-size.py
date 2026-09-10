#!/usr/bin/env python3
"""Refuse a PROJECT.md that will not fit the prompt it is about to be sent in (item 86, P69).

`check-prd-size.py` is the same assertion about the other path's document, and its `Paths` cell
in [`checks.md`](../../../schema/checks.md) is `prd-only` on a decided basis: a PRD is a corpus
fanned into one prompt per feature, and a CRD is one authored document read whole. Filling in
that column at item 79 asked what the unbounded input on the CRD path actually is, and the
answer was not the CRD.

It is `PROJECT.md`. A CRD is written by a person in an interview and is as long as a person
writes. `PROJECT.md` is GENERATED FROM A CODEBASE -- one `<feature>` per feature, one entry per
registry item, plus a markdown half carrying the component tree -- so it scales with the code
and not with an author. `project-format.md` sets no ceiling and `crd-investigator`'s checklist
sets only a floor (*at least 5 features cataloged*).

WHY THIS IS REACHABLE, WHICH HAD TO BE ESTABLISHED BEFORE IT WAS BUILT

  (a) `crd-investigate/SKILL.md`'s own Error Handling table already carries the row
      `Very large codebase | Limit scope, note truncation`. The situation is anticipated IN THE
      PRODUCER, and the whole mitigation is a prose instruction to a model to truncate and
      mention it, with nothing measuring whether it did.
  (b) `project-context-finalizer` is additive and runs after EVERY `/execute`: one `<feature>`
      per implemented feature, one `<endpoint>` per api export, one `<model>` per schema export,
      existing entries preserved. Nothing ever compacts it. The file therefore grows with the
      number of runs a project has had, bounded by no author and by no single generation's
      output limit.
  (c) Measured 2026-09-10 on the live sixth-crossing artefact: 13,803 chars for a 7-feature,
      7-endpoint, 4-model project. 5,567 of those -- 40% -- are the MARKDOWN half, the component
      tree and pattern list, which grow with files rather than with features.

WHAT IT MEASURES, AND WHY THE WHOLE FILE

Every consumer reads the file, not the block: `/crd`, `/crd-context`, `skills/crd` and
`/breakdown` each load `PROJECT.md` into a prompt whole. So the whole file is the number that
matters, and the decomposition below is reported so that an author over the budget can see
which term grew rather than being told only that it did.

  the markdown half   overview, tech stack, component tree, key patterns
  <features>          one per feature
  <*-registry>        one per endpoint, model, event, command, service or screen

TOKENS ARE ESTIMATED, AND THE DIVISOR IS NOT DEFINED HERE

3.6 chars per token is this repository's own corpus measurement, and it already has an owner:
`check-prd-size.py`. This imports it rather than restating it. Three definitions of `<criterion>`
came to exist and disagree exactly because a value was copied to where it was needed; the budget
comes from the same place for the same reason.

The budget is inherited too, and it is conservative here on purpose: `PROJECT.md` is never the
whole prompt it travels in -- the CRD, the skill's own instructions and the tool results sit
beside it -- so a file at the ceiling is already past comfortable.

USAGE

    check-project-size.py <project-path> [--budget N] [--chars-per-token F] [--quiet]

  exit 0  it fits, or there is no PROJECT.md (greenfield has none and never will)
  exit 1  REFUSED -- it exceeds the budget, named with its size
  exit 2  usage error
"""

import argparse
import importlib.util
import os
import re
import sys
import xml.etree.ElementTree as ET

_HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = re.compile(r"<project-context.*?</project-context>", re.S)


def _sibling():
    """`check-prd-size.py` as a module. The divisor and the budget have one definition."""
    path = os.path.join(_HERE, "check-prd-size.py")
    spec = importlib.util.spec_from_file_location("check_prd_size", path)
    if spec is None or not os.path.isfile(path):
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parts(text):
    """(label, count, chars) for the markdown half and each child of the block.

    `count` is None where the section is not a list of anything -- the markdown half and
    `<meta>`. Everything else reports the number of entries, because the entry is the unit
    this file grows in.
    """
    out = []
    m = BLOCK.search(text)
    if not m:
        out.append(("the markdown half", None, len(text)))
        return out

    out.append(("the markdown half", None, len(text) - (m.end() - m.start())))
    try:
        root = ET.fromstring(m.group(0))
    except ET.ParseError:
        # Well-formedness is `check-project-md.py`'s assertion, not this one. Report the block
        # whole rather than refusing on a question another script owns.
        out.append(("<project-context>", None, m.end() - m.start()))
        return out

    for child in root:
        n = len(list(child))
        out.append((f"<{child.tag}>", n if n else None,
                    len(ET.tostring(child, encoding="unicode"))))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project_path")
    ap.add_argument("--budget", type=int, default=None,
                    help="per-prompt ceiling in estimated tokens "
                         "(default: check-prd-size.py's)")
    ap.add_argument("--chars-per-token", type=float, default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    sib = _sibling()
    if sib is None:
        print("REFUSED: check-prd-size.py is not beside this script, and the divisor and "
              "budget are defined there rather than here.", file=sys.stderr)
        return 2

    budget = args.budget if args.budget is not None else sib.DEFAULT_BUDGET
    cpt = (args.chars_per_token if args.chars_per_token is not None
           else sib.DEFAULT_CHARS_PER_TOKEN)
    if budget <= 0 or cpt <= 0:
        print("REFUSED: --budget and --chars-per-token must both be positive.", file=sys.stderr)
        return 2

    path = os.path.join(os.path.abspath(args.project_path), "PROJECT.md")
    if not os.path.isfile(path):
        # Not an error, and the same judgement `check-project-md.py` makes: a greenfield project
        # has no PROJECT.md and never will. It prints no measurement, so a run that measured
        # nothing cannot be read as a run that measured and was content.
        print(f"no PROJECT.md at {path} -- nothing to measure")
        return 0

    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    total = int(len(text) / cpt)
    sections = parts(text)
    entries = sum(n for _label, n, _chars in sections if n)

    if not args.quiet:
        print(f"{path}")
        print(f"  budget              {budget:>8,} tokens (estimated at {cpt} chars/token)")
        print(f"  this file           {total:>8,}  {len(text):,} chars, "
              f"{len(text.splitlines()):,} lines")
        for label, n, chars in sections:
            count = f"{n:,} entries" if n else ""
            print(f"    {label:<18}{int(chars / cpt):>8,}  {count}")
        if entries:
            print(f"  per entry           {int(len(text) / entries / cpt):>8,}  <- what one "
                  f"more feature or registry item costs")
        headroom = budget - total
        print(f"  headroom            {headroom:>8,}"
              + (f"  <- about {int(headroom / (len(text) / entries / cpt)):,} more entries"
                 if entries and headroom > 0 else ""))

    if total > budget:
        print(f"REFUSED: PROJECT.md is {total:,} estimated tokens against a {budget:,}-token "
              f"budget.", file=sys.stderr)
        for label, n, chars in sections:
            if int(chars / cpt) > budget // 4:
                print(f"  {label}: {int(chars / cpt):,} tokens"
                      + (f" over {n:,} entries" if n else ""), file=sys.stderr)
        print("", file=sys.stderr)
        print("This file is read whole by /crd, /crd-context and /breakdown, and nothing "
              "downstream can tell a complete read from a truncated one. Narrow what the "
              "investigation catalogues, split the project, or raise --budget deliberately.",
              file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
