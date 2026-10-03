# Challenge: the minimal pipeline

5 tasks, 100 points, 30 minutes.

The project is in `challenge/work`. Everything happens in
`.github/workflows/`, which you create. The tests play your workflow with act
and read what it produces; they do not read your commands.

### Task 1: the shipped code passes (20 pts)

`act push` plays a single job, green, on the project as it is.

### Task 2: the tests run in the pipeline (20 pts)

The job shows pytest collecting `tests/test_app.py` and reporting its result.

### Task 3: a broken test turns the pipeline red (20 pts)

In a copy where `/health` no longer answers `ok`, the job fails.

### Task 4: an out-of-sync lock file turns the pipeline red (20 pts)

In a copy where `pyproject.toml` declares a dependency missing from
`uv.lock`, the job refuses to install.

### Task 5: pull requests go through the same check (20 pts)

`act pull_request` plays the same job, green, tests included.
