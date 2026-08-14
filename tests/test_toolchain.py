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


@check("no forked skill dispatches work in the background", finding="F17")
def _():
    # A forked skill ends when its turn ends. Dispatching with `run_in_background: true`
    # and then intending to wait does not pause anything: the skill returns immediately
    # with the work outstanding, its parent sees an unfinished batch and re-implements
    # everything inline, and the agent's real result arrives after the context that asked
    # for it is gone. Three end-to-end runs were lost to this before it was understood.
    bad = []
    for rel, text in instruction_text():
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"run_in_background[\"']?\s*[:=>]\s*[\"']?true", line, re.I) or \
               re.search(r"<run_in_background>\s*true", line, re.I):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, (
        "dispatch work in the background from a skill that cannot outlive its own turn "
        "to collect it:\n    " + "\n    ".join(bad))


@check("no skill waits on background tasks it cannot outlive", finding="F17")
def _():
    # The companion to the check above. `TaskOutput` polling only makes sense for
    # background tasks; with blocking dispatch there is no task id to poll, so a lingering
    # instruction to poll is an invitation to re-create the failure. Mentioning the tool in
    # order to forbid it is fine -- a "do not poll" line must not trip this.
    bad = []
    for rel, text in instruction_text():
        for i, line in enumerate(text.splitlines(), 1):
            if "TaskOutput" not in line:
                continue
            if re.search(r"\b(do not|don't|never|no)\b", line, re.I):
                continue
            bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("poll for background results that will never arrive in this "
                     "context:\n    " + "\n    ".join(bad))


@check("worktree creation is a script, never a command in prose", finding="F18")
def _():
    # A `git worktree add` line in a document gets retyped from understanding rather than
    # copied. Across an 18-task run, six agents attempted it, none included `-b`, and all
    # six failed -- without `-b` git checks out the base branch, which the primary worktree
    # already holds, so it refuses every time. The script is the only place this command
    # may live.
    script = os.path.join(SKILLS, "execute-batch", "scripts", "create-worktree.sh")
    assert os.path.isfile(script), "skills/execute-batch/scripts/create-worktree.sh is missing"
    body = open(script, encoding="utf-8").read()
    assert re.search(r"worktree add\s+-b\b", body), (
        "create-worktree.sh does not pass `-b`, which is the entire reason it exists")
    assert "--show-toplevel" in body, (
        "create-worktree.sh does not assert it is in the intended repository (F19)")

    bad = []
    for rel, text in instruction_text():
        if not rel.endswith(".md"):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"^\s*git worktree add\b", line):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("spell out `git worktree add` in prose; call the bundled script "
                     "instead:\n    " + "\n    ".join(bad))


@check("task completion is recorded as a SHA and counted from git", finding="F16")
def _():
    # Run 6 succeeded and still reported 23 of 18 tasks complete, 19 entries in an 18-task
    # list, and an invented elapsed time. Every wrong number was incremented by hand; the
    # only right one was derived. Both scripts must exist, and both must check git rather
    # than take anyone's word.
    rec = os.path.join(SKILLS, "execute-merge", "scripts", "record-task.sh")
    sts = os.path.join(SKILLS, "execute", "scripts", "ledger-status.sh")
    assert os.path.isfile(rec), "skills/execute-merge/scripts/record-task.sh is missing"
    assert os.path.isfile(sts), "skills/execute/scripts/ledger-status.sh is missing"

    rtext = open(rec, encoding="utf-8").read()
    assert "cat-file -e" in rtext, (
        "record-task.sh does not verify the commit exists before recording it")
    assert "gitignore" in rtext, (
        "record-task.sh does not keep the ledger out of the target's git status")

    stext = open(sts, encoding="utf-8").read()
    assert "cat-file -e" in stext, (
        "ledger-status.sh trusts the ledger instead of verifying SHAs against git")

    merge = open(os.path.join(SKILLS, "execute-merge", "SKILL.md"), encoding="utf-8").read()
    assert "record-task.sh" in merge, "execute-merge never records anything in the ledger"
    ex = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    assert "ledger-status.sh" in ex, "execute never reconciles its state against git"


