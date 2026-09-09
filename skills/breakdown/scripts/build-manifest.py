#!/usr/bin/env python3
"""Build (or verify) manifest.json from the task files that actually exist.

The manifest used to be written from layer_plan.json -- the *plan* -- and never reconciled
with what generation produced. On the fixture that meant a manifest declaring 20 tasks and
naming six Layer 0 files, when generation had consolidated those six into four and renamed
every one of them:

    manifest claimed              on disk
    L0-001-create-directory-structure.xml   L0-001-init-project-structure.xml
    L0-002-create-config-files.xml          L0-002-init-git-and-python-env.xml
    L0-003-create-pytest-conftest.xml       L0-003-configure-database-and-app.xml
    L0-004-initialize-database.xml          L0-004-verify-setup.xml
    L0-005-create-fastapi-app.xml           --
    L0-006-verify-environment.xml           --

/execute then reported "18 of 20" for a run that did everything there was to do. The other
three layers matched only because generation happened to follow the plan one-for-one there.

The task files are the deliverable, so the task files are the source of truth. Plans get
revised during generation; that is the plan working, not failing.

It also fills the two fields F9 and item 4.5 are about:

  prd.project_path   -- /execute documents a fallback to this when --project-path is omitted,
                        but the manifest spec never included the field, so the fallback could
                        never fire and --project-path was effectively mandatory.
  toolchain_version  -- read from .claude-plugin/plugin.json, so a generated artefact records
                        which toolchain produced it.
  schema_version     -- how to READ this file, which is a different question from what wrote
                        it. A patch release moves toolchain_version and not this one (P28).

Usage:
    build-manifest.py <tasks-path> [--project-path <path>]   # rewrite manifest.json from disk
    build-manifest.py <tasks-path> --verify                  # report drift, exit 1 if any
"""

import importlib.util
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# One place decides what `a task file parses` means. Importing the owner's helpers is the same
# choice check-coverage.py made about `edges_of`, for the same reason: two answers to one
# question is how the interesting failures happen.
_tx_spec = importlib.util.spec_from_file_location(
    "check_task_xml", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "check-task-xml.py"))
_tx = importlib.util.module_from_spec(_tx_spec)
_tx_spec.loader.exec_module(_tx)
# ONLY the failure reader. This module already has a `task_files`, and it means something
# narrower -- the files matching TASK_RE, not every *.xml -- so importing over the name would
# silently hand a 4-tuple to a function expecting a path.
parse_failures = _tx.parse_failures

TASK_RE = re.compile(r"^(L\d+-\d+)-(.+)\.xml$", re.I)


def task_files(tasks_path):
    """Every task XML on disk, as (layer, task_id, filename, full path)."""
    out = []
    for layer in sorted(os.listdir(tasks_path)):
        layer_dir = os.path.join(tasks_path, layer)
        if not os.path.isdir(layer_dir):
            continue
        for fn in sorted(os.listdir(layer_dir)):
            m = TASK_RE.match(fn)
            if m:
                out.append((layer, m.group(1).upper(), fn, os.path.join(layer_dir, fn)))
    return out


def task_name(path, fallback):
    """The task's declared name, or a readable fallback derived from the filename."""
    try:
        root = ET.parse(path).getroot()
        for xp in ("meta/name", "name", "objective"):
            el = root.find(xp)
            if el is not None and (el.text or "").strip():
                return " ".join((el.text or "").split())
    except Exception:
        # Still tolerant HERE, deliberately: by the time this runs, main() has already refused
        # an unparseable set. This branch is now only reachable when a caller imports the
        # helper directly, and a name is not worth a second refusal (P64).
        pass
    return fallback.replace("-", " ").capitalize()


# Item 16's four elements, as the manifest spells them. The manifest is what every downstream
# reader sizes the work from, so an element that stops here is an element the coverage check
# (item 30) and the cross-check (item 49) can never see.
TRACEABILITY = ("source-feature", "moscow", "satisfies-criteria", "requirement-level")

