# V0: the minimal pipeline

First lab of the **common thread** of the DevSecOps course: the learner
evolves a single project, `notes-api`, from V0 to V11. Here, the project gets
its first pipeline: locked dependencies, tests, on every push and every pull
request.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 30 minutes |
| Paired lesson | [The DevSecOps common thread](https://blog.stephane-robert.info/en/docs/devsecops/capstone/devsecops-capstone/) |
| Next | `capstone-v01-modele-de-menace` |

```bash
mise install                         # uv, Python and act
dsoxlab run capstone-v00-pipeline-minimal
cd labs/v00-pipeline-minimal/challenge/work
act push                             # plays your workflow
dsoxlab check capstone-v00-pipeline-minimal
```

act plays the workflow in the `ubuntu-24.04` runner image, pinned by digest in
`.actrc`. The tests replay your workflow on the project and on copies broken
on purpose, and read the job's result.
