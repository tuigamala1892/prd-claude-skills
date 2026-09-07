"""Mutants for group 8b -- the three CRD references that nothing followed.

The defect being closed is a producer with no consumer, so the mutants are mostly *the consumer
quietly not consuming*: a resolver that reports and exits 0, a comparison that never compares, a
required element whose absence is fine. Each leaves the element in the schema and the check in
the pipeline, and means exactly as much as before it was written.

The last two are the wiring. A reader nothing calls is a script, and the gate skipped this one
for CRDs by construction until 8b -- so `the gate calls it` and `the gate does something with
what it says` are broken separately.
"""

MUTANTS = [
    # ------------------------------------------------------------------ the resolver
    ("a feature-ref may name a feature PROJECT.md does not have",
     "skills/breakdown/scripts/check-references.py",
     '        elif fid not in known:\n            errors.append(f"{rel}: <feature-ref id=\\"{fid}\\"> resolves to no <feature id=> in "',
     '        elif False:\n            errors.append(f"{rel}: <feature-ref id=\\"{fid}\\"> resolves to no <feature id=> in "',
     "a CRD's references resolve, and a required one nothing follows is not required"),

    ("a dangling prd-ref is accepted, so the only change-to-feature link stays unfollowed",
     "skills/breakdown/scripts/check-references.py",
     "        prd = resolve(m.group(1))\n        if not os.path.exists(prd):",
     "        prd = resolve(m.group(1))\n        if False:",
     "a CRD's references resolve, and a required one nothing follows is not required"),

    ("the project-ref is resolved and never compared, which is the check it exists for",
     "skills/breakdown/scripts/check-references.py",
     "            if os.path.normcase(os.path.abspath(project_md)) != os.path.normcase(\n"
     "                    os.path.abspath(expected)):",
     "            if False:",
     "a CRD's references resolve, and a required one nothing follows is not required"),

    ("a CRD with no project-ref is fine, and the element goes back to being Required in name",
     "skills/breakdown/scripts/check-references.py",
     '        errors.append(f"{rel}: no <project-ref>. It is required, and a change with no named "',
     '        warnings.append(f"{rel}: no <project-ref>. It is required, and a change with no named "',
     "a CRD's references resolve, and a required one nothing follows is not required"),

    ("everything is reported and the run exits 0, which is a report nobody has to read",
     "skills/breakdown/scripts/check-references.py",
     "        return 1 if errors else 0\n",
     "        return 0\n",
     "a CRD's references resolve, and a required one nothing follows is not required"),

    ("the comparison it could not make is passed over in silence",
     "skills/breakdown/scripts/check-references.py",
     '        if not args.project_path:\n            print("  NOTE      no --project-path,',
     '        if False:\n            print("  NOTE      no --project-path,',
     "a CRD's references resolve, and a required one nothing follows is not required"),

    # ------------------------------------------------------------------ the wiring
    ("the gate goes back to skipping references for a CRD entirely",
     "skills/breakdown/scripts/check-gate.py",
     '    ref_code, ref_out = run("check-references.py", *ref_args)',
     '    ref_code, ref_out = (0, "") if os.path.isfile(args.document) else run(\n'
     '        "check-references.py", *ref_args)',
     "a CRD's references resolve, and a required one nothing follows is not required"),

    ("the gate runs it and drops what it says",
     "skills/breakdown/scripts/check-gate.py",
     '    for line in dangling:\n        findings.append(("references", line))',
     "    pass",
     "a CRD's references resolve, and a required one nothing follows is not required"),

    # ------------------------------------------------------------------ and the record
    ("the elements are recorded as unread again, contradicting the reader they now have",
     "schema/readers.md",
     "| `change-request` | unread by design |",
     "| `project-ref` | **open** | Required in every CRD and read by nothing |\n"
     "| `change-request` | unread by design |",
     "a CRD's references resolve, and a required one nothing follows is not required"),
]
