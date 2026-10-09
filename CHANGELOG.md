# Changelog

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

All notable changes to this project are recorded in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/).

This repository is a **content catalog**, not a library. A version is
published by a tag, which produces a signed archive (see
[RELEASING.md](./RELEASING.md)); the unit that matters remains the lab, and for
this catalog, the version of the common thread.

## [0.1.0] - 2026-10-09

### Added

- **The catalog**, on the structure of the Kubernetes, Linux and Terraform
  catalogs: `meta.yml` and `meta.fr.yml` contract, reference solutions
  encrypted with ansible-vault under `solution/`, replayed by
  `scripts/verify-solutions.py`, repository meta-tests, bilingual READMEs whose
  catalog is generated.
- **The NIST SSDF 1.1 objective grid** (`curriculums.yml`), read from the
  official PDF: 19 practices in four groups, PW.3 absent. Each version cites
  the practice it implements, and `tests/test_curriculums.py` refuses a missing
  code or a contradictory label.
- **Links computed per language.** `scripts/gen_doc_url_en.py` reads the
  site's `translationOf` fields, the English README points to the translation
  when it exists, and `tests/test_liens_par_langue.py` refuses a link in the
  wrong language.
- **`verify-solutions.py --deux-sens`**, which also plays each suite on the
  fixtures alone and requires that no test passes.
- **`capstone-v00-pipeline-minimal`**, the first version of the common thread:
  `notes-api`, a Flask service and its five tests, gets its first pipeline.
  Five checks played with act 0.2.89: the shipped code passes, pytest really
  runs, a broken test and an out-of-sync `uv.lock` turn the pipeline red, a
  pull request triggers the same check. Proven both ways, then against two
  faulty solutions: a `uv sync` without `--locked` loses the lock check, an
  `echo "5 passed"` instead of pytest loses three.
- **`capstone-v01-modele-de-menace`**: notes-api gets its STRIDE threat model,
  checked by a team tool the pipeline runs on every push. Five checks: the
  model is valid, every route of `app.py` is analysed in it, the SQL injection
  of `/notes/search` is named and stays open, a broken model turns the
  pipeline red, the pipeline stays green and still tests. Proven both ways,
  then against three faulty variants that each lose only the targeted check
  (two for the missing checker).
- **`capstone-v02-secrets-et-sast`**: gitleaks and Semgrep become two blocking
  gates of the pipeline, the injection of `/notes/search` is fixed with a
  parameterised query, a regression test attempts it, and the threat model
  declares it mitigated with that test as evidence. The booby-trapped copy adds
  the injection to a new route no test covers: a first version reintroduced it
  into `/notes/search`, where the regression test turned the pipeline red even
  with a Semgrep that did not block.
- **`capstone-v03-sca-et-triage`**: osv-scanner 2.6.0 becomes a blocking
  gate on `uv.lock`. The starting point adds a signed import route, verified
  with `ecdsa`: eight known vulnerabilities, seven with a fixed version, and
  the Minerva attack (GHSA-wj6h-64fc-37mp), which has none. The seven are
  fixed by upgrading, the eighth is triaged in `osv-scanner.toml` with a
  reason checked against the code (notes-api only verifies) and an expiry
  date within six months; a copy whose exception has expired turns the
  pipeline red. Proven both ways, then against four faulty variants: a
  non-blocking scanner, fixable vulnerabilities excused instead of fixed, an
  exception without a near expiry, a reason that cites nothing.
- **`capstone-v04-identite-sans-secret`**: the deploy job no longer reads an
  AWS access key from the repository secrets. It obtains an OIDC token, the
  only job allowed to, only on a push on main, and assumes a role whose trust
  policy lives in a JSON file. The checks evaluate that policy against five
  tokens (main, work branch, pull request, another repository, another
  audience), because act cannot provide an OIDC token: measured with
  configure-aws-credentials v6.3.0, a role and a static key fail the same way
  under act. The starting point closes the Minerva exception of V3 as its
  review planned, by moving the signature check to `cryptography`. Proven
  both ways, then against four faulty variants that each lose only the
  targeted check.
