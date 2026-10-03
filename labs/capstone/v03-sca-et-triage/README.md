# V3: dependency scanning and triage

Fourth version of the **common thread** of the DevSecOps course. The notes-api
pipeline now scans what it installs: the fixable vulnerabilities are fixed,
and the one without a fix is accepted in writing, with an expiry date.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 45 minutes |
| Paired lesson | [SCA: vulnerabilities in dependencies](https://blog.stephane-robert.info/en/docs/devsecops/code-dependencies/sca/) |
| Previous | `capstone-v02-secrets-et-sast` |
| Next | `capstone-v04-identite-sans-secret` |

```bash
mise install
dsoxlab run   capstone-v03-sca-et-triage
cd labs/capstone/v03-sca-et-triage/challenge/work
act push
dsoxlab check capstone-v03-sca-et-triage
```

The tests play your pipeline on the project, then on two booby-trapped copies:
one gets the vulnerable starting lock back, the other carries an exception
whose date has passed. An expired exception must raise the alarm again.
