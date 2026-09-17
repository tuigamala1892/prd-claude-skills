"""Mutants for **Drives:** being append-only, and a superseded record not counting as coverage.

The ways back: the helper counts superseded records again, either call site stops using it, the
report fires on everything, or decision-record.md loses either half of the rule.
"""

CHECK = "**Drives:** is append-only, and a superseded record's field is history, not coverage"
SCRIPT = "skills/breakdown/scripts/check-references.py"
RECORD = "schema/decision-record.md"

MUTANTS = [
    ("the helper counts a superseded record's field as coverage",
     SCRIPT,
     '        if "supersed" in rec["status"].lower():\n            continue\n',
     "",
     CHECK),

    ("the CRD branch builds its own set from every record",
     SCRIPT,
     "        crd_driven = driven_by(crd_records)\n",
     "        crd_driven = {os.path.basename(t.split(\"#\")[0])\n"
     "                      for r in (crd_records or {}).values() for t in r[\"drives\"]}\n",
     CHECK),

    ("the PRD branch builds its own set from every record",
     SCRIPT,
     "    driven = driven_by(records)\n",
     "    driven = {os.path.basename(t.split(\"#\")[0])\n"
     "              for r in (records or {}).values() for t in r[\"drives\"]}\n",
     CHECK),

    ("the PRD branch reports every significant feature, driven or not",
     SCRIPT,
     "            elif os.path.basename(path_) not in driven:\n",
     "            elif True:\n",
     CHECK),

    ("decision-record.md no longer says the field is append-only",
     RECORD,
     "**`**Drives:**` is append-only: a link is added, never removed.**",
     "**`**Drives:**` is kept up to date with the feature set.**",
     CHECK),

    ("decision-record.md no longer says a superseded field stops counting",
     RECORD,
     "**A superseded record's `**Drives:**` is history, not coverage.**",
     "**A superseded record's `**Drives:**` still counts.**",
     CHECK),
]
