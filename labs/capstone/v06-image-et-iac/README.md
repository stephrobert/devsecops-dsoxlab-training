# V6: the image and the infrastructure

Seventh version of the **common thread** of the DevSecOps course. The
notes-api pipeline now analyses what it ships besides the code: the
configuration of the Dockerfile and the Terraform, then the built image. The
image runs without privileges, and the infrastructure exposes nothing to the
Internet any more.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 60 minutes |
| Paired lesson | [Scanning images, dependencies and IaC with Trivy](https://blog.stephane-robert.info/en/docs/devsecops/containers-iac/trivy/) |
| Previous | `capstone-v05-pipeline-durci` |
| Next | `capstone-v07-sbom-et-provenance` |

```bash
mise install
dsoxlab run   capstone-v06-image-et-iac
cd labs/capstone/v06-image-et-iac/challenge/work
act pull_request
dsoxlab check capstone-v06-image-et-iac
```

The tests play your pipeline on a pull request, then on two booby-trapped
copies: one removes the `USER` of the Dockerfile, the other opens SSH to the
world. They also build your image to check the user that runs it and the
versions it carries.
