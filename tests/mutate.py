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
import time

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


def restore(keep, path, before, attempts=3, pause=0.5):
    """Put `path` back from `keep` and SAY what went wrong, never raise.

    A function rather than four lines inside the loop, because the failure path is the whole
    point and a failure path that cannot be exercised is a hope. Called from a `finally`, an
    exception raised in here escapes the finally and ends the run: no hash verification, no
    restore of the files after this one, and no report naming what is broken. The operator gets
    a traceback and a mutated tree.

    That is the worst shape this harness has. The one time it happened, the mutation left behind
    was to a constant the suite reads, so the WEAKENED CHECK went on passing -- a green suite
    over a tree nobody had put back.

    Returns None when the file is byte-identical to `before`, else a sentence saying why not.
    The retries are for Windows, where a concurrent reader -- a second suite run, an editor, a
    live `claude` session holding --add-dir on this tree -- makes copyfile raise EINVAL for as
    long as it holds the handle. Usually transient, which is why it is worth asking twice more
    before giving up, and never silent, which is why giving up is reported.
    """
    why = None
    for attempt in range(attempts):
        try:
            shutil.copyfile(keep, path)
        except OSError as e:
            why = e
            time.sleep(pause * (attempt + 1))
            continue
        return None if sha(path) == before else "restored, but the bytes differ from before"
    return f"copy failed after {attempts} attempts: {why}"


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
        aborted = False

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
                #
                # THE COPY ITSELF CAN FAIL, and until it was allowed to, that killed the run.
                # `shutil.copyfile` raises EINVAL on Windows when another process holds the
                # file -- a second suite run, an editor, a live `claude` session with
                # --add-dir on this tree. An exception raised HERE escapes the finally and
                # ends the process before the hash verification below, before the remaining
                # files are put back, and before the report that would name what is broken.
                # What the operator gets is a traceback naming no remedy, and what the tree
                # gets is a mutated file.
                #
                # That is the worst shape this harness can fail in. The mutation that was left
                # behind the one time it happened was to a constant the suite reads, so the
                # weakened check went on passing: a green suite over a tree nobody had
                # restored. So a failed restore is RECORDED rather than raised, and the run
                # stops rather than mutating further on top of a file it could not put back.
                problem = restore(keep, path, before)
                if problem:
                    restore_problems.append((rel, keep, problem))
                    aborted = True

            results.append((label, detail, ok))
            if aborted:
                print(f"\nABORTED after {label!r}: {rel} could not be restored, and mutating "
                      f"further would compound it.")
                break

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
        # One check fails in EVERY round by construction and is not an orphan: applying any
        # mutant destroys that mutant's own anchor text, so the anchor sweep is one above its
        # ceiling for the duration. Filtered here rather than tolerated in the check itself --
        # a `+1` allowance there cannot tell `broke its own anchor` from `broke somebody
        # else's`, and the second is what the check is for.
        inevitable = ("every mutant anchor resolves",)
        orphans = {c for c in seen_failures
                   if not any(e in c for e in expected)
                   and not any(i in c for i in inevitable)}
        if orphans:
            print("\nWARNING: these checks failed but matched no mutant's expectation. If one "
                  "was renamed, a MISSED above belongs to a check that actually fired:")
            for o in sorted(orphans):
                print(f"  {o}")

        if restore_problems:
            print("\nRESTORE INCOMPLETE -- the working tree is NOT as this run found it:")
            for rel, keep, why in restore_problems:
                print(f"  {rel}\n      {why}\n      recover with: copy \"{keep}\" \"{rel}\"")
            print("\nThe stash is kept for exactly this. Do not run anything else against this "
                  "tree until every line above is resolved -- a mutation left in place can be a "
                  "WEAKENED CHECK, which the suite then passes.")
            return 2

        print("every file restored byte-for-byte (verified by hash, not assumed)")
        shutil.rmtree(stash, ignore_errors=True)
        return 0 if caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