@check("the manifest is built from task files, not from the plan", finding="F9")
def _():
    # The manifest used to be written from layer_plan.json and never reconciled with what
    # generation produced. On the fixture that meant 20 declared against 18 files, with all
    # six Layer 0 entries naming files that did not exist -- generation had consolidated six
    # planned tasks into four and renamed every one. /execute faithfully reported 18 of 20.
    script = os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py")
    assert os.path.isfile(script), "skills/breakdown/scripts/build-manifest.py is missing"
    body = open(script, encoding="utf-8").read()
    assert "--verify" in body, "build-manifest.py has no verify mode"

    sk = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    assert "build-manifest.py" in sk, (
        "breakdown does not call build-manifest.py, so the manifest is still hand-written")
    assert "--verify" in sk, (
        "breakdown never verifies the manifest against the files it generated")


@check("PROJECT.md is validated after the finalizer rewrites it", finding="F23")
def _():
    # The finalizer writes XML by hand. On its first ever run it emitted
    # `?tag=python&status=archived` into a <description>; a bare & is not valid XML, so the
    # <project-context> block stopped parsing and every consumer broke silently. Escaping is
    # a prose instruction to the agent; the check afterwards is not.
    script = os.path.join(SKILLS, "execute", "scripts", "check-project-md.py")
    assert os.path.isfile(script), "skills/execute/scripts/check-project-md.py is missing"
    body = open(script, encoding="utf-8").read()
    assert "amp;" in body, "check-project-md.py does not handle bare ampersands"
    # Both, not either: an `or` here passes when half the mechanism is removed, which is how
    # three earlier guards in this suite managed to survive their own bite tests.
    assert "ET.fromstring(" in body, \
        "check-project-md.py never parses the block, so it cannot know it is well-formed"
    assert "ParseError" in body, (
        "check-project-md.py does not handle a parse failure, so a malformed block crashes "
        "it rather than being reported")

    ex = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    step10 = ex[ex.find("### Step 10"):ex.find("### Step 11")]
    assert "check-project-md.py" in step10, \
        "Step 10 does not validate PROJECT.md after the finalizer rewrites it"
    assert re.search(r"do not commit", step10, re.I), \
        "Step 10 does not say a failed validation blocks the commit"

    agent = open(os.path.join(AGENTS, "project-context-finalizer.md"), encoding="utf-8").read()
    assert "&amp;" in agent, "the finalizer is not told to escape ampersands"


@check("the CRD fixture is buildable and self-consistent")
def _():
    # The greenfield fixture caught every finding this project fixed; the CRD half had no
    # fixture at all. This checks the definition statically -- that the app is coherent and
    # its traps are intact -- so drift fails here rather than three hours into a CRD run.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "crd_app_files", os.path.join(REPO, "tests", "fixture", "crd_app_files.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    paths = [rel for rel, _c, _n in mod.FILES]
    assert len(paths) == len(set(paths)), "duplicate path in the CRD fixture file list"

    # Every commit must place at least one file, or git rejects the empty commit at build.
    for n, message in enumerate(mod.COMMITS):
        assert any(cn == n for _r, _c, cn in mod.FILES), \
            f"CRD fixture commit {n} ({message}) places no files"
    highest = max(cn for _r, _c, cn in mod.FILES)
    assert highest < len(mod.COMMITS), \
        f"CRD fixture assigns a file to commit {highest} but only {len(mod.COMMITS)} exist"

    # The traps are the fixture's whole value. Losing one silently would make a CRD run
    # look successful while testing nothing interesting.
    body = {rel: content for rel, content, _n in mod.FILES}
    assert "app/models/link_tag.py" in body, \
        "tags must stay a join table; a string column makes impact analysis trivial"
    assert "link_tags" in body.get("app/models/link.py", ""), \
        "Link no longer references the join table"
    assert "delete_link" in body.get("app/api/links.py", ""), \
        "delete must exist -- the change request asks for archiving *alongside* it"
    assert "test_delete_is_permanent" in body.get("tests/test_links.py", ""), \
        "the test that a careless change would break is missing"
    assert "archived" in body.get("tests/test_models.py", ""), \
        "nothing asserts the starting state the change request is expected to alter"
    assert not any("PROJECT.md" in rel for rel in paths), \
        "PROJECT.md must be absent -- producing it is /crd-context's job"

    cr = os.path.join(REPO, "tests", "fixture", "crd", "change-request.md")
    assert os.path.isfile(cr), "tests/fixture/crd/change-request.md is missing"
    text = open(cr, encoding="utf-8").read()
    assert "<" not in text.split("---", 2)[-1], \
        "the change request has XML in it; it must be prose, or /crd is handed its own output"


