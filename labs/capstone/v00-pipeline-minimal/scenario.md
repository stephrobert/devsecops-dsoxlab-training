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
