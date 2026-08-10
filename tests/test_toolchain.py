"""Regression suite for the prd-claude-skills toolchain.

Runs with the standard library alone -- no pytest, no requirements file -- so it
works in CI unchanged. Execute it directly:

    python tests/test_toolchain.py              # static checks (fast, offline)
    python tests/test_toolchain.py --behaviour  # + plugin-load check (needs `claude`)

WHAT THIS DOES NOT DO, DELIBERATELY

It never invokes a real skill. `/execute` creates worktrees and merges branches,
and the Layer 0 template still contains an `rm -rf ...git` (finding F2), so a test
that "just runs the skill to see if it works" can destroy a repository. The probe
harness in docs/skills/probes/ established the frontmatter *rules* empirically
against throwaway skills; this suite enforces those rules statically against the
real ones. Behavioural coverage here stops at "does the plugin load", which is
read-only.

EXPECTED FAILURES

Checks that encode a target state the toolchain has not reached yet are marked
`expect_fail` with the remediation item that will fix them. They report as KNOWN
and do not fail the run. When one starts passing it reports as FIXED and fails the
run instead -- that is the signal to delete the marker, turning it into a
permanent regression guard. A suite that is quietly red forever teaches you to
ignore it.
"""

import argparse
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(REPO, "skills")
AGENTS = os.path.join(REPO, "agents")
COMMANDS = os.path.join(REPO, "commands")

# Identifiers that are current as of this suite being written. `inherit` and the
# bare tier aliases track the latest model and never need migrating.
VALID_MODELS = {
    "claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
    "opus", "sonnet", "haiku", "inherit",
}
STALE_MODELS = {"claude-sonnet-4-6", "claude-sonnet-4-5", "claude-opus-4-1",
                "claude-haiku-5", "claude-3-5-sonnet", "claude-sonnet-4"}

_RESULTS = []


def check(name, finding=None, expect_fail=None):
    """Register a check. `expect_fail` names the remediation item that will fix it."""
    def deco(fn):
        _RESULTS.append({"name": name, "finding": finding,
                         "expect_fail": expect_fail, "fn": fn})
        return fn
    return deco


# --------------------------------------------------------------------- helpers

def parse_frontmatter(path):
    """Return (frontmatter dict, body). Empty dict when there is no `---` block."""
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    try:
        import yaml
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items()}, body
    except Exception:
        pass
    # Fallback: the frontmatter in this repo is flat `key: value`.
    data = {}
    for line in raw.splitlines():
        m2 = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m2:
            data[m2.group(1)] = m2.group(2).strip()
    return data, body


def skill_files():
    if not os.path.isdir(SKILLS):
        return []
    out = []
    for d in sorted(os.listdir(SKILLS)):
        p = os.path.join(SKILLS, d, "SKILL.md")
        if os.path.isfile(p):
            out.append((d, p))
    return out


def agent_files():
    if not os.path.isdir(AGENTS):
        return []
    return [(os.path.splitext(f)[0], os.path.join(AGENTS, f))
            for f in sorted(os.listdir(AGENTS)) if f.endswith(".md")]


def command_files():
    if not os.path.isdir(COMMANDS):
        return []
    return [(os.path.splitext(f)[0], os.path.join(COMMANDS, f))
            for f in sorted(os.listdir(COMMANDS)) if f.endswith(".md")]


def all_tracked_text():
    """Every tracked .md/.json path plus its text, for content-level checks."""
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                             text=True, timeout=30).stdout.split("\n")
    except Exception:
        out = []
    for rel in out:
        if not rel.strip() or not rel.endswith((".md", ".json")):
            continue
        p = os.path.join(REPO, rel.replace("/", os.sep))
        if os.path.isfile(p):
            yield rel, open(p, encoding="utf-8", errors="replace").read()


def instruction_text():
    """Only the files whose text becomes instructions to a model.

    Checks for dangerous commands must scope to these. Prose elsewhere -- the README,
    this suite's own documentation, the assessment -- legitimately quotes the commands
    it is warning about, and failing the build for describing a hazard would teach the
    wrong lesson.
    """
    for rel, text in all_tracked_text():
        if rel.startswith(("skills/", "agents/", "commands/")):
            yield rel, text


# ------------------------------------------------------- plugin/layout integrity

