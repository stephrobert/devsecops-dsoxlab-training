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
