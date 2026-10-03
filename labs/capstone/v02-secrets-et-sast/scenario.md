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
