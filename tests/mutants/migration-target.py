"""Mutants for a migration target written as a version -- the check only ever scanned tests/.

check-enforcement.py probed migrate.py with `--to schema-6`, which would have kept checking
against schema-6 after schema-7 landed, and nothing said so because the version scan stopped at
tests/. The ways back: the probe names a version again, or a toolchain script in any of the
three places the scan now reaches -- schema/scripts, a skill's scripts, a shell script --
passes one.
"""

CHECK = "nothing hardcodes a schema fixture version"

MUTANTS = [
    ("the enforcement probe checks against a named version again",
     "schema/scripts/check-enforcement.py",
     '        "argv": lambda ws: [_doc(ws), "--check"],\n',
     '        "argv": lambda ws: [_doc(ws), "--check", "--to", "schema-6"],\n',
     CHECK),

    ("a skill's script passes a named migration target",
     "skills/breakdown/scripts/check-status.py",
     "# *What document is this* has ONE answer in this toolchain",
     '_TARGET = ["--to", "schema-6"]\n# *What document is this* has ONE answer in this toolchain',
     CHECK),

    ("a shell script runs a migration to a named version",
     "skills/execute/scripts/preflight.sh",
     "set -eu\n",
     "set -eu\n: migrate.py . --check --to schema-6\n",
     CHECK),
]
