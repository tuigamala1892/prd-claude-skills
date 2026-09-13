"""The /migrate fan-out: who may make which judgement, and how the agents are dispatched.

A live run lost on both counts at once. Its forked orchestrator backgrounded 29 agents, hit the
harness's 20-subagent ceiling and ended its turn with 43 files undispatched. The prompts it wrote
for the 22 that did launch told them to assign `pattern`, which the agent's own definition forbids.
The prompt won.

Each list is mutated in both directions. The failure that happened was a PERMITTED list gaining a
person's judgement, and a check that walked only the forbidden direction would not see it.
"""

SKILL = "skills/migrate/SKILL.md"
AGENT = "agents/schema-migrator.md"
GUIDE = "schema/migration.md"
CHECK = ("the agent's judgements are exactly two, and the skill's prompt, the agent and the guide "
         "agree on which")

MUTANTS = [
    # --- the skill's prompt template: the direction that failed live ------------------------
    ("the prompt template authorises a pattern again",
     SKILL,
     "into one EARS sentence, with the `<criterion>` count unchanged and no pattern attribute written",
     "into one EARS sentence with the `<criterion>` count unchanged, and assign its `pattern`",
     CHECK),

    ("the prompt template stops forbidding a user story",
     SKILL,
     "- write a `<user-story>`\n",
     "",
     CHECK),

    # --- the agent ----------------------------------------------------------------------------
    ("the agent's Forbidden list loses depends-on",
     AGENT,
     "- declaring `<depends-on>` edges\n",
     "",
     CHECK),

    ("the agent's Yours list gains gaps",
     AGENT,
     "Everything else goes to\n`<considerations>` verbatim.",
     "Everything else goes to\n`<considerations>` verbatim, and write any `<gap>` the notes imply.",
     CHECK),

    # --- the guide: an allocation moved by a one-word edit ---------------------------------------
    ("the guide hands pattern to the agent",
     GUIDE,
     "| assigning an EARS `pattern` | `pattern` | person |",
     "| assigning an EARS `pattern` | `pattern` | agent |",
     CHECK),

    # --- the dispatch ---------------------------------------------------------------------------
    ("a message may hold more calls than the harness runs at once",
     SKILL,
     "**Blocking, and at most 10 calls in one message.**",
     "**Blocking, and at most 25 calls in one message.**",
     CHECK),

    ("Phase 3 stops dispatching blocking",
     SKILL,
     "  run_in_background: false,\n  description: \"Migrate {file} to {target}\"",
     "  description: \"Migrate {file} to {target}\"",
     CHECK),
]
