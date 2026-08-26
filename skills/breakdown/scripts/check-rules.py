#!/usr/bin/env python3
"""Enforce `architecture.md`'s `<banned>` rules and `<task-limits>` (item 56, P16/P35).

Item 28 gave a project somewhere to declare its constraints and item 37 put `<rules>` in the
exit-code column. **Neither named an enforcer**, so both rows stood for nothing: a project could
declare that contexts never call each other over HTTP, and the toolchain would generate a task
saying "call the billing service over HTTP" and merge the code that did it.

TWO CHECKPOINTS, AND THE KIND DECIDES WHICH APPLY

  --mode review   one generated task, at /breakdown time. Kinds `import` and `content`, checked
                  against what the task SPECIFIES. Free, because no code exists yet: a task
                  saying "call the billing service over HTTP" under a rule banning cross-context
                  calls is wrong before anybody writes a line. Also enforces <task-limits>.

  --mode verify   one implemented task, in its worktree, before merge. All five kinds, checked
                  against the code and the diff. Costs a rejected task, which is still cheaper
                  than a merge.

`edge` and `change` cannot fire at review: there is no dependency graph and no diff until
something is implemented.

WHAT REFUSES AND WHAT ONLY REPORTS

  import      forbidden symbol x path glob                        REFUSES
  content     regex over file contents at a path                   REFUSES
  edge        a module under X importing from Y                    REFUSES   (verify only)
  change      the diff against the base branch                     REFUSES   (verify only)
  judgement   prose for a model to weigh                           REPORTS, always exit 0

`judgement` is a prose guard and is labelled as one. S3 says prose guards get weighed rather
than obeyed, so these never block a merge. A rule that reports is useful; a rule that claims to
enforce and does not is exactly what P16 is about.

EXCEPTIONS BELONG TO THE RULE, NEVER TO THE TASK

`<except match= reason=>` is declared on the rule, reviewed once, and applies consistently. There
is deliberately no per-task exemption: a component that can exempt itself makes the check
advisory with extra steps, and every candidate producer inside the pipeline is disqualified by
that same argument. A genuine one-off is answered by a human editing the rule, which is the slow
route on purpose -- if the rule truly should not apply, editing it is the correct change, and if
it should apply, the task is wrong.

WHAT `edge` DOES NOT CATCH, AND WHY IT IS STILL WORTH HAVING

Resolving an import to a file is language-specific, and this script is not a compiler. Three
forms resolve, and they cover the cases that matter:

  ./x, ../x     relative, resolved against the importing file
  a/b/c         treated as repo-relative
  a.b.c         converted to a/b/c and CONFIRMED against the worktree -- it resolves only if
                a/b/c, a/b/c.py or a/b/c/__init__.py actually exists

The dotted form is not optional: `from services.b.api import thing` is how a Python file crosses
a service boundary, and an `edge` rule that understood only slashes would have missed the most
common form of the violation it exists to catch.

What still does not resolve is a package name that does not mirror the directory layout -- a Java
`com.example.billing`, or a Python module reached through a path manipulation. Those are left
unmatched rather than guessed at, and a `change` rule with no `--base` says UNRESOLVED and
states that it is not in force, rather than passing quietly.

A rule that says what it cannot see beats one that quietly sees nothing.

USAGE

    check-rules.py --rules <path> --mode review --task <task.xml>
    check-rules.py --rules <path> --mode verify --worktree <dir> [--base <ref>]

  --rules      architecture.json (preferred -- already validated) or architecture.md
  --base       the branch the worktree was cut from. Required for `change` rules
  --quiet      summary line only

EXIT CODES

  0  no refusing violation. Judgement findings may have been reported
  1  at least one refusing violation. The task must not merge as it stands
  2  usage error, or rules that cannot be read
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

REFUSING = ("import", "content", "edge", "change")
REVIEW_KINDS = ("import", "content")

# Import forms across the languages this toolchain scaffolds. Deliberately broad: a missed
# import is a rule not enforced, and a spurious one is visible in the report with its line.
IMPORT_PATTERNS = (
    re.compile(r"^\s*from\s+([.\w/]+)\s+import\b", re.M),          # python
    re.compile(r"^\s*import\s+([.\w/]+)", re.M),                    # python / go / java
    re.compile(r"""\bfrom\s+['"]([^'"]+)['"]""", re.M),             # js/ts
    re.compile(r"""\brequire\(\s*['"]([^'"]+)['"]\s*\)""", re.M),   # js
    re.compile(r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)""", re.M), # dynamic js / go
)

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox"}