# Strongest first. `wont-have` is in the list because a task may carry one and must be REFUSED
# rather than ranked -- /execute's preflight does that (item 20), and ranking it away here would
# hide the very thing that refusal exists to catch.
TIERS = ("must-have", "should-have", "could-have", "wont-have")
LEVELS = ("P0", "P1", "P2")


def _strongest(values, order):
    """The strongest of `values` by `order`, ignoring anything not in it."""
    known = [v for v in values if v in order]
    return min(known, key=order.index) if known else None


def source_edges(meta):
    """Every feature this task descends from, as edges. Item 65.

    A task legitimately covers criteria from more than one feature -- an end-to-end integration
    task is the ordinary case -- and until this element repeated, three live runs met one and
    invented three different workarounds (**P43**). The worst was the silent one: `L4-002` walked
    `save-link`, `tag-links` and `list-links` criterion 2 and declared `tag-links` alone. Nothing
    caught it, because item 30's coverage passes when the other criteria are covered by other
    tasks -- what is lost is that every consumer then believes the task belongs to one feature,
    so dropping that feature from scope silently takes the only end-to-end assertion of the other
    two with it.

    BOTH SHAPES ARE READ HERE, and only the new one is ever written (item 45's rule):

        new   <source-feature slug="save-link" moscow="must-have"
                              satisfies-criteria="1,4" requirement-level="P0"/>
        old   <source-feature>save-link</source-feature> plus sibling <moscow>,
              <satisfies-criteria> and <requirement-level> elements

    The siblings also fill in an attribute the new form omits, which is what makes a half-migrated
    task readable rather than an error: the edge is the unit, and the siblings are its defaults.
    """
    sib = {}
    for tag in TRACEABILITY[1:]:
        el = meta.find(tag)
        text = " ".join((el.text or "").split()) if el is not None else ""
        if text:
            sib[tag] = text

    edges = []
    for el in meta.findall("source-feature"):
        slug = (el.get("slug") or " ".join((el.text or "").split() if el.text else "")).strip()
        if not slug:
            continue
        edge = {"slug": slug}
        moscow = el.get("moscow") or sib.get("moscow")
        level = el.get("requirement-level") or sib.get("requirement-level")
        crit = el.get("satisfies-criteria") or sib.get("satisfies-criteria") or ""
        ids = [x.strip() for x in crit.split(",") if x.strip()]
        if moscow:
            edge["moscow"] = moscow.strip()
        if ids:
            edge["satisfies_criteria"] = ids
        if level:
            edge["requirement_level"] = level.strip()
        edges.append(edge)
    return edges


def edges_of(entry):
    """The features one MANIFEST ENTRY descends from, from either manifest shape.

    This is the reader's half of `source_edges`, and it lives here so the toolchain has one
    answer to *what does this task descend from* -- `check-coverage.py` and `check-scope.py`
    both load it from this file rather than re-deriving it, for the reason those two already
    load `select-features.py`: the interesting failures are the ones where two answers disagree.

    Schema 1.3 writes `source_features`; 1.2 and earlier wrote `source_feature` with
    `satisfies_criteria` beside it. A reader that handles one shape either misses every
    multi-feature task or breaks on every manifest written before item 65.
    """
    edges = entry.get("source_features")
    if edges:
        return [e for e in edges if e.get("slug")]
    slug = entry.get("source_feature")
    if not slug:
        return []
    edge = {"slug": slug}
    if entry.get("satisfies_criteria"):
        edge["satisfies_criteria"] = entry["satisfies_criteria"]
    for key in ("moscow", "requirement_level"):
        if entry.get(key):
            edge[key] = entry[key]
    return [edge]