@check("no agent is orphaned -- every one is reachable", finding="F11")
def _():
    # project-context-finalizer sat unreferenced for the life of the toolchain: 219 lines
    # specifying a job that /execute also described inline, with nothing deciding which ran.
    # That is F20's shape, and the general fix is to notice when an agent has no caller.
    #
    # An agent is reachable two ways: a skill runs *as* it (`agent:` frontmatter), or a skill
    # dispatches it (`subagent_type`). Both are real invocation mechanisms; being merely
    # mentioned in prose is not, which is the distinction F20 was about.
    referenced = set()
    for _rel, text in instruction_text():
        for m in re.finditer(r"^agent:[ \t]*([\w-]+)", text, re.M):
            referenced.add(m.group(1))
        for m in re.finditer(r"subagent_type[\"']?\s*[:=]\s*[\"']([\w:-]+)", text):
            referenced.add(m.group(1).split(":")[-1])

    orphans = [name for name, _p in agent_files() if name not in referenced]
    assert not orphans, (
        "agent(s) that nothing invokes -- wire them in or delete them; unreferenced "
        "definitions rot, and a second description of a job nothing dispatches is how "
        "F20 happened:\n    " + "\n    ".join(orphans))


@check("`/prd` looks for existing PRDs before starting a new one", finding="F3")
def _():
    # /prd with no arguments used to begin a fresh interview immediately, and Phase 8 then
    # writes to docs/prd/[slug]/ -- so an existing PRD could be overwritten without anyone
    # being asked. 5.2 test 3 confirmed it: a fresh interview opened with a PRD present.
    # NOTE ON WHAT THIS CAN AND CANNOT DO. A command file is prose, so this check verifies
    # wording, and F15 is the standing reminder that wording is not behaviour. It anchors on
    # the *commands* rather than the surrounding sentences, because a command is the part
    # that would actually run -- and because an earlier version of this check asserted on
    # prose with `|` alternatives, which the prose satisfied redundantly: every mutation of
    # the guard left it green. Only §5.2 test 3 can confirm the behaviour.
    text = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    init = text[text.find("## Initialization"):text.find("## Workflow Phases")]
    assert init.strip(), "prd.md has no Initialization section"

    # Unconditional: the look-up must not sit under an "if --resume" branch.
    assert re.search(r"regardless of arguments", init, re.I), (
        "Initialization does not state the existing-PRD check is unconditional, so the "
        "no-argument path can still start a fresh interview over an existing PRD")
    assert re.search(r"ls -d docs/prd/\*/", init), (
        "Initialization has no command that enumerates existing PRD directories")

    # Both marker locations in one command, so PRDs predating the template are still found.
    marker = re.search(r"grep[^\n]*status[^\n]*\n?[^\n]*", init)
    assert marker, "Initialization has no grep for the in-progress status marker"
    assert "what-next.md" in marker.group(0) and "index.md" in marker.group(0), (
        "the status-marker search does not cover both what-next.md and index.md; a PRD it "
        "cannot find is a PRD it will silently replace")

    # The write path must refuse on its own, not rely on care taken earlier.
    phase8 = text[text.find("### Phase 8"):text.find("## Output Formats")]
    assert re.search(r"test -e docs/prd/", phase8), (
        "Phase 8 writes docs/prd/[slug]/ without a command that checks whether it exists")
    assert re.search(r"\*\*stop and ask\*\*", phase8), (
        "Phase 8 does not require stopping to ask before replacing an existing PRD")


