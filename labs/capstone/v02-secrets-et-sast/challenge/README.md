# Challenge: blocking secrets and SAST

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