class Finding:
    def __init__(self, kind, reason, where, detail, refuses):
        self.kind, self.reason = kind, reason
        self.where, self.detail, self.refuses = where, detail, refuses

    def line(self):
        head = "REFUSED " if self.refuses else "REPORT  "
        return f"  {head} [{self.kind}] {self.where}\n           {self.detail}\n           {self.reason}"


def matches(path, glob):
    """Glob match on a repo-relative POSIX path, tolerant of the `dir/*/` idiom."""
    if not glob:
        return False
    p = path.replace(os.sep, "/")
    g = glob.replace(os.sep, "/")
    if fnmatch.fnmatch(p, g):
        return True
    # `services/*/` means "anything under a direct child of services"
    if g.endswith("/"):
        return fnmatch.fnmatch(p, g + "**") or fnmatch.fnmatch(p, g.rstrip("/"))
    if "**" not in g and fnmatch.fnmatch(p, g + "/**"):
        return True
    return False


def excepted(rule, path):
    for ex in rule.get("excepts") or []:
        if matches(path, ex.get("match")):
            return ex
    return None


def load_rules(path):
    """Accept architecture.json (already validated) or architecture.md (parse it here)."""
    if not os.path.isfile(path):
        return None, f"no rules file at {path}"
    text = open(path, encoding="utf-8", errors="replace").read()
    if path.endswith(".json"):
        try:
            return json.loads(text), None
        except Exception as e:
            return None, f"{path} is not valid JSON: {e}"

    m = re.search(r"<architecture[\s>].*?</architecture>", text, re.S)
    if not m:
        return None, f"{path} has no <architecture> block"
    try:
        root = ET.fromstring(m.group(0))
    except ET.ParseError as e:
        return None, f"<architecture> in {path} is not well-formed: {e}"

    out = {"banned": [], "task_limits": None}
    rules_el = root.find("rules")
    if rules_el is None:
        return out, None
    for banned in rules_el.findall("banned"):
        for el in banned.findall("rule"):
            out["banned"].append({
                "kind": (el.get("kind") or "").strip(),
                "reason": (el.get("reason") or "").strip(),
                "attrs": {k: v for k, v in el.attrib.items() if k not in ("kind", "reason")},
                "body": "".join(el.itertext()).strip() or None,
                "excepts": [{"match": x.get("match"), "reason": x.get("reason")}
                            for x in el.findall("except")],
            })
    limits = rules_el.find("task-limits")
    if limits is not None:
        out["task_limits"] = {
            "default": int(limits.get("default") or 3),
            "limits": [{"match": l.get("match"), "max_files": int(l.get("max-files") or 0)}
                       for l in limits.findall("limit")],
        }
    return out, None


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            full = os.path.join(dirpath, name)
            yield full, os.path.relpath(full, root).replace(os.sep, "/")


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def line_of(text, index):
    return text.count("\n", 0, index) + 1


# ------------------------------------------------------------------ review mode

def task_files(task_xml):
    """The paths a task declares it will create or modify."""
    paths = []
    for m in re.finditer(r"<file[^>]*>(.*?)</file>", task_xml, re.S):
        paths.append(m.group(1).strip())
    for m in re.finditer(r"<files-to-create>(.*?)</files-to-create>", task_xml, re.S):
        for line in m.group(1).splitlines():
            line = line.strip().lstrip("-").strip().strip("`")
            if line and "/" in line and "<" not in line:
                paths.append(line)
    seen, out = set(), []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            out.append(p.replace(os.sep, "/"))
    return out


