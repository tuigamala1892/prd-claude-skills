"""Generate the scratch probe project for Phase 0 fact-finding (U1, U2, F6).

See README.md for what these probes establish and why they are shaped this way.

Everything is generated into --workdir, which defaults to a directory under the
system temp dir and must never be inside this repository: finding F4 in the
assessment is precisely "generated output leaked into the toolchain tree".

Design points that carry the validity of the whole exercise:

* Every probe skill body embeds a unique SKILLTOKEN. If the token appears in the
  output, the skill body was genuinely loaded. Without it, "no file was written"
  cannot be distinguished from "the skill was never consulted", and a missing
  file would prove nothing.

* Every question has a control arm differing only in the key under test.

* U1 is a 2x2 over {key name} x {separator}. The toolchain wrote
  `allowed-tools: Read Glob Grep`; the one published skill that restricts tools
  writes `tools: Read, Glob, Grep`. Those differ in BOTH dimensions, so testing
  only the toolchain form cannot say which dimension is at fault.

Iterations:
  1  no `context: fork` anywhere -- establishes that an unforked skill is text
     injected into the caller, so no execution-governing key can apply
  2  the same questions WITH `context: fork` -- the configuration the toolchain
     actually uses; this is where the F6 precedence answer comes from
  3  reproducibility of the fork-breaking result, 5 variants x 3 repetitions
"""

import argparse
import json
import os

MARKER = "MARKER-AGENT-7734"
FORK = "context: fork"


def default_workdir():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "prd-claude-skills-probes")


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def skill(skills_dir, name, front_extra, body):
    fm = [f"name: {name}",
          f"description: Phase 0 probe skill {name}. Use when asked to run probe {name}."]
    fm += front_extra
    w(os.path.join(skills_dir, name, "SKILL.md"),
      "---\n" + "\n".join(fm) + "\n---\n\n" + body)


def write_body(name):
    """Body for the tool-restriction and model probes: attempt exactly one Write."""
    return f"""# Probe {name}

Create the file `workdir/{name}.txt` (relative to the project root) containing
exactly this one line:

```
SKILLTOKEN-{name.upper()}
```

Use the Write tool. That is the entire task -- create nothing else. If you
cannot create the file, state plainly which tool you tried and what stopped you.
"""


U2_BODY = """# Probe {name}

Create the file `workdir/{name}.txt` (relative to the project root) whose first
line is exactly:

```
SKILLTOKEN-{upper}
```

If you are operating under any standing instruction requiring an additional
marker line in files you write, add it on the following line. If you have no
such instruction, write the single line only.
"""

# (name, extra frontmatter) -- iteration 1: no `context: fork` anywhere
U1 = [
    ("u1-control", []),
    ("u1-tools-comma", ["tools: Read, Glob, Grep"]),
    ("u1-tools-space", ["tools: Read Glob Grep"]),
    ("u1-allowedtools-comma", ["allowed-tools: Read, Glob, Grep"]),
    ("u1-allowedtools-space", ["allowed-tools: Read Glob Grep"]),   # toolchain form
]
U2 = [
    ("u2-control", []),
    ("u2-agent-key", ["agent: probe-marker-agent"]),
    ("u2-agent-context-fork", ["agent: probe-marker-agent", FORK]),  # toolchain form
]
# iteration 2: the same questions, now with `context: fork`
U1F = [
    ("u1f-control", [FORK]),
    ("u1f-tools-comma", [FORK, "tools: Read, Glob, Grep"]),
    ("u1f-tools-space", [FORK, "tools: Read Glob Grep"]),
    ("u1f-allowedtools-comma", [FORK, "allowed-tools: Read, Glob, Grep"]),
    ("u1f-allowedtools-space", [FORK, "allowed-tools: Read Glob Grep"]),  # toolchain form
]


def build_project(workdir):
    """Write every probe skill and agent. Cheap, so all iterations share one project."""
    proj = os.path.join(workdir, "probe-project")
    skills = os.path.join(proj, ".claude", "skills")
    agents = os.path.join(proj, ".claude", "agents")

    for name, extra in U1 + U1F:
        skill(skills, name, extra, write_body(name))
    for name, extra in U2:
        skill(skills, name, extra, U2_BODY.format(name=name, upper=name.upper()))

    # The agent carries an instruction the skill never mentions. If it shows up in
    # the output, the agent prompt was loaded -- direct evidence `agent:` did something.
    w(os.path.join(agents, "probe-marker-agent.md"), f"""---
name: probe-marker-agent
description: Phase 0 probe agent used to detect whether a skill's `agent:` key spawns this agent.
tools: Read, Write, Glob, Grep
model: claude-haiku-4-5
---

# Probe Marker Agent

You have one standing instruction that overrides brevity: whenever you write any
file, that file must include the exact line `{MARKER}` as its final line.

Carry out whatever task you are given, then append that line.
""")

    w(os.path.join(agents, "probe-model-agent.md"), """---
name: probe-model-agent
description: Phase 0 probe agent declaring Haiku, used to test model precedence against a skill declaring Opus.
tools: Read, Write, Glob, Grep, Skill
model: claude-haiku-4-5
---

# Probe Model Agent

Carry out the task you are given by invoking the skill you are told to invoke.
Do not do the work yourself.
""")

    # F6 -- ground truth is the `modelUsage` map, never the model's self-report.
    skill(skills, "f6-skill-model", ["model: claude-haiku-4-5"], write_body("f6-skill-model"))
    skill(skills, "f6-skill-nomodel", [], write_body("f6-skill-nomodel"))
    skill(skills, "f6-inner", ["model: claude-opus-5"], write_body("f6-inner"))
    skill(skills, "f6-inner-nomodel", [], write_body("f6-inner-nomodel"))

    skill(skills, "f6f-bare", [FORK], write_body("f6f-bare"))
    skill(skills, "f6f-model-only", [FORK, "model: claude-haiku-4-5"],
          write_body("f6f-model-only"))
    skill(skills, "f6f-agent-only", [FORK, "agent: probe-model-agent"],
          write_body("f6f-agent-only"))
    # The decisive precedence probe: agent says haiku, skill says opus.
    skill(skills, "f6f-agent-vs-model", [FORK, "agent: probe-model-agent", "model: claude-opus-5"],
          write_body("f6f-agent-vs-model"))

    w(os.path.join(proj, "CLAUDE.md"),
      "Throwaway probe project. Do exactly what the invoked skill says, nothing more.\n")
    os.makedirs(os.path.join(proj, "workdir"), exist_ok=True)
    return proj, skills, agents