@check("execute-state.json is written by a script, never by hand", finding="F21")
def _():
    # Four runs, four different wrong shapes, each produced by a different set of careful
    # prose instructions: 23 of 18 complete; 19 entries for 18 tasks; "completed" alongside
    # 2 remaining; "completed" alongside 4 of 18 while git held 18 merges -- plus a second
    # copy written into the target repository. One script owns the file now.
    ws = os.path.join(SKILLS, "execute", "scripts", "write-state.py")
    assert os.path.isfile(ws), "skills/execute/scripts/write-state.py is missing"
    body = open(ws, encoding="utf-8").read()
    assert "cat-file" in body, "write-state.py trusts the ledger instead of verifying it"
    assert "REFUSED" in body, (
        "write-state.py does not refuse to write inside the target project (F21)")

    # Nobody else may *mutate* it. Reading is fine and sometimes necessary; `rm -f` in
    # --reset is fine. An assignment, an append or a delete into its fields is not -- that
    # is the hand-maintenance this finding is about.
    mutation = re.compile(
        r'state\[["\'](tasks|metrics|completed|merge_queue|layers|abandoned|failed)["\']\]'
        r'.*?(=(?!=)|\.append\(|\.pop\(|\.extend\()'
        r'|^\s*del\s+state\[')
    bad = []
    for rel, text in instruction_text():
        if not rel.endswith(".md"):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if "execute-state.json" in line and re.search(r">\s*\{?tasks_path", line):
                bad.append(f"{rel}:{i}: redirect into the state file -- {line.strip()[:70]}")
            elif mutation.search(line):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("mutate execute-state.json by hand; call write-state.py "
                     "instead:\n    " + "\n    ".join(bad))


@check("resume is decided by verified commits, not by the state file", finding="F16")
def _():
    # A resume that trusts execute-state.json skips work that was never done. That file once
    # reported 20/20 complete against a single merge commit; acting on it is silent data
    # loss, which is worse than crashing. The ledger, re-verified against git, is the only
    # acceptable input.
    sts = os.path.join(SKILLS, "execute", "scripts", "ledger-status.sh")
    assert "verified_tasks" in open(sts, encoding="utf-8").read(), (
        "ledger-status.sh does not report which tasks are verified, so a resume has "
        "nothing safe to skip on")

    ex = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    assert "verified_tasks" in ex, (
        "execute never consults verified_tasks; resume would be trusting the state file")
    # --reset must not be a way to lose work by accident.
    reset_section = ex[ex.find("--reset"):ex.find("--reset") + 4000]
    assert re.search(r"NOT deleted|never deletes", reset_section, re.I), (
        "--reset does not state that it leaves commits and branches alone")


@check("no skill increments a progress counter by hand", finding="F16")
def _():
    # `tasks_completed += 1` is the shape of the bug: a number that drifts from reality and
    # cannot be checked. Counts come from ledger-status.sh, which asks git.
    bad = []
    for rel, text in instruction_text():
        if not rel.endswith(".md"):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"(tasks_completed|tasks_remaining|tasks_failed|total_attempts)"
                         r"\W*\]?\W*(\+=|-=)", line):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("increment progress counters by hand instead of deriving them from "
                     "git:\n    " + "\n    ".join(bad))


