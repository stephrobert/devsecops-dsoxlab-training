# V4: an identity without a secret

Fifth version of the **common thread** of the DevSecOps course. notes-api no
longer publishes its releases with an AWS key stored in the repository: the
deploy job trades an OIDC token for one-hour credentials, for a role that only
the main branch can assume.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 50 minutes |
| Paired lesson | [OIDC: authenticating without a secret](https://blog.stephane-robert.info/en/docs/github-actions/security/oidc/) |
| Previous | `capstone-v03-sca-et-triage` |
| Next | `capstone-v05-pipeline-durci` |

```bash
mise install
dsoxlab run   capstone-v04-identite-sans-secret
cd labs/capstone/v04-identite-sans-secret/challenge/work
act pull_request
dsoxlab check capstone-v04-identite-sans-secret
```

The tests play your pipeline on a work branch and on a pull request, where the
deployment must not start, then evaluate the role's trust policy against the
tokens of five situations.
