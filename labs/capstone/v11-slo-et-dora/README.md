# V11: measuring reliability

Twelfth and last version of the **common thread** of the DevSecOps course.
notes-api gets an availability SLO, an alert that pages the on-call person
when the error budget burns too fast, the runbook the alert links to, and the
computation of the four DORA metrics from its journals.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 60 minutes |
| Paired lesson | [SLO, SLI and error budgets](https://blog.stephane-robert.info/en/docs/devsecops/reliability/slo-sli-error-budget/) |
| Previous | `capstone-v10-vex-et-exceptions` |

```bash
mise install
dsoxlab run   capstone-v11-slo-et-dora
cd labs/capstone/v11-slo-et-dora/challenge/work
act pull_request
dsoxlab check capstone-v11-slo-et-dora
```

The tests submit your alert to known request series with promtool, and your
DORA script to journals whose answers they know.
