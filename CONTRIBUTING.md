# Contributing to devsecops-dsoxlab-training

**Language:** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

This repository is a **lab catalog** consumed by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. Contributions are new
versions of the common thread, fixes and translations. The CLI lives in its own
repository: do not add engine code here.

## Setup

```bash
uv tool install dsoxlab        # the CLI (external tool)
git clone https://github.com/stephrobert/devsecops-dsoxlab-training.git
cd devsecops-dsoxlab-training
mise install                   # act, uv and Python at the versions of mise.toml
dsoxlab validate-structure     # check the contract
```

Docker must answer (`docker info`): act plays the learner's pipeline in the
`ubuntu-24.04` runner image, pinned by digest. The first versions all run in
`runtime: shell`, with no VM and no cloud account.

## The golden rule: a lab is proven both ways

A passing test proves nothing until you have seen **fail** what must fail.
Before committing a lab:

```bash
python3 scripts/verify-solutions.py --deux-sens --lab capstone/<lab>
```

The script plays the lab's suite twice: on the fixtures alone, where **no**
test may pass, then with the decrypted reference solution on top, where **all**
must pass. `scripts/valider-labs.py` then attests it through the real dsoxlab
commands, in `validation-labs.json`.

Ask yourself, for each test: **would it be green if the learner did nothing?**
The common thread makes the trap frequent, since a version's starting point is
the previous version's solution: it already does everything the earlier
versions asked for. Each test therefore requires what is **new** in the
version.

Also prove each test against a **faulty** solution: a `uv sync` without
`--locked`, an `echo "5 passed"` instead of pytest. The targeted test must fall,
and only that one.

## What the tests must read

What the pipeline **produces**, never what the YAML contains:

```python
# NO: rereading what the learner wrote
assert "uv sync --locked" in workflow.read_text()

# YES: play the workflow on a copy broken on purpose, and read the result
res = jouer_act(copy_with_out_of_sync_lock, "push")
assert res.job(job) == "failure"
```

`jouer_act()` and `copie_temporaire()` are the two doors. Reading the YAML is a
last resort, and the test says why: some properties (`permissions:`, pinning an
action by SHA) are in the text and leave no trace in what act produces.

## Anatomy of a lab

```text
labs/capstone/<lab>/
├── lab.yaml            # the contract (id, level, runtime, fixtures, validation…)
├── lab.fr.yaml         # FR override of title/description ONLY
├── README.md / README.fr.md        # the lesson
├── scenario.md / scenario.fr.md    # the situation, the target state, the SSDF practice targeted
├── fixtures/           # notes-api as the previous version left it
└── challenge/
    ├── README.md / README.fr.md    # the mission, no step-by-step
    ├── hints.yaml                  # base64 hints, three cost tiers
    └── tests/test_functional.py    # the proof
solution/capstone/<lab>/            # reference solution, encrypted with ansible-vault
```

There is no `setup.yaml` and no `cleanup.yaml` here: `runtime.fixtures`
declares what is copied, preserving subdirectories, and `dsoxlab clean` removes
the working directory.

## Proposing a version

- **Start from the previous solution.** A version's fixtures are the decrypted
  solution of the one before, and nothing else: a fix to the V2 solution is
  carried over to the V3 fixtures.
- **Cite the SSDF practice implemented**, in both scenarios: "SSDF practice
  targeted: PS.1 (label)" and "Pratique SSDF visée : PS.1 (libellé)".
  `tests/test_curriculums.py` refuses a code missing from the grid or a label
  that contradicts it.
- **Point `doc_url` to the French lesson** the version practises: the CLI reads
  it. The English READMEs point to the translation, computed by
  `scripts/gen_doc_url_en.py`.
- **Pin everything the solution references**: each action on its commit SHA
  with the version as a comment, each image by digest, and date the measurement
  in a comment.

## Local checks before opening a PR

```bash
dsoxlab validate-structure                                 # the meta.yml + lab.yaml contract
python3 scripts/verify-solutions.py --deux-sens            # each lab, both ways
python3 -m pytest tests/ -q                                # the repository meta-tests
python3 scripts/gen_doc_url_en.py <path to the site repo>  # the translation table
python3 scripts/gen_catalog.py                             # refresh the README catalog
```

The catalog is generated from the real `lab.yaml` files: run `gen_catalog.py`
after adding or renaming a lab, and `--check` to verify.

## Conventions

- **Lab id:** `<section>-<slug>`, where `<section>/<slug>` is its path under
  `labs/`: `capstone-v00-pipeline-minimal` lives in `labs/capstone/v00-pipeline-minimal`.
- **Commits:** in French, a factual subject saying **what changed and why**,
  with no conventional prefix. The body tells what was measured, including the
  measurements discarded along the way: they are often worth more than the
  result.
- **i18n:** the file without suffix is English (the repository's official
  language), the `*.fr.md` is the French translation. Both must say the same
  thing.
- **Style:** no emoji and no em dash in what the learner reads. Assertion
  messages teach: they say what is wrong and why, not only what was expected.

## Pull requests

Work on a dedicated branch, keep `dsoxlab validate-structure` green, write a
clear description and link the version or issue addressed.
