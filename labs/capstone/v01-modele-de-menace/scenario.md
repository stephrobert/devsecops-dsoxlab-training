# V1: write down what can go wrong

## Situation

notes-api has its pipeline: every push runs the tests. But the tests check
what the service **promises**, not what an attacker can **do** with it. Before
adding any scanner, the team wants to know what it protects and against what,
and to keep that up to date with the code.

The `challenge/work` directory holds the project as V0 left it, plus a tool
the team has just written: `scripts/check_threat_model.py`. Run on a
`threat-model.yml`, it refuses an incomplete model, a forgotten STRIDE
category, a threat declared mitigated with no file proving it. Its header
describes the expected format.

SSDF practice targeted: PW.1 (design software to meet security requirements and mitigate security risks).

## Goal

1. A `threat-model.yml` at the root of the project, accepted by the checker:
   the six STRIDE categories, each threat with its component, its mitigation
   and its status.
2. Every **route** `src/notes_api/app.py` declares is analysed in it, named
   like the route: `GET /notes/search`.
3. The flaw the code carries today is named in it **as it is**: a threat that
   stays `open` as long as no version has fixed it.
4. The pipeline runs the checker on every push: a broken model must not reach
   `main`.

## Pointers

- Read `app.py` function by function, and ask for each route: who calls it,
  what does it believe about what it receives?
- STRIDE: spoofing (S), tampering (T), repudiation (R), information disclosure
  (I), denial of service (D), elevation of privilege (E).
- A `mitigated` threat must name in `evidence` the file that proves it.

## Check

```bash
dsoxlab check capstone-v01-modele-de-menace
```

Five checks, twenty points each. Three read your model and confront it with
the code; two play your pipeline with act, on the project and on a copy whose
model is broken.
