# V5: the pipeline is code to defend too

## Situation

notes-api opens up to contributions. To welcome each pull request, the team
added `pr-welcome.yml`: it runs the tests of the contribution and thanks the
author with a comment. Since the comment needs a write token, forks included,
the workflow runs on `pull_request_target`.

That trigger runs with the repository's privileges. Yet the workflow checks
out the code of the pull request and runs it: anyone who opens a pull request
runs their code with a write token. The pull request title is also pasted into
the comment script: a well-chosen title becomes a command. The threat model
named it: T-13, `open`.

Nothing reviews the workflows, and a change to `.github/` goes through review
like any other file.

The `challenge/work` directory holds the project in that state.

SSDF practice targeted: PS.1 (protect all forms of code from unauthorized access and tampering).

## Goal

1. The pipeline **audits every workflow** before the tests, and each audit
   **blocks**: actionlint for syntax, zizmor for security flaws.
2. No workflow triggered by `pull_request_target` **runs** what the pull
   request brings, and no script contains a field its author controls (title,
   body, branch name).
3. A **CODEOWNERS** file requires `@acme/security` to review `.github/`,
   `infra/`, `osv-scanner.toml` and `threat-model.yml`, and gives the rest of
   the code an owner.
4. Threat T-13 moves to `mitigated`, with its evidence.

The project must stay green on a pull request. A copy that adds a workflow
running the code of a pull request in a privileged trigger, or a workflow
with an impossible cron, must turn it red.

## Pointers

- actionlint and zizmor run as `docker://` steps, images pinned by digest:
  `rhysd/actionlint`, and `ghcr.io/zizmorcore/zizmor` with `--offline`. In
  a job, the first failing step stops the next ones: the order decides what
  each error lets you see.
- The tests of a contribution already run in `ci.yml`, on `pull_request`,
  without secrets or a write token.
- A zizmor suppression is written as a comment on the targeted line, with its
  reason: `# zizmor: ignore[<rule>] <why>`.
- In CODEOWNERS, the **last** matching line wins.

## Check

```bash
dsoxlab check capstone-v05-pipeline-durci
```

Five checks, twenty points each. They play your pipeline with act on a pull
request and on booby-trapped copies, reread the workflows, and evaluate
CODEOWNERS the way GitHub does.

## A hardened pipeline

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`.github/workflows/pr-welcome.yml` and `threat-model.yml`, and you create a
CODEOWNERS file.

### Task 1: the workflow audit runs and the project passes (20 pts)

`act pull_request` is green, zizmor reports no flaw, and the tests run.

### Task 2: a booby-trapped pull request stops the pipeline (20 pts)

In a copy that adds a `pull_request_target` workflow checking out the code
of the pull request, the job fails on zizmor.

### Task 3: a workflow syntax error stops the pipeline (20 pts)

In a copy that adds a workflow with an impossible cron, the job fails on
actionlint.

### Task 4: no privileged workflow runs the pull request (20 pts)

No workflow on `pull_request_target` checks out or runs the proposed code,
and no script contains a field controlled by the pull request author.

### Task 5: the security team reviews the sensitive paths (20 pts)

CODEOWNERS assigns the workflows, the infrastructure, the triage and the
threat model to `@acme/security`, gives the application code an owner, and
T-13 is `mitigated` with its evidence.
