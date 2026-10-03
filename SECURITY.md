# Security policy

**Language:** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Supported versions

`devsecops-dsoxlab-training` is under active development. Security fixes
are applied to the latest version of the `main` branch.

| Version | Supported |
| --- | --- |
| latest (`main`) | yes |
| older | no |

## Reporting a vulnerability

**Do not open a public issue for a security vulnerability.**

If you believe you have found one, report it privately:

- Preferred: open a
  [private security advisory](https://github.com/stephrobert/devsecops-dsoxlab-training/security/advisories/new)
  on GitHub.
- Otherwise, use the contact details published on
  <https://blog.stephane-robert.info>.

Please include:

- a description of the vulnerability and its impact,
- the steps to reproduce it (command, environment, `act --version`,
  `dsoxlab --version`),
- any relevant logs or proof of concept.

We will keep you posted on the fix and credit you in the release notes if you
wish.

## Disclosure policy

We practise coordinated disclosure and commit to the following timelines,
counted from the moment we receive your report:

| Step | Target |
| --- | --- |
| Acknowledging your report | within **48 hours** |
| Initial assessment and severity triage | within **5 days** |
| Fix released, or a written remediation plan | within **30 days** |
| Public disclosure of the vulnerability | within **90 days** |

We publish the advisory as soon as a fix is available, or at the **90-day** mark
at the latest, whichever comes first. If a vulnerability is being actively
exploited, we may disclose sooner to protect users. If a complex fix needs more
time, we tell you before the deadline and agree a new date with you, rather than
letting it lapse in silence.

## Scope

This repository ships **lab content**: the `notes-api` project at each step of
the common thread, fixtures, pytest tests that play GitHub Actions workflows
with act, and encrypted reference solutions, run by the external `dsoxlab` CLI
on the learner's machine.

`notes-api` is **deliberately vulnerable**: a concatenated SQL query, a pinned
vulnerable dependency, a Dockerfile running as root, an over-permissive
Terraform. These flaws are the subject of the labs, which have them fixed
version after version. They are not vulnerabilities of the repository, and are
not reported here.

In scope:

- dangerous or malicious lab material, in particular a workflow that would
  reach an undeclared destination or exfiltrate data from the learner's
  machine;
- a real secret, a private key or an API token committed by mistake;
- a reference solution shipped in clear, which spoils the lab and stays in the
  history;
- an action or an image referenced without pinning by SHA or digest in what
  the repository ships as a reference.

Out of scope:

- vulnerabilities of the `dsoxlab` engine itself, which belong to
  [its own repository](https://github.com/stephrobert/dsoxlab);
- those of act, of the runner image, of GitHub actions or of any third-party
  dependency, to be reported to their respective projects;
- the deliberate flaws of `notes-api` described above;
- a lab that fails or scores wrongly: that is a defect, opened as a public
  issue.

## What this repository will never ask of you

No lab requires a real secret. The secrets the tests inject to see a pipeline
fail are **fake**, written in a temporary copy of the project and destroyed
with it.
