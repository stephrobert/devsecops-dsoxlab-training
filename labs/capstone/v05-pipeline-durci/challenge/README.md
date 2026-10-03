# Challenge: a hardened pipeline

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`.github/workflows/pr-welcome.yml` and `threat-model.yml`, and you create a
CODEOWNERS file.

### Task 1: the workflow audit runs and the project passes (20 pts)

`act pull_request` is green, zizmor reports no flaw, and the tests run.

### Task 2: a booby-trapped pull request stops the pipeline (20 pts)

In a copy that adds a `pull_request_target` workflow checking out the code
of the pull request, the job fails on zizmor.

### Task 3: a workflow syntax error stops the pipeline (20 pts)

In a copy that adds a workflow with an impossible cron, the job fails on
actionlint.

### Task 4: no privileged workflow runs the pull request (20 pts)

No workflow on `pull_request_target` checks out or runs the proposed code,
and no script contains a field controlled by the pull request author.

### Task 5: the security team reviews the sensitive paths (20 pts)

CODEOWNERS assigns the workflows, the infrastructure, the triage and the
threat model to `@acme/security`, gives the application code an owner, and
T-13 is `mitigated` with its evidence.
