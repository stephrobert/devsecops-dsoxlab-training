# Challenge: VEX and dated exceptions

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`Dockerfile`, `infra/deploy.tf` and `threat-model.yml`, and you create
`.trivyignore.yaml` and `security/notes-api.openvex.json`.

### Task 1: the pipeline passes at the MEDIUM threshold (20 pts)

`act pull_request` is green, and the blocking Trivy analyses (`config` and
`image`) carry the MEDIUM threshold.

### Task 2: the image no longer contains pip (20 pts)

In the built image, neither the pip module nor the pip command exists.

### Task 3: the VEX covers pip in the previous release (20 pts)

Analysed with your VEX, the previous image no longer carries any pip
vulnerability, and nothing else is hidden.

### Task 4: an expired exception raises the alarm again (20 pts)

In a copy whose exceptions have expired, the job fails on the configuration
analysis.

### Task 5: each decision is written, dated, and the model up to date (20 pts)

Each exception is limited to its files, carries a reason and an expiry within
six months, the releases bucket has none, and T-17 is `mitigated` with its
evidence.