@check("plugin.json exists, parses, and declares name + description")
def _():
    p = os.path.join(REPO, ".claude-plugin", "plugin.json")
    assert os.path.isfile(p), "missing .claude-plugin/plugin.json"
    data = json.load(open(p, encoding="utf-8"))
    for key in ("name", "description"):
        assert data.get(key), f"plugin.json has no {key!r}"
    assert data.get("version"), "plugin.json has no version (needed by item 4.5)"


@check("the plugin directories exist and are non-empty")
def _():
    assert skill_files(), "no skills found at skills/*/SKILL.md"
    assert agent_files(), "no agents found at agents/*.md"
    assert command_files(), "no commands found at commands/*.md"


@check("no skills, agents or commands are left under .claude/")
def _():
    stale = [d for d in ("skills", "agents", "commands")
             if os.path.isdir(os.path.join(REPO, ".claude", d))]
    assert not stale, f"still present under .claude/: {stale} -- plugin layout expects them at the root"


@check("nothing references the pre-plugin .claude/ paths")
def _():
    bad = []
    for rel, text in all_tracked_text():
        # The assessment and the rescued docs discuss the old layout on purpose.
        if rel.startswith("docs/") or rel in ("ARCHITECTURE.md", "CLAUDE.md"):
            continue
        for m in re.finditer(r"\.claude/(skills|agents|commands)/", text):
            bad.append(f"{rel}: {m.group(0)}")
    assert not bad, "stale .claude/ path references:\n    " + "\n    ".join(bad)


# ---------------------------------------------------------- frontmatter contract

@check("every skill has frontmatter with name and description")
def _():
    bad = []
    for name, path in skill_files():
        fm, _body = parse_frontmatter(path)
        if not fm:
            bad.append(f"{name}: no frontmatter block")
        else:
            for key in ("name", "description"):
                if not fm.get(key):
                    bad.append(f"{name}: missing {key!r}")
    assert not bad, "\n    " + "\n    ".join(bad)


@check("every skill's name matches its directory")
def _():
    bad = [f"dir {d!r} declares name {parse_frontmatter(p)[0].get('name')!r}"
           for d, p in skill_files() if parse_frontmatter(p)[0].get("name") != d]
    assert not bad, "\n    " + "\n    ".join(bad)


@check("every agent has frontmatter with name and description, name matching its file")
def _():
    bad = []
    for stem, path in agent_files():
        fm, _body = parse_frontmatter(path)
        if not fm:
            bad.append(f"{stem}: no frontmatter")
            continue
        if not fm.get("description"):
            bad.append(f"{stem}: missing description")
        if fm.get("name") != stem:
            bad.append(f"{stem}: declares name {fm.get('name')!r}")
    assert not bad, "\n    " + "\n    ".join(bad)


@check("every command has frontmatter with a description", finding="F8")
def _():
    # Without this a command loads as a project command but silently fails to
    # register as a plugin command. That is how /prd, /crd and /crd-context
    # vanished during the plugin conversion.
    bad = []
    for stem, path in command_files():
        fm, _body = parse_frontmatter(path)
        if not fm.get("description"):
            bad.append(f"{stem}: no description in frontmatter -- will not register as a plugin command")
    assert not bad, "\n    " + "\n    ".join(bad)


# ------------------------------------------------------------ fork / model rules
# These encode what the Phase 0 probes measured. See docs/skills/probes/README.md.

@check("no skill declares `allowed-tools`", finding="F13")
def _():
    bad = [name for name, path in skill_files()
           if "allowed-tools" in parse_frontmatter(path)[0]]
    assert not bad, (
        f"{len(bad)} skill(s) declare `allowed-tools`, which is a COMMAND key. In a skill "
        f"it restricts nothing and stops `context: fork` taking effect, so the skill never "
        f"forks, `agent:` never fires and `model:` never applies:\n    " + "\n    ".join(bad))


@check("every skill declaring `context: fork` can actually fork", finding="F13")
def _():
    bad = [name for name, path in skill_files()
           if parse_frontmatter(path)[0].get("context") == "fork"
           and "allowed-tools" in parse_frontmatter(path)[0]]
    assert not bad, ("declare `context: fork` but also `allowed-tools`, so they do not fork:"
                     "\n    " + "\n    ".join(bad))


@check("every `agent:` named by a skill exists in agents/", finding="F7")
def _():
    known = {stem for stem, _p in agent_files()}
    bad = []
    for name, path in skill_files():
        ref = parse_frontmatter(path)[0].get("agent")
        if ref and ref not in known:
            bad.append(f"{name}: agent {ref!r} not found in agents/")
    assert not bad, "\n    " + "\n    ".join(bad)


