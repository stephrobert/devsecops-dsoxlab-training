# Challenge: the threat model

5 tasks, 100 points, 40 minutes.

The project is in `challenge/work`. You write `threat-model.yml` there, and
you evolve `.github/workflows/ci.yml`. The tests read your model by
confronting it with the code, and play your pipeline with act.

### Task 1: the model is valid (20 pts)

`uv run python scripts/check_threat_model.py threat-model.yml` returns 0.

### Task 2: every route of the application is analysed (20 pts)

Every route `src/notes_api/app.py` declares is the component of at least one
threat, named like the route.

### Task 3: the SQL injection is identified, and stays open (20 pts)

A tampering or disclosure threat targets `GET /notes/search`, and its status is
`open`.

### Task 4: a broken model turns the pipeline red (20 pts)

In a copy where a threat loses its mitigation, the job fails on the checker.

### Task 5: the pipeline checks the model and stays green (20 pts)

On the project as it is, the job is green, checks the model and still runs
the tests.
