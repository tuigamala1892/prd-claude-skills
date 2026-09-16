"""Mutants for `check-artefacts.py` parsing an artefact before it checks anything else.

Found in a live /prd --resume: an element name written in prose left a feature file unparseable,
and every regex rule still passed it. The ways back: the parse is skipped, it is limited to one
kind, the shape rules run on a file that does not parse, or PROJECT.md's prose is parsed too.
"""

CHECK = "every artefact is the shape its own schema version describes -- by running it"

MUTANTS = [
    ("the parse is never attempted",
     "schema/scripts/check-artefacts.py",
     '    if kind == "project-context":\n        return None\n    try:',
     '    if True:\n        return None\n    try:',
     CHECK),

    ("only a feature file is parsed",
     "schema/scripts/check-artefacts.py",
     '    if kind == "project-context":\n        return None\n    try:',
     '    if kind != "feature":\n        return None\n    try:',
     CHECK),

    ("PROJECT.md is parsed whole, prose and all",
     "schema/scripts/check-artefacts.py",
     '    if kind == "project-context":\n        return None\n    try:',
     '    if False:\n        return None\n    try:',
     CHECK),

    ("the shape rules still run on a file that does not parse",
     "schema/scripts/check-artefacts.py",
     '                         "problems": [malformed], "warnings": []})\n            continue\n',
     '                         "problems": [malformed], "warnings": []})\n',
     CHECK),
]