- **`capstone-v05-pipeline-durci`**: the pipeline audits every workflow before
  the tests, actionlint 1.7.12 for syntax then zizmor 1.30.1 for security,
  both blocking. A welcome workflow on `pull_request_target`, which checked
  out and ran the proposed code and pasted the title into a script, is
  rewritten to run nothing from the pull request; CODEOWNERS, evaluated the
  way GitHub does (last match wins), sends the workflows, the infrastructure
  and the security decisions to `@acme/security`. The booby-trapped copy is a
  pwn request that only zizmor sees: a first version used a template
  injection, which actionlint also reports, so the pipeline turned red even
  with a zizmor that did not block. Proven both ways, then against four
  faulty variants.
- **`capstone-v06-image-et-iac`**: Trivy 0.75.0 (signature checked with
  cosign, far from the 0.69.4 to 0.69.6 releases compromised in March 2026)
  analyses the configuration, then the built image, both blocking at HIGH and
  CRITICAL. The Dockerfile moves to two stages from pinned bases, installs
  from `uv.lock` without the dev group, applies the published Debian fixes
  and runs as uid 10001; the infrastructure drops SSH, closes the API to the
  Internet, blocks public access to the buckets and encrypts them with a
  rotated KMS key. Measured on 2026-10-03: the python:3.12-slim image of the
  day already carried a HIGH CVE of libpcre2 fixed in Debian, hence the
  rebuild with the fixes and `--ignore-unfixed`. Proven both ways, then
  against four faulty variants.
- **`capstone-v07-sbom-et-provenance`**: Trivy produces the CycloneDX SBOM of
  the built image, which the team's `scripts/check_sbom.py` confronts with
  `uv.lock` (packages of the application environment only, not the pip of
  the base image); a package installed outside the lock turns the pipeline
  red. The deploy job attests the provenance of the archive with
  attest-build-provenance v4.2.2 and publishes the SBOM next to it, and
  `scripts/verify_release.sh` requires the repository, the signer workflow,
  the ref and a GitHub-hosted runner; the checks run it with a fake `gh` that
  records its arguments, act providing no OIDC token. The SBOM is produced by
  Trivy rather than syft: the syft image carries no cosign signature to
  verify. Artifacts stay on upload-artifact v5.0.0 and download-artifact
  v6.0.0, the later versions failing under act 0.2.89. Proven both ways,
  then against four faulty variants.
- **`capstone-v08-admission-signee`**: notes-api reaches a cluster. The
  learner writes the Kyverno admission policies of the `notes-api`
  namespace, an `ImageValidatingPolicy` for the platform signature and a
  `ValidatingPolicy` for the internal registry, in `policies.kyverno.io/v1`
  since Kyverno 1.19 deprecates `ClusterPolicy`. The checks set up kind
  1.37, a registry reachable as `registry.notes.internal` from the nodes and
  from the Pods, and Kyverno 1.19.1, then request admissions in
  `--dry-run=server`: signed image admitted, unsigned or foreign-key image
  refused, Deployment included, Docker Hub refused in `notes-api` and still
  admitted in `default`. Measured on 2026-10-03: cosign 3.1 writes its
  signature in the new bundle format by default, which Kyverno 1.19.1 does
  not find ("no signatures found"); the bench signs with
  `--new-bundle-format=false`. `mise.toml` now pins kind 0.33.0, kubectl
  1.37.1, helm 4.3.0 and cosign 3.1.3. Proven both ways, then against four
  faulty variants.