@check("no agent is told to invoke a skill it cannot invoke", finding="F20")
def _():
    # `/execute-task ...` inside an Agent prompt is text. It does not resolve, nothing
    # loads, and for five runs the entire task procedure went unread because of it. A
    # dispatched agent has no Skill tool: everything it needs belongs in the prompt or in
    # its agent definition.
    #
    # This catches the two phrasings that produced the bug, not the whole class -- a
    # skill named in a prompt is textually identical to a skill invoked from a skill's own
    # instructions, so no static rule separates them in general. Treat it as a tripwire.
    bad = []
    for rel, text in instruction_text():
        if not rel.endswith(".md"):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"using the /[a-z][a-z0-9-]* skill", line, re.I) or \
               re.search(r"Execute the following command:", line, re.I):
                bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("tell a dispatched agent to run a slash command, which in an agent "
                     "prompt is inert text:\n    " + "\n    ".join(bad))


@check("the task agent is handed a worktree rather than asked to make one", finding="F20")
def _():
    # The caller creates the worktree and passes the path; the agent is forbidden from
    # creating one. Both halves must hold or isolation silently reverts to "whatever
    # directory the agent happened to be in".
    batch = os.path.join(SKILLS, "execute-batch", "SKILL.md")
    assert os.path.isfile(batch), "skills/execute-batch/SKILL.md is missing"
    btext = open(batch, encoding="utf-8").read()
    assert "create-worktree.sh" in btext, (
        "execute-batch does not call create-worktree.sh -- nothing creates the worktree")
    assert "{worktree_path}" in btext, (
        "execute-batch never passes {worktree_path} to the agent it spawns")

    agent = os.path.join(AGENTS, "task-implementer.md")
    atext = open(agent, encoding="utf-8").read()
    assert re.search(r"[Nn]ever run `git worktree add`", atext), (
        "task-implementer is not told to leave worktree creation alone")


@check("no skill instructs `git init`", finding="F19")
def _():
    # /execute creates no repositories. A run that failed to make a worktree walked up to
    # the workspace root, ran `git init` there and merged into it, producing a stray
    # repository holding the docs tree and a gitlink to the real project. Lines that
    # *forbid* git init are the point and must not trip this.
    # Distinguish instructing from discussing. Prose quotes the command inside backticks
    # ("does NOT run `git init`"); an instruction is a bare command, which in these files
    # means inside a fenced block. Stripping inline-code spans separates the two cleanly
    # and needs no keyword list to keep in step with the wording.
    bad = []
    for rel, text in instruction_text():
        if not rel.endswith(".md"):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if "git init" not in re.sub(r"`[^`]*`", "", line):
                continue
            bad.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not bad, ("instruct `git init`, which /execute must never do:\n    "
                     + "\n    ".join(bad))


@check("every `agent:` named by a skill exists in agents/", finding="F7")
def _():
    known = {stem for stem, _p in agent_files()}
    bad = []
    for name, path in skill_files():
        ref = parse_frontmatter(path)[0].get("agent")
        if ref and ref not in known:
            bad.append(f"{name}: agent {ref!r} not found in agents/")
    assert not bad, "\n    " + "\n    ".join(bad)


@check("a skill and the agent it names declare the same model", finding="F7")
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


@check("no stale or invalid model identifiers", finding="F5")
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


