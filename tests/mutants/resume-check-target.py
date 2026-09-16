"""Mutants for the resume steps' `migrate.py --check` -- the line as written was never run.

/prd --resume and /crd --resume asked `migrate.py <dir> --check` with no --to, and the script
refused it as a usage error. Every other check supplied --to itself. The ways back: the script
stops defaulting the target, or defaults it to something other than the newest schema; or any
one of the four command lines stops asking the question the step reads the answer to.
"""

CHECK = "the resume steps' migrate.py lines run as the commands write them"

MUTANTS = [
    ("--check without --to is a usage error again",
     "schema/scripts/migrate.py",
     "        if not args.target and args.check:\n            args.target = VERSIONS[-1]\n",
     "",
     CHECK),

    ("--check without --to checks against the oldest schema, so nothing is ever short",
     "schema/scripts/migrate.py",
     "            args.target = VERSIONS[-1]\n",
     "            args.target = VERSIONS[0]\n",
     CHECK),

    ("/prd's resume step runs a migration with no target instead of a check",
     "commands/prd.md",
     "migrate.py {prd_dir} --check\n```",
     "migrate.py {prd_dir}\n```",
     CHECK),

    ("/prd's re-run when the person stops loses --check",
     "commands/prd.md",
     "Re-run `migrate.py {prd_dir} --check` when",
     "Re-run `migrate.py {prd_dir} --dry-run` when",
     CHECK),

    ("/crd's resume step detects instead of checking, so nothing is ever outstanding",
     "commands/crd.md",
     "migrate.py {project_path}/docs/crd --check\n```",
     "migrate.py {project_path}/docs/crd --detect\n```",
     CHECK),

    ("/crd's re-run when the person stops loses --check",
     "commands/crd.md",
     "Re-run `migrate.py {project_path}/docs/crd --check` when",
     "Re-run `migrate.py {project_path}/docs/crd --dry-run` when",
     CHECK),
]
