#!/usr/bin/env python3
"""Mutation harness: break one thing, run the suite, confirm the NAMED check fails, restore.

**A check that has never been seen failing is a hypothesis.** Phase 3 wrote ten regression
checks and the suite was green after every one of them; mutation then showed that **five did no
work at all**. That is what this exists for, and it is why the standard for this repository is
that no check is finished until it has been watched failing for the reason it exists.

USAGE

    python tests/mutate.py <mutants.py> [--suite tests/test_toolchain.py]

`<mutants.py>` is a Python file defining `MUTANTS`, a list of 5-tuples:

    MUTANTS = [
        ("a short label for the report",     # what this mutant does, in the report
         "skills/breakdown/SKILL.md",        # repo-relative path to break
         "the exact text to find",           # must match exactly, once
         "what to replace it with",
         "substring of the check name that MUST fail"),
    ]

Exit 0 when every mutant was caught, 1 when any survived, 2 when a file could not be restored.

FOUR GUARDS, EACH BECAUSE THE HARNESS ONCE LIED

Every one of these produced a confident wrong number during Phase 3, and each reads exactly like
a healthy result:

1. **The baseline must be green before mutating.** A check that was already failing "catches"
   every mutant trivially. One run reported 13/13 that was entirely hollow because an unrelated
   variable-scope slip had left a check red.

2. **A failing check that no mutant expected is reported as an orphan.** Renaming a check while
   its mutants still name the old one makes the harness report MISSED for a check that actually
   fired -- one round read as 6/13 when it was really 11/13.

3. **Restore is verified by hash, never assumed** -- and never with `git checkout`. The files
   under test are usually uncommitted, so `git checkout -- <file>` reverts to HEAD and discards
   the real work along with the mutation. That cost an afternoon in item 54 and two regression
   checks on 2026-08-27. Copy aside, copy back, compare digests. See `tests/dirty-guard.sh`.

4. **Sleep is inhibited for the duration.** A round launched in the evening was suspended
   overnight; a suspended process gets no chance to act on a wall-clock deadline, so the run
   neither finished nor failed until someone moved the mouse.

AND ONE RULE THIS CANNOT ENFORCE FOR YOU

**Do not run the suite yourself while this is running.** It mutates the working tree, so a
concurrent verification run measures a repository someone else is actively breaking. That
produced two phantom failures on correct code.
"""

import argparse
import hashlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keep_awake import keep_awake  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(path):
    with io.open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_mutants(path):
    spec = importlib.util.spec_from_file_location("mutants", os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mutants = getattr(mod, "MUTANTS", None)
    if not mutants:
        raise SystemExit(f"{path} defines no MUTANTS list")
    for i, m in enumerate(mutants):
        if len(m) != 5:
            raise SystemExit(f"MUTANTS[{i}] has {len(m)} fields, expected 5")
    return mutants


def run_suite(suite):
    p = subprocess.run([sys.executable, suite], cwd=REPO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.stdout + p.stderr


def failing_checks(output):
    return {m.group(1).strip() for m in re.finditer(r"^  FAIL\s+(.*?)\s{2,}", output, re.M)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mutants", help="a .py file defining MUTANTS")
    ap.add_argument("--suite", default=os.path.join("tests", "test_toolchain.py"))
    args = ap.parse_args()

    mutants = load_mutants(args.mutants)

    with keep_awake():
        # GUARD 1 -- an already-red suite makes every mutant look caught.
        baseline = failing_checks(run_suite(args.suite))
        if baseline:
            print("REFUSED: the suite is not green before mutating. These checks already fail, "
                  "so every mutant would appear caught:")
            for f in sorted(baseline):
                print(f"  {f}")
            return 2
        print(f"baseline green: 0 failing checks before mutation ({len(mutants)} mutants)")

        stash = tempfile.mkdtemp(prefix="mutate-")
        results, restore_problems, seen_failures = [], [], set()

        for label, rel, find, replace, must_fail in mutants:
            path = os.path.join(REPO, rel)
            if not os.path.isfile(path):
                results.append((label, f"NO SUCH FILE: {rel}", False))
                continue
            before = sha(path)
            keep = os.path.join(stash, rel.replace("/", "__").replace(os.sep, "__"))
            shutil.copyfile(path, keep)

            text = io.open(path, encoding="utf-8").read()
            if find not in text:
                # Not a survivor: the mutant never applied, which is a defect in the mutant
                # rather than evidence about the check. Reported as its own outcome.
                results.append((label, "ANCHOR NOT FOUND -- mutant never applied", False))
                continue
            io.open(path, "w", encoding="utf-8", newline="").write(
                text.replace(find, replace, 1))

            try:
                failed = failing_checks(run_suite(args.suite))
                seen_failures |= failed
                hit = [f for f in failed if must_fail in f]
                ok = bool(hit)
                detail = (f"caught by: {hit[0]}" if ok
                          else f"NOT CAUGHT. suite reported: {sorted(failed) or 'nothing'}")
            finally:
                # GUARD 3 -- restore from the copy and PROVE it.
                shutil.copyfile(keep, path)
                if sha(path) != before:
                    restore_problems.append(rel)

            results.append((label, detail, ok))

        print()
        print("=" * 100)
        width = max((len(r[0]) for r in results), default=10) + 2
        for label, detail, ok in results:
            print(f"  {'CAUGHT ' if ok else 'MISSED '}  {label:<{width}} {detail}")
        print("=" * 100)

        caught = sum(1 for r in results if r[2])
        print(f"\n{caught}/{len(results)} mutants caught")

        # GUARD 2 -- a check that fired but matched no expectation is almost always a rename,
        # and it makes a working check report as a missed one.
        expected = {m[4] for m in mutants}
        orphans = {c for c in seen_failures if not any(e in c for e in expected)}
        if orphans:
            print("\nWARNING: these checks failed but matched no mutant's expectation. If one "
                  "was renamed, a MISSED above belongs to a check that actually fired:")
            for o in sorted(orphans):
                print(f"  {o}")

        if restore_problems:
            print("\nRESTORE INCOMPLETE -- these do not match their pre-mutation bytes:")
            for r in restore_problems:
                print(f"  {r}")
            print("Recover them from the stash before doing anything else:")
            print(f"  {stash}")
            return 2

        print("every file restored byte-for-byte (verified by hash, not assumed)")
        shutil.rmtree(stash, ignore_errors=True)
        return 0 if caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
