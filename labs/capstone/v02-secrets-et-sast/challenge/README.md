# V2: two gates that block, and the flaw they stop

## Situation

The V1 threat model named what the code carries: `GET /notes/search` pastes
the search term into its SQL query, and the threat is `open`. The pipeline
tests, checks the model, but looks for neither secrets nor dangerous patterns.
A token pasted into the code, or a second concatenated query, would reach
`main` without a word.

The `challenge/work` directory holds the project as V1 left it.

SSDF practices targeted: PW.7 (analyze human-readable code to identify vulnerabilities), PW.5 (create source code by adhering to secure coding practices).

## Goal

1. The pipeline runs a **secret scan** and a **static analysis**, before the
   tests, and each one **blocks**: a finding turns the job red.
2. The injection of `/notes/search` is **fixed in the code**, and a regression
   test attempts it: it would fail if the query became concatenated again.
3. The threat model tells the truth about the code: the tampering threat on
   `GET /notes/search` moves to `mitigated`, and cites that test as evidence.

The project must stay green. A copy that carries a secret, or that adds a
route concatenating a value into a query, must turn it red, and on the right
gate.

## Pointers

- Both tools run as `docker://` steps, image pinned by digest:
  `zricethezav/gitleaks` and `semgrep/semgrep`.
- A scanner that writes its findings but returns 0 blocks nothing: check the
  exit code of each one.
- `sqlite3` accepts `?` parameters: the value travels apart from the query.

## Check

```bash
dsoxlab check capstone-v02-secrets-et-sast
```

Five checks, twenty points each. They play your pipeline with act on the
project and on booby-trapped copies, query the application, and reread the
threat model.

## Blocking secrets and SAST

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You evolve `.github/workflows/ci.yml`,
`src/notes_api/app.py`, `tests/test_app.py` and `threat-model.yml`.

### Task 1: both gates run and the project passes (20 pts)

`act push` is green, and the job shows the secret scan, the static analysis
and the tests.

### Task 2: a secret stops the pipeline (20 pts)

In a copy that carries a GitHub token, the job fails on the secret scan.

### Task 3: a SQL injection stops the pipeline (20 pts)

In a copy that adds a route concatenating a value into its query, the job
fails on the static analysis.

### Task 4: the search resists the injection (20 pts)

`GET /notes/search?q=' OR '1'='1` returns no note.

### Task 5: the model says the threat is mitigated, and its evidence (20 pts)

The tampering threat on `GET /notes/search` is `mitigated`, and its evidence is
a regression test that attempts the injection.
