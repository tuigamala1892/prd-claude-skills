#!/usr/bin/env python3
"""Parse `architecture.md` and refuse a rule file that is present and broken (items 25, 28, 37).

`architecture.md` is the project's prescriptive artefact: the layer graph, the test policy, the
task file limit, the banned patterns and the scaffold. Five opinions that used to be vendored
into the plugin, where no project could override them (P18).

ABSENT IS FINE. PRESENT-AND-BROKEN MUST STOP THE RUN.

That asymmetry is the whole point of this script. A project with no `architecture.md` gets the
behaviour the toolchain has always had, and every PRD written before the file existed keeps
working -- so exit 0 with nothing found is a normal, common result.

But a rule file that is silently ignored is **worse than no rule file**, because the operator
believes the rule is in force. A typo in a `<layer depends-on=>` that quietly drops a dependency
edge, a `<rule>` with no `kind` that quietly enforces nothing, a bare `&` that stops the whole
block parsing -- each of those looks exactly like compliance from the outside. So anything this
script cannot read, it refuses, in the `resolve-output.sh` idiom: name the file, name the line,
generate nothing.

The bare-ampersand case is not hypothetical. `check-project-md.py` exists because
`project-context-finalizer` wrote `?tag=python&status=archived` into PROJECT.md on its first ever
run, the block stopped parsing, every consumer silently broke, and the run reported success.

WHAT IT CHECKS

  <layers>       ids unique within a block; every `depends-on` id known; the graph is acyclic;
                 every layer reachable from a root
  <banned>       every rule has a `kind` from the five and a `reason`; every kind has the
                 attributes it needs; a `content` pattern compiles as a regex
  <testing>      `default` is tdd or none
  <task-limits>  `default` and every `max-files` is a positive integer
  <scaffold>     a template other than `none` names a path
  <principles>   every principle has a unique id -- that id is what a PRD citation resolves to

WHAT IT DOES NOT CHECK

The registry set is **open** (item 25). Any `<*-registry>` is accepted, and one outside the six
known names is reported as a NOTE rather than refused -- closing the set here would re-vendor the
opinion one level down, which is the defect item 25 exists to correct. A registry with a typo'd
name is caught by having no reader, not by this script.

Glob syntax in `match=`, `from=`, `to=` and `path=` is not validated beyond being non-empty.

USAGE

    check-architecture.py <project-root> [--quiet] [--json]

  <project-root>  the directory holding architecture.md
  --json          emit the parsed rules on stdout, for a caller that needs the graph rather
                  than the verdict. Nothing else is printed
  --quiet         summary line only

EXIT CODES

  0  no architecture.md, or one that parses and validates
  1  REFUSED -- present and broken. Nothing should be generated
  2  usage error
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

BLOCK = re.compile(r"<architecture[\s>].*?</architecture>", re.S)
BARE_AMP = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)")

KINDS = {
    "import": ("match", "symbol"),
    "edge": ("from", "to"),
    "change": ("path", "action"),
    "content": ("match", "pattern"),
    "judgement": (),
}
ACTIONS = ("modify", "delete", "rename")
TEST_DEFAULTS = ("tdd", "none")
KNOWN_REGISTRIES = ("api-registry", "schema-registry", "event-registry",
                    "command-registry", "service-registry", "screen-registry")

FILENAME = "architecture.md"


class Refusal(Exception):
    """One reason the file cannot be trusted. Collected rather than raised one at a time."""


def positive_int(value):
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def check_layer_block(block, index, errors):
    """Validate one <layers> element. Returns the parsed layers for --json."""
    where = f"<layers>[{index}]"
    scope = block.get("applies-to")
    if scope is not None and not scope.strip():
        errors.append(f"{where}: applies-to is empty. Omit the attribute for an unscoped graph.")

    layers, seen = {}, []
    for el in block.findall("layer"):
        lid = (el.get("id") or "").strip()
        name = (el.get("name") or "").strip()
        if not lid:
            errors.append(f"{where}: a <layer> has no id.")
            continue
        if not name:
            errors.append(f"{where}: layer {lid!r} has no name.")
        if lid in layers:
            errors.append(f"{where}: layer id {lid!r} is declared twice. "
                          f"Ids are referenced by depends-on and must be unique in the block.")
            continue
        deps = [d.strip() for d in (el.get("depends-on") or "").split(",") if d.strip()]
        layers[lid] = {"id": lid, "name": name, "depends_on": deps}
        seen.append(lid)

    if not layers:
        errors.append(f"{where}: declares no <layer>. An empty graph plans nothing; "
                      f"remove the block to take the default graph.")
        return {"applies_to": scope, "layers": []}

    for lid, layer in layers.items():
        for dep in layer["depends_on"]:
            if dep not in layers:
                errors.append(f"{where}: layer {lid!r} depends on {dep!r}, which is not "
                              f"declared here. Ids are scoped to their block.")
            elif dep == lid:
                errors.append(f"{where}: layer {lid!r} depends on itself.")

    # Cycles, reported as the path rather than as a set -- a reader has to see the loop to fix it.
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {lid: WHITE for lid in layers}
    reported = []

    def visit(lid, path):
        colour[lid] = GREY
        for dep in layers[lid]["depends_on"]:
            if dep not in layers or dep == lid:
                continue
            if colour[dep] == GREY:
                cut = path[path.index(dep):] if dep in path else [dep]
                reported.append(" -> ".join(cut + [lid, dep]))
            elif colour[dep] == WHITE:
                visit(dep, path + [lid])
        colour[lid] = BLACK

    for lid in seen:
        if colour[lid] == WHITE:
            visit(lid, [])
    for cycle in dict.fromkeys(reported):
        errors.append(f"{where}: depends-on cycle: {cycle}. The graph must be acyclic.")

    # Reachability. With no cycles this cannot fail -- every non-root has a valid prerequisite,
    # so induction reaches a root. It is asserted anyway because it is the property that matters
    # (a stranded layer never runs) and because it names the empty-roots case plainly.
    roots = [lid for lid, l in layers.items() if not l["depends_on"]]
    if not roots and not reported:
        errors.append(f"{where}: no layer has an empty depends-on, so nothing can start.")
    reachable, frontier = set(roots), list(roots)
    while frontier:
        cur = frontier.pop()
        for lid, layer in layers.items():
            if lid not in reachable and cur in layer["depends_on"]:
                reachable.add(lid)
                frontier.append(lid)
    stranded = [lid for lid in seen if lid not in reachable]
    if stranded and not reported:
        errors.append(f"{where}: layer(s) {', '.join(sorted(stranded))} are not reachable from "
                      f"any root. Nothing would ever run them.")

    return {"applies_to": scope, "layers": [layers[lid] for lid in seen]}


def check_banned(block, errors):
    rules = []
    for i, el in enumerate(block.findall("rule")):
        where = f"<banned><rule>[{i}]"
        kind = (el.get("kind") or "").strip()
        reason = (el.get("reason") or "").strip()

        if not kind:
            errors.append(f"{where}: no kind. Every rule declares one of "
                          f"{', '.join(sorted(KINDS))} -- the kind decides both what detects "
                          f"the rule and whether it can refuse.")
            continue
        if kind not in KINDS:
            errors.append(f"{where}: kind {kind!r} is not one of {', '.join(sorted(KINDS))}.")
            continue
        if not reason:
            errors.append(f"{where} (kind={kind}): no reason. The reason is reported verbatim to "
                          f"whoever hit the rule; a bare rule number does not say what to do "
                          f"instead.")

        for attr in KINDS[kind]:
            if not (el.get(attr) or "").strip():
                errors.append(f"{where} (kind={kind}): missing {attr!r}, which this kind needs "
                              f"to be detectable at all.")

        if kind == "change":
            action = (el.get("action") or "").strip()
            if action and action not in ACTIONS:
                errors.append(f"{where}: action {action!r} is not one of "
                              f"{', '.join(ACTIONS)}.")
        if kind == "content":
            pattern = el.get("pattern") or ""
            if pattern:
                try:
                    re.compile(pattern)
                except re.error as e:
                    errors.append(f"{where}: pattern {pattern!r} is not a valid regex ({e}).")
        if kind == "judgement" and not "".join(el.itertext()).strip():
            errors.append(f"{where}: a judgement rule is prose for a model to read and this one "
                          f"has an empty body. There is nothing to weigh.")

        excepts = []
        for j, ex in enumerate(el.findall("except")):
            if not (ex.get("match") or "").strip():
                errors.append(f"{where}<except>[{j}]: no match.")
            if not (ex.get("reason") or "").strip():
                errors.append(f"{where}<except>[{j}]: no reason. An exception is reviewed once "
                              f"and lives here; an unexplained one is unreviewable.")
            excepts.append({"match": ex.get("match"), "reason": ex.get("reason")})

        rules.append({"kind": kind, "reason": reason,
                      "attrs": {k: v for k, v in el.attrib.items()
                                if k not in ("kind", "reason")},
                      "body": "".join(el.itertext()).strip() or None,
                      "excepts": excepts})
    return rules


def check_testing(block, errors):
    default = (block.get("default") or "").strip()
    if not default:
        errors.append("<testing>: no default. It is `tdd` or `none`, and three readers "
                      "(generate-tasks, review-tasks, execute-batch) branch on it.")
    elif default not in TEST_DEFAULTS:
        errors.append(f"<testing>: default {default!r} is not one of "
                      f"{', '.join(TEST_DEFAULTS)}.")
    policies = []
    for i, el in enumerate(block.findall("policy")):
        where = f"<testing><policy>[{i}]"
        if not (el.get("match") or "").strip():
            errors.append(f"{where}: no match.")
        if not (el.get("kind") or "").strip():
            errors.append(f"{where}: no kind.")
        policies.append({"match": el.get("match"), "kind": el.get("kind"),
                         "runner": el.get("runner") or block.get("runner")})
    return {"default": default, "runner": block.get("runner"), "policies": policies}


def check_task_limits(block, errors):
    default = block.get("default")
    n = positive_int(default)
    if default is None:
        errors.append("<task-limits>: no default.")
    elif n is None:
        errors.append(f"<task-limits>: default {default!r} is not a positive integer.")
    limits = []
    for i, el in enumerate(block.findall("limit")):
        where = f"<task-limits><limit>[{i}]"
        if not (el.get("match") or "").strip():
            errors.append(f"{where}: no match.")
        m = positive_int(el.get("max-files"))
        if el.get("max-files") is None:
            errors.append(f"{where}: no max-files.")
        elif m is None:
            errors.append(f"{where}: max-files {el.get('max-files')!r} is not a "
                          f"positive integer.")
        limits.append({"match": el.get("match"), "max_files": m})
    return {"default": n, "limits": limits}


def check_scaffold(el, errors):
    template = (el.get("template") or "").strip()
    path = (el.get("path") or "").strip()
    if not template:
        errors.append("<scaffold>: no template. Use template=\"none\" to state that there "
                      "is no scaffold.")
    elif template != "none" and not path:
        errors.append(f"<scaffold>: template {template!r} names no path. The template list is "
                      f"not an enum any more -- a name the toolchain does not ship needs a "
                      f"path to find it.")
    return {"template": template or None, "path": path or None}


def check_design_track(el, errors):
    """Item 38's switch. `enabled` is required and boolean -- absent is not the same as false.

    An absent ELEMENT means false, which is the shipped behaviour. An element present with no
    `enabled` is a project that meant to say something and did not, and guessing which way it
    meant would decide whether a gate stops a run.
    """
    raw = (el.get("enabled") or "").strip().lower()
    if raw not in ("true", "false"):
        errors.append(f"<design-track>: enabled={el.get('enabled')!r} is not `true` or `false`. "
                      f"It decides whether the gate between /breakdown and /execute stops, and "
                      f"a switch nobody set is not a switch set to off.")
    return {"enabled": raw == "true", "adr_dir": (el.get("adr-dir") or "").strip() or None}


def check_principles(block, errors):
    out, seen = [], set()
    for i, el in enumerate(block.findall("principle")):
        pid = (el.get("id") or "").strip()
        if not pid:
            errors.append(f"<principles><principle>[{i}]: no id. The id is what a PRD citation "
                          f"resolves against; without one the principle cannot be cited.")
            continue
        if pid in seen:
            errors.append(f"<principles>: principle id {pid!r} is declared twice. A citation "
                          f"would be ambiguous.")
            continue
        seen.add(pid)
        out.append({"id": pid, "text": " ".join("".join(el.itertext()).split())})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project_root")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root_dir = os.path.abspath(args.project_root)
    path = os.path.join(root_dir, FILENAME)

    if not os.path.isfile(path):
        # The common case, and not an error. Every project predating this file is here.
        if args.json:
            print(json.dumps({"present": False}, indent=2))
        elif not args.quiet:
            print(f"no {FILENAME} at {root_dir} -- defaults apply "
                  f"(layer-definitions.md, tdd, 3 files per task)")
        return 0

    text = open(path, encoding="utf-8", errors="replace").read()
    m = BLOCK.search(text)
    if not m:
        print(f"REFUSED: {path} has no <architecture> block. The prose is for a human; the "
              f"block is what the toolchain reads, and without it this file constrains "
              f"nothing.", file=sys.stderr)
        return 1

    block_text = m.group(0)
    bare = BARE_AMP.findall(block_text)
    try:
        root = ET.fromstring(block_text)
    except ET.ParseError as e:
        print(f"REFUSED: <architecture> in {path} is not well-formed: {e}", file=sys.stderr)
        if bare:
            print(f"  {len(bare)} bare ampersand(s) found, e.g. {bare[0]!r}. Write &amp;.",
                  file=sys.stderr)
        return 1

    errors, notes = [], []
    parsed = {"present": True, "path": path, "version": root.get("version"),
              "layer_blocks": [], "banned": [], "testing": None, "task_limits": None,
              "scaffold": None, "repo_structure": None, "principles": [], "registries": [],
              "design_track": {"enabled": False, "adr_dir": None}}

    rules_el = root.find("rules")
    if rules_el is not None:
        for i, el in enumerate(rules_el.findall("layers")):
            parsed["layer_blocks"].append(check_layer_block(el, i, errors))

        for el in rules_el.findall("banned"):
            parsed["banned"].extend(check_banned(el, errors))

        testing = rules_el.find("testing")
        if testing is not None:
            parsed["testing"] = check_testing(testing, errors)

        limits = rules_el.find("task-limits")
        if limits is not None:
            parsed["task_limits"] = check_task_limits(limits, errors)

        scaffold = rules_el.find("scaffold")
        if scaffold is not None:
            parsed["scaffold"] = check_scaffold(scaffold, errors)

        repo = rules_el.find("repo-structure")
        if repo is not None:
            parsed["repo_structure"] = (repo.text or "").strip() or None

        track = rules_el.find("design-track")
        if track is not None:
            parsed["design_track"] = check_design_track(track, errors)
    else:
        notes.append("no <rules> -- this file declares registries and/or principles only")

    principles_el = root.find("principles")
    if principles_el is not None:
        parsed["principles"] = check_principles(principles_el, errors)

    for child in root:
        if child.tag.endswith("-registry"):
            parsed["registries"].append({"name": child.tag, "entries": len(list(child))})
            if child.tag not in KNOWN_REGISTRIES:
                notes.append(f"registry <{child.tag}> is outside the six names the toolchain "
                             f"ships readers for. The set is open on purpose, but check the "
                             f"spelling -- an unread registry is silent.")
        elif child.tag not in ("rules", "principles", "meta"):
            notes.append(f"root element <{child.tag}> is not read by anything.")

    if errors:
        print(f"REFUSED: {path} is present and cannot be obeyed as written.", file=sys.stderr)
        print("", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        print("", file=sys.stderr)
        print("A rule file that is ignored is worse than none: the rule is not in force and "
              "the operator believes it is. Nothing was generated.", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(parsed, indent=2))
        return 0

    counts = []
    for b in parsed["layer_blocks"]:
        scope = f" applies-to={b['applies_to']}" if b["applies_to"] else ""
        counts.append(f"layers {len(b['layers'])}{scope}")
    if parsed["banned"]:
        refusing = sum(1 for r in parsed["banned"] if r["kind"] != "judgement")
        counts.append(f"banned {len(parsed['banned'])} "
                      f"({refusing} refusing, {len(parsed['banned']) - refusing} reporting)")
    if parsed["testing"]:
        counts.append(f"testing {parsed['testing']['default']}")
    if parsed["task_limits"]:
        counts.append(f"task-limits {parsed['task_limits']['default']}")
    if parsed["scaffold"]:
        counts.append(f"scaffold {parsed['scaffold']['template']}")
    if parsed["design_track"]["enabled"]:
        counts.append("design-track on")
    if parsed["repo_structure"]:
        counts.append(f"repo-structure {parsed['repo_structure']}")
    if parsed["principles"]:
        counts.append(f"principles {len(parsed['principles'])}")
    for r in parsed["registries"]:
        counts.append(f"{r['name']} {r['entries']}")

    print(f"architecture.md valid: " + (", ".join(counts) if counts else "nothing declared"))
    if not args.quiet:
        for n in notes:
            print(f"  NOTE: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
