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

Usage:
    build-manifest.py <tasks-path> [--project-path <path>]   # rewrite manifest.json from disk
    build-manifest.py <tasks-path> --verify                  # report drift, exit 1 if any
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

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
        pass  # a malformed task file is item 4.x's problem, not this script's
    return fallback.replace("-", " ").capitalize()


def build_inventory(tasks_path):
    inventory = []
    for layer, task_id, fn, path in task_files(tasks_path):
        slug = TASK_RE.match(fn).group(2)
        inventory.append({
            "id": task_id,
            "name": task_name(path, slug),
            "layer": layer,
            # Relative to the tasks directory, so the manifest stays valid wherever that
            # directory is moved or mounted. Absolute or workspace-relative paths were both
            # tried before and neither survives the tasks tree being relocated.
            "file": f"{layer}/{fn}",
        })
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


def toolchain_version():
    """The plugin's declared version, so an artefact records what produced it (item 4.5)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(os.path.dirname(here)))  # scripts/breakdown/skills/
    pj = os.path.join(root, ".claude-plugin", "plugin.json")
    try:
        return json.load(open(pj, encoding="utf-8")).get("version")
    except Exception:
        return None


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

    print(f"manifest.json rebuilt: {len(inventory)} task(s) "
          + ", ".join(f"{k} {v}" for k, v in sorted(by_layer.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