@check("a skill and the agent it names declare the same model", finding="F7", expect_fail="4.2")
def _():
    agents = {stem: parse_frontmatter(p)[0] for stem, p in agent_files()}
    bad = []
    for name, path in skill_files():
        fm = parse_frontmatter(path)[0]
        ref, smodel = fm.get("agent"), fm.get("model")
        if not ref or ref not in agents:
            continue
        amodel = agents[ref].get("model")
        if smodel and amodel and smodel != amodel:
            # The skill's model wins (measured, F6), so the agent's silently loses.
            bad.append(f"{name}: skill={smodel} but agent {ref}={amodel}")
    assert not bad, ("skill and agent disagree; the skill's model wins, so the agent's is "
                     "silently ignored:\n    " + "\n    ".join(bad))


@check("no stale or invalid model identifiers", finding="F5", expect_fail="4.2")
def _():
    bad = []
    for label, items in (("skill", skill_files()), ("agent", agent_files()),
                         ("command", command_files())):
        for name, path in items:
            model = parse_frontmatter(path)[0].get("model")
            if model is None:
                continue
            model = str(model).strip()
            if model in STALE_MODELS:
                bad.append(f"{label} {name}: {model} is superseded")
            elif model not in VALID_MODELS:
                bad.append(f"{label} {name}: {model} is not a recognised identifier")
    assert not bad, "\n    " + "\n    ".join(bad)


# ------------------------------------------------------------- dangerous content

@check("no remote operation that assumes a remote exists", finding="F1")
def _():
    # `/execute` must work against a repository with no remote. A bare `git pull` or
    # `git fetch` is the first command of every task, so an unguarded one fails the
    # whole pipeline. Guarded means the file also tests for the remote first.
    bad = []
    for rel, text in instruction_text():
        guarded = "remote get-url" in text
        for i, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if re.search(r"\bgit\s+(pull|fetch)\b", line) and not guarded:
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("fails on a repository with no remote, and this runs before every "
                     "task:\n    " + "\n    ".join(bad))


@check("no hardcoded `main` branch in the execute pipeline", finding="F1")
def _():
    # The branch name is a parameter (`--base-branch`, defaulting to HEAD). A literal
    # `main` in a git command silently targets the wrong branch on any other default.
    bad = []
    for rel, text in instruction_text():
        for i, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#") or "base-branch" in line:
                continue
            if re.search(r"\bgit\s+\S+.*\b(origin/main|main\.\.|\bmain\b)\s*$", line) or \
               re.search(r"\bgit\s+(checkout|merge|fetch|pull|rebase)\s+(origin/)?main\b", line):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("hardcodes the branch name instead of using {base_branch}:\n    "
                     + "\n    ".join(bad))


@check("nothing deletes a .git directory", finding="F2")
def _():
    bad = []
    for rel, text in instruction_text():
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"rm\s+-rf?\s+[^\s]*\.git\b", line):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("destroys git history at whatever path is passed in:\n    "
                     + "\n    ".join(bad))


@check("`/execute` refuses to target the wrong repository", finding="F2")
def _():
    # A mistyped --project-path makes /execute create branches and merge in the wrong
    # repo. The preflight must rule out the paths that are never valid targets.
    text = open(os.path.join(SKILLS, "execute", "SKILL.md"),
                encoding="utf-8", errors="replace").read()
    missing = [name for name, pat in (
        ("docs/prd guard", r"docs/prd"),
        ("toolchain guard", r"\.claude-plugin"),
        ("REFUSED message", r"REFUSED"),
    ) if not re.search(pat, text)]
    assert not missing, ("execute preflight is missing: " + ", ".join(missing))


@check("no generated output committed under skills/", finding="F4")
def _():
    bad = [rel for rel, _t in all_tracked_text()
           if re.match(r"^skills/[^/]+/output/", rel)]
    assert not bad, ("generated artefacts committed into the toolchain tree:\n    "
                     + "\n    ".join(bad))


@check("every referenced references/ file exists")
def _():
    bad = []
    for name, path in skill_files():
        _fm, body = parse_frontmatter(path)
        for m in re.finditer(r"`(?:skills/[^`]+/)?references/([A-Za-z0-9._-]+\.md)`", body):
            target = os.path.join(SKILLS, name, "references", m.group(1))
            if not os.path.isfile(target):
                bad.append(f"{name}: references/{m.group(1)} does not exist")
    assert not bad, "\n    " + "\n    ".join(bad)


