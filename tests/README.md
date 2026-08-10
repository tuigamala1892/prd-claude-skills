# Regression suite

Enforces the invariants established in
[`../docs/skills/toolchain-assessment-and-plan.md`](../docs/skills/toolchain-assessment-and-plan.md).
Standard library only — no pytest, no requirements file.

```bash
python tests/test_toolchain.py              # 17 static checks, fast and offline
python tests/test_toolchain.py --behaviour  # + plugin-load check (needs `claude`, ~30s)
python tests/test_toolchain.py -v           # show detail for known failures too
```

Exit code is 0 when everything either passes or is a declared known failure; 1 when
something genuinely fails **or** when a known failure starts passing.

## Expected failures are the point

Checks that encode a target state the toolchain has not reached are marked
`expect_fail="<item>"`, naming the remediation item that will fix them. They report
as `KNOWN/<item>` and do not break the build.

When one starts passing it reports `FIXED` and **fails the run**. That is the signal
to delete the marker, at which point the check becomes a permanent regression guard.
Without that flip, a suite that is quietly red forever just teaches you to ignore it.

Current baseline: **17 pass, 2 known**.

| Known failure | Fixed by | Finding |
|---|---|---|
| Skill and its named agent declare the same model | 4.2 | F7 |
| No stale or invalid model identifiers | 4.2 | F5 |

The mechanism has been exercised repeatedly. Items 4.11, 4.8 and 4.7 each began as
`expect_fail` checks; when the fix landed they reported `FIXED` with exit code 1, the
markers were removed, and they became permanent guards. Reintroducing `allowed-tools`
to a skill, an unguarded `git pull`, a hardcoded `main`, or a command that deletes
`.git` now fails the suite.

The 4.7/4.8 round also demonstrated the suite catching something a manual sweep had
missed: after the fix looked complete by grep, the new hardcoded-branch check still
failed, pointing at four `git checkout main` lines in
`skills/execute-merge/references/merge-strategy.md`.

### Scope of the dangerous-command checks

Those checks scan only `skills/`, `agents/` and `commands/` — the files whose text
becomes instructions to a model. Prose elsewhere legitimately quotes the commands it
is warning about, and failing the build for *describing* a hazard teaches the wrong
lesson. This was not the original scoping; the first version failed on the README's
own description of the findings.

## What it does not do, deliberately

**It never invokes a real skill.** `/execute` creates worktrees and merges branches,
and the Layer 0 template still contains `rm -rf {output-dir}/.git` (finding F2) — so
a test that "runs the skill to see if it works" can destroy a repository. The risk is
not hypothetical; it is one of the findings this suite guards.

The division of labour:

- [`../docs/skills/probes/`](../docs/skills/probes/) established the frontmatter
  *rules* empirically, against throwaway skills in a scratch project. Run it when the
  Claude Code version changes, since those rules are harness behaviour rather than
  documented API.
- This suite enforces those rules *statically* against the real skills. Run it on
  every change.

Behavioural coverage here stops at "does the plugin register everything on disk",
which is read-only. That check includes a decoy name — if a name that does not exist
is reported present, the answer is an echo rather than a lookup and the check fails.

## Adding a check

```python
@check("short description", finding="F9", expect_fail="4.9")
def _():
    assert condition, "what went wrong, and why it matters"
```

`finding` and `expect_fail` are both optional. Prefer assertion messages that name
the offending files — the runner prints them verbatim, and a check that only says
`False is not True` costs more time than it saves.
