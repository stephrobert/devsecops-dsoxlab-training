# V4: publishing without holding a key

## Situation

The notes-api pipeline now publishes every release to the
`notes-api-releases` bucket. To do so, the `deploy` job reads two repository
secrets, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: the key of an IAM
user created by `infra/deploy.tf`. That key never expires. A compromised
action, a malicious workflow change or a chatty log are enough to leak it, and
it then publishes from anywhere. The threat model names it: T-12, `open`.

The job also starts on any push, work branches included.

Meanwhile, the team kept the commitment of the V3 triage: the signature check
moved to `cryptography`, `ecdsa` left the dependencies, and
`osv-scanner.toml` no longer holds an exception.

The `challenge/work` directory holds the project in that state. The GitHub
repository is `acme/notes-api`, the AWS account `123456789012`.

SSDF practice targeted: PO.5 (implement and maintain secure environments for software development).

## Goal

1. The `deploy` job authenticates through **OIDC**: it assumes an IAM role,
   with no key at all. No workflow reads a repository secret any more.
2. Only that job may request a token (`id-token: write`), and it only starts
   on a **push on main**: neither a work branch nor a pull request publishes.
3. In `infra/`, the IAM user and its key give way to an OIDC provider and a
   role. Its **trust policy** lives in a JSON file and only accepts a token
   issued for main of `acme/notes-api`, addressed to STS.
4. Threat T-12 moves to `mitigated`, with that policy as evidence.

## Pointers

- act cannot provide an OIDC token: the deployment fails under act whatever
  you write. The checks know it, and play the pipeline on a work branch and on
  a pull request, where it must not start.
- The GitHub token carries the repository and the ref in its `sub` claim, for
  instance `repo:acme/notes-api:ref:refs/heads/main`.
- A wildcard in a trust condition is a door: ask yourself which token from
  another context it would let through.

## Check

```bash
dsoxlab check capstone-v04-identite-sans-secret
```

Five checks, twenty points each. They play your pipeline with act on a branch
and a pull request, reread the workflows and the infrastructure, and evaluate
your trust policy against the tokens of five situations.

## An identity without a secret

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`infra/deploy.tf` and `threat-model.yml`, and you create the role's trust
policy in `infra/`.

### Task 1: neither a branch nor a pull request deploys (20 pts)

On a push to a work branch and on a pull request, the tests pass and the
deploy job does not start.

### Task 2: no static key, neither in the pipeline nor in the infra (20 pts)

No workflow reads a repository secret, and `infra/` no longer declares an IAM
user or an access key.

### Task 3: only the deploy job gets an OIDC token (20 pts)

`id-token: write` is declared on that job alone, which assumes a role
(`role-to-assume`) with an action pinned by SHA.

### Task 4: the trust policy only accepts main (20 pts)

The role reads its policy from a JSON file. Evaluated against five tokens, it
only accepts the one of a push on main of `acme/notes-api` addressed to STS.

### Task 5: the model says the key is gone, and its evidence (20 pts)

Threat T-12 is `mitigated`, and its evidence is the trust policy.