def traceability(path):
    """Item 16's elements, read from <meta>. Absent keys are OMITTED, never defaulted.

    A Layer 0 task legitimately carries none of these -- it descends from the tech stack rather
    than from a feature -- so `absent` and `empty` have to stay distinguishable. Writing
    `"source_feature": null` for both would make a task nobody attributed look exactly like one
    that cannot be attributed, and item 30's shortfall report is built on telling them apart.

    Item 65 makes attribution a LIST, and the singular keys survive under one rule:

      `source_features`   every edge, always -- this is what a reader should use
      `source_feature`    the slug, and `satisfies_criteria` its ids -- **only when there is
                          exactly one edge**. A reader that knows only the singular key then
                          sees a multi-feature task as UNATTRIBUTED rather than attributed to
                          whichever edge happened to be first, which is P43's silent
                          misattribution reintroduced by the compatibility shim
      `moscow`, `requirement_level`  the STRONGEST across the edges, always. Both are filters,
                          and a task is built or not built as a unit, so the strongest
                          obligation it carries is the one a filter must see
    """
    out = {}
    try:
        meta = ET.parse(path).getroot().find("meta")
    except Exception:
        return out
    if meta is None:
        return out

    edges = source_edges(meta)
    if not edges:
        return out
    out["source_features"] = edges
    if len(edges) == 1:
        out["source_feature"] = edges[0]["slug"]
        if edges[0].get("satisfies_criteria"):
            out["satisfies_criteria"] = edges[0]["satisfies_criteria"]
    tier = _strongest([e.get("moscow") for e in edges], TIERS)
    level = _strongest([e.get("requirement_level") for e in edges], LEVELS)
    if tier:
        out["moscow"] = tier
    if level:
        out["requirement_level"] = level
    return out


def review_fields(path):
    """The two things a REVIEWER needs and the manifest has never carried (item 32).

    `<objective>` says what the task is for in a sentence, and `<files-to-create>` says where it
    lands. Both are already in the file this traversal opens; not reading them is what made the
    task set reviewable only by opening every task.
    """
    out = {}
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return out
    el = root.find("objective")
    if el is not None and (el.text or "").strip():
        out["objective"] = " ".join((el.text or "").split())
    files = [" ".join((f.text or "").split())
             for f in root.findall("files-to-create/file")
             if (f.text or "").strip()]
    if files:
        out["files"] = files
    return out


def build_inventory(tasks_path):
    inventory = []
    for layer, task_id, fn, path in task_files(tasks_path):
        slug = TASK_RE.match(fn).group(2)
        entry = {
            "id": task_id,
            "name": task_name(path, slug),
            "layer": layer,
            # Relative to the tasks directory, so the manifest stays valid wherever that
            # directory is moved or mounted. Absolute or workspace-relative paths were both
            # tried before and neither survives the tasks tree being relocated.
            "file": f"{layer}/{fn}",
        }
        entry.update(traceability(path))
        entry.update(review_fields(path))
        inventory.append(entry)
    return inventory


def resolve(tasks_path, stored):
    """Locate a manifest `file` entry on disk, whatever prefix convention wrote it.

    Older manifests stored workspace-relative paths (`docs/tasks/<slug>/<layer>/<f>.xml`),
    newer ones store `<layer>/<f>.xml`. Only the last two components are load-bearing, so
    match on those and the check works against either.
    """
    parts = (stored or "").replace("\\", "/").split("/")
    if len(parts) < 2:
        return None
    return os.path.join(tasks_path, parts[-2], parts[-1])


# The manifest's own shape. Bump it when a field is added, removed or changes meaning --
# never for a plugin release, which is what toolchain_version is for.
#
# 1.1 adds item 16's four traceability fields to each inventory entry. A reader written against
# 1.0 still works: the fields are additive and absent ones are omitted rather than nulled.
# 1.2 adds item 32's two review fields, `objective` and `files`, to each inventory entry.
# 1.3 adds item 65's `source_features` list. Additive: `moscow` and `requirement_level` keep
#     their meaning as the task's effective tier and level, and `source_feature` keeps its
#     meaning for the single-feature tasks that are all a 1.2 reader has ever seen -- it is
#     omitted, never guessed, where a task descends from more than one.
MANIFEST_SCHEMA_VERSION = "1.3"

# Item 32's rendered view, beside the manifest it is derived from.
SUMMARY_NAME = "tasks-summary.md"


