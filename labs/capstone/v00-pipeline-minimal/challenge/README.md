# V0: a pipeline that tests every change

## Situation

The team that maintains **notes-api** ships by hand. The tests exist, five
pytest tests in `tests/`, but nothing runs them: a change that breaks note
search reaches production if nobody thought of running them.

The `challenge/work` directory holds the project as the team hands it to you:
the application in `src/notes_api/`, its tests, `pyproject.toml` and its lock
file `uv.lock`. It also carries a `Dockerfile` and an `infra/` folder this lab
does not deal with: later versions of the common thread come back to them. No
workflow.

## Goal

A GitHub Actions workflow that, on every **push** and every **pull request**
to `main`, in a single job:

1. fetches the code;
2. installs the dependencies **exactly** as `uv.lock` describes them;
3. runs the tests.

A broken test must turn the pipeline red. So must a `pyproject.toml` changed
without updating `uv.lock`: CI installs what was locked and reviewed, not what
the index publishes that day.

SSDF practice targeted: PO.3 (implement the supporting toolchain that automates the checks).

## Pointers

- GitHub only reads workflows from `.github/workflows/`.
- `astral-sh/setup-uv` installs uv; `uv sync --locked` refuses a lock file
  that no longer matches `pyproject.toml`.
- `act -l` lists what act understood from your files; `act push` and
  `act pull_request` play the workflow.

## Check

```bash
dsoxlab check capstone-v00-pipeline-minimal
```

Five checks, twenty points each. They play your workflow with act on the
project, then on copies broken on purpose: a test that no longer passes, an
out-of-sync lock file, a pull request. Docker must answer (`docker info`).

## The minimal pipeline

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