# ------------------------------------------------------------------- behavioural

def behaviour_checks():
    """Read-only: confirm the plugin registers everything on disk. Needs `claude`."""
    expected_skills = {n for n, _p in skill_files()}
    expected_agents = {n for n, _p in agent_files()}
    expected_cmds = {n for n, _p in command_files()}
    plugin = json.load(open(os.path.join(REPO, ".claude-plugin", "plugin.json"),
                            encoding="utf-8"))["name"]

    names = sorted(expected_skills | expected_agents | expected_cmds)
    prompt = ("No tools, no preamble. Some names below are fake - be truthful. For each "
              "line output \"NAME = PRESENT\" or \"NAME = ABSENT\" according to your real "
              "available skills, agents and commands.\n"
              + "\n".join(f"{plugin}:{n}" for n in names)
              + f"\n{plugin}:zzz-not-a-real-entry")

    proc = subprocess.run(
        ["claude", "-p", prompt, "--model", "sonnet", "--plugin-dir", REPO],
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    out = proc.stdout or ""

    present = {m.group(1) for m in
               re.finditer(rf"{re.escape(plugin)}:([A-Za-z0-9_-]+)\s*=\s*PRESENT", out, re.I)}
    # The decoy proves the answer is a real lookup rather than an echo of the question.
    assert "zzz-not-a-real-entry" not in present, (
        "the decoy name reported PRESENT, so this answer is an echo, not a lookup:\n" + out[:500])

    missing = sorted((expected_skills | expected_agents | expected_cmds) - present)
    assert not missing, ("on disk but not registered by the plugin:\n    "
                         + "\n    ".join(missing) + f"\n\nraw:\n{out[:800]}")
    return len(present)


# ------------------------------------------------------------------------ runner

def main():
    ap = argparse.ArgumentParser(description="Regression suite for the toolchain")
    ap.add_argument("--behaviour", action="store_true",
                    help="also run the plugin-load check (needs the `claude` CLI, ~30s)")
    ap.add_argument("-v", "--verbose", action="store_true", help="show failure detail for KNOWN")
    args = ap.parse_args()

    width = max(len(r["name"]) for r in _RESULTS) + 2
    passed = failed = known = fixed = 0
    problems = []

    print(f"Regression suite -- {len(_RESULTS)} static checks\n" + "=" * (width + 34))
    for r in _RESULTS:
        tag = f"[{r['finding']}]" if r["finding"] else ""
        try:
            r["fn"]()
            err = None
        except AssertionError as e:
            err = str(e)
        except Exception as e:                      # a broken check is a failure
            err = f"check raised {type(e).__name__}: {e}"

        if err is None and r["expect_fail"]:
            status, fixed = "FIXED", fixed + 1
            problems.append((r["name"], f"now passes -- remove expect_fail={r['expect_fail']!r} "
                                        f"so it becomes a permanent regression guard"))
        elif err is None:
            status, passed = "pass", passed + 1
        elif r["expect_fail"]:
            status, known = f"KNOWN/{r['expect_fail']}", known + 1
            if args.verbose:
                problems.append((r["name"], err))
        else:
            status, failed = "FAIL", failed + 1
            problems.append((r["name"], err))

        print(f"  {status:<12} {r['name']:<{width}} {tag}")

    if args.behaviour:
        print("\nBehavioural check (read-only)\n" + "=" * (width + 34))
        try:
            n = behaviour_checks()
            print(f"  {'pass':<12} plugin registers all {n} entries on disk")
            passed += 1
        except Exception as e:
            print(f"  {'FAIL':<12} plugin load")
            problems.append(("plugin load", str(e)))
            failed += 1

    if problems:
        print("\nDetail\n" + "=" * (width + 34))
        for name, detail in problems:
            print(f"\n  {name}\n    {detail}")

    print(f"\n{'-' * (width + 34)}")
    print(f"passed {passed}   failed {failed}   known {known}   fixed {fixed}")
    if known:
        print(f"\n{known} check(s) encode a target state not yet reached. They are expected to "
              f"fail\nuntil the named remediation item lands, then must have the marker removed.")
    if fixed:
        print(f"\n{fixed} check(s) marked as expected failures now PASS. Remove the marker.")

    return 1 if (failed or fixed) else 0


if __name__ == "__main__":
    sys.exit(main())
