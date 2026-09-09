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
import ast
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keep_awake import keep_awake  # noqa: E402

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

def prose(text):
    """Markdown flattened for assertions about what a document SAYS.

    Three prose checks in Phase 2 failed on formatting rather than on content -- a phrase
    split by a line wrap, and twice on backticks inside the phrase being matched. A check
    pinned to formatting is the F3 mistake in miniature: it breaks when someone rewraps a
    paragraph or emphasises a word, which is not a change in meaning.

    Collapses whitespace and strips ` * _ so `never emit \\`<cwd>\\`` matches "never emit <cwd>".
    """
    return " ".join(re.sub(r"[`*_]", "", text).split())


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
    # Item 9 replaced `ls -d docs/prd/*/` and the two-file grep with list-prds.py, which
    # enumerates the same directories and additionally reports which file carries each status
    # marker -- the half of F3 the grep could only hint at.
    assert re.search(r"list-prds\.py\s+docs/prd", init), (
        "Initialization has no command that enumerates existing PRD directories")

    # Both marker locations must still be covered, and after item 9 that is a property of the
    # script rather than of a sentence -- so assert it where it is now true. A PRD the lookup
    # cannot find is a PRD it will silently replace.
    lister = open(os.path.join(SKILLS, "breakdown", "scripts", "list-prds.py"),
                  encoding="utf-8").read()
    assert "index.md" in lister and "what-next.md" in lister, (
        "list-prds.py does not read both marker locations; PRDs predating the template carry "
        "the marker only in index.md")

    # The write path must refuse on its own, not rely on care taken earlier. It is now an exit
    # code, and the command must treat it as binding rather than advisory.
    # Located by CONTENT, not by number. This was pinned to "### Phase 8" and item 51
    # inserted a Design phase ahead of it, renumbering the output phase to 9. A check
    # pinned to a heading number fails on a renumber, which is not a change in meaning.
    m_out = re.search(r"### Phase \d+: Output", text)
    assert m_out, "/prd has no Output phase"
    phase8 = text[m_out.start():text.find("## Output Formats")]
    assert re.search(r"check-writable\.py docs/prd/", phase8), (
        "Phase 8 writes docs/prd/[slug]/ without running the overwrite guard")
    assert re.search(r"exit code is binding|\*\*Exit 1\*\*", phase8, re.I), (
        "Phase 8 runs the guard without saying its refusal stops the write")
    assert re.search(r"\bStop\b", phase8), (
        "Phase 8 does not require stopping before replacing an existing PRD")


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
    # Any field, not a list of seven. The allowlist let `state["current_batch"] = n` through
    # for as long as that field existed and for two schema revisions after it stopped -- and
    # the whole point of the finding is that the file is derived, which is true of every key
    # in it including ones nobody has invented yet.
    mutation = re.compile(
        r'state\[["\'][^"\']+["\']\]'
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


@check("multi-repo is refused in Phase 1, with what would be needed", finding="P36")
def _():
    # Item 53. The assumption is already enforced -- create-worktree.sh refuses a subdirectory
    # -- but it fires during batch execution, several phases after the layout was knowable. A
    # repo-per-service project gets a layer plan, a manifest and a full task set first, then
    # fails with a message about worktrees that does not name the cause.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-repo-structure.py")
    assert os.path.isfile(script), "check-repo-structure.py is missing"

    caller = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    phase1 = caller[:caller.find("### Phase 2")]
    assert "check-repo-structure.py" in phase1, (
        "the structure check is not in Phase 1, so the refusal still arrives after a task "
        "set has been generated")

    # The producer: /prd must ask, or the element is one nothing writes.
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    assert "<repo-structure>" in prd, "the PRD template does not carry <repo-structure>"
    assert re.search(r"monorepo", prd), "/prd never asks how the code is laid out"

    root = tempfile.mkdtemp(prefix="prd-repo-")
    try:
        def doc(name, body):
            path = os.path.join(root, name)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
            return path

        cases = {
            "single": ("<prd><tech-stack><repo-structure>single</repo-structure>"
                       "</tech-stack></prd>\n", 0),
            "monorepo": ("<prd><tech-stack><repo-structure>monorepo</repo-structure>"
                         "</tech-stack></prd>\n", 0),
            "multi": ("<prd><tech-stack><repo-structure>multi-repo</repo-structure>"
                      "</tech-stack></prd>\n", 1),
            "bogus": ("<prd><tech-stack><repo-structure>polyrepo</repo-structure>"
                      "</tech-stack></prd>\n", 1),
            # Absent must be `single`. Every PRD written before the element existed means one
            # repository; defaulting to a refusal would break all of them.
            "absent": ("<prd><tech-stack><type>greenfield</type></tech-stack></prd>\n", 0),
        }
        for name, (body, expected) in cases.items():
            p = subprocess.run([sys.executable, script, doc(f"{name}.md", body)],
                               capture_output=True, text=True)
            assert p.returncode == expected, (
                f"{name}: expected exit {expected}, got {p.returncode}\n{p.stdout}{p.stderr}")

        # The refusal must say what would be needed, not merely no -- and must not imply the
        # layout is wrong or that git cannot do it.
        p = subprocess.run([sys.executable, script, os.path.join(root, "multi.md")],
                           capture_output=True, text=True)
        assert "Not a git limitation" in p.stderr, (
            "the refusal does not say this is a missing data model rather than a git one")
        for needed in ("target model", "window"):
            assert needed in p.stderr, f"the refusal does not name what is missing: {needed}"
        assert "Nothing was generated" in p.stderr, (
            "the refusal does not say the run produced nothing, which is the point of "
            "refusing in Phase 1 rather than at merge time")

        # And the two supported values are distinguishable by a caller, since <cwd> depends
        # on which one it is.
        p = subprocess.run([sys.executable, script, os.path.join(root, "monorepo.md")],
                           capture_output=True, text=True)
        assert "repo_structure=monorepo" in p.stdout, "the value is not reported to the caller"
        p = subprocess.run([sys.executable, script, os.path.join(root, "absent.md")],
                           capture_output=True, text=True)
        assert "repo_structure=single" in p.stdout and "default" in p.stdout, (
            "a defaulted value is not reported as defaulted, so a reader cannot tell a "
            "declaration from an assumption")

        # Item 53 gates item 54: <cwd> is meaningless outside a monorepo.
        gen = open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
                   encoding="utf-8").read()
        flat = prose(gen)
        assert re.search(r"single.{0,120}never emit <cwd>", flat, re.I), (
            "generate-tasks may emit <cwd> for a single-repo project, where it can only be "
            "wrong")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("`/prd` asks what the repository knows before asking the user", finding="P34")
def _():
    # Item 52. /crd has opened with this check since it was written; commands/prd.md mentioned
    # PROJECT.md zero times, so the two paths disagreed about whether knowing the project
    # matters. Greenfield describes the DOCUMENT, not the repository it lands in.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-project-context.py")
    assert os.path.isfile(script), "check-project-context.py is missing"

    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    init = prd[prd.find("## Initialization"):prd.find("## Workflow Phases")]
    assert "check-project-context.py" in init, (
        "the context check is not in Initialization, so it can be reached only after the "
        "interview has already asked what the stack should be")
    flat = " ".join(prd.split())
    assert re.search(r"follow\s*/\s*extend\s*/\s*override", flat, re.I), (
        "/prd never says what to do with context it finds")
    assert re.search(r"regardless of how Phase 2", flat, re.I), (
        "the check is not stated as unconditional, so it can be skipped by answering "
        "'greenfield' -- which is the omission a --greenfield flag would have caused")

    root = tempfile.mkdtemp(prefix="prd-ctx-")
    try:
        empty = os.path.join(root, "empty")
        os.makedirs(empty)
        p = subprocess.run([sys.executable, script, empty], capture_output=True, text=True)
        assert p.returncode == 0, f"an empty directory did not exit 0 (got {p.returncode})"

        # Context present, and current. Exit 3 is a branch, not a verdict: a PRD is never
        # refused because the repository has a PROJECT.md.
        ctx = os.path.join(root, "ctx")
        os.makedirs(ctx)
        for args_ in (["init", "-q"], ["config", "user.email", "t@e.invalid"],
                      ["config", "user.name", "T"],
                      ["commit", "-q", "--allow-empty", "-m", "base"]):
            subprocess.run(["git"] + args_, cwd=ctx, capture_output=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ctx,
                              capture_output=True, text=True).stdout.strip()
        with open(os.path.join(ctx, "PROJECT.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(f"<project-context><meta><name>Billing</name>"
                    f"<last-context-hash>{head}</last-context-hash></meta></project-context>\n")
        p = subprocess.run([sys.executable, script, ctx], capture_output=True, text=True)
        assert p.returncode == 3, f"context present did not exit 3 (got {p.returncode})"
        assert "Billing" in p.stdout, "the report does not name the project it found"
        assert "STALE" not in p.stdout, "a current PROJECT.md was reported as stale"

        # Stale must be named as stale -- a PRD written against an old description can
        # contradict code that already exists.
        with open(os.path.join(ctx, "PROJECT.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("<project-context><meta><name>Billing</name>"
                    "<last-context-hash>" + "0" * 40 + "</last-context-hash></meta>"
                    "</project-context>\n")
        p = subprocess.run([sys.executable, script, ctx], capture_output=True, text=True)
        assert p.returncode == 3 and "STALE" in p.stdout, (
            f"a stale PROJECT.md was not reported as stale:\n{p.stdout}")

        # It must never write. Updating PROJECT.md is /crd's job.
        before = open(os.path.join(ctx, "PROJECT.md"), "rb").read()
        subprocess.run([sys.executable, script, ctx], capture_output=True, text=True)
        assert open(os.path.join(ctx, "PROJECT.md"), "rb").read() == before, (
            "the context check modified PROJECT.md; it reports and never repairs")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def schema_registry():
    path = os.path.join(REPO, "tests", "fixture", "prd", "SCHEMAS.json")
    return path, json.load(open(path, encoding="utf-8"))


def current_fixture(project):
    """The named fixture project, in whichever schema version the registry calls current.

    Nothing may hardcode a version. Item 45 added a second one, and every path that named
    `schema-1` would have gone on testing the superseded copy while reporting on the current
    schema -- the registry exists to stop exactly that, and cannot if its readers ignore it.
    """
    _path, reg = schema_registry()
    return os.path.join(REPO, "tests", "fixture", "prd", reg["current"], project)


def fixture_digest(version):
    """sha256 over a version directory: sorted relative paths, `path NUL bytes NUL` each."""
    import hashlib
    root = os.path.join(REPO, "tests", "fixture", "prd", version)
    files = []
    for dirpath, _dirs, names in os.walk(root):
        for n in names:
            full = os.path.join(dirpath, n)
            files.append((os.path.relpath(full, root).replace(os.sep, "/"), full))
    h = hashlib.sha256()
    for rel, full in sorted(files):
        h.update(rel.encode("utf-8") + b"\0")
        h.update(open(full, "rb").read() + b"\0")
    return h.hexdigest()


@check("exactly one PRD schema is current, and each has its fixture", finding="P28")
def _():
    # Item 43. The fixture directory is versioned so that Phase 4's schema items can each land
    # by ADDING a schema-2 fixture beside schema-1, instead of breaking the suite in the same
    # commit as the schema change -- which is what items 1, 2, 5, 11, 33, 34 and 35 would
    # otherwise each have to do.
    path, reg = schema_registry()
    assert os.path.isfile(path), "tests/fixture/prd/SCHEMAS.json is missing"

    versions = reg.get("versions") or {}
    assert versions, "the registry lists no schema versions"

    current = [name for name, v in versions.items() if v.get("status") == "current"]
    assert len(current) == 1, (
        f"{len(current)} schemas are marked current ({current}); the end-to-end checks have "
        f"to run against exactly one, and item 24's comparison needs to know which")
    assert reg.get("current") == current[0], (
        f"the registry's `current` field says {reg.get('current')!r} but the version marked "
        f"current is {current[0]!r}")

    # Rule 1: one fixture per version the toolchain still accepts. A listed version with no
    # directory is a promise the repository cannot keep.
    root = os.path.join(REPO, "tests", "fixture", "prd")
    for name, v in versions.items():
        d = os.path.join(root, name)
        assert os.path.isdir(d), f"{name} is registered but {d} does not exist"
        for project in v.get("projects") or []:
            index = os.path.join(d, project, "index.md")
            assert os.path.isfile(index), f"{name}/{project} has no index.md"

    # And the reverse: a directory nobody registered is the decoration rule 1 exists to stop.
    on_disk = {n for n in os.listdir(root)
               if os.path.isdir(os.path.join(root, n)) and n.startswith("schema-")}
    unregistered = sorted(on_disk - set(versions))
    assert not unregistered, (
        f"schema fixture directories exist that the registry does not list: {unregistered}. "
        f"One fixture per accepted version -- an unlisted one is maintained by nobody")


@check("a generated manifest carries both versions, and they are different questions",
       finding="P28")
def _():
    # P28: `toolchain_version` is provenance, `schema_version` is compatibility. A patch
    # release moves the first and not the second, which is why item 24's compatibility
    # decision cannot read the first. Run the generator rather than reading it.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py")
    root = tempfile.mkdtemp(prefix="prd-manifest-")
    try:
        layer = os.path.join(root, "0-setup")
        os.makedirs(layer)
        with open(os.path.join(layer, "L0-001-thing.xml"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("<task><meta><id>L0-001</id><name>Thing</name>"
                    "<layer>0-setup</layer></meta></task>\n")

        p = subprocess.run([sys.executable, script, root], capture_output=True, text=True)
        assert p.returncode == 0, f"build-manifest.py failed: {p.stderr}"
        manifest = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))

        assert "schema_version" in manifest, (
            "the manifest carries no schema_version, so item 24 has nothing to compare and "
            "'refuse on a known incompatibility' cannot be implemented (P28)")
        assert "toolchain_version" in manifest, "the manifest lost its provenance stamp"
        assert manifest["schema_version"] != manifest["toolchain_version"], (
            "schema_version equals toolchain_version, which collapses the distinction P28 "
            "exists to draw: a patch release must move one and not the other")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the golden pair exists: a fixture in the previous schema and the current one",
       finding="P28")
def _():
    # The pair is what makes item 41's migration testable by COMPARISON -- run it over the old
    # fixture, assert the result equals the new one -- and item 24 exercisable at all, since
    # no artefact of an older schema exists anywhere in the repository today.
    #
    # This was marked expect_fail until item 45, which is the schema item that created the
    # second version. It fired as designed: registering schema-2 turned the check green, the
    # run failed with FIXED, and that was the signal to delete the marker rather than a
    # breakage. The comparison it unblocks is item 41's.
    _path, reg = schema_registry()
    versions = reg.get("versions") or {}
    assert len(versions) >= 2, (
        f"only {len(versions)} schema version(s) registered. A single version cannot be a "
        f"golden pair: there is nothing to migrate FROM and nothing for item 24 to refuse")

    frozen = [n for n, v in versions.items() if v.get("frozen")]
    assert frozen, ("no non-current fixture is marked frozen; rule 2 says a superseded "
                    "fixture changes only when the migration's expected output changes")


@check("an oversized PRD is refused before a prompt is built", finding="P5")
def _():
    # Item 18. Phase 2 used to send the whole PRD in one prompt -- ~174k tokens on the sample
    # corpus, to a 200k-window model, with no size check. The failure mode was a silently
    # truncated analysis.json, and everything downstream is built from that file.
    #
    # The refusal is run against a synthetic oversize feature, because both in-repo fixtures
    # are ~2k tokens and would pass whatever the script did.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-prd-size.py")
    assert os.path.isfile(script), "check-prd-size.py is missing"

    root = tempfile.mkdtemp(prefix="prd-size-")
    try:
        prd = os.path.join(root, "big")
        os.makedirs(os.path.join(prd, "features"))
        open(os.path.join(prd, "index.md"), "w", encoding="utf-8", newline="\n").write(
            "<prd><meta><slug>big</slug></meta></prd>\n")
        small = os.path.join(prd, "features", "small.md")
        open(small, "w", encoding="utf-8", newline="\n").write("<feature/>\n" + "x " * 500)
        huge = os.path.join(prd, "features", "huge.md")
        open(huge, "w", encoding="utf-8", newline="\n").write("<feature/>\n" + "x " * 200_000)

        p = subprocess.run([sys.executable, script, prd], capture_output=True, text=True)
        assert p.returncode == 1, f"an oversize feature was not refused (exit {p.returncode})"
        assert "REFUSED" in p.stderr and "huge.md" in p.stderr, (
            f"the refusal does not name the file that is too big:\n{p.stderr}")
        assert "small.md" not in p.stderr, "a file within budget was named in the refusal"
        # The contrast the finding is about must be reported, not just the per-prompt figure.
        assert "whole corpus" in p.stdout, (
            "the report does not say what one prompt would have carried before the split")

        # Within budget, the same tree passes -- the guard must not refuse on total size, only
        # on any single prompt. Splitting is exactly what makes a large corpus workable.
        os.remove(huge)
        for i in range(40):
            open(os.path.join(prd, "features", f"f{i}.md"), "w", encoding="utf-8",
                 newline="\n").write("<feature/>\n" + "x " * 20_000)
        p = subprocess.run([sys.executable, script, prd], capture_output=True, text=True)
        assert p.returncode == 0, (
            "a corpus that is large in TOTAL but fits per prompt was refused; that is the "
            "case item 18 exists to make workable, not to block")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("Phase 2 analyses per feature, and says so where it is instructed", finding="P5")
def _():
    # The script can only guard what the skills actually do. These assert the split is
    # specified at both ends -- the caller that fans out, and the skill that must refuse a
    # whole PRD if one arrives anyway.
    caller = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    analyzer = open(os.path.join(SKILLS, "breakdown-analyze-prd", "SKILL.md"),
                    encoding="utf-8").read()

    assert "check-prd-size.py" in caller, "/breakdown never runs the size check"
    # The INSTRUCTION must be gone; a quotation of it, under "this used to say", is how the
    # file explains itself and must survive. The difference is grammatical -- an imperative
    # line telling the reader to do it -- so test for that rather than for the words, or this
    # check fails the moment someone documents the history it exists to enforce.
    imperative = [ln for ln in caller.splitlines()
                  if re.match(r"^\s*(?:[-*]\s*)?(?:\*\*)?Invoke\b", ln)
                  and re.search(r"full PRD|whole PRD|entire PRD", ln, re.I)]
    assert not imperative, (
        "/breakdown still instructs sending the whole PRD in one prompt (P5):\n    "
        + "\n    ".join(imperative))
    assert re.search(r"index pass", caller, re.I) and re.search(r"per feature", caller, re.I), (
        "Phase 2 does not describe the index pass and the per-feature fan-out")
    assert "analysis.json" in caller, "Phase 2 no longer says where the merged analysis lands"

    # Whitespace-normalised: a prose assertion that breaks when someone re-wraps a paragraph
    # is a check pinned to formatting, which is the F3 mistake in miniature.
    flat = " ".join(analyzer.split())
    assert re.search(r"index\b.*\bfeature\b", flat, re.I), (
        "analyze-prd does not distinguish its two passes")
    assert re.search(r"stop and (say so|report)", flat, re.I), (
        "analyze-prd does not refuse a whole PRD arriving unsplit, so the split is advisory")
    assert "inferred_from" in analyzer, (
        "feature fragments carry no attribution, so the merge cannot say which feature "
        "produced an inferred model")


@check("`/prd`'s overwrite guard is an exit code, not a paragraph", finding="P16")
def _():
    # Item 9. Five prose guards in this repository became programs after being documented and
    # then ignored; /prd's Phase 8 pre-write check was the largest one left. Run both scripts
    # rather than reading them -- "the command mentions test -e" is a property the ignored
    # version also had.
    import shutil
    import tempfile

    writable = os.path.join(SKILLS, "breakdown", "scripts", "check-writable.py")
    listing = os.path.join(SKILLS, "breakdown", "scripts", "list-prds.py")
    for path in (writable, listing):
        assert os.path.isfile(path), f"{os.path.basename(path)} is missing"

    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    assert "check-writable.py" in prd, "/prd never runs the overwrite guard"
    assert "list-prds.py" in prd, "/prd never runs the PRD listing"
    # The prose it replaced must be gone, or both exist and the model may follow either.
    assert "test -e docs/prd/" not in prd, (
        "the old inline `test -e` guard is still in /prd; a guard and its replacement both "
        "present is worse than either alone")
    assert 'grep -l "<status>in-progress</status>"' not in prd, (
        "the old two-file grep is still in /prd")

    root = tempfile.mkdtemp(prefix="prd-guard-")
    try:
        def prd_dir(slug, index_status=None, next_status=None, features=0):
            d = os.path.join(root, "docs", "prd", slug)
            os.makedirs(os.path.join(d, "features"), exist_ok=True)
            if index_status is not None:
                open(os.path.join(d, "index.md"), "w", encoding="utf-8", newline="\n").write(
                    f"<prd><meta><name>{slug}</name>"
                    f"<status>{index_status}</status></meta></prd>\n")
            if next_status is not None:
                open(os.path.join(d, "what-next.md"), "w", encoding="utf-8",
                     newline="\n").write(f"<what-next><status>{next_status}</status>"
                                         f"</what-next>\n")
            for i in range(features):
                open(os.path.join(d, "features", f"f{i}.md"), "w", encoding="utf-8",
                     newline="\n").write("<feature/>\n")
            return d

        live = prd_dir("live-prd", "in-progress", "in-progress", features=2)
        fresh = os.path.join(root, "docs", "prd", "brand-new")

        # The guard refuses a collision, names what would go, and says how many.
        p = subprocess.run([sys.executable, writable, live], capture_output=True, text=True)
        assert p.returncode == 1, "the guard did not refuse an existing PRD"
        assert "REFUSED" in p.stderr and "index.md" in p.stderr and "f0.md" in p.stderr, (
            f"the refusal does not name the files at risk:\n{p.stderr}")

        # --resume is the only way past, and it has to be stated.
        p = subprocess.run([sys.executable, writable, live, "--resume"],
                           capture_output=True, text=True)
        assert p.returncode == 0, "--resume did not permit writing back"

        # A slug nobody has used is not a refusal.
        p = subprocess.run([sys.executable, writable, fresh], capture_output=True, text=True)
        assert p.returncode == 0, "the guard refused a PRD directory that does not exist"

        # F3 as a data defect: the two files disagreeing means a resume finds whichever it
        # reads first. --check has to fail on that, and on a PRD with no marker at all.
        prd_dir("split-brain", "in-progress", "defined")
        prd_dir("silent2", "defined", None)  # one file only is fine, not a disagreement
        # A PRD whose index.md exists but declares no status at all. Not the same as an empty
        # directory, which is correctly invisible: this one is a real PRD that `--resume`
        # cannot see.
        silent = os.path.join(root, "docs", "prd", "silent")
        os.makedirs(silent, exist_ok=True)
        open(os.path.join(silent, "index.md"), "w", encoding="utf-8", newline="\n").write(
            "<prd><meta><name>Silent</name></meta></prd>\n")
        p = subprocess.run([sys.executable, listing, os.path.join(root, "docs", "prd"),
                            "--check"], capture_output=True, text=True)
        assert p.returncode == 1, "a self-contradicting PRD passed --check"
        assert "split-brain" in p.stderr and "silent" in p.stderr
        assert "silent2" not in p.stderr, (
            "a PRD declaring its status in one file only was reported as a defect; that is "
            "the normal older layout F3 exists to keep readable")
        assert "DISAGREE" in p.stdout and "NO MARKER" in p.stdout
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the P1 fixture reads as a product, not as a test", finding="P1")
def _():
    # Item 21's input. Four features, one per tier, two criteria each, and slugs that cannot
    # occur by coincidence -- attribution is a string match until item 16 adds
    # <source-feature>, and a string match is only sound when the string is unique.
    #
    # The first version of this fixture EXPLAINED ITSELF -- the overview named the finding
    # under test, and the won't-have carried "**This feature is rejected and must not be
    # built.**" analyze-prd read all of it and wrote back "Deliberately obscure animal names
    # ... chosen to prevent accidental coincidental matching" and "must not appear in
    # generated tasks". The subject knew what was being measured and what a good answer
    # looked like, so the result was worthless. A fixture that describes the experiment is
    # part of the experiment.
    probe = current_fixture("staff-service")
    index = open(os.path.join(probe, "index.md"), encoding="utf-8").read()

    entries = re.findall(r'<feature priority="([a-z-]+)" file="features/([a-z-]+)\.md">', index)
    tiers = sorted(t for t, _ in entries)
    assert tiers == ["could-have", "must-have", "should-have", "wont-have"], (
        f"the probe must carry exactly one feature per tier, found {tiers}")

    for tier, slug in entries:
        path = os.path.join(probe, "features", f"{slug}.md")
        assert os.path.isfile(path), f"index names features/{slug}.md and it is not there"
        body = open(path, encoding="utf-8").read()
        assert f"<slug>{slug}</slug>" in body, f"{slug}.md does not declare its own slug"
        # Item 1 removed <priority> from the feature file: the index entry is the only place
        # a feature's tier is recorded. Asserting the two AGREE is no longer possible, and the
        # stronger claim replaces it -- the feature file must not carry a second copy at all,
        # because two writers for one fact is what item 1 was about.
        assert "<priority>" not in re.sub(r"<criterion\b[^>]*>", "", body), (
            f"{slug}.md carries a <priority> of its own. Priority lives on the index entry; a "
            f"copy here is the duplication item 1 removed, and nothing keeps the two in step")
        assert len(re.findall(r"<criterion\b", body)) == 2, (
            f"{slug}.md must carry exactly two criteria -- P5 says a bigger probe fails for "
            f"reasons that have nothing to do with what it measures")

    # The won't-have must be specified as well as the others -- a rejected feature that is
    # obviously unbuildable would be skipped for the wrong reason -- and must be rejected
    # ONLY by its priority. An instruction in the prose does the filtering the toolchain is
    # supposed to be measured on.
    wont = open(os.path.join(probe, "features", "quokka-telemetry.md"), encoding="utf-8").read()
    assert ('<feature priority="wont-have" file="features/quokka-telemetry.md">' in index), (
        "the index does not declare quokka-telemetry as wont-have, and since item 1 the index "
        "is the only place that declaration can live")
    body = re.sub(r"<priority>.*?</priority>", "", wont)
    for instruction in ("must not be built", "must not be implemented", "do not build",
                        "explicitly rejected", "out of scope", "not wanted"):
        assert instruction not in body.lower(), (
            f"the won't-have feature contains the instruction {instruction!r}. Rejection is "
            f"declared by <priority>wont-have</priority> and by nothing else, or the fixture "
            f"filters the feature itself and the run measures the fixture")
    lengths = {}
    for _tier, slug in entries:
        lengths[slug] = len(re.sub(r"<[^>]+>", " ", open(
            os.path.join(probe, "features", f"{slug}.md"), encoding="utf-8").read()).split())
    shortest = min(lengths.values())
    assert lengths["quokka-telemetry"] >= shortest, (
        f"the won't-have is the thinnest feature in the fixture {lengths}; it would be "
        f"skippable for being vague rather than for being rejected")

    # And nothing anywhere in the PRD may describe the experiment.
    for dirpath, _dirs, names in os.walk(probe):
        for name in names:
            text = open(os.path.join(dirpath, name), encoding="utf-8").read().lower()
            for leak in ("probe", "finding p1", "toolchain", "regression suite", "coincid",
                         "moscow tier", "breakdown cannot", "measure"):
                assert leak not in text, (
                    f"{name} mentions {leak!r}. The fixture is read by the agent under test; "
                    f"a PRD that explains what is being measured contaminates the measurement")


@check("the P1 probe's grader calls a vacuous run invalid, not clean", finding="P1")
def _():
    # The grader is exercised here, offline, so that the expensive path is not the only thing
    # that has ever run it. The case that matters is the third: a probe reporting "no
    # won't-have tasks" because nothing was generated has measured nothing, and that shape
    # has already produced two false passes in this phase.
    import shutil
    import tempfile

    probe = os.path.join(REPO, "tests", "probe-p1.py")
    assert os.path.isfile(probe), "tests/probe-p1.py is missing"

    root = tempfile.mkdtemp(prefix="prd-p1-")
    try:
        def task(where, tid, objective, requirements=""):
            # A task is attributed by its <name> and <objective> only. <requirements> is
            # written separately here because that is where a real run put "Do NOT add a
            # telemetry table", and counting that as derivation inverts the result.
            os.makedirs(where, exist_ok=True)
            with open(os.path.join(where, f"{tid}.xml"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write(f"<task><meta><id>{tid}</id><name>{objective}</name></meta>"
                        f"<objective>{objective}</objective>"
                        f"<requirements>{requirements}</requirements></task>\n")

        clean = os.path.join(root, "clean")
        task(clean, "L1-001", "zebra-signin stores a password hash",
             "Do NOT add a quokka-telemetry table; that feature is excluded")
        task(clean, "L2-001", "walrus-export returns text/csv")

        dirty = os.path.join(root, "dirty")
        task(dirty, "L1-001", "zebra-signin stores a password hash")
        task(dirty, "L2-003", "quokka-telemetry posts batches to the collector")

        nomust = os.path.join(root, "nomust")
        task(nomust, "L2-001", "walrus-export returns text/csv")

        empty = os.path.join(root, "empty")
        os.makedirs(empty)

        # `clean` carries a negative requirement naming the rejected feature and must still
        # grade 0: an instruction not to build something is not building it.
        expected = {clean: 0, dirty: 1, nomust: 2, empty: 2}
        for where, code in expected.items():
            p = subprocess.run([sys.executable, probe, "--grade", where],
                               capture_output=True, text=True)
            got = p.stdout + p.stderr
            assert p.returncode == code, (
                f"{os.path.basename(where)}: expected exit {code}, got {p.returncode}\n{got}")

        p = subprocess.run([sys.executable, probe, "--grade", dirty],
                           capture_output=True, text=True)
        assert "P1 CONFIRMED" in p.stderr, "a won't-have task was found and not called out"
        assert "L2-003" in p.stdout, "the violating task is not named"

        p = subprocess.run([sys.executable, probe, "--grade", empty],
                           capture_output=True, text=True)
        assert "INVALID" in p.stderr and "measures nothing" in p.stderr, (
            "an empty task set was not called invalid")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("a rename finishes, or leaves the PRD exactly as it was", finding="P27")
def _():
    # Item 42. The rename that prompted it was done correctly across 20 references in 8 files
    # and produced no evidence of that fact -- which is the defect. This runs the script over
    # a copy of the §5.1 fixture, with the two link shapes the corpus has and the fixture does
    # not, and asserts the three postconditions from the outside.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "rename-feature.py")
    assert os.path.isfile(script), "skills/breakdown/scripts/rename-feature.py is missing"
    src = current_fixture("link-shelf")
    assert os.path.isdir(src), "the §5.1 fixture PRD is missing"

    root = tempfile.mkdtemp(prefix="prd-rename-")
    try:
        prd = os.path.join(root, "link-shelf")
        shutil.copytree(src, prd)

        # Inbound links, both shapes, plus a prose mention that must NOT be rewritten.
        lst = os.path.join(prd, "features", "list-links.md")
        text = open(lst, encoding="utf-8").read().replace(
            "</description>",
            "\n  See [Tag links](tag-links.md) and [again](features/tag-links.md).\n"
            "  </description>", 1)
        open(lst, "w", encoding="utf-8", newline="\n").write(text)
        save = os.path.join(prd, "features", "save-link.md")
        text = open(save, encoding="utf-8").read().replace(
            "</description>", "\n  Tagging is specified in tag-links, in prose.\n  </description>", 1)
        open(save, "w", encoding="utf-8", newline="\n").write(text)

        p = subprocess.run([sys.executable, script, prd, "tag-links", "label-links"],
                           capture_output=True, text=True)
        assert p.returncode == 0, f"the rename failed: {p.stdout}\n{p.stderr}"

        # Postcondition 2: no file under the old slug.
        assert not os.path.exists(os.path.join(prd, "features", "tag-links.md"))
        assert os.path.isfile(os.path.join(prd, "features", "label-links.md"))

        # Postcondition 1: nothing *resolves* to the old slug any more -- checked here rather
        # than trusting the script's own report of itself.
        resolving = re.compile(r"features/tag-links\.md|<slug>\s*tag-links\s*</slug>"
                               r"|\]\(\s*tag-links\.md\s*\)")
        for dirpath, _, names in os.walk(prd):
            for name in names:
                if name.endswith(".md"):
                    body = open(os.path.join(dirpath, name), encoding="utf-8").read()
                    assert not resolving.search(body), f"{name} still resolves to tag-links"

        # Postcondition 3: exactly one index entry, exactly one file.
        index = open(os.path.join(prd, "index.md"), encoding="utf-8").read()
        assert index.count('file="features/label-links.md"') == 1
        owners = [n for n in os.listdir(os.path.join(prd, "features"))
                  if "<slug>label-links</slug>" in
                  open(os.path.join(prd, "features", n), encoding="utf-8").read()]
        assert owners == ["label-links.md"], f"the new slug is claimed by {owners}"

        # what-next.md is the sixth site. The plan's item 42 lists five and the fixture is
        # where the sixth turned up -- and item 11 then changed its SHAPE, from a `ref=` path
        # to a `slug=` row in the derived <authoring-gaps>. So the assertion is that the file
        # was carried, not that one spelling of it was: three more `slug=` sites arrived with
        # the schema-4 group, which is the argument for a postcondition over a list.
        wn = open(os.path.join(prd, "what-next.md"), encoding="utf-8").read()
        assert "label-links" in wn and "tag-links" not in wn, (
            "what-next.md was not carried. Its feature references are `<gap slug=>` rows since "
            "item 11, and a rename has to carry every shape of reference or the file is stale")

        # Prose is reported, not rewritten.
        assert "MENTION" in p.stdout and "in prose" in p.stdout, (
            f"the prose mention was not reported: {p.stdout}")
        assert "tag-links, in prose" in open(save, encoding="utf-8").read(), (
            "the script rewrote a sentence; it must only rewrite references")

        # And the half that matters for item 41: a failed postcondition must roll back. Two
        # files claiming one slug is the cheapest way to make postcondition 3 fail after the
        # writes have already happened.
        dup = os.path.join(root, "dup")
        shutil.copytree(src, dup)
        f = os.path.join(dup, "features", "list-links.md")
        body = open(f, encoding="utf-8").read().replace("<slug>list-links</slug>",
                                                        "<slug>saved-link</slug>")
        open(f, "w", encoding="utf-8", newline="\n").write(body)

        before = {}
        for dirpath, _, names in os.walk(dup):
            for name in names:
                full = os.path.join(dirpath, name)
                before[os.path.relpath(full, dup)] = open(full, "rb").read()

        p = subprocess.run([sys.executable, script, dup, "save-link", "saved-link"],
                           capture_output=True, text=True)
        assert p.returncode == 1, "a failing postcondition did not refuse"
        assert "POSTCONDITION FAILED" in p.stderr and "rolled back" in p.stderr

        after = {}
        for dirpath, _, names in os.walk(dup):
            for name in names:
                full = os.path.join(dirpath, name)
                after[os.path.relpath(full, dup)] = open(full, "rb").read()
        assert before == after, (
            "a failed rename left the PRD changed. Every byte must be as it was found, or "
            "the operator is told nothing happened while something did")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the ledger records what was verified, not that it was", finding="P37")
def _():
    # Item 55. `"verified":true` invited the stronger reading: execute-verify runs the task's
    # OWN declared steps, and never the project's build. A task that merges green and breaks
    # CI was indistinguishable from one that did not, and the ledger was the thing implying
    # otherwise. The entry now names its scope.
    #
    # Run rather than read, because the assertion is about the bytes appended to the ledger.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "execute-merge", "scripts", "record-task.sh")
    assert os.path.isfile(script), "skills/execute-merge/scripts/record-task.sh is missing"
    sh = shutil.which("sh")
    assert sh, "sh is not on PATH; the execute pipeline's own scripts could not run either"

    body = open(script, encoding="utf-8").read()
    assert '"verified":true' not in body.replace(" ", ""), (
        "record-task.sh still writes a bare `verified: true`, which claims more than was run")

    root = tempfile.mkdtemp(prefix="prd-ledger-")
    try:
        def git(*args):
            return subprocess.run(["git"] + list(args), cwd=root,
                                  capture_output=True, text=True)

        git("init", "-q")
        git("config", "user.email", "t@example.invalid")
        git("config", "user.name", "T")
        git("commit", "-q", "--allow-empty", "-m", "base")
        sha = git("rev-parse", "HEAD").stdout.strip()

        p = subprocess.run([sh, script, root, "link-shelf", "L1-001", sha, "2"],
                           capture_output=True, text=True)
        assert p.returncode == 0, f"record-task.sh failed on a real commit: {p.stderr}"

        entries = open(os.path.join(root, ".execute", "link-shelf", "ledger.jsonl"),
                       encoding="utf-8").read().strip().splitlines()
        assert len(entries) == 1, f"expected one ledger entry, got {len(entries)}"
        entry = json.loads(entries[0])

        assert entry["verified"] == "task-steps", (
            f"the ledger says verified={entry['verified']!r}; it must name what ran, and the "
            f"only thing that ran is the task's own declared steps")
        assert entry["commit"] == sha and entry["task_id"] == "L1-001"
        assert entry["attempts"] == 2, "attempts was not carried through"

        # The rule the field depends on: an entry is never written for a commit that is not
        # there. A named verification of a merge that did not happen is worse, not better.
        p = subprocess.run([sh, script, root, "link-shelf", "L1-002", "0" * 40],
                           capture_output=True, text=True)
        assert p.returncode != 0, "a commit that does not exist was recorded anyway"
        after = open(os.path.join(root, ".execute", "link-shelf", "ledger.jsonl"),
                     encoding="utf-8").read().strip().splitlines()
        assert len(after) == 1, "the refused entry was appended regardless"
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the completion report does not imply a build it never ran", finding="P37")
def _():
    # The other half of P37. "44/44 tasks completed" is a claim about merges that every
    # reader hears as a claim about the build, and the report is where that costs most.
    body = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    assert re.search(r"^Verified: .*declared steps", body, re.M), (
        "the completion report does not state what was verified")
    assert re.search(r"^Not run: .*(build|test suite)", body, re.M), (
        "the completion report does not state what was NOT run")


@check("`<cwd>` has a producer, two readers, and a guard that runs", finding="P36")
def _():
    # Item 54. Verification used to run at the worktree root and nowhere else, so a monorepo
    # task had to write `cd packages/billing && pytest` inside each command string -- which
    # works in one runner and nowhere else.
    #
    # The element is checked in both directions, which is item 23's rule: a reader with no
    # producer is as broken as a producer with no reader, and `<cwd>` would have shipped with
    # two readers and nothing writing it if nobody looked.
    spec = open(os.path.join(SKILLS, "breakdown", "references", "task-format-spec.md"),
                encoding="utf-8").read()
    verify = open(os.path.join(SKILLS, "execute-verify", "SKILL.md"), encoding="utf-8").read()
    implementer = open(os.path.join(AGENTS, "task-implementer.md"), encoding="utf-8").read()
    generator = open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
                     encoding="utf-8").read()

    assert "<cwd>" in spec, "task-format-spec.md does not declare <cwd>"
    assert "cwd" in verify, "execute-verify does not read <cwd>"
    assert "cwd" in implementer, "the implementer does not read <cwd>"
    assert "cwd" in generator, "nothing produces <cwd> -- it would ship read-only"

    # The spec has to say the two things that make it safe, or the readers are guessing.
    assert re.search(r"relative to the worktree", spec, re.I), (
        "the spec does not say <cwd> is relative to the worktree root")
    assert re.search(r"files-to-create.*worktree root|worktree root.*files-to-create",
                     spec, re.I | re.S), (
        "the spec does not say whether <files-to-create> is relative to <cwd>")

    # And the guard is EXECUTED, not read. `sh` is already a hard dependency of this toolchain
    # -- preflight.sh, create-worktree.sh and merge-task.sh are how /execute works -- so a box
    # without it cannot run the pipeline either.
    import shutil
    import tempfile
    sh = shutil.which("sh")
    assert sh, "sh is not on PATH; the execute pipeline's own scripts could not run either"

    block = None
    for candidate in re.findall(r"```bash\s*\n(.*?)\n```", verify, re.S):
        if "REFUSED: <cwd>" in candidate and "case " in candidate:
            block = candidate
            break
    assert block, "execute-verify states no runnable guard for <cwd>"

    # Substitute the skill's placeholders for shell variables. Nothing else is changed: the
    # lines under test are the lines a model is told to run.
    script = block.replace("{worktree_path}", '$WT').replace("{cwd}", '$CWD')
    script += '\necho "LANDED:$(pwd)"\n'

    root = tempfile.mkdtemp(prefix="prd-cwd-")
    try:
        # The worktree is a level down, and `outside/` is a real directory beside it. That
        # matters: an escaping <cwd> has to point somewhere that EXISTS, or removing the
        # escape branch still produces a refusal -- from `cd` failing -- and the check passes
        # against a guard that no longer guards. That false pass happened once here.
        wt = os.path.join(root, "wt")
        os.makedirs(os.path.join(wt, "packages", "billing"))
        os.makedirs(os.path.join(root, "outside"))

        cases = [
            ("", "LANDED", "an absent <cwd> must land at the worktree root"),
            ("packages/billing", "LANDED", "a plain relative <cwd> must be accepted"),
            ("/etc", "must be relative", "an absolute <cwd> must be refused"),
            ("C:/Windows", "must be relative", "a drive-letter <cwd> must be refused"),
            ("../outside", "must not escape", "a <cwd> escaping to a real directory must be "
                                              "refused by the guard, not by cd failing"),
            ("packages/../packages/billing", "must not escape",
             "a `..` that resolves back inside must still be refused, not normalised"),
            ("packages/nope", "does not exist", "a <cwd> that does not exist must be refused"),
        ]
        for value, expected, why in cases:
            env = dict(os.environ, WT=wt.replace("\\", "/"), CWD=value)
            p = subprocess.run([sh, "-c", script], capture_output=True, text=True, env=env)
            got = (p.stdout + p.stderr).strip()
            assert expected in got, f"{why}; <cwd>={value!r} gave: {got[:160]}"
            if expected != "LANDED":
                assert p.returncode != 0, f"{why}; it refused but exited 0"
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("dangling ADR / OQ citations are refused, and named", finding="P24")
def _():
    # Item 39. The suite is otherwise static, and this one runs a script -- which is safe in a
    # way running a skill is not: check-references.py reads a directory and returns an exit
    # code. It creates nothing, so there is no repository for it to damage.
    #
    # It is run rather than grepped because the assertion that matters is not "the script
    # mentions ADR" -- it is that a planted dangling citation comes back named. A validator
    # that exits 0 on everything passes every static check ever written about it.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-references.py")
    assert os.path.isfile(script), "skills/breakdown/scripts/check-references.py is missing"

    root = tempfile.mkdtemp(prefix="prd-refs-")
    try:
        prd = os.path.join(root, "prd", "link-shelf")
        adr = os.path.join(root, "architecture", "decisions")
        os.makedirs(os.path.join(prd, "features"))
        os.makedirs(adr)

        def write(path, text):
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)

        write(os.path.join(prd, "index.md"),
              "# Link Shelf\nSettled by ADR-003. Superseded elsewhere: ADR-007.\nOpen: OQ-012.\n")
        write(os.path.join(prd, "features", "tagging.md"),
              "# Tagging\nPer ADR-999 a join table. See OQ-004 and OQ-777.\n")
        write(os.path.join(adr, "003-join-table.md"),
              "# Tags are a join table\n**Status:** Accepted\n"
              "**Drives:** [Tagging](../../prd/link-shelf/features/tagging.md), "
              "[Gone](../../prd/link-shelf/features/removed.md)\n")
        write(os.path.join(adr, "007-sqlite.md"), "# SQLite\n**Status:** Superseded by ADR-011\n")
        write(os.path.join(adr, "011-postgres.md"), "# Postgres\n**Status:** Accepted\n")
        write(os.path.join(root, "architecture", "open-questions.md"),
              "# Open Questions\n## OQ-004 -- ordering? Resolved 2026-03-02 by ADR-003\n"
              "## OQ-012 -- which auth provider?\n")

        p = subprocess.run([sys.executable, script, prd], capture_output=True, text=True)
        out = p.stdout

        assert p.returncode == 1, f"a PRD with three dangling references exited {p.returncode}"

        # Each dangling reference is named, as written, with somewhere to look.
        for needle in ("ADR-999", "OQ-777", "removed.md"):
            assert needle in out, f"the report does not name {needle}:\n{out}"
        assert "features" in out and ":2:" in out, (
            f"the report names no file and line for a citation:\n{out}")

        # A superseded record and a resolved question are reported, and do NOT refuse: both
        # still exist, and citing one is a judgement call rather than a defect.
        assert "ADR-007 is superseded by ADR-011" in out, f"supersession not reported:\n{out}"
        assert "OQ-004" in out and "Resolved" in out, f"resolution not reported:\n{out}"

        # Citations are echoed as written. ADR-007 and ADR-7 are the same record, and a report
        # that renames one sends a reader looking for a string that is not in the file.
        assert "ADR-7 " not in out and "OQ-4 " not in out, (
            f"the report strips leading zeros from citations:\n{out}")

        # With the dangling three repaired, the same tree passes -- warnings and all.
        write(os.path.join(prd, "features", "tagging.md"),
              "# Tagging\nPer ADR-003 a join table. See OQ-004 and OQ-012.\n")
        write(os.path.join(adr, "003-join-table.md"),
              "# Tags are a join table\n**Status:** Accepted\n"
              "**Drives:** [Tagging](../../prd/link-shelf/features/tagging.md)\n")
        p = subprocess.run([sys.executable, script, prd], capture_output=True, text=True)
        assert p.returncode == 0, f"a PRD with no dangling references exited {p.returncode}"

        # And a citation with nowhere to resolve against is an error, not a quiet pass. A
        # validator that goes green because it could not find the register is decorative.
        lonely = os.path.join(root, "lonely")
        os.makedirs(lonely)
        shutil.copy(os.path.join(prd, "index.md"), lonely)
        p = subprocess.run([sys.executable, script, lonely], capture_output=True, text=True)
        assert p.returncode == 1, "citations with no decision directory exited 0"
        assert "--adr-dir" in p.stdout, "the refusal does not name the flag that would fix it"
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("both ends of the pipeline call the reference check", finding="P24")
def _():
    # Item 39's own argument, applied to itself: a script nothing invokes is the producer
    # without a reader that this plan exists to describe. /breakdown must refuse on it;
    # /prd runs it as early warning while the author is still in the conversation.
    breakdown = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    assert "check-references.py" in breakdown, "/breakdown never runs the reference check"
    assert "check-references.py" in prd, "/prd never runs the reference check"
    # The probe established that CLAUDE_PLUGIN_ROOT is expanded where the command is written
    # and is NOT exported to the spawned shell, so the path has to be passed as an argument.
    assert "${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/check-references.py" in prd, (
        "/prd invokes the script by a path the harness will not expand")


@check("state-schema.md documents the file write-state.py actually writes", finding="P28")
def _():
    # A reference that describes a different document from the one the producer emits is the
    # drift this repository keeps finding in other people's artefacts. It was live here: the
    # reference said schema_version 2.0 and hand-maintained `options`, `worktrees` and
    # `current_layer`; the script writes 3.0 and none of them. Compare the two mechanically
    # rather than by reading, because reading is what missed it for three schema revisions.
    ws = os.path.join(SKILLS, "execute", "scripts", "write-state.py")
    doc_path = os.path.join(SKILLS, "execute", "references", "state-schema.md")
    assert os.path.isfile(doc_path), "skills/execute/references/state-schema.md is missing"
    doc = open(doc_path, encoding="utf-8").read()

    # The writer's own dict literal, not a copy of it kept in sync by hand.
    written = None
    for node in ast.walk(ast.parse(open(ws, encoding="utf-8").read())):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                and any(isinstance(t, ast.Name) and t.id == "state" for t in node.targets)):
            written = node.value
    assert written is not None, "no `state = {...}` literal found in write-state.py"
    writer_keys = [k.value for k in written.keys if isinstance(k, ast.Constant)]
    writer_version = next(
        v.value for k, v in zip(written.keys, written.values)
        if isinstance(k, ast.Constant) and k.value == "schema_version")

    # The documented example is the ```json block that parses as an object carrying a version.
    documented = None
    for block in re.findall(r"```json\s*\n(.*?)\n```", doc, re.S):
        try:
            obj = json.loads(block)
        except Exception:
            continue
        if isinstance(obj, dict) and "schema_version" in obj:
            documented = obj
            break
    assert documented is not None, (
        "state-schema.md has no complete ```json example carrying schema_version")

    missing = [k for k in writer_keys if k not in documented]
    extra = [k for k in documented if k not in writer_keys]
    assert not missing and not extra, (
        "state-schema.md and write-state.py disagree about the root fields"
        + (f"\n    written, undocumented: {missing}" if missing else "")
        + (f"\n    documented, never written: {extra}" if extra else ""))

    # Every version the reference states -- in the example and in the prose above it.
    stated = (set(re.findall(r'"schema_version"\s*:\s*"([^"]+)"', doc))
              | set(re.findall(r"Current version:\s*`([^`]+)`", doc)))
    assert stated == {writer_version}, (
        f"write-state.py writes schema_version {writer_version!r}; "
        f"state-schema.md states {sorted(stated)}")

    # Fields 2.0 carried and 3.0 does not, at a nesting the key comparison cannot reach.
    gone = [f for f in ("commits", "errors", "retry_feedback", "elapsed_seconds",
                        "total_retries", "worktree_path")
            if f'"{f}"' in json.dumps(documented)]
    assert not gone, f"the documented example still carries 2.0 fields: {gone}"


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


@check("the merge is executed by one script, not described", finding="F17")
def _():
    # Item 4.12's structural half: git operations in one place with one owner. The merge was
    # the last git sequence still spelled out in prose -- twelve commands across ten steps --
    # and every other one became a script because the described version failed: `-b` dropped
    # from `git worktree add` by six agents out of six (F18), a run that walked up out of the
    # target and merged into a repository it had just created (F19).
    import shutil
    import stat
    import tempfile

    script = os.path.join(SKILLS, "execute-merge", "scripts", "merge-task.sh")
    assert os.path.isfile(script), "skills/execute-merge/scripts/merge-task.sh is missing"

    merge_md = os.path.join(SKILLS, "execute-merge", "SKILL.md")
    md = open(merge_md, encoding="utf-8").read()
    assert "merge-task.sh" in md, "execute-merge never calls the script, so the merge is prose again"

    # The point is that the commands are no longer *here* to be retyped. A `git merge` or
    # `git worktree remove` line in an instruction file is an invitation to run it by hand
    # from whatever directory the model happens to be in, which is how F19 happened.
    banned = re.compile(r"^\s*git\s+(merge|checkout|worktree|branch|commit|add)\b")
    bad = [f"{i}: {l.strip()[:90]}"
           for i, l in enumerate(md.splitlines(), 1) if banned.search(l)]
    assert not bad, ("execute-merge spells out git commands again; call merge-task.sh:\n    "
                     + "\n    ".join(bad))

    # The ledger must be written by the merge script, and the slug it needs must actually be
    # threaded to it. It was an undeclared input for four runs.
    body = open(script, encoding="utf-8").read()
    assert "record-task.sh" in body, (
        "merge-task.sh does not record the merge, so a merged task stays invisible to resume")
    assert body.index("record-task.sh") < body.index("worktree remove"), (
        "merge-task.sh cleans up before recording; a cleanup failure would then lose a "
        "completed task")

    layer = open(os.path.join(SKILLS, "execute-layer", "SKILL.md"), encoding="utf-8").read()
    ex = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    def declares(text, flag):
        return any(l.lstrip().startswith(f"| `{flag}") for l in text.splitlines())

    def passes(text, skill, flag):
        return any(f"/{skill} " in l and flag in l for l in text.splitlines())

    assert declares(md, "--prd-slug"), "execute-merge does not declare --prd-slug"
    assert declares(layer, "--prd-slug"), "execute-layer does not declare --prd-slug"
    assert passes(layer, "execute-merge", "--prd-slug"), (
        "execute-layer never passes --prd-slug on, so merge-task.sh cannot name the ledger")
    assert passes(ex, "execute-layer", "--prd-slug"), (
        "execute never passes --prd-slug down, so the ledger is unnamed")

    if not shutil.which("git") or not shutil.which("sh"):
        return  # nothing to run the guard with; the static half above still applied

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    create = os.path.join(SKILLS, "execute-batch", "scripts", "create-worktree.sh")
    root = tempfile.mkdtemp(prefix="merge-task-check-")
    try:
        app = os.path.join(root, "app")
        wt = os.path.join(root, "wt")
        os.makedirs(app)

        def g(*args, cwd=app):
            return subprocess.run(["git", "-C", cwd, *args], capture_output=True,
                                  text=True, timeout=60)

        # Base branch is `trunk`, never `main` -- F1 is that assumption.
        for args in (["init", "-q", "-b", "trunk", "."],
                     ["config", "user.email", "t@t.invalid"], ["config", "user.name", "T"]):
            g(*args)
        open(os.path.join(app, "README.md"), "w").write("base")
        g("add", "-A")
        g("commit", "-qm", "init")

        taskfile = os.path.join(root, "L1-001.xml")
        open(taskfile, "w").write(
            "<task><meta><id>L1-001</id><name>Create enums</name>"
            "<layer>1-foundation</layer></meta></task>")

        def make_task(tid, fname, content):
            subprocess.run(["sh", create, app, tid, wt, "trunk"],
                           capture_output=True, text=True, timeout=60)
            d = os.path.join(wt, tid)
            open(os.path.join(d, fname), "w").write(content)
            g("add", "-A", cwd=d)
            g("commit", "-qm", f"[{tid}] work", cwd=d)
            return d

        def merge(tid, wtpath, tf=None, base="trunk"):
            p = subprocess.run(["sh", script, app, "demo", tid, wtpath, tf or taskfile, base],
                               capture_output=True, text=True, timeout=120)
            return p.returncode, (p.stdout or "") + (p.stderr or "")

        d1 = make_task("L1-001", "one.txt", "one")
        rc, out = merge("L1-001", d1)
        assert rc == 0, f"merge of a clean task failed: {out[-300:]}"

        merges = g("log", "--merges", "--oneline").stdout.strip().splitlines()
        assert len(merges) == 1, f"expected exactly 1 merge commit, got {len(merges)}"
        ledger = os.path.join(app, ".execute", "demo", "ledger.jsonl")
        assert os.path.isfile(ledger), "the merge was not recorded in the ledger"
        entries = [l for l in open(ledger, encoding="utf-8").read().splitlines() if l.strip()]
        assert len(entries) == 1, f"expected 1 ledger entry, got {len(entries)}"
        assert g("rev-parse", "HEAD").stdout.strip() in entries[0], (
            "the ledger records a SHA that is not the merge commit")
        assert not os.path.isdir(d1), "the worktree was not cleaned up after a successful merge"

        # The merge QUEUE: two tasks branched from the same base, different files, merged one
        # after the other. This is what a parallel batch produces, and it is the case the
        # brownfield run could not reach -- every layer there held exactly one task, so
        # merge-task.sh was only ever called once per batch. The second merge here starts from
        # a base that the first has already moved.
        base_before = g("rev-parse", "HEAD").stdout.strip()
        q1 = make_task("L2-001", "alpha.txt", "alpha")
        q2 = make_task("L2-002", "beta.txt", "beta")
        assert g("rev-parse", "HEAD").stdout.strip() == base_before, (
            "the test branched the second task from a moved base; it no longer models a batch")
        rc, out = merge("L2-001", q1)
        assert rc == 0, f"first merge of the queue failed: {out[-300:]}"
        moved = g("rev-parse", "HEAD").stdout.strip()
        assert moved != base_before, "the first merge did not move the base"
        rc, out = merge("L2-002", q2)
        assert rc == 0, (
            "the second merge in the queue failed against a base the first had moved -- "
            f"this is every batch of more than one task:\n{out[-300:]}")
        for f in ("alpha.txt", "beta.txt"):
            assert os.path.isfile(os.path.join(app, f)), (
                f"{f} is missing after both merges; the queue lost a task's work")
        entries = [l for l in open(ledger, encoding="utf-8").read().splitlines() if l.strip()]
        assert len(entries) == 3, f"expected 3 ledger entries after the queue, got {len(entries)}"

        # A conflict must abort, preserve the worktree, and record NOTHING. Recording a
        # conflicted merge would make resume skip a task that never landed.
        d2 = make_task("L1-002", "clash.txt", "A")
        d3 = make_task("L1-003", "clash.txt", "B")
        rc, out = merge("L1-002", d2)
        assert rc == 0, f"second clean merge failed: {out[-300:]}"

        # Relative, not a hard-coded total: an absolute count here silently went stale the
        # moment a case was inserted above it, and reported a defect that did not exist.
        before_conflict = len(
            [l for l in open(ledger, encoding="utf-8").read().splitlines() if l.strip()])
        rc, out = merge("L1-003", d3)
        assert rc == 3, f"a conflicting merge returned {rc}, expected 3: {out[-300:]}"
        assert os.path.isdir(d3), "a conflicting merge destroyed the worktree holding the work"
        assert not os.path.isfile(os.path.join(app, ".git", "MERGE_HEAD")), (
            "a conflicting merge was left in progress rather than aborted")
        entries = [l for l in open(ledger, encoding="utf-8").read().splitlines() if l.strip()]
        assert len(entries) == before_conflict, (
            f"a conflicted merge was recorded in the ledger ({before_conflict} -> "
            f"{len(entries)}) -- resume would skip a task that never landed")

        # Refusals: nothing merged, nothing recorded, HEAD untouched.
        head = g("rev-parse", "HEAD").stdout.strip()
        for label, args in (
            ("a worktree that does not exist", ("L1-004", os.path.join(root, "nope"))),
            ("a target that is not a repository", ("L1-003", d3)),
        ):
            if label.startswith("a target"):
                p = subprocess.run(["sh", script, root, "demo", "L1-003", d3, taskfile, "trunk"],
                                   capture_output=True, text=True, timeout=60)
                rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
            else:
                rc, out = merge(*args)
            assert rc == 1, f"expected refusal (1) for {label}, got {rc}: {out[:200]}"
            assert "REFUSED" in out, f"refusal of {label} does not say REFUSED: {out[:200]}"

        assert g("rev-parse", "HEAD").stdout.strip() == head, (
            "a refused merge still moved HEAD")
        entries = [l for l in open(ledger, encoding="utf-8").read().splitlines() if l.strip()]
        assert len(entries) == before_conflict, "a refused merge still wrote to the ledger"
    finally:
        rmtree(root)


@check("last-context-hash is stamped by the caller, not invented by the agent", finding="F23")
def _():
    # The one CRD run that has ever happened left <last-context-hash>current-HEAD</...> in the
    # fixture's PROJECT.md -- the literal placeholder, overwriting a valid hash. The finalizer
    # declares `tools: Read Write Glob`, so it cannot run `git rev-parse` and never could.
    # Downstream, `git diff current-HEAD..HEAD` is `fatal: ambiguous argument`, and both update
    # paths treat an unusable hash as "fall back to full investigation" -- the most expensive
    # operation in the CRD half, chosen silently, forever.
    import shutil
    import stat
    import tempfile

    script = os.path.join(SKILLS, "execute", "scripts", "check-project-md.py")
    assert os.path.isfile(script), "skills/execute/scripts/check-project-md.py is missing"

    fin = open(os.path.join(AGENTS, "project-context-finalizer.md"), encoding="utf-8").read()
    templated = [f"{i}: {l.strip()[:90]}"
                 for i, l in enumerate(fin.splitlines(), 1)
                 if "<last-context-hash>" in l and "{" in l]
    assert not templated, (
        "the finalizer is told to fill in <last-context-hash> from a placeholder, and it has "
        "no Bash to compute one with -- that is how the literal string `current-HEAD` got "
        "into PROJECT.md:\n    " + "\n    ".join(templated))

    # Assert the COMMAND, not the prose about it. `"--stamp-hash" in ex` was true from the
    # paragraph explaining the flag, so deleting it from the invocation slipped straight past
    # -- the same weak-assertion shape as F15 and as the --prd-slug check in 4.12.
    ex_lines = open(os.path.join(SKILLS, "execute", "SKILL.md"),
                    encoding="utf-8").read().splitlines()
    stamped_at = [i for i, l in enumerate(ex_lines)
                  if "check-project-md.py" in l and "--stamp-hash" in l]
    assert stamped_at, (
        "no check-project-md.py invocation in execute passes --stamp-hash, so nothing ever "
        "writes a real hash -- describing the flag is not running it")
    committed_at = [i for i, l in enumerate(ex_lines)
                    if 'commit -m "docs: Update PROJECT.md' in l]
    assert committed_at, "execute no longer commits PROJECT.md"
    assert stamped_at[0] < committed_at[0], (
        "execute stamps the hash after committing PROJECT.md, so the stamp is never committed")

    if not shutil.which("git"):
        return

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    PROJECT_MD = """# Project

<project-context>
  <meta>
    <name>demo</name>
    <last-updated>2026-01-01T00:00:00Z</last-updated>
    <last-context-hash>PLACEHOLDER</last-context-hash>
  </meta>
  <features><feature id="a"><name>A</name></feature></features>
  <api-registry><endpoint path="/a"/></api-registry>
  <schema-registry><model name="A"/></schema-registry>
</project-context>
"""

    root = tempfile.mkdtemp(prefix="context-hash-check-")
    try:
        app = os.path.join(root, "app")
        os.makedirs(app)

        def g(*a):
            return subprocess.run(["git", "-C", app, *a], capture_output=True,
                                  text=True, timeout=60)

        for a in (["init", "-q", "-b", "trunk", "."],
                  ["config", "user.email", "t@t.invalid"], ["config", "user.name", "T"]):
            g(*a)
        open(os.path.join(app, "code.py"), "w").write("x = 1\n")
        g("add", "-A")
        g("commit", "-qm", "code")

        def run(*flags):
            p = subprocess.run([sys.executable, script, app, *flags],
                               capture_output=True, text=True, timeout=60)
            return p.returncode, (p.stdout or "") + (p.stderr or "")

        def write(hash_value):
            open(os.path.join(app, "PROJECT.md"), "w", encoding="utf-8").write(
                PROJECT_MD.replace("PLACEHOLDER", hash_value))

        # The exact string the real run produced must be rejected, not silently believed.
        write("current-HEAD")
        rc, out = run("--status")
        assert rc == 1, f"a placeholder hash was accepted as usable (exit {rc}): {out[:200]}"
        assert "UNUSABLE" in out, f"unusable hash not reported as such: {out[:200]}"

        # Stamp, then commit PROJECT.md -- the real sequence. The hash is one behind HEAD by
        # construction, and that must NOT read as stale.
        rc, out = run("--fix", "--stamp-hash")
        assert rc == 0, f"stamping failed: {out[:300]}"
        stamped = subprocess.run(["git", "-C", app, "rev-parse", "HEAD"],
                                 capture_output=True, text=True, timeout=60).stdout.strip()
        assert stamped in open(os.path.join(app, "PROJECT.md"), encoding="utf-8").read(), (
            "--stamp-hash did not write HEAD into the file")

        g("add", "-A")
        g("commit", "-qm", "docs: Update PROJECT.md")
        head = subprocess.run(["git", "-C", app, "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=60).stdout.strip()
        assert head != stamped, "the test did not actually advance HEAD; it proves nothing"

        rc, out = run("--status")
        assert rc == 0, (
            "the context reads as STALE immediately after being written -- the off-by-one is "
            f"back. A PROJECT.md-only commit is not a code change:\n{out[:300]}")
        assert "stale=no" in out, f"expected stale=no, got: {out[:200]}"

        # A real code change must still register.
        open(os.path.join(app, "code.py"), "a").write("y = 2\n")
        g("add", "-A")
        g("commit", "-qm", "feat: change code")
        rc, out = run("--status")
        assert rc == 3, f"a real code change did not read as stale (exit {rc}): {out[:200]}"
        assert "stale=yes" in out and "code.py" in out, f"unexpected status output: {out[:200]}"
    finally:
        rmtree(root)


@check("no generated output committed under skills/", finding="F4")
def _():
    bad = [rel for rel, _t in all_tracked_text()
           if re.match(r"^skills/[^/]+/output/", rel)]
    assert not bad, ("generated artefacts committed into the toolchain tree:\n    "
                     + "\n    ".join(bad))


@check("nothing tracked is also ignored", finding="F4")
def _():
    # `.gitignore` does not apply to files git already tracks, so a rule added after the fact
    # silences the warning without removing the file. Four .pyc files rode along that way,
    # under `__pycache__/` and `*.pyc` rules that had been correct the whole time -- and the
    # F4 check above never saw them because it guards `skills/` and they were under `tests/`.
    #
    # This is the general form: ask git for the contradiction rather than enumerating the file
    # types that might cause it.
    p = subprocess.run(["git", "ls-files", "--cached", "--ignored", "--exclude-standard"],
                       cwd=REPO, capture_output=True, text=True)
    if p.returncode != 0:
        # Not a git checkout (an export, a tarball). Nothing to assert, and failing here would
        # be asserting a property of the packaging rather than of the toolchain.
        return
    tracked_and_ignored = [line for line in p.stdout.splitlines() if line.strip()]
    assert not tracked_and_ignored, (
        "these files are tracked AND matched by .gitignore, so the ignore rule is inert and "
        "they keep committing:\n    " + "\n    ".join(tracked_and_ignored)
        + "\n\n    Fix with `git rm --cached <file>`; the ignore rules are already right.")


@check("`/breakdown` resolves its output paths rather than joining strings", finding="F4")
def _():
    # F4: a whole run's tasks landed in skills/breakdown-generate-tasks/output/, because the
    # sub-skill was handed a relative directory and resolved it against its own. §3.1 says
    # plainly that a prose absolute-path check would not fix this -- "writing more emphatic
    # prose is not a fix" -- so run the guard and assert what it does.
    import shutil
    import stat
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "resolve-output.sh")
    assert os.path.isfile(script), "skills/breakdown/scripts/resolve-output.sh is missing"

    sk = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    assert "resolve-output.sh" in sk, (
        "breakdown never calls resolve-output.sh, so nothing resolves anything")

    # The point of resolving is that the resolved value is then *used*. A skill that runs the
    # script and goes on to write `docs/tasks/{slug}` anyway has gained nothing.
    stale = [f"{i}: {l.strip()[:90]}"
             for i, l in enumerate(sk.splitlines(), 1)
             if "docs/tasks/{slug}" in l and "resolve-output.sh" not in l]
    assert not stale, ("breakdown still uses the relative path after resolving it:\n    "
                       + "\n    ".join(stale))

    gen = open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
               encoding="utf-8").read()
    assert "must be absolute" in gen, (
        "breakdown-generate-tasks accepts a relative output dir -- the F4 path exactly")

    if not shutil.which("sh"):
        return  # nothing to run the guard with; the static half above still applied

    def run(*args):
        p = subprocess.run(["sh", script, *args], cwd=ws, capture_output=True,
                           text=True, timeout=60)
        return p.returncode, (p.stdout or "") + (p.stderr or "")

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    root = tempfile.mkdtemp(prefix="resolve-output-check-")
    try:
        ws = os.path.join(root, "ws")
        os.makedirs(ws)

        # A relative tasks directory is allowed, and comes back absolute.
        rc, out = run("docs/tasks/link-shelf")
        assert rc == 0, f"refused a relative tasks dir, which is the documented default: {out[:200]}"
        line = [l for l in out.splitlines() if l.startswith("tasks_dir=")]
        assert line, f"no tasks_dir on stdout: {out[:200]}"
        got = line[0].split("=", 1)[1]
        # Not os.path.isabs: on Windows since 3.13 it calls `/tmp/x` rooted-but-not-absolute,
        # which would fail this check against a path the script resolved perfectly well. The
        # script emits POSIX paths under Git Bash whatever the host.
        assert re.match(r"^(/|[A-Za-z]:)", got), (
            f"tasks_dir came back relative, so nothing was resolved: {got}")

        # An absolute target is allowed; a relative one is the §5.2 test 5 case.
        #
        # Assert the VALUE, not merely that a `target_dir=` line appeared. The first version of
        # this check tested only presence, and passed while the script silently resolved
        # `C:\Users\...\nope\app` to `/tmp/nope/app` -- backslashes are ordinary characters to
        # `dirname`, and MSYS mangled the rest. A path nobody named, returned with exit 0.
        def norm(p):
            return p.replace("\\", "/").rstrip("/").lower()

        for label, given in (("an existing parent", os.path.join(root, "app")),
                             ("a path not created yet", os.path.join(root, "nope", "app"))):
            rc, out = run("docs/tasks/link-shelf", given)
            assert rc == 0, f"refused an absolute target ({label}): {out[:200]}"
            got = [l for l in out.splitlines() if l.startswith("target_dir=")]
            assert got, f"no target_dir echoed for {label}: {out[:200]}"
            got = got[0].split("=", 1)[1]
            assert norm(got) == norm(given), (
                f"target_dir resolved to somewhere the caller did not name ({label}):\n"
                f"    given: {given}\n    got:   {got}")

        rc, out = run("docs/tasks/link-shelf", "./relative-out")
        assert rc != 0, "a relative --output-dir was ACCEPTED (§5.2 test 5)"
        assert "REFUSED" in out, f"refusal does not say REFUSED: {out[:200]}"
        assert not os.path.isdir(os.path.join(ws, "relative-out")), (
            "the guard created the directory it refused")

        # F4 itself: output resolving inside a plugin, by either route.
        plug = os.path.join(root, "plug")
        os.makedirs(os.path.join(plug, ".claude-plugin"))
        open(os.path.join(plug, ".claude-plugin", "plugin.json"), "w").write("{}")
        for label, args in (
            ("a tasks dir inside a plugin", (os.path.join(plug, "skills", "x", "output"),)),
            ("a target inside a plugin", ("docs/tasks/link-shelf", os.path.join(plug, "app"))),
        ):
            rc, out = run(*args)
            assert rc != 0, f"ACCEPTED {label} -- this is F4"
            assert "REFUSED" in out, f"refusal of {label} does not say REFUSED: {out[:200]}"
    finally:
        rmtree(root)


@check("the §5.1 fixture PRD is valid and self-consistent")
def _():
    # The fixture is only useful if /breakdown can parse it. Validating here means a
    # drifting fixture fails the fast suite rather than an end-to-end run.
    import xml.etree.ElementTree as ET
    base = current_fixture("link-shelf")
    assert os.path.isdir(base), f"{base} is missing"

    root = ET.parse(os.path.join(base, "index.md")).getroot()
    assert root.tag == "prd", f"index.md root is <{root.tag}>, expected <prd>"
    feats = root.findall("features/feature")
    assert 2 <= len(feats) <= 4, f"{len(feats)} features; §5.1 asks for two or three"

    missing = [f.get("file") for f in feats
               if not f.get("file")
               or not os.path.isfile(os.path.join(base, f.get("file").replace("/", os.sep)))]
    assert not missing, f"feature files missing: {missing}"

    # Item 12's dual read, asserted rather than assumed: <status> is under <meta> in a migrated
    # file and a direct child in one that has not been migrated yet, and BOTH must keep working
    # until every artefact has moved. A PRD that cannot be found is a PRD that gets overwritten
    # -- F3, which cost an interview before it was fixed.
    wn = ET.parse(os.path.join(base, "what-next.md")).getroot()
    status = (wn.findtext("meta/status") or wn.findtext("status") or "").strip()
    assert status == "in-progress", (
        "fixture what-next.md needs <status>in-progress</status> for the resume test (F3), "
        "under <meta> or directly under <what-next>")


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



@check("a rule file that cannot be obeyed stops the run -- by running the guard", finding="P18")
def _():
    """items 25/28/37. Absent is fine; present-and-broken must refuse, naming the element.

    The asymmetry is the whole finding. A silently ignored rule file is worse than none,
    because the rule is not in force and the operator believes it is -- which is P16's failure
    mode one level up. So this runs the script rather than reading it: `the script mentions
    <layers>` is a property every useless validator also has.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-architecture.py")
    assert os.path.isfile(script), "check-architecture.py is missing"

    def run(root, *extra):
        return subprocess.run([sys.executable, script, root, *extra],
                              capture_output=True, text=True)

    root = tempfile.mkdtemp(prefix="prd-arch-")
    try:
        def project(name, body):
            d = os.path.join(root, name)
            os.makedirs(d, exist_ok=True)
            if body is not None:
                with open(os.path.join(d, "architecture.md"), "w",
                          encoding="utf-8", newline="\n") as f:
                    f.write(body)
            return d

        VALID = """# Architecture: Demo
<architecture version="1.0">
  <rules>
    <layers>
      <layer id="1" name="contracts" depends-on=""/>
      <layer id="2" name="producers" depends-on="1"/>
      <layer id="3" name="consumers" depends-on="1"/>
      <layer id="4" name="integration" depends-on="2,3"/>
    </layers>
    <testing default="tdd" runner="pytest">
      <policy match="web/**" kind="component" runner="vitest"/>
    </testing>
    <task-limits default="3"><limit match="contracts/**" max-files="5"/></task-limits>
    <banned>
      <rule kind="import" match="contexts/**" symbol="httpx" reason="ADR-004: by event">
        <except match="contexts/*/adapters/outbound/**" reason="third-party APIs are HTTP"/>
      </rule>
      <rule kind="judgement" reason="ADR-011: tolerate replay">not idempotent</rule>
    </banned>
    <scaffold template="none"/>
  </rules>
  <principles><principle id="P-001">Delete rather than configure.</principle></principles>
  <event-registry/>
</architecture>
"""
        # 1. Absent is a normal, common, non-error result. Every project predating this file.
        p = run(project("absent", None))
        assert p.returncode == 0, f"absent architecture.md refused: {p.stderr}"
        assert "defaults apply" in p.stdout, (
            "an absent rule file must say the defaults apply, not merely stay silent -- "
            f"got: {p.stdout!r}")

        # 2. A valid one passes, and reports what it found rather than just 'ok'.
        p = run(project("valid", VALID))
        assert p.returncode == 0, f"a valid architecture.md was refused:\n{p.stderr}"
        for expected in ("layers 4", "banned 2", "testing tdd", "task-limits 3",
                         "principles 1", "event-registry"):
            assert expected in p.stdout, (
                f"the summary does not name {expected!r}; an operator cannot tell which rules "
                f"are in force. got: {p.stdout!r}")
        assert "1 refusing, 1 reporting" in p.stdout, (
            "the summary must separate rules that refuse from rules that only report -- "
            "claiming enforcement the toolchain does not deliver is the failure P16 is about")

        # 3. Every refusal class, each asserted on its NAMED cause rather than on exit 1.
        #    An exit code alone cannot tell a guard from a coincidence (item 54's false pass).
        broken = {
            "cycle": (VALID.replace('<layer id="1" name="contracts" depends-on=""/>',
                                    '<layer id="1" name="contracts" depends-on="4"/>'),
                      "cycle"),
            "unknown-dep": (VALID.replace('depends-on="2,3"', 'depends-on="2,9"'),
                            "is not declared here"),
            "dup-id": (VALID.replace('<layer id="3" name="consumers" depends-on="1"/>',
                                     '<layer id="2" name="consumers" depends-on="1"/>'),
                       "declared twice"),
            "no-kind": (VALID.replace('<rule kind="import" match="contexts/**"',
                                      '<rule match="contexts/**"'), "no kind"),
            "no-reason": (VALID.replace(' reason="ADR-004: by event"', ''), "no reason"),
            "missing-attr": (VALID.replace(' symbol="httpx"', ''), "missing 'symbol'"),
            "bad-testing": (VALID.replace('default="tdd"', 'default="sometimes"'),
                            "is not one of tdd, none"),
            "bad-limit": (VALID.replace('max-files="5"', 'max-files="none"'),
                          "not a positive integer"),
            "dup-principle": (VALID.replace('</principles>',
                                            '<principle id="P-001">again</principle></principles>'),
                              "declared twice"),
            "no-principle-id": (VALID.replace('<principle id="P-001">', '<principle>'), "no id"),
            "bare-amp": (VALID.replace('<event-registry/>',
                                       '<event-registry><e n="a&b"/></event-registry>'),
                         "bare ampersand"),
            "no-block": ("# Architecture\n\nProse only, no machine-readable section.\n",
                         "no <architecture> block"),
        }
        for name, (body, expect) in broken.items():
            p = run(project(f"broken-{name}", body))
            assert p.returncode == 1, (
                f"{name}: a rule file that cannot be obeyed exited {p.returncode}. "
                f"Silently ignoring it is the finding.\n{p.stdout}{p.stderr}")
            assert expect in p.stderr, (
                f"{name}: refused, but never named the cause {expect!r}. A refusal an operator "
                f"cannot act on is barely better than none.\n{p.stderr}")

        # 4. --json is what a caller consumes; the graph must survive the round trip.
        p = run(project("valid-json", VALID), "--json")
        assert p.returncode == 0, p.stderr
        data = json.loads(p.stdout)
        layers = data["layer_blocks"][0]["layers"]
        assert [l["id"] for l in layers] == ["1", "2", "3", "4"], layers
        assert layers[3]["depends_on"] == ["2", "3"], (
            "depends-on must parse as a LIST -- a single-valued read collapses the fan-in that "
            f"makes the graph a DAG rather than a chain: {layers[3]}")
        assert [r["kind"] for r in data["banned"]] == ["import", "judgement"]
        assert data["banned"][0]["excepts"][0]["match"].startswith("contexts/"), (
            "an <except> that does not survive parsing is a rule the implementer will write "
            "around for no reason")

        # 5. Wired in. A guard nothing calls is the producer-without-a-reader this plan is about.
        caller = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
        phase1 = caller[:caller.find("### Phase 2")]
        assert "check-architecture.py" in phase1, (
            "the rule-file guard is not called in /breakdown Phase 1, so a broken rule file is "
            "discovered by not being obeyed")
        assert prose("Stop and report it verbatim") in prose(phase1), (
            "Phase 1 does not bind the exit code to stopping")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the layer graph plan-layers documents is the one the validator emits", finding="P18")
def _():
    """Item 28's core, asserted the way 23a learned to assert a schema: mechanically.

    Two earlier versions of this check were decorative and mutation killed both. The first
    asserted plan-layers *mentions* `architecture.md`; the phrase appears five times, so
    deleting the branch that honours a declared graph left the word behind. The second asserted
    it mentions `layer_blocks` and `depends_on`; those appear several times too, so renaming the
    field in the documented example still passed.

    **A substring check over a document that repeats the token cannot detect the removal of one
    occurrence.** So this parses the example instead and compares it against what
    `check-architecture.py --json` really writes -- the same producer-versus-spec comparison
    item 23a used, after three schema revisions had drifted while being read rather than run.
    """
    import shutil
    import tempfile

    planner = open(os.path.join(SKILLS, "breakdown-plan-layers", "SKILL.md"),
                   encoding="utf-8").read()

    blocks = re.findall(r"```json\s*\n(.*?)```", planner, re.S)
    assert blocks, "plan-layers documents no JSON example, so the graph's shape is prose"

    documented = None
    for b in blocks:
        try:
            documented = json.loads("{" + b.strip().rstrip(",") + "}")
        except Exception:
            continue
        if "layer_blocks" in documented:
            break
        documented = None
    assert documented is not None, (
        "no JSON example in plan-layers parses and carries `layer_blocks`. The planner reads "
        "check-architecture.py --json output; an example that does not parse is not that")

    # What the producer actually emits, taken by running it rather than by reading it.
    script = os.path.join(SKILLS, "breakdown", "scripts", "check-architecture.py")
    root = tempfile.mkdtemp(prefix="prd-graph-")
    try:
        with open(os.path.join(root, "architecture.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write('<architecture version="1.0"><rules><layers>'
                    '<layer id="1" name="contracts" depends-on=""/>'
                    '<layer id="2" name="producers" depends-on="1"/>'
                    '<layer id="3" name="consumers" depends-on="1"/>'
                    '<layer id="4" name="integration" depends-on="2,3"/>'
                    '</layers></rules><api-registry/></architecture>\n')
        proc = subprocess.run([sys.executable, script, root, "--json"],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        emitted = json.loads(proc.stdout)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    doc_block = documented["layer_blocks"][0]
    emit_block = emitted["layer_blocks"][0]

    assert set(doc_block) == set(emit_block), (
        f"the documented block's keys {sorted(doc_block)} are not the ones the validator emits "
        f"{sorted(emit_block)}. The planner would look for a field that is not written")
    assert set(doc_block["layers"][0]) == set(emit_block["layers"][0]), (
        f"documented layer keys {sorted(doc_block['layers'][0])} != emitted "
        f"{sorted(emit_block['layers'][0])}")

    # The fan-in is the property that made this a DAG rather than a chain, so assert it
    # survives BOTH the producer and the document.
    fan_in = [l for l in emit_block["layers"] if len(l["depends_on"]) > 1]
    assert fan_in, "the validator collapsed a multi-valued depends-on; the graph is now a chain"
    doc_fan_in = [l for l in doc_block["layers"] if len(l.get("depends_on") or []) > 1]
    assert doc_fan_in, (
        "the documented example has no layer depending on more than one other, so it does not "
        "show the planner the case that matters. Read as a chain, producers and consumers "
        "become sequential -- destroying the independence the architecture was chosen for")

    # The rules that are genuinely prose, asserted as whole sentences rather than tokens --
    # and each must carry its CONDITION, not only its consequence. A mutation that deleted the
    # condition while leaving "that graph, exactly as declared" survived an earlier version of
    # this check: the planner was still told what to do, and no longer told when.
    for sentence in (
        "architecture.json with a non-empty layer_blocks",   # the condition
        "that graph, exactly as declared",                   # the consequence
        "no architecture.json, or empty layer_blocks",       # the other condition
        "the five tiers below, as always",                   # the other consequence
        "Do not merge the two",
        "a DAG, not a chain",
    ):
        assert prose(sentence) in prose(planner), (
            f"plan-layers no longer states: {sentence!r}")
    assert re.search(r"default graph|the default tiers", planner), (
        "the shipped five tiers are not marked as a DEFAULT. That relabelling is the whole of "
        "item 28: they were the graph, with no override, so a project that disagreed had to "
        "fork the plugin (P18)")

    # The wiring: producer in Phase 1, carrier in Phase 3, or a validated graph is dropped.
    breakdown = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    phase1 = breakdown[:breakdown.find("### Phase 2")]
    assert re.search(r"check-architecture\.py[^\n]*--json[^\n]*architecture\.json", phase1), (
        "Phase 1 does not derive architecture.json from `check-architecture.py --json`. A "
        "second parser of the same markdown can disagree with the one that validated it")
    # The carrier itself, not a sentence near it. Phase 3's invocation must NAME the file, or
    # the graph is validated in Phase 1 and then dropped on the floor.
    section = breakdown[breakdown.find("Invoke the `breakdown-plan-layers`"):]
    section = section[:section.find("**For CRD:**")]
    # The INVOCATION sentence, not the section around it. A later paragraph discussing the file
    # is not the same as handing it over -- and half-edited instructions that say both are this
    # repository's most repeated defect. Item 60 was exactly that: the correct rule was added
    # without removing the four blocks it contradicted, so the document stated both.
    invocation = section[:section.find(chr(10) + chr(10))]
    assert "architecture.json" in invocation, (
        "the sentence invoking plan-layers does not name architecture.json, so a declared graph "
        "is validated in Phase 1 and then dropped. A later paragraph mentioning the file is not "
        "the same as passing it:" + chr(10) + invocation)
    # The CLAIM, not its phrasing: a declared graph replaces the defaults and is not
    # merged with them. Item 31 reworded "the five tiers below" to "the default tiers"
    # -- correctly, since Phase 3 no longer carries a list -- and this assertion had
    # pinned the old words. Assert what must stay true.
    assert prose("Not merged with them") in prose(section), (
        "Phase 3 no longer states that a declared graph REPLACES the default tiers. Merging "
        "them is how a project acquires layers it explicitly rejected")


@check("`<testing default>` reaches execution as data, not as a fourth opinion", finding="P18")
def _():
    """P18's second row: an opinion enforced in more places than it is documented.

    The mandate is not in `tdd-workflow.md`, which only describes Red/Green/Refactor. It is
    imposed by `task-format-spec.md` marking the section required and `review-criteria.md`
    making it critical -- so a project declaring `<testing default="none">` that changed only
    some of them has every task fail batch review at /breakdown and never reach execution.

    Each assertion below is a **whole sentence that exists for one reason**, not a token. A
    token check passes for as long as the word is anywhere in the file, which is how the first
    two versions of this check survived having the branch deleted.
    """
    def read(*parts):
        return open(os.path.join(*parts), encoding="utf-8").read()

    required = {
        "breakdown-generate-tasks/SKILL.md": (
            os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
            ['in which case omit <test-requirements>',
             'review-tasks reads the same declaration']),
        "breakdown/references/task-format-spec.md": (
            os.path.join(SKILLS, "breakdown", "references", "task-format-spec.md"),
            ['decides whether this section is required',
             'required when <testing default="tdd">']),
        "breakdown/references/review-criteria.md": (
            os.path.join(SKILLS, "breakdown", "references", "review-criteria.md"),
            ['test-requirements is required unless the project declares']),
        "execute-batch/SKILL.md": (
            os.path.join(SKILLS, "execute-batch", "SKILL.md"),
            ['do not open architecture.md here',
             'has no <test-requirements>',
             'the section\'s presence is the declaration']),
    }
    bad = []
    for label, (path, sentences) in required.items():
        text = prose(read(*[path]))
        for sentence in sentences:
            if prose(sentence).lower() not in text.lower():
                bad.append(f"{label}: no longer states {sentence!r}")
    assert not bad, "\n    " + "\n    ".join(bad)

    # execute-batch must not decide TEST POLICY by opening a file: the task it is holding
    # already carries that decision, and a second channel can disagree with the artefact being
    # implemented.
    #
    # Asserted POSITIVELY, and that is the third correction to this one assertion. It began as
    # "the word `architecture` must not appear in the argument table", which failed when item
    # 56 legitimately gave execute-batch a `--rules` path to FORWARD to execute-verify. Narrowed
    # to "architecture.md must not appear in the TDD section", it failed again -- that section
    # has to *mention* the file to explain that the declaration is honoured upstream.
    #
    # Mentioning a file and opening it are different acts, and only one of them is the defect.
    # So assert what must be TRUE rather than hunting for words that must be absent; the
    # sentences below are already required by the table at the top of this check.
    batch = read(SKILLS, "execute-batch", "SKILL.md")
    tdd_section = batch[batch.find("**`{tdd_workflow_line}` is conditional"):
                        batch.find("**Example - launching")]
    assert tdd_section, "execute-batch lost the section explaining the TDD branch"
    assert prose("Read the task instead") in prose(tdd_section), (
        "execute-batch's TDD section no longer says where the answer comes from. The task's own "
        "<test-requirements> IS the declaration; anything else is a second source of truth")

    # A `--rules` argument is legitimate -- <banned> rules need the worktree and the diff, which
    # exist only at verify time -- but it must be forwarded, never consumed for test policy.
    args = batch[batch.find("## Input Arguments"):batch.find("## Execution Flow")]
    if "--rules" in args:
        assert "forward" in args.lower(), (
            "execute-batch takes a --rules path without saying it forwards it. If it consumes "
            "the rules itself, the TDD policy has two sources again")

    # tdd-workflow.md describes the procedure and must not acquire the mandate: a fourth
    # enforcement site makes the opinion harder to override rather than easier.
    workflow = prose(read(SKILLS, "execute-batch", "references", "tdd-workflow.md")).lower()
    for claim in ("tdd is mandatory", "every project must write tests first"):
        assert claim not in workflow, (
            f"tdd-workflow.md now asserts {claim!r}. The mandate is imposed upstream; a fourth "
            f"site is one more place to change and one more that can be missed (P18)")


@check("PROJECT.md requires a registry, not the REST pair -- by running the guard", finding="P35")
def _():
    """Review finding R8, plan item 25. The pair was REST plus relational.

    `check-project-md.py` hard-required api-registry AND schema-registry, so a CLI project
    seeded with only a <command-registry> failed a guard it should have passed -- the toolchain
    re-vendoring its own architecture one level below where item 28 freed it.

    The two names were a proxy for *a consumer can read this*. Requiring any one keeps the proxy
    honest without mandating a shape.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "execute", "scripts", "check-project-md.py")
    assert os.path.isfile(script)

    HEAD = ("# Project: demo\n<project-context version=\"1.0\">\n"
            "  <meta><last-updated>2026-08-26T00:00:00Z</last-updated>"
            "<last-context-hash>abc1234</last-context-hash></meta>\n"
            "  <features><feature id=\"f\" status=\"complete\"><name>F</name>"
            "<files>src/f.py</files></feature></features>\n")

    cases = {
        "command-only": ("  <command-registry><command name=\"run\"/></command-registry>\n", 0),
        "event-only": ("  <event-registry><event name=\"Placed\"/></event-registry>\n", 0),
        "screen-only": ("  <screen-registry><screen name=\"Home\"/></screen-registry>\n", 0),
        "rest-pair": ("  <api-registry/>\n  <schema-registry/>\n", 0),
        "none": ("", 1),
    }
    root = tempfile.mkdtemp(prefix="prd-pmd-")
    try:
        for name, (registry, expected) in cases.items():
            d = os.path.join(root, name)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "PROJECT.md"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write(HEAD + registry + "</project-context>\n")
            p = subprocess.run([sys.executable, script, d], capture_output=True, text=True)
            assert p.returncode == expected, (
                f"{name}: expected exit {expected}, got {p.returncode}. A registry set fixed at "
                f"REST-plus-relational is the opinion item 25 exists to open.\n"
                f"{p.stdout}{p.stderr}")

        # Refusing with no registry must say what to supply, not merely that something is absent.
        p = subprocess.run([sys.executable, script, os.path.join(root, "none")],
                           capture_output=True, text=True)
        assert "command-registry" in p.stderr and "event-registry" in p.stderr, (
            "the refusal does not name the registries a project might supply, so it reads as "
            f"'you are missing the two I know about':\n{p.stderr}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("principle citations resolve, and criterion priorities are not mistaken for them",
       finding="P24")
def _():
    """The tenth of item 39's 190 references, deferred until <principles> had a home.

    The deferral is now closed, and the second half of this check is why it needed care:
    item 34's criterion priorities are written P0, P1 and P2. A citation pattern without the
    hyphen would report a dangling principle on every prioritised criterion in the corpus --
    550 of them -- which is a validator that has to be switched off to get any work done.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-references.py")
    root = tempfile.mkdtemp(prefix="prd-princ-")
    try:
        prd = os.path.join(root, "docs", "prd", "demo", "features")
        os.makedirs(prd)
        with open(os.path.join(root, "architecture.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("<architecture version=\"1.0\"><principles>"
                    "<principle id=\"P-001\">Delete rather than configure.</principle>"
                    "<principle id=\"P-002\">One artefact, one concern.</principle>"
                    "</principles><api-registry/></architecture>\n")
        with open(os.path.join(root, "docs", "prd", "demo", "index.md"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write("<prd><meta><slug>demo</slug></meta></prd>\n")

        feature = os.path.join(prd, "a.md")

        def write(desc):
            with open(feature, "w", encoding="utf-8", newline="\n") as f:
                f.write("<feature><meta><slug>a</slug></meta>\n"
                        f"<description>{desc}</description>\n"
                        "<acceptance-criteria>\n"
                        "  <criterion id=\"1\" pattern=\"event-driven\" priority=\"P0\">"
                        "When x, the system shall y.</criterion>\n"
                        "  <criterion id=\"2\" pattern=\"unwanted-behaviour\" priority=\"P1\">"
                        "If x fails, the system shall z.</criterion>\n"
                        "  <criterion id=\"3\" pattern=\"state-driven\" priority=\"P2\">"
                        "While x, the system shall w.</criterion>\n"
                        "</acceptance-criteria></feature>\n")

        target = os.path.join(root, "docs", "prd", "demo")

        def run(*extra):
            return subprocess.run([sys.executable, script, target, *extra],
                                  capture_output=True, text=True)

        # Resolving citations pass -- and P0/P1/P2 must not be counted at all.
        write("Follows P-001, and P-2 by its numeric part.")
        p = run()
        assert p.returncode == 0, f"valid principle citations refused:\n{p.stdout}{p.stderr}"
        assert "2 references checked" in p.stdout, (
            "expected exactly the two P-NNN citations. Counting the criterion priorities P0, "
            f"P1 and P2 would make this 5 and every prioritised criterion a dangling "
            f"reference:\n{p.stdout}")

        # A dangling one is refused and named as written.
        write("Follows P-001 and P-404.")
        p = run()
        assert p.returncode == 1, f"a dangling principle exited 0:\n{p.stdout}"
        assert "P-404" in p.stdout, f"the dangling citation is not named:\n{p.stdout}"
        assert "P-001" not in p.stdout.replace("P-0011", ""), (
            f"a resolving citation was reported as dangling:\n{p.stdout}")

        # Citations with nowhere to resolve are an error naming the flag, not a quiet pass.
        os.rename(os.path.join(root, "architecture.md"), os.path.join(root, "arch.off"))
        write("Follows P-001.")
        p = run()
        assert p.returncode == 1, (
            "a principle citation with no architecture.md passed quietly, which is how a "
            f"validator becomes decorative:\n{p.stdout}")
        assert "--architecture" in p.stdout, (
            f"the error does not name the flag that would fix it:\n{p.stdout}")

        # The docstring must no longer claim principles are the deferred exclusion.
        text = open(script, encoding="utf-8").read()
        assert "180 of the corpus" not in prose(text) or "now" in prose(text).lower(), (
            "check-references.py still advertises principles as not checked")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("architecture.md has a producer, and it runs before dependencies", finding="P17")
def _():
    """Item 51. Items 25 and 28 gave the file a home, a schema and four readers, and no writer.

    A reader with no producer is the mirror of this plan's own central finding, and it went
    unnoticed for twenty-six items. So this asserts the property in BOTH directions -- the thing
    item 23 says every element needs -- rather than only checking that a Design phase exists.
    """
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()

    # --- the producer exists, and is placed where its inputs are ready ----------------
    phases = re.findall(r"### Phase (\d+): ([^\n]+)", prd)
    numbers = [int(n) for n, _t in phases]
    assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers), (
        f"/prd's phases are not a clean ascending sequence: {phases}")

    by_name = {t.lower(): int(n) for n, t in phases}
    design = [n for t, n in by_name.items() if "design" in t]
    features = [n for t, n in by_name.items() if "feature" in t]
    deps = [n for t, n in by_name.items() if "dependenc" in t]
    assert design, "/prd has no Design phase, so architecture.md has no producer (item 51)"
    assert features and deps, f"/prd lost its Features or Dependencies phase: {phases}"
    assert features[0] < design[0] < deps[0], (
        f"Design is at phase {design[0]}, Features at {features[0]}, Dependencies at {deps[0]}. "
        f"Design must follow features (so the conversation knows what is being built) and "
        f"precede dependencies (which are partly DECIDED by the architecture -- asking them "
        f"first inverts the causality)")

    design_body = prd[prd.find(f"### Phase {design[0]}:"):
                      prd.find(f"### Phase {design[0] + 1}:")]
    assert design_body.strip(), "the Design phase is a heading with no body"

    # --- it must actually write the file, and validate what it wrote ------------------
    assert "architecture.md" in design_body, (
        "the Design phase never names architecture.md, so it produces nothing")
    assert "check-architecture.py" in design_body, (
        "the Design phase writes a rule file and never validates it. /prd is the one moment the "
        "person who made the decision is still in the conversation to fix it")
    assert "${CLAUDE_PLUGIN_ROOT}" in design_body, (
        "the script is invoked without ${CLAUDE_PLUGIN_ROOT}. OQ1's probe established that a "
        "bare relative path fails -- cwd is the project, not the plugin")

    # --- the default branch must write nothing AND be recorded -----------------------
    flat = prose(design_body)
    assert prose("Write no architecture.md") in flat, (
        "the Design phase does not say that taking the default writes nothing. A PRD with no "
        "rule file must stay a valid PRD, or item 28 breaks every artefact on the day it lands")
    # Asserted as a structure inside the phase, not as the string "what-next.md" -- that
    # filename appears three times in this section, so removing the instruction that records
    # the decision leaves the word behind. Third time this class of check has been caught out
    # in this phase: scope to the region that owns the claim, and assert a shape.
    recorded = re.search(r"```xml\s*\n\s*<step\b[^>]*\bkind=[\"']decision[\"'][^>]*>",
                         design_body)
    assert recorded, (
        "the Design phase's default branch writes no recorded decision. 'Defaults, "
        "deliberately' and 'nobody was asked' must be distinguishable later, and an absent "
        "architecture.md cannot tell them apart -- so declining has to leave a mark somewhere")
    assert "what-next.md" in design_body[:recorded.start()], (
        "the decision record is not attributed to what-next.md, so nothing says where it lands")

    # --- it must read before it writes (item 52's check, used rather than duplicated) --
    assert re.search(r"follow\s*/\s*extend\s*/\s*override", flat, re.I), (
        "the Design phase does not offer follow / extend / override, so a repository that "
        "already declares an architecture gets asked from a blank page (P34)")

    # --- and the whole point: a producer whose output has readers --------------------
    readers = {
        "breakdown/SKILL.md": os.path.join(SKILLS, "breakdown", "SKILL.md"),
        "breakdown-plan-layers/SKILL.md": os.path.join(
            SKILLS, "breakdown-plan-layers", "SKILL.md"),
        "breakdown-analyze-prd/SKILL.md": os.path.join(
            SKILLS, "breakdown-analyze-prd", "SKILL.md"),
        "breakdown-generate-tasks/SKILL.md": os.path.join(
            SKILLS, "breakdown-generate-tasks", "SKILL.md"),
    }
    # A reader must devote a HEADING or a numbered step to the file -- the word appearing
    # somewhere in a 400-line skill is not evidence that anything reads it. `plan-layers` is
    # exempt from the heading rule because its own check already compares the documented JSON
    # against live producer output, which is far stronger than any prose assertion here.
    unread = []
    for label, path in readers.items():
        text = open(path, encoding="utf-8").read()
        if "plan-layers" in label:
            if "architecture.json" not in text:
                unread.append(f"{label} (no architecture.json)")
            continue
        owns = re.search(r"^#{2,4} [^\n]*architecture", text, re.M | re.I) or \
            re.search(r"^\d+\. \*\*[^\n]*(architecture|project's own rules)", text, re.M | re.I)
        if not owns:
            unread.append(f"{label} (no section owning it)")
    assert not unread, (
        "architecture.md now has a producer and these named readers give it no section of their "
        "own: " + ", ".join(unread) + ". A producer with no reader is P4, and this plan's "
        "closing argument is that neither half may stand alone")

    # --- the template it writes must be the one the validator accepts ----------------
    fmt = os.path.join(SKILLS, "breakdown", "references", "architecture-format.md")
    assert os.path.isfile(fmt)
    assert "architecture-format.md" in design_body, (
        "the phase that WRITES architecture.md does not cite the format specification. A "
        "citation elsewhere in the file is not the same thing: the producer and the schema drift "
        "apart exactly where the writing happens, which is P30 by construction")
    # And the citation must resolve, or it is a pointer to nothing.
    for link in re.findall(r"\]\(([^)]*architecture-format\.md)\)", design_body):
        target = os.path.normpath(os.path.join(COMMANDS, link))
        assert os.path.isfile(target), f"the format link does not resolve: {link} -> {target}"



@check("the layer set is derived from content, not taken as a list", finding="P33")
def _():
    """Item 31. The CRD path derived the layer set and then undid it; the PRD path never asked.

    `/breakdown` Phase 4 took `[0-setup, 1-foundation, 2-backend, 3-frontend, 4-integration]`
    unconditionally for every PRD, so a PRD with no frontend got a frontend layer. The CRD path
    asked the right question -- does this change span tiers? -- and then ended with *"Always
    include Layer 4 (integration) for wiring changes together"*, which made the minimum possible
    plan two layers, two batches and two rounds of generate -> review -> retry for a change that
    might be one edit to one file.

    The derivation is a TABLE, so this parses the table rather than grepping for sentences. It
    also must not forbid the phrase it deletes: Phase 2 shipped a check that failed on the
    sentence quoting the old instruction to explain the change, which forbade documenting the
    history it enforced.
    """
    caller = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    planner = open(os.path.join(SKILLS, "breakdown-plan-layers", "SKILL.md"),
                   encoding="utf-8").read()

    phase3 = caller[caller.find("### Phase 3:"):caller.find("### Phase 4:")]
    phase4 = caller[caller.find("### Phase 4:"):caller.find("### Phase 5:")]
    assert phase3 and phase4, "/breakdown lost Phase 3 or Phase 4"

    # --- the derivation exists as a table, with a condition per layer ------------------
    rows = {}
    for line in phase3.splitlines():
        m = re.match(r"\s*\|\s*`?([0-9]-[a-z]+)`?\s*\|([^|]*)\|", line)
        if m:
            rows[m.group(1)] = prose(m.group(2)).lower()
    for layer in ("0-setup", "1-foundation", "2-backend", "3-frontend", "4-integration"):
        assert layer in rows, (
            f"Phase 3 has no derivation row for {layer}. Without a stated condition the layer is "
            f"either always present or always absent, and 'always present' is the defect")

    # --- integration must be conditional on tier COUNT, which is the deleted line -----
    integration = rows["4-integration"]
    assert "more than one" in integration or "two or more" in integration, (
        f"the integration layer's condition is {integration!r}, which does not depend on how "
        f"many other tiers survived. `Always include Layer 4` is what made the minimum plan two "
        f"layers instead of one -- there is nothing to integrate when only one tier moved")

    # --- Phase 4 must not restore the unconditional list -----------------------------
    literal = re.search(r"\[\s*0-setup\s*,\s*1-foundation\s*,\s*2-backend", phase4)
    assert not literal, (
        "Phase 4 again names the five layers as a literal list. It must process exactly the "
        "layers layer_plan.json contains, or it silently restores the unconditional tiers "
        "Phase 3 just derived away:\n" + literal.group(0))
    assert "layer_plan.json" in phase4, (
        "Phase 4 does not take its layer set from layer_plan.json, so the derivation has no "
        "consumer")

    # --- the degenerate case, stated on both sides -----------------------------------
    # BOTH ends, not either. This was an `or`, and a mutant deleting Phase 3's rule was
    # satisfied by Phase 4's mention of it. An `or` across two locations means each one alone
    # suffices -- which is exactly what a producer/consumer pair must never allow, and halves
    # the strength of the assertion for free.
    assert prose("one layer holding one task") in prose(phase3), (
        "Phase 3 no longer states the degenerate case. One layer holding one task is not a "
        "plan; running it directly is the small path P21 asks for, arriving from the right "
        "question rather than from a file-count threshold")
    assert prose("one layer with one task") in prose(phase4), (
        "Phase 4 no longer acts on the degenerate case, so Phase 3 derives it and nothing "
        "honours it")

    # --- the planner's own output must carry the derivation, parsed not grepped -------
    blocks = re.findall(r"```json\s*\n(.*?)```", planner, re.S)
    plan = None
    for b in blocks:
        try:
            candidate = json.loads(b)
        except Exception:
            continue
        if isinstance(candidate, dict) and "layers" in candidate:
            plan = candidate
            break
    assert plan is not None, (
        "plan-layers documents no parseable layer plan, so its output shape is prose")
    assert "layers_dropped" in plan, (
        "the documented layer plan has no `layers_dropped`. A derivation that drops a tier "
        "without saying so leaves an operator who expected four tasks and got one with no "
        "explanation -- the report is half the item")
    assert "degenerate" in plan, (
        "the documented layer plan cannot express the single-layer single-task case, so the "
        "caller has nothing to branch on")
    assert isinstance(plan["layers_dropped"], list) and plan["layers_dropped"], (
        "`layers_dropped` is documented as empty, so the example never shows what a dropped "
        "layer looks like")
    for entry in plan["layers_dropped"]:
        assert "reason" in entry, (
            f"a dropped layer carries no reason: {entry}. 'Dropped: 3-frontend' without "
            f"'no components in this document' is not something an operator can act on")

    # --- skip-layering and skip-batching must stay distinct --------------------------
    flat = prose(phase3)
    assert prose("Skip batching") in flat and prose("Skip layering") in flat, (
        "Phase 3 does not keep skip-layering and skip-batching apart. Twenty endpoints in one "
        "tier is a large change that needs no layering and still wants batching, and a "
        "threshold on file count gets that backwards")



@check("`<banned>` and `<task-limits>` are enforced -- by running the enforcer", finding="P35")
def _():
    """Item 56. Item 28 gave a project somewhere to declare constraints; item 37 put `<rules>`
    in the exit-code column. Neither named an enforcer, so both rows stood for nothing.

    Every kind is run against a real violation and a real clean case. `the script mentions
    <banned>` is a property every useless validator also has, and this phase has already shipped
    five checks with exactly that defect.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-rules.py")
    assert os.path.isfile(script), "check-rules.py is missing"

    ARCH = (
        '<architecture version="1.0"><rules>\n'
        '<task-limits default="3"><limit match="contracts/**" max-files="5"/></task-limits>\n'
        '<banned>\n'
        '  <rule kind="import" match="contexts/**" symbol="httpx|requests"\n'
        '        reason="ADR-004: contexts communicate by event, never by call">\n'
        '    <except match="contexts/*/adapters/outbound/**" reason="third-party APIs are HTTP"/>\n'
        '  </rule>\n'
        '  <rule kind="content" match="services/*/src/**" pattern="(postgres|mysql)://"\n'
        '        reason="ADR-002: no shared datastore across services"/>\n'
        '  <rule kind="edge" from="services/*/" to="services/*/"\n'
        '        reason="ADR-002: services are independently deployable"/>\n'
        '  <rule kind="change" path="contracts/**" action="modify"\n'
        '        reason="published events are immutable; add a version, never edit"/>\n'
        '  <rule kind="judgement" reason="ADR-011: consumers must tolerate replay">\n'
        '    handler with side effects that are not idempotent\n'
        '  </rule>\n'
        '</banned></rules></architecture>\n')

    root = tempfile.mkdtemp(prefix="prd-rules-")
    try:
        def write(rel, text):
            full = os.path.join(root, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            return full

        arch = write("architecture.md", ARCH)

        def run(*args):
            p = subprocess.run([sys.executable, script, "--rules", arch, *args],
                               capture_output=True, text=True)
            return p.returncode, p.stdout, p.stderr

        # ---------------- review mode: only import/content, plus task-limits -------------
        clean = write("t-clean.xml",
                      "<task><requirements><requirement id=\"1\">Publish an event."
                      "</requirement></requirements>\n<files-to-create>\n"
                      "- contexts/orders/handlers.py\n</files-to-create></task>")
        rc, out, err = run("--mode", "review", "--task", clean)
        assert rc == 0, f"a compliant task was refused:\n{err}"
        assert "judgement" in out, (
            "a judgement rule did not appear in the report. It must be surfaced for a human "
            "even when nothing refuses -- reporting is the whole of what that kind does")

        bad = write("t-bad.xml",
                    "<task><requirements><requirement id=\"1\">Call billing with httpx.post()."
                    "</requirement></requirements>\n<files-to-create>\n"
                    "- contexts/orders/client.py\n</files-to-create></task>")
        rc, out, err = run("--mode", "review", "--task", bad)
        assert rc == 1, (
            "a task SPECIFYING a banned import was not refused at review. Catching it here is "
            "free -- no code exists yet -- and the cost of missing it is a rejected task after "
            f"an implementation run:\n{out}{err}")
        assert "ADR-004" in err, (
            f"the rule's reason was not reported verbatim. A bare rule number does not tell an "
            f"implementer what to do instead:\n{err}")

        exempt = write("t-exempt.xml",
                       "<task><requirements><requirement id=\"1\">Call Stripe with httpx."
                       "</requirement></requirements>\n<files-to-create>\n"
                       "- contexts/billing/adapters/outbound/stripe.py\n"
                       "</files-to-create></task>")
        rc, _out, err = run("--mode", "review", "--task", exempt)
        assert rc == 0, (
            "the rule's own <except> did not suppress the violation. An exception that does not "
            f"apply makes the rule unusable and pushes people toward per-task exemptions:\n{err}")

        over = write("t-over.xml", "<task><files-to-create>\n- app/a.py\n- app/b.py\n"
                                   "- app/c.py\n- app/d.py\n</files-to-create></task>")
        rc, _out, err = run("--mode", "review", "--task", over)
        assert rc == 1 and "task-limits" in err, (
            f"4 files against a default limit of 3 was not refused:\n{err}")

        # `content` must fire at review too, not only `import`. This was a genuine coverage
        # gap: a mutant restricting review to imports alone passed every assertion here.
        content_bad = write("t-content.xml",
                            "<task><requirements><requirement id=\"1\">Set DSN to "
                            "postgres://shared/warehouse.</requirement></requirements>\n"
                            "<files-to-create>\n- services/a/src/db.py\n"
                            "</files-to-create></task>")
        rc, _out, err = run("--mode", "review", "--task", content_bad)
        assert rc == 1 and "[content]" in err, (
            "a task SPECIFYING a banned content pattern was not refused at review. `content` "
            "and `import` are the two kinds that can fire before code exists, and catching "
            f"either one there is free:\n{err}")
        assert "ADR-002" in err, f"the content rule's reason was not reported:\n{err}"

        scoped = write("t-scoped.xml", "<task><files-to-create>\n- contracts/a.py\n"
                                       "- contracts/b.py\n- contracts/c.py\n- contracts/d.py\n"
                                       "- contracts/e.py\n</files-to-create></task>")
        rc, _out, err = run("--mode", "review", "--task", scoped)
        assert rc == 0, (
            "the scoped <limit match=\"contracts/**\" max-files=\"5\"> was not honoured. "
            f"Three files is right for a UI change and wrong for adding an event type:\n{err}")

        # ---------------- verify mode: all five, against code and diff ------------------
        wt = os.path.join(root, "wt")
        os.makedirs(wt)
        for cmd in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
            subprocess.run(["git", "-C", wt, *cmd], capture_output=True)
        write("wt/contracts/order.py", "SCHEMA = {'v': 1}\n")
        write("wt/services/b/api.py", "def thing(): ...\n")
        write("wt/services/a/src/ok.py", "from services.a.api import x\n")
        write("wt/services/a/api.py", "x = 1\n")
        subprocess.run(["git", "-C", wt, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", wt, "commit", "-qm", "base"], capture_output=True)
        base = subprocess.run(["git", "-C", wt, "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()

        rc, out, err = run("--mode", "verify", "--worktree", wt, "--base", base)
        assert rc == 0, f"a clean worktree was refused:\n{err}"

        write("wt/contexts/orders/client.py", "import httpx\n")
        write("wt/services/a/src/db.py", "DSN = 'postgres://shared/db'\n")
        write("wt/services/a/src/cross.py", "from services.b.api import thing\n")
        write("wt/contracts/order.py", "SCHEMA = {'v': 1, 'extra': True}\n")
        subprocess.run(["git", "-C", wt, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", wt, "commit", "-qm", "violations"], capture_output=True)

        rc, out, err = run("--mode", "verify", "--worktree", wt, "--base", base)
        assert rc == 1, f"a worktree violating four rules was not refused:\n{out}"
        for kind in ("import", "content", "edge", "change"):
            assert f"[{kind}]" in err, (
                f"the {kind} rule did not fire. Each of the four refusing kinds detects "
                f"something the others cannot, and a silent one is a rule the operator believes "
                f"is in force:\n{err}")

        # The dotted import is the case that matters and the one a naive matcher misses.
        assert "cross.py" in err, (
            "a dotted cross-service import was not caught. `from services.b.api import thing` "
            "is how a Python file crosses a service boundary; a matcher understanding only "
            f"slashes misses the commonest form of the violation:\n{err}")
        assert "ok.py" not in err, (
            "a service importing its OWN module was reported as a boundary crossing. A rule "
            f"that fires on compliant code gets switched off:\n{err}")

        # judgement never changes the exit code, and never lands in the refusing stream.
        assert "[judgement]" in out and "[judgement]" not in err, (
            "a judgement rule reached the refusing stream. S3: prose guards get weighed rather "
            "than obeyed, so these report and never block a merge. A rule that claims to "
            f"enforce and does not is what P16 is about.\nout={out}\nerr={err}")

        # A `change` rule with no diff must say it is not in force, not pass quietly.
        rc, out, err = run("--mode", "verify", "--worktree", wt)
        assert "UNRESOLVED" in out, (
            "with no --base, the change rule passed silently instead of reporting that it could "
            f"not see its evidence:\n{out}")

        # ---------------- both checkpoints must actually call it ------------------------
        reviewer = open(os.path.join(SKILLS, "breakdown-review-tasks", "SKILL.md"),
                        encoding="utf-8").read()
        verifier = open(os.path.join(SKILLS, "execute-verify", "SKILL.md"),
                        encoding="utf-8").read()
        # Asserted as a RUNNABLE INVOCATION inside a fenced block, not as the string
        # "check-rules.py". Both files also mention the script in prose -- review-tasks in its
        # criterion 7, execute-verify in its argument table -- so a mutant deleting the command
        # left the word behind and passed an earlier version of this check.
        for label, text in (("breakdown-review-tasks", reviewer),
                            ("execute-verify", verifier)):
            invocations = [b for b in re.findall(r"```bash\s*\n(.*?)```", text, re.S)
                           if "check-rules.py" in b]
            assert invocations, (
                f"{label} names check-rules.py in prose but never runs it. A checkpoint that "
                f"describes the enforcer instead of invoking it enforces nothing -- which is "
                f"P16 in the component whose whole job is enforcement")
            body = invocations[0]
            assert "--rules" in body and "--mode" in body, (
                f"{label}'s invocation is missing --rules or --mode:\n{body}")

        # The judgement verdict, taken from the TABLE ROW that carries it. The paragraph below
        # that table also contains "never fail", so a mutant flipping the row survived an
        # earlier assertion that merely looked for those words somewhere in the file.
        row = None
        for line in verifier.splitlines():
            if line.strip().startswith("|") and "judgement" in line:
                row = [c.strip() for c in line.strip().strip("|").split("|")]
        assert row, "execute-verify has no table row for the judgement kind"
        verdict = prose(row[-1]).lower()
        assert "never fail" in verdict or "report only" in verdict, (
            f"execute-verify's judgement row says {verdict!r}. S3: prose guards get weighed "
            f"rather than obeyed, so these report and never block a merge. A rule that claims "
            f"to enforce and does not is exactly what P16 is about")
        assert "fail the task" not in verdict, (
            f"execute-verify now fails tasks on a judgement finding: {verdict!r}. That is "
            f"inventing enforcement the toolchain cannot deliver")
    finally:
        shutil.rmtree(root, ignore_errors=True)



@check("greenfield ends with an architecture record, not without one", finding="P17")
def _():
    """Item 26. P17's output half: the finalizer ran only where PROJECT.md already existed.

    `test -f {project_path}/PROJECT.md` is a condition no greenfield run can satisfy, so a new
    project ran the entire pipeline and ended with no architecture record at all -- and the
    first /crd against it then paid for a full crd-investigate to rediscover architecture the
    PRD had already stated. The toolchain HAD an architecture artefact and greenfield was the
    only path that could not reach it.
    """
    execute = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
    agent = open(os.path.join(AGENTS, "project-context-finalizer.md"), encoding="utf-8").read()

    step = execute[execute.find("### Step 10"):]
    step = step[:step.find("### Step 11")] or step[:4000]
    assert step, "/execute lost its finalize-context step"

    # The gate must BRANCH, not skip. Asserted from the decision table rather than from prose:
    # the surrounding paragraphs necessarily discuss the old behaviour to explain the change,
    # so a substring check would find the history rather than the rule.
    actions = {}
    for line in step.splitlines():
        if line.strip().startswith("|") and line.count("|") >= 3:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and not set(cells[0]) <= set("- "):
                actions[prose(cells[0]).lower()] = prose(cells[-1]).lower()
    assert actions, "/execute Step 10 has no decision table, so the branch is prose"

    creates = [v for k, v in actions.items() if "no project.md" in k and "prd" in k]
    assert creates, (
        f"no row covers 'no PROJECT.md, run came from a PRD'. That is the greenfield case, and "
        f"skipping it silently is the whole of P17's output half. rows={list(actions)}")
    assert "create" in creates[0], (
        f"the greenfield row does not create PROJECT.md: {creates[0]!r}")

    updates = [v for k, v in actions.items() if "project.md exists" in k]
    assert updates and "update" in updates[0], (
        "the existing-PROJECT.md row no longer updates it, so item 26 broke the path that "
        "already worked")

    # The agent must be able to act on it.
    assert re.search(r"^#+ .*[Tt]wo modes", agent, re.M) or "`create`" in agent, (
        "project-context-finalizer has no create mode, so /execute branches to an agent that "
        "cannot do the work")
    for sentence in ("Do not copy <rules> or <principles>",
                     "the export wins"):
        assert prose(sentence) in prose(agent), (
            f"the finalizer no longer states: {sentence!r}. Seeding is a COPY of the registries "
            f"only -- architecture.md is prescriptive and PROJECT.md is descriptive, and "
            f"collapsing that distinction makes a constraint indistinguishable from an "
            f"observation")

    # A created file has to satisfy the validator that guards every consumer.
    assert prose("at least one\nregistry") in prose(agent) or \
        prose("at least one registry") in prose(agent), (
        "the finalizer does not know that check-project-md.py requires a registry, so `create` "
        "can produce a file that fails the guard on the next run")


@check("impact analysis reports contracts, not only APIs", finding="P35")
def _():
    """Item 57. Item 25 opened the registry set; without this, that is half a change.

    `crd-impact-analysis` could now READ an event or a command registry and would have had
    nowhere to report the impact -- it emitted `<affected-apis>` and `<affected-schemas>` and
    nothing else. The half that shows.
    """
    fmt = open(os.path.join(SKILLS, "crd", "references", "crd-format.md"),
               encoding="utf-8").read()
    skill = open(os.path.join(SKILLS, "crd-impact-analysis", "SKILL.md"),
                 encoding="utf-8").read()
    agent = open(os.path.join(AGENTS, "crd-impact-analyzer.md"), encoding="utf-8").read()

    # Producer and schema must agree, and the sample must parse -- P10's shape is a producer
    # and a spec that drifted, so compare them rather than reading each.
    for label, text in (("crd-format.md", fmt), ("crd-impact-analysis", skill),
                        ("crd-impact-analyzer", agent)):
        m = re.search(r"<affected-contracts>.*?</affected-contracts>", text, re.S)
        assert m, f"{label} does not carry <affected-contracts>"
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(m.group(0))
        except Exception as e:
            raise AssertionError(f"{label}'s <affected-contracts> sample does not parse: {e}")
        kinds = {c.get("kind") for c in root.findall("contract")}
        assert None not in kinds, f"{label} has a <contract> with no kind"
        assert {"api", "schema"} <= kinds, (
            f"{label}'s sample drops a kind PROJECT.md has always had: {sorted(kinds)}")
        assert kinds - {"api", "schema"}, (
            f"{label}'s sample shows only api and schema, so it does not demonstrate the open "
            f"set that is the entire point of the change: {sorted(kinds)}")
        for c in root.findall("contract"):
            assert c.get("ref"), f"{label} has a <contract> with no ref"

    # The old elements stay READABLE. Every CRD written before this exists.
    assert "affected-apis" in fmt, (
        "crd-format.md no longer mentions <affected-apis>. It is deprecated, not deleted -- "
        "every CRD written before this change carries it, and item 41 rewrites them")
    assert re.search(r"affected-apis.*[Dd]eprecated", fmt), (
        "<affected-apis> is present but not marked deprecated, so a reader cannot tell which "
        "of the two shapes to write")

    # The reader must refuse clearly rather than reporting an empty impact.
    assert prose("do not report an empty impact") in prose(skill).lower(), (
        "crd-impact-analysis does not say what to do when the registry it needs is absent. "
        "check-project-md.py requires ANY registry, not a particular one, so it will not have "
        "stopped a project that lacks the kind this analysis reads -- and an empty impact "
        "reported as a finding is worse than a refusal")

    # And the layer derivation must key off the new shape, or item 31 reads a dead element.
    caller = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    phase3 = caller[caller.find("### Phase 3:"):caller.find("### Phase 4:")]
    # Per ROW, not per section. The mutant that got through reverted only the foundation row
    # to `<affected-schemas>`; the backend row still said "contract" and "kind=", so a check
    # looking for those anywhere in Phase 3 passed while half the derivation read a deprecated
    # element. Two rows, two independent assertions.
    rows = {}
    for line in phase3.splitlines():
        m = re.match(r"\s*\|\s*`?([0-9]-[a-z]+)`?\s*\|[^|]*\|([^|]*)\|", line)
        if m:
            rows[m.group(1)] = m.group(2)
    for layer in ("1-foundation", "2-backend"):
        assert layer in rows, f"the derivation table lost its {layer} row"
        evidence = rows[layer]
        assert "contract" in evidence, (
            f"{layer}'s evidence column is {evidence.strip()!r}, which does not read "
            f"<affected-contracts>. Item 57 generalised impact analysis from APIs to contracts; "
            f"a derivation still keyed to the deprecated element puts an event or command "
            f"change in no tier at all")
        for dead in ("<affected-apis>", "<affected-schemas>"):
            assert dead not in evidence, (
                f"{layer}'s evidence column still reads {dead}, which item 57 deprecated")


# ------------------------------------------------------------------- schema core

SCHEMA = os.path.join(REPO, "schema")

# The four artefact root elements. A template for one of these is schema, and schema in a
# command file cannot be cited by a skill -- which is how three separate definitions of
# `<criterion>` came to exist and drift apart (item 44).
ARTEFACT_ROOTS = {"prd", "crd", "feature", "what-next"}


def md_links(text):
    """(label, target) for every inline markdown link whose target is a local path."""
    out = []
    for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        out.append((label, target.split("#", 1)[0]))
    return out


def xml_bodies(text):
    """The body of every ```xml fenced block, in order."""
    return re.findall(r"```xml\n(.*?)```", text, re.S)


def xml_blocks(text):
    """Root element name of every ```xml fenced block, in order."""
    roots = []
    for body in re.findall(r"```xml\n(.*?)```", text, re.S):
        m = re.search(r"<([A-Za-z][\w-]*)", body)
        if m:
            roots.append(m.group(1))
    return roots


@check("the schema core is one definition that both paths cite -- and its citations resolve",
       finding="P30")
def _():
    """Item 44.

    Three documents restated the criterion shape before the core existed and had already
    drifted: `crd-format.md` marks `<scope>` and `<confidence>` required, and the command that
    writes CRDs emitted neither.

    Asserting that drift is gone by grepping for a phrase would survive the drift coming back.
    So this parses instead:

      1. the core declares a version, and it is the one SCHEMAS.json calls current;
      2. every local link out of the core resolves to a file that exists;
      3. the core's "who cites this file" table is not aspirational -- each named document
         really does link to the core, or to the intermediary its own row names.

    (3) is the load-bearing one. A row added without wiring is exactly how a shared definition
    becomes a stored one.
    """
    core_path = os.path.join(SCHEMA, "core.md")
    assert os.path.isfile(core_path), "schema/core.md does not exist"
    core = open(core_path, encoding="utf-8").read()

    m = re.search(r'<schema-core\s+version="([^"]+)"\s*/>', core)
    assert m, "schema/core.md declares no <schema-core version=...>"
    declared = m.group(1)

    schemas = json.load(open(os.path.join(REPO, "tests", "fixture", "prd", "SCHEMAS.json"),
                             encoding="utf-8"))
    assert declared == schemas["current"], (
        f"schema/core.md declares {declared!r}; SCHEMAS.json calls {schemas['current']!r} "
        f"current. A core that has moved on from its fixtures is a migration nobody rehearsed")

    for _label, target in md_links(core):
        resolved = os.path.normpath(os.path.join(SCHEMA, target))
        assert os.path.isfile(resolved), f"schema/core.md links {target}, which does not exist"

    # Scope to the citation table's own section. Matching the whole document would let any
    # other table in it satisfy the check.
    region = core.split("## Who cites this file", 1)
    assert len(region) == 2, "schema/core.md has no 'Who cites this file' section"
    rows = [r.strip() for r in region[1].splitlines() if r.strip().startswith("|")]
    rows = [r for r in rows[2:] if r]           # drop the header and its rule
    assert len(rows) >= 6, f"only {len(rows)} citing documents listed; the table is a stub"

    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        links = md_links(cells[0])
        assert links, f"citation row names no document: {row}"
        rel = links[0][1]
        doc = os.path.normpath(os.path.join(SCHEMA, rel))
        assert os.path.isfile(doc), f"citation row names {rel}, which does not exist"

        doc_links = md_links(open(doc, encoding="utf-8").read())
        targets = {os.path.basename(t) for _l, t in doc_links}
        via = re.search(r"via `([^`]+)`", cells[1])
        wanted = via.group(1) if via else "core.md"
        assert wanted in targets, (
            f"{rel} is listed as citing the core"
            + (f" via {wanted}" if via else "")
            + f", but links no {wanted}. A row without a citation is a claim, not a citation")

        # An indirect citation is a chain, and a chain is only as good as its second hop.
        # Asserting the first hop alone would pass while the intermediary had quietly stopped
        # citing the core -- which is the drift this whole item exists to stop.
        if via:
            # Resolve the intermediary from the citing document's own link, not by guessing a
            # directory: `crd-format.md` lives under skills/crd/references/ and `prd-format.md`
            # beside the core, and only the citing file knows which.
            hop_rel = next(t for _l, t in doc_links if os.path.basename(t) == wanted)
            hop = os.path.normpath(os.path.join(os.path.dirname(doc), hop_rel))
            assert os.path.isfile(hop), f"{rel} cites the core via {hop_rel}, which does not exist"

            # Scoped to the intermediary's PREAMBLE -- everything before its first section.
            # "links core.md somewhere" is satisfied by any passing mention and cannot be
            # falsified by one edit, which makes it decorative. A format document has to say
            # up front that its shared elements are defined elsewhere, because a reader who
            # gets as far as the templates without being told has already been misled.
            preamble = re.split(r"^## ", open(hop, encoding="utf-8").read(), 1, re.M)[0]
            assert "core.md" in {os.path.basename(t) for _l, t in md_links(preamble)}, (
                f"{rel} reaches the core through {wanted}, but {wanted} does not cite core.md "
                f"before its first section -- the chain is broken at its second hop")


@check("no artefact template lives in a command file", finding="P30")
def _():
    """Item 44's first consequence, and the mechanism behind the drift it fixes.

    A template inside `commands/*.md` cannot be cited by a skill, so the skill grows a copy.
    This parses every fenced xml block in the two commands and in the orchestrating skill and
    asserts none is rooted at an artefact element -- a structural claim about what the block
    IS, rather than a search for forbidden words.

    `<step>` fragments stay: they are the payload of an instruction, and the one that survives
    names the schema file defining its shape.
    """
    offenders, cites = [], []
    homes = {
        os.path.join(COMMANDS, "prd.md"): "prd-format.md",
        os.path.join(COMMANDS, "crd.md"): "crd-format.md",
        os.path.join(SKILLS, "crd", "SKILL.md"): "crd-format.md",
    }
    for path, home in homes.items():
        text = open(path, encoding="utf-8").read()
        for root in xml_blocks(text):
            if root in ARTEFACT_ROOTS:
                offenders.append(f"{os.path.relpath(path, REPO)} carries a <{root}> template")
        if home not in {os.path.basename(t) for _l, t in md_links(text)}:
            cites.append(f"{os.path.relpath(path, REPO)} links no {home}")

    assert not offenders, "\n    " + "\n    ".join(offenders)
    assert not cites, (
        "a command that writes an artefact must name where the artefact is defined, or the "
        "template comes back:\n    " + "\n    ".join(cites))
# ------------------------------------------------------- status vocabularies (45)

# The four tags core §3 names, and the file each belongs to. `<status>` is deliberately not a
# key: it survived the rename, and it is the only one of the four with a shipped reader.
RENAMED_TAGS = {
    "definition": "a PRD feature file's <meta>",
    "workflow": "a CRD's <meta>",
    "built": "PROJECT.md's <feature>",
}


@check("a frozen fixture is frozen -- by hash, not by intention", finding="P28")
def _():
    """Item 43's rule 2, which had no enforcement until item 45 created something to freeze.

    A superseded fixture is item 41's migration INPUT. If it drifts, the migration is compared
    against an output whose input has quietly moved, and the comparison still passes -- which is
    the worst available failure, because it looks like proof.
    """
    _path, reg = schema_registry()
    frozen = {n: v for n, v in (reg.get("versions") or {}).items() if v.get("frozen")}
    assert frozen, "no fixture is frozen, so rule 2 guards nothing"

    for name, v in frozen.items():
        recorded = v.get("frozen_sha256") or ""
        assert re.fullmatch(r"[0-9a-f]{64}", recorded), (
            f"{name} is marked frozen but records no sha256. Rule 2 is a comment until the "
            f"digest is written down")
        actual = fixture_digest(name)
        assert actual == recorded, (
            f"{name} is frozen and has changed.\n"
            f"      recorded {recorded}\n"
            f"      actual   {actual}\n"
            f"    If the change is deliberate -- the migration's expected output moved -- paste "
            f"the actual digest into SCHEMAS.json. If it is not, this is the edit rule 2 exists "
            f"to catch")


@check("three status vocabularies, three distinct names -- and the fourth keeps the word",
       finding="P29")
def _():
    """Item 45.

    The defect was one word meaning four things, so the check has to be about the *set* of
    names, not about any one document's wording. It reads core §3's table as data -- the tag,
    the file it lives in, and its values -- and asserts against that:

      1. the four rows carry four distinct tags, and exactly one is still `<status>`;
      2. no two rows share a value set, or the rename bought nothing;
      3. the three renamed tags actually appear in the documents that define them, and the
         old spelling does not survive as a template anyone would copy.

    (1) is what the item is. (2) is why it was worth doing -- three of the four vocabularies
    contain `in-progress`, which is what made reading the wrong tag return a plausible answer
    rather than an error.
    """
    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()
    region = core.split("## 3. Status", 1)
    assert len(region) == 2, "schema/core.md has no status section"
    region = region[1].split("\n## ", 1)[0]

    rows = [r.strip() for r in region.splitlines() if r.strip().startswith("|")]
    rows = [r for r in rows[2:] if r]
    assert len(rows) == 4, f"core §3 lists {len(rows)} status vocabularies; item 45 names four"

    tags, valuesets = [], []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        tag = re.search(r"`([^`]+)`", cells[0])
        assert tag, f"a status row names no tag: {row}"
        tags.append(tag.group(1))
        valuesets.append(frozenset(re.findall(r"`([a-z-]+)`", cells[3])))

    assert len(set(tags)) == 4, (
        f"core §3's four rows carry {len(set(tags))} distinct tags ({tags}). One word for two "
        f"things is the whole defect item 45 exists to remove")
    survivors = [t for t in tags if t == "<status>"]
    assert len(survivors) == 1, (
        f"{len(survivors)} rows still spell the tag `<status>`. Exactly one keeps the word -- "
        f"the document-level one, which is the only one with a shipped reader")

    # If the vocabularies were disjoint, sharing a tag would have been merely untidy. The
    # specific overlap is the argument: `in-progress` means three different things in three of
    # the four, so reading the wrong tag returned a PLAUSIBLE answer rather than an error.
    #
    # "some pair overlaps" was the first version of this assertion and it could not be broken
    # by any single edit -- six pairs satisfied it. Naming the value and the count makes it a
    # claim about the thing that actually motivated the rename.
    shared = [v for v in valuesets if "in-progress" in v]
    assert len(shared) >= 3, (
        f"`in-progress` now appears in {len(shared)} of the four status vocabularies. Core §3 "
        f"no longer records why one word for four things was dangerous rather than untidy")

    # And the rename must have reached every template, not just the table describing them.
    # UNIVERSALLY quantified, per document: `any(...)` passed while half the templates in
    # project-format.md still wrote the old attribute, because the other half satisfied it.
    prd_fmt = open(os.path.join(SCHEMA, "prd-format.md"), encoding="utf-8").read()
    feature_templates = [b for b in xml_bodies(prd_fmt) if b.lstrip().startswith("<feature>")]
    assert feature_templates, "schema/prd-format.md carries no <feature> template"
    for b in feature_templates:
        assert "<definition>" in b, (
            "a <feature> template in schema/prd-format.md does not write <definition>. A "
            "rename that reaches the prose and not the template is a rename nobody will follow")

    crd_fmt = open(os.path.join(SKILLS, "crd", "references", "crd-format.md"),
                   encoding="utf-8").read()
    meta_templates = [b for b in xml_bodies(crd_fmt) if "<created>" in b]
    assert meta_templates, "crd-format.md carries no CRD <meta> template"
    for b in meta_templates:
        assert "<workflow>" in b, (
            "a CRD <meta> template in crd-format.md does not write <workflow>")

    proj_fmt = open(os.path.join(SKILLS, "crd", "references", "project-format.md"),
                    encoding="utf-8").read()
    entries = re.findall(r"<feature id=\"[^\"]+\"[^>]*>", proj_fmt)
    assert entries, "project-format.md carries no <feature> entry"
    for e in entries:
        assert "built=" in e, (
            f"a PROJECT.md feature entry still writes the old attribute: {e}")

    # Backward read is a policy, and a policy with no statement is a guess made per reader.
    flat = prose(core)
    assert re.search(r"Accepted on read; never written", flat), (
        "core §3 does not say what a reader does with an artefact written before the rename, "
        "so each reader decides separately -- which is how two of them disagree")


@check("nothing hardcodes a schema fixture version", finding="P28")
def _():
    """Item 45 created the second version, and every path naming `schema-1` would have gone on
    exercising the superseded copy while reporting on the current schema.

    The registry cannot keep the fixture set honest if its readers route around it. Scoped to
    the test harness, because that is who reads fixtures.
    """
    offenders = []
    for name in sorted(os.listdir(os.path.join(REPO, "tests"))):
        if not name.endswith(".py"):
            continue
        path = os.path.join(REPO, "tests", name)
        for i, line in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
            if re.search(r'"schema-\d+"', line) and "reg[" not in line:
                offenders.append(f"tests/{name}:{i}: {line.strip()}")
    for name in sorted(os.listdir(os.path.join(REPO, "tests", "fixture"))):
        if not name.endswith(".py"):
            continue
        path = os.path.join(REPO, "tests", "fixture", name)
        for i, line in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
            if re.search(r'"schema-\d+"', line):
                offenders.append(f"tests/fixture/{name}:{i}: {line.strip()}")

    assert not offenders, (
        "these name a schema version directly instead of asking SCHEMAS.json which is "
        "current:\n    " + "\n    ".join(offenders))
# ------------------------------------------------------------ migration (41)

MIGRATE = os.path.join(SCHEMA, "scripts", "migrate.py")


def _run_migrate(*args):
    return subprocess.run([sys.executable, MIGRATE, *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _mechanical_pair():
    """(from, to) for a step the registry calls fully mechanical, or None.

    Which steps are mechanical is SCHEMAS.json's to declare. Hardcoding schema-1 -> schema-2
    here would have quietly stopped exercising the golden comparison the moment a third version
    arrived -- which is the same defect item 45 found in setup_fixture.py, one file along.
    """
    _path, reg = schema_registry()
    versions = list(reg.get("versions") or {})
    for i, name in enumerate(versions):
        if i and (reg["versions"][name].get("migration_from_previous") == "mechanical"):
            return versions[i - 1], name
    return None


@check("the migration turns the old fixture into the new one, exactly -- by running it",
       finding="P28")
def _():
    """Item 41's golden comparison, which is the whole reason item 43 versioned the fixtures.

    Run the migration over a frozen tree and assert the result is byte-for-byte the next
    version's tree. A postcondition asserts what someone thought to assert; a golden comparison
    catches the losses nobody thought of, because the expected output was authored separately.

    Then run it AGAIN over its own output. Re-running must be a no-op, because a 65-file
    migration will be interrupted -- and the marker of `already migrated` is the shape, so
    idempotence is a property of the rules rather than of a stamp.

    Scoped to a step the registry calls MECHANICAL. A step carrying judgements cannot be
    compared this way and has a check of its own; conflating them would have meant either
    weakening this one or claiming the script does something it is forbidden to do.
    """
    import filecmp
    import shutil
    import tempfile

    assert os.path.isfile(MIGRATE), "schema/scripts/migrate.py is missing"
    pair = _mechanical_pair()
    assert pair, ("no step is declared `migration_from_previous: mechanical`, so nothing can be "
                  "compared byte-for-byte and item 41's golden comparison has no subject")
    src_version, target = pair

    root = tempfile.mkdtemp(prefix="prd-migrate-")
    try:
        work = os.path.join(root, "tree")
        shutil.copytree(os.path.join(REPO, "tests", "fixture", "prd", src_version), work)

        # --check BEFORE migrating, which is the only run in which its answer can be wrong.
        # Asserting it only on an already-migrated tree exercises nothing: every branch agrees
        # there, and a --check that always returned 0 would pass.
        p = _run_migrate(work, "--to", target, "--quiet", "--check")
        assert p.returncode == 1, (
            f"--check called a {src_version} tree finished (exit {p.returncode}). 'The migration "
            f"ran' and 'the migration finished' are different claims and this is the difference")

        p = _run_migrate(work, "--to", target, "--quiet")
        assert p.returncode == 0, (
            f"migrating {src_version} -> {target} exited {p.returncode}:\n{p.stdout}\n{p.stderr}")

        expected = os.path.join(REPO, "tests", "fixture", "prd", target)
        cmp = filecmp.dircmp(work, expected)

        def differences(d, prefix=""):
            out = [prefix + n for n in (d.left_only + d.right_only + d.diff_files + d.funny_files)]
            for name, sub in d.subdirs.items():
                out += differences(sub, prefix + name + "/")
            return out

        diffs = differences(cmp)
        assert not diffs, (
            f"the migration's output is not the {target} fixture. A golden comparison exists "
            f"to catch exactly this:\n    " + "\n    ".join(diffs))

        # Idempotence, measured rather than asserted: a second run must change nothing.
        before = {}
        for dp, _dn, fn in os.walk(work):
            for n in fn:
                before[os.path.join(dp, n)] = open(os.path.join(dp, n), "rb").read()

        p = _run_migrate(work, "--to", target, "--quiet")
        assert p.returncode == 0, f"re-running the migration exited {p.returncode}: {p.stderr}"
        for full, content in before.items():
            assert open(full, "rb").read() == content, (
                f"a second migration run modified {os.path.relpath(full, work)}. Re-entering a "
                f"partly migrated tree has to be safe, and it is only safe if this holds")

        # And --check must agree that it finished. "The migration ran" is a different claim.
        p = _run_migrate(work, "--to", target, "--quiet", "--check")
        assert p.returncode == 0, (
            f"--check disagrees that the tree is in {target}:\n{p.stdout}\n{p.stderr}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _strip_judgement(text, elements):
    """Remove the elements a mixed step's migration is forbidden to produce.

    What is left is exactly what the script was supposed to do, so comparing it to the fixture
    asserts the mechanical half and says nothing about the judgement half -- which is the only
    honest golden comparison for a step that carries both.
    """
    for name in elements:
        text = re.sub(r"[ \t]*<%s\b[^>]*/>\n?" % name, "", text)
        text = re.sub(r"[ \t]*<%s\b.*?</%s>\n?" % (name, name), "", text, flags=re.S)
    # Blank lines go too. Removing an element leaves the whitespace that framed it, and
    # that whitespace is not content -- comparing it would make the check fail on where a
    # paragraph break happened to fall rather than on what the migration did.
    return "\n".join(ln for ln in text.splitlines() if ln.strip())


@check("a migration it may not finish does the half it can, and says which half -- by running it",
       finding="P28")
def _():
    """Items 33, 41 and the schema-4 group together.

    A step is `mixed` when part of it is mechanical and part is a judgement the guide forbids a
    machine to make -- rewriting a Given/When/Then into EARS and assigning its `pattern`, or
    writing a `<user-story>` there is nothing in the file to derive.

    A script that stopped at the boundary would leave the mechanical work undone; one that
    crossed it would invent the judgement. So it does its half, reports PARTIAL, and `--check`
    refuses the tree -- and each of those three is asserted, because two of them passing without
    the third is exactly the failure that reads as success.

    EVERY mixed step is exercised, not the first one found. Testing one of two leaves the other
    unchecked while reporting green, which is the site-counting defect in its other direction.
    """
    import shutil
    import tempfile

    _path, reg = schema_registry()
    versions = list(reg.get("versions") or {})
    mixed = [(versions[i - 1], n) for i, n in enumerate(versions)
             if i and reg["versions"][n].get("migration_from_previous") == "mixed"]
    assert mixed, "no step is declared `mixed`, so the PARTIAL state is unexercised"

    for src_version, target in mixed:
        judgement = reg["versions"][target].get("judgement_elements") or []
        assert judgement, (
            f"{target} is a mixed step and names no judgement_elements, so there is nothing to "
            f"exclude from the comparison and nothing recorded about what the script may not do")

        root = tempfile.mkdtemp(prefix="prd-partial-")
        try:
            work = os.path.join(root, "tree")
            shutil.copytree(os.path.join(REPO, "tests", "fixture", "prd", src_version), work)

            p = _run_migrate(work, "--to", target)
            assert p.returncode == 0, (
                f"{src_version} -> {target}: the mechanical half failed: {p.stdout}\n{p.stderr}")
            assert "PARTIAL" in p.stdout or "PARTIAL" in p.stderr, (
                f"{src_version} -> {target} carries judgements and reported no PARTIAL state, so "
                f"'the script ran' and 'the migration finished' are indistinguishable:\n"
                f"{p.stdout}\n{p.stderr}")

            p = _run_migrate(work, "--to", target, "--quiet", "--check")
            assert p.returncode == 1, (
                f"{src_version} -> {target}: --check called a partly migrated tree finished "
                f"(exit {p.returncode}). The whole point of PARTIAL is that this run refuses")

            expected_root = os.path.join(REPO, "tests", "fixture", "prd", target)
            for dp, _dn, fn in os.walk(work):
                for n in sorted(fn):
                    rel = os.path.relpath(os.path.join(dp, n), work)
                    got = open(os.path.join(dp, n), encoding="utf-8").read()
                    want = open(os.path.join(expected_root, rel), encoding="utf-8").read()

                    # Everything OUTSIDE the judgement surface must match the fixture exactly.
                    assert _strip_judgement(got, judgement) == _strip_judgement(want, judgement), (
                        f"{src_version} -> {target}: {rel} differs from the fixture outside "
                        f"{judgement}. That is the half the script owns, so anything it moved "
                        f"there, it moved by accident")

                    # And it must not have PRODUCED any of the forbidden elements. An element
                    # already in the source is not evidence either way -- the script leaving
                    # `<tbd-items>` alone is required, not forbidden -- so the exclusion is
                    # derived from the source file rather than hardcoded, which is what stops
                    # this list going stale the next time a step is added.
                    source = open(os.path.join(REPO, "tests", "fixture", "prd", src_version,
                                               rel), encoding="utf-8").read()
                    for name in judgement:
                        if f"<{name}" in source:
                            continue
                        assert f"<{name}" not in got, (
                            f"{src_version} -> {target}: {rel} carries a <{name}> the script "
                            f"produced. Assigning it is a judgement the guide forbids")

            # Criteria and definition exist before the step, so their ABSENCE cannot be the test.
            # The specific forbidden act is the attribute and the value, so assert those.
            if "acceptance-criteria" in judgement:
                for dp, _dn, fn in os.walk(work):
                    for n in sorted(fn):
                        got = open(os.path.join(dp, n), encoding="utf-8").read()
                        rel = os.path.relpath(os.path.join(dp, n), work)
                        # Asserted per criterion, against the SAME criterion in the source, and
                        # only where the step actually touched it. Both halves of this were once
                        # asserted over every criterion in the file, which held while every
                        # criterion in a mixed step came from a migration -- schema-5 is where
                        # that stopped being true. Its fixture CRD carries two AUTHORED criteria,
                        # which legitimately have a `pattern` and legitimately have no
                        # `derived-from` (core §2: migration only), beside four migrated from
                        # <requirement>, which are the opposite. Sweeping the file cannot tell
                        # them apart; comparing to the source can, and it does not weaken the
                        # earlier steps -- for schema-2 -> schema-3 the script rewrites every
                        # criterion, so every one is still checked.
                        source = open(os.path.join(REPO, "tests", "fixture", "prd", src_version,
                                                   rel), encoding="utf-8").read()
                        before = {}
                        for t in re.findall(r"<criterion\b([^>]*)>", source):
                            cid = re.search(r'id="([^"]*)"', t)
                            before[cid.group(1) if cid else None] = t
                        for t in re.findall(r"<criterion\b([^>]*)>", got):
                            cid = re.search(r'id="([^"]*)"', t)
                            if before.get(cid.group(1) if cid else None) == t:
                                continue  # the step did not touch it; it is the author\'s
                            assert 'priority="' in t and "derived-from=" in t, (
                                f"{rel} has a criterion this step wrote that is missing priority "
                                f"or derived-from. The value is written in rather than "
                                f"defaulted, or a partly assigned corpus cannot be told from a "
                                f"finished one")
                            assert "pattern=" not in t, (
                                f"{rel} has a criterion carrying a `pattern` the script "
                                f"assigned. A pattern derived by the heuristics it exists to "
                                f"replace is circular")
        finally:
            shutil.rmtree(root, ignore_errors=True)


@check("a file the migration cannot place stops it, and is named -- by running it",
       finding="P28")
def _():
    """Item 41's escalation path: *stop and report this file*, never transform it anyway.

    The asymmetry is the point, so both halves are exercised. A file that cannot be placed must
    (a) exit non-zero, (b) be named, and (c) LEAVE THE TREE ALONE -- including the files beside
    it that were perfectly migratable. Reporting a problem while half-applying the change is
    worse than either refusing or proceeding.
    """
    import shutil
    import tempfile

    _path, reg = schema_registry()
    target = reg["current"]

    root = tempfile.mkdtemp(prefix="prd-escalate-")
    try:
        work = os.path.join(root, "tree")
        os.makedirs(work)
        good = os.path.join(work, "ok.md")
        open(good, "w", encoding="utf-8", newline="\n").write(
            "<feature>\n  <meta>\n    <status>defined</status>\n  </meta>\n</feature>\n")
        stray = os.path.join(work, "stray.md")
        open(stray, "w", encoding="utf-8", newline="\n").write("prose, and no root element\n")
        odd = os.path.join(work, "odd.md")
        open(odd, "w", encoding="utf-8", newline="\n").write(
            "<feature>\n  <meta>\n    <name>X</name>\n  </meta>\n</feature>\n")

        untouched = {p: open(p, "rb").read() for p in (stray, odd)}

        p = _run_migrate(work, "--to", target, "--quiet")
        assert p.returncode == 2, (
            f"a file matching no precondition did not escalate (exit {p.returncode}). Exit 2 is "
            f"separate from exit 1 precisely so that 'nothing was written for these' is sayable")
        for name in ("stray.md", "odd.md"):
            assert name in p.stderr, f"the escalation does not name {name}:\n{p.stderr}"

        for path, content in untouched.items():
            assert open(path, "rb").read() == content, (
                f"{os.path.basename(path)} was escalated AND modified. Escalation means the "
                f"tree is exactly as it was found")

        # The half that must still work: a file it CAN place is migrated in the same run.
        assert "<definition>defined</definition>" in open(good, encoding="utf-8").read(), (
            "one unplaceable file stopped the files it has nothing to do with. Per-file is the "
            "unit of decision, and a run that gives up wholesale cannot be resumed")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the migration guide has an executor, and the executor cites the guide", finding="P24")
def _():
    """Item 41: the guide is 'a specification with a consumer', so it is held to the same rule
    as every other producer/consumer pair here -- the consumer must be named and must exist.

    Three named consumers, each verified as a link that resolves rather than as a mention:
    the script that runs the mechanical rules, the agent that performs the judgements, and the
    skill that dispatches the agent per file.
    """
    guide = os.path.join(SCHEMA, "migration.md")
    assert os.path.isfile(guide), "schema/migration.md does not exist"
    text = open(guide, encoding="utf-8").read()

    for _label, target in md_links(text):
        resolved = os.path.normpath(os.path.join(SCHEMA, target))
        assert os.path.isfile(resolved), f"migration.md links {target}, which does not exist"

    assert "migrate.py" in text, "the guide names no script for its mechanical rules"
    assert "schema-migrator" in text, "the guide names no agent for its judgements"

    # And the citation runs the other way too, or the guide is prose beside a program.
    #
    # A RESOLVING LINK, not a mention. `"migration.md" in body` was the first version and it
    # counted the agent's own frontmatter description as a citation, so removing the actual
    # link changed nothing. One site, and it is the site that has to work.
    agent_path = os.path.join(AGENTS, "schema-migrator.md")
    skill_path = os.path.join(SKILLS, "migrate", "SKILL.md")
    agent = open(agent_path, encoding="utf-8").read()
    skill = open(skill_path, encoding="utf-8").read()

    for name, path_, body in (("schema-migrator", agent_path, agent),
                              ("migrate", skill_path, skill)):
        links = [t for _l, t in md_links(body) if os.path.basename(t) == "migration.md"]
        assert links, (
            f"{name} performs a migration without linking schema/migration.md, so the rules it "
            f"follows are whatever it remembers")
        for t in links:
            resolved = os.path.normpath(os.path.join(os.path.dirname(path_), t))
            assert os.path.isfile(resolved), f"{name} links {t}, which does not exist"
        assert "migrate.py" in body, f"{name} never runs the script that owns the mechanical rules"

    # The escalation instruction is the one most likely to erode, and the erosion looks like
    # helpfulness. Scoped to the ONE line in each document that owns the claim -- a document-wide
    # search matched three other sentences and survived the row being reversed.
    owners = {
        "migration.md": (text, "Escalation is always the same"),
        "schema-migrator": (agent, "ESCALATE"),
        "migrate": (skill, "no precondition"),
    }
    for name, (body, anchor) in owners.items():
        lines = [ln for ln in body.splitlines() if anchor in ln and not ln.startswith("#")]
        assert lines, f"{name} has no line about a file the migration cannot place"
        assert any(re.search(r"\bstop\b", prose(ln), re.I) for ln in lines), (
            f"{name}'s escalation instruction no longer says to stop:\n      "
            + "\n      ".join(ln.strip() for ln in lines)
            + "\n    'Transform it anyway' is the failure this path exists to prevent")
# ----------------------------------------------------------- EARS criteria (33/34)

EARS_PATTERNS = {"ubiquitous", "state-driven", "event-driven", "optional-feature",
                 "unwanted-behaviour", "complex"}


@check("a criterion is one EARS sentence with a pattern and a priority", finding="P23")
def _():
    """Items 33 and 34.

    Given/When/Then is a SCENARIO format and cannot state a requirement, which is why the CRD
    path needed a second list to hold requirements at all. Replacing it is what makes "covers
    the edge cases" an attribute count rather than a judgement.

    Parsed, not matched. Every criterion in every template on both paths is read as XML and
    checked for the two attributes and the word `shall` -- so this survives any rewording and
    fails the moment one template is updated and the other is not, which is the drift item 44
    was extracted to stop.
    """
    templates = {
        "schema/prd-format.md": os.path.join(SCHEMA, "prd-format.md"),
        "schema/core.md": os.path.join(SCHEMA, "core.md"),
        "crd-format.md": os.path.join(SKILLS, "crd", "references", "crd-format.md"),
    }

    seen = 0
    for label, path in templates.items():
        for body in xml_bodies(open(path, encoding="utf-8").read()):
            for attrs, inner in re.findall(r"<criterion\b([^>]*)>(.*?)</criterion>", body, re.S):
                seen += 1
                a = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
                assert "id" in a, f"{label}: a criterion carries no id"
                assert a.get("pattern") in EARS_PATTERNS, (
                    f"{label}: criterion {a.get('id')} has pattern {a.get('pattern')!r}, which "
                    f"is not one of the six EARS patterns")
                assert re.fullmatch(r"P[012]", a.get("priority", "")), (
                    f"{label}: criterion {a.get('id')} has priority {a.get('priority')!r}; "
                    f"item 34 chose P0|P1|P2 precisely so it could not be read as MoSCoW")
                flat = " ".join(inner.split())
                assert "<given>" not in flat and "<when>" not in flat, (
                    f"{label}: criterion {a.get('id')} is still a Given/When/Then triple")
                assert re.search(r"\bshall\b", flat), (
                    f"{label}: criterion {a.get('id')} contains no `shall`. An EARS criterion "
                    f"states what the system must do; without it this is a scenario again")
    assert seen >= 6, f"only {seen} criteria in the schema documents; the templates are a stub"

    # The taxonomy has to be WRITTEN DOWN somewhere a person assigning one can read, and all six
    # of it -- the value of the attribute is that it distinguishes the failure cases from the
    # happy path, which five patterns cannot do.
    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()
    region = core.split("### The six patterns", 1)
    assert len(region) == 2, "core.md does not enumerate the EARS patterns"
    listed = set(re.findall(r"`([a-z-]+)`", region[1].split("\n## ", 1)[0]))
    assert EARS_PATTERNS <= listed, (
        f"core.md's pattern table is missing {sorted(EARS_PATTERNS - listed)}")

    # And the consumer has to do something with the attribute, or it is decoration.
    gen = open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
               encoding="utf-8").read()
    for pattern in EARS_PATTERNS:
        assert pattern in gen, (
            f"breakdown-generate-tasks says nothing about `{pattern}` criteria, so `pattern` "
            f"reaches the generator and changes nothing -- which is the unread element this "
            f"plan exists to remove")


@check("the two priority levels stay in two vocabularies, and the filter says so", finding="P1")
def _():
    """Item 34's whole design, and the reason it is not MoSCoW.

    Feature priority selects WHICH FEATURES; criterion priority selects WHICH CRITERIA WITHIN
    THEM. Sharing a vocabulary would make every flag, report line and conversation ambiguous
    about which level it meant -- which is what item 29 refused when it declined to run
    `<needs-clarification>` beside `<gaps>`.
    """
    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()
    region = core.split("## 4. Priority", 1)
    assert len(region) == 2, "core.md has no priority section"
    region = region[1].split("\n## ", 1)[0]

    # The FIRST table only. §4 grew a second one at item 47 -- the MoSCoW -> P0|P1|P2 map --
    # and sweeping every row in the section counted eight "levels", which is the shape of check
    # this repository keeps getting wrong: a region without a shape. Take the first contiguous
    # run of table rows, which is the one that is about levels.
    table, seen = [], False
    for line in region.splitlines():
        if line.strip().startswith("|"):
            table.append(line.strip())
            seen = True
        elif seen:
            break
    rows = [r for r in table[2:] if r]
    assert len(rows) == 2, f"core §4's first table lists {len(rows)} levels; item 34 defines two"

    vocabs = []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        vocabs.append(set(re.findall(r"`([\w-]+)`", cells[2])))

    assert not (vocabs[0] & vocabs[1]), (
        f"the two priority levels share {sorted(vocabs[0] & vocabs[1])}. They are in different "
        f"vocabularies on purpose, so that no flag or report line is ambiguous about which "
        f"level it means")
    assert {"P0", "P1", "P2"} <= (vocabs[0] | vocabs[1]), "core §4 never names P0|P1|P2"
    assert any("must-have" in v for v in vocabs), "core §4 never names MoSCoW"

    # The flag exists, is ordered against the feature-level one, and reports what it excluded.
    skill = prose(open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read())
    assert "--requirement-level" in skill, "/breakdown gained no --requirement-level flag"
    assert re.search(r"Applied second", skill), (
        "/breakdown does not say which of the two filters runs first. Filtering criteria out of "
        "features that were about to be dropped whole changes nothing and costs a pass")
    assert re.search(r"Report what the filter excluded", skill), (
        "/breakdown never reports what --requirement-level removed. A filter whose effect is "
        "invisible is a filter nobody can check")
# ----------------------------------------------- the feature template's other half (schema-4)

GAP_KINDS = {"specification", "dependency", "decision", "ownership", "evidence"}
EDGE_KINDS = {"data", "runtime", "reference"}


@check("uncertainty has a channel that survives the handoff, and review lets it through",
       finding="P19")
def _():
    """Item 29.

    Banning `TBD` outright is what makes INVENTION the compliant answer: an author who cannot
    write "we have not decided this" writes something plausible instead, and nothing downstream
    can tell the difference. So a marked gap must PASS review and BLOCK execution, while
    unmarked vagueness keeps failing exactly as it did.

    Three things have to hold together or the channel leaks:
      1. the five kinds exist and each says whether it blocks or warns;
      2. every hop preserves the gap -- analysis carries it, the task file carries it;
      3. the reviewer's placeholder ban is scoped AROUND it.
    """
    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()
    region = core.split("## 6. Gaps", 1)
    assert len(region) == 2, "core.md defines no <gaps> element"
    # Bounded at the next section. §6 was the last one when this was written, so an unbounded
    # read worked by accident until core gained a §7 -- whose two-column tables then arrived
    # here as gap kinds and raised IndexError.
    region = region[1].split("\n## ", 1)[0]

    rows = [r.strip() for r in region.split("### The five kinds", 1)[1].splitlines()
            if r.strip().startswith("|")]
    rows = [r for r in rows[2:] if r]
    kinds = {}
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        m = re.search(r"`([a-z]+)`", cells[0])
        if m:
            kinds[m.group(1)] = prose(cells[2])
    assert set(kinds) == GAP_KINDS, (
        f"core §6 declares kinds {sorted(kinds)}; item 29 defines {sorted(GAP_KINDS)}")

    warners = [k for k, v in kinds.items() if re.search(r"\bwarn\b", v, re.I)]
    assert len(warners) >= 2, (
        f"only {warners} warn rather than stop. Three of the five warn on purpose -- an "
        f"overnight run should be halted by a genuine unknown, not by every open item, and a "
        f"boolean `blocking=` could not draw that line")
    # The CELL, not the row. `specification ... yes` matched the second column as happily as
    # the first, so a mutant that flipped "bars defined" to "no" was invisible.
    spec_row = next(r for r in rows if "`specification`" in r)
    bars_definition = [c.strip() for c in spec_row.strip("|").split("|")][1]
    assert re.search(r"\byes\b", prose(bars_definition), re.I), (
        f"core §6's `specification` row says {bars_definition!r} under 'blocks definition'. "
        f"That a specification gap bars `defined` is the one rule here a script can enforce "
        f"without judgement")

    # Every hop. A channel that survives four of five hops delivers nothing.
    analyzer = open(os.path.join(SKILLS, "breakdown-analyze-prd", "SKILL.md"),
                    encoding="utf-8").read()
    assert '"gaps"' in analyzer, "analysis.json carries no gaps, so nothing downstream sees one"
    # Scoped to the SECTION HEADING. Searching the document matched the body sentence as well,
    # so retitling the section "gaps are reviewed and settled here" changed nothing.
    headings = [ln for ln in analyzer.splitlines() if ln.startswith("###") and "gap" in ln.lower()]
    assert headings, "analyze-prd has no section about gaps"
    assert any(re.search(r"carried, never resolved", prose(h), re.I) for h in headings), (
        f"analyze-prd's gaps section is titled {headings!r}. It has to say the gaps are carried "
        f"and not resolved -- a gap this pass quietly answers becomes a requirement nobody "
        f"wrote, arriving with an author's authority")

    task_fmt = open(os.path.join(SKILLS, "breakdown", "references", "task-format-spec.md"),
                    encoding="utf-8").read()
    # A parsed block whose root is <gaps>, not the word in a sentence. The prose describing the
    # rule survived the sample being commented out, and the prose is not what a generator copies.
    assert any(b.lstrip().startswith("<gaps>") for b in xml_bodies(task_fmt)), (
        "task-format-spec.md shows no <gaps> block. A task file is self-contained by mandate, "
        "so an implementer who cannot see the gap fills it in")

    # The corollary, and the thing most likely to be reverted by someone tidying: the ban is on
    # UNMARKED vagueness. Scoped to the line that carries the ban, not the document.
    for rel in ("skills/breakdown/references/review-criteria.md",
                "skills/breakdown-review-tasks/SKILL.md"):
        text = open(os.path.join(REPO, rel), encoding="utf-8").read()
        bans = [ln for ln in text.splitlines() if "placeholder text" in ln]
        assert bans, f"{rel} no longer states a placeholder ban at all"
        for ln in bans:
            assert re.search(r"\bunmarked\b", ln, re.I), (
                f"{rel} bans placeholders without qualifying it to UNMARKED ones:\n      "
                f"{ln.strip()}\n    A declared <gap> failing review is what makes invention the "
                f"compliant answer (item 29)")


@check("feature dependencies are declared edges, and ordering is derived from them",
       finding="P11")
def _():
    """Item 27.

    `what-next.md`'s task-generation order was deduced by a model during `/prd` -- a second
    model's unvalidated inference, produced with more context than `/breakdown` has but with no
    dependency graph and no awareness that layer planning exists to do the job. The durable
    artefact is the dependencies, not the order.

    So: the element exists with a `kind`, the analyser emits the edges, and the component that
    owns ordering is told to derive from them rather than to read a sequence.
    """
    fmt = open(os.path.join(SCHEMA, "prd-format.md"), encoding="utf-8").read()
    region = fmt.split("### `<depends-on>`", 1)
    assert len(region) == 2, "prd-format.md defines no <depends-on> element"
    region = region[1].split("\n### ", 1)[0]

    rows = [r.strip() for r in region.splitlines() if r.strip().startswith("|")]
    kinds = {m.group(1) for r in rows[2:] for m in [re.match(r"\|\s*`([a-z]+)`", r)] if m}
    assert kinds == EDGE_KINDS, f"<depends-on> declares kinds {sorted(kinds)}, not {sorted(EDGE_KINDS)}"
    # NOT through prose(): it strips backticks, so a pattern containing them can never match.
    # The check passed nothing for one run because of exactly that.
    assert "`reference`" in region, "the reference kind is undocumented"

    analyzer = open(os.path.join(SKILLS, "breakdown-analyze-prd", "SKILL.md"),
                    encoding="utf-8").read()
    assert "feature_edges" in analyzer, "analysis.json carries no feature edges"
    assert re.search(r"markdown link between features is not an edge", prose(analyzer), re.I), (
        "analyze-prd does not say a plain link is not a dependency, which is the ambiguity "
        "<depends-on> exists to remove -- re-deriving edges from links puts the guess back")

    planner = open(os.path.join(SKILLS, "breakdown-plan-layers", "SKILL.md"),
                   encoding="utf-8").read()
    flat = prose(planner)
    assert "feature_edges" in planner, "plan-layers never reads the declared edges"
    edge_rows = [ln for ln in planner.splitlines() if re.match(r"\|\s*`reference`", ln.strip())]
    assert edge_rows, "plan-layers does not say what each edge kind constrains"
    assert re.search(r"\bnone\b", prose(edge_rows[0]), re.I), (
        "plan-layers gives `reference` an ordering constraint. That it carries none is the "
        "point of having three kinds rather than a boolean")
    assert re.search(r"You own the ordering", flat), (
        "plan-layers is not told that ordering is its own job, so a sequence recorded during "
        "the interview can still be deferred to -- two producers for one artefact")


@check("the feature template carries intent, significance, and no second priority",
       finding="P8")
def _():
    """Items 1, 2, 5 and 35, which are one template between them.

    Parsed as XML rather than matched: the template is read for the elements it declares, so
    this survives rewording and fails when one of the six items is quietly dropped.
    """
    fmt = open(os.path.join(SCHEMA, "prd-format.md"), encoding="utf-8").read()
    blocks = [b for b in xml_bodies(fmt) if b.lstrip().startswith("<feature>")]
    assert blocks, "prd-format.md carries no <feature> template"
    tpl = blocks[0]

    for element in ("<user-story>", "<gaps>", "<data-model>", "<considerations>",
                    "<depends-on", "<architecturally-significant", "<rationale>",
                    "<superseded-by"):
        assert element in tpl, f"the feature template declares no {element}"

    meta = re.search(r"<meta>(.*?)</meta>", tpl, re.S)
    assert meta, "the feature template has no <meta>"
    assert "<priority>" not in meta.group(1), (
        "the feature template still carries <priority> in <meta>. It duplicates the index "
        "entry with nothing keeping the two in step -- item 1 removes it")

    definition = re.search(r"<definition>([^<]*)</definition>", meta.group(1))
    assert definition, "the feature template declares no <definition>"
    values = set(definition.group(1).split("|"))
    assert {"excluded", "superseded"} <= values, (
        f"<definition> offers {sorted(values)}. `excluded` and `superseded` are how a feature "
        f"that is not being built stays in the PRD as a record instead of vanishing from it")

    # Item 5, which is a decision rather than a deletion: nothing ever had <phases>, and the
    # argument for never adding it has to be written down or it gets added.
    #
    # Scoped to the PARSED TEMPLATE, not to the document. The first version searched the whole
    # file for `<phases>` and failed on the heading of the section explaining why there isn't
    # one -- the F3 mistake in miniature: a check that fails when the absence is documented.
    for block in xml_bodies(fmt):
        assert "<phases>" not in block, (
            "a <phases> element has appeared in a template. Phasing is priority plus gaps")
    for attrs in re.findall(r"<criterion\b([^>]*)>", tpl):
        assert "phase=" not in attrs, (
            "a criterion carries a phase= attribute. Item 5 removed it: a phase says `later` "
            "and carries nothing else, while a gap says why and since when")
    region = fmt.split("### There is no `<phases>` element", 1)
    assert len(region) == 2, (
        "prd-format.md does not record WHY there is no <phases> element. An absence with no "
        "argument beside it is an omission somebody will helpfully correct")
    flat = prose(region[1].split("\n## ", 1)[0])
    assert re.search(r"essential but blocked", flat), (
        "the <phases> decision no longer states the case that looked like it needed a third "
        "axis, which is the only part of the argument a reader will want to check")
    assert re.search(r"\bdemote\b", flat), (
        "the <phases> decision no longer says what a phase would have COST -- forcing an author "
        "to demote something important in order to say it is stuck. Without that sentence the "
        "section records a preference rather than an argument")

    # Item 35 needs a reader, or it is the unread element this plan exists to remove -- and
    # the reader is verified BY RUNNING IT. `"architecturally-significant" in refs` passed
    # while the script's pattern had been renamed to match nothing: the docstring satisfied it.
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-references.py")
    root = tempfile.mkdtemp(prefix="prd-significant-")
    try:
        prd = os.path.join(root, "prd", "features")
        adr = os.path.join(root, "architecture", "decisions")
        os.makedirs(prd)
        os.makedirs(adr)
        open(os.path.join(root, "prd", "index.md"), "w", encoding="utf-8",
             newline="\n").write("<prd><meta><slug>x</slug></meta></prd>\n")
        open(os.path.join(prd, "flagged.md"), "w", encoding="utf-8", newline="\n").write(
            "<feature>\n  <meta>\n    <slug>flagged</slug>\n"
            '    <architecturally-significant because="cross-cutting"/>\n'
            "  </meta>\n</feature>\n")

        p = subprocess.run([sys.executable, script, os.path.join(root, "prd"),
                            "--adr-dir", adr], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        out = p.stdout + p.stderr
        assert "flagged.md" in out and "STALE" in out, (
            f"a feature declaring itself architecturally significant, with no record driving "
            f"it, was not reported. A flag nothing reads is the defect item 23's rule is "
            f"about:\n{out}")
        assert p.returncode == 0, (
            f"the report REFUSED (exit {p.returncode}). The flag is a judgement and its absence "
            f"proves nothing, so this reports and never refuses")

        # And the other half of the asymmetry: a record that drives it silences the report.
        open(os.path.join(adr, "ADR-001-flagged.md"), "w", encoding="utf-8",
             newline="\n").write(
            "# ADR-001: Flagged crosses every context\n\n**Status:** Accepted\n"
            "**Drives:** [Flagged](../../prd/features/flagged.md)\n")
        p = subprocess.run([sys.executable, script, os.path.join(root, "prd"),
                            "--adr-dir", adr], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        assert "flagged.md: is architecturally significant" not in (p.stdout + p.stderr), (
            "a significant feature named by a record's **Drives:** is still reported. The "
            "report would then fire on every flagged feature and be ignored")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("`<considerations>` is unread by design, and says so", finding="P4")
def _():
    """Item 2's smaller half, and the one most likely to erode.

    `<data-model>` earns an element because a consumer must UNDERSTAND it -- analyze-prd reads
    entities and fields and stops inferring them. `<considerations>` earns one because it is the
    catch-all that makes migration lossless, and nothing reads it.

    The distinction between *unread by design* and *unread by oversight* is the whole point, and
    it only exists if it is written down.
    """
    fmt = prose(open(os.path.join(SCHEMA, "prd-format.md"), encoding="utf-8").read())
    assert re.search(r"considerations> is unread by design", fmt), (
        "prd-format.md does not mark <considerations> unread by design, so it is "
        "indistinguishable from an element nobody got round to reading")
    assert re.search(r"verbatim, never dropped", fmt), (
        "the template no longer promises that unrecognised note content survives migration "
        "verbatim. That promise is what makes the two-way split safe at all")
    assert re.search(r"no <relationships> element", fmt, re.I), (
        "prd-format.md does not record that <relationships> was dropped. §4.3 removed it "
        "because <depends-on> already carries the outbound edges, and an absence with no "
        "argument beside it gets helpfully restored")

    analyzer = prose(open(os.path.join(SKILLS, "breakdown-analyze-prd", "SKILL.md"),
                          encoding="utf-8").read())
    assert re.search(r"considerations> is not read", analyzer), (
        "analyze-prd is not told to leave <considerations> alone, so the catch-all becomes "
        "another thing to mine and the split stops being safe")
    assert re.search(r"When a feature declares one, copy it", analyzer), (
        "analyze-prd is not told to prefer a declared <data-model> over its own inference, "
        "which is the entire reason the element exists (P4)")
# --------------------------------------------- conventions, what-next, decision record (4/11/12/36)

def _mini_prd(root, definition, extra="", index_entry=True):
    """A one-feature PRD on disk. Synthetic rather than a fixture: `excluded` and `superseded`
    appear in neither fixture project, and adding them there would perturb every golden
    comparison to exercise two rules."""
    os.makedirs(os.path.join(root, "features"), exist_ok=True)
    entry = ('    <feature priority="must-have" file="features/one.md"><name>One</name></feature>\n'
             if index_entry else "")
    open(os.path.join(root, "index.md"), "w", encoding="utf-8", newline="\n").write(
        f"<prd>\n  <meta><slug>mini</slug><status>complete</status></meta>\n"
        f"  <features>\n{entry}  </features>\n</prd>\n")
    open(os.path.join(root, "features", "one.md"), "w", encoding="utf-8", newline="\n").write(
        f"<feature>\n  <meta>\n    <slug>one</slug>\n"
        f"    <definition>{definition}</definition>\n  </meta>\n"
        f"  <user-story>As a person, I want a thing, so that a reason.</user-story>\n"
        f"{extra}</feature>\n")
    return root


@check("a feature that will not be built says why, and leaves the index -- by running it",
       finding="P8")
def _():
    """Item 4. `excluded` and `superseded` were conventions an authoring corpus invented because
    the schema had nowhere to record "we decided not to build this". They are schema now, and
    each is paired with the element that says WHY -- which is what turns a convention into
    something a postcondition can hold.

    Run the migration rather than read it: the rules transform nothing, so their whole value is
    the exit code, and an exit code that has not been seen non-zero is a hypothesis.
    """
    import shutil
    import tempfile

    _path, reg = schema_registry()
    target = reg["current"]
    root = tempfile.mkdtemp(prefix="prd-conventions-")
    try:
        # R7: excluded with no rationale must refuse; with one, it passes.
        bad = _mini_prd(os.path.join(root, "a"), "excluded")
        p = _run_migrate(bad, "--to", target, "--quiet")
        assert p.returncode == 1 and "R7" in p.stderr, (
            f"an `excluded` feature with no <rationale> was accepted (exit {p.returncode}). A "
            f"feature nobody will build is a decision, and a decision nobody can reconstruct is "
            f"a gap in the record:\n{p.stdout}\n{p.stderr}")
        assert "NOT WRITTEN" in p.stderr, "the refusal does not say the file was left alone"

        # An EMPTY <rationale> is the case the first version of this check never built, so a
        # mutant that stopped calling .strip() survived. "The element is there" and "somebody
        # wrote something in it" are different claims.
        empty = _mini_prd(os.path.join(root, "a2"), "excluded", "  <rationale>   </rationale>\n")
        p = _run_migrate(empty, "--to", target, "--quiet")
        assert p.returncode == 1 and "R7" in p.stderr, (
            f"an empty <rationale> was accepted (exit {p.returncode}). An element with nothing "
            f"in it records that somebody knew a reason was wanted, and nothing else")

        good = _mini_prd(os.path.join(root, "b"), "excluded",
                         "  <rationale>The data it needed never arrived.</rationale>\n")
        p = _run_migrate(good, "--to", target, "--quiet")
        assert p.returncode == 0, f"an `excluded` feature WITH a rationale was refused: {p.stderr}"

        # R8: superseded needs a successor that EXISTS, and must leave the index. The two are
        # tested separately -- the first version left this one in the index as well, so the
        # index rule satisfied the assertion and a mutant that dropped the successor check
        # survived. One assertion, one rule.
        dangling = _mini_prd(os.path.join(root, "c"), "superseded",
                             '  <superseded-by slug="other"/>\n', index_entry=False)
        p = _run_migrate(dangling, "--to", target, "--quiet")
        assert p.returncode == 1 and "does not exist" in p.stderr, (
            f"a `superseded` feature naming a successor that does not exist was accepted "
            f"(exit {p.returncode}). Without a resolving pointer the feature is merely "
            f"missing, and nothing says what absorbed it:\n{p.stderr}")

        still_listed = _mini_prd(os.path.join(root, "d"), "superseded",
                                 '  <superseded-by slug="one"/>\n')
        p = _run_migrate(still_listed, "--to", target, "--quiet")
        assert p.returncode == 1 and "index.md still points at it" in p.stderr, (
            "a `superseded` feature still listed in index.md was accepted. The index is the "
            "planning view and a merged feature is no longer a unit of planning -- leaving the "
            "entry makes the feature count wrong")

        gone = _mini_prd(os.path.join(root, "e"), "superseded",
                         '  <superseded-by slug="one"/>\n', index_entry=False)
        p = _run_migrate(gone, "--to", target, "--quiet")
        assert p.returncode == 0, (
            f"a correctly superseded feature was refused: {p.stderr}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Scoped to the SENTENCE that binds reclassification to the rule. "ceiling" appears three
    # times in the guide, so searching the document let the binding sentence be deleted while
    # the explanation of what a ceiling is stayed behind, explaining nothing.
    guide = open(os.path.join(SCHEMA, "migration.md"), encoding="utf-8").read()
    binding = [ln for ln in guide.splitlines()
               if "Reclassif" in ln and re.search(r"ceiling", ln, re.I)]
    assert binding, (
        "the guide no longer says that RECLASSIFICATION derives a ceiling. A derivation that "
        "reports a value can contradict an author; one that reports a ceiling cannot, and item "
        "3 has to inherit that rather than invent it")


@check("what-next.md's gap list is derived, and staleness is an exit code -- by running it",
       finding="P12")
def _():
    """Item 11.

    A PRD with twenty-one unfinished features has twenty-one entries to keep in step with
    twenty-one files, and hand-maintenance of that has never once happened: the corpus this
    schema was measured against listed ZERO tbd items while carrying twenty-one. Generating it
    is the only version that stays true -- so the element ships WITH its producer rather than
    waiting for item 6, which is the mistake item 51 exists because of.

    Asserted by running the builder over the real fixture and mutating a feature underneath it.
    """
    import shutil
    import tempfile

    builder = os.path.join(SCHEMA, "scripts", "build-what-next.py")
    assert os.path.isfile(builder), "schema/scripts/build-what-next.py is missing"

    root = tempfile.mkdtemp(prefix="prd-whatnext-")
    try:
        work = os.path.join(root, "prd")
        shutil.copytree(current_fixture("link-shelf"), work)

        def run(*args):
            return subprocess.run([sys.executable, builder, work, *args],
                                  capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")

        p = run("--check")
        assert p.returncode == 0, (
            f"the fixture's <authoring-gaps> is already stale, so the rest of this check would "
            f"be measuring a broken baseline:\n{p.stdout}\n{p.stderr}")

        # Add a gap to a feature. The derived block must now disagree -- that is the whole
        # point of deriving it, and `--check` is what makes the disagreement actionable.
        feature = os.path.join(work, "features", "save-link.md")
        text = open(feature, encoding="utf-8").read()
        open(feature, "w", encoding="utf-8", newline="\n").write(text.replace(
            "</acceptance-criteria>",
            '</acceptance-criteria>\n\n  <gaps>\n    <gap id="9" kind="ownership" '
            'raised="2026-08-27">\n    Who owns the URL parser is unsettled.\n    </gap>\n'
            "  </gaps>", 1))

        p = run("--check")
        assert p.returncode == 1 and "STALE" in p.stderr, (
            "a feature grew a gap and the derived block did not go stale. A list that cannot "
            "notice is a list nobody can trust")

        p = run()
        assert p.returncode == 0, f"the rebuild failed: {p.stderr}"
        rebuilt = open(os.path.join(work, "what-next.md"), encoding="utf-8").read()
        assert 'slug="save-link" id="9" kind="ownership"' in rebuilt, (
            "the rebuilt block does not carry the new gap")
        assert "Who owns the URL parser" not in rebuilt, (
            "the derived block copied the gap's BODY. It aggregates pointers so that a gap is "
            "written in one place and corrected in one place; a copy is a second thing to keep "
            "in step")
        assert run("--check").returncode == 0, "the rebuild did not settle"

        # It must aggregate, never invent: a feature with no gaps and no shortfall adds nothing.
        counts = re.search(r"<summary ([^/]*)/>", rebuilt)
        assert counts, "the derived block carries no <summary>"
        assert 'defined="3"' in counts.group(1), (
            f"the summary miscounts the fixture's definitions: {counts.group(1)}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Scoped to the SECTION that argues it, not the document -- the phrase also appears in the
    # template's own XML comment, which satisfied the assertion on its own.
    fmt = open(os.path.join(SCHEMA, "prd-format.md"), encoding="utf-8").read()
    section = fmt.split("### `<authoring-gaps>` is derived", 1)
    assert len(section) == 2, "prd-format.md no longer argues why the block is derived"
    section = section[1].split("\n### ", 1)[0]
    assert re.search(r"Never hand-maintained", prose(section)), (
        "prd-format.md's <authoring-gaps> section does not say the block is never "
        "hand-maintained, so the next person to find it out of date will edit it")
    assert re.search(r"zero.*twenty-one|twenty-one.*zero", prose(section), re.I), (
        "the section no longer carries the measurement that makes the rule an argument rather "
        "than a preference: a corpus listing zero TBD items while carrying twenty-one")


@check("the resume marker is readable in both shapes -- by running the finder", finding="F3")
def _():
    """Item 12.

    `/prd`'s initialization reads `<status>` from what-next.md OR index.md, and item 11 moved it
    under `<meta>` in the new shape. The dual check has to keep working across a PARTLY migrated
    tree, because a PRD that cannot be found is a PRD that gets overwritten -- F3, which cost an
    interview before it was fixed.

    So both shapes are put in front of the real finder, in one directory, and both must be seen.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "list-prds.py")
    root = tempfile.mkdtemp(prefix="prd-dual-")
    try:
        for name, body in (
            ("migrated", "<what-next>\n  <meta>\n    <prd-slug>migrated</prd-slug>\n"
                         "    <status>in-progress</status>\n  </meta>\n</what-next>\n"),
            ("legacy", "<what-next>\n  <status>in-progress</status>\n</what-next>\n"),
        ):
            d = os.path.join(root, name)
            os.makedirs(os.path.join(d, "features"))
            open(os.path.join(d, "index.md"), "w", encoding="utf-8", newline="\n").write(
                f"<prd><meta><slug>{name}</slug><status>in-progress</status></meta></prd>\n")
            open(os.path.join(d, "what-next.md"), "w", encoding="utf-8", newline="\n").write(body)

        p = subprocess.run([sys.executable, script, root], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        out = p.stdout + p.stderr
        for name in ("migrated", "legacy"):
            assert name in out, f"{name} was not listed at all:\n{out}"
        assert "NO MARKER" not in out, (
            f"a PRD's resume marker was not found in one of the two shapes. Until every "
            f"artefact is migrated, both have to work:\n{out}")
        assert "DISAGREE" not in out, f"the two files were read as disagreeing:\n{out}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the decision record has a template, a test for when to write one, and a reader",
       finding="P24")
def _():
    """Item 36.

    Adopted from a project that already had nineteen and a settled house style, so the checks
    read a convention that exists rather than asking for a migration.

    The load-bearing part is not the section list -- it is the TEST. `**No rejected alternatives
    means it is not a decision record**` is what stops a principle being filed as a decision and
    read as though something was weighed.
    """
    path = os.path.join(SCHEMA, "decision-record.md")
    assert os.path.isfile(path), "schema/decision-record.md does not exist"
    text = open(path, encoding="utf-8").read()

    blocks = [b for b in re.findall(r"```markdown\n(.*?)```", text, re.S)]
    assert blocks, "decision-record.md carries no template"
    tpl = blocks[0]
    for field in ("**Status:**", "**Date:**", "**Drives:**"):
        assert field in tpl, f"the template carries no {field} field"
    for section in ("## Context", "## Options Considered", "## Decision", "## Rationale",
                    "## Consequences"):
        assert section in tpl, f"the template is missing {section}"
    assert "**Verdict:**" in tpl, (
        "an option carries no Verdict, so a rejected alternative is recorded without saying "
        "what it was rejected on")

    flat = prose(text)
    assert re.search(r"No rejected alternatives means it is not a decision record", flat), (
        "decision-record.md drops the test for whether you are writing one. Without it a "
        "principle gets filed as a decision and read as though something was weighed")
    assert re.search(r"Titles state a claim, not a topic", flat), (
        "the title convention is gone -- a record titled with a topic makes a reader open the "
        "file to find out what was decided")
    assert re.search(r'design-track enabled="false"', text), (
        "the design track is not declared off by default, so adopting the template turns on a "
        "gate nobody asked for")

    # A reader, or it is a template nobody validates. check-references.py already reads both
    # bolded fields -- assert the citation runs both ways.
    refs = open(os.path.join(SKILLS, "breakdown", "scripts", "check-references.py"),
                encoding="utf-8").read()
    assert "decision-record.md" in refs, (
        "check-references.py validates a record's fields without citing where they are defined")
    # A row naming a reader that EXISTS ON DISK, reached by a link that resolves.
    #
    # Two weaker versions of this were satisfied by something else in the file: "the script is
    # mentioned" matched the prose about `**Drives:**`, and "some row looks like a path" matched
    # the `/prd Phase 4` row. The table lists three readers and only one of them is a program
    # today -- so the claim is that at least one is, and the way to be sure is to resolve it.
    readers = text.split("## What reads this", 1)
    assert len(readers) == 2, "decision-record.md has no 'what reads this' section"
    rows = [ln.strip() for ln in readers[1].splitlines() if ln.strip().startswith("|")][2:]
    resolving = [t for r in rows for _l, t in md_links(r.split("|")[1])
                 if os.path.isfile(os.path.normpath(os.path.join(SCHEMA, t)))]
    assert resolving, (
        "decision-record.md's reader table names no reader that exists on disk. A template "
        "whose conventions nothing validates is a suggestion, and the two fields this one is "
        "built around already have a program that reads them")

# ------------------------------------------------- the CRD parity pass (46/47/48, schema-5)


def _crd(workflow="ready", requirements=None, meta_priority=None, gaps=""):
    """A CRD in whatever shape the caller needs, built rather than stored.

    Written as a helper because the three checks below each need a DIFFERENT shape -- one with
    requirements, one with a `wont-have` among them, one already migrated -- and a fixture per
    shape is four files to keep in step with a schema that is still moving.
    """
    reqs = ""
    if requirements:
        rows = "\n".join('    <requirement id="%d" priority="%s">Requirement %d.</requirement>'
                         % (i, p, i) for i, p in enumerate(requirements, start=1))
        reqs = "  <requirements>\n%s\n  </requirements>\n" % rows
    prio = "    <priority>%s</priority>\n" % meta_priority if meta_priority else ""
    return (
        "<crd>\n  <meta>\n    <name>Probe</name>\n    <slug>probe</slug>\n"
        "    <type>feature-modify</type>\n    <created>2026-08-27</created>\n"
        "    <workflow>%s</workflow>\n%s  </meta>\n"
        "%s"
        '  <acceptance-criteria>\n'
        '    <criterion id="1" pattern="ubiquitous" priority="P0">\n'
        "    The system shall do the thing it already did.\n"
        "    </criterion>\n"
        "  </acceptance-criteria>\n%s</crd>\n" % (workflow, prio, reqs, gaps))


@check("a CRD carries one list, not two -- and the migration moves it, by running it",
       finding="P31")
def _():
    """Item 46.

    An EARS criterion IS a requirement, so the CRD's second list had nothing of its own to
    carry -- it existed because Given/When/Then is a scenario format and a scenario cannot state
    an obligation. Item 33 removed the cause; this removes the effect.

    Asserted by RUNNING the migration rather than by reading the format document, because "the
    document says the element is retired" is a property the pre-item-46 document also had: it
    said so in a paragraph about a future item.
    """
    import shutil
    import tempfile

    # The document SHAPE, not a mention. crd-format.md necessarily still says the word
    # `<requirements>` -- the retirement note is where it explains itself -- so the claim worth
    # asserting is that the structure block no longer contains one.
    fmt = open(os.path.join(SKILLS, "crd", "references", "crd-format.md"),
               encoding="utf-8").read()
    blocks = re.findall(r"```xml\n(.*?)```", fmt, re.S)
    assert blocks, "crd-format.md carries no XML at all"
    structure = next((b for b in blocks if "<crd>" in b and "..." in b), None)
    assert structure, "crd-format.md has no document-structure block"
    assert "<requirements>" not in structure, (
        "crd-format.md's document structure still contains <requirements>. The element is "
        "retired; a structure block that lists it is the instruction people actually follow")
    assert "<gaps>" in structure, "the CRD structure gained no <gaps> (item 48)"

    full = next((b for b in blocks if "<crd>" in b and "<impact-analysis>" in b
                 and "..." not in b), None)
    assert full, "crd-format.md has no complete example"
    assert "<requirement " not in full and "<requirements>" not in full, (
        "crd-format.md's complete example still authors a <requirements> list")

    # And the interview no longer collects two lists.
    for path in (os.path.join(COMMANDS, "crd.md"), os.path.join(SKILLS, "crd", "SKILL.md")):
        text = prose(open(path, encoding="utf-8").read())
        assert re.search(r"[Oo]ne list, not two", text), (
            f"{os.path.basename(path)} does not say the interview captures one list. Asking for "
            f"requirements and then criteria for each gets the same content twice under two ids")

    # Now the mechanism: the migration MOVES the entries, renumbering them so that an id which
    # resolved before the step still resolves after it.
    _p, reg = schema_registry()
    current = reg["current"]
    root = tempfile.mkdtemp(prefix="crd-46-")
    try:
        path = os.path.join(root, "probe.md")
        open(path, "w", encoding="utf-8", newline="\n").write(
            _crd(requirements=["must-have", "should-have", "could-have"],
                 meta_priority="should-have"))
        p = _run_migrate(path, "--to", current, "--quiet")
        assert p.returncode == 0, (
            f"migrating a CRD to {current} exited {p.returncode}: {p.stderr}")

        out = open(path, encoding="utf-8").read()
        assert "<requirements>" not in out and "<requirement " not in out, (
            f"the migration left the retired list in place:\n{out}")
        ids = re.findall(r'<criterion\b[^>]*\bid="([^"]*)"', out)
        assert ids == ["1", "2", "3", "4"], (
            f"the merged id space is {ids}; the existing criterion must keep id 1 and the "
            f"migrated requirements must continue after it")
        assert 'derived-from="requirement-1"' in out, (
            "a migrated requirement carries no derived-from, so the citation it used to answer "
            "resolves to nothing")
        assert 'derived-from="1"' not in out.replace('derived-from="requirement-1"', ""), (
            "a migrated requirement carries a BARE derived-from. After the merge a bare id is "
            "ambiguous between the two former spaces, which is what the prefix exists to stop")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("requirement priority is P0|P1|P2 on both paths, and `wont-have` escalates -- by running it",
       finding="P31")
def _():
    """Item 47.

    The CRD had MoSCoW at the requirement level and P0|P1|P2 on criteria: two vocabularies for
    one concept, which is what made `--requirement-level` select nothing here. The vocabularies
    swap levels rather than one absorbing the other -- MoSCoW moves UP to the document.

    The interesting half is the fourth MoSCoW value. `P0|P1|P2` has no `not building this`
    level, deliberately, so `wont-have` has no honest target: P2 would make a declined
    requirement buildable by default and dropping it would delete a decision. That is an
    escalation, and it is asserted by running it -- a mapping table nobody executes is a
    paragraph.
    """
    import shutil
    import tempfile

    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()
    section = core.split("## 4. Priority", 1)[1].split("\n## ", 1)[0]
    assert "<meta><priority>" in section or "`<priority>` in `<meta>`" in section, (
        "core §4 never says where a CRD's MoSCoW lives, so the level it moved to is undocumented")

    # The map, as a shape: four MoSCoW values, and exactly one of them with no P-value.
    rows = [r for r in section.splitlines() if r.strip().startswith("|") and "-have" in r]
    mapped = {}
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        was = re.findall(r"`(\w+-have)`", cells[0])
        if len(was) == 1:
            mapped[was[0]] = set(re.findall(r"`(P[012])`", cells[1] if len(cells) > 1 else ""))
    assert set(mapped) == {"must-have", "should-have", "could-have", "wont-have"}, (
        f"core §4's MoSCoW map covers {sorted(mapped)}; all four values need an answer, "
        f"including the one whose answer is that there is none")
    assert not mapped["wont-have"], (
        "core §4 gives `wont-have` a P-level. P0|P1|P2 has no `not building this` value by "
        "design -- that judgement belongs to the whole item")
    assert all(len(v) == 1 for k, v in mapped.items() if k != "wont-have"), (
        "the MoSCoW map is not one to one; collapsing two tiers into one loses a distinction "
        "someone made")

    _p, reg = schema_registry()
    current = reg["current"]
    root = tempfile.mkdtemp(prefix="crd-47-")
    try:
        # Mapped one to one, and the values arrive on the criteria rather than being defaulted.
        ok = os.path.join(root, "ok.md")
        open(ok, "w", encoding="utf-8", newline="\n").write(
            _crd(requirements=["must-have", "should-have", "could-have"],
                 meta_priority="must-have"))
        p = _run_migrate(ok, "--to", current, "--quiet")
        assert p.returncode == 0, f"a mappable CRD exited {p.returncode}: {p.stderr}"
        out = open(ok, encoding="utf-8").read()
        got = dict(zip(re.findall(r'derived-from="requirement-(\d)"', out),
                       [m for m in re.findall(r'<criterion\b[^>]*derived-from="requirement-\d"',
                                              out)]))
        assert re.search(r'priority="P0"[^>]*derived-from="requirement-1"', out), (
            f"must-have did not become P0:\n{out}")
        assert re.search(r'priority="P1"[^>]*derived-from="requirement-2"', out), (
            f"should-have did not become P1:\n{out}")
        assert re.search(r'priority="P2"[^>]*derived-from="requirement-3"', out), (
            f"could-have did not become P2:\n{out}")

        # And the escalation: exit 2, the requirement named, and NOTHING written.
        bad = os.path.join(root, "bad.md")
        source = _crd(requirements=["must-have", "wont-have"], meta_priority="could-have")
        open(bad, "w", encoding="utf-8", newline="\n").write(source)
        p = _run_migrate(bad, "--to", current, "--quiet")
        assert p.returncode == 2, (
            f"a CRD holding a `wont-have` requirement exited {p.returncode}, not 2. Exit 2 is "
            f"the escalation path and it exists so that nothing is written for these files")
        assert "wont-have" in p.stderr and "requirement 2" in p.stderr, (
            f"the escalation does not name the requirement that caused it:\n{p.stderr}")
        assert open(bad, encoding="utf-8").read() == source, (
            "the escalated CRD was modified. Nothing is written for a file the migration "
            "cannot place -- that is the difference between exit 2 and exit 1")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("`/crd` cannot silently replace a CRD, and `ready` cannot outrank its gaps -- by running it",
       finding="P32")
def _():
    """Item 48.

    F3 cost an interview on the PRD path: `/prd` wrote over an existing PRD because the guard
    was a paragraph. `/crd` had the identical hole -- documented as stateless, writing
    docs/crd/{slug}.md with no check -- and had simply not been caught by it yet.

    The guard is the PRD one generalised to take a FILE rather than a second script, which is
    this repository's most repeated lesson: `keep_awake` was written inside one caller, item 60
    was a rule added without removing what it contradicted. A fix belongs at the level of the
    problem, and this problem was never PRD-specific.
    """
    import shutil
    import tempfile

    guard = os.path.join(SKILLS, "breakdown", "scripts", "check-writable.py")

    # The INVOCATION, with the path it guards -- not the substring `check-writable.py`.
    #
    # That weaker form survived a mutation round: /crd names the script twice, once plainly and
    # once with --resume, so replacing the first invocation with the `test -e` prose it was
    # written to retire left the substring assertion true and the suite green. Two sites
    # satisfying one check means no single edit can break it, which is the third time that shape
    # has cost this repository a hollow pass.
    for path in (os.path.join(COMMANDS, "crd.md"), os.path.join(SKILLS, "crd", "SKILL.md")):
        text = open(path, encoding="utf-8").read()
        name = os.path.basename(path)
        assert "check-writable.py {project_path}/docs/crd/{slug}.md" in text, (
            f"{name} never runs the overwrite guard on the file it is about to write, so a slug "
            f"collision destroys the earlier CRD in silence -- which is F3 exactly")
        assert "--resume" in text, f"{name} has no way past the guard"
        # And the prose guard must not come back beside it. A documented check and an executable
        # one both present is worse than either alone: the model may follow either.
        assert "test -e" not in text, (
            f"{name} carries a prose `test -e` guard beside the program. Five guards in this "
            f"repository became programs because the documented version was ignored")

    crd_md = open(os.path.join(COMMANDS, "crd.md"), encoding="utf-8").read()
    assert "check-writable.py {project_path}/docs/crd/{slug}.md --resume" in crd_md, (
        "/crd names no --resume form of the guard, so a caller who meant to resume has only "
        "the refusal and no stated way past it")

    root = tempfile.mkdtemp(prefix="crd-48-")
    try:
        live = os.path.join(root, "archive-links.md")
        open(live, "w", encoding="utf-8", newline="\n").write(_crd(meta_priority="should-have"))

        p = subprocess.run([sys.executable, guard, live], capture_output=True, text=True)
        assert p.returncode == 1, "the guard did not refuse an existing CRD file"
        assert "REFUSED" in p.stderr and "archive-links.md" in p.stderr, (
            f"the refusal does not name the document at risk:\n{p.stderr}")

        p = subprocess.run([sys.executable, guard, live, "--resume"],
                           capture_output=True, text=True)
        assert p.returncode == 0, "--resume did not permit writing a CRD back"

        p = subprocess.run([sys.executable, guard, os.path.join(root, "new.md")],
                           capture_output=True, text=True)
        assert p.returncode == 0, "the guard refused a slug nobody has used"
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # The other half of item 48: <gaps> reaches the CRD, and it gives <workflow> the mechanical
    # test it lacked. Asserted as the RULE rather than as a sentence, because the rule is what
    # a check can later become.
    fmt = prose(open(os.path.join(SKILLS, "crd", "references", "crd-format.md"),
                     encoding="utf-8").read())
    assert re.search(r'ready must not carry a <gap kind="specification">', fmt), (
        "crd-format.md never states the draft/ready test. Before item 48 the distinction rested "
        "entirely on the author's say-so, which is what <definition> had before item 29")
    core = prose(open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read())
    assert re.search(r"CRD marked ready must not carry a specification gap", core), (
        "core §6 states the rule for <definition> and not for <workflow>, so the two rows are "
        "checked by two rules that can drift")
    crd = prose(open(os.path.join(COMMANDS, "crd.md"), encoding="utf-8").read())
    assert "kind=\"specification\"" in crd or 'kind="specification"' in crd, (
        "/crd never tells the interview to record a deferral as a gap, so 'we'll define that "
        "later' still leaves nothing behind")


# ------------------------------------------- scope, confidence and parity (49/50, schema-5)


@check("the analysis predicts size and certainty, and something reads them -- by running it",
       finding="P19")
def _():
    """Item 49.

    `<scope>` and `<confidence>` were REQUIRED fields on the CRD path with no consumer anywhere
    in the toolchain -- which is why items 29 and 31 were each written as if from nothing. A
    required field nobody reads is worse than an absent one: it looks like a signal.

    The producer half is asserted on the analyser, and the reader half BY RUNNING IT, over three
    shapes -- a gross disagreement, an adjacent pair that must stay quiet, and a missing file.
    A cross-check that reports everything is one nobody reads, so the quiet case is as much the
    subject here as the loud one.
    """
    import json
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-scope.py")
    assert os.path.isfile(script), "check-scope.py does not exist, so item 49's fields have no reader"

    # The RUNNABLE invocation, not the string. /breakdown names check-scope.py three times --
    # once as a command and twice in prose about it -- so a bare substring is satisfied by the
    # prose alone and survives the command being deleted. That is the site-counting rule, and
    # it cost this suite a hollow check one commit ago and another one here.
    skill_raw = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    assert "scripts/check-scope.py {tasks_dir}" in skill_raw, (
        "/breakdown never RUNS the cross-check on the tasks directory. Naming the script in "
        "prose is what item 49 replaced, not what it asked for")

    # The producer: the FEATURE pass emits both, and the index pass is told not to. Asserted in
    # the OUTPUT BLOCK -- the analyser also discusses the key in prose, and prose is not a
    # schema the caller's merge can read.
    analyser = open(os.path.join(SKILLS, "breakdown-analyze-prd", "SKILL.md"),
                    encoding="utf-8").read()
    blocks = re.findall(r"```json\n(.*?)```", analyser, re.S)
    assert blocks, "breakdown-analyze-prd declares no output shape at all"
    assert any('"feature_signals"' in b for b in blocks), (
        "breakdown-analyze-prd's output shape carries no per-feature scope/confidence, so "
        "check-scope.py reads a key nothing writes -- which is the defect item 49 exists to "
        "remove, reintroduced from the other end")
    flat = prose(analyser)
    assert re.search(r"index pass emits neither", flat), (
        "the analyser does not say the index pass withholds these. index.md carries a summary "
        "line per feature, which is not evidence of size")

    root = tempfile.mkdtemp(prefix="scope-49-")
    try:
        builder = os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py")

        def run(analysis, count, slug=None):
            """Write real task files, BUILD the manifest, then compare.

            The manifest is produced by running build-manifest.py rather than hand-written.
            When this check shipped it seeded a `tasks` key that no manifest has ever had, and
            check-scope.py read the same invented key -- so the check validated the
            implementation against itself and attributed nothing on a real manifest. A fixture
            that agrees with the code it tests is the failure that reads exactly like a pass.
            """
            d = os.path.join(root, "t")
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(os.path.join(d, "1-foundation"))
            for i in range(count):
                trace = ""
                if slug:
                    trace = ("    <source-feature>%s</source-feature>\n"
                             "    <moscow>must-have</moscow>\n"
                             "    <satisfies-criteria>1</satisfies-criteria>\n"
                             "    <requirement-level>P0</requirement-level>\n" % slug)
                with open(os.path.join(d, "1-foundation", "L1-%03d-probe.xml" % (i + 1)),
                          "w", encoding="utf-8", newline="\n") as f:
                    f.write("<task>\n  <meta>\n    <id>L1-%03d</id>\n    <name>Probe %d</name>\n"
                            "    <layer>1-foundation</layer>\n    <priority>1</priority>\n"
                            "%s  </meta>\n</task>\n" % (i + 1, i + 1, trace))
            with open(os.path.join(d, "analysis.json"), "w", encoding="utf-8",
                      newline="\n") as f:
                json.dump(analysis, f)
            b = subprocess.run([sys.executable, builder, d], capture_output=True, text=True)
            assert b.returncode == 0, f"build-manifest.py failed: {b.stdout}\n{b.stderr}"
            return subprocess.run([sys.executable, script, d], capture_output=True, text=True)

        # Gross disagreement, on both paths at once.
        p = run({"scope": "small", "confidence": "medium",
                 "feature_signals": [{"feature": "save-link", "scope": "small",
                                      "confidence": "low"}]},
                11, "save-link")
        assert p.returncode == 0, (
            f"the cross-check exited {p.returncode}. A prediction losing an argument with an "
            f"observation is information, not a failure -- one that can block gets disabled")
        assert p.stdout.count("DISAGREES") == 2, (
            f"expected a disagreement at the document level AND the feature level:\n{p.stdout}")
        assert "save-link" in p.stdout and "11" in p.stdout, (
            f"the report does not name the feature or the count:\n{p.stdout}")
        assert "low" in p.stdout, (
            f"confidence is not reported. It grades the analysis and has nothing to be compared "
            f"against, which is exactly why it has to be SAID:\n{p.stdout}")

        # Adjacent bands stay quiet. Bands are files and the observation is tasks, so the units
        # do not line up -- a check that fires on that noise is one nobody reads.
        p = run({"scope": "small", "confidence": "high",
                 "feature_signals": [{"feature": "save-link", "scope": "small",
                                      "confidence": "high"}]},
                5, "save-link")
        assert p.returncode == 0 and "DISAGREES" not in p.stdout, (
            f"small against medium was reported as a disagreement:\n{p.stdout}")

        # Unattributed tasks are COUNTED, never passed over. Item 16 has not landed, so on the
        # PRD path this is the normal case -- and a cross-check that silently compares nothing
        # is indistinguishable from one that found nothing wrong.
        p = run({"feature_signals": [{"feature": "save-link", "scope": "small",
                                      "confidence": "high"}]}, 4)
        assert re.search(r"4 of 4 task\(s\) name no source feature", p.stdout), (
            f"tasks that could not be attributed were not counted:\n{p.stdout}")

        # Item 16's elements survive into the manifest, which is what every downstream reader
        # sizes the work from. Asserted on the file build-manifest.py wrote, not on the task.
        inv = json.load(open(os.path.join(root, "t", "manifest.json"),
                             encoding="utf-8")).get("task_inventory") or []
        assert inv and all("source_feature" not in e for e in inv), (
            "the last run had no traceability, so this assertion is checking the wrong tree")
        p = run({"feature_signals": [{"feature": "save-link", "scope": "large",
                                      "confidence": "high"}]}, 2, "save-link")
        inv = json.load(open(os.path.join(root, "t", "manifest.json"),
                             encoding="utf-8")).get("task_inventory") or []
        assert inv and all(e.get("source_feature") == "save-link" for e in inv), (
            f"build-manifest.py dropped <source-feature>; item 30 and item 49 both read it from "
            f"the manifest and would attribute nothing:\n{inv}")
        assert all(e.get("moscow") == "must-have" and e.get("requirement_level") == "P0"
                   and e.get("satisfies_criteria") == ["1"] for e in inv), (
            f"build-manifest.py dropped one of item 16's other three elements:\n{inv}")
        assert "DISAGREES" in p.stdout, (
            f"large against 2 tasks is non-adjacent and should have been reported:\n{p.stdout}")

        # A missing input is a failure, which is a different answer from a quiet comparison.
        p = subprocess.run([sys.executable, script, os.path.join(root, "absent")],
                           capture_output=True, text=True)
        assert p.returncode == 1, (
            f"a missing analysis.json exited {p.returncode}, not 1. 'Nothing to compare' and "
            f"'nothing disagreed' must not share an exit code")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("parity between the paths is a table with probes, and the probes resolve", finding="P30")
def _():
    """Item 50, and its fourth bullet is the point: the plan's `who is ahead where` ledger
    becomes a TEST rather than a paragraph that goes stale.

    Five of the asymmetries §5 J resolved existed because nobody had read the two paths side by
    side. A prose description of the difference is exactly as durable as the week it was written
    in -- so every claim in the table carries a `file :: string` probe, and every probe is run.

    `open` is a legitimate verdict. The rows nobody has decided about are LISTED, not refused:
    an unexamined asymmetry is a fact about this project, and the defect this file prevents is
    one nobody has written down.
    """
    path = os.path.join(SCHEMA, "parity.md")
    assert os.path.isfile(path), (
        "schema/parity.md does not exist. core.md records what the two paths share; without its "
        "counterpart the distance between them is measured by nobody")
    text = open(path, encoding="utf-8").read()

    section = text.split("## The table", 1)
    assert len(section) == 2, "parity.md has no table section"
    rows = [r.strip() for r in section[1].splitlines() if r.strip().startswith("|")]
    rows = [r for r in rows[2:] if r.strip("| ")]
    assert len(rows) >= 12, (
        f"parity.md lists {len(rows)} capabilities. §5 J compared twelve and the table should "
        f"not have shrunk below what has already been read")

    verdicts, opens, probes = set(), [], 0
    for row in rows:
        # Split on UNESCAPED pipes. A cell legitimately contains `P0\|P1\|P2` -- markdown's own
        # escape -- and splitting naively turned a six-cell row into eight.
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", row.strip("|"))]
        assert len(cells) == 6, f"malformed parity row ({len(cells)} cells): {row[:60]}"
        capability, prd, crd, verdict, settled, why = cells
        verdicts.add(verdict)
        assert verdict in ("both", "prd-only", "crd-only"), (
            f"{capability}: unknown verdict {verdict!r}")

        # A verdict and its evidence must agree. This is the half that cannot go stale: an `--`
        # whose counterpart quietly appeared, or a `both` whose evidence was deleted, fails.
        if verdict == "both":
            assert prd != "—" and crd != "—", f"{capability}: `both` with a missing side"
        else:
            missing, present = (crd, prd) if verdict == "prd-only" else (prd, crd)
            assert missing == "—", f"{capability}: {verdict} but both sides carry evidence"
            assert present != "—", f"{capability}: {verdict} and neither side has any"
            assert settled in ("yes", "**open**", "open"), (
                f"{capability}: an asymmetry must say whether it was decided or is open")
            assert len(why) > 20, (
                f"{capability}: an asymmetric row with no reason. A difference nobody wrote "
                f"down is the thing this file exists to prevent")
            if "open" in settled:
                opens.append(capability)

        for cell in (prd, crd):
            if cell == "—":
                continue
            assert "::" in cell, f"{capability}: evidence {cell!r} is not `file :: string`"
            rel, needle = [x.strip() for x in cell.split("::", 1)]
            rel = rel.strip("`")
            needle = needle.strip("`")
            full = os.path.join(REPO, rel.replace("/", os.sep))
            assert os.path.isfile(full), f"{capability}: parity.md cites a missing file {rel}"
            body = open(full, encoding="utf-8").read()
            assert needle in body, (
                f"{capability}: {rel} no longer contains {needle!r}. The capability moved and "
                f"the table did not -- which is the staleness the probes exist to catch")
            probes += 1

    assert probes >= 20, f"only {probes} probes resolve; the table is mostly assertion"
    assert {"both", "prd-only", "crd-only"} & verdicts == verdicts, "unknown verdict slipped in"
    assert "both" in verdicts, (
        "no row is `both`, so the table records only differences and cannot show a resolution")
    assert "crd-only" in verdicts and "prd-only" in verdicts, (
        "the table leans entirely one way. §5 J's finding was that the CRD path was AHEAD on "
        "five of six concerns, and a table that cannot express that is measuring the wrong thing")

    # The other three bullets of item 50 are already checks; assert they exist rather than
    # restating them here, so there is one statement of each rule and not two.
    suite = open(os.path.join(REPO, "tests", "test_toolchain.py"), encoding="utf-8").read()
    for name in ("the schema core is one definition that both paths cite",
                 "three status vocabularies, three distinct names"):
        assert name in suite, f"item 50 relies on `{name}`, which is not in the suite"

    if opens:
        print("    (%d open asymmetry/ies: %s)" % (len(opens), "; ".join(opens)))


# ------------------------------------------------ the three filters (13/14/15), finding P1


def _probe_prd(root, features):
    """A PRD with exactly the properties one rule needs, and no others.

    ONE RULE PER FEATURE, deliberately. The reference fixture's `quokka-telemetry` is `wont-have`
    AND carries a specification gap AND is `in-progress` -- three rules satisfied by one feature,
    so a check that watched it pass could not say which rule fired, and removing any two would
    still look green. That is the same site-counting defect this repository keeps meeting, in the
    fixture rather than in the assertion.

    `features` is a list of (slug, tier, definition, [gap kinds]).
    """
    os.makedirs(os.path.join(root, "features"), exist_ok=True)
    entries = "\n".join(
        '    <feature priority="%s" file="features/%s.md">\n'
        '      <name>%s</name><summary>Probe.</summary>\n'
        '    </feature>' % (tier, slug, slug) for slug, tier, _d, _g in features)
    with open(os.path.join(root, "index.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("<prd>\n  <meta><name>Probe</name><slug>probe</slug>"
                "<status>complete</status></meta>\n  <features>\n%s\n  </features>\n</prd>\n"
                % entries)
    for slug, _tier, definition, gaps in features:
        block = ""
        if gaps:
            rows = "\n".join('    <gap id="%d" kind="%s" raised="2026-08-27">Probe.</gap>'
                             % (i, k) for i, k in enumerate(gaps, start=1))
            block = "  <gaps>\n%s\n  </gaps>\n" % rows
        with open(os.path.join(root, "features", slug + ".md"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write("<feature>\n  <meta><name>%s</name><slug>%s</slug>"
                    "<definition>%s</definition></meta>\n%s</feature>\n"
                    % (slug, slug, definition, block))
    return root


@check("/breakdown declines work it was told not to do, and names what it declined -- by running it",
       finding="P1")
def _():
    """Items 13, 14 and 15 -- P1's whole first half.

    `/breakdown` filtered NOTHING. Every feature named in the index became tasks, so a
    `wont-have` feature, a `superseded` one and a `tbd` one all reached `/execute` as work.

    Three rules wearing one symptom, and they are NOT the same kind of rule, which is most of
    what is asserted here. Item 14 is a preference and has a flag. Item 13 is correctness and
    must have no way past it -- a `wont-have` feature is one somebody DECIDED against, and an
    override would make the decision advisory. Item 15 is a defect in the PRD and is therefore
    named rather than quietly dropped.
    """
    import json
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "select-features.py")
    assert os.path.isfile(script), "select-features.py does not exist, so /breakdown still builds everything"

    # The RUNNABLE invocation, not the filename. Twice now a bare substring has been satisfied by
    # prose ABOUT a script while the command that ran it was deleted.
    skill = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    assert "scripts/select-features.py {prd_dir}" in skill, (
        "/breakdown never RUNS the selector on the PRD directory")
    for flag in ("--priority", "--include-tbd"):
        assert flag in skill, f"/breakdown documents no {flag}"

    root = tempfile.mkdtemp(prefix="filters-13-")
    try:
        def run(features, *args):
            d = os.path.join(root, "p")
            shutil.rmtree(d, ignore_errors=True)
            _probe_prd(d, features)
            p = subprocess.run([sys.executable, script, d, "--json"] + list(args),
                               capture_output=True, text=True)
            return p, json.loads(p.stdout) if p.stdout.strip() else {}

        # ---- item 13: three values, none of them overridable. The flags are passed BECAUSE
        # the claim is that they make no difference here -- asserting the default alone would
        # leave "no override" untested, which is the half that is actually a promise.
        for slug, tier, definition in (("nope", "wont-have", "defined"),
                                       ("gone", "must-have", "excluded"),
                                       ("merged", "must-have", "superseded")):
            for extra in ([], ["--include-tbd"], ["--priority", "could-have", "--include-tbd"]):
                p, out = run([(slug, tier, definition, []), ("keep", "must-have", "defined", [])],
                             *extra)
                assert out["selected"] == ["keep"], (
                    f"{definition}/{tier} was selected with {extra or 'defaults'}. Item 13 is "
                    f"correctness, not a preference -- there is meant to be no way past it:\n"
                    f"{p.stdout}")
                assert any("item 13" in r for d in out["dropped"] if d["slug"] == slug
                           for r in d["reasons"]), (
                    f"{slug} was dropped without citing item 13, so the report cannot tell an "
                    f"operator which rule to argue with")

        # ---- item 14: the threshold, and its default. The default is the load-bearing part:
        # it preserves today's behaviour minus item 13, so the flag adds capability without
        # silently changing what an existing invocation builds.
        tiers = [("m", "must-have", "defined", []), ("s", "should-have", "defined", []),
                 ("c", "could-have", "defined", [])]
        _p, out = run(tiers)
        assert set(out["selected"]) == {"m", "s", "c"}, (
            f"the default threshold is not `could-have`; an existing invocation just changed "
            f"what it builds: {out['selected']}")
        assert out["threshold"] == "could-have"
        _p, out = run(tiers, "--priority", "must-have")
        assert out["selected"] == ["m"], f"--priority must-have selected {out['selected']}"
        _p, out = run(tiers, "--priority", "should-have")
        assert set(out["selected"]) == {"m", "s"}, (
            f"--priority should-have must be must+should, not {out['selected']}")

        # ---- item 15: the gap block beats the status, and only ONE kind refuses.
        p, out = run([("sketch", "must-have", "tbd", []),
                      ("holed", "must-have", "defined", ["specification"]),
                      ("waiting", "must-have", "defined", ["dependency"]),
                      ("undecided", "must-have", "defined", ["decision"]),
                      ("unsure", "must-have", "defined", ["evidence"]),
                      ("whose", "must-have", "defined", ["ownership"])])
        assert set(out["selected"]) == {"waiting", "undecided", "unsure", "whose"}, (
            f"the four non-specification gap kinds must WARN, not refuse -- they say the feature "
            f"is specified but not yet buildable, which is a scheduling fact:\n{p.stdout}")
        assert set(out["warnings"]) >= {"waiting", "undecided", "unsure", "whose"}, (
            "a feature carrying an open gap was built with no warning at all")

        # --include-tbd reaches the STATUS and must never reach the gap. A status is a summary;
        # the gap is the author saying the specification is incomplete.
        p, out = run([("sketch", "must-have", "tbd", []),
                      ("holed", "must-have", "defined", ["specification"])], "--include-tbd")
        assert out["selected"] == ["sketch"], (
            f"--include-tbd must reach `tbd` and NOT a specification gap:\n{p.stdout}")

        # A `defined` feature carrying a specification gap is still refused. That is the whole
        # point of "the gap block beats the status" -- asserting it only on a `tbd` feature would
        # pass on a script that never read the gaps at all.
        assert any("item 15" in r for d in out["dropped"] if d["slug"] == "holed"
                   for r in d["reasons"]), "a `defined` feature with a specification gap was not refused by item 15"

        # ---- every reason, not the first that matched. Fixing one of two must visibly change
        # something, or the report teaches an operator that the fix did nothing.
        p, out = run([("both", "wont-have", "defined", ["specification"]),
                      ("keep", "must-have", "defined", [])])
        reasons = [d["reasons"] for d in out["dropped"] if d["slug"] == "both"][0]
        assert len(reasons) >= 2 and any("item 13" in r for r in reasons) \
            and any("item 15" in r for r in reasons), (
            f"a feature excluded by two rules reported {len(reasons)}:\n{reasons}")

        # ---- the sentence item 15 exists to make sayable, on stderr so it cannot become line
        # eleven of twenty.
        p, out = run([("holed", "must-have", "defined", ["specification"]),
                      ("keep", "must-have", "defined", [])])
        assert out["undefined_must_haves"] == ["holed"]
        assert "must-have" in p.stderr and "not defined enough" in p.stderr, (
            f"an undefined must-have was not called out on stderr:\n{p.stderr}")

        # ---- nothing selectable is an exit code, not an empty success.
        p, out = run([("nope", "wont-have", "defined", [])])
        assert p.returncode == 1, (
            f"a PRD with nothing buildable exited {p.returncode}. 'Built everything asked for' "
            f"and 'there was nothing to build' must not share an exit code")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # ---- and the CRD path, where item 47 is what gave --priority anything to read.
    _p, reg = schema_registry()
    crd = os.path.join(REPO, "tests", "fixture", "prd", reg["current"], "link-shelf", "crd",
                       "archive-links.md")
    if os.path.isfile(crd):
        p = subprocess.run([sys.executable, script, crd, "--json", "--priority", "must-have"],
                           capture_output=True, text=True)
        out = json.loads(p.stdout)
        assert out["selected"] == [] and p.returncode == 1, (
            f"a should-have change request was not declined by --priority must-have. Before "
            f"item 47 this flag had no field to read on the CRD path:\n{p.stdout}")


# ------------------------------------- the carry across the boundary (16/17/30/19/20), P20


def _task_xml(tid, slug=None, crits="1", moscow="must-have", level="P0"):
    trace = ""
    if slug:
        trace = ("    <source-feature>%s</source-feature>\n    <moscow>%s</moscow>\n"
                 "    <satisfies-criteria>%s</satisfies-criteria>\n"
                 "    <requirement-level>%s</requirement-level>\n" % (slug, moscow, crits, level))
    return ("<task>\n  <meta>\n    <id>%s</id>\n    <name>Probe %s</name>\n"
            "    <layer>1-foundation</layer>\n    <priority>1</priority>\n%s  </meta>\n"
            "</task>\n" % (tid, tid, trace))


def _task_tree(root, tasks):
    """A tasks directory with real files and a manifest BUILT by build-manifest.py."""
    layer = os.path.join(root, "1-foundation")
    os.makedirs(layer, exist_ok=True)
    for i, kwargs in enumerate(tasks, start=1):
        tid = "L1-%03d" % i
        with open(os.path.join(layer, "%s-probe.xml" % tid), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write(_task_xml(tid, **kwargs))
    builder = os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py")
    p = subprocess.run([sys.executable, builder, root], capture_output=True, text=True)
    assert p.returncode == 0, f"build-manifest.py failed: {p.stdout}\n{p.stderr}"
    return root


@check("a task names the feature and criteria it came from, and `<priority>` is left alone",
       finding="P15")
def _():
    """Items 16 and 17.

    Before these a task named its source feature NOWHERE. Attribution downstream was a string
    match on `<name>`, which is why item 21's tier probe had to invent slugs that could not occur
    by coincidence, and why check-scope.py could attribute nothing.

    The `<priority>` half is the part worth guarding. It is an integer meaning merge order within
    the layer and has meant that since the beginning (P3); overloading it with MoSCoW would leave
    every reader ambiguous about which of two unrelated orderings it was reading. So the assertion
    is not only that the tier arrives, but that it arrives UNDER A DIFFERENT NAME.
    """
    spec = open(os.path.join(SKILLS, "breakdown", "references", "task-format-spec.md"),
                encoding="utf-8").read()
    blocks = re.findall(r"```xml\n(.*?)```", spec, re.S)
    meta = next((b for b in blocks if "<meta>" in b and "<id>" in b), None)
    assert meta, "task-format-spec.md has no <meta> example"
    # Item 65 moved these onto the element as attributes, one `<source-feature>` per feature the
    # task descends from. The four names still have to be there, and this reads them off the
    # example rather than looking for four opening tags that no longer exist.
    edge = re.search(r"<source-feature\b([^>]*)/>", meta)
    assert edge, "the task <meta> example carries no <source-feature .../>"
    for attr in ("slug", "moscow", "satisfies-criteria", "requirement-level"):
        assert re.search(r'\b%s="[^"]+"' % attr, edge.group(1)), (
            f"the task <meta> example's <source-feature> carries no `{attr}`: {edge.group(0)}")

    # P3: <priority> keeps its meaning. A MoSCoW value inside it is the overload item 16 avoided.
    prio = re.search(r"<priority>([^<]*)</priority>", meta)
    assert prio and prio.group(1).strip().isdigit(), (
        f"<priority> in the task example is {prio.group(1) if prio else 'absent'!r}. It is an "
        f"integer meaning merge order (P3); the feature's tier belongs in <moscow>")

    flat = prose(spec)
    assert re.search(r"Layer 0 is exempt", flat), (
        "the spec does not exempt Layer 0. Its tasks descend from the tech stack rather than "
        "from a feature, and inventing a <source-feature> for them puts a false attribution "
        "into item 30's coverage check")
    assert re.search(r"highest", flat), (
        "the spec does not say <requirement-level> is the HIGHEST of the criteria named; a task "
        "is built or not built as a unit")

    # Item 17: the criteria are carried structurally, verbatim, and the tests cite them.
    ctx = next((b for b in blocks if "<acceptance-criteria>" in b and "<tech-stack>" in b), None)
    assert ctx, "task <context> does not carry <acceptance-criteria> structurally (item 17)"
    assert "<data-model>" in ctx, "task <context> does not carry the feature's <data-model>"
    assert re.search(r"Verbatim means verbatim", flat), (
        "the spec does not require the criteria verbatim. A reworded criterion is one no "
        "reviewer can match back to the PRD, which is what core §1's ids are for")
    assert re.search(r'<test id="2" covers="7">', spec), (
        "no test in the spec cites the criterion it covers, so item 30 has nothing to check "
        "within a single file")

    # And the generator is told to produce them -- the runnable half is item 30's check below.
    gen = prose(open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
                     encoding="utf-8").read())
    assert re.search(r"Copy each <criterion> element whole", gen), (
        "breakdown-generate-tasks is not told to copy the criterion element whole")
    assert re.search(r"data model is copied, never inferred", gen), (
        "the generator may still infer a data model beside the author's, which is the half-read "
        "half-invented case item 17 exists to stop")


@check("the task set is checked against the document it came from -- by running it",
       finding="P20")
def _():
    """Item 30, and it is only answerable because item 16 landed.

    Four assertions here; the fifth in the plan -- significance against a decision record's
    **Drives:** -- lives in check-references.py and is NOT restated, because a rule stated in two
    programs is one that gets changed in one of them.

    THE SHORTFALL IS ASSERTED BY NAME. "1 feature has no task" passes a test that a check naming
    the WRONG feature would also pass, and item 59's third assertion exists for the same reason.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-coverage.py")
    assert os.path.isfile(script), "check-coverage.py does not exist"
    skill = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    assert "scripts/check-coverage.py {prd_dir} {tasks_dir}" in skill, (
        "/breakdown never RUNS the coverage check on the PRD and the tasks directory")

    # The fifth assertion is somewhere else, and this is the statement that it is.
    refs = open(os.path.join(SKILLS, "breakdown", "scripts", "check-references.py"),
                encoding="utf-8").read()
    assert "**Drives:**" in refs, (
        "check-references.py no longer checks significance against a decision record, so item "
        "30's fifth assertion is now stated nowhere")
    doc = open(script, encoding="utf-8").read()
    assert "check-references.py" in doc, (
        "check-coverage.py does not name where the fifth assertion lives, so a reader will "
        "conclude it was dropped")

    _p, reg = schema_registry()
    prd = os.path.join(REPO, "tests", "fixture", "prd", reg["current"], "link-shelf")
    root = tempfile.mkdtemp(prefix="cov-30-")
    try:
        def run(tasks, *args):
            d = os.path.join(root, "t")
            shutil.rmtree(d, ignore_errors=True)
            _task_tree(d, tasks)
            p = subprocess.run([sys.executable, script, prd, d, "--json"] + list(args),
                               capture_output=True, text=True)
            return p, json.loads(p.stdout)

        # DERIVED from the fixture, not listed here. The ids were hardcoded until schema-6 gave
        # list-links the unwanted-behaviour criterion the bar had been asking for, and a check
        # that has to be edited whenever the corpus gains a criterion is a check that will one
        # day be edited to agree with a defect.
        index = open(os.path.join(prd, "index.md"), encoding="utf-8").read()
        full = []
        for tier, rel in re.findall(r'<feature\s+priority="([^"]+)"\s+file="([^"]+)"', index):
            slug = os.path.splitext(os.path.basename(rel))[0]
            text = open(os.path.join(prd, rel.replace("/", os.sep)), encoding="utf-8").read()
            ids = re.findall(r'<criterion\b[^>]*\bid="([^"]+)"', text)
            full.append(dict(slug=slug, crits=",".join(ids), moscow=tier))
        assert len(full) >= 3 and all(f["crits"] for f in full), (
            f"the fixture PRD no longer yields a coverable task set: {full}")

        # Complete coverage is exit 0 -- and asserting this is what stops a check that reports
        # a shortfall unconditionally from passing everything below.
        p, out = run(full)
        assert p.returncode == 0, f"complete coverage was reported as a shortfall:\n{p.stderr}"
        assert not out["uncovered_features"] and not out["uncovered_criteria"]

        # 1. A feature with no task at all, BY NAME.
        p, out = run(full[:2])
        assert p.returncode == 1
        assert [f["slug"] for f in out["uncovered_features"]] == ["tag-links"], (
            f"the shortfall does not name the feature. A check that counts correctly and "
            f"attributes wrongly passes any test that only counts:\n{out}")
        assert "tag-links" in p.stderr, "the operator-facing report does not name it either"

        # 3. Criteria, both directions.
        p, out = run([dict(slug="save-link", crits="1,2")] + full[1:])
        assert {(c["feature"], c["id"]) for c in out["uncovered_criteria"]} == {
            ("save-link", "3"), ("save-link", "4")}, (
            f"an uncovered criterion was not named: {out['uncovered_criteria']}")
        p, out = run([dict(slug="save-link", crits="1,2,3,4,99")] + full[1:])
        assert [c["id"] for c in out["unknown_criteria"]] == ["99"], (
            f"a task citing a criterion that does not exist was not reported: {out}")

        # 2. A <source-feature> naming nothing in the document.
        p, out = run(full + [dict(slug="ghost-feature")])
        assert [f["slug"] for f in out["unresolved_source_features"]] == ["ghost-feature"]

        # 5. Item 13's runtime backstop, on the fixture that actually has a wont-have feature.
        staff = os.path.join(REPO, "tests", "fixture", "prd", reg["current"], "staff-service")
        d = os.path.join(root, "s")
        _task_tree(d, [dict(slug="zebra-signin", crits="1,2,3,4"),
                       dict(slug="quokka-telemetry", crits="1")])
        p = subprocess.run([sys.executable, script, staff, d, "--json",
                            "--priority", "must-have"], capture_output=True, text=True)
        out = json.loads(p.stdout)
        assert [f["slug"] for f in out["forbidden_source_features"]] == ["quokka-telemetry"], (
            f"a task descending from a wont-have feature was not refused. That is item 13's "
            f"runtime backstop, and it fires when the selection gate did not run:\n{out}")
        assert p.returncode == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("/execute reports the tier it built and refuses won't-have work -- by running both",
       finding="P1")
def _():
    """Items 19 and 20, which are why they were moved out of group 5c: both read `<moscow>` on a
    TASK, and nothing put it there until item 16.

    `<requirement-level>` would otherwise have no reader at all -- item 16 writes it, item 30
    checks criteria against the threshold rather than against the element, and nothing else looks
    at it. The report is both the cheapest reader and the useful one.
    """
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="exec-19-")
    try:
        project = os.path.join(root, "proj")
        os.makedirs(project)
        for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(["git"] + args, cwd=project, capture_output=True, text=True)

        tasks = os.path.join(root, "tasks")
        _task_tree(tasks, [dict(slug="save-link", moscow="must-have", level="P0"),
                           dict(slug="tag-links", moscow="should-have", level="P1"),
                           dict(slug=None)])  # Layer 0 shape: no tier at all
        with open(os.path.join(tasks, "layer_plan.json"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write('{"layers": []}\n')

        # ---- item 19: the tiers are DERIVED into the state file, not counted by a reporter.
        writer = os.path.join(SKILLS, "execute", "scripts", "write-state.py")
        p = subprocess.run([sys.executable, writer, tasks, project, "probe"],
                           capture_output=True, text=True)
        assert p.returncode == 0, f"write-state.py failed: {p.stdout}\n{p.stderr}"
        state = json.load(open(os.path.join(tasks, "execute-state.json"), encoding="utf-8"))

        assert state.get("tiers", {}).get("by_tier") == {"must-have/P0": 1,
                                                         "should-have/P1": 1}, (
            f"execute-state.json does not group by BOTH tiers. The two-level filter is "
            f"invisible in the output otherwise:\n{state.get('tiers')}")
        assert state["tiers"].get("unattributed") == 1, (
            "a task with no tier was not counted as unattributed. Layer 0 legitimately has "
            "none, and silently dropping it makes a partial report look complete")
        rec = state["tasks"]["L1-001"]
        assert rec.get("moscow") == "must-have" and rec.get("requirement_level") == "P0"
        assert "moscow" not in state["tasks"]["L1-003"], (
            "a task with no tier was given a null one; `has no tier` and `tier not recorded` "
            "must stay distinguishable")

        schema = open(os.path.join(SKILLS, "execute", "references", "state-schema.md"),
                      encoding="utf-8").read()
        for field in ('"tiers"', '"moscow"', '"requirement_level"'):
            assert field in schema, (
                f"state-schema.md does not document {field}. A live producer/spec mismatch in "
                f"this exact file is what item 23a was")

        # ---- item 20: preflight refuses, names the file, and still works when it should.
        flight = os.path.join(SKILLS, "execute", "scripts", "preflight.sh")
        p = subprocess.run(["sh", flight, tasks, project], capture_output=True, text=True)
        assert p.returncode == 0, f"preflight refused a clean tree: {p.stderr}"
        assert p.stdout.strip(), "preflight stopped printing the resolved base branch"

        bad = os.path.join(tasks, "1-foundation", "L1-004-wont.xml")
        with open(bad, "w", encoding="utf-8", newline="\n") as f:
            f.write(_task_xml("L1-004", slug="quokka-telemetry", moscow="wont-have"))
        p = subprocess.run(["sh", flight, tasks, project], capture_output=True, text=True)
        assert p.returncode == 1, (
            "a task carrying <moscow>wont-have</moscow> reached /execute and was not refused. "
            "That means item 13's gate did not run, and item 20 is the exit code that says so")
        assert "REFUSED" in p.stderr and "L1-004" in p.stderr, (
            f"the refusal does not name the offending task file:\n{p.stderr}")

        skill = prose(open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read())
        assert re.search(r"wont-have", skill), "/execute does not document the item 20 refusal"
        assert re.search(r"tiers block", skill), (
            "/execute is not told to report the tier from the state file's derived block, so it "
            "will count its own and disagree with the tasks it counted")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ------------------------------------- the boundary test's grader (item 59), finding A8/R13


@check("the boundary grader detects each of its five failures -- by breaking them", finding="A8")
def _():
    """Item 59's grader, exercised without spending a live run.

    `boundary-test.py` splits `--grade` from `--run` for the reason probe-p1.py did: **a grader
    that has only ever run behind the expensive path is a grader nobody has checked.** So this
    drives the grader over a task set the check builds itself, then BREAKS each assertion in turn
    and asserts the grader notices.

    Passing on a compliant task set is the weakest half of this. A grader that returned 0
    unconditionally would pass that and nothing else here.

    Assertion 3 is the one worth insisting on and it is why the grader exists at all: a coverage
    check reporting "1 feature has no task" passes any test that a check naming the WRONG feature
    would also pass. The mutation below keeps the COUNT correct and changes only the name.
    """
    import shutil
    import tempfile

    grader = os.path.join(REPO, "tests", "boundary-test.py")
    assert os.path.isfile(grader), "tests/boundary-test.py does not exist"

    _p, reg = schema_registry()
    prd = os.path.join(REPO, "tests", "fixture", "prd", reg["current"], "link-shelf")
    crit = re.compile(r"<criterion\b([^>]*)>(.*?)</criterion>", re.S)

    root = tempfile.mkdtemp(prefix="boundary-59-")
    try:
        project = os.path.join(root, "app")
        os.makedirs(project)
        for a in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(["git"] + a, cwd=project, capture_output=True, text=True)

        def seed():
            """A task set that satisfies all five assertions, built from the fixture PRD."""
            tasks = os.path.join(root, "tasks")
            shutil.rmtree(tasks, ignore_errors=True)
            os.makedirs(os.path.join(tasks, "1-foundation"))
            index = open(os.path.join(prd, "index.md"), encoding="utf-8").read()
            n = 0
            per_feature = []
            for tier, rel in re.findall(r'<feature\s+priority="([^"]+)" file="([^"]+)"', index):
                slug = os.path.splitext(os.path.basename(rel))[0]
                text = open(os.path.join(prd, rel), encoding="utf-8").read()
                found = crit.findall(text)
                n += 1
                body = "\n".join("    <criterion%s>%s</criterion>" % (a, b) for a, b in found)
                ids = ",".join(re.search(r'id="([^"]*)"', a).group(1) for a, _ in found)
                with open(os.path.join(tasks, "1-foundation", "L1-%03d-%s.xml" % (n, slug)),
                          "w", encoding="utf-8", newline="\n") as f:
                    f.write("<task>\n  <meta>\n    <id>L1-%03d</id>\n    <name>Build %s</name>\n"
                            "    <layer>1-foundation</layer>\n    <priority>%d</priority>\n"
                            '    <source-feature slug="%s" moscow="%s" '
                            'satisfies-criteria="%s" requirement-level="P0"/>\n  </meta>\n'
                            "  <context>\n    <acceptance-criteria>\n%s\n"
                            "    </acceptance-criteria>\n  </context>\n</task>\n"
                            % (n, slug, n, slug, tier, ids, body))
                per_feature.append((slug, tier, ids, body))

            # One task descending from TWO features, which is what item 65 exists for and what
            # three live runs each worked around differently (P43). The criteria are grouped by
            # feature because ids repeat across them: `1` names a different requirement in each.
            if len(per_feature) >= 2:
                (s1, t1, i1, b1), (s2, t2, i2, b2) = per_feature[0], per_feature[1]
                n += 1
                with open(os.path.join(tasks, "1-foundation", "L1-%03d-integration.xml" % n),
                          "w", encoding="utf-8", newline="\n") as f:
                    f.write("<task>\n  <meta>\n    <id>L1-%03d</id>\n"
                            "    <name>Wire %s and %s together</name>\n"
                            "    <layer>1-foundation</layer>\n    <priority>%d</priority>\n"
                            '    <source-feature slug="%s" moscow="%s" '
                            'satisfies-criteria="%s" requirement-level="P0"/>\n'
                            '    <source-feature slug="%s" moscow="%s" '
                            'satisfies-criteria="%s" requirement-level="P0"/>\n  </meta>\n'
                            "  <context>\n    <acceptance-criteria>\n"
                            '    <from-feature slug="%s">\n%s\n    </from-feature>\n'
                            '    <from-feature slug="%s">\n%s\n    </from-feature>\n'
                            "    </acceptance-criteria>\n  </context>\n</task>\n"
                            % (n, s1, s2, n, s1, t1, i1, s2, t2, i2, s1, b1, s2, b2))
            b = subprocess.run([sys.executable, os.path.join(SKILLS, "breakdown", "scripts",
                                                             "build-manifest.py"), tasks],
                               capture_output=True, text=True)
            assert b.returncode == 0, f"build-manifest.py failed: {b.stdout}\n{b.stderr}"
            return tasks

        def grade(tasks):
            return subprocess.run([sys.executable, grader, "--grade", prd, tasks,
                                   "--project", project], capture_output=True, text=True)

        def a_task(tasks, needle):
            for dp, _dn, fn in os.walk(tasks):
                for n in fn:
                    if needle in n:
                        return os.path.join(dp, n)
            raise AssertionError(f"no task file matching {needle}")

        # A compliant set passes -- the baseline without which every failure below is hollow.
        tasks = seed()
        p = grade(tasks)
        assert p.returncode == 0, f"a compliant task set was graded as failing:\n{p.stdout}\n{p.stderr}"
        for n in ("1:", "2:", "3:", "4:", "5:"):
            assert n in p.stdout, f"assertion group {n} did not run at all:\n{p.stdout}"

        # 1. A REWORDED criterion. This is the assertion that would have failed for the whole
        #    life of the toolchain, and the reason item 17 carries the element rather than prose.
        tasks = seed()
        path = a_task(tasks, "save-link")
        text = open(path, encoding="utf-8").read()
        i, j = text.index("<criterion"), text.index("</criterion>")
        open(path, "w", encoding="utf-8", newline="\n").write(
            text[:i] + text[i:j].replace("shall", "should", 1) + text[j:])
        p = grade(tasks)
        assert p.returncode == 1 and "REWORDED" in p.stderr, (
            f"a criterion arriving reworded was not detected:\n{p.stdout}\n{p.stderr}")

        # 2. Both directions: a name that resolves to nothing, and a feature nothing names.
        tasks = seed()
        path = a_task(tasks, "tag-links")
        # Read BEFORE opening for write. `open(path, "w")` truncates, and an inner read
        # evaluated as the write's argument then returns "" -- which is how this check first
        # reported a missing failure that the grader had in fact produced.
        text = open(path, encoding="utf-8").read()
        # The slug, wherever the schema keeps it. Item 65 moved it from the element's text into a
        # `slug` attribute and the literal that used to be here silently stopped matching -- so
        # the mutation mutated nothing and the assertion below failed for the one reason that
        # says nothing about the grader. The substitution count is asserted for exactly that.
        mutated, subs = re.subn(r'(?<=slug=")tag-links(?=")'
                                r'|(?<=<source-feature>)tag-links(?=</source-feature>)',
                                "ghost", text)
        assert subs == 1, (
            f"the ghost-slug mutation matched {subs} sites, not 1. It no longer breaks the "
            f"attribution it exists to break")
        open(path, "w", encoding="utf-8", newline="\n").write(mutated)
        p = grade(tasks)
        assert p.returncode == 1 and "ghost" in p.stderr and "tag-links is in scope" in p.stderr, (
            f"<source-feature> was not resolved in both directions:\n{p.stderr}")

        # 4. A task with no tier. Item 19's element has no other reader.
        tasks = seed()
        path = a_task(tasks, "save-link")
        text = open(path, encoding="utf-8").read()
        # Attribute or element, whichever this schema version keeps the level in.
        mutated, subs = re.subn(r'\s*requirement-level="P0"'
                                r'|[ \t]*<requirement-level>P0</requirement-level>\n', "", text)
        assert subs >= 1, "the requirement-level mutation matched nothing to remove"
        open(path, "w", encoding="utf-8", newline="\n").write(mutated)
        p = grade(tasks)
        assert p.returncode == 1 and "FAIL 4:" in p.stderr, (
            f"a task carrying no requirement-level was not detected:\n{p.stderr}")

        # 3. THE ONE. Break the coverage check so it names the wrong feature while keeping the
        #    count right, and assert the grader is not fooled. A test that does not force this
        #    cannot detect a check that counts correctly and attributes wrongly.
        cov = os.path.join(SKILLS, "breakdown", "scripts", "check-coverage.py")
        original = open(cov, encoding="utf-8").read()
        try:
            open(cov, "w", encoding="utf-8", newline="\n").write(original.replace(
                '"uncovered_features": [{"slug": r["slug"], "tier": r["tier"]} for r in uncovered],',
                '"uncovered_features": [{"slug": "save-link", "tier": r["tier"]} for r in uncovered],'))
            p = grade(seed())
            assert p.returncode == 1 and "attributes wrongly" in p.stderr, (
                f"the grader accepted a coverage report that named the WRONG feature. That is "
                f"the failure item 59's third assertion exists to catch:\n{p.stderr}")
        finally:
            open(cov, "w", encoding="utf-8", newline="\n").write(original)

        # 5. Preflight stops refusing. Absence is not refusal, which is item 20's whole point.
        flight = os.path.join(SKILLS, "execute", "scripts", "preflight.sh")
        original = open(flight, encoding="utf-8").read()
        try:
            # Match the assignment, not the exact grep. Item 65 rewrote this line to accept the
            # per-edge `moscow="wont-have"` attribute, and the literal below silently stopped
            # applying -- so the mutation mutated nothing and this assertion failed for the one
            # reason that says nothing about the grader. The substitution count is asserted for
            # exactly that: a mutation that does not apply must fail loudly, not quietly pass.
            mutated, n = re.subn(r"(?m)^wont=\$\(.*\)$", 'wont=""', original)
            assert n == 1, (
                f"the preflight mutation matched {n} sites, not 1. It no longer breaks the "
                f"refusal it is meant to break, and the assertion below would be measuring "
                f"nothing")
            open(flight, "w", encoding="utf-8", newline="\n").write(mutated)
            p = grade(seed())
            assert p.returncode == 1 and "FAIL 5:" in p.stderr, (
                f"the grader did not notice preflight had stopped refusing:\n{p.stderr}")
        finally:
            open(flight, "w", encoding="utf-8", newline="\n").write(original)

        # And the live mode exists, is documented, and is not what runs here.
        doc = open(grader, encoding="utf-8").read()
        assert "--run" in doc and "claude" in doc, (
            "boundary-test.py has no live mode, so item 59 is a grader with nothing to grade")
        assert 'reg["current"]' in doc, (
            "the live mode names a schema version instead of reading SCHEMAS.json; a runtime "
            "test pinned to an old fixture tests a corpus three migrations out of date")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ------------------------------------------ the definition bar (58/3/6/7/40/8, group 5d)


def _checks_table():
    """schema/checks.md's table, as (assertion, owner, callers, item) tuples."""
    path = os.path.join(SCHEMA, "checks.md")
    assert os.path.isfile(path), (
        "schema/checks.md does not exist. Item 6 had accumulated eleven assertions and four "
        "other items claimed the same ground; the table is what gives each one an owner")
    text = open(path, encoding="utf-8").read()
    section = text.split("## The table", 1)
    assert len(section) == 2, "checks.md has no table section"
    rows = [r.strip() for r in section[1].split("\n---\n", 1)[0].splitlines()
            if r.strip().startswith("|")]
    out = []
    for row in rows[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) == 4, f"malformed checks row ({len(cells)} cells): {row[:60]}"
        out.append(tuple(cells))
    return path, text, out


@check("every assertion has one owning script, and every caller named actually runs it",
       finding="A7")
def _():
    """Item 58.

    `"No reference anywhere to a slug that has no file"` was owned by items 6, 22, 39, 40 and 42
    at once, and item 6 alone had accumulated eleven assertions in a prose list. The repository's
    idiom is one script, one job, one exit code, and a table is only worth having if it is run:
    every owner must exist and every caller named must cite the script it claims to call.
    """
    path, text, rows = _checks_table()
    assert len(rows) >= 15, (
        f"checks.md lists {len(rows)} assertions. The toolchain has more than that under "
        f"skills/*/scripts alone, so the table is a stub rather than an inventory")

    on_disk = {}
    for root, _dirs, files in os.walk(REPO):
        if ".git" in root:
            continue
        for name in files:
            if name.endswith((".py", ".sh")):
                on_disk.setdefault(name, os.path.join(root, name))

    owners, unowned = [], 0
    for assertion, owner, callers, item in rows:
        if owner == "—":
            # A specified-but-unbuilt assertion is kept as a row, not deleted: it is what
            # Phase 6 is. It must still name the item that will build it.
            assert re.search(r"\d", item), f"unowned row names no item: {assertion[:50]}"
            unowned += 1
            continue
        script = owner.strip("`")
        owners.append(script)
        assert script in on_disk, f"checks.md gives `{assertion[:40]}` an owner that does not exist: {script}"
        named = re.findall(r"`([^`]+)`", callers)
        assert named, f"{script} is listed with no caller -- a script nobody calls is a file"
        for caller in named:
            full = os.path.join(REPO, caller.replace("/", os.sep))
            assert os.path.isfile(full), f"{script}: caller {caller} does not exist"
            body = open(full, encoding="utf-8", errors="replace").read()
            assert script in body, (
                f"{caller} is listed as calling {script} and never names it. A row without an "
                f"invocation is a claim, not a caller")

    assert len(set(owners)) == len(owners), (
        f"two assertions share an owner: {[o for o in owners if owners.count(o) > 1]}. One "
        f"script, one job -- a script that owns two assertions has two reasons to exit 1")
    # `unowned` is 0 as of item 22 landing, and that is a state rather than a rule: an
    # assertion this plan specified and has not built must be a ROW rather than an omission,
    # and when the last one is built the row correctly disappears. What is asserted is the
    # convention -- an ownerless row names the item that will build it, checked above -- not
    # that one must always exist. Asserting the count would have made finishing Phase 6 fail.
    assert unowned >= 0

    # The core is where the elements are defined, and a table of assertions over them that does
    # not cite it is a second vocabulary waiting to happen.
    assert "core.md" in text, "checks.md never cites the core it makes assertions about"


@check("a feature's declared definition is checked against its own content -- by running it",
       finding="P26")
def _():
    """Item 3, and the direction is the whole design.

    The rule derives a CEILING, never a value. Report where declared exceeds what the content
    supports; stay silent where it sits below, because an author may hold a feature at
    `in-progress` for reasons the file cannot express. A rule that derives a value calls that a
    defect -- which is what the first version of this rule did, on a real corpus.

    So the silent direction is asserted as hard as the loud one: a check that reported both would
    contradict the author, and one that reported neither would be decorative.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-status.py")
    assert os.path.isfile(script), "check-status.py does not exist, so <definition> has no reader"

    root = tempfile.mkdtemp(prefix="status-3-")
    try:
        def work(project="staff-service"):
            d = os.path.join(root, "p")
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(current_fixture(project), d)
            return d

        def run(d, *extra):
            return subprocess.run([sys.executable, script, d, "--today", "2026-08-30", *extra],
                                  capture_output=True, text=True, encoding="utf-8")

        def edit(d, rel, old, new):
            p = os.path.join(d, rel.replace("/", os.sep))
            text = open(p, encoding="utf-8").read()
            assert old in text, f"fixture no longer contains {old[:40]!r}"
            open(p, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))

        # --- the baseline. The reference fixture must be clean, or every assertion below is
        #     measured against noise.
        d = work()
        p = run(d)
        assert p.returncode == 0 and "0 contradictions" in p.stdout, (
            f"the current fixture already contradicts itself:\n{p.stdout}{p.stderr}")

        # --- LOUD: a label that claims more than the file carries.
        d = work()
        edit(d, "features/narwhal-theme.md", "<user-story>", "<user-story-was>")
        edit(d, "features/narwhal-theme.md", "</user-story>", "</user-story-was>")
        p = run(d)
        assert p.returncode == 1 and "narwhal-theme" in p.stdout and "user-story" in p.stdout, (
            f"a `defined` feature with no user story was not contradicted:\n{p.stdout}")

        # --- LOUD: the one rule core 6 states outright -- `defined` cannot carry a
        #     specification gap. quokka-telemetry is the fixture feature that carries one.
        d = work()
        edit(d, "features/quokka-telemetry.md",
             "<definition>in-progress</definition>", "<definition>defined</definition>")
        p = run(d)
        assert p.returncode == 1 and "quokka-telemetry" in p.stdout, (
            f"`defined` with a specification gap was accepted:\n{p.stdout}")
        assert "specification" in p.stdout, (
            f"the contradiction does not say WHICH gap bars the label:\n{p.stdout}")

        # --- SILENT: content that supports MORE than the author declared. This must not fail
        #     the run. An author holding something back is the case the ceiling exists for.
        d = work()
        edit(d, "features/walrus-export.md",
             "<definition>defined</definition>", "<definition>tbd</definition>")
        p = run(d)
        assert p.returncode == 0, (
            f"a feature declared BELOW its ceiling failed the check. Deriving a ceiling rather "
            f"than a value is the entire design of item 3:\n{p.stdout}")
        assert "ESCALATE" in p.stdout and "walrus-export" in p.stdout, (
            f"the observation was not reported at all, which is the other failure:\n{p.stdout}")
        assert run(d, "--strict").returncode == 1, (
            "--strict does not raise escalations to failures, so there is no way to run the "
            "check in a mode that insists on them")

        # --- the gap rules, which the ceiling depends on.
        d = work()
        edit(d, "features/quokka-telemetry.md", 'kind="dependency" raised="2026-08-27"',
             'kind="wibble" raised="soon"')
        p = run(d)
        assert p.returncode == 1, f"a malformed <gap> was accepted:\n{p.stdout}"
        assert "wibble" in p.stdout and "soon" in p.stdout, (
            f"the report names neither the bad kind nor the bad date:\n{p.stdout}")

        # --- age is reported and never judged.
        d = work()
        p = run(d)
        assert "AGE" in p.stdout and "days ago" in p.stdout, (
            f"gap age is not reported, so an item raised months ago and one raised yesterday "
            f"read identically:\n{p.stdout}")

        # It reports; it never repairs.
        d = work()
        before = open(os.path.join(d, "features", "quokka-telemetry.md"), "rb").read()
        run(d)
        assert open(os.path.join(d, "features", "quokka-telemetry.md"), "rb").read() == before, (
            "check-status.py modified a feature file. A wrong status usually signals wrong "
            "CONTENT, and silently relabelling hides that")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("each mechanical test of the well-defined bar fires -- by breaking one at a time",
       finding="P26")
def _():
    """Item 40.

    Five of the eight tests are mechanical and each is broken here separately, because a bar that
    reports something on a broken feature proves only that it reports something. The judgement
    half is deliberately absent from the script and is asserted on the agent instead.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-definition.py")
    assert os.path.isfile(script), "check-definition.py does not exist, so section 4.2's bar is prose"

    root = tempfile.mkdtemp(prefix="bar-40-")
    try:
        def work():
            d = os.path.join(root, "p")
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(current_fixture("link-shelf"), d)
            return d

        def run(d, *extra):
            return subprocess.run([sys.executable, script, d, *extra],
                                  capture_output=True, text=True, encoding="utf-8")

        def edit(d, rel, old, new):
            p = os.path.join(d, rel.replace("/", os.sep))
            text = open(p, encoding="utf-8").read()
            assert old in text, f"fixture no longer contains {old[:40]!r}"
            open(p, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))

        # --- the baseline is now CLEAN, and that is the change schema-6 made. Until then this
        #     check used the fixture's own defects as its positive control -- list-links declared
        #     `defined` with no failure-path criterion and no data model, exactly the state P23
        #     measured across a real corpus. Item 40's finding was that live control firing.
        #
        #     A control that depends on a defect staying unfixed is a control that argues against
        #     fixing it. Every test below now breaks the fixture itself, so the baseline asserts
        #     the opposite thing: a corpus that passes the bar is reported as passing it, which is
        #     what stops a check that reports something unconditionally from passing everything.
        d = work()
        p = run(d)
        assert p.returncode == 0, (
            f"the current fixture does not pass the bar it is the reference for:\n{p.stdout}")
        assert not [l for l in p.stdout.splitlines() if "BAR" in l], (
            f"a feature that passes every mechanical test was reported anyway:\n{p.stdout}")

        # --- test 2: the failure path. Turn the one unwanted-behaviour criterion into a happy
        #     path and the feature must stop qualifying.
        d = work()
        edit(d, "features/save-link.md", 'pattern="unwanted-behaviour" priority="P0"',
             'pattern="event-driven" priority="P0"')
        edit(d, "features/save-link.md", 'pattern="unwanted-behaviour" priority="P1"',
             'pattern="event-driven" priority="P1"')
        p = run(d)
        assert "BAR t2" in p.stdout and "save-link" in p.stdout, (
            f"a feature whose criteria are entirely happy-path passed test 2:\n{p.stdout}")

        # --- test 2, other half: a criterion with no pattern cannot be counted at all.
        d = work()
        edit(d, "features/save-link.md", ' pattern="unwanted-behaviour" priority="P0"',
             ' priority="P0"')
        p = run(d)
        assert "BAR t2" in p.stdout and "pattern" in p.stdout, (
            f"a criterion with no `pattern` was counted anyway:\n{p.stdout}")

        # --- test 4: the data model.
        d = work()
        edit(d, "features/save-link.md", "<data-model>", "<data-model-was>")
        edit(d, "features/save-link.md", "</data-model>", "</data-model-was>")
        p = run(d)
        assert "BAR t4" in p.stdout and "save-link" in p.stdout, (
            f"a `defined` feature with no data model passed test 4:\n{p.stdout}")

        # --- test 5: a dependency with a name and no role is a brand name.
        d = work()
        edit(d, "index.md", "<purpose>HTTP API framework</purpose>", "")
        p = run(d)
        assert "BAR t5" in p.stdout and "fastapi" in p.stdout, (
            f"a dependency with no <purpose> passed test 5:\n{p.stdout}")

        # --- test 7, outbound: an edge to a feature that does not exist.
        d = work()
        edit(d, "features/tag-links.md", '<depends-on slug="save-link" kind="data"/>',
             '<depends-on slug="ghost" kind="data"/>')
        p = run(d)
        assert "BAR t7" in p.stdout and "ghost" in p.stdout, (
            f"a <depends-on> naming nothing passed test 7:\n{p.stdout}")

        # --- test 7, inbound: THE one that gets skipped. A feature makes a claim on another and
        #     declares no dependency, and the report must name both ends.
        d = work()
        edit(d, "features/list-links.md", "No pagination:",
             "Filtering belongs to tag-links. No pagination:")
        p = run(d)
        assert "EDGE" in p.stdout and "list-links" in p.stdout and "tag-links" in p.stdout, (
            f"an undeclared inbound claim was not reported:\n{p.stdout}")
        assert run(d, "--strict").returncode == 1, (
            "--strict does not raise the one-way edges, so there is no mode that insists on them")

        # --- test 8: the tautology screen, and it must not fire on a real story.
        d = work()
        edit(d, "features/save-link.md",
             "I want to store a URL with an optional title, so that I can come\n  back to it "
             "without keeping a browser tab open.",
             "I want to store a URL, so that I can store a URL.")
        p = run(d)
        assert "BAR t8" in p.stdout and "save-link" in p.stdout, (
            f"a `so that` clause restating the `I want` clause passed test 8:\n{p.stdout}")
        assert "BAR t8" not in run(work()).stdout, (
            f"test 8 fires on the fixture's real user stories, so it is a false positive "
            f"machine rather than a screen")

        # --- item 34's count: a distribution, reported and not judged. A corpus where
        #     everything is P0 carries no information, and neither does one where nothing is set;
        #     no threshold between those is defensible, so the check asserts the COUNT exists and
        #     tracks the file rather than asserting what it should be.
        d = work()
        p = run(d)
        assert re.search(r"criterion priority: .*P0 \d+", p.stdout), (
            f"the bar reports no criterion-priority distribution:\n{p.stdout}")
        assert "P2" not in p.stdout.split("criterion priority:")[1], (
            f"the fixture has no P2 criterion and the tally claims one:\n{p.stdout}")
        edit(d, "features/save-link.md", 'priority="P1" derived-from="4"',
             'priority="P2" derived-from="4"')
        assert "P2 1" in run(d).stdout.split("criterion priority:")[1], (
            "the tally does not track the file it is counting")

        # --- the gate reports and the label stays the author's.
        d = work()
        before = open(os.path.join(d, "features", "list-links.md"), "rb").read()
        run(d)
        assert open(os.path.join(d, "features", "list-links.md"), "rb").read() == before, (
            "check-definition.py edited a feature. The bar is deliberately weaker than refusing "
            "the label: a gate that blocks it invites relabelling rather than fixing")

        # --- the judgement half is NOT in the script.
        body = open(script, encoding="utf-8").read()
        for named in ("judgement", "review-definition"):
            assert named in body, (
                f"check-definition.py does not say where the tests it cannot settle go. A script "
                f"silently passing over a class of input is worse than one that says so")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the index, the feature directory and every reference reconcile -- by running it",
       finding="P27")
def _():
    """Items 6 and 42.

    `rename-feature.py` proves the operation it just performed. This proves the STATE, at any
    moment, which is the half that decays: a PRD is edited by hand for weeks after the last
    rename, and an unindexed file is a residue, real drift, or a legitimately retired feature.
    Only the third has a marker.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-rename.py")
    assert os.path.isfile(script), "check-rename.py does not exist"

    root = tempfile.mkdtemp(prefix="rename-6-")
    try:
        def work():
            d = os.path.join(root, "p")
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(current_fixture("link-shelf"), d)
            return d

        def run(d):
            return subprocess.run([sys.executable, script, d],
                                  capture_output=True, text=True, encoding="utf-8")

        def edit(d, rel, old, new):
            p = os.path.join(d, rel.replace("/", os.sep))
            text = open(p, encoding="utf-8").read()
            assert old in text, f"fixture no longer contains {old[:40]!r}"
            open(p, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))

        d = work()
        p = run(d)
        assert p.returncode == 0, f"the current fixture does not reconcile with itself:\n{p.stdout}"

        # A rename that stopped half way: the index moved and the file did not.
        d = work()
        edit(d, "index.md", 'file="features/tag-links.md"', 'file="features/tagging.md"')
        p = run(d)
        assert p.returncode == 1 and "tagging.md" in p.stdout and "tag-links.md" in p.stdout, (
            f"neither the dangling entry nor the orphaned file was named:\n{p.stdout}")

        # The file moved and its own <slug> did not.
        d = work()
        edit(d, "features/list-links.md", "<slug>list-links</slug>", "<slug>list-the-links</slug>")
        p = run(d)
        assert p.returncode == 1 and "list-the-links" in p.stdout, (
            f"a feature whose <slug> disagrees with its filename was accepted:\n{p.stdout}")

        # Item 1's residue: a <priority> left behind in a feature file.
        d = work()
        edit(d, "features/list-links.md", "<slug>list-links</slug>",
             "<slug>list-links</slug>\n    <priority>must-have</priority>")
        p = run(d)
        assert p.returncode == 1 and "priority" in p.stdout, (
            f"a feature file still carrying <priority> was accepted:\n{p.stdout}")

        # A reference to a slug with no file -- the postcondition a rename has to satisfy.
        d = work()
        edit(d, "features/save-link.md", "<description>",
             '<depends-on slug="ghost" kind="data"/>\n\n  <description>')
        p = run(d)
        assert p.returncode == 1 and "ghost" in p.stdout, (
            f"a <depends-on> resolving to nothing was accepted:\n{p.stdout}")

        # And the exit condition nobody evaluates: reported, not refused.
        d = work()
        with open(os.path.join(d, "features", "old-shelf.md"), "w", encoding="utf-8",
                  newline="\n") as f:
            f.write('<feature>\n  <meta><name>Old shelf</name><slug>old-shelf</slug>'
                    '<definition>superseded</definition></meta>\n'
                    '  <superseded-by slug="save-link"/>\n</feature>\n')
        p = run(d)
        assert p.returncode == 0, (
            f"an unindexed `superseded` file was treated as a defect. It is removed from the "
            f"index deliberately:\n{p.stdout}")
        assert "RETIRED" in p.stdout and "old-shelf" in p.stdout, (
            f"a superseded pointer nothing references any more went unreported:\n{p.stdout}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("/prd calls the checks rather than restating them, and --resume re-runs them all",
       finding="P16")
def _():
    """Items 6, 7 and 58.

    Item 6 is the CALLER, not the container. The assertions live in scripts with exit codes; this
    asserts the invocations exist where they have to run, and that `--resume` runs them across the
    whole PRD rather than across what the session touched -- the untouched features are exactly
    the ones whose labels have gone stale.
    """
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    root = "${CLAUDE_PLUGIN_ROOT}/skills/breakdown/scripts/"

    phase7 = prd[prd.find("### Phase 7:"):prd.find("### Phase 8:")]
    assert phase7.strip(), "prd.md has no Phase 7"
    for script in ("check-status.py", "check-rename.py", "check-references.py",
                   "check-definition.py"):
        # The RUNNABLE invocation, not the name. A command that discusses a script in prose
        # keeps discussing it after the command line is deleted.
        assert f"{root}{script} " in phase7, (
            f"Phase 7 never RUNS {script}; item 6's whole content is that the validation phase "
            f"is a caller of scripts rather than a list of prose questions")

    init = prd[prd.find("## Initialization"):prd.find("## Workflow Phases")]
    for script in ("check-status.py", "check-definition.py"):
        assert f"{root}{script} " in init, (
            f"--resume does not re-run {script}. Stamping only what this session touched is how "
            f"a label drifts from its content in the first place (item 7)")
    assert re.search(r"over \*\*all\*\* of them", init), (
        "the resume check does not say it runs across every feature, so it reads as a check of "
        "the ones about to be edited")

    assert "checks.md" in prd, (
        "/prd never cites the assertion table, so the next assertion added here will be added "
        "here rather than given an owner")

    # The four prose questions must not also live in the trailing section: one rule, one place.
    tail = prd[prd.find("## Consistency Checks to Perform"):]
    assert tail.strip(), "prd.md lost its Consistency Checks section"
    assert "Phase 7" in tail, (
        "the trailing consistency section restates checks instead of pointing at the phase that "
        "runs them, which is the duplication item 6 exists to remove")


@check("an unflagged feature that looks significant is a candidate, and never a failure",
       finding="P17")
def _():
    """Items 6 and 35.

    `<architecturally-significant>` is a declared judgement, so item 6 asks for candidates to be
    *screened and reported, never applied*. Both halves are asserted: the screen must fire on a
    feature that plainly qualifies, and it must never reach the exit code -- including under
    --strict, because a heuristic that can fail a build has been promoted to a rule behind
    everyone's back.
    """
    import re as _re
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-references.py")

    root = tempfile.mkdtemp(prefix="asr-35-")
    try:
        def work(project):
            d = os.path.join(root, "p")
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(current_fixture(project), d)
            return d

        def run(d, *extra):
            return subprocess.run([sys.executable, script, d, *extra],
                                  capture_output=True, text=True, encoding="utf-8")

        def unflag(d, rel):
            p = os.path.join(d, rel.replace("/", os.sep))
            text = open(p, encoding="utf-8").read()
            stripped = _re.sub(r"\s*<architecturally-significant[^>]*/>", "", text)
            assert stripped != text, f"{rel} carries no flag to remove"
            open(p, "w", encoding="utf-8", newline="\n").write(stripped)

        # --- a flagged feature is never a candidate. The flag is the author's answer, and
        #     re-asking a question somebody has already answered is how a report gets ignored.
        d = work("staff-service")
        p = run(d)
        assert p.returncode == 0, f"the reference check refused a clean fixture:\n{p.stdout}"
        assert "0 significance candidates" in p.stdout, (
            f"a feature that already declares the flag was screened anyway:\n{p.stdout}")

        # --- unflag both, and the screen must find the one that plainly qualifies.
        d = work("staff-service")
        unflag(d, "features/zebra-signin.md")
        unflag(d, "features/quokka-telemetry.md")
        p = run(d)
        assert "CANDIDATE" in p.stdout and "zebra-signin" in p.stdout, (
            f"a sign-in feature holding passwords was not screened as a candidate:\n{p.stdout}")
        assert "quality-attribute" in p.stdout, (
            f"the candidate does not say WHICH heuristic matched, so there is nothing to argue "
            f"with:\n{p.stdout}")

        # --- and it never reaches the exit code, in either mode.
        assert p.returncode == 0, f"a candidate failed the run:\n{p.stdout}"
        strict = run(d, "--strict")
        assert strict.returncode == 0, (
            f"--strict turned a heuristic into a gate. A candidate is a screen for a "
            f"conversation:\n{strict.stdout}")

        # --- reach counts documents that CHOSE to name the feature. index.md and what-next.md
        #     name every feature by construction, and counting them would hand every feature two
        #     free edges. save-link is named by three others; the number is the assertion.
        d = work("link-shelf")
        p = run(d)
        m = _re.search(r"save-link\.md: cross-cutting \(named by (\d+) other documents\)", p.stdout)
        assert m, f"the fixture's most-depended-on feature was not screened:\n{p.stdout}"
        assert m.group(1) == "3", (
            f"reach counted {m.group(1)} documents. index.md and what-next.md name every "
            f"feature, so including them makes the threshold meaningless")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the criteria challenger proposes, never writes, and carries both of its modes",
       finding="P23")
def _():
    """Item 8.

    A same-persona author would deepen the bias the corpus already has: the best-defined features
    carry negative cases and abstention behaviour, which is exactly what someone who has just
    written the happy path does not add. So the agent is adversarial, opt-in per feature, and
    proposes only -- and `proposes only` is asserted against its TOOLS rather than its prose,
    because an agent holding Write can write whatever its prose says.
    """
    path = os.path.join(AGENTS, "prd-criteria-author.md")
    assert os.path.isfile(path), "agents/prd-criteria-author.md does not exist"
    fm, body = parse_frontmatter(path)
    assert fm.get("name") == "prd-criteria-author", f"declares name {fm.get('name')!r}"

    tools = str(fm.get("tools") or "")
    for writing in ("Write", "Edit", "NotebookEdit"):
        assert writing not in tools, (
            f"the agent is given {writing}. It proposes criteria and the author accepts or "
            f"rejects each one; an agent that can write closes the loop this item says must "
            f"stay open")

    flat = prose(body)
    for mode in ("propose-criteria", "review-definition"):
        assert mode in body, f"the agent does not carry its {mode} mode"
    # Its checklist is the six EARS patterns -- that is what turns a vague brief into a
    # specific question about which pattern is unrepresented.
    for pattern in ("ubiquitous", "event-driven", "state-driven", "optional-feature",
                    "unwanted-behaviour", "complex"):
        assert pattern in body, f"the agent's checklist is missing the {pattern} pattern"
    assert re.search(r"user-story|user story", flat, re.I), (
        "the agent does not draft the user story, so 44 of 64 features still name no user")
    assert "data-model" in body, (
        "the agent does not propose the data-model note, which `defined` requires")

    # It is dispatched, per feature, from both ends of the workflow.
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    dispatches = re.findall(r'subagent_type:\s*"prd-criteria-author"', prd)
    assert len(dispatches) >= 2, (
        f"{len(dispatches)} dispatch(es) of the challenger. It has two modes and two moments -- "
        f"proposing criteria while the feature is being written, and reviewing a definition "
        f"before the label is set")
    assert re.search(r"opt-in, per feature", prose(prd)), (
        "nothing says the challenger is opt-in per feature. Run unattended across twenty `tbd` "
        "features it produces plausible criteria nobody agreed to, and a `defined` derived from "
        "those is true and worthless")


# ------------------------------------------------- the residue (10/24/32/38, group 5e)


def _versioned_task_tree(root, features, slug="link-shelf"):
    """A tasks directory with one task per (slug, tier, criteria), plus its manifest."""
    import json
    tasks = os.path.join(root, "tasks")
    os.makedirs(os.path.join(tasks, "2-backend"), exist_ok=True)
    for i, (feature, tier, crit) in enumerate(features, start=1):
        with open(os.path.join(tasks, "2-backend", f"L2-{i:03d}-{feature}.xml"),
                  "w", encoding="utf-8", newline="\n") as f:
            f.write(f"<task>\n  <meta><id>L2-{i:03d}</id><name>{feature}</name>\n"
                    f"    <layer>2-backend</layer><priority>1</priority>\n"
                    f"    <source-feature>{feature}</source-feature><moscow>{tier}</moscow>\n"
                    f"    <satisfies-criteria>{crit}</satisfies-criteria>\n"
                    f"    <requirement-level>P0</requirement-level></meta>\n"
                    f"  <objective>Implement {feature}.</objective>\n"
                    f"  <files-to-create><file>app/{feature}.py</file></files-to-create>\n"
                    f"</task>\n")
    with open(os.path.join(tasks, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"prd": {"slug": slug, "project_path": root}}, f)
    subprocess.run([sys.executable,
                    os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py"),
                    tasks, "--project-path", root],
                   capture_output=True, text=True)
    return tasks


@check("the task set is reviewable without opening every task -- by running it", finding="P22")
def _():
    """Item 32.

    Every other item in this plan adds fidelity -- more content carried, more faithfully -- and
    the review burden scales with it. Self-containment stays, because it is right for the
    CONSUMER; what was missing is a view OVER the set. It comes off a traversal that already
    exists, so a second walker would be a second answer to "what tasks exist".
    """
    import shutil
    import tempfile

    builder = os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py")
    root = tempfile.mkdtemp(prefix="summary-32-")
    try:
        tasks = _versioned_task_tree(root, [("save-link", "must-have", "1,2,3"),
                                  ("tag-links", "should-have", "1,2")])
        summary = os.path.join(tasks, "tasks-summary.md")
        assert os.path.isfile(summary), (
            "build-manifest.py wrote no tasks-summary.md, so the task set can still only be "
            "reviewed by opening every task")
        text = open(summary, encoding="utf-8").read()

        # The four things a reviewer needs per task, none of which the manifest carried before.
        for wanted in ("save-link", "must-have", "Implement save-link.", "app/save-link.py"):
            assert wanted in text, f"the summary does not carry {wanted!r}:\n{text}"
        assert "1, 2, 3" in text, f"the summary does not name the criteria a task satisfies:\n{text}"

        # It is DERIVED, so drift is an exit code rather than a stale file nobody notices.
        p = subprocess.run([sys.executable, builder, tasks, "--verify"],
                           capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 0, f"a freshly built summary reads as drifted:\n{p.stdout}{p.stderr}"

        with open(summary, "a", encoding="utf-8", newline="\n") as f:
            f.write("\nhand-edited\n")
        p = subprocess.run([sys.executable, builder, tasks, "--verify"],
                           capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 1 and "tasks-summary.md" in (p.stdout + p.stderr), (
            f"a hand-edited summary was accepted, so `derived` is a claim rather than a "
            f"property:\n{p.stdout}{p.stderr}")

        os.remove(summary)
        p = subprocess.run([sys.executable, builder, tasks, "--verify"],
                           capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 1, "a missing summary was accepted"

        # And it does NOT try to diff task text. That comparison is check-coverage.py's, made
        # possible by item 17's verbatim criterion ids -- a prose diff would be a second answer.
        body = open(builder, encoding="utf-8").read()
        assert "check-coverage.py" in body, (
            "nothing in the builder says where the criteria comparison actually lives, so the "
            "next person adds a worse one here")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the manifest's version stamps finally have a reader -- by running it", finding="P28")
def _():
    """Item 24.

    Both stamps have been written since item 4.5 and NOTHING read either of them. A stamp nobody
    reads is provenance theatre: it makes an artefact look checked while the incompatibility it
    exists to catch goes through in silence.

    The two are asserted separately, because conflating them is the defect P28 named:
    `schema_version` decides and `toolchain_version` is reported.
    """
    import json
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "execute", "scripts", "check-compatibility.py")
    assert os.path.isfile(script), "check-compatibility.py does not exist"

    # The reader's accepted version is DECLARED here, not imported from the producer. Importing
    # it would make producer and reader equal by construction and the check a function that
    # returns True.
    body = open(script, encoding="utf-8").read()
    code = body.split('"""', 2)[-1]          # past the docstring, which argues about the import
    borrowed = [ln for ln in code.splitlines()
                if "MANIFEST_SCHEMA_VERSION" in ln
                or ("build-manifest" in ln and ("import" in ln or "spec_from_file" in ln))]
    assert not borrowed, (
        "the reader takes its accepted version from the producer, so the two can never disagree "
        f"and the compatibility check can never fire: {borrowed}")
    assert re.search(r"^READER_SCHEMA\s*=", code, re.M), (
        "the reader declares no accepted version of its own, so there is nothing for a manifest "
        "to be compared against")

    root = tempfile.mkdtemp(prefix="compat-24-")
    try:
        tasks = _versioned_task_tree(root, [("save-link", "must-have", "1")])

        def with_version(schema, toolchain="0.0.1"):
            path = os.path.join(tasks, "manifest.json")
            m = json.load(open(path, encoding="utf-8"))
            if schema is None:
                m.pop("schema_version", None)
            else:
                m["schema_version"] = schema
            m["toolchain_version"] = toolchain
            json.dump(m, open(path, "w", encoding="utf-8"), indent=2)
            return subprocess.run([sys.executable, script, tasks],
                                  capture_output=True, text=True, encoding="utf-8")

        # What build-manifest.py just wrote must be readable, or the pair is broken on arrival.
        p = subprocess.run([sys.executable, script, tasks],
                           capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 0 and "0 refusals" in p.stdout, (
            f"the reader refuses the manifest the producer just wrote:\n{p.stdout}{p.stderr}")

        # A major it has never seen: REFUSE. Reading it anyway produces a plausible wrong answer.
        p = with_version("99.0")
        assert p.returncode == 1 and "REFUSED" in p.stdout, (
            f"a manifest from a future major was accepted:\n{p.stdout}")

        # A newer minor: additive, so it RUNS -- and says what it is ignoring.
        p = with_version("1.99")
        assert p.returncode == 0, (
            f"an additive minor was refused. Minors being additive is what let item 16 add four "
            f"fields without breaking a reader written against 1.0:\n{p.stdout}")
        assert "WARN" in p.stdout, f"a newer minor passed in silence:\n{p.stdout}"

        # Absent: warn, never refuse. It is a manifest from before the stamp existed.
        p = with_version(None)
        assert p.returncode == 0 and "WARN" in p.stdout, (
            f"a manifest with no schema_version was refused rather than reported:\n{p.stdout}")

        # PROVENANCE is reported and never decided on. A patch release moves toolchain_version
        # and not schema_version, so refusing on it would make every release a migration.
        p = with_version("1.2", toolchain="0.0.1")
        assert p.returncode == 0, (
            f"a manifest from a different toolchain was refused on PROVENANCE. That is the "
            f"conflation P28 exists to prevent:\n{p.stdout}")
        assert "NOTE" in p.stdout and "0.0.1" in p.stdout, (
            f"the producing toolchain is not reported at all:\n{p.stdout}")

        # And /execute must actually run it.
        skill = open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read()
        assert "scripts/check-compatibility.py {tasks_path}" in skill, (
            "/execute never RUNS the compatibility check; naming a script in prose is what "
            "item 9 replaced, not what item 24 asked for")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("what-next.md records what wrote it, once, and something reads it", finding="P28")
def _():
    """Item 24's other half.

    The stamp is inserted when ABSENT and never updated. Rewriting it on every derivation would
    turn provenance into a version tracker: every plugin release would make every what-next.md
    look stale, and a file that is always stale is a check nobody runs.
    """
    import shutil
    import tempfile

    builder = os.path.join(REPO, "schema", "scripts", "build-what-next.py")
    lister = os.path.join(SKILLS, "breakdown", "scripts", "list-prds.py")

    root = tempfile.mkdtemp(prefix="stamp-24-")
    try:
        prd = os.path.join(root, "docs", "prd", "link-shelf")
        os.makedirs(os.path.dirname(prd), exist_ok=True)
        shutil.copytree(current_fixture("link-shelf"), prd)
        wn = os.path.join(prd, "what-next.md")

        assert "<toolchain-version>" not in open(wn, encoding="utf-8").read(), (
            "the fixture already carries a stamp, so this check cannot see one being written")

        subprocess.run([sys.executable, builder, prd], capture_output=True, text=True)
        stamped = open(wn, encoding="utf-8").read()
        m = re.search(r"<toolchain-version>\s*([^<\s]+)\s*</toolchain-version>", stamped)
        assert m, f"build-what-next.py wrote no <toolchain-version>:\n{stamped[:400]}"
        plugin = json.load(open(os.path.join(REPO, ".claude-plugin", "plugin.json"),
                                encoding="utf-8"))["version"]
        assert m.group(1) == plugin, (
            f"stamped {m.group(1)}, plugin declares {plugin}. A provenance stamp that does not "
            f"match what produced it is worse than none")
        assert stamped.index("<toolchain-version>") < stamped.index("</meta>"), (
            "the stamp landed outside <meta>, where no reader looks for it")

        # Written once. An older stamp is the ORDINARY case and must survive a rebuild.
        open(wn, "w", encoding="utf-8", newline="\n").write(
            stamped.replace(f"<toolchain-version>{plugin}<", "<toolchain-version>0.0.1<"))
        subprocess.run([sys.executable, builder, prd], capture_output=True, text=True)
        assert "<toolchain-version>0.0.1</toolchain-version>" in open(wn, encoding="utf-8").read(), (
            "the builder overwrote an older stamp. That turns provenance into a version tracker "
            "and makes every PRD look stale on every release")

        p = subprocess.run([sys.executable, builder, prd, "--check"],
                           capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 0, (
            f"--check fails on an older stamp, so every plugin release would make every PRD "
            f"read as stale:\n{p.stdout}{p.stderr}")

        # And it has a READER. An element with no reader is the defect this plan removes.
        p = subprocess.run([sys.executable, lister, os.path.join(root, "docs", "prd")],
                           capture_output=True, text=True, encoding="utf-8")
        assert "0.0.1" in p.stdout and plugin in p.stdout, (
            f"list-prds.py does not report the toolchain that wrote the PRD:\n{p.stdout}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the gate asserts three things by name, and the switch decides only whether it stops",
       finding="P25")
def _():
    """Item 38.

    Placed at the /breakdown -> /execute boundary and nowhere else: not inside /execute, which is
    the unattended overnight case P19 refuses to block. The switch controls the STOP, never the
    CHECK -- the report is the valuable half, and the assertions are worth running either way.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py")
    assert os.path.isfile(script), "check-gate.py does not exist, so item 38's gate is prose"

    root = tempfile.mkdtemp(prefix="gate-38-")
    try:
        prd = os.path.join(root, "prd")
        shutil.copytree(current_fixture("link-shelf"), prd)

        def track(enabled):
            with open(os.path.join(root, "architecture.md"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write('# Architecture: Gate\n\n## Machine-Readable Section\n'
                        '<architecture version="1.1">\n  <rules>\n'
                        f'    <design-track enabled="{enabled}"/>\n'
                        '  </rules>\n</architecture>\n')

        def gate(tasks, *extra):
            return subprocess.run([sys.executable, script, prd, tasks,
                                   "--project-path", root, *extra],
                                  capture_output=True, text=True, encoding="utf-8")

        # tag-links carries a `decision` gap in the fixture, so building it is assertion 3's
        # live case: an undecided question built anyway is an invented one.
        full = _versioned_task_tree(root, [("save-link", "must-have", "1,2,3,4"),
                                 ("list-links", "must-have", "1,2,3"),
                                 ("tag-links", "should-have", "1,2,3,4")])

        track("false")
        p = gate(full)
        assert p.returncode == 0, (
            f"the gate refused with the design track OFF. Off means report and return -- a gate "
            f"that stops an unattended run is the thing P19 refuses:\n{p.stdout}")
        assert "tag-links" in p.stdout and "decision" in p.stdout, (
            f"assertion 3 did not name the blocked feature:\n{p.stdout}")

        # Same tree, same findings, switch on: it stops. The findings did not change; the
        # consequence did, which is the whole content of <design-track>.
        track("true")
        p_on = gate(full)
        assert p_on.returncode == 1, (
            f"the design track is ON and the gate did not stop:\n{p_on.stdout}")
        assert "tag-links" in p_on.stdout, "the findings changed with the switch, and must not"

        # Assertion 1: a feature with no task, named -- not counted.
        os.remove(os.path.join(full, "2-backend", "L2-003-tag-links.xml"))
        subprocess.run([sys.executable,
                        os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py"),
                        full, "--project-path", root], capture_output=True, text=True)
        track("false")
        p = gate(full)
        assert "SHORTFALL" in p.stdout and "tag-links" in p.stdout, (
            f"a feature with no task was not reported by name:\n{p.stdout}")

        # And the shortfall must reach the CONSEQUENCE, not only the report. Removing the
        # tag-links task also removes assertion 3's finding -- it is no longer a built feature --
        # so coverage is the only finding left, and with the track on it must stop the run.
        # A mutant that printed this report and counted no finding survived a check asserting
        # the word SHORTFALL: the report is the visible half and the exit code is the half that
        # does anything.
        track("true")
        p = gate(full)
        assert p.returncode == 1, (
            f"a coverage shortfall was reported and then not counted, so the gate reads as "
            f"`nothing to confirm` with a feature missing every task:\n{p.stdout}")
        assert "confirmation required" in p.stdout, (
            f"the gate stopped without saying that is what it did:\n{p.stdout}")

        # Assertion 2: a significant feature nothing drives, scoped to what was BUILT.
        prd2 = os.path.join(root, "prd2")
        shutil.copytree(current_fixture("staff-service"), prd2)
        tasks2 = _versioned_task_tree(os.path.join(root, "s"), [("zebra-signin", "must-have", "1,2")],
                            slug="staff-service")
        p = subprocess.run([sys.executable, script, prd2, tasks2, "--priority", "must-have"],
                           capture_output=True, text=True, encoding="utf-8")
        assert "zebra-signin" in p.stdout, (
            f"a built, architecturally-significant feature that no record drives went "
            f"unreported:\n{p.stdout}")
        assert "quokka-telemetry" not in p.stdout, (
            f"the gate reported a significant feature nobody built. Its question is whether THIS "
            f"task set may proceed:\n{p.stdout}")

        # It runs the owners rather than re-deciding what they decide.
        body = open(script, encoding="utf-8").read()
        for owner in ("check-coverage.py", "check-references.py"):
            assert owner in body, f"the gate does not run {owner}; it has its own opinion instead"

        # /breakdown must actually run it, as a command rather than as a paragraph about one.
        skill = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
        assert "scripts/check-gate.py {prd_dir} {tasks_dir}" in skill, (
            "/breakdown never RUNS the gate, so item 38 is a script nothing invokes")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("`<design-track>` has a host artefact, and an unset switch is refused", finding="P25")
def _():
    """Item 38's other half.

    `decision-record.md` described the switch and no artefact had anywhere to write it: a
    reference describing a setting with no home, and a gate that did not exist to read it. An
    element present with no `enabled` is refused rather than defaulted -- a project that meant to
    say something and did not is not the same as one that never opted in.
    """
    import shutil
    import tempfile

    fmt = open(os.path.join(SKILLS, "breakdown", "references", "architecture-format.md"),
               encoding="utf-8").read()
    assert "<design-track" in fmt, (
        "architecture.md's format spec has no <design-track>, so the switch decision-record.md "
        "describes still has nowhere to live")

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-architecture.py")
    root = tempfile.mkdtemp(prefix="track-38-")
    try:
        def arch(rule):
            with open(os.path.join(root, "architecture.md"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write('# Architecture: T\n\n## Machine-Readable Section\n'
                        f'<architecture version="1.1">\n  <rules>\n    {rule}\n'
                        '  </rules>\n</architecture>\n')
            return subprocess.run([sys.executable, script, root, "--json"],
                                  capture_output=True, text=True, encoding="utf-8")

        p = arch('<design-track enabled="true" adr-dir="../decisions"/>')
        assert p.returncode == 0, f"a valid design-track was refused:\n{p.stdout}{p.stderr}"
        parsed = json.loads(p.stdout)["design_track"]
        assert parsed["enabled"] is True and parsed["adr_dir"] == "../decisions", (
            f"the switch did not parse: {parsed}")

        p = arch('<design-track enabled="false"/>')
        assert json.loads(p.stdout)["design_track"]["enabled"] is False

        p = arch('<design-track adr-dir="../decisions"/>')
        assert p.returncode == 1 and "design-track" in p.stderr, (
            f"an element with no `enabled` was defaulted rather than refused. A switch nobody "
            f"set is not a switch set to off:\n{p.stdout}{p.stderr}")

        p = arch('<design-track enabled="yes"/>')
        assert p.returncode == 1, f"`yes` was accepted as a boolean:\n{p.stdout}{p.stderr}"

        # Absent element and absent file both mean off -- the shipped behaviour, not a fallback.
        p = arch('<testing default="tdd"/>')
        assert json.loads(p.stdout)["design_track"]["enabled"] is False, (
            "an architecture.md that never mentions the design track does not read as off")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("`/prd` writes features one at a time, and edits re-read only what it is editing",
       finding="P5")
def _():
    """Item 10.

    P5 at the authoring end: `/prd` drafting sixty-four features in one context is the same
    problem `/breakdown` had reading them in one gulp, in the direction nobody was watching.
    Item 18 fixed the reading side and left the writing side alone.
    """
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    output = prd[prd.find("### Phase 9: Output"):prd.find("## Output Formats")]
    assert output.strip(), "prd.md has no Phase 9"
    flat = prose(output)

    assert re.search(r"one file at a time", flat), (
        "Phase 9 does not say to write feature files one at a time, so the whole set is drafted "
        "into one context -- which is P5, at the authoring end")
    assert re.search(r"P5", output), (
        "the rule is stated without the finding it comes from, so the next rewrite drops it as "
        "a style preference")
    assert re.search(r"re-read only the feature being edited", flat), (
        "nothing bounds what a later EDIT loads, which is where the blob comes back")

    # The derived block is not hand-written either, and the command must run its producer.
    assert "schema/scripts/build-what-next.py {prd_dir}" in prd, (
        "/prd never runs build-what-next.py, so <authoring-gaps> goes back to being "
        "hand-maintained -- which the corpus shows never happens")


# ------------------------------------------------ hold it in place (22/23, Phase 6)


@check("every artefact is the shape its own schema version describes -- by running it",
       finding="P10")
def _():
    """Item 22, and item 23's `each fixture validates against its OWN schema`.

    P10 is a general failure with a specific symptom: the spec said XML, the run produced
    markdown, and nothing noticed for weeks. The version is DETECTED, never declared -- the
    marker is the shape (item 41) -- so a schema-1 fixture is not broken for lacking
    `<user-story>`; it is a schema-1 fixture, and is judged by schema-1's rules.
    """
    import shutil
    import tempfile

    script = os.path.join(REPO, "schema", "scripts", "check-artefacts.py")
    assert os.path.isfile(script), "check-artefacts.py does not exist, so P10 has no check"

    def run(path, *extra):
        # errors="replace": a report quoting a document quotes its em dashes, and a pipe on
        # Windows is not UTF-8. A check that dies decoding its subject has measured nothing.
        return subprocess.run([sys.executable, script, path, *extra], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    _path, reg = schema_registry()
    versions = sorted(reg["versions"])
    assert len(versions) >= 2, "there is only one fixture version, so `its own schema` is vacuous"

    # --- every fixture version, judged by its own rules. The schema-1 fixtures predate half
    #     the elements the current schema requires and must not be reported for it.
    for version in versions:
        root = os.path.join(REPO, "tests", "fixture", "prd", version)
        p = run(root)
        invalid = [ln for ln in p.stdout.splitlines() if "INVALID" in ln]
        # staff-service carried a document-level <status> outside core 3's enum in schema-1..5,
        # reported rather than fixed because those fixtures are frozen. schema-6 fixes it, so the
        # CURRENT version must be clean and the frozen ones keep their known defect -- which is
        # also the assertion that the fix actually reached the current fixture.
        if version == reg["current"]:
            assert not invalid, (
                f"{version} is the current fixture and reports a defect it should have been "
                f"fixed by:\n" + "\n".join(invalid))
        else:
            assert all("staff-service" in ln for ln in invalid), (
                f"{version} reports a defect outside the one the corpus is known to carry:\n"
                + "\n".join(invalid))
        assert not [ln for ln in p.stdout.splitlines()
                    if "INVALID" in ln and "user-story" in ln], (
            f"{version} is being judged by a LATER schema's rules -- an older fixture reported "
            f"for an element its version does not have:\n{p.stdout}")

    # --- and an invalid document status is named, by file and by value. The corpus used to
    #     supply this defect and schema-6 fixed it, so the check now INJECTS one: a control that
    #     depends on a defect staying unfixed is a control that argues against fixing it.
    inject = tempfile.mkdtemp(prefix="artefacts-status-")
    try:
        d = os.path.join(inject, "p")
        shutil.copytree(os.path.join(REPO, "tests", "fixture", "prd", reg["current"],
                                     "staff-service"), d)
        idx = os.path.join(d, "index.md")
        text = open(idx, encoding="utf-8").read()
        assert "<status>in-progress</status>" in text, (
            f"the current fixture's index.md no longer carries a document status to break:\n"
            f"{text[:300]}")
        open(idx, "w", encoding="utf-8", newline="\n").write(
            text.replace("<status>in-progress</status>", "<status>defined</status>", 1))
        p = run(d)
        assert p.returncode == 1, "an invalid document status was not reported at all"
        assert "index.md" in p.stdout and "'defined'" in p.stdout, (
            f"the report does not name the file and the value:\n{p.stdout}")
    finally:
        shutil.rmtree(inject, ignore_errors=True)

    root = tempfile.mkdtemp(prefix="artefacts-22-")
    try:
        def work():
            d = os.path.join(root, "p")
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(current_fixture("link-shelf"), d)
            return d

        def edit(d, rel, old, new):
            p_ = os.path.join(d, rel.replace("/", os.sep))
            text = open(p_, encoding="utf-8").read()
            assert old in text, f"fixture no longer contains {old[:40]!r}"
            open(p_, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))

        d = work()
        assert run(d).returncode == 0, f"a clean fixture was reported invalid:\n{run(d).stdout}"

        # Each enum, one at a time. A checker that reports SOMETHING on a broken file proves
        # only that it reports something.
        for rel, old, new, wanted in (
                ("features/save-link.md", 'pattern="event-driven"', 'pattern="wibble"', "wibble"),
                ("features/save-link.md", 'priority="P0"', 'priority="P9"', "P9"),
                ("features/list-links.md", "<definition>defined</definition>",
                 "<definition>shipped</definition>", "shipped"),
                ("index.md", 'priority="must-have"', 'priority="vital"', "vital"),
                ("what-next.md", 'kind="breakdown"', 'kind="vibes"', "vibes")):
            d = work()
            edit(d, rel, old, new)
            p = run(d)
            assert p.returncode == 1 and wanted in p.stdout, (
                f"{new} passed as a valid value:\n{p.stdout}")

        # A retired element is refused rather than ignored.
        d = work()
        edit(d, "features/tag-links.md", "<gaps>", "<phases><phase>2</phase></phases>\n\n  <gaps>")
        p = run(d)
        assert p.returncode == 1 and "phases" in p.stdout, (
            f"<phases> was retired at item 5 and passed anyway:\n{p.stdout}")

        # A pre-rename spelling is ACCEPTED ON READ -- core 3's policy for all three renames.
        # Refusing it would strand every artefact authored before the rename.
        d = work()
        edit(d, "features/list-links.md", "<definition>defined</definition>",
             "<status>defined</status>")
        p = run(d)
        # Assert the LINE, not the word. `OLD` also appears on the "is at schema-1" notice the
        # same edit triggers, so a check looking for the token passed while the rule it was
        # written for sat behind an unreachable branch -- which is how the mutation round found
        # the branch rather than the check.
        spelled = [ln for ln in p.stdout.splitlines()
                   if "OLD" in ln and "still spells it" in ln and "list-links" in ln]
        assert spelled, f"the pre-item-45 spelling was not reported as such:\n{p.stdout}"
        assert p.returncode == 0, (
            f"an artefact in the pre-item-45 spelling was REFUSED. Accepted on read, never "
            f"written, is the policy all three renames share:\n{p.stdout}")

        # It does not decide what another script owns. Duplicate criterion ids are
        # check-definition.py's, and two owners for one assertion is what checks.md prevents.
        d = work()
        edit(d, "features/save-link.md", '<criterion id="2"', '<criterion id="1"')
        assert run(d).returncode == 0, (
            "check-artefacts reported a duplicate criterion id, which check-definition.py owns")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Both ends of the pipeline run it: producer-side is early warning, consumer-side refuses.
    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()
    breakdown = open(os.path.join(SKILLS, "breakdown", "SKILL.md"), encoding="utf-8").read()
    assert "schema/scripts/check-artefacts.py docs/prd/{slug}" in prd, (
        "/prd never RUNS the artefact check on what it just wrote")
    assert "schema/scripts/check-artefacts.py {input_path_or_prd_dir}" in breakdown, (
        "/breakdown never RUNS the artefact check on its input, so a malformed document becomes "
        "forty malformed tasks")


@check("every element the schema defines has a reader, or a written reason -- by running it",
       finding="P4")
def _():
    """Item 23, and the plan calls this its closing argument.

    P2 and P4 were both invisible to a suite that reads the files, because **the failure is an
    absent consumer rather than a wrong string**. An audit of the plan against this rule found
    nine failures in a document whose own conclusion is the rule.

    The reader is MEASURED, not declared: a registry of 128 rows would be 128 claims. What is
    declared is the exception, and an element with neither a reader nor a row fails.
    """
    import shutil
    import tempfile

    script = os.path.join(REPO, "schema", "scripts", "check-readers.py")
    assert os.path.isfile(script), "check-readers.py does not exist"
    doc = os.path.join(SCHEMA, "readers.md")
    assert os.path.isfile(doc), "schema/readers.md does not exist"

    def run(repo=None, *extra):
        return subprocess.run([sys.executable, script] + (["--repo", repo] if repo else [])
                              + list(extra), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    p = run()
    assert p.returncode == 0, (
        f"an element in this repository has no reader and no recorded reason:\n{p.stdout}")
    m = re.search(r"(\d+) elements defined: (\d+) read by a script, (\d+) by an instruction, "
                  r"(\d+) unread \((\d+) open\), (\d+) undeclared", p.stdout)
    assert m, f"the audit prints no summary to assert on:\n{p.stdout}"
    total, by_script, undeclared = int(m.group(1)), int(m.group(2)), int(m.group(6))
    assert total > 100, f"only {total} elements found; the extraction has stopped working"
    assert by_script > total // 2, (
        f"only {by_script} of {total} elements are read by a SCRIPT. An instruction reader is "
        f"prose about a mechanism, and prose outlives the mechanism")
    assert undeclared == 0

    # `open` is a verdict, not a failure -- the parity.md rule, reached again. Group 8b closed
    # the last three, so this used to assert that some existed and now cannot: the verdict has to
    # keep working for a corpus that has none of it, or the next unread element arrives to a
    # vocabulary nothing exercises.
    #
    # The parser proof moved with it. `assert opens` was doubling as evidence that the table was
    # being read at all -- a control that depended on rows nobody had closed yet, which is the
    # same shape as the three fixture-defect controls schema-6 had to rewrite.
    verdicts = open(os.path.join(SCHEMA, "readers.md"), encoding="utf-8").read()
    assert re.search(r"\|\s*`open`\s*\|", verdicts), (
        "readers.md no longer DEFINES the `open` verdict. Closing every open row is good news; "
        "deleting the verdict means the next producer with no consumer has nowhere to be "
        "recorded, and gets decided by whoever notices it")
    rows = [ln for ln in verdicts.splitlines()
            if ln.startswith("| `") and "|" in ln[3:]]
    assert len(rows) > 10, (
        f"only {len(rows)} verdict rows parsed out of readers.md, so `no open rows` may be the "
        f"parser having quietly stopped reading the table rather than an empty exception list")
    opens = [ln for ln in p.stdout.splitlines() if "OPEN" in ln]
    assert run(None, "--strict").returncode == (1 if opens else 0), (
        f"--strict disagrees with the audit about the {len(opens)} open row(s) it reported")

    # --- the assertion itself, on a synthetic repository: an element nobody reads FAILS.
    root = tempfile.mkdtemp(prefix="readers-23-")
    try:
        def build(template, table_rows, reader="", plan=""):
            shutil.rmtree(root, ignore_errors=True)
            os.makedirs(os.path.join(root, "schema"))
            os.makedirs(os.path.join(root, "skills", "demo"))
            os.makedirs(os.path.join(root, "docs"))
            os.makedirs(os.path.join(root, "tests"))
            with open(os.path.join(root, "docs", "plan.md"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write("# Plan\n\n" + plan + "\n")
            # A .py under tests/, because that is where the exclusion actually bites: a markdown
            # file outside skills/commands/agents/schema is not a candidate reader anyway, so a
            # docs/*.md probe alone leaves the rule untested.
            with open(os.path.join(root, "tests", "probe.py"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write("# regression probe\nPROBE = %r\n" % plan)
            with open(os.path.join(root, "schema", "core.md"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write("# Core\n\n```xml\n" + template + "\n```\n")
            with open(os.path.join(root, "schema", "readers.md"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write("# Readers\n\n## The exceptions\n\n| Element | Verdict | Why |\n"
                        "|---|---|---|\n" + table_rows + "\n\n---\n")
            with open(os.path.join(root, "skills", "demo", "SKILL.md"), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write("---\nname: demo\n---\n\n" + reader + "\n")
            return root

        p = run(build("<thing>\n  <read-me/>\n  <nobody-reads-me/>\n</thing>", "",
                      "This skill reads <read-me/> and <thing>."))
        assert p.returncode == 1 and "nobody-reads-me" in p.stdout, (
            f"an element nothing names passed the audit:\n{p.stdout}")
        assert "read-me" not in p.stdout.replace("nobody-reads-me", ""), (
            f"an element that IS named was reported as unread:\n{p.stdout}")

        # Declaring it is what makes it pass -- and the reason travels with it.
        p = run(build("<thing>\n  <read-me/>\n  <nobody-reads-me/>\n</thing>",
                      "| nobody-reads-me | unread by design | prose for a human |",
                      "This skill reads <read-me/> and <thing>."))
        assert p.returncode == 0, f"a declared exception still failed:\n{p.stdout}"

        # An exception list that outlives its elements is a list nobody has read.
        p = run(build("<thing>\n  <read-me/>\n</thing>",
                      "| gone-element | unread by design | it left |",
                      "This skill reads <read-me/> and <thing>."))
        assert p.returncode == 1 and "gone-element" in p.stdout, (
            f"readers.md declared an element no schema defines and the audit accepted it:"
            f"\n{p.stdout}")

        # A verdict outside the three is a verdict nobody agreed on.
        p = run(build("<thing>\n  <read-me/>\n  <nobody-reads-me/>\n</thing>",
                      "| nobody-reads-me | probably fine | shrug |",
                      "This skill reads <read-me/> and <thing>."))
        assert p.returncode == 1 and "probably fine" in p.stdout, (
            f"an invented verdict was accepted:\n{p.stdout}")

        # Writing ABOUT an element is not reading it. The plan and this suite name every element
        # in the schema; counting them would make "somebody documented it" indistinguishable
        # from "somebody consumes it", which is the distinction the whole audit is made of.
        p = run(build("<thing>\n  <read-me/>\n  <nobody-reads-me/>\n</thing>", "",
                      "This skill reads <read-me/> and <thing>.",
                      plan="Item 99 proposes <nobody-reads-me/> and argues for it at length."))
        assert p.returncode == 1 and "nobody-reads-me" in p.stdout, (
            f"a document under docs/ counted as a reader, so writing about an element is now "
            f"indistinguishable from consuming it:\n{p.stdout}")

        # The defining document is NOT a reader. Otherwise every element reads itself and the
        # whole audit is a function that returns True.
        p = run(build("<thing>\n  <only-in-the-schema/>\n</thing>", "", ""))
        assert p.returncode == 1 and "only-in-the-schema" in p.stdout, (
            f"an element defined in a schema document counted as read by that document:"
            f"\n{p.stdout}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # Every open row carries a reason. A verdict with no `why` is the silence the file forbids.
    section = open(doc, encoding="utf-8").read().split("## The exceptions", 1)
    assert len(section) == 2, "readers.md has no exceptions table"
    for line in section[1].split("\n---\n", 1)[0].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in ("element", "") or set(line) <= set("|- "):
            continue
        assert len(cells[2]) > 30, f"exception {cells[0]} gives no reason: {cells[2]!r}"


@check("the definition enum is one set, wherever it is implemented", finding="P29")
def _():
    """Item 23: `the status enum in the template matches the one the derivation script
    implements`.

    Three programs and one document carry this enum. It is the shape of P29's defect one level
    down: not four things called `status`, but one vocabulary written out four times, drifting a
    value at a time until a feature is valid in one reader and invalid in the next.
    """
    import importlib.util

    def load(rel, name):
        spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    artefacts = load("schema/scripts/check-artefacts.py", "art")
    status = load("skills/breakdown/scripts/check-status.py", "st")

    implemented = set(status.LADDER) | set(status.OFF_LADDER)
    assert artefacts.DEFINITION == implemented, (
        f"check-artefacts accepts {sorted(artefacts.DEFINITION)} and check-status derives over "
        f"{sorted(implemented)}. A value valid in one reader and invalid in the next is P29 one "
        f"level down")

    # And the document both of them answer to. Core 3's table is the definition; a script that
    # has drifted from it is a script obeying a rule nobody wrote.
    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()
    row = [ln for ln in core.splitlines()
           if ln.startswith("|") and "`<definition>`" in ln]
    assert row, "core.md's status table has no <definition> row"
    documented = set(re.findall(r"`([a-z-]+)`", row[0].split("|")[-2]))
    assert documented, f"the <definition> row names no values: {row[0]}"
    assert documented <= artefacts.DEFINITION, (
        f"core.md documents {sorted(documented - artefacts.DEFINITION)}, which no reader "
        f"accepts")


# --------------------------------------------- what the live run found (61/62)


@check("the layer set is derived, and nothing instructs otherwise", finding="P39")
def _():
    """Items 31 and 61.

    Item 31 derived the layer set from content and updated the section that describes it. The
    *Do NOT* list eight sections below still said `every project needs all 4 layers`, and a live
    run followed the derivation and reported the contradiction in its own instructions.

    A check on the MECHANISM could not see this: the mechanism was right. What was wrong was a
    second instruction about it, in the same file, which the model reads with equal weight.
    """
    rel = os.path.join(SKILLS, "breakdown-plan-layers", "SKILL.md")
    text = open(rel, encoding="utf-8").read()
    flat = prose(text)

    # The derivation must still be instructed -- asserting only the absence of the contradiction
    # would pass on a file that had lost both halves.
    assert re.search(r"decide which layers exist at all", flat), (
        "plan-layers no longer tells the model to decide which layers exist, so item 31's "
        "derivation has no instruction behind it")
    assert re.search(r"A tier with no work in it is not a tier", flat), (
        "the rule that makes the derivation actionable is gone")

    # And nothing may require a fixed number of layers. Match the CLAIM rather than one
    # phrasing: any sentence pairing `every project` with a count of layers.
    #
    # This fires on a QUOTATION of the rescinded instruction too, and that is deliberate rather
    # than a false positive -- it caught exactly that on the commit that removed the line. A
    # skill is instructions to a model, which reads a quoted rule with the same weight as a
    # stated one; the history belongs in the plan and the ledger, where P39 and item 61 hold it.
    bad = [ln.strip() for ln in text.splitlines()
           if re.search(r"every project.*\b(all )?\d+ layers|needs all \d+ layers", ln, re.I)]
    assert not bad, (
        "an instruction requires a fixed number of layers, contradicting the derivation in the "
        "same file:\n    " + "\n    ".join(bad))

    # A dropped layer is named, never silent -- the half an operator needs. Asserted at BOTH
    # sites and scoped to each, because the first version of this was an `or` across the two:
    # deleting the rule from the derivation paragraph left the Do-NOT bullet matching, and the
    # mutant walked through. That is the `or across locations` failure this suite has a name for.
    region = flat.split("First, decide which layers exist at all", 1)
    assert len(region) == 2, "plan-layers no longer has its derivation paragraph"
    assert re.search(r"name the ones you dropped and why", region[1][:400]), (
        "the derivation paragraph no longer requires a dropped layer to be named, so a run that "
        "produces one task instead of four explains nothing to the operator")

    donot = flat.split("## Do NOT", 1)
    assert len(donot) == 2, "plan-layers has no Do NOT list"
    assert re.search(r"Drop a layer silently", donot[1]), (
        "the Do NOT list no longer forbids dropping a layer silently; the derivation paragraph "
        "asks for the reason and nothing forbids omitting it")


@check("the task schema admits every layer the layer graph can produce", finding="P40")
def _():
    """Items 28 and 62.

    `id` was `L[1-4]-[0-9]{3}` and `layer` an enum of four, while three fields ten lines below
    read `Required except in Layer 0`. Every Layer 0 task the toolchain has generated was invalid
    under its own schema, and item 28's per-project layer graph makes a fixed enum wrong for a
    second, independent reason.

    Asserted by RUNNING the documented pattern against the ids the toolchain actually writes.
    """
    spec = os.path.join(SKILLS, "breakdown", "references", "task-format-spec.md")
    text = open(spec, encoding="utf-8").read()

    m = re.search(r"`id`:\s*Must match pattern\s*`([^`]+)`", text)
    assert m, "task-format-spec.md documents no id pattern at all"
    pattern = m.group(1)

    # The ids this toolchain generates, including the ones its own Layer 0 templates use.
    for tid in ("L0-001", "L1-001", "L2-014", "L4-002", "L10-003"):
        assert re.fullmatch(pattern, tid), (
            f"the documented id pattern {pattern!r} rejects {tid}, which the toolchain writes. "
            f"A spec that forbids its own output is the defect P40 named")
    for bad in ("L1-1", "X1-001", "L1-0001"):
        assert not re.fullmatch(pattern, bad), (
            f"the documented id pattern {pattern!r} accepts {bad}, so it constrains nothing")

    # And `layer` is no longer a closed list of four. The five shipped names may be named as
    # DEFAULTS; what must not survive is an enum that item 28's per-project graph contradicts.
    row = [ln for ln in text.splitlines() if ln.strip().startswith("- `layer`")]
    assert row, "task-format-spec.md documents no `layer` constraint"
    assert not re.search(r"One of:", row[0]), (
        f"`layer` is still a closed enum: {row[0].strip()}. Item 28 lets a project declare its "
        f"own <layers> graph, instantiated per service with ids scoped to their block, and no "
        f"fixed list of four names can describe that")
    assert "0-setup" in row[0] or "0-setup" in text.split("- `layer`")[1][:400], (
        "the layer constraint never mentions 0-setup, which three fields below call out by name")


@check("the generator is told where its verification commands will run", finding="P42")
def _():
    """Item 64, first half.

    A live run wrote `pathlib.Path('.git').is_dir()` as a verification step. Inside a worktree
    `.git` is a FILE, so the step is false for the execution model the plugin itself uses -- and
    nothing in `breakdown-generate-tasks` said where its commands would run. Every
    environment-shaped assertion it invents was a guess.

    Two halves, and the second is what makes this more than a prose check: the stated facts are
    PARSED out of the brief, then MEASURED against a worktree built here by the toolchain's own
    `create-worktree.sh`. The brief must say it, and git must still do it -- a brief that drifts
    out of agreement with reality fails exactly as loudly as a brief that says nothing.
    """
    import shutil
    import stat
    import tempfile

    skill = os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md")
    text = open(skill, encoding="utf-8").read()

    parts = text.split("## Where your verification commands will run", 1)
    assert len(parts) == 2, (
        "breakdown-generate-tasks no longer states the execution context of its verification "
        "steps, so every environment-shaped assertion it writes is a guess again (P42)")
    region = parts[1].split("\n## ", 1)[0]

    block = re.search(r"```text\n(.*?)```", region, re.S)
    assert block, ("the execution context is no longer stated as a block anything can parse; "
                   "this check reads the facts rather than looking for words about them")
    facts, key = {}, None
    for line in block.group(1).splitlines():
        m = re.match(r"^(\S+)\s\s+(\S.*)$", line)
        if m:
            key, facts[key] = m.group(1), m.group(2)
        elif key and line.strip():
            facts[key] += " " + line.strip()

    for k in ("cwd", ".git", "branch", "tree", "siblings"):
        assert k in facts, (
            f"the execution context no longer states `{k}`. It states {sorted(facts)} -- and a "
            f"fact the generator is not given is one it invents")

    assert re.search(r"\bfile\b", facts[".git"], re.I) and \
        re.search(r"never a directory|not a directory", facts[".git"], re.I), (
        f"the brief no longer says `.git` is a file and not a directory: {facts['.git']!r}. "
        f"That single sentence is the whole of P42's concrete instance")
    assert "worktree-" in facts["branch"] and \
        re.search(r"never the base branch", facts["branch"], re.I), (
        f"the brief no longer says which branch a step runs on: {facts['branch']!r}")
    assert re.search(r"fresh|untracked|no build output", facts["tree"], re.I), (
        f"the brief no longer says the tree is a fresh checkout: {facts['tree']!r}")
    assert re.search(r"not visible|NOT visible|not present|never visible", facts["siblings"]), (
        f"the brief no longer says a sibling task's output is absent: {facts['siblings']!r}")

    if not (shutil.which("git") and shutil.which("sh")):
        return                      # nothing to measure with; the parsed half still applied

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    create = os.path.join(SKILLS, "execute-batch", "scripts", "create-worktree.sh")
    root = tempfile.mkdtemp(prefix="exec-context-check-")
    try:
        app, wt = os.path.join(root, "app"), os.path.join(root, "wt")
        os.makedirs(app)

        def g(*args, cwd=app):
            return subprocess.run(["git", "-C", cwd, *args], capture_output=True,
                                  text=True, timeout=60)

        # `trunk`, never `main` -- F1 is that assumption, and `branch` is a fact under test here.
        for args in (["init", "-q", "-b", "trunk", "."],
                     ["config", "user.email", "t@t.invalid"], ["config", "user.name", "T"]):
            g(*args)
        open(os.path.join(app, "README.md"), "w").write("base")
        g("add", "-A")
        g("commit", "-qm", "init")
        # An untracked leftover in the primary tree, for the `tree` fact.
        os.makedirs(os.path.join(app, "node_modules"))
        open(os.path.join(app, "node_modules", "left.txt"), "w").write("over")

        for tid in ("L1-001", "L1-002"):
            p = subprocess.run(["sh", create, app, tid, wt, "trunk"],
                               capture_output=True, text=True, timeout=60)
            assert p.returncode == 0, f"create-worktree.sh failed for {tid}: {p.stderr[-300:]}"
        d1, d2 = os.path.join(wt, "L1-001"), os.path.join(wt, "L1-002")

        gitlink = os.path.join(d1, ".git")
        assert os.path.isfile(gitlink) and not os.path.isdir(gitlink), (
            "git no longer represents a worktree's .git as a gitlink FILE. The brief in "
            "breakdown-generate-tasks now states something false, which is worse than stating "
            "nothing -- correct it there before relaxing this")

        cur = g("branch", "--show-current", cwd=d1).stdout.strip()
        assert cur == "worktree-L1-001" and cur != "trunk", (
            f"a task's worktree is on branch {cur!r}, not `worktree-L1-001`; the brief's `branch` "
            f"fact is now wrong and a step comparing against the base branch would pass")

        open(os.path.join(d2, "sibling.txt"), "w").write("mine")
        g("add", "-A", cwd=d2)
        g("commit", "-qm", "sibling work", cwd=d2)
        assert not os.path.exists(os.path.join(d1, "sibling.txt")), (
            "a sibling task's committed output is visible from another task's worktree; the "
            "brief's `siblings` fact is wrong and cross-task verification steps would work")

        assert not os.path.exists(os.path.join(d1, "node_modules")), (
            "an untracked directory from the primary tree appeared in the worktree; the brief's "
            "`tree` fact is wrong and `ls node_modules` would pass in the check but not the run")
    finally:
        rmtree(root)


@check("an environment-shaped verification step is a review question", finding="P42")
def _():
    """Item 64, second half -- the durable one.

    The measured facts can go out of date. *Prefer a claim about the artefact over a claim about
    the environment* cannot, because it is about what a verification step is for. It has to hold
    in both places: the generator's brief, where the step is written, and `review-criteria.md`,
    where it is judged -- and in the CRITICAL section there, because a step that cannot pass is
    exactly what P41's run edited a task to get past.
    """
    gen = open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
               encoding="utf-8").read()
    parts = gen.split("### Assert the artefact, not the environment", 1)
    assert len(parts) == 2, (
        "the generator no longer prefers artefact assertions to environment assertions; the "
        "five facts alone are a list that goes stale, which is the half item 64 called durable")
    # Unescaped pipes only: one `over` cell is a pipeline, `git log --oneline \| wc -l`.
    rows = [[c.strip() for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))]
            for ln in parts[1].split("\n## ", 1)[0].splitlines()
            if ln.strip().startswith("|") and not re.match(r"^\|[\s|:-]+\|$", ln.strip())]
    rows = [r for r in rows if len(r) == 3 and r[0].lower() != "prefer"]
    assert len(rows) >= 3, f"the prefer/over table has {len(rows)} row(s) of guidance, not 3+"
    for prefer, over, why in rows:
        assert "`" in prefer and "`" in over and why, (
            f"a prefer/over row names no runnable pair or gives no reason: {[prefer, over, why]}")
    assert any(".git" in over for _p, over, _w in rows), (
        "the table no longer contains the assertion a live run actually wrote (`.git`), so the "
        "one worked example P42 produced has been generalised away")

    rc = open(os.path.join(SKILLS, "breakdown", "references", "review-criteria.md"),
              encoding="utf-8").read()
    critical = rc.split("## Critical Criteria", 1)
    assert len(critical) == 2, "review-criteria.md has no Critical Criteria section"
    critical = critical[1].split("## Warning Criteria", 1)[0]
    assert "### 6. Verification Steps" in critical, (
        "verification steps are no longer reviewed as a CRITICAL criterion; a step that cannot "
        "pass is what P41's run rewrote a task file to get past")
    sec6 = critical.split("### 6. Verification Steps", 1)[1].split("\n### ", 1)[0]
    bullets = [prose(b) for b in re.split(r"\n- \[ \] ", sec6)[1:]]

    assert any(re.search(r"worktree", b) and re.search(r"\.git", b) for b in bullets), (
        "no critical criterion asks whether a step holds inside a worktree, which is where "
        "/execute runs every one of them (P42)")
    assert any(re.search(r"artefact|artifact", b) and re.search(r"environment|execution model", b)
               for b in bullets), (
        "no critical criterion prefers an assertion about the task's own output to one about "
        "the environment, so the reviewer can only catch the examples, never the class")

    table = rc.split("### Environment-Shaped Verification Steps", 1)
    assert len(table) == 2, "review-criteria.md lists no environment-shaped patterns to flag"
    fence = re.search(r"```\n(.*?)```", table[1], re.S)
    assert fence, "the environment-shaped patterns are no longer in a block that can be read"
    pairs = [ln.split("→") for ln in fence.group(1).splitlines() if "→" in ln]
    assert len(pairs) >= 4, f"only {len(pairs)} pattern(s) are given a re-aimed replacement"
    for bad, good in pairs:
        assert bad.strip() and good.strip(), f"a pattern row has an empty half: {bad!r} {good!r}"
    assert any(".git" in bad for bad, _g in pairs), (
        "the one pattern a live run actually produced is no longer listed")


@check("a task file edited mid-run is a stop with a diff -- by running it", finding="P41")
def _():
    """Item 63, the guard.

    The third live crossing met a Layer 0 task whose `<verification>` block was unsatisfiable, and
    the run edited the task file and carried on to `14/14`. Nothing forbade it; nothing recorded
    it. Prose here is the guard a model can reason past -- item 4.13 -- so this is a script with
    an exit code, and this check RUNS it: record, edit, verify, and read what it wrote.

    The last assertion is the one to keep. The edit record must not disturb `ledger-status.sh`,
    because that is what a resume is derived from: an entry without a commit would read there as a
    task whose commit had vanished, and the guard against a false green would have manufactured a
    false red.
    """
    import shutil
    import stat
    import tempfile

    script = os.path.join(SKILLS, "execute", "scripts", "task-integrity.py")
    assert os.path.isfile(script), "skills/execute/scripts/task-integrity.py is missing"

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    root = tempfile.mkdtemp(prefix="task-integrity-check-")
    try:
        tasks = os.path.join(root, "tasks", "0-setup")
        app = os.path.join(root, "app")
        os.makedirs(tasks)
        os.makedirs(app)
        tp, one, two = os.path.join(root, "tasks"), None, None

        def task(tid, step):
            path = os.path.join(tasks, f"{tid}-thing.xml")
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"<task><meta><id>{tid}</id></meta>"
                        f"<verification><step>{step}</step></verification></task>\n")
            return path

        one = task("L0-001", "Run: pytest -q")
        two = task("L0-002", "Run: ruff check .")

        def run(*args):
            p = subprocess.run([sys.executable, script, *args], capture_output=True,
                               text=True, timeout=120)
            return p.returncode, p.stdout or "", p.stderr or ""

        # Nothing recorded is NOT `unchanged`, and must never be reported as one.
        rc, out, err = run("verify", tp, app, "demo")
        assert rc == 2, f"verify with no record exited {rc}, not 2:\n{out}{err}"
        assert "UNCHANGED" not in out.upper(), (
            "verify with nothing recorded reported the task files unchanged. An unmade check "
            "reported as a passing one is the false green this whole guard exists to prevent")

        rc, out, _ = run("record", tp, app, "demo")
        assert rc == 0 and "RECORDED 2" in out, f"record exited {rc}: {out}"

        rc, out, _ = run("verify", tp, app, "demo")
        assert rc == 0 and "UNCHANGED 2" in out, f"clean verify exited {rc}: {out}"

        # Now the P41 edit: one verification step rewritten to something satisfiable.
        with open(one, "w", encoding="utf-8", newline="\n") as f:
            f.write("<task><meta><id>L0-001</id></meta>"
                    "<verification><step>Run: pytest -q -k not_the_broken_one</step>"
                    "</verification></task>\n")
        rc, out, err = run("verify", tp, app, "demo")
        assert rc == 1, f"an edited task file exited {rc}, not 1 -- the guard did not fire"
        assert "not_the_broken_one" in out and out.lstrip().startswith("---"), (
            "the edit is reported without a diff of what changed. A summary of an edit to an "
            f"acceptance criterion is not the evidence:\n{out[:400]}")
        assert "L0-001" in err, f"the stop does not name the task:\n{err[:300]}"

        # The record: an edit leaves a trace, which is the third part of item 63.
        edits = os.path.join(app, ".execute", "demo", "task-edits.jsonl")
        assert os.path.isfile(edits), (
            "nothing recorded the edit. The ledger indexes commits, so without this the next "
            "14/14 is unauditable in exactly the way P41's was")
        entry = json.loads(open(edits, encoding="utf-8").read().splitlines()[0])
        for field in ("task_id", "kind", "sha_before", "sha_after", "diff"):
            assert entry.get(field), f"the edit record has no {field}: {entry}"
        assert entry["sha_before"] != entry["sha_after"], "the record's two hashes are equal"
        assert os.path.isfile(os.path.join(app, ".execute", "demo", entry["diff"])), (
            f"the record points at a diff that was never written: {entry['diff']}")
        assert open(os.path.join(app, ".execute", ".gitignore"),
                    encoding="utf-8").read().strip() == "*", (
            "the record is not self-ignoring, so a run's own bookkeeping shows up in the "
            "project's `git status` -- record-task.sh writes this marker for the same reason")

        # A removed task and an appeared task are both edits.
        os.remove(two)
        task("L0-003", "Run: true")
        rc, _out, err = run("verify", tp, app, "demo")
        assert rc == 1 and "removed" in err and "added" in err, (
            f"a removed and an added task file were not both reported:\n{err[:400]}")

        # And none of it may disturb the ledger a resume is derived from.
        if shutil.which("git") and shutil.which("sh"):
            def g(*args):
                return subprocess.run(["git", "-C", app, *args], capture_output=True,
                                      text=True, timeout=60)
            for args in (["init", "-q", "-b", "trunk", "."],
                         ["config", "user.email", "t@t.invalid"], ["config", "user.name", "T"]):
                g(*args)
            open(os.path.join(app, "README.md"), "w").write("x")
            g("add", "-A")
            g("commit", "-qm", "init")
            sha = g("rev-parse", "HEAD").stdout.strip()
            rec = os.path.join(SKILLS, "execute-merge", "scripts", "record-task.sh")
            subprocess.run(["sh", rec, app, "demo", "L0-001", sha], capture_output=True,
                           text=True, timeout=60)
            status = os.path.join(SKILLS, "execute", "scripts", "ledger-status.sh")
            before = subprocess.run(["sh", status, app, "demo", "3"], capture_output=True,
                                    text=True, timeout=60).stdout
            run("verify", tp, app, "demo")           # writes more edit records
            after = subprocess.run(["sh", status, app, "demo", "3"], capture_output=True,
                                   text=True, timeout=60).stdout
            assert json.loads(before) == json.loads(after), (
                "recording a task edit changed what ledger-status.sh reports. The edit record "
                "must live beside the ledger and not in it: an entry with no commit reads there "
                f"as a task whose commit has vanished.\nbefore {before}\nafter  {after}")
    finally:
        rmtree(root)


@check("the guard runs before dispatch and again before anything merges", finding="P41")
def _():
    """Item 63, the wiring.

    A guard nothing calls is a script, not a guard -- and both stamps in the manifest were
    written for four months before anything read either of them (P28). So this asserts the calls
    themselves, in the two skills that must make them, and the mode each one passes.
    """
    def invocations(path):
        text = open(path, encoding="utf-8").read()
        return [re.sub(r"\s+", " ", m.group(0)).strip()
                for m in re.finditer(r"task-integrity\.py[^\n`]*", text)]

    ex = os.path.join(SKILLS, "execute", "SKILL.md")
    text = open(ex, encoding="utf-8").read()
    calls = invocations(ex)
    modes = [c.split()[1] for c in calls if len(c.split()) > 1]
    assert "record" in modes, (
        "/execute never records the task files, so there is nothing to compare them against "
        "and the guard cannot fire at all")
    assert "verify" in modes, "/execute never re-checks the task files before it reports"
    for call in calls:
        if call.split()[1:2] in (["record"], ["verify"]):
            assert "{tasks_path}" in call and "{project_path}" in call and "{prd_slug}" in call, (
                f"an invocation cannot address the run it belongs to: {call}")

    # Order: the record is taken before any layer is dispatched, and re-checked after.
    rec_at = text.index("task-integrity.py record")
    dispatch_at = text.index("### Step 6: Execute Layers")
    ver_at = text.rindex("task-integrity.py verify")
    assert rec_at < dispatch_at < ver_at, (
        "the snapshot is not taken before dispatch and re-checked after it; a hash taken after "
        "the run cannot say what the run was given")

    # And the two outcomes are reported as their own stop kinds, not folded into `abandoned`.
    # Named in the table AND given a report of their own, each assertion scoped to its own
    # region: `task_edited` appears in three places in this file, so `kind in text` was an `or`
    # across locations and a mutant that removed the report section walked through it.
    step8 = text.split("### Step 8: Handle Stop Condition", 1)
    assert len(step8) == 2, "/execute no longer handles stop conditions at all"
    step8 = step8[1].split("### Step 9", 1)[0]
    named = {ln.strip().strip("|").split("|")[0].strip().strip("`")
             for ln in step8.splitlines() if ln.strip().startswith("| `")}
    for kind in ("abandoned", "usage_limit", "task_defect", "task_edited"):
        assert kind in named, (
            f"the stop-kind table does not name `{kind}`: {sorted(named)}. Four outcomes ask "
            f"four different things of the operator, and a table missing one folds it into "
            f"`abandoned`, which sends them to debug code that never failed")
    for kind in ("task_defect", "task_edited"):
        section = re.search(r'#### `stop_reason_kind: "%s"`(.*?)(?=\n#### |\Z)' % kind,
                            step8, re.S)
        assert section, (
            f"`{kind}` is named in the table and never reported. The table says the kinds "
            f"differ; only the report shows the operator what to do about this one")
        assert "STOPPED:" in section.group(1), (
            f"`{kind}`'s section shows no report block, so what the operator sees is left to "
            f"the model that stopped -- which is where P41's run wrote its own account")
    assert re.search(r"exit code 2|Exit 2|`NO RECORD`", text), (
        "/execute does not say what to do when nothing was recorded -- the case where the check "
        "silently becomes a claim nobody made")

    layer = os.path.join(SKILLS, "execute-layer", "SKILL.md")
    ltext = open(layer, encoding="utf-8").read()
    lcalls = invocations(layer)
    assert any(c.split()[1:2] == ["verify"] for c in lcalls), (
        "execute-layer never re-checks the task files, so an edit is caught only after every "
        "batch of the run has merged against it")
    merge_at = ltext.index("/execute-merge --task-id")
    check_at = ltext.index("task-integrity.py verify")
    assert check_at < merge_at, (
        "the task files are checked after the merge invocation rather than before it. Merging "
        "work verified against a rewritten task launders the edit into the ledger as a commit")


@check("an unsatisfiable task is reported, and reporting it has somewhere to go", finding="P41")
def _():
    """Item 63, the escalation path -- and the half that makes the guard bearable.

    A rule that leaves the operator stuck is a rule that gets removed, so the ban on editing a
    task file is only half of this item. The other half is that `blocked` has a shape, survives
    the batch without being retried, and reaches `/execute` as its own stop kind.

    Asserted by PARSING the documented JSON rather than by looking for words about it.
    """
    def blocks(path):
        text = open(path, encoding="utf-8").read()
        out = []
        for m in re.finditer(r"```json\n(.*?)```", text, re.S):
            body = re.sub(r"^\s*RESULT:\s*", "", m.group(1))
            try:
                out.append(json.loads(body))
            except ValueError:
                pass
        return out

    agent = os.path.join(AGENTS, "task-implementer.md")
    atext = open(agent, encoding="utf-8").read()
    assert re.search(r"task file[^.]{0,80}read-only|not (modify|edit) the task file",
                     prose(atext), re.I), (
        "the implementer is not told the task file is read-only, which is the one sentence "
        "item 63 is: an implementer and an orchestrator may not modify a task file")

    blocked = [b for b in blocks(agent) if b.get("status") == "blocked"]
    assert blocked, ("the implementer has no documented `blocked` result, so an agent that "
                     "diagnoses an unsatisfiable task has nothing to return but a failure")
    blocker = blocked[0].get("blocker") or {}
    for field in ("kind", "step", "contradicts"):
        assert blocker.get(field), (
            f"the blocker carries no `{field}`: {blocker}. The operator fixes this in "
            f"/breakdown, and both halves of the contradiction have to be quoted or they cannot")
    assert blocked[0].get("commit_hash") is None, (
        "a blocked task documents a commit; nothing was implemented, so there is nothing to merge")

    ver = open(os.path.join(SKILLS, "execute-verify", "SKILL.md"), encoding="utf-8").read()
    assert re.search(r"never modify the task file|not modify the task file", ver, re.I), (
        "the verifier may still edit the task file it is verifying against -- which is the "
        "wrong independence exactly: independent of the implementer, not of the criteria")
    assert re.search(r'"kind":\s*"task-defect"', ver), (
        "the verifier has no way to report a step no implementation could pass, so its only "
        "vocabulary for an unsatisfiable task is `failed`, which buys five retries of it")

    btext = open(os.path.join(SKILLS, "execute-batch", "SKILL.md"), encoding="utf-8").read()
    stops = [b for b in blocks(os.path.join(SKILLS, "execute-batch", "SKILL.md"))
             if b.get("stop_reason_kind") == "task_defect"]
    assert stops, "execute-batch never returns a `task_defect` stop, so a blocked task is lost"
    assert stops[0].get("defect_task") and stops[0]["defect_task"] not in (
        stops[0].get("failed", []) + stops[0].get("abandoned", [])), (
        "the defective task is reported as failed or abandoned. It failed nothing and spent no "
        "attempt; naming it either way sends the operator to debug the implementation")
    # Scoped to the step that owns the claim. Searched across the whole file this passed on the
    # usage-limit step's `Do not increment the task's attempt count`, four sections away -- the
    # `or across locations` failure again, and the mutant that deleted the sentence survived.
    step7b = btext.split("### Step 7b", 1)
    assert len(step7b) == 2, (
        "execute-batch has no step for a `blocked` result, so an unsatisfiable task rejoins the "
        "retry queue as an ordinary failure")
    step7b = prose(step7b[1].split("\n### ", 1)[0])
    assert re.search(r"(do not|never)[^.]{0,80}(queue a retry|retry)", step7b, re.I), (
        "a blocked task can still be retried. Five attempts against a task no implementation "
        "can satisfy is five guaranteed failures and an `abandoned` report naming the wrong thing")
    assert re.search(r"(do not|never)[^.]{0,80}increment", step7b, re.I), (
        "a blocked task still spends an attempt, so a task nobody could implement burns the "
        "budget a resume needs -- the same waste item 4.14 removed for the usage limit")

    ltext = open(os.path.join(SKILLS, "execute-layer", "SKILL.md"), encoding="utf-8").read()
    row = [ln for ln in ltext.splitlines() if ln.startswith("| `task_defect`")]
    assert row, "execute-layer does not carry `task_defect` through to the orchestrator"
    assert re.search(r"breakdown", row[0]), (
        f"the layer does not say whose defect a `task_defect` is: {row[0].strip()}")


def _edge_xml(edges):
    return "".join(
        '    <source-feature slug="%s" moscow="%s" satisfies-criteria="%s" '
        'requirement-level="%s"/>\n' % e for e in edges)


def _multi_task_xml(tid, edges, groups=None):
    """A task in item 65's shape: one <source-feature> per feature, criteria grouped by feature."""
    ctx = ""
    if groups:
        body = ""
        for slug, crits in groups:
            inner = "".join(
                '      <criterion id="%s" pattern="event-driven" priority="P0">\n'
                '      %s criterion %s.\n      </criterion>\n' % (c, slug, c) for c in crits)
            body += '    <from-feature slug="%s">\n%s    </from-feature>\n' % (slug, inner)
        ctx = "  <context>\n    <acceptance-criteria>\n%s    </acceptance-criteria>\n" \
              "  </context>\n" % body
    return ("<task>\n  <meta>\n    <id>%s</id>\n    <name>Probe %s</name>\n"
            "    <layer>4-integration</layer>\n    <priority>1</priority>\n%s  </meta>\n%s"
            "</task>\n" % (tid, tid, _edge_xml(edges), ctx))


@check("a task names every feature it descends from, and the manifest carries all of them",
       finding="P43")
def _():
    """Item 65, the producer half -- asserted by RUNNING build-manifest.py.

    `<source-feature>` held one slug, so a task covering several had to lie about which. Three
    live runs met the case and invented three workarounds; the worst narrowed the attribution to
    one feature silently, and nothing caught it because item 30's coverage passes when the other
    criteria are covered by other tasks. What was lost is that every consumer then believes the
    task belongs to one feature.

    The compatibility rule is asserted here too, and it is the interesting half: the singular
    `source_feature` key is written ONLY for a single-feature task. A 1.2 reader then sees a
    multi-feature task as unattributed rather than attributed to whichever edge came first --
    P43's silent misattribution reintroduced by the shim meant to preserve it.
    """
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="item65-manifest-")
    try:
        layer = os.path.join(root, "4-integration")
        os.makedirs(layer)
        # The integration task run 3 met: three features, one task, criterion ids that collide.
        open(os.path.join(layer, "L4-002-probe.xml"), "w", encoding="utf-8",
             newline="\n").write(_multi_task_xml(
                 "L4-002",
                 # WEAKEST FIRST, deliberately. With the strongest edge first, "the strongest of
                 # the edges" and "the first edge" give the same answer, and the assertion below
                 # holds for a manifest that simply takes whichever came first -- a mutant that
                 # did exactly that walked through this check.
                 [("list-links", "could-have", "2", "P2"),
                  ("save-link", "must-have", "1", "P0"),
                  ("tag-links", "should-have", "1,3", "P1")],
                 [("list-links", ["2"]), ("save-link", ["1"]), ("tag-links", ["1", "3"])]))
        # And one task in the shape every task file written before item 65 carries.
        open(os.path.join(layer, "L4-003-probe.xml"), "w", encoding="utf-8",
             newline="\n").write(_task_xml("L4-003", slug="save-link", crits="4",
                                           moscow="should-have", level="P1"))

        builder = os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py")
        p = subprocess.run([sys.executable, builder, root], capture_output=True, text=True)
        assert p.returncode == 0, f"build-manifest.py failed: {p.stdout}\n{p.stderr}"
        man = json.load(open(os.path.join(root, "manifest.json"), encoding="utf-8"))
        inv = {e["id"]: e for e in man["task_inventory"]}

        assert man["schema_version"] >= "1.3", (
            f"the manifest shape changed and its version did not: {man['schema_version']}. "
            f"check-compatibility.py is the reader that decides whether a manifest can be read "
            f"at all, and it decides on this field")

        multi = inv["L4-002"]
        edges = multi.get("source_features")
        assert edges and [e["slug"] for e in edges] == ["list-links", "save-link", "tag-links"], (
            f"the manifest carries {edges!r} for a task that names three features. A task walking "
            f"three and recorded as one is P43, and every consumer downstream believes it")
        by_slug = {e["slug"]: e for e in edges}
        assert by_slug["tag-links"]["satisfies_criteria"] == ["1", "3"], (
            f"criteria are not scoped to their own feature: {by_slug['tag-links']}. Ids repeat "
            f"across features, so an unscoped list cites criterion 1 of whichever it likes")
        assert by_slug["save-link"]["satisfies_criteria"] == ["1"], by_slug["save-link"]

        assert "source_feature" not in multi, (
            "the manifest names ONE source_feature for a task that descends from three. A 1.2 "
            "reader must see this task as unattributed rather than attributed to the first edge "
            "-- writing the singular key here reintroduces P43 inside the compatibility shim")
        assert multi.get("moscow") == "must-have" and multi.get("requirement_level") == "P0", (
            f"the effective tier is {multi.get('moscow')}/{multi.get('requirement_level')}, not "
            f"the strongest of the three edges. A task is built or not built as a unit, so a "
            f"filter must see the strongest obligation it carries")

        old = inv["L4-003"]
        assert old.get("source_feature") == "save-link" and old.get("satisfies_criteria") == ["4"], (
            f"a task in the pre-item-65 shape no longer reads: {old}. The old shape is accepted "
            f"on read and never written -- a reader that refuses it strands every task set "
            f"generated before today")
        assert [e["slug"] for e in old["source_features"]] == ["save-link"], old["source_features"]

        summary = open(os.path.join(root, "tasks-summary.md"), encoding="utf-8").read()
        row = [ln for ln in summary.splitlines() if ln.startswith("| `L4-002`")]
        assert row and all(s in row[0] for s in ("save-link", "tag-links", "list-links")), (
            f"tasks-summary.md shows {row[0] if row else 'no row'} -- a reviewer reading one slug "
            f"for a task that walks three is exactly the reader item 32 built this view for")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("coverage and scope attribute a task to every feature it names -- by running them",
       finding="P43")
def _():
    """Item 65, the consumer half.

    The tempting cheap fix for P43 was to let `check-coverage.py` accept a criterion cited by a
    task from another feature. That makes the report pass and leaves the task set exactly as
    unattributable as it was -- P2's mistake with the arrow reversed, a consumer weakened to
    match an under-specified producer. So the producer carries the edges and these two read them.

    Both directions are asserted: the honest multi-feature task covers all three features, and
    the narrowed one -- run 3's silent workaround -- is reported as a shortfall naming the two
    features it dropped.
    """
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="item65-coverage-")
    try:
        prd = os.path.join(root, "prd")
        feat = os.path.join(prd, "features")
        os.makedirs(feat)
        slugs = [("save-link", "must-have"), ("tag-links", "should-have"),
                 ("list-links", "should-have")]
        # An index entry has a body -- `select-features.py` reads the name out of it, and a
        # self-closing tag matches its pattern not at all, which reads as "names no features".
        entries = "".join(
            '  <feature priority="%s" file="features/%s.md">\n    <name>%s</name>\n'
            '  </feature>\n' % (tier, slug, slug)
            for slug, tier in slugs)
        open(os.path.join(prd, "index.md"), "w", encoding="utf-8", newline="\n").write(
            "<prd>\n<meta><slug>probe</slug></meta>\n<features>\n%s</features>\n</prd>\n" % entries)
        for slug, _tier in slugs:
            open(os.path.join(feat, slug + ".md"), "w", encoding="utf-8", newline="\n").write(
                '<feature>\n<meta><slug>%s</slug><definition>defined</definition></meta>\n'
                '<acceptance-criteria>\n'
                '<criterion id="1" pattern="event-driven" priority="P0">%s one.</criterion>\n'
                '<criterion id="2" pattern="event-driven" priority="P0">%s two.</criterion>\n'
                '</acceptance-criteria>\n</feature>\n' % (slug, slug, slug))

        def build(tasks_dir, edges):
            layer = os.path.join(tasks_dir, "4-integration")
            os.makedirs(layer, exist_ok=True)
            open(os.path.join(layer, "L4-001-probe.xml"), "w", encoding="utf-8",
                 newline="\n").write(_multi_task_xml("L4-001", edges))
            p = subprocess.run([sys.executable,
                                os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py"),
                                tasks_dir], capture_output=True, text=True)
            assert p.returncode == 0, p.stdout + p.stderr
            return tasks_dir

        cov = os.path.join(SKILLS, "breakdown", "scripts", "check-coverage.py")
        every = [(s, t, "1,2", "P0") for s, t in slugs]

        honest = build(os.path.join(root, "honest"), every)
        p = subprocess.run([sys.executable, cov, prd, honest, "--json"],
                           capture_output=True, text=True)
        out = json.loads(p.stdout)
        assert out["uncovered_features"] == [] and out["uncovered_criteria"] == [], (
            f"one task naming three features did not cover them: {p.stdout}\n{p.stderr}")
        assert out["attributed_tasks"] == 1, out["attributed_tasks"]

        # Run 3's workaround: the same task, narrowed to the feature it resembles most.
        narrow = build(os.path.join(root, "narrow"), [("tag-links", "should-have", "1,2", "P0")])
        p = subprocess.run([sys.executable, cov, prd, narrow, "--json"],
                           capture_output=True, text=True)
        out = json.loads(p.stdout)
        assert sorted(f["slug"] for f in out["uncovered_features"]) == ["list-links", "save-link"], (
            f"narrowing a three-feature task to one was not reported: {p.stdout}. This is the "
            f"whole of P43 -- the narrowing is silent unless attribution decides coverage")
        # And the criteria are scoped to the feature that declared them. The tempting cheap fix
        # for P43 was to let a criterion cited by ANY task count for every feature with that id;
        # every feature here has ids 1 and 2, so that version reports full criterion coverage
        # for a task that touches one of the three. The plan names this explicitly: a consumer
        # weakened to match an under-specified producer is P2's mistake with the arrow reversed.
        assert {(c["feature"], c["id"]) for c in out["uncovered_criteria"]} >= {
            ("save-link", "1"), ("save-link", "2"),
            ("list-links", "1"), ("list-links", "2")}, (
            f"criterion ids are pooled across features, so citing `tag-links` 1 and 2 covered "
            f"every feature's 1 and 2: {out['uncovered_criteria']}")

        # And the cross-check counts the task under every feature, not just the first.
        # The cross-check compares a per-feature prediction against the tasks attributed to that
        # feature. `list-links` is predicted `large` and is reachable ONLY through the multi-edge
        # task, so the disagreement below can be reported only if the task counted under it --
        # before item 65 that task belonged to whichever feature it named, and `list-links` had
        # no tasks to compare against at all.
        open(os.path.join(honest, "analysis.json"), "w", encoding="utf-8", newline="\n").write(
            json.dumps({"scope": "small", "confidence": "high", "feature_signals": [
                {"feature": "list-links", "scope": "large", "confidence": "high"}]}))
        p = subprocess.run([sys.executable,
                            os.path.join(SKILLS, "breakdown", "scripts", "check-scope.py"),
                            honest], capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        out = p.stdout + p.stderr
        assert re.search(r"list-links was analysed as large", out), (
            f"check-scope.py did not compare `list-links`, which the only task in the set names "
            f"as its third feature. A task counted under one of the three leaves the other two "
            f"with nothing to compare, and the cross-check reports nothing while looking "
            f"identical to agreement:\n{out}")
        assert "name no source feature" not in out, (
            f"the one task in this set is reported as unattributed:\n{out}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the wont-have refusal and the gate read the per-edge shape -- by running them",
       finding="P43")
def _():
    """Item 65's two raw-text readers, which parse task files without an XML parser.

    Both were written against `<moscow>wont-have</moscow>` and `<source-feature>slug</...>` as
    literal strings. A guard that silently stops matching is worse than one that was never
    written: item 20's refusal is defence in depth, and defence in depth that no longer fires
    reports a clean preflight on the exact task set it exists to stop.
    """
    import importlib.util
    import shutil
    import tempfile

    spec = importlib.util.spec_from_file_location(
        "check_gate", os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py"))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    root = tempfile.mkdtemp(prefix="item65-guards-")
    try:
        layer = os.path.join(root, "tasks", "4-integration")
        os.makedirs(layer)
        open(os.path.join(layer, "L4-001-probe.xml"), "w", encoding="utf-8",
             newline="\n").write(_multi_task_xml(
                 "L4-001", [("save-link", "must-have", "1", "P0"),
                            ("tag-links", "should-have", "1", "P1")]))
        open(os.path.join(layer, "L4-002-probe.xml"), "w", encoding="utf-8",
             newline="\n").write(_task_xml("L4-002", slug="list-links"))

        built = gate.built_features(os.path.join(root, "tasks"))
        assert built == {"save-link", "tag-links", "list-links"}, (
            f"the gate sees {sorted(built)} of three features. It scopes the significance "
            f"assertion to what was BUILT, so a slug it cannot parse is a feature whose stale "
            f"decision record stops being reported")

        if not (shutil.which("git") and shutil.which("sh")):
            return
        app = os.path.join(root, "app")
        os.makedirs(app)
        for args in (["init", "-q", "-b", "trunk", "."],
                     ["config", "user.email", "t@t.invalid"], ["config", "user.name", "T"]):
            subprocess.run(["git", "-C", app, *args], capture_output=True, text=True)
        open(os.path.join(app, "README.md"), "w").write("x")
        subprocess.run(["git", "-C", app, "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", app, "commit", "-qm", "init"], capture_output=True)
        tasks = os.path.join(root, "tasks")
        for name, body in (("manifest.json", '{"tasks": []}'), ("layer_plan.json", '{"layers": []}')):
            open(os.path.join(tasks, name), "w", encoding="utf-8", newline="\n").write(body)

        flight = os.path.join(SKILLS, "execute", "scripts", "preflight.sh")
        clean = subprocess.run(["sh", flight, tasks, app], capture_output=True, text=True,
                               timeout=120)
        assert clean.returncode == 0, (
            f"preflight refused a clean tree, so the refusal below would prove nothing: "
            f"{clean.stderr}")

        # A wont-have edge on a task whose OTHER edge is must-have. The effective tier is
        # must-have, so a refusal reading the effective tier would let this through -- and the
        # refusal is about whether the task should exist, not how important it is.
        open(os.path.join(layer, "L4-003-probe.xml"), "w", encoding="utf-8",
             newline="\n").write(_multi_task_xml(
                 "L4-003", [("save-link", "must-have", "1", "P0"),
                            ("rejected", "wont-have", "1", "P0")]))
        p = subprocess.run(["sh", flight, tasks, app], capture_output=True, text=True, timeout=120)
        assert p.returncode == 1 and "L4-003" in p.stderr, (
            f"preflight did not refuse a task carrying moscow=\"wont-have\" as an edge "
            f"(exit {p.returncode}):\n{p.stderr}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("the schema, the generator and the reviewer all say a task may name several features",
       finding="P43")
def _():
    """Item 65's instruction half -- and it is three files because the shape has three owners.

    The generator writes the element, the spec defines it, and `review-criteria.md` is what
    fails a task that narrows. A rule stated in one of the three is a rule two of them contradict.
    """
    spec = open(os.path.join(SKILLS, "breakdown", "references", "task-format-spec.md"),
                encoding="utf-8").read()
    gen = open(os.path.join(SKILLS, "breakdown-generate-tasks", "SKILL.md"),
               encoding="utf-8").read()
    rev = open(os.path.join(SKILLS, "breakdown", "references", "review-criteria.md"),
               encoding="utf-8").read()

    # The spec's example is parsed, not read: several edges, each with its own criteria.
    edges = re.findall(r"<source-feature\b([^>]*)/>", spec)
    multi = [e for e in edges if 'slug="tag-links"' in e]
    assert len(edges) >= 3 and multi, (
        "the spec never shows a task descending from more than one feature, so the shape it "
        "defines has no worked example of the case it exists for")
    assert all(re.search(r'satisfies-criteria="[^"]+"', e) for e in edges), (
        f"an example edge carries no criteria of its own: {edges}. Per-feature ids are the "
        f"point -- `1` means a different requirement in each feature")

    # The old shape is read and never written -- item 45's rule, and the reason a corpus survives.
    #
    # BOTH halves, in ONE paragraph, inside the section that owns the claim. The first version of
    # this was an alternation over the whole file, and it matched the second sentence of the very
    # paragraph a mutant had gutted: `still accepted by every reader` survived while the promise
    # it belonged to did not. Two halves matched separately are two claims, not one rule.
    region = spec.split("#### A task names every feature it descends from", 1)
    assert len(region) == 2, "the spec has no section for item 65's shape"
    paras = [prose(p) for p in region[1].split("\n### ", 1)[0].split("\n\n")]
    assert any(re.search(r"accepted|read", p, re.I) and re.search(r"never written|not written", p,
                                                                 re.I) for p in paras), (
        "the spec does not promise, in one place, that the pre-item-65 shape is still read and "
        "no longer written. A reader that refuses it strands every task set generated before "
        "today; a generator that keeps writing it strands the readers of the new one")

    # The grouping rule, in the two files that must agree about it.
    for name, text in (("task-format-spec.md", spec), ("breakdown-generate-tasks", gen),
                       ("review-criteria.md", rev)):
        assert "from-feature" in text, (
            f"{name} does not mention <from-feature>, so criterion ids from two features are "
            f"carried into one task with nothing saying which is which")
    assert re.search(r"more than one .{0,40}source-feature", prose(rev), re.I), (
        "review-criteria.md does not scope the grouping requirement to multi-feature tasks, so "
        "it either demands a wrapper on every task or asks for nothing")
    assert re.search(r"never narrow|not narrow|every feature (the task|it) (actually )?covers",
                     prose(gen), re.I), (
        "the generator is not told to name every feature the task covers. Narrowing to the "
        "closest one is what run 3 did, and it is silent")


@check("the layer set is the plan's, not a list in /execute's prose -- by running it",
       finding="P44")
def _():
    """Item 66.

    `/execute` Step 6 iterated a hardcoded five-name list while item 31 derived the set from the
    document, item 62 made the schema admit any layer id, and item 28 let a project declare its
    own graph instantiated per service. The producer derived and the consumer recited, and the
    failure is silent and total: against a project whose layers are named anything else, the loop
    finds no tasks under any of its five names and reports a COMPLETED RUN OF ZERO TASKS.

    Asserted by running the script on a project whose layers no hardcoded list could contain.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "execute", "scripts", "resolve-layers.py")
    assert os.path.isfile(script), "skills/execute/scripts/resolve-layers.py is missing"

    root = tempfile.mkdtemp(prefix="item66-layers-")
    try:
        def tasks_dir(name, layers, files):
            """A tasks tree with a layer_plan and a manifest BUILT from the files on disk."""
            d = os.path.join(root, name)
            for layer, tids in files:
                os.makedirs(os.path.join(d, layer), exist_ok=True)
                for tid in tids:
                    open(os.path.join(d, layer, "%s-x.xml" % tid), "w", encoding="utf-8",
                         newline="\n").write(
                        "<task><meta><id>%s</id><name>N</name><layer>%s</layer>"
                        "<priority>1</priority></meta></task>\n" % (tid, layer))
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "layer_plan.json"), "w", encoding="utf-8", newline="\n").write(
                json.dumps({"layers": [{"id": lid, "name": lid, "tasks": []} for lid in layers]}))
            p = subprocess.run([sys.executable,
                                os.path.join(SKILLS, "breakdown", "scripts", "build-manifest.py"),
                                d], capture_output=True, text=True)
            assert p.returncode == 0, p.stdout + p.stderr
            return d

        def run(d, *args):
            p = subprocess.run([sys.executable, script, d, *args], capture_output=True, text=True)
            return p.returncode, (p.stdout or ""), (p.stderr or "")

        # A project that declared its own graph (item 28), instantiated per service. No fixed
        # list of tier names contains any of these.
        declared = tasks_dir("declared",
                             ["1-contracts", "2-service-billing", "3-service-ledger"],
                             [("2-service-billing", ["L2-001", "L2-002"]),
                              ("3-service-ledger", ["L3-001"])])
        rc, out, err = run(declared)
        assert rc == 0, f"resolving a declared graph exited {rc}: {err}"
        assert out.split() == ["2-service-billing", "3-service-ledger"], (
            f"the layers of this run resolved to {out.split()}. A hardcoded tier list resolves "
            f"to nothing here, skips every layer, and reports a completed run of zero -- P44")
        assert "1-contracts" in err, (
            "a planned layer with no tasks was not reported. It is usually item 31 dropping a "
            "tier correctly and occasionally generation failing quietly, and only an operator "
            "can tell those apart")

        # Order is the PLAN's, not the alphabet's and not the filesystem's.
        ordered = tasks_dir("ordered", ["9-last", "1-first"],
                            [("1-first", ["L1-001"]), ("9-last", ["L9-001"])])
        rc, out, _err = run(ordered)
        assert rc == 0 and out.split() == ["9-last", "1-first"], (
            f"layers came back as {out.split()}, not in the order layer_plan.json records them. "
            f"The plan is the dependency order; sorting it is a different run")

        # Tasks under a layer nothing planned: reported, and still executed.
        ghost = tasks_dir("ghost", ["1-first"],
                          [("1-first", ["L1-001"]), ("7-ghost", ["L7-001"])])
        rc, out, err = run(ghost)
        assert rc == 0 and out.split() == ["1-first", "7-ghost"], (
            f"a layer with tasks and no plan entry was dropped: {out.split()}. The task files are "
            f"the deliverable; refusing to run work that exists helps nobody")
        assert "7-ghost" in err and "breakdown" in err, (
            f"the plan/files disagreement was not reported as a /breakdown defect:\n{err}")

        # Nothing to run is a REFUSAL, not an empty success.
        empty = tasks_dir("empty", ["1-first", "2-second"], [])
        rc, out, err = run(empty)
        assert rc == 1 and "REFUSED" in err, (
            f"a run with no tasks in any layer exited {rc}. Reporting a completed run of zero "
            f"tasks is the exact failure P44 describes")
        assert not out.strip(), (
            f"a refused run still printed a layer list on stdout: {out!r}. A caller reading the "
            f"list before the exit code acts on a run that was refused")

        # And --layer names a layer of THIS run, or it is refused by name.
        rc, out, err = run(declared, "--layer", "3-frontend")
        assert rc == 1 and "3-frontend" in err and "2-service-billing" in err, (
            f"--layer with a name this run does not have exited {rc}: it must refuse and say "
            f"which layers exist, rather than iterating to a silent zero:\n{err}")
        assert not out.strip(), f"a refused --layer still printed a layer list: {out!r}"
        rc, _out, _err = run(declared, "--layer", "2-service-billing")
        assert rc == 0, "a --layer the run does have was refused"
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("/execute asks for its layers and recites none", finding="P44")
def _():
    """Item 66's other half: the list is gone from the prose, and the rule replacing it is true.

    Item 61's first attempt is why the second assertion exists. It removed a rescinded
    instruction and quoted it in the replacement as a historical note -- and a model reads a
    quoted rule with the same weight as a stated one. A file that says *"this used to iterate
    0-setup, 1-foundation, ..."* has the list in it, whatever the sentence around it claims.
    """
    ex = os.path.join(SKILLS, "execute", "SKILL.md")
    text = open(ex, encoding="utf-8").read()

    assert re.search(r"resolve-layers\.py \{tasks_path\}", text), (
        "/execute never runs resolve-layers.py, so its layer set comes from somewhere it wrote "
        "down -- which is P44 restored")

    step6 = text.split("### Step 6: Execute Layers", 1)
    assert len(step6) == 2, "/execute has no Step 6"
    step6 = step6[1].split("\n### ", 1)[0]
    call_at = step6.index("resolve-layers.py")
    loop_at = step6.index("for layer in layers:")
    assert call_at < loop_at, (
        "the layer list is resolved after the loop that iterates it, so the loop iterates "
        "something else")

    # No list of tier names anywhere in the file -- not as a loop, and not as a quoted history.
    listing = re.search(r"\[[^\]\n]*['\"]0-setup['\"][^\]\n]*['\"]1-foundation['\"][^\]\n]*\]", text)
    assert not listing, (
        f"/execute still carries a list of tier names: {listing.group(0)}. Whether it is iterated "
        f"or quoted as history, it is the list P44 is about -- the history belongs in the plan "
        f"and the ledger (item 61's own first attempt made exactly this mistake)")

    rules = text.split("## Critical Rules", 1)
    assert len(rules) == 2, "/execute has no Critical Rules"
    flat = prose(rules[1])
    assert not re.search(r"Never skip layers|0.1.2.3.4|all 4 layers", flat), (
        "a Critical Rule still asserts a fixed layer sequence. Item 31 derives the set, item 28 "
        "lets a project name its own, and a rule that contradicts them is the second half of P44")
    assert re.search(r"layers the plan declares|order it declares", flat, re.I), (
        "the Critical Rules no longer say what IS true about layers. A check that only forbids "
        "the old sentence passes on a file that has lost both")


@check("the `defined` gate has both halves, and a stale review is not a review -- by running it",
       finding="P26")
def _():
    """Item 40's second half, which schema-6 gave a place to live.

    The bar is *the mechanical tests pass AND a review has been recorded*. For four phases only
    the first half existed, so a feature labelled `defined` and one labelled `defined` after
    somebody read it were the same file -- and nothing downstream could tell them apart.

    The state worth asserting is the third one. A review element alone says a review happened
    once and lets the file be rewritten underneath it, which is a ledger recording adjectives.
    `sha` is what makes it a record: reviewed, STALE, or absent, and the middle one is the state
    that only exists because the hash does.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-definition.py")
    root = tempfile.mkdtemp(prefix="review-40-")
    try:
        d = os.path.join(root, "p")
        shutil.copytree(current_fixture("link-shelf"), d)

        def run(*extra):
            return subprocess.run([sys.executable, script, d, *extra],
                                  capture_output=True, text=True, encoding="utf-8")

        # The fixture arrives reviewed -- that is what schema-6 did -- and passes strictly.
        p = run("--strict")
        assert p.returncode == 0, f"the current fixture does not pass the bar:\n{p.stdout}"
        assert re.search(r"\b(\d+) of \1 reviewed", p.stdout), (
            f"not every `defined` feature in the current fixture is reviewed:\n{p.stdout}")

        # Edit a reviewed feature and the review must go STALE. Nothing about the edit is
        # invalid -- that is the point: the file changed after somebody read it.
        target = os.path.join(d, "features", "save-link.md")
        text = open(target, encoding="utf-8").read()
        open(target, "w", encoding="utf-8", newline="\n").write(
            text.replace("</feature>", "  <!-- one word changed after the review -->\n</feature>"))
        p = run()
        assert "STALE" in p.stdout and "save-link" in p.stdout, (
            f"a feature edited after its review still reads as reviewed:\n{p.stdout}")
        assert p.returncode == 0, (
            "a stale review FAILED the run. Section 4.2's principle is that a wrong label signals "
            "wrong content, so a gate that blocks invites relabelling rather than fixing -- this "
            "one reports, and only --strict is an exit code")
        p = run("--strict")
        assert p.returncode == 1, "--strict passed a stale review, so the report has no teeth"

        # Removing the element is the same verdict by a different route.
        text = open(target, encoding="utf-8").read()
        open(target, "w", encoding="utf-8", newline="\n").write(
            re.sub(r"[ \t]*<review\b[^>]*/>\n", "", text))
        p = run()
        assert "no review recorded" in p.stdout, (
            f"a feature with no review at all was not reported:\n{p.stdout}")

        # And the recorder closes it, computing the hash itself -- one implementation of the
        # rule, in the file that reads it, because a digest computed by hand is right four
        # times and wrong on the fifth.
        p = run("--record-review", "--by", "someone")
        assert p.returncode == 0, f"--record-review failed:\n{p.stdout}\n{p.stderr}"
        p = run("--strict")
        assert p.returncode == 0, (
            f"a freshly recorded review does not satisfy the reader that wrote it:\n{p.stdout}")

        # A review with no reviewer is the adjective this element replaced.
        p = run("--record-review")
        assert p.returncode == 2 and "REFUSED" in p.stderr, (
            f"--record-review wrote a review with nobody's name on it (exit {p.returncode})")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("schema-6 migrates the half it can and reports the half nobody can -- by running it",
       finding="P28")
def _():
    """The schema-5 -> schema-6 step, and the first rule in the migration with no mechanical half.

    R11/R12 map a document `<status>` outside its own enum onto `in-progress` -- the weaker
    claim, because a machine resolving toward `complete` asserts an interview finished that
    nobody finished. R13 cannot do anything at all: a review is a person having read the file.

    So the step must do two things that look contradictory and are not: change what it can, and
    refuse to call the tree finished. A migration that did only the first would leave `--check`
    saying a partly migrated tree is done, which is the failure PARTIAL exists to name.
    """
    import shutil
    import tempfile

    # Derived, never named: the registry says which version is current and which precedes it.
    # A check that names one is a check that quietly stops exercising the newest step.
    _path, reg = schema_registry()
    versions = list(reg["versions"])
    target = reg["current"]
    src_version = versions[versions.index(target) - 1]
    assert reg["versions"][target].get("migration_from_previous") == "mixed", (
        f"the current step {src_version} -> {target} is not `mixed`, so this check is about a "
        f"step that no longer exists")

    root = tempfile.mkdtemp(prefix="current-step-")
    try:
        work = os.path.join(root, "tree")
        shutil.copytree(os.path.join(REPO, "tests", "fixture", "prd", src_version), work)

        p = _run_migrate(work, "--to", target)
        assert p.returncode == 0, f"the step failed outright:\n{p.stdout}\n{p.stderr}"
        out = p.stdout + p.stderr

        # The mechanical half: the document status that nothing had ever validated.
        for rel in ("index.md", "what-next.md"):
            text = open(os.path.join(work, "staff-service", rel), encoding="utf-8").read()
            assert "<status>in-progress</status>" in text, (
                f"staff-service/{rel} still carries a document status outside its own enum. "
                f"/prd --resume finds unfinished PRDs by that tag, so a value nothing can "
                f"classify is a PRD nothing can resume")
            assert "<status>defined</status>" not in text, f"{rel} kept the invalid value"

        # The judgement half: every `defined` feature is PARTIAL, and none of them was touched.
        partial = [ln for ln in out.splitlines() if "PARTIAL" in ln and "R13" in ln]
        assert len(partial) >= 5, (
            f"only {len(partial)} feature(s) reported PARTIAL for the review. A step that "
            f"invents reviews would report none:\n{out}")
        for ln in partial:
            path = os.path.join(work, ln.split()[1].replace("\\", os.sep).replace("/", os.sep))
            if os.path.isfile(path):
                assert "<review" not in open(path, encoding="utf-8").read(), (
                    f"{ln.split()[1]} came out of the migration carrying a review nobody wrote. "
                    f"A placeholder review is a record of nothing, which is the adjective this "
                    f"element replaced")

        # And the tree is not finished, which is the whole point of the state.
        p = _run_migrate(work, "--to", target, "--quiet", "--check")
        assert p.returncode == 1, (
            f"--check called a tree finished in which no feature has been reviewed (exit "
            f"{p.returncode}). `the migration ran` and `the migration finished` are different "
            f"claims")

        # Recording the reviews is what finishes it -- by a person, through the reader.
        cd = os.path.join(SKILLS, "breakdown", "scripts", "check-definition.py")
        for project in ("link-shelf", "staff-service"):
            subprocess.run([sys.executable, cd, os.path.join(work, project),
                            "--record-review", "--by", "suite", "--quiet"],
                           capture_output=True, text=True)
        p = _run_migrate(work, "--to", target, "--quiet", "--check")
        assert p.returncode == 0, (
            f"a tree whose features have all been reviewed is still unfinished:\n{p.stdout}\n"
            f"{p.stderr}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


@check("a CRD's references resolve, and a required one nothing follows is not required -- by running it",
       finding="P24")
def _():
    """Group 8b, and item 39's rule arriving on the path that never had it.

    Three CRD elements had a producer and no consumer from item 23's audit onward, one of them
    `Required`: `<project-ref>` naming the PROJECT.md the change is against, `<prd-ref>` linking
    a change back to the PRD that produced the feature, and `<feature-ref id=>` naming a feature
    in PROJECT.md. `readers.md` carried all three as `open` -- a producer with no consumer is
    P2's shape, and a REQUIRED one is P2 with the volume up.

    The reader is `check-references.py`, which already resolved the PRD path's citations. Same
    program rather than a second one, because it is the same rule: a reference that names
    something must resolve to it, or be reported by name.

    `<project-ref>` is COMPARED against the project the run resolved, never used to resolve it.
    A document choosing which PROJECT.md a run reads would hand a file authority over where the
    run points; comparing catches the case that matters -- a change about another codebase.
    """
    import shutil
    import tempfile

    script = os.path.join(SKILLS, "breakdown", "scripts", "check-references.py")
    root = tempfile.mkdtemp(prefix="crd-refs-8b-")
    try:
        proj = os.path.join(root, "proj")
        os.makedirs(os.path.join(proj, "docs", "prd", "link-shelf"))
        open(os.path.join(proj, "PROJECT.md"), "w", encoding="utf-8", newline="\n").write(
            "<project-context>\n  <meta><name>Demo</name></meta>\n  <features>\n"
            '    <feature id="save-link" built="complete"><name>Save</name></feature>\n'
            '    <feature id="list-links" built="partial"><name>List</name></feature>\n'
            "  </features>\n</project-context>\n")
        open(os.path.join(proj, "docs", "prd", "link-shelf", "index.md"), "w",
             encoding="utf-8", newline="\n").write("<prd><meta><slug>link-shelf</slug></meta></prd>\n")

        def crd(name, project_ref="PROJECT.md", prd_ref="docs/prd/link-shelf/index.md",
                features=("save-link", "list-links")):
            path = os.path.join(proj, name)
            refs = "".join('    <feature-ref id="%s">note</feature-ref>\n' % f for f in features)
            open(path, "w", encoding="utf-8", newline="\n").write(
                "<crd>\n  <meta><slug>demo</slug><workflow>ready</workflow></meta>\n"
                "  <context>\n"
                f"    <project-ref>{project_ref}</project-ref>\n"
                + (f"    <prd-ref>{prd_ref}</prd-ref>\n" if prd_ref else "")
                + f"    <related-features>\n{refs}    </related-features>\n"
                "  </context>\n</crd>\n")
            return path

        def run(path, *extra):
            return subprocess.run([sys.executable, script, path, *extra],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace")

        # A CRD whose references all resolve. Without this the failures below prove nothing.
        p = run(crd("good.md"), "--project-path", proj)
        assert p.returncode == 0, f"a CRD with sound references was reported:\n{p.stdout}{p.stderr}"
        assert re.search(r"\b[1-9]\d* reference\(s\) checked", p.stdout), (
            f"the CRD branch checked no references at all:\n{p.stdout}")

        # 1. a feature-ref naming a feature PROJECT.md does not have.
        p = run(crd("ghost.md", features=("save-link", "ghost-feature")), "--project-path", proj)
        assert p.returncode == 1 and "ghost-feature" in p.stderr, (
            f"a <feature-ref> naming nothing resolved anyway (exit {p.returncode}):\n{p.stderr}")

        # 2. a prd-ref that does not exist -- the only structured change-to-feature link there is.
        p = run(crd("noprd.md", prd_ref="docs/prd/gone/index.md"), "--project-path", proj)
        assert p.returncode == 1 and "prd-ref" in p.stderr, (
            f"a dangling <prd-ref> was accepted:\n{p.stderr}")

        # 3. a project-ref pointing at a PROJECT.md that is not this run's.
        other = os.path.join(root, "other")
        os.makedirs(other)
        shutil.copyfile(os.path.join(proj, "PROJECT.md"), os.path.join(other, "PROJECT.md"))
        p = run(crd("elsewhere.md", project_ref="../other/PROJECT.md"), "--project-path", proj)
        assert p.returncode == 1 and "another project" in p.stderr, (
            f"a CRD naming a different PROJECT.md than the run passed:\n{p.stderr}")

        # 4. and the required element missing entirely.
        path = crd("noproject.md")
        text = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8", newline="\n").write(
            re.sub(r"[ \t]*<project-ref>.*?</project-ref>\n", "", text))
        p = run(path, "--project-path", proj)
        assert p.returncode == 1 and "project-ref" in p.stderr, (
            f"a CRD with no <project-ref> was accepted, and it is Required:\n{p.stderr}")

        # Without --project-path the comparison cannot be made, and the run says so rather than
        # reporting a check it did not make.
        p = run(crd("alone.md"))
        assert "no --project-path" in p.stdout, (
            f"the CRD branch made no note of the comparison it could not make:\n{p.stdout}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # And the gate stops skipping it: a CRD used to short-circuit the reference check entirely.
    gate = open(os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py"),
                encoding="utf-8").read()
    assert not re.search(r'\(0, ""\) if os\.path\.isfile\(args\.document\)', gate), (
        "the gate still short-circuits the reference check for a CRD, so the reader added here "
        "is never reached by the one caller that matters")

    # And it REPORTS what the resolver says, asserted by running it rather than by finding the
    # word `dangling` in the source -- which is what this said first, and a mutant that dropped
    # the findings loop while keeping the variable walked straight through it.
    root = tempfile.mkdtemp(prefix="gate-refs-8b-")
    try:
        proj = os.path.join(root, "proj")
        os.makedirs(os.path.join(proj, "tasks"))
        open(os.path.join(proj, "PROJECT.md"), "w", encoding="utf-8", newline="\n").write(
            "<project-context>\n  <meta><name>Demo</name></meta>\n  <features>\n"
            '    <feature id="save-link" built="complete"><name>Save</name></feature>\n'
            "  </features>\n</project-context>\n")
        crd_path = os.path.join(proj, "demo.md")
        open(crd_path, "w", encoding="utf-8", newline="\n").write(
            "<crd>\n  <meta><slug>demo</slug><workflow>ready</workflow></meta>\n  <context>\n"
            "    <project-ref>PROJECT.md</project-ref>\n    <related-features>\n"
            '      <feature-ref id="ghost-feature">note</feature-ref>\n'
            "    </related-features>\n  </context>\n</crd>\n")
        for name, body in (("manifest.json", '{"task_inventory": []}'),
                           ("analysis.json", '{"scope": "small"}')):
            open(os.path.join(proj, "tasks", name), "w", encoding="utf-8",
                 newline="\n").write(body)
        p = subprocess.run(
            [sys.executable, os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py"),
             crd_path, os.path.join(proj, "tasks"), "--project-path", proj],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert "ghost-feature" in (p.stdout + p.stderr), (
            f"the gate ran the reference check on a CRD and reported nothing it said:\n"
            f"{p.stdout}\n{p.stderr}")

        # And it is a FINDING, not only a printed line. Asserting the printed line alone left a
        # mutant alive that dropped the reference from `findings` while still printing it --
        # findings are what the gate's confirmation and its count are built on, so a dangling
        # reference that prints and does not count is a report with nothing behind it.
        p = subprocess.run(
            [sys.executable, os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py"),
             crd_path, os.path.join(proj, "tasks"), "--project-path", proj, "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        report = json.loads(p.stdout)
        refs = [f for f in report.get("findings") or [] if f.get("assertion") == "references"]
        assert refs and any("ghost-feature" in f["detail"] for f in refs), (
            f"the gate's findings carry no `references` entry, so the dangling reference is "
            f"printed and counts for nothing:\n{p.stdout}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    # readers.md keeps the verdict it no longer uses.
    readers = open(os.path.join(SCHEMA, "readers.md"), encoding="utf-8").read()
    for tag in ("project-ref", "prd-ref", "feature-ref"):
        assert not re.search(r"\|\s*`%s`\s*\|\s*\*\*open\*\*" % tag, readers), (
            f"`{tag}` is still recorded as a producer with no consumer, and it now has one")


@check("a snapshot that replaces another says what changed between them -- by running it",
       finding="P45")
def _():
    """Item 67, and the defect a live run found in item 63's own guard.

    `record` runs on every invocation, including a resume -- deliberately, because an operator
    may fix a task between runs and forbidding that leaves an unsatisfiable task with nowhere to
    go. The assumption inside that was the defect: *the operator* and *the run* are the same
    participant when one agent stops, edits and resumes. The fourth crossing did exactly that,
    the resume snapshotted the edited file, and `verify` said UNCHANGED for the rest of the run.

    The rule is unchanged and the silence is not: a re-record compares first, records every
    difference with both hashes and a diff, and carries on. What must never happen again is a
    snapshot replacing another with nothing recording what it replaced.
    """
    import shutil
    import stat
    import tempfile

    script = os.path.join(SKILLS, "execute", "scripts", "task-integrity.py")

    def rmtree(path):
        def clear_ro(func, target, _exc):
            os.chmod(target, stat.S_IWRITE)
            func(target)
        try:
            shutil.rmtree(path, onexc=clear_ro)
        except TypeError:
            shutil.rmtree(path, onerror=clear_ro)

    root = tempfile.mkdtemp(prefix="item67-")
    try:
        tasks, app = os.path.join(root, "tasks"), os.path.join(root, "app")
        os.makedirs(os.path.join(tasks, "0-setup"))
        os.makedirs(app)
        task = os.path.join(tasks, "0-setup", "L0-001-x.xml")

        def write(step):
            open(task, "w", encoding="utf-8", newline="\n").write(
                "<task><meta><id>L0-001</id></meta><verification><step>%s</step>"
                "</verification></task>\n" % step)

        def run(mode):
            p = subprocess.run([sys.executable, script, mode, tasks, app, "demo"],
                               capture_output=True, text=True, timeout=120)
            return p.returncode, (p.stdout or ""), (p.stderr or "")

        write("Run: pytest")
        rc, out, _err = run("record")
        assert rc == 0 and "RECORDED" in out, out

        # The between-runs edit: the exact move the fourth crossing made.
        write("Run: pytest -k not_the_broken_one")
        rc, out, err = run("record")
        assert rc == 0, (
            f"a re-record after an edit between runs exited {rc}. Fixing a task between runs is "
            f"the supported path -- item 63's escalation exists so an unsatisfiable task has "
            f"one -- and blocking it here would take that away")
        assert "CHANGED SINCE LAST RUN" in err and "L0-001" in err, (
            f"the re-record replaced a snapshot without saying what it replaced:\n{err}")
        assert "not_the_broken_one" in err and err.count("---") >= 1, (
            f"the report names the file and shows no diff. A summary of an edit to an acceptance "
            f"criterion is not the evidence:\n{err}")
        assert "changed since the last run" in out, (
            f"the RECORDED line does not carry the count, so a caller reading stdout sees a "
            f"clean record: {out}")

        edits = os.path.join(app, ".execute", "demo", "task-edits.jsonl")
        assert os.path.isfile(edits), "nothing recorded the edit between runs"
        entry = json.loads(open(edits, encoding="utf-8").read().splitlines()[0])
        assert entry["kind"] == "edited-between-runs", (
            f"the record does not distinguish an edit between runs from one during a dispatch: "
            f"{entry}. They are the same act and only one of them is legitimate, so the KIND is "
            f"the whole of the difference")
        assert entry["sha_before"] != entry["sha_after"], entry
        assert os.path.isfile(os.path.join(app, ".execute", "demo", entry["diff"])), (
            f"the record points at a diff that was never written: {entry['diff']}")

        # The new snapshot is the edited file -- the resume must not fight the fix it recorded.
        rc, out, _err = run("verify")
        assert rc == 0 and "UNCHANGED" in out, (
            f"after recording the edit, the new snapshot does not match the task files: {out}")

        # And a mid-dispatch edit is still a stop, distinguished only by `kind`.
        write("Run: true")
        rc, _out, err = run("verify")
        assert rc == 1 and "EDITED" in err, f"a mid-dispatch edit stopped being a stop: {err}"
        kinds = [json.loads(l)["kind"] for l in open(edits, encoding="utf-8").read().splitlines()]
        assert kinds == ["edited-between-runs", "modified"], (
            f"the two kinds of edit are not told apart in the record: {kinds}")

        # Two diffs, two files: a second edit must not overwrite the record of the first.
        diffs = os.listdir(os.path.join(app, ".execute", "demo", "task-edits"))
        assert len(diffs) == 2, (
            f"{len(diffs)} diff file(s) for two edits to the same task. A record that overwrites "
            f"itself is the erasure P45 was about, one directory down: {diffs}")
    finally:
        rmtree(root)

    # And /execute is told to report it, since a resume that says nothing is how P45 stayed
    # invisible through a whole run.
    ex = prose(open(os.path.join(SKILLS, "execute", "SKILL.md"), encoding="utf-8").read())
    assert re.search(r"re-record says what it replaced|changed since the last run", ex, re.I), (
        "/execute does not mention that a re-record reports what it replaced, so the lines land "
        "in a file nobody was told to read")


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


@check("the review the gate requires has a producer on the authoring path -- by running it",
       finding="P46")
def _():
    """Item 68, finding V1. Item 23's rule, run in the direction it does not check.

    schema-6 exists to give item 40's gate its second half, and it shipped with a READER
    (`check-definition.py`), a fixture and a migration rule -- and nothing on the authoring path
    that can write one. `check-readers.py` cannot see this: it asserts every element has a
    reader, and the reverse direction is a report by design.

    The defect was not only an omission. `/prd` INSTRUCTED the author that the PRD carries no
    place to record a review, which was true before schema-6 and false after it -- so a run
    following its own command file would report the absence as unfixable.

    Three assertions, and the third is the one that would have caught it:
      1. the template `/prd` writes from carries <review> in <meta>
      2. `/prd` names the producer, and the producer really has that flag
      3. `/prd` does not still claim there is nowhere to record a review
    """
    fmt = open(os.path.join(SCHEMA, "prd-format.md"), encoding="utf-8").read()

    # 1. Scope to the feature template's <meta> block. Matching the whole file would let the
    #    prose below it satisfy a check about the template.
    blocks = re.findall(r"```xml\n(.*?)```", fmt, re.S)
    metas = [m.group(1) for b in blocks for m in [re.search(r"<meta>(.*?)</meta>", b, re.S)]
             if m and "<slug>" in m.group(1) and "<definition>" in m.group(1)]
    assert metas, "prd-format.md has no feature <meta> template carrying <slug> and <definition>"
    assert any("<review" in m for m in metas), (
        "the feature template in prd-format.md does not carry <review>. core section 7 is the "
        "only section of the core that no format reference points at, and the bar requires the "
        "element on every `defined` feature")

    prd = open(os.path.join(COMMANDS, "prd.md"), encoding="utf-8").read()

    # 2. The producer, named where the judgement it records is produced -- and it must be real.
    assert "--record-review" in prd, (
        "commands/prd.md never names `check-definition.py --record-review`. The element has a "
        "reader, a fixture and a migration rule; without this it has no producer, which is P2's "
        "shape inside the version that shipped the element")
    definition = open(os.path.join(SKILLS, "breakdown", "scripts", "check-definition.py"),
                      encoding="utf-8").read()
    assert '"--record-review"' in definition, (
        "commands/prd.md names a flag check-definition.py does not register. A cited producer "
        "that cannot run is the same defect one step along")

    # 3. The claim, not the phrasing. `prose()` so a rewrap or an emphasis does not decide it.
    flat = prose(prd)
    for stale in ("carries no place to record that review",
                  "no place to record that review",
                  "carries no place to record"):
        assert stale not in flat, (
            f"commands/prd.md still tells the author {stale!r}. schema-6 IS that place, and an "
            f"instruction that denies it is what made the element unproducible")


@check("every file that runs an owning script is listed as its caller -- by running it",
       finding="P47")
def _():
    """Item 69, finding V3. The direction `checks.md` asserted about itself and never checked.

    The existing check walks the table forward: the owner exists, and each CLAIMED caller names
    it. Nothing walked it backward, so a script wired into a new caller -- or a script that owns
    an assertion and never gets a row at all -- was invisible. Both happened, in consecutive
    phases: group 8b gave `check-references.py` two new callers, and Phase 7 shipped
    `task-integrity.py` and `resolve-layers.py`, each with a REFUSED exit code and no row.

    INVOKES, NOT MENTIONS, and the distinction is the whole check. Half the repository names
    these scripts in a docstring or a cross-reference; a naive substring match reports thirty
    files and is therefore ignored. A caller is a line that RUNS it: `python <path>/<script>`,
    `sh <path>/<script>`, a `run("<script>")` helper, or an interpolated plugin path. That rule
    finds exactly the four real gaps this check was written for and no others.
    """
    text = open(os.path.join(SCHEMA, "checks.md"), encoding="utf-8").read()
    assert "## The table" in text, "checks.md has no table section"
    table = text.split("## The table", 1)[1]

    rows = []
    for line in table.splitlines():
        if not line.startswith("| ") or line.startswith("| Assertion") or set(line) <= set("| -"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4:
            rows.append((cells[0], cells[1].strip("`"), re.findall(r"`([^`]+)`", cells[2])))
    assert rows, "checks.md's table parsed to no rows -- the check is measuring nothing"

    def invokes(body, script):
        for line in body.splitlines():
            if script not in line:
                continue
            if re.search(r"(python\d?|sh|bash)\s+[^\s|]*" + re.escape(script), line):
                return True
            if re.search(r"run\(\s*[\"']" + re.escape(script), line):
                return True
            if re.search(r"(\$\{CLAUDE_PLUGIN_ROOT\}|\{skill_dir\})[^\s`]*" + re.escape(script),
                         line):
                return True
        return False

    scan = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", "data", "docs", "tests", ".tmp-phase10")]
        for fn in files:
            if fn.endswith((".md", ".py", ".sh")):
                scan.append(os.path.relpath(os.path.join(root, fn), REPO).replace(os.sep, "/"))
    assert len(scan) > 40, f"the file scan found only {len(scan)} files, so it is not scanning"

    unlisted = []
    for assertion, owner, claimed in rows:
        if not owner.endswith((".py", ".sh")):
            continue
        for p in scan:
            if p.endswith("/" + owner) or p == owner or p in claimed:
                continue
            try:
                body = open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if invokes(body, owner):
                unlisted.append(f"{p} runs {owner} and is not in its `Invoked by` column")

    assert not unlisted, (
        "checks.md is behind the toolchain it describes:\n    " + "\n    ".join(unlisted)
        + "\n\nA row is the claim that every caller is known. An unlisted caller is how "
          "`check-references.py` reached a CRD for a whole phase with the table saying otherwise")

    # And the two Phase 7 assertions that had no row at all. Named rather than derived: a
    # script with a REFUSED exit code is an assertion, and the table's own exclusion list is
    # seven scripts that DO things, all of which predate these two.
    owners = {owner for _a, owner, _c in rows}
    for script, why in (("task-integrity.py", "decides whether a task file is the one dispatched"),
                        ("resolve-layers.py", "decides which layers this run executes")):
        assert script in owners, (
            f"{script} {why} and exits 1 to refuse, and checks.md gives it no row. "
            f"`resolve-output.sh` is in the table on exactly that basis")


@check("a documented invocation names the plugin root, never a bare relative path",
       finding="P48")
def _():
    """Item 70, finding V2. Open question 1 measured this and item 9 states it as a rule.

    The working directory is the TARGET PROJECT, not the plugin, so `python skills/x/y.py`
    resolves against the wrong tree and fails with a bare `No such file or directory` -- an error
    that reads like a missing file rather than a wrong assumption. The probe recorded the same
    thing from the other side: a command naming no path at all left the model to brute-force it,
    at eight tool calls including a `find /`.

    Every invocation site in the repository used `${CLAUDE_PLUGIN_ROOT}` or `{skill_dir}` until
    Phase 8 added two that did not -- one of them in `migration.md`, 87 lines from four of its
    own that do it correctly, and the other the only documented invocation of the producer item
    68 exists to supply. A rule with two violations needs a check; a convention with none did not.
    """
    bare = re.compile(r"(?<![\w/}])(python\d?|sh|bash)\s+(skills|schema|commands|agents)/[\w./-]+\.(py|sh)")

    offenders = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", "data", "docs", "tests", ".tmp-phase10")]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, REPO).replace(os.sep, "/")
            for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                m = bare.search(line)
                if m:
                    offenders.append(f"{rel}:{n}  {m.group(0)}")

    assert not offenders, (
        "a documented command uses a path relative to the plugin, which resolves against the "
        "target project instead:\n    " + "\n    ".join(offenders)
        + "\n\nUse ${CLAUDE_PLUGIN_ROOT}/... in a command or reference, {skill_dir}/... in a "
          "skill. And pass the path as an ARGUMENT: the variable is expanded by the harness at "
          "command-expansion time and is NOT exported to the shell the script runs in")


@check("no shipped artefact describes a state the toolchain has left -- by running it",
       finding="P49")
def _():
    """Item 71, finding V4. Three instances, one shape, and each was found a different way.

    (a) A SCRIPT SAYS A LANDED ITEM IS PENDING. `check-scope.py` shipped in group 5b saying
        `ATTRIBUTION IS ITEM 16's, AND IT HAS NOT LANDED`; item 16 landed in 5d, two commits
        later, and by item 65 the same file was calling `edges_of()`. The docstring is a comment
        and costs nothing; line 170 prints `(item 16 adds the attribution)` to an OPERATOR, so a
        real generator defect reads as a not-yet-built feature. The landed set is derived from
        the ledger rather than listed here, so this generalises past the instance that caused it.

    (b) A REGISTRY STATES A COUNT THAT IS WRONG. `readers.md` said the reverse report yields six.
        It yields seven. Asserting the number against the SCRIPT rather than against a constant
        is the only version of this that cannot go stale the same way.

    (c) THREE SIBLING REGISTRIES STAMP A SUPERSEDED SCHEMA. `checks.md`, `parity.md` and
        `readers.md` carried `schema-5` while the core carried `schema-6`, and only the core's
        stamp was asserted. Either reading of that stamp indicts it: if it means what the core's
        means it was wrong, and if it means `last reconciled at` then it was ANNOUNCING that
        these files were a version behind while nothing read it -- which (b) and item 69's
        missing rows independently confirm. Settled as the first reading: one meaning for one
        syntax, and `reconciled at` is what item 69's reverse check measures properly.
    """
    # ---- (a) a landed item, described as pending, in something that ships
    ledger = open(os.path.join(REPO, "docs", "skills", "plugin-2.0-progress.md"),
                  encoding="utf-8").read()
    landed = set()
    for line in ledger.splitlines():
        if line.startswith("| **") and ("Landed" in line or "Done" in line):
            landed.update(int(n) for n in re.findall(r"\b(\d{1,2})\b", line.split("|")[1]))
    assert len(landed) > 50, (
        f"only {len(landed)} landed items parsed from the ledger -- the check is measuring "
        f"almost nothing, which is how a control passes over its own subject in silence")

    pending = re.compile(r"(has not landed|have not landed|has not yet landed|is not yet built|"
                         r"does not exist yet|item \d{1,2} adds\b|item \d{1,2} will\b)", re.I)
    stale = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs
                   if d not in (".git", "__pycache__", "data", "docs", "tests", ".tmp-phase10")]
        for fn in files:
            if not fn.endswith((".py", ".sh", ".md")):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, REPO).replace(os.sep, "/")
            for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if not pending.search(line):
                    continue
                # THE CLAIM AND THE ITEM MUST BE IN THE SAME CLAUSE. Pairing them anywhere on a
                # line conflates *this line mentions item N* with *this line says item N is
                # pending*, and that produced a false positive the day it was written: a parity
                # row reading "item 57 generalised it; an added entity is a contract naming a ref
                # that DOES NOT EXIST YET" was flagged, where the thing not existing is a schema
                # ref and not an item. Splitting on clause boundaries is the rule a reader
                # applies -- a claim about an item ends where its sentence does.
                for clause in re.split(r"[.;]|\s—\s", line):
                    if not pending.search(clause):
                        continue
                    cited = {int(x) for x in re.findall(r"item (\d{1,2})", clause, re.I)}
                    if cited & landed:
                        stale.append(f"{rel}:{n}  {clause.strip()[:100]}")
                        break
    assert not stale, (
        "a shipped artefact says a landed item is still pending:\n    " + "\n    ".join(stale)
        + "\n\nThe ledger records these as landed. A docstring costs a reader a minute; a line "
          "printed to an operator costs them the diagnosis")

    # ---- (b) the registry's own count, against the script that produces it
    readers_md = open(os.path.join(SCHEMA, "readers.md"), encoding="utf-8").read()
    script = os.path.join(SCHEMA, "scripts", "check-readers.py")
    p = subprocess.run([sys.executable, script], capture_output=True, text=True, encoding="utf-8")
    actual = len(re.findall(r"^\s*READ-ONLY\b", p.stdout, re.M))
    assert actual, f"check-readers.py reported no READ-ONLY lines at all:\n{p.stdout[-400:]}"

    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    m = re.search(r"filters take it to \*\*(\w+)\*\*", readers_md)
    assert m, ("readers.md no longer states how many candidates survive its filters. The number "
               "is the only part of that paragraph a reader can check")
    claimed = words.get(m.group(1).lower(), None)
    assert claimed == actual, (
        f"readers.md says the reverse report yields {m.group(1)} ({claimed}); running "
        f"check-readers.py yields {actual}. A registry whose own figure is wrong is the failure "
        f"it exists to prevent, one level in")

    # ---- (c) one meaning for one syntax, across every schema document that stamps a version
    schemas = json.load(open(os.path.join(REPO, "tests", "fixture", "prd", "SCHEMAS.json"),
                             encoding="utf-8"))
    current = schemas["current"]
    stamped = 0
    for fn in sorted(os.listdir(SCHEMA)):
        if not fn.endswith(".md"):
            continue
        body = open(os.path.join(SCHEMA, fn), encoding="utf-8").read()
        for tag, version in re.findall(r"<([a-z-]+)\s+(?:version|schema)=\"(schema-\d+)\"\s*/>",
                                       body):
            stamped += 1
            assert version == current, (
                f"schema/{fn} stamps <{tag} ...=\"{version}\"> while SCHEMAS.json calls "
                f"{current!r} current. A stamp that is allowed to lag is a stamp nobody reads, "
                f"which is P28's own finding")
    assert stamped >= 4, (
        f"only {stamped} schema stamps found; the core, checks, parity and readers all carry one, "
        f"so a lower count means this loop has stopped matching them")


@check("the documents that describe the layout describe the one on disk -- by reading both",
       finding="P50")
def _():
    """Item 72, finding V12/V13. Nine phases landed without touching a top-level document.

    `ARCHITECTURE.md`, `README.md` and `CLAUDE.md` each enumerate or count the repository, and
    each was written before `migrate/`, `prd-criteria-author` and `schema/` existed. The ledger
    never mentions any of them -- not as done, not as deferred -- which is how a document that
    onboards somebody ends up describing a smaller project than the one they cloned.

    BOTH DIRECTIONS, for item 69's reason one level up. A document naming something that does not
    exist sends a reader to a missing file; a document silently omitting something real is worse,
    because there is nothing to look up and no way to notice. `execute-task` was the first kind
    for nine phases and `schema/` was the second.
    """
    on_disk_skills = {d for d in os.listdir(SKILLS)
                      if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))}
    on_disk_agents = {f[:-3] for f in os.listdir(AGENTS) if f.endswith(".md")}
    assert len(on_disk_skills) > 10 and len(on_disk_agents) > 5, (
        "the disk scan found almost nothing, so this check is measuring itself")

    def enumerated(path, heading):
        """Names inside the fenced block under `heading`. Scoped: the whole file would let any
        passing mention satisfy a check about a structural listing."""
        text = open(path, encoding="utf-8").read()
        assert heading in text, f"{os.path.basename(path)} has no '{heading}' section"
        after = text.split(heading, 1)[1]
        blocks = re.findall(r"```[a-z]*\n(.*?)```", after, re.S)
        assert blocks, f"{os.path.basename(path)}'s '{heading}' section has no fenced block"
        return blocks[0]

    for path, heading in ((os.path.join(REPO, "ARCHITECTURE.md"), "## File Structure"),
                          (os.path.join(REPO, "CLAUDE.md"), "## Key Directories")):
        name = os.path.basename(path)
        block = enumerated(path, heading)

        named = set(re.findall(r"\b([a-z0-9]+(?:-[a-z0-9]+)*)/\s", block))
        ghosts = {n for n in named
                  if n.endswith(("-prd", "-tasks", "-layers", "-batch", "-verify", "-merge",
                                 "-layer", "-task", "-update", "-analysis", "-investigate"))
                  and n not in on_disk_skills}
        assert not ghosts, (
            f"{name}'s {heading} lists skill directories that do not exist: {sorted(ghosts)}. "
            f"A reader following one finds nothing, and `execute-task` was listed for nine "
            f"phases after item 4.15 removed it")

        missing = sorted(s for s in on_disk_skills if s + "/" not in block)
        assert not missing, (
            f"{name}'s {heading} omits skills that exist: {missing}. An omission is worse than a "
            f"ghost -- there is nothing to look up and no way to notice")

        # A LINE that starts with it, not a mention of it anywhere. `schema/checks.md` inside a
        # comment about a different directory satisfied the looser form, so the check asserted a
        # string rather than the shape it cared about -- two sites, and no single edit could
        # break it. See the site-counting rule this ledger has confirmed five times.
        assert re.search(r"^schema/", block, re.M), (
            f"{name}'s {heading} does not list schema/ as a top-level directory. Item 44 made it "
            f"the single definition of every element both paths share, and it went unlisted in "
            f"both of these documents for four phases")

        agents_missing = sorted(a for a in on_disk_agents if a not in block)
        assert not agents_missing, (
            f"{name}'s {heading} omits agents that exist: {agents_missing}")

    # README states counts rather than enumerating, so the count is what can go wrong.
    readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
    for label, actual in (("skills", len(on_disk_skills)),
                          ("subagent definitions", len(on_disk_agents)),
                          ("slash commands", len(command_files()))):
        m = re.search(r"(\d+)\s+" + re.escape(label), readme)
        assert m, f"README.md no longer states a count of {label}; it did, and it was wrong"
        assert int(m.group(1)) == actual, (
            f"README.md says {m.group(1)} {label}; there are {actual}")


@check("a documented frontmatter example is one a skill could actually declare",
       finding="P50")
def _():
    """Item 72's second half. `ARCHITECTURE.md` teaches the pattern and taught it wrong.

    Its `What is Context Fork?` section shows a SKILL.md frontmatter example carrying
    `allowed-tools:` -- the command key that silently stops `context: fork` taking effect (F13),
    which is the single defect item 4.11 existed to remove and which the suite forbids in every
    real skill. The example was on a skill that does not exist, so nothing pointed at it, and a
    reader copying it writes a skill that does not fork and cannot be told why.

    The model table is the same failure in data rather than in syntax: it assigned `sonnet` to
    almost everything while the files declare a mix of haiku, sonnet and opus, and named a
    component that has not existed since item 4.15.
    """
    arch_path = os.path.join(REPO, "ARCHITECTURE.md")
    arch = open(arch_path, encoding="utf-8").read()

    for block in re.findall(r"```yaml\n(.*?)```", arch, re.S):
        assert "allowed-tools" not in block, (
            "ARCHITECTURE.md shows a skill frontmatter example declaring `allowed-tools`. That "
            "is a COMMAND key: in a skill it restricts nothing and silently disables "
            "`context: fork` (F13). The suite forbids it in every real skill, and a document "
            "teaching it is the same defect with a wider blast radius")

    # The model table, against what the files declare. A table of assignments nobody compares
    # to the frontmatter is a table of intentions.
    declared = {}
    for name, path in skill_files():
        fm, _ = parse_frontmatter(path)
        if fm.get("model"):
            declared[name] = str(fm["model"]).strip()
    assert declared, "no skill declares a model, so this check has nothing to compare"

    section = arch.split("## Model Selection Strategy", 1)
    assert len(section) == 2, "ARCHITECTURE.md has no Model Selection Strategy section"
    table = section[1].split("##", 1)[0]

    rows = {}
    for line in table.splitlines():
        if not line.startswith("|") or set(line) <= set("|- "):     # skip the separator row
            continue
        m = re.match(r"\|\s*`?/?([a-z0-9-]+)`?[^|]*\|\s*`?([a-z0-9.*()-]+)`?[^|]*\|", line)
        if m:
            rows[m.group(1)] = m.group(2)
    assert len(rows) > 5, f"the model table parsed to {len(rows)} rows, so it is not being read"

    for name, model in sorted(rows.items()):
        if name in ("component", "prd", "crd", "crd-context"):
            continue
        assert name in declared or name in {a for a, _p in agent_files()}, (
            f"the model table names `{name}`, which is neither a skill nor an agent. "
            f"`execute-task` sat in this table for nine phases after item 4.15 removed it")
        if name in declared:
            assert declared[name].startswith(model) or model in declared[name], (
                f"the model table says `{name}` runs on {model}; its SKILL.md declares "
                f"{declared[name]}. A table of assignments nobody compares to the frontmatter "
                f"is a table of intentions")


@check("the documented way to load the plugin is the one that works", finding="P50")
def _():
    """Item 72's third half, and the only one a new user meets in their first minute.

    `--plugin-dir` loads the plugin; it does not make the plugin's own scripts readable. Without
    `--add-dir` on the same checkout, `/breakdown` stops in Phase 1 because `resolve-output.sh`,
    `check-references.py` and `build-manifest.py` are outside the session's allowed directories.
    That was MEASURED on 2026-08-26 and written into CLAUDE.md; README.md kept the one-flag form,
    so the file a new reader opens first is the one that does not work.
    """
    # EVERY line that gives the flag, fenced or inline. The first version of this check read
    # only fenced blocks and a mutant walked straight past it: CLAUDE.md gives the command in
    # inline backticks inside a block quote, so the one document that had the rule right was
    # the one the check could not see.
    seen = 0
    for name in ("README.md", "CLAUDE.md"):
        text = open(os.path.join(REPO, name), encoding="utf-8").read()
        for line in text.splitlines():
            if "--plugin-dir" not in line:
                continue
            seen += 1
            assert "--add-dir" in line, (
                f"{name} documents `{line.strip()[:90]}`. `--plugin-dir` loads the plugin and "
                f"does not make its bundled scripts readable -- measured 2026-08-26, and without "
                f"`--add-dir` /breakdown stops in Phase 1")
    assert seen >= 2, (
        f"only {seen} line(s) documenting --plugin-dir were found across README.md and CLAUDE.md. "
        f"Both give the command; a check that finds fewer has stopped reading one of them")


@check("a document describing a target state says whether it was reached", finding="P50")
def _():
    """Item 72's fourth half, and the cheapest of the four to have got wrong.

    `target-state-data-flow.md` opens `Status: Target state. None of this is built.` -- written
    2026-08-25, true then, and false since Phase 6 closed the plan. Every box in it now exists.
    A document that announces its own obsolescence and is never revisited is worse than one with
    no status at all, because the status is the part a reader trusts without checking.
    """
    p = os.path.join(REPO, "docs", "skills", "target-state-data-flow.md")
    text = open(p, encoding="utf-8").read()

    # The document QUOTES the claim it used to make, to explain the correction. A check that
    # cannot tell an assertion from a quotation of one forbids documenting the history it
    # enforces -- which this suite did once before, in Phase 2, on the words "full PRD content".
    # So quoted spans come out before the negative assertion is made.
    status_line = re.search(r"^\*\*Status:\*\*(.*)$", text, re.M)
    assert status_line, "target-state-data-flow.md has no **Status:** line at all"
    unquoted = re.sub(r"[\"“‘’”][^\"“‘’”]*"
                      r"[\"“‘’”]", " ", status_line.group(1))
    assert not re.search(r"none of this is built", prose(unquoted), re.I), (
        "target-state-data-flow.md's status still asserts that none of it is built. Items 1-67 "
        "landed across nine phases; the plan's own header was corrected at item 68's phase and "
        "this is the same defect in the document that header points at")

    # THE STATUS FIELD, not the paragraph around it. The first version asked whether any of
    # `built|landed|reached` appeared in the first twenty lines -- six sites did, so deleting the
    # verdict changed nothing and the mutant survived. That is the site-counting rule twice in
    # one phase: a check satisfied by more than one site cannot be broken by one edit.
    # The verdict must LEAD the field, not appear somewhere in it. Asserting it anywhere in the
    # line was satisfied by "every box in it was built across Phases 1-9" further along, so
    # deleting the verdict itself changed nothing -- the site-counting rule a third time in one
    # phase, and inside a line short enough that it looked scoped already.
    verdict = prose(status_line.group(1))
    opening = " ".join(verdict.split()[:6])
    assert re.search(r"\b(reached|not reached|built|landed|implemented|superseded|abandoned)\b",
                     opening, re.I), (
        f"target-state-data-flow.md's status opens {opening!r}, which does not say whether the "
        f"target state was reached. A status field leads with its value; removing a false status "
        f"leaves a reader with no status, which is the same problem quieter")


@check("no task depends on a layer that runs after it -- by running it on both controls",
       finding="P51")
def _():
    """Item 73, and open question 7 is why it is an exit code.

    OQ7 ran a PRD through the shipped graph and through an inverted one. The inverted arm emitted
    14 tasks in which backend endpoints imported `Link`, `get_db` and `db_session` from a layer
    the declared graph runs AFTER them -- 16 unsatisfiable edges -- and `check-coverage.py` and
    `check-gate.py` both exited 0. A second run of the same graph noticed and refused. **The
    protection was a model judgement and it fired in one run of two.**

    BOTH CONTROLS, AND THE NEGATIVE ONE IS NOT DECORATION. A checker that refuses everything
    would pass a test that only feeds it the bad arm. `sound/` is real generator output from the
    default graph and must be silent; `inverted/` is real output from the inverted one and must
    refuse. Neither was hand-built -- a fixture written to match the checker validates the code
    against itself.
    """
    script = os.path.join(SKILLS, "breakdown", "scripts", "check-layering.py")
    assert os.path.isfile(script), "check-layering.py does not exist"
    base = os.path.join(REPO, "tests", "fixture", "layering")

    def run(arm, *extra):
        return subprocess.run([sys.executable, script, os.path.join(base, arm), *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    # Negative control: the sound arm must be silent, or the check has no discrimination.
    p = run("sound")
    assert p.returncode == 0, (
        f"check-layering.py refused the SOUND arm, which came out of the default graph with no "
        f"forward references at all:\n{p.stderr[:500]}")

    # Positive control: the inverted arm must refuse, and must NAME what it found.
    p = run("inverted")
    assert p.returncode == 1, (
        f"check-layering.py passed the INVERTED arm. That task set has backend endpoints "
        f"importing their models from a layer that runs after them; if this passes, the check "
        f"has no subject:\n{p.stdout[-500:]}")
    assert "4-foundation" in p.stderr and "3-backend" in p.stderr, (
        f"the refusal does not name both layers, so an operator cannot act on it:\n{p.stderr[:400]}")
    assert re.search(r"needs '(get_db|Link|db_session)'", p.stderr), (
        f"the refusal names no interface. A count is not a finding -- item 30's lesson:\n"
        f"{p.stderr[:400]}")

    # --json is the object and nothing else (group 8b's defect, not repeated).
    p = run("inverted", "--json")
    data = json.loads(p.stdout)
    assert len(data["violations"]) >= 10, (
        f"the inverted arm yields {len(data['violations'])} violations; the measured run had 16. "
        f"A positive control that has drifted toward zero is a check losing its subject")
    assert data["order_source"] == "layer_plan.json", (
        "order came from directory names rather than the plan. A layer id is not a rank -- the "
        "graph that produced this fixture has ids ascending while its dependencies do not")

    # An external library is NOT a violation. The first version of this metric counted `python`
    # and `sqlite3` as unmet contracts and reported 9 findings against the sound arm.
    p = run("sound", "--json")
    assert json.loads(p.stdout)["violations"] == [], (
        "the sound arm reports violations. Its tasks depend on `python`, `pip` and `sqlite3`, "
        "which no task exports and which are external libraries rather than missing contracts")


@check("a declared layer order is obeyed, not improved on -- by running it on both controls",
       finding="P52")
def _():
    """Item 74. The skill states this rule and a live run broke half of it.

    `plan-layers` may decide WHICH layers exist -- item 31, a tier with no work is not a tier --
    and may not decide what ORDER they run in when the project declared one. Its Dependency
    Ordering section: *a contradiction, not an ordering. Report it and place the tasks by layer.*
    Two obligations. Against an inverted graph the run wrote `ordering_conflicts` at severity
    critical, naming both layers, and then emitted them resequenced into the buildable order.

    SUBSEQUENCE, NOT EQUALITY, because dropping an empty layer is expected.

    BOTH FIXTURES CAME FROM THE SAME DECLARED GRAPH, which is what makes the pair worth having:
    the only difference between them is the behaviour under test. `inverted/` obeyed the order,
    `inverted-halted/` did not.
    """
    script = os.path.join(SKILLS, "breakdown", "scripts", "check-layer-order.py")
    assert os.path.isfile(script), "check-layer-order.py does not exist"
    base = os.path.join(REPO, "tests", "fixture", "layering")

    def run(arm, *extra):
        return subprocess.run([sys.executable, script, os.path.join(base, arm), *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    # Negative control: same graph, order obeyed. A checker that refuses everything is useless.
    p = run("inverted")
    assert p.returncode == 0, (
        f"the arm that OBEYED the declared order was refused. Its emitted 0-setup, 3-backend, "
        f"4-foundation is a legal subsequence of 0,1,2,3,4 -- dropping empty layers is item 31:\n"
        f"{p.stderr[:400]}")

    # Positive control: same graph, order resequenced.
    p = run("inverted-halted")
    assert p.returncode == 1, (
        f"the arm that RESEQUENCED the declared graph passed. It emitted 0-setup, 4-foundation, "
        f"3-backend against a declared 0,1,2,3,4:\n{p.stdout[-400:]}")
    # Layers that were DROPPED, so they can only have come from the declared line. Asserting the
    # word "declared" instead was satisfied by the refusal's opening sentence -- two sites, and
    # the mutant that deleted the line passed. The site-counting rule, a fourth time.
    for want in ("1-integration", "2-frontend"):
        assert want in p.stderr, (
            f"the refusal does not print the declared order -- {want!r} is in it and nowhere "
            f"else. An operator has to see both sequences to know which rule was disobeyed:\n"
            f"{p.stderr[:400]}")
    assert "4-foundation -> 3-backend" in p.stderr or "4-foundation" in p.stderr, (
        f"the refusal does not print the emitted order:\n{p.stderr[:400]}")

    # No declared graph is not a violation -- the shipped default promises nothing about order
    # beyond its own definition, and refusing here would make the check fire on every ordinary run.
    p = run("sound")
    assert p.returncode == 0 and "no declared graph" in p.stdout, (
        f"a project with no architecture.md was judged against a graph it never declared:\n"
        f"{p.stdout[:300]}{p.stderr[:300]}")

    # The subsequence rule itself, rather than the two recorded outcomes: a dropped layer is
    # legal and a swapped pair is not, asserted on the function so a fixture cannot drift past it.
    import importlib.util
    spec = importlib.util.spec_from_file_location("clo", script)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    declared = ["0-a", "1-b", "2-c", "3-d"]
    assert m.is_subsequence(["0-a", "2-c"], declared)[0], "dropping a layer must be legal"
    assert m.is_subsequence(declared, declared)[0], "the identity must be legal"
    assert not m.is_subsequence(["2-c", "1-b"], declared)[0], "a swapped pair must not be legal"
    assert not m.is_subsequence(["0-a", "9-z"], declared)[0], "an undeclared layer must not be legal"

@check("item 21's authoring trajectory is what the probe still measures -- by running it",
       finding="P28")
def _():
    """V6. The after-measurement, asserted against its producer rather than written down.

    Item 21 owes a before-and-after on authoring size, and the plan now carries the whole
    trajectory as a table: six fixture versions, words, criteria and elements. **A figure in prose
    is exactly what went stale in `readers.md`** -- it claimed six candidates against a script
    printing seven -- so this one is compared to `probe-p1.py --baseline` on every row.

    Five of the six fixtures are frozen and cannot move. `schema-6` is current and can, which is
    the drift this catches: change the reference fixture and the recorded measurement stops being
    a measurement of it.

    IT DOES NOT ASSERT THE NUMBERS THEMSELVES. Pinning 394 or 763 here would make the check a
    second copy of the table, wrong in the same way at the same time. It asserts that the table
    and the script agree, whatever they say.
    """
    plan = open(os.path.join(REPO, "docs", "skills", "plugin-2.0-plan.md"),
                encoding="utf-8").read()
    section = plan.split("Taken 2026-09-08", 1)
    assert len(section) == 2, "the plan no longer records item 21's after-measurement"
    table = section[1].split("**The format change", 1)[0]

    rows = re.findall(r"\|\s*`(schema-\d)`\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|"
                      r"\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|", table)
    assert len(rows) >= 5, (
        f"only {len(rows)} rows parsed from item 21's trajectory table; it records six. A check "
        f"that reads fewer rows than the table holds is passing over its own subject")

    probe = os.path.join(REPO, "tests", "probe-p1.py")
    for version, words, criteria, elements in rows:
        fixture = os.path.join(REPO, "tests", "fixture", "prd", version, "staff-service")
        assert os.path.isdir(fixture), f"the plan cites {version}, which has no fixture"
        p = subprocess.run([sys.executable, probe, "--baseline", fixture],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert p.returncode == 0, f"probe-p1.py --baseline failed on {version}:\n{p.stderr[:300]}"
        m = re.search(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)", p.stdout, re.M)
        assert m, f"no TOTAL line for {version}:\n{p.stdout[-300:]}"
        actual = m.groups()
        assert actual == (words, criteria, elements), (
            f"item 21's table says {version} is {words}/{criteria}/{elements} words/criteria/"
            f"elements; the probe measures {'/'.join(actual)}. The recorded after-measurement has "
            f"stopped describing the fixture it was taken on -- re-take it, or the plan is "
            f"carrying a number nobody has re-run")

    # The judgement table, the same way. It is the half of item 21 that a script CAN take, and a
    # figure in prose is exactly what went stale in readers.md.
    # Scoped to the judgement table's own section. Splitting only on its END matched the SIZE
    # table above it, so every row compared a word count against a judgement count and the check
    # failed for the wrong reason -- a region without a start is not a region.
    jsplit = section[1].split("The other half of the sentence", 1)
    assert len(jsplit) == 2, "item 21 no longer records the author-judgement measurement"
    jtable = jsplit[1].split("This inverts", 1)[0]
    jrows = re.findall(r"\|\s*`(schema-\d)`[^|]*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|", jtable)
    assert len(jrows) >= 3, (
        f"only {len(jrows)} rows parsed from item 21's author-judgement table -- a check reading "
        f"fewer rows than the table holds is passing over its own subject")
    for version, expected in jrows:
        fixture = os.path.join(REPO, "tests", "fixture", "prd", version, "staff-service")
        p2 = subprocess.run([sys.executable, probe, "--decisions", fixture],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert p2.returncode == 0, f"--decisions failed on {version}: {p2.stderr[:300]}"
        m2 = re.search(r"^TOTAL\s+(\d+)", p2.stdout, re.M)
        assert m2, f"no TOTAL line from --decisions for {version}: {p2.stdout[-300:]}"
        assert m2.group(1) == expected, (
            f"item 21's judgement table says {version} demands {expected} author judgements; "
            f"the probe counts {m2.group(1)}. The measurement has stopped describing the schema "
            f"it was taken on")

@check("a CRD's schema contracts have a route into the task that implements them",
       finding="P53")
def _():
    """Item 75. One element, two producers -- and the second one was missing.

    The PRD path carries `<notes><data-model>` into a task's `<context>`: analyze-prd reads it
    into `data_models`, generate-tasks copies it, and the task format defines the element. The CRD
    path declares the same information as `<contract kind="schema">`, has it read by
    `crd-impact-analysis` -- and then hands the implementer a task carrying none of it.

    THE ROUTE IS THREE LINKS AND ALL THREE MUST HOLD. Asserting only that some file mentions
    `affected-contracts` would pass on a repository where any one of them is missing, which is the
    state this item found: crd-format.md and crd-impact-analysis both named it, and the two
    components between the document and the task did not.
    """
    def read(*parts):
        return open(os.path.join(REPO, *parts), encoding="utf-8", errors="replace").read()

    # 1. The producer: /breakdown's CRD extraction list must take the contracts into data_models.
    bd = read("skills", "breakdown", "SKILL.md")
    crd_extract = bd.split("**For CRD:**", 1)
    assert len(crd_extract) == 2, "breakdown/SKILL.md has no CRD extraction list"
    crd_extract = crd_extract[1].split("### Phase 3", 1)[0]
    assert "affected-contracts" in crd_extract and "data_models" in crd_extract, (
        "the CRD extraction list does not take <affected-contracts> into data_models. Without it "
        "the document's schema changes stop at analysis and never reach a task")

    # 2. The reader: analyze-prd must say where a CRD's data models come from.
    ap = read("skills", "breakdown-analyze-prd", "SKILL.md")
    assert "affected-contracts" in ap, (
        "breakdown-analyze-prd never mentions <affected-contracts>. It is the component that "
        "fills data_models, and on the CRD path it had no instruction at all")
    apf = prose(ap)
    assert "kind=" in ap and 'schema' in ap, "analyze-prd does not say which contract kind to read"

    # 3. The carrier: generate-tasks must carry them, under the same `touches` rule.
    gt = read("skills", "breakdown-generate-tasks", "SKILL.md")
    section = gt.split("The data model is copied, never inferred", 1)
    assert len(section) == 2, "generate-tasks has no data-model rule to widen"
    rule = section[1].split("###", 1)[0]
    assert "affected-contracts" in rule or "kind=\"schema\"" in rule, (
        "generate-tasks' data-model rule is still PRD-only. It is the component that writes "
        "<context><data-model>, so a producer upstream with no carrier here changes nothing")
    assert "touch" in prose(rule).lower(), (
        "the CRD half names no scoping rule. Carrying every contract in the document into every "
        "task is the failure `touches` exists to prevent")

    # 4. The format: one element, two sources, said in the spec that defines it.
    spec = read("skills", "breakdown", "references", "task-format-spec.md")
    dm = spec.split("- `data-model`:", 1)
    assert len(dm) == 2, "task-format-spec.md no longer defines `data-model`"
    dm = dm[1].split("\n- `", 1)[0]
    assert "CRD" in dm and "kind=\"schema\"" in dm, (
        "task-format-spec.md still defines <data-model> as the feature's own only. The element "
        "needed a second producer, not a second element, and the spec is where that is said")
    assert re.search(r"never inferred|Copied, never", dm), (
        "the widened definition dropped the copied-never-inferred rule, which is the half that "
        "keeps a second source from becoming a second guess")

    # 5. And the retired spellings must not be named as current anywhere that routes work.
    for name, text in (("breakdown/SKILL.md", bd),
                       ("breakdown-analyze-prd/SKILL.md", ap),
                       ("breakdown-generate-tasks/SKILL.md", gt)):
        for line in text.splitlines():
            if "affected-schemas" not in line and "affected-apis" not in line:
                continue
            assert re.search(r"retired|deprecat|until item 57|accepted on read", line, re.I), (
                f"{name} names <affected-schemas>/<affected-apis> without saying they are "
                f"retired: {line.strip()[:100]}. Item 57 replaced them with <affected-contracts>, "
                f"and a document pointing a reader at a section the producer stopped writing is "
                f"the same defect as a stale caller list")

@check("a CRD can declare architectural significance, and something reads it -- by running it",
       finding="P54")
def _():
    """Item 76. The element and its reader had to arrive together, which is not what P54 said.

    P54 was first written as *a live reader with no producer* -- `check-references.py` reads
    `<architecturally-significant>` and `check-gate.py` runs it for a CRD, so the consumer was
    said to be scanning for something the CRD schema never defined. **It was not scanning.**
    `main()` takes the CRD branch and returns before the significance screen, which iterates a PRD
    *directory*. The element had neither producer nor reader on this path, and adding the format
    half alone would have shipped exactly the defect the item exists to remove.

    So both halves are asserted, and the reader is asserted BY RUNNING IT rather than by finding
    the identifier in the source: the screen exists in that file either way, and what was wrong
    was which branch reaches it.
    """
    import shutil
    import tempfile

    crd_fmt = open(os.path.join(SKILLS, "crd", "references", "crd-format.md"),
                   encoding="utf-8").read()
    core = open(os.path.join(SCHEMA, "core.md"), encoding="utf-8").read()

    # The producer: the CRD format defines it, and defines it by citing the core (item 44).
    assert "architecturally-significant" in crd_fmt, (
        "crd-format.md does not define <architecturally-significant>. A refactor CRD is the "
        "document item 35 was written for")
    assert re.search(r"core\s*§?\s*8|#8-architecturally-significant", crd_fmt, re.I), (
        "crd-format.md defines the element without citing the core. Two definitions of one "
        "element is what item 44 exists to prevent -- it is how three <criterion> definitions "
        "came to disagree")
    assert re.search(r"^## 8\.", core, re.M), "core.md has no section 8 to cite"

    # The reader, by running it on a CRD that carries the flag.
    root = tempfile.mkdtemp(prefix="item76-")
    try:
        crd = os.path.join(root, "change.md")
        open(crd, "w", encoding="utf-8", newline="\n").write(
            "<crd>\n  <meta>\n    <slug>swap-session-store</slug>\n"
            "    <architecturally-significant because=\"cross-cutting\" criteria=\"1\"/>\n"
            "  </meta>\n</crd>\n")
        script = os.path.join(SKILLS, "breakdown", "scripts", "check-references.py")

        def run(path):
            return subprocess.run([sys.executable, script, path], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace")

        p = run(crd)
        assert "architecturally significant" in p.stdout.lower(), (
            f"check-references.py read a CRD carrying the flag and said nothing about it. The "
            f"significance screen iterates a PRD directory and the CRD branch returns before "
            f"reaching it, so the element would have had no reader on this path:\n{p.stdout[:400]}")

        # An unusable `because` must refuse, or the flag says a design step is warranted in a
        # kind nothing downstream can act on.
        open(crd, "w", encoding="utf-8", newline="\n").write(
            "<crd>\n  <meta>\n    <slug>swap-session-store</slug>\n"
            "    <architecturally-significant because=\"vibes\"/>\n  </meta>\n</crd>\n")
        p = run(crd)
        assert p.returncode == 1 and "not one of" in p.stderr, (
            f"a `because` outside core section 8's enum was accepted:\n{p.stderr[:300]}")

        open(crd, "w", encoding="utf-8", newline="\n").write(
            "<crd>\n  <meta>\n    <slug>swap-session-store</slug>\n"
            "    <architecturally-significant/>\n  </meta>\n</crd>\n")
        p = run(crd)
        assert p.returncode == 1 and "names no `because`" in p.stderr, (
            f"a flag with no `because` was accepted, so it claims a design step is warranted "
            f"without saying which kind:\n{p.stderr[:300]}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

@check("the gate's assertions reach a CRD, not only a PRD directory -- by running it",
       finding="P55")
def _():
    """Item 77. Two assertions that ran on one path and silently skipped the other.

    Found by the fifth live crossing -- the first CRD run since the fidelity plan began. Both
    have the same shape: `os.path.isdir(args.document)` treats *PRD directory* as the general
    case and lets a CRD, which is a FILE, fall through to a default.

      P55  blocking_gaps() was guarded by isdir AND read features_of_prd() unconditionally, so
           item 29's execution stop was unreachable on the CRD path. A change request carrying
           two <gap kind="decision"> -- which core section 6 makes a stop -- got `3 blocked OK`.

      P56  the CRD significance branch reported every finding under NOTE while check-gate.py
           filters for STALE, and it never resolved **Drives:** at all. A CRD declaring itself
           architecturally significant with nothing recording the decision got `2 significance
           OK`. That branch was added the previous day by item 76, which makes it the sharper
           of the two: the screen fired and nothing downstream acted on it.

    ASSERTED BY RUNNING THE GATE, because both defects were invisible to source inspection --
    the code was present and correct, and unreachable.
    """
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="item77-")
    try:
        crd_dir = os.path.join(root, "docs", "crd")
        adr = os.path.join(root, "docs", "architecture", "decisions")
        tasks = os.path.join(root, "tasks", "2-backend")
        for d in (crd_dir, adr, tasks):
            os.makedirs(d)

        crd = os.path.join(crd_dir, "swap-store.md")
        open(crd, "w", encoding="utf-8", newline="\n").write(
            "<crd>\n  <meta>\n    <slug>swap-store</slug>\n"
            "    <priority>must-have</priority>\n"
            "    <architecturally-significant because=\"cross-cutting\" criteria=\"1\"/>\n"
            "  </meta>\n  <gaps>\n"
            "    <gap id=\"1\" kind=\"decision\" raised=\"2026-09-09\">Undecided</gap>\n"
            "  </gaps>\n</crd>\n")
        # A record that drives something ELSE. `**Drives:**` takes a markdown link, not a bare
        # filename -- a first version of this fixture used a bare name, index_records parsed no
        # drives at all, and the undriven case then passed for the wrong reason.
        open(os.path.join(adr, "ADR-001-other.md"), "w", encoding="utf-8", newline="\n").write(
            "# ADR-001: Other\n**Status:** Accepted\n"
            "**Drives:** [Other](../../crd/other-thing.md)\n")
        open(os.path.join(tasks, "L2-001-swap.xml"), "w", encoding="utf-8", newline="\n").write(
            "<task><meta><id>L2-001</id>\n"
            "<source-feature slug=\"swap-store\" moscow=\"must-have\" satisfies-criteria=\"1\" "
            "requirement-level=\"P0\"/>\n</meta></task>\n")
        json.dump({"total_tasks": 1, "task_inventory": [{"id": "L2-001", "layer": "2-backend"}]},
                  open(os.path.join(root, "tasks", "manifest.json"), "w", encoding="utf-8"))

        p = subprocess.run(
            [sys.executable, os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py"),
             crd, os.path.join(root, "tasks")],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = p.stdout + p.stderr

        assert "blocking gap" in out, (
            f"the gate reported no blocking gap for a CRD carrying <gap kind=\"decision\">. "
            f"Core section 6 makes that a stop, and item 29's refusal was unreachable here "
            f"because blocking_gaps() was guarded on isdir:\n{out[:600]}")
        assert "swap-store" in out, (
            f"the blocking gap is not attributed by slug, so an operator cannot act on it:"
            f"\n{out[:400]}")
        assert "undriven" in out or "no decision record names it" in out, (
            f"the gate reported no undriven significance for a CRD that declares itself "
            f"significant with nothing driving it. The CRD branch printed under NOTE and the "
            f"gate filters for STALE:\n{out[:600]}")

        # And the driven case must NOT be reported, or the assertion is satisfied by a checker
        # that flags everything.
        open(os.path.join(adr, "ADR-002-store.md"), "w", encoding="utf-8", newline="\n").write(
            "# ADR-002: Store\n**Status:** Accepted\n"
            "**Drives:** [Swap](../../crd/swap-store.md)\n")
        p = subprocess.run(
            [sys.executable, os.path.join(SKILLS, "breakdown", "scripts", "check-gate.py"),
             crd, os.path.join(root, "tasks")],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert "no decision record names it" not in (p.stdout + p.stderr), (
            "a CRD whose significance IS driven by a decision record was still reported as "
            "undriven, so the check flags every flagged document and measures nothing")
    finally:
        shutil.rmtree(root, ignore_errors=True)

# ------------------------------------------------------------------------ runner

def main():
    with keep_awake():
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