- **`capstone-v09-runtime-cloisonne`**: the notes-api namespace enforces the
  restricted Pod Security Standard, the Deployment drops every capability,
  forbids escalation and mounts no API token, and NetworkPolicies only let
  the ingress controller in and DNS out. The checks build the learner's
  image, load it into kind, apply the manifests and measure the real traffic
  from `ingress`, from `default` and from notes-api itself; they read
  `/proc/self/status` (`NoNewPrivs`, `CapBnd`) rather than the manifest. The
  V6 image already runs as uid 10001, so a check on the uid alone would have
  passed on the starting point. Runtime detection (Falco) is left out: it
  needs a real machine, not a cluster in Docker. Proven both ways, then
  against four faulty variants; a fifth, without the deny-all policy, rightly
  passes, the two other policies already isolating the pods they select.
- **`capstone-v10-vex-et-exceptions`**: the Trivy gates move to MEDIUM. Three
  configuration findings come up: versioning on the releases bucket is
  fixed, the exports bucket (AWS-0090) and the internal registry unknown to
  Trivy (KSV-0125, the V8 admission policy being the compensating control)
  become dated exceptions in `.trivyignore.yaml`. pip 25.0.1 of the base
  image leaves the final image, and a VEX document declares its
  vulnerabilities `not_affected` for the releases already shipped. The
  checks build the previous image from the fixtures and analyse it with the
  learner's VEX; the pip CVE identifiers are read from Trivy at run time,
  not written in the tests. Measured on 2026-10-03: without
  `--ignore-unfixed`, the image carries over 150 Debian CVEs without a fix,
  far too unstable to found a lab on; pip 25.0.1, frozen by the base image
  digest, carries 5 MEDIUM CVEs fixed upstream. Proven both ways, then
  against four faulty variants.
- **`capstone-v11-slo-et-dora`**, the last version of the common thread: the
  availability SLO of notes-api (99.5% over 28 days) becomes a Prometheus
  alert that pages at a 14.4 burn rate over a long and a short window, with
  its promtool unit tests; a runbook the alert links to; and `scripts/dora.py`,
  which computes the four DORA metrics from the deployment and incident
  journals. The checks submit the learner's alert to their own series with
  promtool 3.15.0, asking for no alert and reading what promtool actually
  saw under `got:`, so the alert labels stay free; and they run the DORA
  script on three fabricated journals against an independent reference.
  Proven both ways, then against four faulty variants.
- **`tests/test_fixtures_declarees.py`**: each file of `fixtures/` must be
  declared in `runtime.fixtures`. The V5 `lab.yaml` omitted
  `infra/github-oidc-trust.json`: the solution replay copies the whole
  folder and never saw it, while a learner started with `dsoxlab run` would
  have received a project whose threat model fails from the start.
- **`infra/main.tf` passes `terraform validate`** from V0 on: the description
  "SSH d'administration" contained an apostrophe the AWS provider refuses.
- **`capstone-v09b-detection-falco`**, a side version between V9 and V10 and
  the first lab of the catalog on a real machine: on an Ubuntu 24.04 VM
  provisioned by dsoxlab (KVM or Incus, network `lab-devsecops`
  10.10.60.0/24), notes-api runs in Docker under Falco 0.45.0 and its modern
  eBPF probe, installed from its repository after the signing key
  fingerprint is checked. The learner writes the Falco rules of notes-api;
  the checks trigger a shell and a write themselves, with a unique marker,
  then what must trigger nothing, and read the alerts of the learner's rules
  only. Measured on 2026-10-03: `output_fields` only carries the fields the
  rule output cites, and `falco -V` on the learner's file alone fails on the
  macros of the default rules. Proven both ways by `valider-labs.py`, then
  against three faulty rule sets that each lose only the targeted check.
- **Attestation**: the thirteen labs are VALIDE in `validation-labs.json`,
  0 then 100. `jouer_act` passes `--rm` to act: without it, the container of
  every failed job stays behind, and the booby-trapped copies fail on
  purpose. `valider-labs.py` plays the `solution.yaml` of a `vm` lab with
  ansible-playbook, and `verify-solutions.py` leaves `vm` labs to it.

[Unreleased]: https://github.com/stephrobert/devsecops-dsoxlab-training/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/stephrobert/devsecops-dsoxlab-training/releases/tag/v0.1.0
