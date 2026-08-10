"""Grade the Phase 0 probes and print the table the findings were read off.

Detection signals, chosen after iteration 1 showed the obvious ones were wrong:

* fork    -- `toolUseResult.status == "forked"` on the Skill tool result.
             NOT `isSidechain`, which stays False even for forked skill execution.
* models  -- the `modelUsage` map in the `claude -p --output-format json` result.
             Covers forked and subagent work, which never reaches the parent
             transcript. Asking a model to name itself is unreliable.
* inline  -- a `Write` in the PARENT transcript. When a skill forks, the parent
             shows only `Skill`; seeing `Write` there means the body ran inline.

Assertions are phrased as the hypothesis under test and graded identically on both
arms, so `with_skill` beating `without_skill` means the frontmatter key did
something, and the two arms tying means it did nothing.
"""

import argparse
import json
import os

MARKER = "MARKER-AGENT-7734"
SESSION_MODEL = "claude-sonnet-5"


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-probes")


def analyse(rundir):
    f = {"skill_tool_used": False, "write_in_parent": False, "forked": False,
         "tools": [], "models": [], "tool_errors": []}

    tp = os.path.join(rundir, "transcript.jsonl")
    if os.path.isfile(tp):
        for line in open(tp, encoding="utf-8", errors="replace"):
            if '"status": "forked"' in line or '"status":"forked"' in line:
                f["forked"] = True
            try:
                d = json.loads(line)
            except Exception:
                continue
            for b in ((d.get("message") or {}).get("content") or []):
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    f["tools"].append(b.get("name"))
                    if b.get("name") == "Skill":
                        f["skill_tool_used"] = True
                    if b.get("name") in ("Write", "Edit"):
                        f["write_in_parent"] = True
                if b.get("type") == "tool_result" and b.get("is_error"):
                    f["tool_errors"].append(str(b.get("content"))[:300])

    raw = os.path.join(rundir, "raw.json")
    if os.path.isfile(raw):
        try:
            f["models"] = sorted((json.load(open(raw, encoding="utf-8"))
                                  .get("modelUsage") or {}).keys())
        except Exception:
            pass

    outdir = os.path.join(rundir, "outputs")
    files = sorted(os.listdir(outdir)) if os.path.isdir(outdir) else []
    body = ""
    for fn in files:
        try:
            body += open(os.path.join(outdir, fn), encoding="utf-8", errors="replace").read()
        except Exception:
            pass
    f.update(files=files, output_text=body, wrote_file=bool(files),
             token_present="SKILLTOKEN-" in body, marker_present=MARKER in body)
    f["extra_models"] = [m for m in f["models"] if SESSION_MODEL not in m]
    return f


def assertions_for(question, f):
    a = [("Probe validity: the skill was genuinely invoked via the Skill tool",
          f["skill_tool_used"], f"parent tools: {sorted(set(f['tools'])) or 'none'}")]

    if question == "U1":
        a += [
            ("`context: fork` took effect -- the skill ran in its own forked context",
             f["forked"], f"forked={f['forked']}"),
            ("The skill body did NOT run inline (no Write in the parent transcript)",
             not f["write_in_parent"], f"Write/Edit in parent: {f['write_in_parent']}"),
            ("The declared tool restriction took effect -- no file was written",
             not f["wrote_file"], f"files: {f['files'] or 'none'}"),
        ]
    elif question == "U2":
        a += [
            ("The skill forked into its declared agent", f["forked"], f"forked={f['forked']}"),
            (f"The declared agent's prompt took effect ({MARKER} in the written file)",
             f["marker_present"], f"marker={f['marker_present']}"),
            ("The agent's declared model actually ran (a non-session model appears)",
             bool(f["extra_models"]), f"models: {f['models'] or 'none'}"),
        ]
    elif question == "F6":
        a += [
            ("The skill forked into its own context", f["forked"], f"forked={f['forked']}"),
            ("Probe validity: the skill body ran to completion (file produced)",
             f["wrote_file"], f"files: {f['files'] or 'none'}"),
            ("A declared model overrode the session model",
             bool(f["extra_models"]),
             f"models: {f['models'] or 'none'}; non-session: {f['extra_models'] or 'none'}"),
        ]
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iteration", type=int, choices=(1, 2, 3), required=True)
    ap.add_argument("--workdir", default=default_workdir())
    args = ap.parse_args()

    ws = os.path.join(args.workdir, f"iteration-{args.iteration}")
    runs = json.load(open(os.path.join(args.workdir, f"runs{args.iteration}.json"),
                          encoding="utf-8"))

    print(f"{'skill under test':<26}{'arm':<15}{'models used':<40}"
          f"{'fork':<7}{'wrote':<7}{'parent tools'}")
    print("-" * 125)

    seen, graded = set(), 0
    for r in runs:
        key = (r["eval_name"], r["configuration"])
        if key in seen:
            continue
        seen.add(key)
        rundir = os.path.join(ws, r["eval_name"], r["configuration"])
        if not os.path.isdir(rundir):
            continue

        f = analyse(rundir)
        exp = [{"text": t, "passed": bool(p), "evidence": e}
               for t, p, e in assertions_for(r["question"], f)]
        passed = sum(e["passed"] for e in exp)
        json.dump({"expectations": exp,
                   "summary": {"passed": passed, "failed": len(exp) - passed,
                               "total": len(exp),
                               "pass_rate": round(passed / len(exp), 3) if exp else 0.0},
                   "observed": {k: f[k] for k in
                                ("forked", "models", "extra_models", "files",
                                 "skill_tool_used", "write_in_parent")}},
                  open(os.path.join(rundir, "grading.json"), "w", encoding="utf-8"), indent=2)
        graded += 1

        print(f"{r['skill']:<26}{r['configuration']:<15}"
              f"{', '.join(f['models']) or '-':<40}"
              f"{'YES' if f['forked'] else 'no':<7}"
              f"{'YES' if f['wrote_file'] else 'no':<7}"
              f"{sorted(set(f['tools']))}")

    print(f"\ngraded {graded} runs in {ws}")
    if args.iteration == 3:
        print("\nExpected result: control and `tools:` variants fork 3/3; "
              "`allowed-tools` variants fork 0/3.")


if __name__ == "__main__":
    main()
