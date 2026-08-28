"""Mutants for items 61 and 62 -- the two contradictions a live run found.

Both checks guard PROSE, which is the weakest thing to guard and the reason these two defects
survived 112 checks: the mechanism was right in each case and a second instruction about it was
wrong. So each rule is broken twice -- once by restoring the old wording, once by removing the
half that makes the check non-vacuous.

The last pair is the important one. A check that only asserts the absence of a bad sentence
passes on a file that has lost the good sentence too, which is how a guard against a
contradiction becomes a guard against nothing.
"""

MUTANTS = [
    # ---------------------------------------------------------------- item 61
    ("the rescinded instruction comes back verbatim",
     "skills/breakdown-plan-layers/SKILL.md",
     "- **Emit a layer with no work in it** — see *First, decide which layers exist at all* above",
     "- Skip layers (every project needs all 4 layers)",
     "the layer set is derived, and nothing instructs otherwise"),

    ("it comes back in different words, asserting the same fixed count",
     "skills/breakdown-plan-layers/SKILL.md",
     "- Assume a fixed number of layers. The set is derived from the document and from",
     "- Remember every project needs all 4 layers, derived from the document and from",
     "the layer set is derived, and nothing instructs otherwise"),

    ("the derivation instruction goes, leaving a check that forbids a sentence nobody would write",
     "skills/breakdown-plan-layers/SKILL.md",
     "**First, decide which layers exist at all.** A tier with no work in it is not a tier: emit only",
     "**Emit the layers.** Generate tasks for each of them: emit only",
     "the layer set is derived, and nothing instructs otherwise"),

    ("a dropped layer stops having to be named, so one task instead of four explains nothing",
     "skills/breakdown-plan-layers/SKILL.md",
     "the layers this document actually puts work in, and name the ones you dropped and why.",
     "the layers this document actually puts work in.",
     "the layer set is derived, and nothing instructs otherwise"),

    # ---------------------------------------------------------------- item 62
    ("the id pattern goes back to rejecting Layer 0",
     "skills/breakdown/references/task-format-spec.md",
     "- `id`: Must match pattern `L[0-9]+-[0-9]{3}`",
     "- `id`: Must match pattern `L[1-4]-[0-9]{3}`",
     "the task schema admits every layer the layer graph can produce"),

    ("the id pattern is widened until it constrains nothing",
     "skills/breakdown/references/task-format-spec.md",
     "- `id`: Must match pattern `L[0-9]+-[0-9]{3}`",
     "- `id`: Must match pattern `.*`",
     "the task schema admits every layer the layer graph can produce"),

    ("`layer` becomes a closed enum again, which item 28's per-project graph contradicts",
     "skills/breakdown/references/task-format-spec.md",
     "- `layer`: `{id}-{name}`, from the layer set `plan-layers` derived — `0-setup`, `1-foundation`,",
     "- `layer`: One of: `0-setup`, `1-foundation`,",
     "the task schema admits every layer the layer graph can produce"),
]