def toolchain_version():
    """The plugin's declared version, so an artefact records what produced it (item 4.5)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))  # scripts/breakdown/skills/
    pj = os.path.join(root, ".claude-plugin", "plugin.json")
    try:
        return json.load(open(pj, encoding="utf-8")).get("version")
    except Exception:
        return None


def render_summary(inventory, by_layer, slug):
    """One row per task: what it came from, how important, what it does, where it lands.

    Item 32, and it changes no task format. Self-containment is right for the CONSUMER -- a task
    agent with no context needs the whole story in one file -- and it is what makes the SET
    unreviewable: every other item in this plan adds fidelity, and the review burden scales with
    it. This is the cheapest thing that keeps a human able to check the result at all.

    What it deliberately does not do is diff task text. What a reviewer needs to check is whether
    the criteria a task carries match the feature they came from, and item 17's verbatim ids turn
    that from a read-through into a set comparison -- which `check-coverage.py` already does
    mechanically. A summary that tried to do it in prose would be a second, worse answer.
    """
    lines = [f"# Task summary — {slug}" if slug else "# Task summary", ""]
    lines.append(f"**{len(inventory)} tasks** — "
                 + ", ".join(f"{k} {v}" for k, v in sorted(by_layer.items())))
    lines.append("")
    lines.append("Derived from the task files by `build-manifest.py`. Do not edit: it is "
                 "rewritten whenever the manifest is, and `--verify` fails when it has drifted.")
    lines.append("")
    lines.append("| Task | Layer | From | Tier | Criteria | Objective | Files |")
    lines.append("|---|---|---|---|---|---|---|")
    for e in inventory:
        # A Layer 0 task descends from the tech stack rather than from a feature, so `absent`
        # is a real answer here and is printed as one rather than as an empty cell.
        #
        # Every feature, one per line, with its own criteria on the matching line (item 65). A
        # reviewer reading one slug for a task that walks three is exactly the reader P43 was
        # about, and this table is the view item 32 built so the set could be checked without
        # opening every file.
        edges = e.get("source_features") or (
            [{"slug": e["source_feature"],
              "satisfies_criteria": e.get("satisfies_criteria")}] if e.get("source_feature")
            else [])
        origin = "<br>".join(x["slug"] for x in edges) or "—"
        crit = "<br>".join(", ".join(x.get("satisfies_criteria") or []) or "—"
                           for x in edges) or "—"
        tier = e.get("moscow") or "—"
        obj = e.get("objective") or e.get("name") or ""
        if len(obj) > 120:
            obj = obj[:117].rstrip() + "..."
        files = "<br>".join(f"`{f}`" for f in (e.get("files") or [])) or "—"
        # A pipe inside a cell would end the column early and silently reshape the table.
        def cell(s):
            return str(s).replace("|", "\\|")

        lines.append(f"| `{e['id']}` | {cell(e['layer'])} | {cell(origin)} | {cell(tier)} | "
                     f"{cell(crit)} | {cell(obj)} | {files} |")
    lines.append("")
    return "\n".join(lines)


def main():
    argv = sys.argv[1:]
    verify = "--verify" in argv
    project_path = None
    if "--project-path" in argv:
        i = argv.index("--project-path")
        if i + 1 < len(argv):
            project_path = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__.strip().split("Usage:")[-1], file=sys.stderr)
        return 2

    tasks_path = os.path.abspath(args[0])
    if not os.path.isdir(tasks_path):
        print(f"tasks path does not exist: {tasks_path}", file=sys.stderr)
        return 1

    manifest_path = os.path.join(tasks_path, "manifest.json")
    existing = {}
    if os.path.isfile(manifest_path):
        try:
            existing = json.load(open(manifest_path, encoding="utf-8"))
        except Exception as e:
            print(f"existing manifest.json does not parse ({e}); rebuilding", file=sys.stderr)

    # P64. This script's assertion is *the manifest matches the files on disk*, and a manifest
    # that silently omits a file it could not read does not match them. It does NOT re-implement
    # the check -- it names the script that owns it, the way `check-status.py` names
    # `check-rename.py` for a dangling index entry. Every reader below this one reports a
    # different symptom for the same cause, so the run stops here instead.
    unparseable = parse_failures([t[3] for t in task_files(tasks_path)],
                                 tasks_path)
    if unparseable:
        for rel, msg in unparseable:
            print(f"  MALFORMED  {rel}: {msg}", file=sys.stderr)
        print(f"REFUSED: {len(unparseable)} task file(s) do not parse, so a manifest built now "
              f"would omit them silently.\n         `check-task-xml.py {args[0]}` owns this "
              f"assertion and prints the position of each.", file=sys.stderr)
        return 1

    inventory = build_inventory(tasks_path)
    by_layer = {}
    for e in inventory:
        by_layer[e["layer"]] = by_layer.get(e["layer"], 0) + 1

    if verify:
        problems = []
        old_inv = existing.get("task_inventory", [])
        old_ids = [e.get("id") for e in old_inv]
        new_ids = [e["id"] for e in inventory]

        declared = existing.get("summary", {}).get("total_tasks")
        if declared is not None and declared != len(inventory):
            problems.append(f"summary.total_tasks says {declared}, {len(inventory)} task files exist")

        # F9: /execute documents a fallback to manifest.prd.project_path. Without the field
        # the fallback can never fire, so --project-path becomes mandatory in practice.
        if not (existing.get("prd") or {}).get("project_path"):
            problems.append("prd.project_path is absent -- /execute's documented fallback "
                            "cannot fire, making --project-path mandatory (F9)")

        for e in old_inv:
            full = resolve(tasks_path, e.get("file"))
            if full is None or not os.path.isfile(full):
                problems.append(f"{e.get('id')}: manifest names a file that does not exist "
                                f"-- {e.get('file')}")

        for tid in new_ids:
            if tid not in old_ids:
                problems.append(f"{tid}: task file exists but is absent from the manifest")

        # Item 32's summary is derived, so a stale one is drift like any other. It is checked
        # here rather than in a script of its own because it comes off this traversal: a second
        # walker would be a second answer to "what tasks exist".
        summary_path = os.path.join(tasks_path, SUMMARY_NAME)
        wanted = render_summary(inventory, by_layer,
                                (existing.get("prd") or {}).get("slug"))
        if not os.path.isfile(summary_path):
            problems.append(f"{SUMMARY_NAME} is absent -- the task set can only be reviewed by "
                            f"opening every task (item 32)")
        elif open(summary_path, encoding="utf-8").read() != wanted:
            problems.append(f"{SUMMARY_NAME} does not match the task files -- it is derived, so "
                            f"rebuild it rather than editing it")

        if problems:
            print(f"manifest.json disagrees with the {len(inventory)} task files on disk:",
                  file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            print("\nRun without --verify to rebuild it from the files.", file=sys.stderr)
            return 1
        print(f"manifest.json matches the {len(inventory)} task files on disk")
        return 0

    manifest = dict(existing)
    manifest["task_inventory"] = inventory
    summary = dict(existing.get("summary", {}))
    summary["total_tasks"] = len(inventory)
    summary["tasks_per_layer"] = by_layer
    manifest["summary"] = summary

    version = toolchain_version()
    if version:
        manifest["toolchain_version"] = version

    # Two versions, and they answer different questions (P28, item 43). `toolchain_version` is
    # provenance -- what produced this file. `schema_version` is compatibility -- how to read
    # it. A patch release moves the first and not the second, which is exactly why a provenance
    # stamp cannot answer a compatibility question, and why item 24's comparison reads this one.
    manifest["schema_version"] = MANIFEST_SCHEMA_VERSION

    # F9: record the target so /execute's documented fallback can actually fire. Prefer the
    # explicit argument, then whatever the manifest already knows, then the older key name
    # this field used to hide behind.
    prd = dict(existing.get("prd") or {})
    resolved = project_path or prd.get("project_path") or existing.get("output_dir")
    if resolved:
        prd["project_path"] = resolved
    for key, src in (("slug", "prd_slug"), ("name", "prd_name")):
        if src in existing and key not in prd:
            prd[key] = existing[src]
    if prd:
        manifest["prd"] = prd

    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    # Item 32. Written from the same inventory, in the same pass, so the two cannot disagree.
    summary_path = os.path.join(tasks_path, SUMMARY_NAME)
    with open(summary_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_summary(inventory, by_layer, prd.get("slug")))

    print(f"manifest.json rebuilt: {len(inventory)} task(s) "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_layer.items()))
          + f"; {SUMMARY_NAME} rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
