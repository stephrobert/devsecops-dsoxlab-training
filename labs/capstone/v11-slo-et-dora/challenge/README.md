# V11: knowing before the users, and measuring delivery

## Situation

From V0 to V10, notes-api became hard to attack. Yet nothing tells the team
the service is down: the users notice, and whoever is on call then works out
how to restore it. The threat model names it: T-18, `open`.

The team set itself a service level objective (SLO): **99.5% of requests**
served without a 5xx error, over **28 days**. The error budget is therefore
0.5%. The platform exposes the `http_requests_total` counter, with the labels
`job="notes-api"` and `code`.

It also keeps two journals of the last quarter: `ops/deployments.jsonl` (one
production deployment per line: `sha`, `committed_at`, `deployed_at`,
`failed`) and `ops/incidents.jsonl` (one incident per line: `deployment_sha`,
`started_at`, `resolved_at`).

The `challenge/work` directory holds the project as V10 left it, with those
journals.

SSDF practice targeted: PO.4 (define and use criteria for software security checks).

## Goal

1. `ops/alerts.yaml` carries the **`NotesApiErrorBudgetBurn`** alert: it fires
   when the budget burns **14.4 times** too fast, over a one-hour long window
   and a five-minute short one, and not when it wears out slowly. It links to
   the runbook through its `runbook_url` annotation.
2. `ops/alerts.test.yaml` tests that alert with `promtool test rules`.
3. `ops/runbooks/notes-api-indisponible.md` guides the on-call person:
   symptoms, diagnosis, remediation with a rollback, escalation. Each
   `kubectl` command targets the real namespace and Deployment.
4. `scripts/dora.py <deployments.jsonl> <incidents.jsonl>` writes a JSON
   object with the four DORA metrics, rounded to two decimals:
   - `deployments_per_week`: deployments divided by the weeks between the
     first and the last (one week at least);
   - `lead_time_hours_median`: median of `deployed_at - committed_at`, in
     hours;
   - `change_failure_rate`: share of the deployments that failed (`failed`)
     or caused an incident;
   - `recovery_time_hours_median`: median of `resolved_at - started_at` over
     the incidents, in hours, `null` without incident (the *Failed Deployment
     Recovery Time*).
5. The pipeline checks and tests the alert with promtool, and computes the
   metrics; T-18 moves to `mitigated`.

## Pointers

- promtool lives in the `prom/prometheus` image: a `docker://` step with
  `entrypoint: /bin/promtool`.
- Burning the budget 14.4 times too fast means exceeding 14.4 × 0.5% = 7.2%
  of errors: at that rate, the 28-day budget is gone in two days.
- Two windows, long and short: the long one proves the burn lasts, the short
  one that it still does.

## Check

```bash
dsoxlab check capstone-v11-slo-et-dora
```

Five checks, twenty points each. They play your pipeline with act, submit
your alert to their own request series, run your DORA script on journals
whose answers they know, and reread the runbook.

## Measuring reliability

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
