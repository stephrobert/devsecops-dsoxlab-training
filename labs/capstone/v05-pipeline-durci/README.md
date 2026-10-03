# V5: a hardened pipeline

Sixth version of the **common thread** of the DevSecOps course. The notes-api
workflows go through their own audit on every pull request, the welcome
workflow no longer runs the proposed code, and the security team reviews any
change to the sensitive paths.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 50 minutes |
| Paired lesson | [Auditing your workflows with zizmor](https://blog.stephane-robert.info/en/docs/github-actions/security/zizmor/) |
| Previous | `capstone-v04-identite-sans-secret` |
| Next | `capstone-v06-image-et-iac` |

```bash
mise install
dsoxlab run   capstone-v05-pipeline-durci
cd labs/capstone/v05-pipeline-durci/challenge/work
act pull_request
dsoxlab check capstone-v05-pipeline-durci
```

The tests play your pipeline on a pull request, then on two booby-trapped
copies: one adds a pull request that runs its own code with the
repository's privileges, the other a workflow with an impossible cron. Each one must be stopped by the right tool.
