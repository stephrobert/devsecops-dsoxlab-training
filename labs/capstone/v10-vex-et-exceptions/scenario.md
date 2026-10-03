# V10: every accepted finding is written, dated and published

## Situation

Until now, the notes-api pipeline only blocked at the HIGH threshold. The team
raises it to **MEDIUM**, for the image and for the configuration. Three
configuration findings come up at once:

- AWS-0090 on `infra/deploy.tf`: the releases bucket has no versioning;
- AWS-0090 on `infra/main.tf`: neither has the exports bucket;
- KSV-0125 on `deploy/k8s/deployment.yaml`: the image comes from a registry
  Trivy does not know.

On the image side, Trivy reports **pip 25.0.1**, from the base image, with
several MEDIUM vulnerabilities. notes-api never runs pip. Yet the images
already released contain it, and the scanners of those who run them report
them. The threat model names it: T-17, `open`.

The `challenge/work` directory holds the project as V9 left it.

SSDF practice targeted: RV.2 (assess, prioritize, and remediate vulnerabilities).

## Goal

1. The `config` and `image` analyses of Trivy **block at the MEDIUM
   threshold**.
2. What can be fixed is **fixed**: the releases bucket enables versioning,
   and the final image **no longer contains pip**.
3. What is accepted is a **dated exception** in `.trivyignore.yaml`: limited
   to its file, with its reason, and an expiry within six months.
4. `security/notes-api.openvex.json` is a **VEX** document that declares each
   pip vulnerability `not_affected` for the releases already shipped, with its
   justification, and nothing else.
5. Threat T-17 moves to `mitigated`, with its evidence.

A copy whose exceptions have expired must turn the pipeline red.

## Pointers

- `--ignorefile .trivyignore.yaml` reads the exceptions; an entry carries
  `id`, `paths`, `statement` and `expired_at`. `--skip-check-update` freezes
  the checks to those of the pinned Trivy version.
- The internal registry is unknown to Trivy, but a control already
  guarantees it: the V8 admission policy. An exception can rest on a
  **compensating control**, as long as it names it.
- OpenVEX: `"products": [{"@id": "pkg:pypi/pip@25.0.1"}]`, `"status":
  "not_affected"` and a standard `justification`. `--vex <file>` makes Trivy
  read it.
- Removing a useless tool beats explaining why its flaws do not count: the
  VEX serves the releases that can no longer be rebuilt.

## Check

```bash
dsoxlab check capstone-v10-vex-et-exceptions
```

Five checks, twenty points each. They play your pipeline with act, build your
image and the one of the previous release, analyse the latter with your VEX,
and replay the pipeline on a copy whose exceptions have expired.