def review(rules, task_path):
    findings = []
    text = read_text(task_path)
    declared = task_files(text)
    name = os.path.basename(task_path)

    for rule in rules.get("banned", []):
        kind = rule["kind"]
        if kind == "judgement":
            findings.append(Finding(kind, rule["reason"], name,
                                    f"for a reviewer to weigh: {rule.get('body') or ''}", False))
            continue
        if kind not in REVIEW_KINDS:
            continue
        glob = rule["attrs"].get("match")
        scoped = [p for p in declared if matches(p, glob)]
        if not scoped:
            continue

        if kind == "import":
            symbols = rule["attrs"].get("symbol") or ""
            pattern = re.compile(r"\b(" + symbols + r")\b")
            for m in pattern.finditer(text):
                covered = [p for p in scoped if not excepted(rule, p)]
                if not covered:
                    continue
                findings.append(Finding(
                    kind, rule["reason"], f"{name}:{line_of(text, m.start())}",
                    f"the task specifies {m.group(1)!r} and touches {', '.join(covered)}", True))
                break
        elif kind == "content":
            pattern = re.compile(rule["attrs"].get("pattern") or "(?!)")
            for m in pattern.finditer(text):
                covered = [p for p in scoped if not excepted(rule, p)]
                if not covered:
                    continue
                findings.append(Finding(
                    kind, rule["reason"], f"{name}:{line_of(text, m.start())}",
                    f"the task specifies {m.group(0)!r} for {', '.join(covered)}", True))
                break

    # <task-limits>, enforced where the count actually is rather than in prose.
    limits = rules.get("task_limits")
    if limits and declared:
        effective = limits["default"]
        why = "default"
        for lim in limits["limits"]:
            if any(matches(p, lim["match"]) for p in declared):
                effective, why = lim["max_files"], f"scoped to {lim['match']}"
                break
        if len(declared) > effective:
            findings.append(Finding(
                "task-limits", f"limit is {effective} ({why})", name,
                f"declares {len(declared)} files: {', '.join(declared)}", True))
    return findings


# ------------------------------------------------------------------ verify mode

def git(worktree, *args):
    try:
        p = subprocess.run(["git", "-C", worktree, *args], capture_output=True,
                           text=True, timeout=120)
    except Exception:
        return None
    return p.stdout if p.returncode == 0 else None


def resolve_import(target, from_rel, worktree=None):
    """Best effort: a target that looks like a path becomes one. Otherwise None.

    The dotted case is not optional. `from services.b.api import thing` is how a Python file
    imports across a service boundary, and an `edge` rule that only understood slashes would
    have missed the single most common form of the violation it exists to catch -- passing
    silently, which is the failure mode this whole plan is about.

    So a dotted target is converted to a path and **confirmed against the worktree**: if
    `services/b/api.py`, `services/b/api/` or `services/b/api/__init__.py` exists, the import
    resolves there. If none exists it is a package name that does not mirror the layout, and
    `None` is the honest answer rather than a guess.
    """
    if target.startswith("."):
        base = os.path.dirname(from_rel)
        return os.path.normpath(os.path.join(base, target)).replace(os.sep, "/")
    if "/" in target:
        return target.strip("/")
    if "." in target and worktree:
        candidate = target.replace(".", "/")
        for probe in (candidate, candidate + ".py", candidate + "/__init__.py"):
            if os.path.exists(os.path.join(worktree, probe.replace("/", os.sep))):
                return candidate
    return None


