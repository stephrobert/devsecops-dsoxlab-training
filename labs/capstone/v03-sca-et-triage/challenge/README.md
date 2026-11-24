# V3: dependencies, what you fix and what you own

## Situation

Since V2, the pipeline stops a secret and an injection. It does not look at
what the project **installs**. The `uv.lock` lock pins flask and werkzeug at
3.0.3, and the team has just added a `POST /notes/import` route, which checks
the ECDSA signature of a batch of notes with the `ecdsa` library 0.19.1. These
three packages have published vulnerabilities, and nothing says so.

The `challenge/work` directory holds the project as V2 left it, with the
import route, its tests and its threat T-11.

SSDF practices targeted: RV.2 (assess, prioritize, and remediate vulnerabilities), PW.4 (reuse existing, well-secured software components).

## Goal

1. The pipeline runs a **dependency scan** on `uv.lock`, before the tests, and
   it **blocks**: a known vulnerability turns the job red.
2. Every vulnerability that has a **fixed version** is fixed: the package goes
   up, the lock follows, and so does the Dockerfile.
3. The vulnerability that has **no fix** is triaged in `osv-scanner.toml`: a
   reason that can be checked against the code, and an expiry date within six
   months.
4. The threat model tells the truth: the threat on dependencies (T-08) moves
   to `mitigated`, with its evidence.

The project must stay green. A copy that gets the starting lock back, or whose
exception has expired, must turn it red.

## Pointers

- `ghcr.io/google/osv-scanner` runs as a `docker://` step, image pinned by
  digest: `scan source -r .` reads the lock and queries the OSV database.
- Run it on the project as it is first: the `FIXED VERSION` column says what
  can be fixed, and `--` what never will be.
- Before accepting a risk, read the advisory: which functions are affected,
  and does notes-api call them?
- osv-scanner reads `uv.lock`, not the `pip install` line of the Dockerfile.

## Check

```bash
dsoxlab check capstone-v03-sca-et-triage
```

Five checks, twenty points each. They play your pipeline with act on the
project and on booby-trapped copies, and reread the lock, the Dockerfile, the
triage file and the threat model.

## Dependency scanning and triage

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
