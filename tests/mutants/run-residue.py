"""What the gap-closure run reported and nobody verified: P72, P73, P74.

P72: `/breakdown` step 11 now hands `check-references.py` the project a CRD is against. P73:
`check-resume.py` refuses to resume from artefacts built from different documents, and every skip
in Phases 2-4 leans on it. P74: `analysis.json`'s `gaps` is named, one shape, where it is written.
The mutants aim at tidying a careful person might do -- making the flag look like its neighbours,
treating a missing record as a fresh run, dropping a key nobody seemed to read.
"""

SKILL = "skills/breakdown/SKILL.md"
RESUME = "skills/breakdown/scripts/check-resume.py"

P72 = "/breakdown hands check-references.py the project a CRD is against"
P73 = "a resumed /breakdown resumes from the documents it was given, or refuses"
P74 = "analysis.json's gaps are one shape, named where the analysis is written"
PROBED = "every assertion says which paths it reaches, and each `both` is probed by running it"
CALLERS = "every file that runs an owning script is listed as its caller"

MUTANTS = [
    # --- P72 ------------------------------------------------------------------------------------
    ("step 11 drops --project-path again, which is P72 reopened",
     SKILL,
     "check-references.py {document} [--project-path {target_dir}] [--adr-dir DIR]",
     "check-references.py {document} [--adr-dir DIR]",
     P72),

    ("step 11's flag is tidied to look like its neighbours, and names no value the run has",
     SKILL,
     "check-references.py {document} [--project-path {target_dir}] [--adr-dir DIR]",
     "check-references.py {document} [--project-path DIR] [--adr-dir DIR]",
     P72),

    # --- P73: the wiring ------------------------------------------------------------------------
    ("step 8 goes back to looking for .done markers",
     SKILL,
     "   python {skill_dir}/scripts/check-resume.py {document} {tasks_dir} [--project-path {target_dir}]\n",
     "   ls {tasks_dir}/*/.done\n",
     P73),

    ("step 8 stops passing the project, so PROJECT.md is never recorded",
     SKILL,
     "check-resume.py {document} {tasks_dir} [--project-path {target_dir}]",
     "check-resume.py {document} {tasks_dir}",
     P73),

    ("Phase 2 skips on existence alone",
     SKILL,
     "If analysis.json exists, skip this phase — sound only because step 8's `check-resume.py` "
     "has shown it was built from these documents.",
     "If analysis.json exists, skip this phase.",
     P73),

    ("Phase 3 skips on existence alone",
     SKILL,
     "If layer_plan.json exists, skip this phase — sound only because step 8's `check-resume.py` "
     "has shown it was built from these documents.",
     "If layer_plan.json exists, skip this phase.",
     P73),

    # --- P73: the script ------------------------------------------------------------------------
    ("a changed source is resumed from anyway",
     RESUME,
     "    if drift:",
     "    if False:",
     P73),

    ("a done layer is not a resume",
     RESUME,
     'for p in glob.glob(os.path.join(tasks_dir, "*", ".done")))',
     "for p in [])",
     P73),

    ("PROJECT.md is not a source on the CRD path",
     RESUME,
     "        if os.path.isfile(document):\n            candidate = os.path.join(project_path, \"PROJECT.md\")",
     "        if False:\n            candidate = os.path.join(project_path, \"PROJECT.md\")",
     P73),

    ("a missing record is treated as a fresh run, and the old artefacts are resumed from",
     RESUME,
     "    if not present:",
     "    if not present or not os.path.isfile(record):",
     P73),

    ("the resume check loses its enforcement probe",
     "schema/scripts/check-enforcement.py",
     '    "check-resume.py": {',
     '    "check-resume-unprobed.py": {',
     PROBED),

    ("the resume check loses its checks.md row's caller",
     "schema/checks.md",
     "| `check-resume.py` | `skills/breakdown/SKILL.md` | both |",
     "| `check-resume.py` | `commands/crd.md` | both |",
     CALLERS),

    # --- P74 ------------------------------------------------------------------------------------
    ("the PRD merge drops `body` from the gaps shape",
     SKILL,
     "concatenated, each `{feature, id, kind, raised, body}`**",
     "concatenated, each `{feature, id, kind, raised}`**",
     P74),

    ("the CRD block stops naming the gaps shape",
     SKILL,
     "- Open gaps from `<gaps>`, into `gaps` — the PRD path's list shape, each\n"
     "  `{feature, id, kind, raised, body}`,",
     "- Open gaps from `<gaps>`, into `gaps` — the PRD path's list shape,",
     P74),

    ("the analyzer's documented example renames body to text, as the CRD run did",
     "skills/breakdown-analyze-prd/SKILL.md",
     '      "body": "Retention period for archived links is unspecified."',
     '      "text": "Retention period for archived links is unspecified."',
     P74),
]