def verify(rules, worktree, base):
    findings = []
    files = list(walk(worktree))

    changed = None
    if base:
        raw = git(worktree, "diff", "--name-status", f"{base}...HEAD")
        if raw is not None:
            changed = []
            for line in raw.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    changed.append((parts[0][0], parts[-1].replace(os.sep, "/")))

    for rule in rules.get("banned", []):
        kind, reason = rule["kind"], rule["reason"]

        if kind == "judgement":
            findings.append(Finding(kind, reason, "worktree",
                                    f"for a model to weigh: {rule.get('body') or ''}", False))
            continue

        if kind == "import":
            symbols = rule["attrs"].get("symbol") or "(?!)"
            glob = rule["attrs"].get("match")
            pattern = re.compile(r"\b(" + symbols + r")\b")
            for full, rel in files:
                if not matches(rel, glob) or excepted(rule, rel):
                    continue
                text = read_text(full)
                for p in IMPORT_PATTERNS:
                    for m in p.finditer(text):
                        if pattern.search(m.group(1)):
                            findings.append(Finding(
                                kind, reason, f"{rel}:{line_of(text, m.start())}",
                                f"imports {m.group(1)!r}", True))

        elif kind == "content":
            glob = rule["attrs"].get("match")
            pattern = re.compile(rule["attrs"].get("pattern") or "(?!)")
            for full, rel in files:
                if not matches(rel, glob) or excepted(rule, rel):
                    continue
                text = read_text(full)
                m = pattern.search(text)
                if m:
                    findings.append(Finding(
                        kind, reason, f"{rel}:{line_of(text, m.start())}",
                        f"matches {m.group(0)!r}", True))

        elif kind == "edge":
            src, dst = rule["attrs"].get("from"), rule["attrs"].get("to")
            for full, rel in files:
                if not matches(rel, src) or excepted(rule, rel):
                    continue
                text = read_text(full)
                for p in IMPORT_PATTERNS:
                    for m in p.finditer(text):
                        target = resolve_import(m.group(1), rel, worktree)
                        if target is None:
                            continue
                        if not matches(target, dst):
                            continue
                        # Same unit importing itself is not a crossing. `services/*/` means
                        # "another service", so compare the matched unit prefix.
                        if src.rstrip("/*") and target.split("/")[:2] == rel.split("/")[:2]:
                            continue
                        findings.append(Finding(
                            kind, reason, f"{rel}:{line_of(text, m.start())}",
                            f"imports {target!r}, which is under {dst!r}", True))

        elif kind == "change":
            glob = rule["attrs"].get("path")
            action = (rule["attrs"].get("action") or "modify").lower()
            wanted = {"modify": "M", "delete": "D", "rename": "R"}.get(action, "M")
            if changed is None:
                findings.append(Finding(
                    kind, reason, "diff",
                    f"UNRESOLVED: no --base given, so the diff this rule is about was never "
                    f"computed. The rule is NOT in force for this run", False))
                continue
            for status, path in changed:
                if status == wanted and matches(path, glob) and not excepted(rule, path):
                    past = {"modify": "modified", "delete": "deleted",
                            "rename": "renamed"}.get(action, action)
                    findings.append(Finding(
                        kind, reason, path, f"{past} in this diff, which this rule forbids",
                        True))
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rules", required=True)
    ap.add_argument("--mode", required=True, choices=("review", "verify"))
    ap.add_argument("--task")
    ap.add_argument("--worktree")
    ap.add_argument("--base")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rules, err = load_rules(os.path.abspath(args.rules))
    if err:
        # Absent rules is not this script's call to make -- the caller decides whether a project
        # with no architecture.md should run it at all. Reaching here with an unreadable file is
        # a usage error, and silently passing would be the failure item 28 describes.
        print(f"REFUSED: {err}", file=sys.stderr)
        return 2

    if args.mode == "review":
        if not args.task or not os.path.isfile(args.task):
            print("REFUSED: --mode review needs --task <task.xml>", file=sys.stderr)
            return 2
        findings = review(rules, os.path.abspath(args.task))
        where = os.path.basename(args.task)
    else:
        if not args.worktree or not os.path.isdir(args.worktree):
            print("REFUSED: --mode verify needs --worktree <dir>", file=sys.stderr)
            return 2
        findings = verify(rules, os.path.abspath(args.worktree), args.base)
        where = args.worktree

    refusing = [f for f in findings if f.refuses]
    reporting = [f for f in findings if not f.refuses]

    for f in refusing:
        print(f.line(), file=sys.stderr)
    for f in reporting:
        print(f.line())

    total_rules = len(rules.get("banned", []))
    print(f"{args.mode}: {total_rules} rule(s) against {where} -- "
          f"{len(refusing)} refusing, {len(reporting)} reporting")

    if refusing:
        print("", file=sys.stderr)
        print("Each reason above is quoted from architecture.md verbatim: it says what to do "
              "instead. If a rule should not apply here, edit the rule -- there is no per-task "
              "exemption, deliberately.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