@check("`/execute` refuses to target the wrong repository -- by running the guard", finding="F15")
def _():
    # This check used to assert that the guard *text* appeared in SKILL.md. F15 is what that
    # was worth: the text was present, correct and ignored. So run the guard instead, against
    # real directories, and assert what it does.
    import shutil
    import stat
    import tempfile

    pf = os.path.join(SKILLS, "execute", "scripts", "preflight.sh")
    assert os.path.isfile(pf), "skills/execute/scripts/preflight.sh is missing"

    sk = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    assert "preflight.sh" in sk, "execute never calls preflight.sh, so nothing enforces it"

    if not shutil.which("git") or not shutil.which("sh"):
        return  # nothing to run the guard with; the static half above still applied

    def run(tasks, project, base=None):
        cmd = ["sh", pf, tasks, project] + ([base] if base else [])
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return p.returncode, (p.stdout or "") + (p.stderr or "")

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    root = tempfile.mkdtemp(prefix="preflight-check-")
    try:
        tasks = os.path.join(root, "tasks")
        os.makedirs(tasks)
        for f in ("manifest.json", "layer_plan.json"):
            open(os.path.join(tasks, f), "w").write("{}")

        def new_repo(name):
            d = os.path.join(root, name)
            os.makedirs(d, exist_ok=True)
            for args in (["init", "-q", "-b", "main", "."],
                         ["config", "user.email", "t@t.invalid"],
                         ["config", "user.name", "T"]):
                subprocess.run(["git", "-C", d] + args, capture_output=True, timeout=60)
            open(os.path.join(d, "f.txt"), "w").write("x")
            subprocess.run(["git", "-C", d, "add", "-A"], capture_output=True, timeout=60)
            subprocess.run(["git", "-C", d, "commit", "-qm", "init"],
                           capture_output=True, timeout=60)
            return d

        app = new_repo("app")

        rc, out = run(tasks, app)
        assert rc == 0, f"preflight refuses a valid target: {out.strip()[:200]}"
        assert "main" in out, f"preflight did not resolve the base branch: {out.strip()[:200]}"

        # The cases that must be refused. Each is a real failure this project has hit.
        docs = new_repo("docsrepo")
        os.makedirs(os.path.join(docs, "docs", "prd"), exist_ok=True)

        plugin = new_repo("toolchain")
        os.makedirs(os.path.join(plugin, ".claude-plugin"), exist_ok=True)
        open(os.path.join(plugin, ".claude-plugin", "plugin.json"), "w").write("{}")

        plain = os.path.join(root, "plain")
        os.makedirs(plain)
        sub = os.path.join(app, "sub")
        os.makedirs(sub, exist_ok=True)

        for label, args in (
            ("a documentation tree (F15's exact case)", (tasks, docs)),
            ("the toolchain repository", (tasks, plugin)),
            ("a directory that is not a repository", (tasks, plain)),
            ("a subdirectory of a repository (F19)", (tasks, sub)),
            ("a nonexistent base branch", (tasks, app, "nosuchbranch")),
        ):
            rc, out = run(*args)
            assert rc != 0, f"preflight ACCEPTED {label}"
            assert "REFUSED" in out, f"refusal of {label} does not say REFUSED: {out[:160]}"

        assert not os.path.isdir(os.path.join(plain, ".git")), (
            "preflight created a repository -- /execute must never run `git init`")
    finally:
        rmtree(root)


