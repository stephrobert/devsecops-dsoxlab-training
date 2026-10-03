# Changelog

**Language:** [English](./CHANGELOG.md) · [Français](./CHANGELOG.fr.md)

All notable changes to this project are recorded in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/).

This repository is a **content catalog**, not a library. A version is
published by a tag, which produces a signed archive (see
[RELEASING.md](./RELEASING.md)); the unit that matters remains the lab, and for
this catalog, the version of the common thread.

## [Unreleased]

### Added

- **The catalog**, on the structure of the Kubernetes, Linux and Terraform
  catalogs: `meta.yml` and `meta.fr.yml` contract, reference solutions
  encrypted with ansible-vault under `solution/`, replayed by
  `scripts/verify-solutions.py`, repository meta-tests, bilingual READMEs whose
  catalog is generated.
- **The NIST SSDF 1.1 objective grid** (`curriculums.yml`), read from the
  official PDF: 19 practices in four groups, PW.3 absent. Each version cites
  the practice it implements, and `tests/test_curriculums.py` refuses a missing
  code or a contradictory label.
- **Links computed per language.** `scripts/gen_doc_url_en.py` reads the
  site's `translationOf` fields, the English README points to the translation
  when it exists, and `tests/test_liens_par_langue.py` refuses a link in the
  wrong language.
- **`verify-solutions.py --deux-sens`**, which also plays each suite on the
  fixtures alone and requires that no test passes.
- **`capstone-v00-pipeline-minimal`**, the first version of the common thread:
  `notes-api`, a Flask service and its five tests, gets its first pipeline.
  Five checks played with act 0.2.89: the shipped code passes, pytest really
  runs, a broken test and an out-of-sync `uv.lock` turn the pipeline red, a
  pull request triggers the same check. Proven both ways, then against two
  faulty solutions: a `uv sync` without `--locked` loses the lock check, an
  `echo "5 passed"` instead of pytest loses three.
- **`capstone-v01-modele-de-menace`**: notes-api gets its STRIDE threat model,
  checked by a team tool the pipeline runs on every push. Five checks: the
  model is valid, every route of `app.py` is analysed in it, the SQL injection
  of `/notes/search` is named and stays open, a broken model turns the
  pipeline red, the pipeline stays green and still tests. Proven both ways,
  then against three faulty variants that each lose only the targeted check
  (two for the missing checker).
- **`capstone-v02-secrets-et-sast`**: gitleaks and Semgrep become two blocking
  gates of the pipeline, the injection of `/notes/search` is fixed with a
  parameterised query, a regression test attempts it, and the threat model
  declares it mitigated with that test as evidence. The booby-trapped copy adds
  the injection to a new route no test covers: a first version reintroduced it
  into `/notes/search`, where the regression test turned the pipeline red even
  with a Semgrep that did not block.
