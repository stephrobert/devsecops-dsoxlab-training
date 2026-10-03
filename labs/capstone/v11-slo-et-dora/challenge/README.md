# Challenge: measuring reliability

5 tasks, 100 points, 60 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml` and
`threat-model.yml`, and you create `ops/alerts.yaml`, `ops/alerts.test.yaml`,
`ops/runbooks/notes-api-indisponible.md` and `scripts/dora.py`.

### Task 1: the pipeline checks the alert and measures delivery (20 pts)

`act pull_request` is green, promtool checks the rules, and the job writes
the DORA metrics.

### Task 2: the alert fires when the budget burns, and only then (20 pts)

With 10% of errors, `NotesApiErrorBudgetBurn` fires at 1h30; with 1%, it
never fires.

### Task 3: the DORA metrics are right (20 pts)

On three fabricated journals, `scripts/dora.py` returns the values the
scenario's definition gives.

### Task 4: the runbook guides the on-call person (20 pts)

Four sections (symptoms, diagnosis, remediation, escalation), a rollback,
`kubectl` commands that target `notes-api`, and the alert linking to the
runbook.

### Task 5: a broken rule stops the pipeline, the model up to date (20 pts)

In a copy whose rule no longer parses, the job fails; T-18 is `mitigated`
with its evidence.
