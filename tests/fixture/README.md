# §5.1 test fixture — Link Shelf

The minimal PRD called for by §5.1 of
[`../../docs/skills/toolchain-assessment-and-plan.md`](../../docs/skills/toolchain-assessment-and-plan.md):
small enough to iterate on, complete enough to exercise layer planning, the merge
queue, and the behaviours the three blocking fixes changed.

```bash
python tests/fixture/setup_fixture.py           # build the workspace
python tests/fixture/setup_fixture.py --clean   # rebuild from scratch
python tests/fixture/setup_fixture.py --verify  # check invariants after a run
```

The workspace is built **outside this repository** and the script refuses to build
inside it. `/execute` creates branches, merges and removes worktrees in its target;
pointing that at the toolchain would be finding F4 at its worst.

## What the fixture is

`Link Shelf` — save a URL, list saved URLs, tag them. Three features, two models,
three endpoints, no frontend and no auth.

| Choice | Why |
|---|---|
| SQLite, not PostgreSQL | A fixture that needs a database server fails for reasons unrelated to what is being tested |
| No template path | Layer 0 creates directories instead of copying a tree, so the fixture does not depend on a template existing |
| Target repo pre-created, **no remote** | `/execute`'s preflight requires an existing repository; no remote is exactly the configuration F1 could not survive, so the fixture reproduces it rather than avoiding it |
| Tags as a join table, not a string column | The one deliberate piece of real modelling. A single-table shortcut would make the data-model layer trivial and stop the fixture exercising the part of layer planning most likely to break |
| One `should-have` among two `must-have` | Forces layer planning to place a lower-priority item rather than treating every feature identically |
| Ordering has its own acceptance criterion | A test that only counted rows would pass against insertion-order output and break later |

Scope is capped on purpose. If this fixture starts growing, add a second one rather
than extending it.

## What `--verify` proves

It compares against a baseline recorded at build time, which makes **F2 falsifiable**
rather than merely hoped for:

- **The target repository is still the same repository.** Not just "`.git` exists" —
  it checks the recorded root commit is still reachable, so reinitialising the repo is
  caught as well as deleting it.
- **No remote was needed.** If one appears, that is reported: the fixture would no
  longer be testing the no-remote path.
- **What actually happened** — tasks generated, commits added, and any worktree still
  attached, which after a clean run means a task was abandoned.

The negative case is tested: deleting `app/.git` makes `--verify` exit 1 with a clear
failure, so a silent pass means the invariant genuinely held.

## The §5.2 sequence

`setup_fixture.py` prints these with real paths.

| # | Test | Passes when |
|---|---|---|
| 2 | `/prd` on a fresh directory | PRD written; `what-next.md` valid XML with `<status>` |
| 3 | `/prd` again, no arguments | Existing PRD detected and offered; nothing overwritten |
| 4 | `/prd --resume` | Finds the PRD via `what-next.md` |
| 5 | `/breakdown` with a relative `--output-dir` | Rejected with a clear error |
| 6 | `/breakdown` with an absolute `--output-dir` | Tasks land there; nothing written into the toolchain tree |
| 7 | `/execute` against a repo with **no remote** | Runs; no `git pull` failure |
| 8 | `/execute` against a path containing `docs/prd/` | Refused |
| 9 | Full `/execute` run | Tasks implement, verify and merge; no `.git` deleted anywhere |

Tests 5, 6 and 9 depend on items 4.6 and 4.9, which are not done — expect those to
fail. Tests 7, 8 and the `.git` half of 9 cover the three blocking fixes and should
pass.

**The thing most worth watching is test 9.** Item 4.11 made skills fork for the first
time, and a forked skill returns a summary to its caller rather than mutating the
caller's context. `execute-batch` and `execute-layer` orchestrate other skills and are
the most likely to behave differently now. That change has never been exercised — this
fixture is where it will first show up.
