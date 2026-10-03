# Challenge: an identity without a secret

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
