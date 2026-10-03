# Challenge: the image and the infrastructure

5 tasks, 100 points, 60 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`Dockerfile`, `infra/main.tf`, `infra/deploy.tf` and `threat-model.yml`.

### Task 1: the image and the infrastructure are analysed, the project passes (20 pts)

`act pull_request` is green, and the job shows Trivy analysing the
configuration, then the built image.

### Task 2: a Dockerfile without a user stops the pipeline (20 pts)

In a copy whose Dockerfile no longer has a `USER`, the job fails on rule
DS-0002.

### Task 3: SSH open to the world stops the pipeline (20 pts)

In a copy that adds a security group opening port 22 to `0.0.0.0/0`, the job
fails on rule AWS-0107.

### Task 4: the image runs without privileges, from the lock (20 pts)

The base images are pinned by digest, the image runs under a non-zero uid,
carries the versions of `uv.lock` and does not carry pytest.

### Task 5: the model says the image and the infrastructure are handled (20 pts)

No ingress rule accepts `0.0.0.0/0`, and T-09 and T-10 are `mitigated` with
their evidence.
