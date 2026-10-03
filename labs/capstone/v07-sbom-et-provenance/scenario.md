# V7: know what ships, prove where it comes from

## Situation

The notes-api pipeline analyses the code, the dependencies, the workflows,
the image and the infrastructure, then the `deploy` job publishes an archive
to the `notes-api-releases` bucket. Whoever then deploys that archive knows
nothing about it: neither what it contains nor which pipeline built it. An
archive replaced in the bucket, or built from a branch, would deploy like the
others. The threat model names it: T-14, `open`.

The team wrote `scripts/check_sbom.py`: it confronts a CycloneDX SBOM with
`uv.lock` and reports any package of the application environment that is not
locked, or not at the right version.

The `challenge/work` directory holds the project as V6 left it, with that
tool.

SSDF practices targeted: PS.2 (provide a mechanism for verifying software release integrity), PS.3 (archive and protect each software release).

## Goal

1. The pipeline produces the **SBOM of the built image**, in CycloneDX,
   **confronts it with `uv.lock`** using the team's tool, and keeps the SBOM
   as an artifact of the run.
2. The deploy job **attests the provenance** of the archive it publishes (a
   SLSA attestation signed through Sigstore), and publishes the SBOM next to
   it.
3. `scripts/verify_release.sh <archive>` **verifies the attestation** before
   any deployment: repository `acme/notes-api`, workflow `ci.yml`, ref
   `refs/heads/main`, a GitHub-hosted runner. It fails when the verification
   fails.
4. Threat T-14 moves to `mitigated`, with that script as evidence.

The project must stay green on a pull request. A copy whose image installs a
package outside the lock must turn it red.

## Pointers

- Trivy, already pinned in V6, produces an SBOM:
  `image --input notes-api.tar --format cyclonedx --output sbom.cdx.json`.
- act cannot provide an OIDC token: it cannot sign an attestation. The checks
  therefore reread the deploy job, and run your verification script with a
  fake `gh` that records its arguments.
- Under act 0.2.89, `upload-artifact` beyond v5 and `download-artifact`
  beyond v6 fail against the local artifact server: pin v5.0.0 and v6.0.0.
- `gh attestation verify --help` lists the options that restrict the accepted
  signer.

## Check

```bash
dsoxlab check capstone-v07-sbom-et-provenance
```

Five checks, twenty points each. They play your pipeline with act on a pull
request and on a booby-trapped copy, reread the deploy job, and run your
verification script.