@check("a usage limit stops the run instead of burning five retries", finding="F15")
def _():
    # `execute-task` retries five times. Against a closed subscription window that is five
    # guaranteed failures spending the allowance the resume will need. The decision has to be
    # an exit code: a usage limit reads like a transient error, and "try once more" reads like
    # a reasonable response to one -- which is the F15 shape, a correct instruction reasoned
    # past. So run the classifier and assert what it does, rather than that SKILL.md says so.
    import shutil

    script = os.path.join(SKILLS, "execute-batch", "scripts", "classify-failure.sh")
    assert os.path.isfile(script), "skills/execute-batch/scripts/classify-failure.sh is missing"

    # Wiring, asserted one piece at a time. An `A or B` guard here has passed three times in
    # this project while half the mechanism was gone.
    batch = open(os.path.join(SKILLS, "execute-batch", "SKILL.md"), encoding="utf-8").read()
    assert "classify-failure.sh" in batch, (
        "execute-batch never runs the classifier, so every failure still retries five times")
    assert "usage_limit" in batch, "execute-batch does not report a usage-limit stop distinctly"

    layer = open(os.path.join(SKILLS, "execute-layer", "SKILL.md"), encoding="utf-8").read()
    assert "stop_reason_kind" in layer, (
        "execute-layer flattens the two stop kinds, so /execute cannot tell them apart")

    ex = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    assert "usage_limit" in ex, "execute has no usage-limit branch in its stop message"

    if not shutil.which("sh"):
        return  # nothing to run the guard with; the static half above still applied

    def classify(text):
        p = subprocess.run(["sh", script], input=text, capture_output=True,
                           text=True, timeout=60)
        return p.returncode, (p.stdout or "").splitlines()

    # Real error shapes. `limit` must stop (exit 3); everything else must retry (exit 0).
    STOP = [
        "Claude AI usage limit reached. Your limit will reset at 5pm.",
        '{"error":{"message":"Your credit balance is too low to access the Anthropic API."}}',
        "You have exceeded your monthly quota",
        "5-hour limit reached",
        "weekly limit reached for this account",
    ]
    # These read like limits and are not. Collapsing them into `limit` would halt healthy
    # runs on a per-minute blip, which is a worse failure than the one being fixed.
    GO = [
        'API Error: 429 {"type":"rate_limit_error","message":"Number of requests exceeded"}',
        'API Error: 529 {"type":"overloaded_error"}',
        "Connection error: ECONNRESET",
        "verification_failed: pytest tests/test_x.py -- 1 test failed",
        "ModuleNotFoundError: no module named app.models",
        "",                      # nothing recognisable must retry, i.e. behave as it does today
        "some error nobody has seen before",
    ]

    for text in STOP:
        rc, out = classify(text)
        assert rc == 3, f"classifier lets the run continue on a usage limit: {text[:70]!r}"
        assert out and out[0] == "limit", f"expected `limit`, got {out[:1]}: {text[:70]!r}"

    for text in GO:
        rc, out = classify(text)
        assert rc == 0, f"classifier stops the whole run on a retryable failure: {text[:70]!r}"
        assert out and out[0] in ("code", "transient"), (
            f"expected `code`/`transient`, got {out[:1]}: {text[:70]!r}")

    # The stop message is only actionable if it says when to come back, and the reset time
    # must be quoted rather than estimated -- so it appears only when the error carried one.
    rc, out = classify("Claude AI usage limit reached, resets at 2026-08-14T17:30:00Z")
    assert any(l.startswith("reset:") for l in out), (
        "classifier dropped the reset time the error supplied")
    rc, out = classify("Claude AI usage limit reached")
    assert not any(l.startswith("reset:") for l in out), (
        "classifier invented a reset time the error did not contain")


@check("no generated output committed under skills/", finding="F4")
def _():
    bad = [rel for rel, _t in all_tracked_text()
           if re.match(r"^skills/[^/]+/output/", rel)]
    assert not bad, ("generated artefacts committed into the toolchain tree:\n    "
                     + "\n    ".join(bad))


@check("the §5.1 fixture PRD is valid and self-consistent")
def _():
    # The fixture is only useful if /breakdown can parse it. Validating here means a
    # drifting fixture fails the fast suite rather than an end-to-end run.
    import xml.etree.ElementTree as ET
    base = os.path.join(REPO, "tests", "fixture", "prd", "link-shelf")
    assert os.path.isdir(base), "tests/fixture/prd/link-shelf is missing"

    root = ET.parse(os.path.join(base, "index.md")).getroot()
    assert root.tag == "prd", f"index.md root is <{root.tag}>, expected <prd>"
    feats = root.findall("features/feature")
    assert 2 <= len(feats) <= 4, f"{len(feats)} features; §5.1 asks for two or three"

    missing = [f.get("file") for f in feats
               if not f.get("file")
               or not os.path.isfile(os.path.join(base, f.get("file").replace("/", os.sep)))]
    assert not missing, f"feature files missing: {missing}"

    wn = ET.parse(os.path.join(base, "what-next.md")).getroot()
    assert (wn.findtext("status") or "").strip() == "in-progress", \
        "fixture what-next.md needs <status>in-progress</status> for the resume test (F3)"


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
