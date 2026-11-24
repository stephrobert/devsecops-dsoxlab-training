# V6: what you ship, besides the code

## Situation

The notes-api pipeline rereads the code, the dependencies and the workflows.
It looks neither at the **image** that goes to production nor at the
**infrastructure** that hosts it, and the threat model has kept two threats
open there since V1:

- T-09: the `Dockerfile` starts from `python:3.12` without a digest, installs
  versions copied by hand in a `pip install` line, and runs the service as
  root;
- T-10: `infra/main.tf` opens SSH and the API to `0.0.0.0/0`, and both buckets
  have neither a public access block nor encryption with a managed key.

The `challenge/work` directory holds the project as V5 left it.

SSDF practice targeted: PW.6 (configure the compilation, interpreter, and build processes to improve executable security).

## Goal

1. The pipeline **analyses the configuration** (Dockerfile and Terraform) and
   **the built image**, and each analysis **blocks** at the HIGH and CRITICAL
   threshold. For the image, only what has a published fix blocks.
2. The **Dockerfile** starts from images pinned by digest, installs the
   dependencies from `uv.lock` without the development group, applies the
   published Debian fixes, and runs as an **unprivileged user**.
3. The **infrastructure** exposes nothing to the Internet any more: no SSH,
   the API reachable from the VPC only; each bucket blocks public access and
   encrypts with a KMS key whose rotation is enabled.
4. T-09 and T-10 move to `mitigated`, each with its evidence.

The project must stay green on a pull request. A copy whose Dockerfile loses
its `USER`, or that opens SSH to the world, must turn it red.

## Pointers

- Trivy runs as a `docker://` step, image pinned by digest: `config` for the
  configuration, `image --input <archive>` for an image saved with
  `docker save`. Avoid versions 0.69.4 to 0.69.6, compromised in March 2026.
- A frozen base image ages: rebuilding it with `apt-get upgrade` applies the
  fixes published since.
- The MEDIUM and LOW findings that remain (logging, bucket versioning) are
  below the threshold: that is a decision, to be written down, not an
  oversight.

## Check

```bash
dsoxlab check capstone-v06-image-et-iac
```

Five checks, twenty points each. They play your pipeline with act on a pull
request and on booby-trapped copies, build your image to query it, and reread
the infrastructure and the threat model.

## The image and the infrastructure

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
