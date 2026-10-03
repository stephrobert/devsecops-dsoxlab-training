# Challenge: SBOM and provenance

5 tasks, 100 points, 55 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml` and
`threat-model.yml`, and you create `scripts/verify_release.sh`.

### Task 1: the image SBOM is confronted with the lock (20 pts)

`act pull_request` is green, and the job shows the "SBOM matches uv.lock"
line of the team's tool.

### Task 2: a package outside the lock stops the pipeline (20 pts)

In a copy whose image installs `six` outside `uv.lock`, the job fails on the
SBOM confrontation.

### Task 3: the deployment attests the provenance of the archive (20 pts)

The deploy job, reserved to main, declares `id-token: write` and
`attestations: write`, and attests the `.tgz` archive with an action pinned
by SHA.

### Task 4: the verification requires the repository, the workflow and main (20 pts)

`scripts/verify_release.sh <archive>` calls `gh attestation verify` with the
repository, the signer workflow, the ref and the refusal of self-hosted
runners, and fails when the verification fails.

### Task 5: the SBOM is published, the model up to date (20 pts)

The deploy job publishes `sbom.cdx.json` next to the archive, and T-14 is
`mitigated` with its evidence.
