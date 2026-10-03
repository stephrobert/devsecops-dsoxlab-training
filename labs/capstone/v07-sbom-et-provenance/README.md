# V7: SBOM and provenance

Eighth version of the **common thread** of the DevSecOps course. The notes-api
pipeline produces the inventory of what the image carries and confronts it
with the lock. The deploy job attests the provenance of every archive, and a
script refuses to deploy one that the main pipeline did not build.

| | |
|---|---|
| Target | your workstation: uv, Python and act (`mise install`), a **Docker** that answers |
| Duration | about 55 minutes |
| Paired lesson | [From SLSA provenance to a decision](https://blog.stephane-robert.info/en/docs/devsecops/supply-chain/slsa-provenance/) |
| Previous | `capstone-v06-image-et-iac` |

```bash
mise install
dsoxlab run   capstone-v07-sbom-et-provenance
cd labs/capstone/v07-sbom-et-provenance/challenge/work
act pull_request
dsoxlab check capstone-v07-sbom-et-provenance
```

The tests play your pipeline on a pull request, then on a copy whose image
installs a package outside the lock. They also run your verification script
with a fake `gh`, to read what it requires.
