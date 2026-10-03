# V2: blocking secrets and SAST

Third version of the **common thread** of the DevSecOps course. The notes-api
pipeline gets two gates that block, a secret scan and a static analysis, and
the SQL injection named by the threat model is fixed.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 50 minutes |
| Paired lesson | [Automated security testing](https://blog.stephane-robert.info/en/docs/devsecops/code-dependencies/security-testing/) |
| Previous | `capstone-v01-modele-de-menace` |
| Next | `capstone-v03-sca-et-triage` |

```bash
mise install
dsoxlab run   capstone-v02-secrets-et-sast
cd labs/capstone/v02-secrets-et-sast/challenge/work
act push
dsoxlab check capstone-v02-secrets-et-sast
```

The tests play your pipeline on the project, then on two booby-trapped copies:
one carries a token, the other adds a route that concatenates a value into its
query. No test of the application covers that route: only the static analysis
can stop it.
