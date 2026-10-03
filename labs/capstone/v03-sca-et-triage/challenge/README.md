# Challenge: dependency scanning and triage

5 tasks, 100 points, 45 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`pyproject.toml`, `uv.lock`, `Dockerfile` and `threat-model.yml`, and you
create `osv-scanner.toml`.

### Task 1: the pipeline scans the dependencies and passes (20 pts)

`act push` is green, and the job shows osv-scanner reading `uv.lock`, then the
tests.

### Task 2: the vulnerable lock stops the pipeline (20 pts)

In a copy that gets the starting `pyproject.toml` and `uv.lock` back, the job
fails on the dependency scan.

### Task 3: the fixable vulnerabilities are fixed (20 pts)

flask, werkzeug and ecdsa are locked at a fixed version, the Dockerfile
installs the same ones, and `osv-scanner.toml` excuses no vulnerability that
has a fix.

### Task 4: the exception is justified, dated, and the model up to date (20 pts)

The Minerva attack on ecdsa is accepted with a reason that cites signature
verification, and an expiry date within six months. Threat T-08 is
`mitigated`, with its evidence.

### Task 5: an expired exception raises the alarm again (20 pts)

In a copy whose `ignoreUntil` has passed, the job fails on
GHSA-wj6h-64fc-37mp.