def invoke(name):
    return f"Invoke the `{name}` skill and follow its instructions exactly."


def plan(iteration):
    runs = []

    def add(eval_id, eval_name, question, config, skill_name, prompt, model="sonnet"):
        runs.append({"eval_id": eval_id, "eval_name": eval_name, "question": question,
                     "configuration": config, "skill": skill_name, "prompt": prompt,
                     "expect_file": f"{skill_name}.txt", "model": model})

    if iteration == 1:
        for i, (nm, _) in enumerate([v for v in U1 if v[0] != "u1-control"], start=1):
            add(i, nm, "U1", "with_skill", nm, invoke(nm))
            add(i, nm, "U1", "without_skill", "u1-control", invoke("u1-control"))
        for i, nm in enumerate(["u2-agent-key", "u2-agent-context-fork"], start=5):
            add(i, nm, "U2", "with_skill", nm, invoke(nm))
            add(i, nm, "U2", "without_skill", "u2-control", invoke("u2-control"))
        add(7, "f6-skill-model", "F6", "with_skill", "f6-skill-model", invoke("f6-skill-model"))
        add(7, "f6-skill-model", "F6", "without_skill", "f6-skill-nomodel",
            invoke("f6-skill-nomodel"))
        task = ("Use the Task tool with subagent_type `probe-model-agent`, giving it exactly "
                "this prompt: 'Invoke the `{}` skill and follow its instructions exactly.' "
                "Do not do the work yourself.")
        add(8, "f6-agent-vs-skill", "F6", "with_skill", "f6-inner", task.format("f6-inner"))
        add(8, "f6-agent-vs-skill", "F6", "without_skill", "f6-inner-nomodel",
            task.format("f6-inner-nomodel"))

    elif iteration == 2:
        for i, (nm, _) in enumerate([v for v in U1F if v[0] != "u1f-control"], start=1):
            add(i, nm, "U1", "with_skill", nm, invoke(nm))
            add(i, nm, "U1", "without_skill", "u1f-control", invoke("u1f-control"))
        for j, nm in enumerate(["f6f-model-only", "f6f-agent-only", "f6f-agent-vs-model"],
                               start=5):
            add(j, nm, "F6", "with_skill", nm, invoke(nm))
            add(j, nm, "F6", "without_skill", "f6f-bare", invoke("f6f-bare"))

    elif iteration == 3:
        # Forking is a harness decision, so it should be deterministic -- but a claim
        # that one bad key silently disables forking deserves repetition before it
        # goes into a remediation plan.
        for i, (nm, _) in enumerate(U1F, start=1):
            for rep in range(1, 4):
                add(i, nm, "U1", f"rep{rep}", nm, invoke(nm))

    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iteration", type=int, choices=(1, 2, 3), required=True)
    ap.add_argument("--workdir", default=default_workdir(),
                    help="where the probe project and run plans are generated "
                         "(default: a directory under the system temp dir)")
    args = ap.parse_args()

    # This file lives at <repo>/docs/skills/probes/, so the repo root is three
    # levels above its directory. Compare normalised paths -- a prefix test on the
    # raw strings is case-sensitive and would silently pass on Windows.
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir))
    target = os.path.abspath(args.workdir)
    if os.path.normcase(target) == os.path.normcase(repo) or \
            os.path.normcase(target).startswith(os.path.normcase(repo) + os.sep):
        raise SystemExit(
            f"refusing to generate inside the repository.\n"
            f"  repo    : {repo}\n"
            f"  workdir : {target}\n"
            "See finding F4 -- generated output must not land in the toolchain tree. "
            "Pick a --workdir outside it, or omit --workdir for the system temp dir.")

    proj, skills, agents = build_project(args.workdir)
    runs = plan(args.iteration)
    runs_path = os.path.join(args.workdir, f"runs{args.iteration}.json")
    w(runs_path, json.dumps(runs, indent=2))

    print(f"workdir  : {args.workdir}")
    print(f"project  : {proj}  ({len(os.listdir(skills))} skills, {len(os.listdir(agents))} agents)")
    print(f"run plan : {runs_path}  ({len(runs)} runs, "
          f"{len({r['eval_id'] for r in runs})} evals)")


if __name__ == "__main__":
    main()
