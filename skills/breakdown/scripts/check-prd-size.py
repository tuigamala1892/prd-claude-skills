#!/usr/bin/env python3
"""Refuse a PRD that will not fit the prompt it is about to be sent in (item 18, P5).

`breakdown/SKILL.md` Phase 2 said: *"Invoke the `breakdown-analyze-prd` skill with the full PRD
content."* For the sample corpus that is ~174k tokens in one prompt, to a skill declaring
`model: claude-haiku-4-5` and a 200k window. It nominally fits and cannot work: ~35k left for a
structured extraction of 64 features, against an explicit instruction not to truncate or
summarise them. There was no chunking, no per-feature pass, and **no size check** -- so the
failure mode was a silently truncated analysis, which is the worst available one. Everything
downstream is built from that file.

Item 18 splits the analysis into an index pass and one pass per feature. This script is the
guard that makes the split honest: it measures what each prompt would carry and refuses before
anything is sent, rather than discovering the problem in a truncated `analysis.json`.

WHAT IT MEASURES

  index.md            the index pass -- tech stack, feature list, priorities
  features/*.md       one per-feature pass each
  the whole corpus    what the pre-item-18 design would have sent as a single prompt,
                      reported for contrast and never as a target

TOKENS ARE ESTIMATED, AND THE DIVISOR IS THIS REPOSITORY'S OWN MEASUREMENT

No tokeniser ships with the toolchain, so tokens are estimated from characters. The divisor is
3.6, taken from the corpus figures the plan already records -- ~628 KB against ~174k tokens --
rather than from a generic rule of thumb. It is an estimate and is labelled as one everywhere it
is printed. `--chars-per-token` overrides it.

An estimate is the right instrument here because the decision it feeds is a wide one: a feature
file at 8k or 11k tokens is fine either way, and one at 90k is a refusal either way.

USAGE

    check-prd-size.py <prd-dir> [--budget 60000] [--chars-per-token 3.6] [--quiet]

  exit 0  every prompt fits its budget
  exit 1  REFUSED -- at least one prompt would exceed it, named with its size
  exit 2  usage error, or no PRD found
"""

import argparse
import os
import sys

DEFAULT_BUDGET = 60_000
DEFAULT_CHARS_PER_TOKEN = 3.6


def tokens(path, cpt):
    with open(path, encoding="utf-8", errors="replace") as f:
        return int(len(f.read()) / cpt)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prd_dir")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                    help=f"per-prompt ceiling in estimated tokens (default {DEFAULT_BUDGET})")
    ap.add_argument("--chars-per-token", type=float, default=DEFAULT_CHARS_PER_TOKEN)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    prd_dir = os.path.abspath(args.prd_dir)
    index = os.path.join(prd_dir, "index.md")
    if not os.path.isfile(index):
        print(f"REFUSED: no index.md in {prd_dir}", file=sys.stderr)
        return 2

    cpt = args.chars_per_token
    features_dir = os.path.join(prd_dir, "features")
    features = []
    if os.path.isdir(features_dir):
        features = [os.path.join(features_dir, n) for n in sorted(os.listdir(features_dir))
                    if n.lower().endswith(".md")]

    prompts = [("index.md", tokens(index, cpt))]
    for path in features:
        prompts.append((os.path.join("features", os.path.basename(path)), tokens(path, cpt)))

    over = [(name, n) for name, n in prompts if n > args.budget]
    total = sum(n for _name, n in prompts)
    largest = max(prompts, key=lambda p: p[1])

    if not args.quiet:
        print(f"{len(prompts)} prompt(s): 1 index pass + {len(features)} feature pass(es)")
        print(f"  budget per prompt   {args.budget:>8,} tokens (estimated at "
              f"{cpt} chars/token)")
        print(f"  largest prompt      {largest[1]:>8,}  {largest[0]}")
        print(f"  index pass          {prompts[0][1]:>8,}")
        if features:
            per = [n for _n, n in prompts[1:]]
            print(f"  feature passes      {min(per):>8,} min, {max(per):,} max, "
                  f"{sum(per) // len(per):,} mean")
        print(f"  whole corpus        {total:>8,}  <- what one prompt would have carried "
              f"before item 18")

    if over:
        print(f"REFUSED: {len(over)} prompt(s) exceed the {args.budget:,}-token budget:",
              file=sys.stderr)
        for name, n in over:
            print(f"  {name}: {n:,} tokens", file=sys.stderr)
        print("", file=sys.stderr)
        print("Split the feature, or raise --budget deliberately. Do not send it anyway: "
              "there is no truncation that leaves the analysis correct, and everything "
              "downstream is built from it.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
