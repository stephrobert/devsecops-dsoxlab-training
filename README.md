# DevSecOps Training: the common thread, from V0 to V11

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/devsecops-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/devsecops-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/devsecops-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/devsecops-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/devsecops-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/devsecops-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Hands-on **DevSecOps** training, driven by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. This repository is the
**capstone** of the [DevSecOps course](https://blog.stephane-robert.info/en/docs/devsecops/)
on blog.stephane-robert.info, written as a **common thread**: a single project,
`notes-api`, hardened version after version, one version per module of the
course.

## What it is

`devsecops-dsoxlab-training` is a **content repository**, not an application.
It provides:

- a **single project**, `notes-api`, a small Flask service shipped with its
  flaws: a concatenated SQL query, a vulnerable dependency, a Dockerfile
  running as root, an over-permissive Terraform, no pipeline;
- **labs** whose starting point is the solution of the previous one, from V0
  (a minimal pipeline) to V11 (the project's delivery metrics);
- **automated validation** that plays the learner's pipeline with act and
  judges what it produces, never the commands typed;
- an **objective grid**, the NIST SSDF: each version cites the practice it
  implements;
- a **score** with hints of increasing cost.

The `dsoxlab` CLI is the single entry point: it sets up a lab, shows the
brief, validates, scores and reports. It lives in **its own repository** and is
installed **separately**.

## Requirements

- Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)
- `git`
- **A Docker that answers** (`docker info`): act plays the learner's pipeline
  in the `ubuntu-24.04` runner image, pinned by digest.
- **[`mise`](https://mise.jdx.dev/)**, which installs act 0.2.89, uv and Python
  at the versions of `mise.toml` (`mise install`). Any act release older than
  0.2.86 is vulnerable to CVE-2026-34041 and CVE-2026-34042.

No VM or cloud account for the first versions: everything plays on the
learner's machine, in `runtime: shell`. The versions that need a Kubernetes
cluster or a VM will declare it in their `lab.yaml`.

## Install

`dsoxlab` is published on [PyPI](https://pypi.org/project/dsoxlab/) and
installs as a standalone tool:

```bash
# 1. Install the dsoxlab CLI (external tool, stays out of this repo)
uv tool install dsoxlab        # or: pipx install dsoxlab

# 2. Clone this lab catalog, and install its tools
git clone https://github.com/stephrobert/devsecops-dsoxlab-training.git
cd devsecops-dsoxlab-training
mise install

# 3. Check the contract is valid
dsoxlab validate-structure
```

### Your first lab, in five minutes

```bash
dsoxlab list-labs                                # browse the catalog
dsoxlab run       capstone-v00-pipeline-minimal  # set up the starting state
dsoxlab challenge capstone-v00-pipeline-minimal  # read the mission
# ... you work in challenge/work ...
act push                                         # play your pipeline
dsoxlab check     capstone-v00-pipeline-minimal  # validate and score
```

`run` creates the lab's working directory and copies the declared fixtures
into it. Everything then happens in `challenge/work`: it is the only place you
modify, and `dsoxlab clean` removes it.

Stuck? `dsoxlab hint <id>` reveals a hint, whose cost is deducted from the
score.

### Keeping it up to date

```bash
git pull                       # the catalog
uv tool upgrade dsoxlab        # the engine
mise install                   # the pinned tools
```

The three evolve separately. A lab that fails after an upgrade of act or of
the runner image is a defect of the catalog: open an issue, the form comes
pre-filled by `dsoxlab support --issue`.

## How it works

### The declarative contract (two levels)

The catalog is described by data, not code, which keeps the `dsoxlab` engine
domain-agnostic:

- **`meta.yml`**, at the root, declares the repository's identity and the
  **order** of the versions, which is the order of play: it is never
  reordered;
- **`lab.yaml`**, per lab, declares its `skills`, its `level`, its `runtime`
  (type, fixtures), its `distros`, its `doc_url` and a `validation` block. A
  `lab.fr.yaml` overrides the `title` and the `description` in French, and
  nothing else.

`dsoxlab validate-structure` checks the whole contract, and
`tests/test_schemas_dsoxlab.py` checks each `lab.yaml` against the schema
published by dsoxlab.

### The lab lifecycle

```bash
dsoxlab list-labs              # browse the catalog
dsoxlab show      <id>         # a lab's metadata and state
dsoxlab run       <id>         # set up the starting state
dsoxlab challenge <id>         # read the mission, no step-by-step
dsoxlab hint      <id>         # reveal a hint (deducted from the score)
dsoxlab check     <id>         # run the tests, compute and record the score
dsoxlab clean     <id>         # remove the working directory
dsoxlab progress               # progress per section, average score
```

### Runtimes

| Runtime | What the lab needs |
|---|---|
| `shell` + act | a terminal, Docker and the tools of `mise.toml`. The tests play your pipeline with act, on your project and on copies broken on purpose. |

### The validation model

Validation **proves the state, it does not trust the learner**. Each lab ships
`pytest` tests under `challenge/tests/` that play the pipeline with act and read
what it produces: the job's result and the lines each step wrote. To see the
pipeline fail when it must fail, a test modifies a **copy** of the project: a
broken test, an injected secret, a vulnerable dependency. Your project is never
touched.

And a lab is proven **both ways**: the tests must fail before the work, and
pass after. `scripts/verify-solutions.py --deux-sens` checks it for every lab,
and `scripts/valider-labs.py` attests it through the real dsoxlab commands in
`validation-labs.json`.

The reference solutions live under `solution/`, **encrypted with
ansible-vault**: a solution shipped in clear spoils the lab, and git keeps it
forever.

### The objective grid: the NIST SSDF

Each version cites, in its scenario, the NIST SSDF practice it implements:
"SSDF practice targeted: PO.3". `curriculums.yml` holds the grid, its official
source and the date it was last checked, and `tests/test_curriculums.py`
refuses a code missing from the grid or a label that contradicts it.

### Scoring, hints, progress

`check` records a score (tests passed over total, minus the cost of the hints
revealed). Hints are **base64-encoded** in `challenge/hints.yaml`, so they are
not read by opening the file, and their cost grows with their precision. The
history lives in a SQLite database **local to this repository**.

### Links to the guides

A lab's `doc_url` is the French lesson, because dsoxlab reads it. The links of
the READMEs are **computed**: `scripts/gen_doc_url_en.py` reads the site's
`translationOf` fields, and `scripts/gen_catalog.py` points the English README
to the translation when it exists. `tests/test_liens_par_langue.py` refuses a
link in the wrong language.

## Catalog

<!-- LABS:START -->
### The common thread: notes-api from V0 to V11

| Lab (id) | Title | Level | Runtime | Companion guide |
|---|---|---|---|---|
| `capstone-v00-pipeline-minimal` | V0, a minimal pipeline: notes-api tested on every push | capstone | shell | [guide](https://blog.stephane-robert.info/en/docs/devsecops/capstone/devsecops-capstone/) |

_1 labs, table generated by `scripts/gen_catalog.py`._
<!-- LABS:END -->

## Contributing and license

Contributions are welcome: read [CONTRIBUTING.md](./CONTRIBUTING.md), which
describes the real anatomy of a lab in this repository and the golden rule, a
lab is proven both ways. The [code of conduct](./CODE_OF_CONDUCT.md) applies to
all exchanges, and vulnerabilities are reported privately:
[SECURITY.md](./SECURITY.md).

### License

This content is published under [Creative Commons Attribution 4.0
International](./LICENSE) (CC BY 4.0). You may share and adapt it, including
commercially, provided you credit the source.
